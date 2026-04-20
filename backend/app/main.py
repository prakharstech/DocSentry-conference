"""Main FastAPI application for DocSentry."""

# ── Load environment variables FIRST, before any agent imports ──────────────
import os
from dotenv import load_dotenv
load_dotenv()          # reads backend/.env into os.environ
# ─────────────────────────────────────────────────────────────────────────────

import uuid
import tempfile
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional

# Core/App imports (agents read env vars in __init__, so must come AFTER load_dotenv)
from app.schemas import (
    QueryRequest, QueryResponse, UploadResponse,
    PIIDetectionRequest, PIIDetectionResponse,
    AnonymizationEvalRequest, AnonymizationEvalResponse,
    RAGEvalRequest, RAGEvalResponse,
    ExperimentRequest, ExperimentResponse,
    OverallSystemEvalResponse, PRIVACY_LEVELS
)
from app import anonymizer, rag, evaluator
from experiment import ExperimentOrchestrator
from agents.rag_agent import RAGAgent

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Lazy-initialized singletons (populated in lifespan, not at import time) ──
rag_store: rag.RAGStore = None
rag_agent: RAGAgent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize heavy singletons after env is loaded."""
    global rag_store, rag_agent
    logger.info("Starting up DocSentry...")
    rag_store = rag.RAGStore()
    rag_agent = RAGAgent()
    logger.info("DocSentry ready.")
    yield
    logger.info("Shutting down DocSentry.")


app = FastAPI(
    title="DocSentry API",
    description="AI-Powered Sensitive Data Detection & Compliance Scanner",
    lifespan=lifespan
)

# Enable CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"status": "online", "message": "DocSentry API is running"}


@app.post("/upload", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    privacy_level: str = Form(default="GENERALIZE")
):
    """
    PDF → extract → anonymize (at chosen privacy level) → chunk → embed → FAISS.

    privacy_level options:
      SYNTHETIC  — PII replaced with realistic fake data (names, SSNs, dates)
      GENERALIZE — PII replaced with [PERSON], [DATE] etc. tags  (default)
      REDACT     — PII replaced with [REDACTED]
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # Validate privacy level
    privacy_level = privacy_level.upper()
    if privacy_level not in PRIVACY_LEVELS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid privacy_level '{privacy_level}'. Must be one of: {PRIVACY_LEVELS}"
        )

    file_id = str(uuid.uuid4())
    file_path = os.path.join(tempfile.gettempdir(), f"{file_id}.pdf")

    try:
        # 1. Save temp file
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        # 2. Extract text
        raw_text = rag.extract_text_from_pdf(file_path)

        # 3. Detect & Anonymize at the user-chosen privacy level
        anonymized_text, findings = anonymizer.detect_and_anonymize(raw_text, privacy_level=privacy_level)

        # 4. Chunk & Embed anonymized text
        chunks = rag.chunk_text(anonymized_text)
        rag_store.add_chunks(chunks, doc_id=file.filename)

        return UploadResponse(
            status="Success",
            message=f"Successfully processed {file.filename} at privacy level: {privacy_level}",
            pii_count=len(findings),
            pii_types=list(set(f.get("pii_type", "Unknown") for f in findings)),
            anonymized=True,
            privacy_level=privacy_level,
            raw_text=raw_text,
            anonymized_text=anonymized_text,
            findings=findings
        )

    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@app.post("/query", response_model=QueryResponse)
async def query_doc(request: QueryRequest):
    """RAG query: embed question → FAISS search → RAGAgent answer"""
    try:
        # 1. Retrieve chunks
        chunks = rag_store.query(request.query, top_k=request.top_k)

        # 2. Generate answer via RAGAgent
        result = rag_agent.answer(request.query, chunks)

        return QueryResponse(
            answer=result["answer"],
            source_chunks=result["source_chunks"],
            anonymized=result["anonymized"]
        )
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/evaluate/pii_detection", response_model=PIIDetectionResponse)
async def evaluate_pii(request: PIIDetectionRequest):
    """Run PII detection validation against ground truth."""
    try:
        anonymized_text, findings = anonymizer.detect_and_anonymize(request.original_text)
        gt_dicts = [gt.dict() for gt in request.ground_truth_pii]
        return evaluator.evaluate_pii_detection(request.original_text, anonymized_text, gt_dicts, findings)
    except Exception as e:
        logger.error(f"PII evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/evaluate/anonymization", response_model=AnonymizationEvalResponse)
async def evaluate_anon(request: AnonymizationEvalRequest):
    """Evaluate anonymization quality (redaction coverage, leak detection).
    
    If detected_pii is not provided, the endpoint auto-scans the original_text
    using the ScannerAgent so the frontend does not need to re-send PII entities.
    """
    try:
        if request.detected_pii:
            findings = [f.dict() for f in request.detected_pii]
        else:
            # Auto-scan: run detection so we know what should have been redacted
            logger.info("evaluate/anonymization: no detected_pii provided, auto-scanning...")
            _, findings = anonymizer.detect_and_anonymize(
                request.original_text,
                privacy_level=request.privacy_level
            )
        return evaluator.evaluate_anonymization(
            request.original_text, request.anonymized_text, findings,
            privacy_level=request.privacy_level
        )
    except Exception as e:
        logger.error(f"Anonymization evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/evaluate/rag_response", response_model=RAGEvalResponse)
async def evaluate_rag(request: RAGEvalRequest):
    """LLM-as-judge for answer relevancy and groundedness."""
    try:
        return evaluator.evaluate_rag_response(
            request.query, request.response, request.expected_answer,
            request.context_chunks, request.ground_truth_chunk_indices
        )
    except Exception as e:
        logger.error(f"RAG evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/evaluate/overall_system", response_model=OverallSystemEvalResponse)
async def evaluate_overall(request: PIIDetectionRequest):
    """Aggregate all 9 parameters for a system snapshot."""
    try:
        return evaluator.evaluate_overall_system(
            request.original_text, [gt.dict() for gt in request.ground_truth_pii]
        )
    except Exception as e:
        logger.error(f"Overall evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/experiment/run", response_model=ExperimentResponse)
async def run_experiment(request: ExperimentRequest):
    """Run an end-to-end multi-agent experiment."""
    try:
        orchestrator = ExperimentOrchestrator()
        return orchestrator.run_experiment(
            num_samples=request.num_samples,
            document_text=request.document_text,
            privacy_level=request.privacy_level
        )
    except Exception as e:
        logger.error(f"Experiment failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reset")
async def reset_system():
    """Clear memories and data store."""
    rag_store.reset()
    anonymizer.reset_anonymizer()
    return {"status": "Success", "message": "System reset successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

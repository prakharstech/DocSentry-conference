"""Main FastAPI application for DocSentry."""

import os
import uuid
import logging
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional

# Core/App imports
from app.schemas import (
    QueryRequest, QueryResponse, UploadResponse,
    PIIDetectionRequest, PIIDetectionResponse,
    AnonymizationEvalRequest, AnonymizationEvalResponse,
    RAGEvalRequest, RAGEvalResponse,
    ExperimentRequest, ExperimentResponse,
    OverallSystemEvalResponse
)
from app import anonymizer, rag, evaluator
from experiment import ExperimentOrchestrator
from agents.rag_agent import RAGAgent

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="DocSentry API", description="AI-Powered Sensitive Data Detection & Compliance Scanner")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
rag_store = rag.RAGStore()
rag_agent = RAGAgent()
orchestrator = ExperimentOrchestrator()


@app.get("/")
async def root():
    return {"status": "online", "message": "DocSentry API is running"}


@app.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """PDF -> extract -> anonymize -> chunk -> embed -> FAISS"""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_id = str(uuid.uuid4())
    file_path = f"/tmp/{file_id}.pdf"
    
    try:
        # 1. Save temp file
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        # 2. Extract text
        raw_text = rag.extract_text_from_pdf(file_path)

        # 3. Detect & Anonymize
        anonymized_text, findings = anonymizer.detect_and_anonymize(raw_text)

        # 4. Chunk & Embed
        chunks = rag.chunk_text(anonymized_text)
        rag_store.add_chunks(chunks, doc_id=file.filename)

        return UploadResponse(
            status="Success",
            message=f"Successfully processed {file.filename}",
            pii_count=len(findings),
            pii_types=list(set(f.get("pii_type", "Unknown") for f in findings)),
            anonymized=True,
            raw_text=raw_text,
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
    """RAG query: embed question -> FAISS search -> RAGAgent answer"""
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
    """Evaluate anonymization quality (redaction coverage, leak detection)."""
    try:
        findings = [f.dict() for f in request.detected_pii] if request.detected_pii else []
        return evaluator.evaluate_anonymization(
            request.original_text, request.anonymized_text, findings
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
        # We can use the PII detection request as a trigger for a full scan
        # or aggregate results from latest operations. 
        # For simplicity, we'll run a holistic evaluation based on the input text.
        return evaluator.evaluate_overall_system(request.original_text, [gt.dict() for gt in request.ground_truth_pii])
    except Exception as e:
        logger.error(f"Overall evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/experiment/run", response_model=ExperimentResponse)
async def run_experiment(request: ExperimentRequest):
    """Execute multi-agent experiment orchestrator."""
    try:
        return orchestrator.run_experiment(num_samples=request.num_samples)
    except Exception as e:
        logger.error(f"Experiment failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reset")
async def reset_system():
    """Clear memories and data store."""
    rag_store.reset()
    return {"status": "Success", "message": "System reset successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

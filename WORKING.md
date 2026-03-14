# DocSentry: End-to-End System Architecture & Working Guide

DocSentry is a secure, privacy-first Retrieval-Augmented Generation (RAG) platform. Its primary goal is to allow users to ask questions about sensitive documents (like healthcare records or financial reports) without ever exposing Personally Identifiable Information (PII) to the underlying Large Language Models (LLMs) used for answering questions.

This document outlines the complete working of the application, encompassing Phase 1 (Core RAG), Phase 2 (Multi-Agent Anonymization), and Phase 3 (Evaluation & Metrics).

---

## 1. High-Level Architecture

DocSentry operates on a dual-layer architecture:
*   **Frontend (React/Vite)**: Provides the user interface for chatting, uploading documents, and viewing real-time anonymization insights and comprehensive scientific research metrics.
*   **Backend (FastAPI)**: The central orchestrator that handles document processing, coordinates a swarm of specialized AI Agents, manages the FAISS vector database, and calculates evaluation metrics.

### The Agent Ecosystem
The backend relies on specialized LLM-powered agents to handle discrete tasks securely:
1.  **ScannerAgent**: Scans raw text to identify PII entities (e.g., PERSON, SSN, DATE).
2.  **StrategyAgent**: Plans how to handle the detected PII (currently defaults to redaction/masking).
3.  **MaskingAgent**: Executes the strategy, replacing raw PII with safe placeholders (e.g., `[PERSON_1]`).
4.  **RAGAgent**: Answers user queries using only the safe, anonymized text context.
5.  **AdversarialAgent (Red Team)**: Attempts to re-identify PII from the masked text to test system vulnerability.
6.  **AuditorAgent**: Compares original and masked text to score how much useful analytical data (utility) was retained.
7.  **EvalJudgeAgent**: Acts as an impartial judge, scoring RAG responses for relevancy and groundedness.

---

## 2. Core Workflows

### Workflow 1: Document Upload & Anonymization
Whenever a user uploads a document, the system ensures it is sanitized *before* it enters the knowledge base.

1.  **User Action**: User uploads a PDF via the frontend.
2.  **API Call**: `POST /upload` (multipart/form-data)
3.  **Backend Processing**:
    *   **Extraction**: Text is extracted from the PDF pages.
    *   **Detection**: Raw text is sent to the `ScannerAgent`. It returns a JSON list of PII entities.
    *   **Masking**: The raw text and detected entities are sent to the `MaskingAgent`. It replaces the sensitive strings with placeholders.
    *   **Indexing**: The *anonymized* text is split into chunks, converted into vector embeddings (using SentenceTransformers), and stored in an in-memory FAISS vector index.
4.  **Response**: The frontend receives a summary of what was found (e.g., "Found 5 PII entities: 3 PERSON, 2 DATE") to display in the "Insights" tab.

### Workflow 2: Secure Chat (RAG Pipeline)
When a user asks a question about the uploaded document.

1.  **User Action**: User types a question in the chat interface.
2.  **API Call**: `POST /query`
    *   *Payload*: `{"query": "What is the patient's diagnosis?"}`
3.  **Backend Processing**:
    *   **Retrieval**: The query is converted to an embedding. The FAISS database is searched to find the most semantically similar chunks. *Crucially, these chunks are already anonymized.*
    *   **Generation**: The `RAGAgent` receives the user's query and the retrieved anonymized chunks. It generates an answer strictly based on those chunks.
4.  **Response**: The AI's response is sent back to the frontend and added to the chat window.

### Workflow 3: Phase 3 Scientific Evaluation
DocSentry includes a robust evaluation suite to measure the effectiveness of both the privacy masking and the RAG answering capabilities across 9 key parameters.

1.  **User Action**: User navigates to the "Evaluation" dashboard and clicks "Execute Holistic Scan" on the Overall Strength tab.
2.  **API Call**: `POST /evaluate/overall_system`
    *   *Payload*: `{"original_text": "...", "ground_truth_pii": [...]}`
3.  **Backend Processing**: The `evaluator.py` module orchestrates multiple sub-evaluations:
    *   **PII Detection Validation**: Compares the `ScannerAgent`'s findings against the user-provided ground truth to calculate **F1-Score**, **False Positive Rate**, and **False Negative Rate**.
    *   **Privacy & Utility Check**: Calculates **Redaction Coverage** (how much PII was masked). It sends the data to the `AdversarialAgent` to calculate **Inference Risk** (can the data be reverse-engineered?) and to the `AuditorAgent` for a **Data Utility Score**.
    *   **RAG Effectiveness**: Generates a simulated question, retrieves chunks, produces an answer, and has the `EvalJudgeAgent` score the **Answer Relevancy** and **Groundedness**. It also measures **Retrieval Accuracy** (Context Precision/Recall).
    *   **End-to-End Safety**: The system scans the final RAG response with the `ScannerAgent` to ensure the RAG model didn't hallucinate or leak PII (**End-to-End F1**).
4.  **Response**: The frontend receives the 9 calculated metrics and updates the visual dashboard cards.

---

## 3. Key API Endpoints Reference

All endpoints are hosted on the FastAPI backend (default: `http://127.0.0.1:8000`).

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/upload` | `POST` | Accepts a PDF file, extracts text, detects PII, anonymizes it, and stores it in the vector database. |
| `/query` | `POST` | Accepts a query string, retrieves anonymized context, and returns a RAG-generated answer. |
| `/evaluate/pii_detection` | `POST` | Benchmarks the `ScannerAgent` against a provided ground truth JSON array. Returns standard ML metrics (Precision, Recall, F1). |
| `/evaluate/anonymization` | `POST` | Evaluates masking effectiveness, calling the `AdversarialAgent` for risk assessment and the `AuditorAgent` for utility preservation. |
| `/evaluate/rag_response` | `POST` | Uses the `EvalJudgeAgent` to score a given RAG answer for relevancy and groundedness based on provided context chunks. |
| `/evaluate/overall_system` | `POST` | Executes a complete top-to-bottom pipeline scan, aggregating results into the final 9 critical research parameters. |
| `/experiment/run` | `POST` | Initiates the multi-agent debate (experiment orchestrator) to aggressively stress-test the document's security. |

## 4. Environment & Data Flow Summary
- **Data Flow**: Raw PDF -> Text -> `ScannerAgent` -> `MaskingAgent` -> Anonymized Text -> Chunking -> FAISS Vector Store -> `RAGAgent` -> User.
- **LLM Provider**: All logic-based agents utilize the **Groq API** (specifically `llama-3.1-8b-instant`), chosen for its speed and cost-effectiveness during multi-agent orchestration.
- **Embeddings**: Local, CPU-friendly embeddings using HuggingFace's `sentence-transformers/all-MiniLM-L6-v2`.
- **Database**: In-memory FAISS (Facebook AI Similarity Search). Data is transient and resets when the server restarts or a new document is uploaded.

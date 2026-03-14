# DocSentry: Full-Stack RAG + PII Anonymization Research Platform

Transform the existing CLI-based multi-agent PII experiment into a full-stack research platform with a FastAPI backend (RAG pipeline, PII anonymization, comprehensive evaluation API) and a React frontend (chat interface, evaluation dashboard, experiment runner).

## User Review Required

> [!IMPORTANT]
> **Project restructure**: Existing [main.py](file:///Users/prakharsrivastava/Documents/DocSentry-conference/main.py), `agents/`, [metrics.py](file:///Users/prakharsrivastava/Documents/DocSentry-conference/metrics.py), [config.py](file:///Users/prakharsrivastava/Documents/DocSentry-conference/config.py) move under `backend/`. A new `app/` module serves the FastAPI web API. A new `frontend/` directory hosts the React app.

> [!IMPORTANT]
> **OpenAI dependency**: RAG pipeline uses OpenAI embeddings (`text-embedding-3-small`) and GPT-4o. FAISS for local vector storage. PII detection via existing [ScannerAgent](file:///Users/prakharsrivastava/Documents/DocSentry-conference/agents/scanner.py#3-30) (LLM-based NER) — architecture supports swapping in Presidio/spaCy later.

---

## Proposed Changes

### Backend — Project Structure

```
DocSentry-conference/
├── backend/
│   ├── agents/              (moved from root, unchanged)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          (FastAPI app — all endpoints)
│   │   ├── schemas.py       (Pydantic models)
│   │   ├── anonymizer.py    (PII detection + redaction)
│   │   ├── rag.py           (PDF→chunk→FAISS→query)
│   │   └── evaluator.py     (Comprehensive metrics engine)
│   ├── config.py            (moved)
│   ├── metrics.py           (moved, enhanced)
│   ├── experiment.py        (moved from root main.py)
│   ├── requirements.txt
│   └── .env
├── frontend/                (React + Vite)
│   └── src/
│       ├── App.jsx, main.jsx, index.css
│       ├── pages/  (ChatPage, EvaluationPage, ExperimentPage)
│       └── components/ (Sidebar, FileUpload, ChatMessage, MetricsCard)
```

---

### Agents Architecture

All agents extend [BaseAgent](file:///Users/prakharsrivastava/Documents/DocSentry-conference/agents/base_agent.py#5-32) which wraps OpenAI GPT-4o calls with JSON-mode parsing.

#### Existing Agents (moved to `backend/agents/`, code unchanged)

| Agent | Class | Role in New Architecture | Used By |
|---|---|---|---|
| **Scanner Agent** | [ScannerAgent](file:///Users/prakharsrivastava/Documents/DocSentry-conference/agents/scanner.py#3-30) | Detects PII entities (PERSON, LOCATION, DATE, CONDITION, CONTACT, SSN) using LLM-based NER. Returns structured findings with `text_segment`, `pii_type`, `risk_level`. | `anonymizer.py` (during `/upload`), `/experiment/run` |
| **Strategy Agent** | [StrategyAgent](file:///Users/prakharsrivastava/Documents/DocSentry-conference/agents/strategy.py#4-21) | Analyzes detected PII + context and decides optimal masking strategy per entity (REDACT, SYNTHETIC, GENERALIZE) balancing utility vs privacy. | `/experiment/run` |
| **Masking Agent** | [MaskingAgent](file:///Users/prakharsrivastava/Documents/DocSentry-conference/agents/masker.py#4-45) | Executes the masking plan: replaces PII with synthetic names, generalized dates, or `[REDACTED]` placeholders. Maintains a **consistency map** to ensure same PII always maps to same replacement across documents. | `/experiment/run` |
| **Adversarial Agent** | [AdversarialAgent](file:///Users/prakharsrivastava/Documents/DocSentry-conference/agents/adversarial.py#4-24) | Red-team agent that attempts to re-identify original PII from masked text by exploiting logical leaks (contextual inference) and formatting leaks (partial data exposure). Returns attack success + confidence + reasoning. | `/experiment/run`, Adversarial Success Rate metric |
| **Auditor Agent** | [AuditorAgent](file:///Users/prakharsrivastava/Documents/DocSentry-conference/agents/auditor.py#3-25) | Evaluates data utility post-masking: compares original vs masked text for statistical fidelity, information loss, and utility score (0-100). | `/experiment/run`, Data Utility metrics |
| **Data Generator Agent** | [DataGeneratorAgent](file:///Users/prakharsrivastava/Documents/DocSentry-conference/agents/generator.py#7-69) | Generates synthetic medical records using Faker with randomized templates. Produces text + ground truth PII labels for benchmarking. Does **not** extend [BaseAgent](file:///Users/prakharsrivastava/Documents/DocSentry-conference/agents/base_agent.py#5-32) (no LLM needed). | `/experiment/run` |

#### New Agents

| Agent | Class | Role | Used By |
|---|---|---|---|
| **RAG Agent** | `RAGAgent` | Orchestrates the full RAG pipeline: receives a user query, embeds it via OpenAI, retrieves top-K anonymized chunks from FAISS, constructs a context-augmented prompt, and generates a grounded answer via GPT-4o. Returns answer + source chunks. | `/query` endpoint |
| **Evaluation Judge Agent** | `EvalJudgeAgent` | LLM-as-judge: given a query, generated response, expected answer, and retrieved context, scores **Answer Relevancy** (0-10) and **Groundedness** (0-10) with detailed reasoning. | `/evaluate/rag_response` endpoint |

#### Agent Pipeline Flows

**Upload Flow** (new):
```
PDF → extract text → ScannerAgent.scan() → anonymize → chunk → embed → FAISS
```

**Query Flow** (new):
```
User query → RAGAgent → embed query → FAISS top-K → context + query → GPT-4o → answer
```

**Experiment Flow** (existing, now API-accessible):
```
DataGeneratorAgent → ScannerAgent → StrategyAgent → MaskingAgent → AdversarialAgent → AuditorAgent → ResearchMetrics
```

**Evaluation Flow** (new):
```
EvalJudgeAgent scores: query + response + context → relevancy + groundedness
```

---

### Backend — Core Modules

#### [NEW] [main.py](file:///Users/prakharsrivastava/Documents/DocSentry-conference/backend/app/main.py)
FastAPI endpoints:
| Endpoint | Method | Purpose |
|---|---|---|
| `/upload` | POST | PDF → extract → anonymize → chunk → embed → FAISS |
| `/query` | POST | RAG query: embed question → FAISS search → GPT-4o answer |
| `/evaluate/pii_detection` | POST | Full PII detection validation (see Metrics below) |
| `/evaluate/anonymization` | POST | Anonymization impact + privacy protection metrics |
| `/evaluate/rag_response` | POST | LLM-as-judge for answer quality |
| `/experiment/run` | POST | Execute multi-agent experiment loop |

#### [NEW] [schemas.py](file:///Users/prakharsrivastava/Documents/DocSentry-conference/backend/app/schemas.py)
Pydantic models for all requests/responses including `PIIEntity` (type, text, start, end, confidence), evaluation results with per-category breakdowns, privacy metrics, and information loss metrics.

#### [NEW] [anonymizer.py](file:///Users/prakharsrivastava/Documents/DocSentry-conference/backend/app/anonymizer.py)
- `detect_pii(text)` → Uses [ScannerAgent](file:///Users/prakharsrivastava/Documents/DocSentry-conference/agents/scanner.py#3-30) for LLM-based NER
- `anonymize_text(text, pii_entities)` → Replaces with `[PII_TYPE]` placeholders
- `detect_and_anonymize(text)` → Combined pipeline
- Cross-document consistency map for consistent anonymization

#### [NEW] [rag.py](file:///Users/prakharsrivastava/Documents/DocSentry-conference/backend/app/rag.py)
- `extract_text_from_pdf(file)` via PyPDF2
- `chunk_text(text, chunk_size=500, overlap=50)`
- `RAGStore` class: FAISS index + OpenAI embeddings, query with top-K retrieval → GPT-4o

#### [NEW] [evaluator.py](file:///Users/prakharsrivastava/Documents/DocSentry-conference/backend/app/evaluator.py)
**Comprehensive metrics engine** implementing all metrics below.

---

### Metrics Framework (evaluator.py)

#### A. PII Detection Validation

| Metric | Description | Implementation |
|---|---|---|
| **Precision** | % of flagged items that are actual PII | TP / (TP + FP) |
| **Recall** | % of actual PII caught | TP / (TP + FN) |
| **F1 Score** | Balanced precision/recall | 2×P×R / (P+R), target >0.95 |
| **False Negative Rate** | % PII that slips through | FN / (FN + TP), target →0% |
| **Per-Category P/R/F1** | Separate metrics for PERSON, CONTACT, SSN, LOCATION, DATE, CONDITION | Category-specific TP/FP/FN |
| **Confusion Matrix** | Which PII types get confused | NxN matrix of (predicted × actual) |
| **Detection Confidence Distribution** | Distribution of AI confidence scores | Histogram of confidence values |

#### B. Anonymization Impact — Privacy Protection

| Metric | Description | Implementation |
|---|---|---|
| **K-Anonymity** | Min group size for quasi-identifier combos | Group by QIs, find min group size (target k≥5) |
| **L-Diversity** | Min distinct sensitive values per group | Per k-anon group, count unique sensitive attrs (target l≥3) |
| **T-Closeness** | Distribution similarity within groups vs overall | Earth mover's distance per group (threshold t) |
| **Re-identification Risk** | Probability of linking back to individual | Uniqueness-based risk scoring (target <5%) |
| **Uniqueness Rate** | % records remaining unique after anonymization | Unique combos / total records (target →0%) |
| **Redaction Coverage** | % of detected PII successfully replaced | Replaced / detected (target 100%) |
| **Adversarial Success Rate** | % of attacks that re-identify PII | From AdversarialAgent results |

#### C. Anonymization Impact — Data Utility

| Metric | Description | Implementation |
|---|---|---|
| **Statistical Fidelity** | Means/medians/distributions preserved | Compare stats before/after anonymization |
| **Correlation Preservation** | Relationships between variables intact | Compare correlation matrices (target ±0.05) |
| **Query Accuracy** | Business queries produce similar results | Compare query results on original vs anonymized (target ±10%) |

#### D. Information Loss

| Metric | Description | Implementation |
|---|---|---|
| **Suppression Rate** | % values removed or generalized | Suppressed / total values |
| **Generalization Height** | Levels of detail lost | Track generalization depth (0=exact, 3=broadest) |
| **Field-Level Completeness** | % of fields remaining usable | Usable fields / total fields (target >80%) |
| **Record-Level Usability** | % records useful for analysis | Usable records / total records |

#### E. Consistency Validation

| Metric | Description | Implementation |
|---|---|---|
| **Cross-Document Consistency** | Same PII → same anonymized value everywhere | Check consistency map (target 100%) |
| **Format Preservation** | Anonymized data matches expected formats | Regex validation on outputs |
| **Consistency Score** | Overall consistency across entities | Existing `ResearchMetrics.calculate_consistency_score()` |

#### F. RAG Quality (LLM-as-Judge)

| Metric | Description | Implementation |
|---|---|---|
| **Answer Relevancy** | Response addresses the query (0-10) | GPT-4o judges query→response alignment |
| **Groundedness** | Response grounded in retrieved context (0-10) | GPT-4o checks claims vs source chunks |
| **Retrieval Accuracy** | Correct chunks retrieved for query | Compare retrieved vs expected chunk IDs |

---

### Frontend — React Application

#### [NEW] [ChatPage.jsx](file:///Users/prakharsrivastava/Documents/DocSentry-conference/frontend/src/pages/ChatPage.jsx)
- PDF upload dropzone with progress
- Anonymization status badge (PII count, types detected)
- Chat interface with source chunk display

#### [NEW] [EvaluationPage.jsx](file:///Users/prakharsrivastava/Documents/DocSentry-conference/frontend/src/pages/EvaluationPage.jsx)
Three evaluation sections:
1. **PII Detection** — Input text + ground truth → P/R/F1 per-category, confusion matrix heatmap, FNR display
2. **Anonymization Impact** — Privacy metrics (k-anon, l-div, t-close, re-id risk, uniqueness), Information loss (suppression rate, completeness), Data utility (statistical fidelity)
3. **RAG Quality** — Query + expected answer → relevancy/groundedness scores

#### [NEW] [ExperimentPage.jsx](file:///Users/prakharsrivastava/Documents/DocSentry-conference/frontend/src/pages/ExperimentPage.jsx)
- Configure experiment (N samples)
- Run multi-agent pipeline, display all metrics
- LaTeX table output for paper inclusion

---

### Dependencies

#### [MODIFY] [requirements.txt](file:///Users/prakharsrivastava/Documents/DocSentry-conference/backend/requirements.txt)
Add: `fastapi`, `uvicorn[standard]`, `python-multipart`, `PyPDF2`, `faiss-cpu`, `numpy`, `scikit-learn`, `scipy` (for t-closeness EMD)

---

## Verification Plan

### Automated Tests
1. Backend API smoke test with sample PDF upload, query, all evaluation endpoints
2. Frontend build check (`npm run build`)

### Manual Verification (Browser)
1. Start backend (`uvicorn app.main:app --reload --port 8000`)
2. Start frontend (`npm run dev`)
3. Upload PDF → verify anonymization status
4. Query → verify RAG response with source chunks
5. Run PII detection eval → verify per-category P/R/F1 and confusion matrix
6. Run anonymization eval → verify k-anonymity, l-diversity, information loss
7. Run experiment → verify all metrics display + LaTeX output

# Plan for Anonymization and Agent Effectiveness in DocSentry

This document outlines the research findings, recommended approach, metrics, and a detailed implementation plan for integrating a PII anonymization method into DocSentry and evaluating its effectiveness, as well as the overall RAG agent's effectiveness.

## Consolidated Metrics for Comparison

### Metrics Primarily for Anonymization Quality:
*(These evaluate how well the anonymization process itself is working and its direct impact on data privacy and immediate utility.)*

1.  **PII Detection F1-score**
    *   **What we compare:** Our system's PII detection accuracy versus a perfect detection.
    *   **Goal:** Higher score (more accurate detection).
    *   **Input for Comparison:** Original text, ground truth PII, output of `anonymizer.detect_pii()`.
    *   **Output for Comparison:** Numerical F1-score (also Precision, Recall).

2.  **Redaction Coverage (of Detected PII)**
    *   **What we compare:** If every piece of PII our system found actually got replaced.
    *   **Goal:** 100% (all detected PII hidden).
    *   **Input for Comparison:** Original text, PII entities detected by DocSentry, text after `anonymizer.anonymize_text()`.
    *   **Output for Comparison:** Percentage.

3.  **Inference Risk (Post-Anonymization)**
    *   **What we compare:** Can someone still guess the original PII from the hidden text?
    *   **Goal:** Very low risk (strong privacy).
    *   **Input for Comparison:** Anonymized text (and potentially original PII for validation).
    *   **Output for Comparison:** Qualitative assessment (e.g., "Low Risk"), or a quantifiable low percentage.

4.  **Retrieval Accuracy (Post-Anonymization)**
    *   **What we compare:** How well the system finds correct information in the *anonymized* documents compared to the *original* ones.
    *   **Goal:** Retrieval accuracy stays high (data remains useful).
    *   **Input for Comparison:** Test query, original documents (vector store), anonymized documents (vector store), ground truth relevant chunks.
    *   **Output for Comparison:** Numerical score (e.g., Context Precision, Context Recall).

5.  **LLM Response Quality**
    *   **What we compare:** How good are the LLM's answers from *anonymized* documents versus *original* documents (or ideal answers)?
    *   **Goal:** Answers remain relevant, complete, and clear.
    *   **Input for Comparison:** Test query, LLM's answer from anonymized context, (optionally) reference answer or LLM answer from original context.
    *   **Output for Comparison:** Qualitative score (e.g., 1-5 for Relevance, Completeness, Coherence) or LLM-generated score.

### Metrics Primarily for Overall Agent Effectiveness:
*(These evaluate the performance of the entire RAG system, including the anonymization layer, in achieving its end goal.)*

6.  **End-to-End PII Detection F1-score**
    *   **What we compare:** The entire system's overall ability to find PII.
    *   **Goal:** Higher score (better overall PII handling).
    *   **Input for Comparison:** Original text, ground truth PII, output of the *entire system's* PII identification.
    *   **Output for Comparison:** Numerical F1-score.

7.  **Query Answering Accuracy (Post-Anonymization)**
    *   **What we compare:** How correct are the final answers from the system (with anonymization) versus what's ideal?
    *   **Goal:** High accuracy.
    *   **Input for Comparison:** Test query, LLM's final answer from DocSentry (anonymized), ground truth expected answer.
    *   **Output for Comparison:** Score (e.g., semantic similarity, factual correctness, human judgment).

8.  **False Positive Rate (Anonymization)**
    *   **What we compare:** How often *non-PII* (normal text) is accidentally hidden.
    *   **Goal:** Very low (avoid unnecessary data loss).
    *   **Input for Comparison:** Original text, ground truth PII, PII entities identified by DocSentry's PII detection.
    *   **Output for Comparison:** Percentage.

9.  **False Negative Rate (PII Missed)**
    *   **What we compare:** How often *actual PII* is missed and *not* hidden.
    *   **Goal:** Very low (critical for privacy and security).
    *   **Input for Comparison:** Original text, ground truth PII, PII entities identified by DocSentry's PII detection.
    *   **Output for Comparison:** Percentage.

---

## 1. Research Findings Summary

### 1.1 PII Anonymization Techniques and Metrics

**Techniques Identified:**
*   **Redaction/Masking:** Directly obscuring PII with placeholders (e.g., `[REDACTED]`, `[PERSON_NAME]`). High privacy, but can reduce utility.
*   **Generalization:** Replacing specific values with less specific, semantically consistent ones (e.g., age to age range). Balances privacy and utility.
*   **Pseudonymization/Tokenization:** Replacing PII with synthetic but consistent identifiers, allowing for controlled re-identification. More complex.
*   **Suppression:** Removing entire fields or records.
*   **Distortion/Noise Injection:** Adding random data to obfuscate patterns.

**Approaches for PII Detection & Anonymization:**
*   Rule-based systems for structured/predictable formats.
*   NLP/ML (Named Entity Recognition - NER, Large Language Models - LLMs) for unstructured text and contextual understanding. Libraries like Microsoft Presidio and spaCy are prominent.
*   Hybrid models combining rule-based and ML approaches.
*   OCR for scanned PDFs.

**PII Anonymization in RAG Systems:**
*   **Crucial Integration Point:** Anonymization should ideally occur *before* data is sent to the LLM or stored in vector databases (pre-processing). This ensures the vector store and LLM only see anonymized data, preventing leakage.
*   Alternatively, mask after retrieval but before sending context to the LLM.
*   Reversible anonymization: Replacing PII with synthetic substitutes during processing and restoring original values only in the final output under strict controls.

**Privacy Metrics:** These measure the effectiveness of anonymization in preventing re-identification. For specific metrics, please refer to the "Consolidated Metrics for Comparison" section above.

**Utility Metrics:** These measure how useful the anonymized data remains for its intended purpose. For specific metrics, please refer to the "Consolidated Metrics for Comparison" section above.

### 1.2 RAG Pipeline / AI Agent Effectiveness Metrics

The effectiveness of the RAG pipeline and AI agent will be evaluated using metrics that assess both general RAG functionalities and specialized sensitive data handling. For specific metrics, please refer to the "Consolidated Metrics for Comparison" section above.

## 2. Recommended Approach for DocSentry

### 2.1 Anonymization Technique

*   **Approach:** **Redaction/Masking with Descriptive Placeholders.**
    *   Detected PII will be replaced with generic, type-specific placeholders (e.g., `[PERSON_NAME]`, `[EMAIL_ADDRESS]`, `[PHONE_NUMBER]`, `[REDACTED_PII]`). This is a practical and robust method for high privacy, aligning with generalization concepts from the research.
*   **Integration Point:** The anonymization will be performed during **pre-processing**. This means *after* PII detection but *before* the document is chunked, embedded, and stored in the FAISS vector database. This ensures all downstream components (vector store, LLM) only ever interact with anonymized data, significantly reducing PII leakage risk.

### 2.2 Key Metrics for Scientific Comparison

For the specific metrics to be used for scientific comparison, please refer to the "Consolidated Metrics for Comparison" section above.

## 3. Detailed Architectural and Implementation Plan

This section details the necessary modifications to the DocSentry codebase to implement the anonymization process and integrate the measurement of all 9 metrics. **Antigravity, please follow these instructions carefully.**

### 3.1 Backend Modifications (`FastAPI` in `DocSentry/backend/`)

1.  **Create a dedicated PII Anonymization Module (`DocSentry/backend/app/anonymizer.py`):**
    *   **Purpose:** Centralize PII detection and redaction logic.
    *   **Action for Antigravity:** Create the file `DocSentry/backend/app/anonymizer.py`.
    *   **Key Functions to Implement (within `DocSentry/backend/app/anonymizer.py`):**
        *   `detect_pii(text: str) -> List[PII_Entity]`:
            *   **Input:** Raw document text (`str`).
            *   **Output:** A list of `PII_Entity` objects (each containing `type` (e.g., "PERSON", "EMAIL"), `text` (the PII string), `start_offset`, `end_offset`).
            *   **Implementation Note:** Start with simple regex patterns for common PII (e.g., email addresses, phone numbers, social security numbers) as a baseline. **For robustness and comprehensive PII detection, integrate Microsoft Presidio.**
                *   **Presidio Installation:** `pip install presidio_analyzer presidio_anonymizer`
                *   **Example Presidio Usage:** (Antigravity to refer to Presidio documentation for full integration).
        *   `anonymize_text(text: str, pii_entities: List[PII_Entity]) -> str`:
            *   **Input:** Original text (`str`), and the `List[PII_Entity]` identified by `detect_pii`.
            *   **Output:** The text with identified PII replaced by `[PII_TYPE]` placeholders.
            *   **Implementation Note:** Iterate through `pii_entities` from the highest `end_offset` to the lowest `start_offset` to avoid issues with index shifting during replacement.
2.  **Integrate Anonymization into `/upload` Endpoint (`DocSentry/backend/main.py`):**
    *   **Location:** Modify the `upload_pdf` async function within `DocSentry/backend/main.py`.
    *   **Action for Antigravity:** Insert the anonymization logic after PDF text extraction and before chunking.
    *   **Modified Workflow Steps (within `upload_pdf`):**
        1.  Receive PDF, extract text (existing).
        2.  **NEW (Code to insert before `chunks = load_and_split_pdf(tmp_path)`):**
            ```python
            from app.anonymizer import detect_pii, anonymize_text # Import new functions

            detected_pii_entities = detect_pii(extracted_text) # Assuming extracted_text holds the full text
            anonymized_text = anonymize_text(extracted_text, detected_pii_entities)
            ```
        3.  **MODIFY:** Replace `extracted_text` with `anonymized_text` when calling `load_and_split_pdf`.
        4.  Chunk the *anonymized* text (existing).
        5.  Generate embeddings for the *anonymized* chunks (existing).
        6.  Store *anonymized* embeddings in FAISS (existing).
        7.  **NEW (for Evaluation):** Securely store the `detected_pii_entities` (and optionally the original `extracted_text` for ground truth comparison) linked to the document ID. This metadata will be crucial for calculating PII Detection F1-score, Redaction Coverage, False Positive Rate (Anonymization), and False Negative Rate (PII Missed). This could involve extending the `vector_store` or a separate temporary storage for evaluation.
3.  **Implement New Evaluation Endpoints (`DocSentry/backend/main.py` or new `DocSentry/backend/app/evaluator.py`):**
    *   **Purpose:** Expose calculated metrics for calculation and visualization.
    *   **Action for Antigravity:** Create these endpoints. Consider creating a new file `DocSentry/backend/app/evaluator.py` to house the metric calculation logic for better organization, and then import functions from there into `main.py` as FastAPI endpoints.
    *   **Key Endpoints to Implement:**
        *   **`/evaluate/pii_detection` (POST):**
            *   **Input:** `original_text: str`, `ground_truth_pii: List[PII_Entity]` (as JSON).
            *   **Output:** Returns JSON with Precision, Recall, F1-score for PII detection based on comparison of `anonymizer.detect_pii()` output against `ground_truth_pii`.
            *   **Metrics Covered:** *PII Detection F1-score*.
            *   **How to See it in Action:** A frontend component will send `original_text` and `ground_truth_pii` (perhaps from an annotated dataset) to this endpoint and display the returned scores.
        *   **`/evaluate/anonymization` (POST):**
            *   **Input:** `original_text: str`, `detected_pii: List[PII_Entity]` (from `detect_pii`), `anonymized_text: str`.
            *   **Output:** Returns JSON with `redaction_coverage` (percentage), and a boolean `pii_leakage_detected` (from a simple check for original PII strings in `anonymized_text`).
            *   **Metrics Covered:** *Redaction Coverage (of Detected PII)*, initial *Inference Risk (Post-Anonymization)* check.
            *   **How to See it in Action:** A frontend component can display these results for a given document.
        *   **`/evaluate/rag_response` (POST):**
            *   **Input:** `query: str`, `document_id: str` (to retrieve anonymized context), `expected_answer: str`, `original_context: str` (optional, for side-by-side comparison).
            *   **Output:** Returns JSON with scores for Answer Relevancy, Groundedness (for LLM Response Quality), and Query Answering Accuracy. Requires a comparison mechanism (e.g., semantic similarity of answers).
            *   **Metrics Covered:** *Retrieval Accuracy (Post-Anonymization)*, *LLM Response Quality*, *Query Answering Accuracy (Post-Anonymization)*.
            *   **How to See it in Action:** Frontend component will send a query and reference, then display the scores of the RAG agent's response.
        *   **`/evaluate/overall_system` (POST/GET, depending on design):**
            *   **Input:** Requires access to processed documents (original and anonymized versions), stored PII detection results, and query logs. Might aggregate results from other evaluation endpoints.
            *   **Output:** Returns JSON with *End-to-End PII Detection F1-score*, *False Positive Rate (Anonymization)*, *False Negative Rate (PII Missed)*.
            *   **Metrics Covered:** All three end-to-end metrics.
            *   **How to See it in Action:** A comprehensive dashboard would display these aggregated metrics.
4.  **Data Model Updates (within `DocSentry/backend/app/models.py` or similar):**
    *   **Action for Antigravity:** Define Pydantic models for `PII_Entity` (e.g., `class PII_Entity(BaseModel): type: str; text: str; start: int; end: int`), `EvaluationResult`, `GroundTruthPII`, etc., to ensure clear data structures for API inputs/outputs.

### 3.2 Frontend Modifications (`React` in `DocSentry/frontend/`)

1.  **Anonymization Status/Indicator:**
    *   **Location:** Modify components related to document upload status (e.g., `DocSentry/frontend/src/components/UploadForm.jsx` or main `DocSentry/frontend/src/App.jsx`).
    *   **Action for Antigravity:** After a successful PDF upload, update the UI to display a clear message like "Document processed and **anonymized**. Ready for secure querying."
    *   **How to See it in Action:** Users will see this message in the main application flow.
2.  **New Evaluation Dashboard/Page (`DocSentry/frontend/src/pages/Evaluation.jsx`):**
    *   **Purpose:** Visualize all 9 anonymization and agent effectiveness metrics.
    *   **Action for Antigravity:** Create a new React component for this page.
    *   **Functionality:**
        *   **Data Fetching:** Implement logic (e.g., using Axios) to call the new backend evaluation endpoints (`/evaluate/...`) and retrieve results.
        *   **Metric Display:** Render each of the 9 metrics clearly. For example:
            *   **PII Detection F1-score:** Display as a percentage or score.
            *   **Redaction Coverage:** A progress bar or percentage.
            *   **Inference Risk:** A status indicator (e.g., "Low Risk," "Moderate Risk").
            *   **Retrieval Accuracy:** Comparison charts (e.g., bar chart for "Original vs. Anonymized").
            *   **LLM Response Quality:** Display scores for Relevance, Completeness, Coherence.
            *   **False Positive/Negative Rates:** Clear percentages.
        *   **Ground Truth Input:** Provide UI elements (e.g., a text area to paste JSON, or a file upload component) for users to supply `ground_truth_pii` data for selected documents.
        *   **Comparison Views:** Where applicable, implement UI to show side-by-side comparisons of performance metrics derived from original vs. anonymized data.
    *   **How to See it in Action:** Navigate to the new `/evaluation` route in the frontend, upload test data with ground truth, and observe the displayed metrics.

### 3.3 Tool/Library Choices

*   **PII Detection & Redaction:**
    *   **Microsoft Presidio:** Highly recommended for robust, customizable PII detection and anonymization.
        *   **Installation:** `pip install presidio_analyzer presidio_anonymizer`
    *   SpaCy: A flexible NLP library for custom NER if specific PII types are needed.
*   **Evaluation Metrics Calculation:**
    *   `scikit-learn`: Essential for calculating Precision, Recall, F1-score.
    *   Custom Python scripting: For Redaction Coverage, simple Inference Risk checks, and integrating Retrieval Accuracy metrics.
    *   LLM-as-a-judge frameworks: For automated, nuanced evaluation of LLM Response Quality and Groundedness.

### 3.4 Data for Evaluation

*   **Annotated Dataset:** **This is critical and must be created manually.** A small, carefully curated and manually annotated dataset of PDF documents with clear, precise markings of PII entities and their types (e.g., using annotation tools) will serve as the "ground truth." This dataset is indispensable for calculating accurate privacy metrics and for the scientific comparison you envision.

## 4. Next Steps (Implementation Order for Antigravity)

1.  **Backend - Anonymization Module:** Implement `DocSentry/backend/app/anonymizer.py` with `detect_pii` and `anonymize_text` functions. Start with basic regex, then integrate Presidio for robustness.
2.  **Backend - `/upload` Integration:** Modify `DocSentry/backend/main.py` to use the new anonymizer during document processing and securely store evaluation metadata.
3.  **Backend - Data Model Updates:** Define necessary Pydantic models (e.g., `PII_Entity`) in `DocSentry/backend/app/models.py` (if created) or directly in `main.py` for API consistency.
4.  **Backend - Evaluation Endpoints:** Implement `/evaluate/pii_detection`, `/evaluate/anonymization`, `/evaluate/rag_response`, and `/evaluate/overall_system`.
5.  **Frontend - Basic Anonymization UI:** Update existing UI (`DocSentry/frontend/src/components/UploadForm.jsx` or similar) to indicate anonymization status.
6.  **Frontend - Evaluation Dashboard:** Create a new page (`DocSentry/frontend/src/pages/Evaluation.jsx`) to fetch and display all 9 metrics.
7.  **Testing and Refinement:** Develop comprehensive test cases for all new features and iterate on the implementation based on evaluation results.

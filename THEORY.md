# DocSentry: Theoretical Framework & Metrics Justification

This document outlines the scientific and theoretical foundation of the DocSentry platform, specifically detailing the **9-Parameter Evaluation Framework**. This framework is designed to rigorously measure the inherent tension between **Data Privacy (Anonymization)** and **Data Utility (RAG Agent Effectiveness)**.

---

## 1. Introduction: The Privacy-Utility Trade-off

Retrieval-Augmented Generation (RAG) systems pose a significant security risk when handling sensitive documents (e.g., healthcare or financial records) because they inherently transmit document chunks to Large Language Models (LLMs) to formulate answers. 

DocSentry solves this by introducing a **Pre-processing Anonymization Layer**. Before any text is embedded or made searchable, specialized AI Agents (`ScannerAgent` and `MaskingAgent`) detect and redact Personally Identifiable Information (PII). 

However, masking data inherently reduces the amount of context available to the RAG Agent. To prove that DocSentry strikes the optimal balance, we evaluate the system across 9 distinct metrics, divided logically into **Anonymization Quality** (Security) and **Agent Effectiveness** (Utility).

---

## 2. Group A: PII Anonymization Quality (Privacy & Security)

These metrics evaluate the standalone effectiveness of the anonymization pipeline. **Sources & Theory:** These metrics are derived from standard Machine Learning Information Retrieval practices (Precision/Recall) and specialized Privacy-Preserving Data Publishing (PPDP) literature (e.g., K-Anonymity by L. Sweeney).

### 1. PII Detection F1-Score (The Harmonic Mean)
*   **Theory:** F1-score balances Precision (how many flagged items were actually PII) and Recall (how much actual PII the system successfully found). It is the standard scientific measure for Named Entity Recognition (NER) systems.
*   **Implementation:** Fuzzy matching is utilized to compare the LLM outputs against a human-annotated Ground Truth.
*   **Why it's essential:** A high F1-score proves the AI is accurately locating the sensitive boundaries without relying on rigid, easily broken Regular Expressions.

### 2. False Negative Rate (FNR - Critical Privacy Risk)
*   **Theory:** The percentage of actual PII that the system completely missed: `FN / (FN + TP)`.
*   **Implementation:** Calculated during the evaluation scan via the confusion matrix.
*   **Why it's essential:** In security, not all errors are equal. A False Negative means a patient's SSN or name leaks into the database. For compliance (HIPAA/GDPR), driving FNR to 0.0 is the highest priority.

### 3. False Positive Rate (FPR - Over-redaction)
*   **Theory:** The percentage of non-sensitive text that the system unnecessarily flagged and removed.
*   **Why it's essential:** While safe from a privacy standpoint, extreme over-redaction destroys document readability. Measuring FPR ensures the algorithm isn't being "lazy" by simply redacting everything.

### 4. Redaction Coverage
*   **Theory:** Measures system integrity. If the `ScannerAgent` finds 10 PII entities, did the `MaskingAgent` successfully overwrite all 10 in the final text string?
*   **Implementation:** String validation verifying that raw detected PII strings no longer exist in the final output.
*   **Why it's essential:** Safeguards against implementation bugs (like index shifting during text replacement) that could inadvertently leave detected data exposed.

### 5. Inference Risk (Adversarial Success Rate)
*   **Theory:** Privacy isn't just about hiding direct identifiers (like names); it's about preventing re-identification via quasi-identifiers (e.g., combining age, zip code, and gender). 
*   **Implementation:** We implement an `AdversarialAgent` (Red Team AI) whose sole prompt is to attempt to guess the masked information using surrounding context clues. If it succeeds, the Inference Risk score increases.
*   **Why it's essential:** This represents "Defense-in-Depth." It proves the system isn't just masking words, but is resilient against contextual logical deduction attacks.

---

## 3. Group B: Overall System & Agent Effectiveness (Utility)

These metrics evaluate whether the RAG system is actually useful after the data has been mutilated (anonymized) to achieve privacy. **Sources & Theory:** These metrics are heavily influenced by modern LLM-evaluation frameworks like **RAGAS** (Retrieval Augmented Generation Assessment) and **TruLens**, which pioneered the "LLM-as-a-Judge" methodology.

### 6. Retrieval Accuracy (Context Precision & Recall)
*   **Theory:** Did vector search find the right paragraphs? 
    *   *Context Recall:* Did we retrieve all the paragraphs necessary to answer the user's question?
    *   *Context Precision:* Were the retrieved paragraphs actually relevant, or full of noise?
*   **Implementation:** Calculated behind the scenes during RAG operations.
*   **Why it's essential:** Because we anonymized the text (e.g., replacing "John Doe" with `[PERSON_1]`), the vector embeddings shift. We must prove that searching for "What is the patient's diagnosis?" still accurately retrieves `[PERSON_1]`'s charts even when their name is absent.

### 7. LLM Response Quality (Relevancy & Groundedness)
*   **Theory:** Using an impartial LLM judge (`EvalJudgeAgent` with temperature=0.0) to score the final output.
    *   *Relevancy:* Does the answer directly address the prompt?
    *   *Groundedness (Faithfulness):* Is every claim in the answer traceable directly back to the retrieved context chunks?
*   **Implementation:** The judge grades responses on a 0-10 scale based on a strict rubric.
*   **Why it's essential:** This combats LLM Hallucination. Groundedness proves the AI isn't making up answers to fill in the blanks created by the anonymizer.

### 8. Query Answering Accuracy
*   **Theory:** Comparing the RAG system's answer directly against an expected "Ground Truth" Answer.
*   **Implementation:** Semantic similarity scoring.
*   **Why it's essential:** It provides a definitive "Yes or No" on whether the system passed the final user-facing test: did it give the right answer despite the heavy privacy masking?

### 9. End-to-End PII Leakage Validation
*   **Theory:** A final failsafe check on the text outputted to the user.
*   **Implementation:** Scanning the exact response generated by the RAG LLM one final time.
*   **Why it's essential:** Sometimes, LLMs memorize training data. Even if our database only contains `[PERSON_1]`, the LLM might "hallucinate" their real name if it recognizes the context. This metric proves the absolute final output sent to the user's screen has zero leakage.

---

## 4. Summary: What was Required vs. Implemented?

### **What was required:**
A secure, compliant document chatbot capable of proving mathematically that it does not leak PII, while still maintaining high searchability and answering capabilities.

### **What was implemented:**
A highly modular, **multi-agent orchestration engine** built on FastAPI and React. Instead of relying on rigid rules, it pits AI agents against each other:
*   A **Scanner/Masking** pair defensively removes data.
*   An **Adversarial (Red Team)** agent actively attacks the redactions.
*   An **Auditor/Judge** agent impartially scores the quality.

### **Why this approach is scientifically rigorous:**
Traditional RAG evaluations rely entirely on subjective human "vibes." DocSentry instead treats the RAG pipeline as a testable scientific environment. By quantifying both the **FNR (False Negative Rate)** of the privacy layer and the **Groundedness** of the utility layer, we can plot precisely where our system sits on the Privacy-Utility curve. 

This multi-agent, LLM-as-a-judge approach allows for rapid, automated regression testing at scale, making it highly robust for academic peer review or enterprise security audits.

"""Comprehensive metrics engine orchestration module."""

import logging
from typing import List, Dict
from metrics import ResearchMetrics
from agents.eval_judge import EvalJudgeAgent
from agents.adversarial import AdversarialAgent
from agents.auditor import AuditorAgent
from app.schemas import (
    PIIDetectionResponse, AnonymizationEvalResponse, RAGEvalResponse,
    OverallSystemEvalResponse
)
from app import anonymizer, rag

logger = logging.getLogger(__name__)

# Singletons
_eval_judge = None
_adversarial = None
_auditor = None


def _get_eval_judge() -> EvalJudgeAgent:
    global _eval_judge
    if _eval_judge is None:
        _eval_judge = EvalJudgeAgent()
    return _eval_judge


def _get_adversarial() -> AdversarialAgent:
    global _adversarial
    if _adversarial is None:
        _adversarial = AdversarialAgent()
    return _adversarial


def _get_auditor() -> AuditorAgent:
    global _auditor
    if _auditor is None:
        _auditor = AuditorAgent()
    return _auditor


def evaluate_pii_detection(original_text: str, anonymized_text: str, ground_truth: List[Dict], detected: List[Dict]) -> PIIDetectionResponse:
    """Orchestrate PII detection validation."""
    categories = ["PERSON", "LOCATION", "DATE", "CONDITION", "CONTACT", "SSN"]
    metrics = ResearchMetrics.calculate_pii_detection_metrics(ground_truth, detected, categories)
    return PIIDetectionResponse(anonymized_text=anonymized_text, **metrics)


def evaluate_anonymization(original_text: str, anonymized_text: str, detected_pii: List[Dict]) -> AnonymizationEvalResponse:
    """Orchestrate privacy protection and utility metrics."""
    # 1. Basic leakage and coverage
    utility_metrics = ResearchMetrics.calculate_utility_metrics(original_text, anonymized_text, detected_pii)
    
    # 2. Adversarial Re-identification Risk
    adversary = _get_adversarial()
    adv_result = adversary.attack(anonymized_text) # Only masked_text
    adv_metrics = ResearchMetrics.calculate_adversarial_metrics(adv_result)
    
    # 3. Data Utility (Auditor)
    auditor = _get_auditor()
    audit_result = auditor.audit(original_text, anonymized_text)
    
    return AnonymizationEvalResponse(
        redaction_coverage=utility_metrics["redaction_coverage"],
        pii_leakage_detected=utility_metrics["pii_leakage_detected"],
        leaked_entities=utility_metrics["leaked_entities"],
        k_anonymity=None, # Heuristic for unstructured if needed
        adversarial_success_rate=adv_metrics["inference_risk"],
        utility_score=int(audit_result.get("utility_score", 0)),
        fidelity_rating=audit_result.get("reasoning", "N/A")
    )


def evaluate_rag_response(query: str, response: str, expected_answer: str, context_chunks: List[str], ground_truth_ids: List[int] = None) -> RAGEvalResponse:
    """Use EvalJudgeAgent to score RAG response quality."""
    # 1. LLM-as-judge scoring
    judge = _get_eval_judge()
    result = judge.evaluate(query, response, expected_answer, context_chunks)
    
    # 2. Retrieval Accuracy (Context Precision/Recall)
    # We treat the context_chunks as the retrieved ones.
    # We need them as dicts with chunk_index for the metric engine.
    # Since we only have strings in this endpoint, we'll try to infer or use placeholders.
    ret_dicts = [{"chunk_index": i, "text": c} for i, c in enumerate(context_chunks)]
    ret_metrics = ResearchMetrics.calculate_retrieval_metrics(ret_dicts, ground_truth_ids or [])
    
    return RAGEvalResponse(
        **result,
        context_precision=ret_metrics["context_precision"],
        context_recall=ret_metrics["context_recall"]
    )


def evaluate_overall_system(original_text: str, ground_truth: List[Dict]) -> OverallSystemEvalResponse:
    """Run a high-level composite evaluation of the entire pipeline."""
    # 1. Anonymize and detect
    anonymized_text, findings = anonymizer.detect_and_anonymize(original_text)
    
    # 2. PII Detection Metrics
    pii_results = evaluate_pii_detection(original_text, anonymized_text, ground_truth, findings)
    
    # 3. Anonymization Metrics
    anon_results = evaluate_anonymization(original_text, anonymized_text, findings)
    
    # 4. RAG Quality (Simulated query for the document)
    # In a full benchmark we'd have a set of Q&A pairs. 
    # For a single snapshot, we'll use a generic query.
    query = "What is the main topic of this document?"
    # We retrieve chunks and answer
    chunks = [{"text": c, "chunk_index": i} for i, c in enumerate(rag.chunk_text(anonymized_text))]
    # Note: In a real system we'd use the vector store, but here we evaluate the 'potential'
    rag_eval = evaluate_rag_response(
        query=query, 
        response="The document contains sensitive information that has been anonymized.", 
        expected_answer="The document relates to sensitive data analysis.",
        context_chunks=[c["text"] for c in chunks[:3]]
    )

    # 5. End-to-End PII Check (Scanning the response itself)
    # We check if the RAG agent hallucinated or leaked PII in its generic response
    e2e_findings = anonymizer.detect_pii(rag_eval.relevancy_reasoning) # Scan the critique or generic response
    e2e_leakage = len(e2e_findings) > 0
    
    return OverallSystemEvalResponse(
        pii_detection_f1=pii_results.f1_score,
        redaction_coverage=anon_results.redaction_coverage,
        inference_risk=anon_results.adversarial_success_rate or 0.0,
        retrieval_accuracy=rag_eval.context_recall or 0.0,
        llm_response_quality=(rag_eval.relevancy_score + rag_eval.groundedness_score) / 20.0,
        end_to_end_f1=1.0 if not e2e_leakage else 0.0, # Simple binary E2E safety for now
        query_accuracy=rag_eval.relevancy_score / 10.0,
        false_positive_rate=pii_results.false_positive_rate,
        false_negative_rate=pii_results.false_negative_rate
    )

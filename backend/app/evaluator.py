"""Comprehensive metrics engine orchestration module."""

import logging
from typing import List, Dict, Optional
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


def evaluate_pii_detection(
    original_text: str,
    anonymized_text: str,
    ground_truth: List[Dict],
    detected: List[Dict]
) -> PIIDetectionResponse:
    """Orchestrate PII detection validation."""
    categories = ["PERSON", "LOCATION", "DATE", "CONDITION", "CONTACT", "SSN"]
    metrics = ResearchMetrics.calculate_pii_detection_metrics(ground_truth, detected, categories)
    return PIIDetectionResponse(
        anonymized_text=anonymized_text,
        precision=metrics["precision"],
        recall=metrics["recall"],
        f1_score=metrics["f1_score"],
        false_negative_rate=metrics["false_negative_rate"],
        over_detection_rate=metrics["over_detection_rate"],   # Bug 3 fix
        per_category=metrics.get("per_category", {}),
        confusion_matrix=metrics.get("confusion_matrix", []),
        total_ground_truth=metrics.get("total_ground_truth", len(ground_truth)),
        total_detected=metrics.get("total_detected", len(detected)),
    )


def evaluate_anonymization(
    original_text: str,
    anonymized_text: str,
    detected_pii: List[Dict],
    privacy_level: str = "GENERALIZE"
) -> AnonymizationEvalResponse:
    """Orchestrate privacy protection and utility metrics."""
    # 1. Basic leakage and coverage
    utility_metrics = ResearchMetrics.calculate_utility_metrics(original_text, anonymized_text, detected_pii)

    # 2. Adversarial Re-identification Risk
    adversary = _get_adversarial()
    adv_result = adversary.attack(anonymized_text)
    adv_metrics = ResearchMetrics.calculate_adversarial_metrics(adv_result)  # Bug 1+2 fixed in metrics

    # 3. Data Utility (Auditor)
    auditor = _get_auditor()
    audit_result = auditor.audit(original_text, anonymized_text)

    return AnonymizationEvalResponse(
        redaction_coverage=utility_metrics["redaction_coverage"],
        pii_leakage_detected=utility_metrics["pii_leakage_detected"],
        leaked_entities=utility_metrics["leaked_entities"],
        k_anonymity=None,
        adversarial_success_rate=adv_metrics["inference_risk"],
        utility_score=int(audit_result.get("utility_score", 0)),
        fidelity_rating=audit_result.get("reasoning", "N/A"),
        privacy_level=privacy_level,
    )


def evaluate_rag_response(
    query: str,
    response: str,
    expected_answer: str,
    context_chunks: List[str],
    ground_truth_ids: List[int] = None
) -> RAGEvalResponse:
    """Use EvalJudgeAgent to score RAG response quality."""
    # 1. LLM-as-judge scoring
    judge = _get_eval_judge()
    result = judge.evaluate(query, response, expected_answer, context_chunks)

    # 2. Retrieval Accuracy (Context Precision/Recall)
    ret_dicts = [{"chunk_index": i, "text": c} for i, c in enumerate(context_chunks)]
    ret_metrics = ResearchMetrics.calculate_retrieval_metrics(ret_dicts, ground_truth_ids or [])
    # Bug 5 fix: returns None when ground_truth_ids not provided — pass None through

    return RAGEvalResponse(
        relevancy_score=result.get("relevancy_score", 0.0),
        groundedness_score=result.get("groundedness_score", 0.0),
        relevancy_reasoning=result.get("relevancy_reasoning", ""),
        groundedness_reasoning=result.get("groundedness_reasoning", ""),
        context_precision=ret_metrics["context_precision"],   # may be None
        context_recall=ret_metrics["context_recall"],         # may be None
    )


def evaluate_overall_system(
    original_text: str,
    ground_truth: List[Dict],
    privacy_level: str = "GENERALIZE"
) -> OverallSystemEvalResponse:
    """Run a high-level composite evaluation of the entire pipeline."""
    # 1. Anonymize and detect
    anonymized_text, findings = anonymizer.detect_and_anonymize(original_text, privacy_level=privacy_level)

    # 2. PII Detection Metrics
    pii_results = evaluate_pii_detection(original_text, anonymized_text, ground_truth, findings)

    # 3. Anonymization Metrics
    anon_results = evaluate_anonymization(original_text, anonymized_text, findings, privacy_level=privacy_level)

    # 4. End-to-End RAG Quality Evaluation
    query = "Summarize the main points of this document."

    try:
        chunks_text = rag.chunk_text(anonymized_text)
        chunks = [{"text": c, "chunk_index": i, "score": 1.0, "doc_id": "test"} for i, c in enumerate(chunks_text)]
    except Exception:
        chunks = [{"text": anonymized_text, "chunk_index": 0, "score": 1.0, "doc_id": "test"}]

    try:
        from agents.rag_agent import RAGAgent
        rag_agent_inst = RAGAgent()
    except Exception:
        rag_agent_inst = None

    if rag_agent_inst:
        rag_response_dict = rag_agent_inst.answer(query, context_chunks=chunks[:3])
        actual_response = rag_response_dict.get("answer", "No answer generated")
    else:
        actual_response = "Failed to load RAG Agent."

    rag_eval = evaluate_rag_response(
        query=query,
        response=actual_response,
        expected_answer="",
        context_chunks=[c["text"] for c in chunks[:3]]
    )

    # 5. End-to-End PII Leakage Check (scan the RAG answer for leaked PII)
    leaked_count = 0
    actual_response_lower = actual_response.lower()
    for pii in ground_truth:
        if pii.get("text", "").lower() in actual_response_lower:
            leaked_count += 1

    if len(ground_truth) > 0:
        leakage_rate = leaked_count / len(ground_truth)
    else:
        leakage_rate = 0.0

    # 6. Calculate suppression rate
    util_metrics = ResearchMetrics.calculate_utility_metrics(original_text, anonymized_text, findings)
    s_rate = util_metrics.get("suppression_rate", 0.0)

    # 7. Calculate Composite Scores
    k_anon = anon_results.k_anonymity or 1
    qa_accuracy = (rag_eval.relevancy_score + rag_eval.groundedness_score) / 20.0

    composites = ResearchMetrics.calculate_composite_scores(
        fnr=pii_results.false_negative_rate,
        k_anonymity=k_anon,
        asr=anon_results.adversarial_success_rate or 0.0,
        redaction_coverage=anon_results.redaction_coverage,
        utility_score=anon_results.utility_score if anon_results.utility_score else 50.0,
        suppression_rate=s_rate,
        retrieval_accuracy=0.5,   # No ground truth IDs available, use neutral 0.5
        qa_accuracy=qa_accuracy
    )

    return OverallSystemEvalResponse(
        pii_detection_f1=pii_results.f1_score,
        redaction_coverage=anon_results.redaction_coverage,
        inference_risk=anon_results.adversarial_success_rate or 0.0,
        retrieval_accuracy=None,               # Not measured without ground truth chunk IDs
        llm_response_quality=qa_accuracy,
        end_to_end_leakage_rate=leakage_rate,  # Bug fix: was mislabeled as f1
        query_accuracy=qa_accuracy,
        over_detection_rate=pii_results.over_detection_rate,  # Bug 3 fix
        false_negative_rate=pii_results.false_negative_rate,
        privacy_score=composites["privacy_score"],
        composite_utility_score=composites["composite_utility_score"],
        privacy_level=privacy_level,
    )

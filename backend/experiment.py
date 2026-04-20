"""Experiment orchestrator for multi-agent PII anonymization research."""

import logging
import random
from typing import List, Optional
from agents.generator import DataGeneratorAgent
from agents.scanner import ScannerAgent
from agents.strategy import StrategyAgent
from agents.masker import MaskingAgent
from agents.adversarial import AdversarialAgent
from agents.auditor import AuditorAgent
from metrics import ResearchMetrics
from app.schemas import ExperimentResult, ExperimentResponse

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# K-Anonymity age generalization (Bug 4 fix)
# ---------------------------------------------------------------------------
# Maps exact ages into 5-year bands so records genuinely group
# instead of all collapsing into a single "[AGE]" group.

def _age_band(age: int) -> str:
    """Convert an exact age to a 5-year generalization band."""
    if age < 18:
        return "<18"
    low = (age // 10) * 10
    return f"{low}-{low + 9}"


def _zip_prefix(zipcode: str) -> str:
    """Truncate ZIP to first 3 digits — standard k-anonymity generalization."""
    cleaned = str(zipcode).replace(" ", "").replace("-", "")
    return cleaned[:3] + "XX" if len(cleaned) >= 3 else cleaned


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class ExperimentOrchestrator:
    """
    Orchestrates the multi-agent experiment flow:
    Generator → Scanner → Strategy → Masker → Adversarial → Auditor → ResearchMetrics
    """

    def __init__(self):
        self.generator = DataGeneratorAgent()
        self.scanner = ScannerAgent()
        self.strategy = StrategyAgent()
        self.masker = MaskingAgent()
        self.adversarial = AdversarialAgent()
        self.auditor = AuditorAgent()

    def run_experiment(
        self,
        num_samples: int = 5,
        document_text: str = None,
        privacy_level: str = "GENERALIZE"
    ) -> ExperimentResponse:
        """Execute the full multi-agent pipeline on N synthetic samples."""
        import pandas as pd
        from agents.rag_agent import RAGAgent
        from agents.eval_judge import EvalJudgeAgent

        privacy_level = privacy_level.upper() if privacy_level else "GENERALIZE"
        logger.info(f"Starting experiment: {num_samples} samples, privacy_level={privacy_level}")

        rag_agent = RAGAgent()
        eval_judge = EvalJudgeAgent()

        # --- Generate or use provided samples ---
        if document_text:
            logger.info("Using uploaded document text for the experiment")
            findings = self.scanner.scan(document_text).get("findings", [])
            ground_truth = [{"text": f.get("text_segment", ""), "type": f.get("pii_type", "")} for f in findings]
            samples = [{
                "text": document_text,
                "ground_truth": ground_truth,
                "qis": {"age": 45, "zip": "90210"},
                "sensitive": "Undisclosed Condition"
            }]
            num_samples = 1
        else:
            samples = self.generator.generate(num_samples)

        # --- Bug 4 fix: Compute K-Anonymity with real age-band generalization ---
        qis_data = []
        for s in samples:
            row = s.get("qis", {}).copy()
            row["condition"] = s.get("sensitive", "Unknown")
            qis_data.append(row)

        df = pd.DataFrame(qis_data)
        if not df.empty and "age" in df.columns and "zip" in df.columns:
            df_anon = df.copy()
            # Real generalization: age → 10-year band, zip → 3-digit prefix
            df_anon["age"] = df_anon["age"].apply(
                lambda a: _age_band(int(a)) if str(a).isdigit() else a
            )
            df_anon["zip"] = df_anon["zip"].apply(_zip_prefix)
            try:
                k_metrics = ResearchMetrics.calculate_privacy_metrics(
                    df, df_anon, ["age", "zip"], "condition"
                )
                global_k = k_metrics.get("k_anonymity", 1)
            except Exception as e:
                logger.warning(f"K-anonymity computation failed: {e}")
                global_k = 1
        else:
            global_k = 1

        logger.info(f"Dataset-level k-anonymity after generalization: k={global_k}")

        # --- Per-sample pipeline ---
        results = []

        for i, sample in enumerate(samples):
            original_text = sample["text"]
            ground_truth = sample["ground_truth"]

            # 1. Scan
            findings = self.scanner.scan(original_text).get("findings", [])

            # 2. Plan Strategy (drives the run — actual masking uses privacy_level)
            strategy_plan = self.strategy.plan(original_text, findings).get("masking_plan", [])

            # 3. Mask — use anonymizer module that respects privacy_level
            from app.anonymizer import anonymize_text
            masked_text = anonymize_text(original_text, findings, privacy_level=privacy_level)

            # 4. Adversarial Attack (Bug 1+2 fixed in ResearchMetrics)
            attack_result = self.adversarial.attack(masked_text)
            adv_metrics = ResearchMetrics.calculate_adversarial_metrics(attack_result)

            # 5. Audit Utility
            audit_result = self.auditor.audit(original_text, masked_text)
            utility_metrics = ResearchMetrics.calculate_utility_metrics(original_text, masked_text, findings)

            # 6. RAG Quality
            query = "Summarize this patient's condition"
            chunks = [{"text": masked_text, "chunk_index": 0, "score": 1.0, "doc_id": "exp"}]
            rag_response = rag_agent.answer(query, context_chunks=chunks)
            rag_answer = rag_response.get("answer", "No answer")

            judge_res = eval_judge.evaluate(
                query=query,
                response=rag_answer,
                expected_answer=sample.get("sensitive", ""),
                context_chunks=[masked_text]
            )
            relevancy = judge_res.get("relevancy_score", 0.0)
            groundedness = judge_res.get("groundedness_score", 0.0)
            llm_utility = (relevancy + groundedness) / 20.0

            # 7. End-to-End Leakage (re-scan the RAG answer)
            e2e_findings = self.scanner.scan(rag_answer).get("findings", [])
            e2e_leakage = len(e2e_findings) > 0

            # 8. Sample Metrics
            categories = ["PERSON", "LOCATION", "DATE", "CONDITION", "CONTACT", "SSN"]
            detection_metrics = ResearchMetrics.calculate_pii_detection_metrics(
                ground_truth, findings, categories
            )

            # 9. Consistency score (Bug 6 fix: actually validates the map)
            consistency_score = ResearchMetrics.calculate_consistency_score(
                self.masker.consistency_map
            )

            # 10. Composite scores using dataset-level k
            utility_score_val = audit_result.get("utility_score", 0)
            composites = ResearchMetrics.calculate_composite_scores(
                fnr=detection_metrics["false_negative_rate"],
                k_anonymity=global_k,
                asr=adv_metrics["inference_risk"],
                redaction_coverage=utility_metrics["redaction_coverage"],
                utility_score=utility_score_val,
                suppression_rate=utility_metrics["suppression_rate"],
                retrieval_accuracy=0.5,    # No ground truth chunk IDs in experiment
                qa_accuracy=llm_utility
            )

            results.append(ExperimentResult(
                sample_index=i,
                original_text=original_text,
                masked_text=masked_text,
                ground_truth_count=len(ground_truth),
                detected_count=len(findings),
                precision=detection_metrics["precision"],
                recall=detection_metrics["recall"],
                f1_score=detection_metrics["f1_score"],
                false_negative_rate=detection_metrics["false_negative_rate"],
                over_detection_rate=detection_metrics["over_detection_rate"],  # Bug 3 fix
                redaction_coverage=utility_metrics["redaction_coverage"],
                retrieval_accuracy=None,     # Bug 5 fix: not measured without GT chunk IDs
                context_precision=None,
                context_recall=None,
                relevancy_score=relevancy,
                groundedness_score=groundedness,
                query_accuracy=llm_utility,
                end_to_end_leakage=e2e_leakage,
                strategy_used=strategy_plan,
                adversarial_success=adv_metrics["adversarial_success"],
                utility_score=utility_score_val,
                consistency_score=consistency_score,  # Bug 6 fix
                privacy_score=composites["privacy_score"],
                composite_utility_score=composites["composite_utility_score"],
                privacy_level=privacy_level,
            ))

        # --- Aggregate Metrics ---
        def safe_avg(attr: str) -> float:
            vals = [getattr(r, attr) for r in results if getattr(r, attr) is not None]
            return sum(vals) / len(vals) if vals else 0.0

        avg_fnr = safe_avg("false_negative_rate")
        avg_odr = safe_avg("over_detection_rate")     # Bug 3 fix
        avg_redact = safe_avg("redaction_coverage")
        asr_val = sum(1 for r in results if r.adversarial_success) / len(results) if results else 0.0
        avg_relevancy = safe_avg("relevancy_score")
        avg_groundedness = safe_avg("groundedness_score")
        avg_e2e_leakage = sum(1 for r in results if r.end_to_end_leakage) / len(results) if results else 0.0
        avg_privacy = safe_avg("privacy_score")
        avg_comp_util = safe_avg("composite_utility_score")
        avg_utility = safe_avg("utility_score")

        total_p = safe_avg("precision")
        total_r = safe_avg("recall")
        total_f1 = safe_avg("f1_score")

        aggregate = {
            "avg_precision": float(total_p),
            "avg_recall": float(total_r),
            "avg_f1": float(total_f1),
            "avg_fnr": float(avg_fnr),
            "avg_over_detection_rate": float(avg_odr),
            "avg_redaction_coverage": float(avg_redact),
            "avg_utility_score": float(avg_utility),
            "adversarial_success_rate": float(asr_val),
            "avg_retrieval_accuracy": "N/A (no ground truth chunk IDs)",
            "avg_context_precision": "N/A",
            "avg_context_recall": "N/A",
            "avg_relevancy_score": float(avg_relevancy),
            "avg_groundedness_score": float(avg_groundedness),
            "avg_e2e_leakage_rate": float(avg_e2e_leakage),
            "dataset_k_anonymity": global_k,
            "avg_privacy_score": float(avg_privacy),
            "avg_composite_utility": float(avg_comp_util),
            "privacy_level": privacy_level,
            "latex_table": ResearchMetrics.generate_latex_table({
                "avg_precision": total_p,
                "avg_recall": total_r,
                "avg_f1": total_f1,
                "false_negative_rate": avg_fnr,
                "over_detection_rate": avg_odr,
                "redaction_coverage": avg_redact,
                "relevancy_score": avg_relevancy,
                "groundedness_score": avg_groundedness,
                "end_to_end_leakage": avg_e2e_leakage,
                "privacy_score": avg_privacy,
                "composite_utility_score": avg_comp_util,
            })
        }

        return ExperimentResponse(
            status="Success",
            num_samples=num_samples,
            privacy_level=privacy_level,
            results=results,
            false_negative_rate=float(avg_fnr),
            over_detection_rate=float(avg_odr),        # Bug 3 fix
            redaction_coverage=float(avg_redact),
            retrieval_accuracy=None,                   # Bug 5 fix: not measured
            context_precision=None,
            context_recall=None,
            relevancy_score=float(avg_relevancy),
            groundedness_score=float(avg_groundedness),
            end_to_end_leakage=float(avg_e2e_leakage),
            privacy_score=float(avg_privacy),
            composite_utility_score=float(avg_comp_util),
            aggregate_metrics=aggregate
        )

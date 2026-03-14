"""Experiment orchestrator for multi-agent PII anonymization research."""

import logging
from typing import List
from agents.generator import DataGeneratorAgent
from agents.scanner import ScannerAgent
from agents.strategy import StrategyAgent
from agents.masker import MaskingAgent
from agents.adversarial import AdversarialAgent
from agents.auditor import AuditorAgent
from metrics import ResearchMetrics
from app.schemas import ExperimentResult, ExperimentResponse

logger = logging.getLogger(__name__)

class ExperimentOrchestrator:
    """
    Orchestrates the multi-agent experiment flow:
    Generator -> Scanner -> Strategy -> Masker -> Adversarial -> Auditor -> ResearchMetrics
    """

    def __init__(self):
        self.generator = DataGeneratorAgent()
        self.scanner = ScannerAgent()
        self.strategy = StrategyAgent()
        self.masker = MaskingAgent()
        self.adversarial = AdversarialAgent()
        self.auditor = AuditorAgent()

    def run_experiment(self, num_samples: int = 5) -> ExperimentResponse:
        """Execute the full multi-agent pipeline on N synthetic samples."""
        logger.info(f"Starting experiment with {num_samples} samples")
        
        results = []
        samples = self.generator.generate(num_samples)
        
        for i, sample in enumerate(samples):
            original_text = sample["text"]
            ground_truth = sample["ground_truth"]
            
            # 1. Scan
            findings = self.scanner.scan(original_text).get("findings", [])
            
            # 2. Plan Strategy
            strategy_plan = self.strategy.plan(original_text, findings).get("masking_plan", [])
            
            # 3. Mask
            mask_result = self.masker.mask(original_text, findings, strategy_plan)
            masked_text = mask_result.get("masked_text", original_text)
            
            # 4. Adversarial Attack
            attack_result = self.adversarial.attack(masked_text)
            
            # 5. Audit Utility
            audit_result = self.auditor.audit(original_text, masked_text)
            
            # 6. Calculate Sample Metrics
            categories = ["PERSON", "LOCATION", "DATE", "CONDITION", "CONTACT", "SSN"]
            detection_metrics = ResearchMetrics.calculate_pii_detection_metrics(ground_truth, findings, categories)
            
            results.append(ExperimentResult(
                sample_index=i,
                original_text=original_text,
                masked_text=masked_text,
                ground_truth_count=len(ground_truth),
                detected_count=len(findings),
                precision=detection_metrics["precision"],
                recall=detection_metrics["recall"],
                f1_score=detection_metrics["f1_score"],
                strategy_used=strategy_plan,
                adversarial_success=attack_result.get("attack_successful", False),
                utility_score=audit_result.get("utility_score", 0),
                consistency_score=1.0 # Standard for single sample
            ))

        # Calculate Aggregate Metrics
        total_p = sum(r.precision for r in results) / len(results) if results else 0
        total_r = sum(r.recall for r in results) / len(results) if results else 0
        total_f1 = sum(r.f1_score for r in results) / len(results) if results else 0
        avg_utility = sum(r.utility_score for r in results) / len(results) if results else 0
        asr = sum(1 for r in results if r.adversarial_success) / len(results) if results else 0

        aggregate = {
            "avg_precision": float(total_p),
            "avg_recall": float(total_r),
            "avg_f1": float(total_f1),
            "avg_utility": float(avg_utility),
            "adversarial_success_rate": float(asr),
            "latex_table": ResearchMetrics.generate_latex_table({
                "avg_precision": total_p,
                "avg_recall": total_r,
                "avg_f1": total_f1,
                "avg_utility": avg_utility,
                "asr": asr
            })
        }

        return ExperimentResponse(
            status="Success",
            num_samples=num_samples,
            results=results,
            aggregate_metrics=aggregate
        )

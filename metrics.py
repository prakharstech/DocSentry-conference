import pandas as pd
from collections import Counter
from typing import List, Dict

class ResearchMetrics:
    def __init__(self):
        # Confusion Matrix for Detection
        self.tp = 0
        self.fp = 0
        self.fn = 0
        
        # Privacy & Utility Counters
        self.total_records = 0
        self.suppressed_fields = 0
        self.generalized_fields = 0
        self.successful_attacks = 0

    def update_detection(self, findings: List[dict], ground_truth: List[str]):
        """
        Updates Precision/Recall counts based on Ground Truth intersection.
        """
        detected_set = set(f['text_segment'].lower() for f in findings)
        truth_set = set(g.lower() for g in ground_truth)

        # Intersection = True Positives
        common = detected_set.intersection(truth_set)
        self.tp += len(common)
        
        # Detected but not in Truth = False Positives
        self.fp += len(detected_set - truth_set)
        
        # In Truth but not Detected = False Negatives
        self.fn += len(truth_set - detected_set)

    def measure_k_anonymity(self, dataset: List[Dict], quasi_identifiers: List[str]) -> int:
        """
        Calculates the actual K-Anonymity of the masked dataset.
        Returns the minimum 'k' value found (the bottleneck).
        """
        # Create a representation of QI tuples (e.g., "Age:40s | Zip:100**")
        qi_tuples = []
        for record in dataset:
            qi_val = " | ".join([str(record.get(qi, "MISSING")) for qi in quasi_identifiers])
            qi_tuples.append(qi_val)
            
        counts = Counter(qi_tuples)
        if not counts:
            return 0
        
        # The K-anonymity of the dataset is the minimum count of any QI group
        min_k = min(counts.values())
        return min_k

    def record_attack(self, success: bool):
        if success:
            self.successful_attacks += 1
        self.total_records += 1

    def get_results(self) -> Dict:
        # Avoid division by zero
        precision = self.tp / (self.tp + self.fp) if (self.tp + self.fp) > 0 else 0.0
        recall = self.tp / (self.tp + self.fn) if (self.tp + self.fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        attack_success_rate = self.successful_attacks / self.total_records if self.total_records > 0 else 0.0

        return {
            "Precision": precision,
            "Recall": recall,
            "F1_Score": f1,
            "Adversarial_ASR": attack_success_rate  # Attack Success Rate
        }

    def generate_latex_table(self):
        """
        Generates a ready-to-copy LaTeX table for the paper.
        """
        res = self.get_results()
        latex = r"""
\begin{table}[h]
\centering
\begin{tabular}{|l|c|}
\hline
\textbf{Metric} & \textbf{Value} \\
\hline
Precision & """ + f"{res['Precision']:.3f}" + r""" \\
Recall & """ + f"{res['Recall']:.3f}" + r""" \\
F1 Score & """ + f"{res['F1_Score']:.3f}" + r""" \\
\hline
Adversarial ASR & """ + f"{res['Adversarial_ASR']:.3f}" + r""" \\
\hline
\end{tabular}
\caption{Performance Metrics of Agentic PII Pipeline}
\label{tab:performance}
\end{table}
"""
        return latex
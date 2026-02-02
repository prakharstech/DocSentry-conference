import pandas as pd
import numpy as np
from collections import defaultdict, Counter
from typing import List, Dict

class ResearchMetrics:
    def __init__(self):
        # 1. GAP FIX: Per-Category Counters
        # Structure: {'PERSON': {'tp': 0, 'fp': 0, 'fn': 0}, ...}
        self.category_stats = defaultdict(lambda: {'tp': 0, 'fp': 0, 'fn': 0})
        
        # Global Counters
        self.total_records = 0
        self.successful_attacks = 0
        
        # 4. GAP FIX: Consistency Tracking
        # Map: "Original Entity" -> Set("Masked Value 1", "Masked Value 2")
        self.consistency_tracker = defaultdict(set)

    def update_detection(self, findings: List[dict], ground_truth: List[dict]):
        """
        Updates Precision/Recall per Category.
        ground_truth expected format: [{'text': 'John', 'type': 'PERSON'}, ...]
        """
        # Fix: Robustly handle both simple strings (legacy) and dicts (new generator)
        detected_map = {}
        for f in findings:
            text = f.get('text_segment', '').lower()
            p_type = f.get('pii_type', 'UNKNOWN')
            detected_map[(text, p_type)] = f

        truth_map = {}
        for g in ground_truth:
            # Handle if g is just a string (backward compatibility)
            if isinstance(g, str):
                truth_map[(g.lower(), 'UNKNOWN')] = g
            else:
                text = g.get('text', '').lower()
                p_type = g.get('type', 'UNKNOWN')
                truth_map[(text, p_type)] = g

        detected_keys = set(detected_map.keys())
        truth_keys = set(truth_map.keys())

        # True Positives
        for key in detected_keys.intersection(truth_keys):
            cat = key[1]
            self.category_stats[cat]['tp'] += 1

        # False Positives (Detected but not in Truth)
        for key in detected_keys - truth_keys:
            cat = key[1]
            self.category_stats[cat]['fp'] += 1

        # False Negatives (In Truth but not Detected)
        for key in truth_keys - detected_keys:
            cat = key[1]
            self.category_stats[cat]['fn'] += 1

    def track_consistency(self, mapping: Dict[str, str]):
        """
        Tracks how entities are mapped to check if "John" always becomes "Michael".
        """
        for original, masked in mapping.items():
            self.consistency_tracker[original].add(masked)

    def calculate_consistency_score(self):
        """
        Returns % of entities that were masked consistently (mapped to exactly 1 value).
        """
        if not self.consistency_tracker: return 1.0
        consistent_entities = sum(1 for v in self.consistency_tracker.values() if len(v) == 1)
        return consistent_entities / len(self.consistency_tracker)

    def measure_privacy_stats(self, dataset: List[Dict], qi_cols: List[str], sensitive_col: str):
        """
        3. GAP FIX: K-Anonymity + L-Diversity
        """
        df = pd.DataFrame(dataset)
        if df.empty: return 0, 0

        # Group by Quasi-Identifiers
        # Fill N/As to avoid grouping errors
        df[qi_cols] = df[qi_cols].fillna('MISSING')
        groups = df.groupby(qi_cols)
        
        # K-Anonymity: Min group size
        min_k = groups.size().min()
        
        # L-Diversity: Min unique sensitive values in any group
        if sensitive_col in df.columns:
            min_l = groups[sensitive_col].nunique().min()
        else:
            min_l = 0
        
        return min_k, min_l

    def measure_statistical_fidelity(self, original_df: pd.DataFrame, masked_df: pd.DataFrame, num_col: str):
        """
        2. GAP FIX: Statistical Fidelity (Mean Shift)
        """
        try:
            # Clean data (remove non-numeric chars for calculation)
            def clean(x): 
                try: return float(str(x).replace('s','').replace('+','')) # Handle "40s"
                except: return None
            
            orig_mean = original_df[num_col].apply(clean).mean()
            mask_mean = masked_df[num_col].apply(clean).mean()
            
            # % Difference
            if orig_mean and orig_mean != 0:
                fidelity_loss = abs(orig_mean - mask_mean) / orig_mean
                return 1.0 - fidelity_loss # Score 0-1 (1 is perfect)
            return 0.0
        except:
            return 0.0

    def record_attack(self, success: bool):
        if success: self.successful_attacks += 1
        self.total_records += 1

    def generate_latex_table(self):
        # Calculate Global F1
        total_tp = sum(c['tp'] for c in self.category_stats.values())
        total_fp = sum(c['fp'] for c in self.category_stats.values())
        total_fn = sum(c['fn'] for c in self.category_stats.values())
        
        precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
        recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        asr = self.successful_attacks / self.total_records if self.total_records > 0 else 0
        consistency = self.calculate_consistency_score()

        latex = r"""
\begin{table}[h]
\centering
\begin{tabular}{|l|c|}
\hline
\textbf{Metric} & \textbf{Value} \\
\hline
Global Precision & """ + f"{precision:.3f}" + r""" \\
Global Recall & """ + f"{recall:.3f}" + r""" \\
Global F1 Score & """ + f"{f1:.3f}" + r""" \\
\hline
Consistency Score & """ + f"{consistency:.3f}" + r""" \\
Adversarial ASR & """ + f"{asr:.3f}" + r""" \\
\hline
\end{tabular}
\caption{Overall System Performance}
\end{table}
"""
        return latex
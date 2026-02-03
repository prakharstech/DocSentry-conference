import pandas as pd
from collections import defaultdict
from typing import List, Dict

class ResearchMetrics:
    def __init__(self):
        self.category_stats = defaultdict(lambda: {'tp': 0, 'fp': 0, 'fn': 0})
        self.total_records = 0
        self.successful_attacks = 0
        self.consistency_tracker = defaultdict(set)

    def update_detection(self, findings: List[dict], ground_truth: List[dict]):
        """
        Updates metrics using FUZZY MATCHING (Overlap).
        """
        # 1. Normalize Detected Items
        detected_items = []
        for f in findings:
            text = f.get('text_segment', '').lower().strip()
            # Map common Scanner variations to standard types
            cat = f.get('pii_type', 'UNKNOWN').upper()
            if cat in ['NAME', 'PATIENT']: cat = 'PERSON'
            if cat in ['ADDRESS', 'CITY']: cat = 'LOCATION'
            detected_items.append({'text': text, 'type': cat, 'matched': False})

        # 2. Normalize Ground Truth Items
        truth_items = []
        for g in ground_truth:
            if isinstance(g, str): # Handle legacy string format
                text = g.lower().strip()
                cat = 'UNKNOWN'
            else:
                text = g.get('text', '').lower().strip()
                cat = g.get('type', 'UNKNOWN').upper()
            truth_items.append({'text': text, 'type': cat, 'matched': False})

        # 3. Fuzzy Match Logic
        for t_item in truth_items:
            for d_item in detected_items:
                # Check Type Match
                if t_item['type'] == d_item['type']:
                    # Check Text Overlap (Is one inside the other?)
                    if (t_item['text'] == d_item['text'] or 
                        t_item['text'] in d_item['text'] or 
                        d_item['text'] in t_item['text']):
                        
                        if not t_item['matched']:
                            # Success!
                            self.category_stats[t_item['type']]['tp'] += 1
                            t_item['matched'] = True
                            d_item['matched'] = True
                            break # Move to next truth item

        # 4. Count Failures
        for t_item in truth_items:
            if not t_item['matched']:
                self.category_stats[t_item['type']]['fn'] += 1 # Missed it

        for d_item in detected_items:
            if not d_item['matched']:
                self.category_stats[d_item['type']]['fp'] += 1 # Hallucination

    def track_consistency(self, mapping: Dict[str, str]):
        for original, masked in mapping.items():
            self.consistency_tracker[original].add(masked)

    def calculate_consistency_score(self):
        if not self.consistency_tracker: return 1.0
        consistent_entities = sum(1 for v in self.consistency_tracker.values() if len(v) == 1)
        return consistent_entities / len(self.consistency_tracker)

    def measure_privacy_stats(self, dataset: List[Dict], qi_cols: List[str], sensitive_col: str):
        df = pd.DataFrame(dataset)
        if df.empty: return 0, 0
        df[qi_cols] = df[qi_cols].fillna('MISSING')
        groups = df.groupby(qi_cols)
        min_k = groups.size().min()
        if sensitive_col in df.columns:
            min_l = groups[sensitive_col].nunique().min()
        else:
            min_l = 0
        return min_k, min_l

    def record_attack(self, success: bool):
        if success: self.successful_attacks += 1
        self.total_records += 1

    def generate_latex_table(self):
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
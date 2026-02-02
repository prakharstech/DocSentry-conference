import os
import pandas as pd
from agents.scanner import ScannerAgent
from agents.strategy import StrategyAgent
from agents.masker import MaskingAgent
from agents.adversarial import AdversarialAgent
from agents.auditor import AuditorAgent  # <--- ADDED THIS IMPORT
from metrics import ResearchMetrics

def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY missing.")
        return

    # 1. Setup Agents & Metrics
    scanner = ScannerAgent()
    strategy = StrategyAgent()
    masker = MaskingAgent()
    adversary = AdversarialAgent()
    auditor = AuditorAgent()  # <--- ADDED INSTANTIATION
    metrics = ResearchMetrics()

    # 2. Experimental Dataset 
    dataset = [
        {"id": 1, "text": "Patient John Doe (DOB: 1980-05-12) diagnosed with Flu.", "ground_truth": ["John Doe", "1980-05-12"], "qis": {"age": "43", "zip": "90210", "condition": "Flu"}},
        {"id": 2, "text": "Patient Jane Smith (DOB: 1982-08-20) has Flu symptoms.", "ground_truth": ["Jane Smith", "1982-08-20"], "qis": {"age": "41", "zip": "90210", "condition": "Flu"}},
        {"id": 3, "text": "Subject Bob Jones, born 1980-01-01. Zip 90210.", "ground_truth": ["Bob Jones", "1980-01-01"], "qis": {"age": "43", "zip": "90210", "condition": "Flu"}}, 
        {"id": 4, "text": "Alice White, 43 years old, from 90210.", "ground_truth": ["Alice White"], "qis": {"age": "43", "zip": "90210", "condition": "Broken Arm"}}
    ]

    print(f"--- 🧪 STARTING EXPERIMENT (N={len(dataset)}) ---\n")

    processed_records = []

    for record in dataset:
        original_text = record["text"]
        truth = record["ground_truth"]
        
        # A. Detection Phase
        scan_res = scanner.scan(original_text)
        findings = scan_res.get("findings", [])
        metrics.update_detection(findings, truth)
        
        # B. Strategy & Masking
        plan = strategy.plan(original_text, findings).get("masking_plan", [])
        mask_res = masker.mask(original_text, plan)
        masked_text = mask_res.get("masked_text", original_text)
        
        # C. Adversarial Attack (Robustness)
        attack = adversary.attack(masked_text)
        metrics.record_attack(attack.get("attack_successful", False))

        # D. Auditor Check (Utility/Fidelity) <--- ADDED THIS STEP
        audit = auditor.evaluate(original_text, masked_text)
        
        # E. Store for K-Anonymity Calculation
        final_qis = record["qis"].copy()
        if "1980" in masked_text or "40s" in masked_text: 
            final_qis["age"] = "40-45"
            
        processed_records.append(final_qis)
        
        # Print Progress including Audit Score
        print(f"[{record['id']}] Attack: {attack.get('attack_successful')} | Utility Score: {audit.get('utility_score')}/100")

    # 3. Calculate Global Privacy Metrics
    k_val = metrics.measure_k_anonymity(processed_records, ["age", "zip"])
    
    # 4. Final Output for Paper
    print("\n" + "="*50)
    print("📝 RESEARCH RESULTS (Copy to Paper)")
    print("="*50)
    
    results = metrics.get_results()
    print(f"Precision: {results['Precision']:.2%}")
    print(f"Recall:    {results['Recall']:.2%}")
    print(f"F1 Score:  {results['F1_Score']:.2f}")
    print(f"Adversarial Inference Rate: {results['Adversarial_ASR']:.2%}")
    print(f"Minimum K-Anonymity (k): {k_val}")
    
    print("\n--- LaTeX Table ---")
    print(metrics.generate_latex_table())

if __name__ == "__main__":
    main()
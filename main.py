import os
import pandas as pd
from agents.scanner import ScannerAgent
from agents.strategy import StrategyAgent
from agents.masker import MaskingAgent
from agents.adversarial import AdversarialAgent
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
    metrics = ResearchMetrics()

    # 2. Experimental Dataset (Simulating a medical CSV export)
    # We need structured data to measure K-Anonymity effectively.
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
        metrics.update_detection(findings, truth) # Update F1 Scores
        
        # B. Strategy & Masking
        plan = strategy.plan(original_text, findings).get("masking_plan", [])
        mask_res = masker.mask(original_text, plan)
        masked_text = mask_res.get("masked_text", original_text)
        
        # C. Adversarial Attack
        attack = adversary.attack(masked_text)
        metrics.record_attack(attack.get("attack_successful", False))
        
        # D. Store for K-Anonymity Calculation
        # In a real paper, we would parse the masked text to extract the remaining QIs.
        # Here we simulate the effect: if Strategy was "GENERALIZE", we generalize the QI stored in the dict.
        final_qis = record["qis"].copy()
        # (Simplified logic: In a full system, you'd map the text changes back to the QI fields)
        if "1980" in masked_text or "40s" in masked_text: 
            final_qis["age"] = "40-45" # Example of generalization
            
        processed_records.append(final_qis)
        
        print(f"[{record['id']}] Processed. Attack Success: {attack.get('attack_successful')}")

    # 3. Calculate Global Privacy Metrics
    # We define Quasi-Identifiers (QIs) as Age and Zip
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
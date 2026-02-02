import os
import time
from agents.scanner import ScannerAgent
from agents.strategy import StrategyAgent
from agents.masker import MaskingAgent
from agents.adversarial import AdversarialAgent
from agents.auditor import AuditorAgent
from agents.generator import DataGeneratorAgent # <--- USES THE NEW GENERATOR
from metrics import ResearchMetrics

def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY missing.")
        return

    # 1. Initialize Agents
    # We use the Generator Agent instead of a hardcoded list
    generator = DataGeneratorAgent() 
    scanner = ScannerAgent()
    strategy = StrategyAgent()
    masker = MaskingAgent()
    adversary = AdversarialAgent()
    auditor = AuditorAgent()
    metrics = ResearchMetrics()

    # 2. Config
    N_SAMPLES = 10  # Change this to 100 or 1000 for a full paper experiment
    print(f"--- 🧪 STARTING INFINITE DATA EXPERIMENT (N={N_SAMPLES}) ---\n")

    masked_data_db = [] # Mimics our "Secure Database" output

    for i in range(1, N_SAMPLES + 1):
        print(f"Generating Record {i}/{N_SAMPLES}...", end="\r")
        
        # A. GENERATE (AI creates unique data + ground truth on the fly)
        record = generator.generate()
        if not record: 
            print(f"Skipping record {i} (Generation failed)")
            continue
        
        text = record.get("text", "")
        ground_truth = record.get("ground_truth", []) # List of Dicts (compatible with new metrics)
        
        # B. SCAN
        findings = scanner.scan(text).get("findings", [])
        metrics.update_detection(findings, ground_truth)
        
        # C. STRATEGIZE & MASK
        plan = strategy.plan(text, findings).get("masking_plan", [])
        mask_res = masker.mask(text, plan)
        masked_text = mask_res.get("masked_text", text)
        
        # Track Consistency
        metrics.track_consistency(mask_res.get("new_mappings", {}))
        
        # D. ADVERSARIAL & AUDIT
        attack = adversary.attack(masked_text)
        metrics.record_attack(attack.get("attack_successful", False))
        
        # Optional: Audit for utility (Log it, but don't stop execution)
        # audit = auditor.evaluate(text, masked_text) 
        
        # E. STORE (For Statistical Fidelity Analysis)
        # We store the original values and the masked result
        masked_data_db.append({
            "age": record.get("qis", {}).get("age"),
            "zip": record.get("qis", {}).get("zip"),
            "condition": record.get("sensitive")
        })
        
        # Print sample to show variety
        print(f"\n[Record {i}]\nOriginal: {text}\nMasked:   {masked_text}")
        
    print("\n\n--- 📊 ANALYSIS COMPLETE ---")
    
    # 3. Calculate Advanced Metrics (K-Anonymity, L-Diversity, Fidelity)
    k, l = metrics.measure_privacy_stats(masked_data_db, ["age", "zip"], "condition")
    
    print("\n=== LATEX TABLE ===")
    print(metrics.generate_latex_table())
    print(f"Min K-Anonymity: {k}")
    print(f"Min L-Diversity: {l}")

if __name__ == "__main__":
    main()
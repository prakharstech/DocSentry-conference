import os
from agents.scanner import ScannerAgent
from agents.masker import MaskingAgent
from agents.auditor import AuditorAgent

def main():
    # 1. Setup
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: Please set OPENAI_API_KEY environment variable.")
        return

    scanner = ScannerAgent()
    masker = MaskingAgent()
    auditor = AuditorAgent()

    # 2. Input Data (Simulating a document)
    document_segments = [
        "My name is Sarah Connor. I live in Los Angeles.",
        "Please send the files to sarah [at] skynet [dot] com.",
        "Later, Sarah met with Kyle Reese at the Techoir club."
    ]

    print("\n--- 🚀 STARTING PII PROTECTION PIPELINE ---\n")

    full_masked_doc = []

    # 3. Process Loop
    for i, segment in enumerate(document_segments):
        print(f"\nProcessing Segment {i+1}/{len(document_segments)}...")
        
        # Step A: Scan
        scan_result = scanner.scan(segment)
        findings = scan_result.get("findings", [])
        
        if findings:
            print(f"   ⚠️  Found {len(findings)} PII entities.")
        else:
            print("   ✅ No PII found.")

        # Step B: Mask (Pass findings + consistency is handled inside agent)
        mask_result = masker.mask(segment, findings)
        masked_text = mask_result.get("masked_text", segment)
        full_masked_doc.append(masked_text)

        # Step C: Audit (Per segment check)
        audit = auditor.evaluate(segment, masked_text)
        print(f"   📊 Scores - Privacy: {audit['privacy_score']}, Utility: {audit['utility_score']}")
        if not audit.get('pass'):
            print(f"   🚨 WARNING: Segment failed audit! {audit.get('critique')}")

    # 4. Final Output
    print("\n" + "="*50)
    print("FINAL CONSISTENT DOCUMENT")
    print("="*50)
    print(" ".join(full_masked_doc))
    print("\nConsistency Map Used:", masker.consistency_map)

if __name__ == "__main__":
    main()
from .base_agent import BaseAgent

class AuditorAgent(BaseAgent):
    SYSTEM_PROMPT = """
    You are a Privacy Auditor. Compare Original vs Masked text.
    
    Score 0-100 on:
    1. Privacy: Did any PII leak? (Strict penalty)
    2. Utility: Is the text still readable? (Grammar/Flow)

    Return JSON:
    {
        "privacy_score": 95,
        "utility_score": 90,
        "pass": true,
        "critique": "short feedback"
    }
    """

    def evaluate(self, original: str, masked: str):
        print("⚖️  Auditor Agent: Scoring results...")
        payload = f"Original: {original}\n\nMasked: {masked}"
        return self.call_llm(self.SYSTEM_PROMPT, payload)
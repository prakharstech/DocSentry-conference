from .base_agent import BaseAgent

class AuditorAgent(BaseAgent):
    SYSTEM_PROMPT = """
    You are a Data Utility & Fidelity Auditor.
    Compare Original vs Masked text.
    
    Analyze for:
    1. Statistical Fidelity: Is the *meaning* preserved? (e.g., "Age 42" -> "40s" is good fidelity; "Age 42" -> "[REDACTED]" is low fidelity).
    2. Information Loss: How much context is gone?
    3. Utility Score: 0-100.

    Return JSON:
    {
        "utility_score": 85,
        "fidelity_rating": "High/Medium/Low",
        "information_loss_critique": "Location generalized to City, preserving regional analytics utility."
    }
    """

    def evaluate(self, original: str, masked: str):
        print("⚖️  Auditor Agent: Calculating Fidelity & Utility...")
        payload = f"Original: {original}\n\nMasked: {masked}"
        return self.call_llm(self.SYSTEM_PROMPT, payload)
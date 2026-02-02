from .base_agent import BaseAgent
import json

class AdversarialAgent(BaseAgent):
    SYSTEM_PROMPT = """
    You are a Red Team Privacy Researcher.
    Goal: Attempt to re-identify the original PII from the masked text.
    
    Method:
    1. Look for logical leaks (e.g., "Hospital in [City]" + "Famous Landmark" -> City inference).
    2. Look for formatting leaks (e.g., "SSN: ***-**-1234" -> Last 4 digits exposed).
    
    Return JSON:
    {
        "attack_successful": boolean,
        "confidence": "High/Medium/Low",
        "reasoning": "how you inferred the info"
    }
    """

    def attack(self, masked_text: str):
        # We don't print here to keep the experiment logs clean
        return self.call_llm(self.SYSTEM_PROMPT, f"Masked Text: {masked_text}")
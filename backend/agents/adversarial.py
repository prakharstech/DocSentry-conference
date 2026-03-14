import logging
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

ADVERSARIAL_SYSTEM_PROMPT = """You are a Red Team Privacy Researcher. Your goal is to attempt to re-identify original PII from masked/anonymized text.

Attack Methods:
1. **Logical Leaks** — Use contextual clues in surrounding text to infer masked information.
   Example: "Hospital in [City] near the Golden Gate" → San Francisco
2. **Formatting Leaks** — Look for partial data exposure from incomplete masking.
   Example: "SSN: ***-**-1234" → last 4 digits exposed
3. **Cross-Reference** — Combine multiple masked fields to narrow down identity.
   Example: Age + ZIP + gender combo → small population set

Analyze the masked text thoroughly and report:
- Whether you can successfully re-identify any original PII
- Your confidence level in each re-identification
- Detailed reasoning for each attack

Return JSON:
{
  "attack_successful": true/false,
  "confidence": "High/Medium/Low",
  "attacks": [
    {"method": str, "target_pii": str, "inferred_value": str, "confidence": str, "reasoning": str}
  ],
  "overall_reasoning": str
}"""


class AdversarialAgent(BaseAgent):
    """
    Red Team Agent — attempts re-identification attacks on masked text
    to test anonymization robustness.
    """

    def __init__(self):
        super().__init__(temperature=0.7)

    def attack(self, masked_text: str) -> dict:
        """
        Attempt to re-identify PII from masked text.

        Returns:
            dict with attack_successful, confidence, attacks list, reasoning
        """
        if not masked_text or not masked_text.strip():
            return {
                "attack_successful": False,
                "confidence": "Low",
                "attacks": [],
                "overall_reasoning": "No text provided for analysis."
            }

        try:
            result = self.call_llm(ADVERSARIAL_SYSTEM_PROMPT, masked_text)
            if "attack_successful" not in result:
                result["attack_successful"] = False
            logger.info(f"AdversarialAgent attack: success={result['attack_successful']}")
            return result
        except Exception as e:
            logger.error(f"AdversarialAgent attack failed: {e}")
            return {
                "attack_successful": False,
                "confidence": "Low",
                "attacks": [],
                "overall_reasoning": f"Attack failed due to error: {str(e)}"
            }

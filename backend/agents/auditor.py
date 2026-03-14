import logging
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

AUDITOR_SYSTEM_PROMPT = """You are a Data Utility & Fidelity Auditor. Your role is to compare original text with its masked/anonymized version and evaluate how much useful information has been preserved.

Evaluate on three dimensions:
1. **Statistical Fidelity** — Are the key facts, numbers, and relationships in the data preserved?
2. **Information Loss** — How much meaningful content was lost or distorted by the masking?
3. **Utility Score** — Overall usability of the masked text for its intended analytical purpose (0-100).

Scoring Rubric:
- 80-100 (High Fidelity): Meaning fully preserved, text remains analytics-ready
- 50-79 (Medium Fidelity): Some context lost but still usable with caveats
- 0-49 (Low Fidelity): Severe information loss, limited analytical value

Return JSON:
{
  "utility_score": int (0-100),
  "fidelity_rating": "High/Medium/Low",
  "statistical_fidelity": str (assessment),
  "information_loss_critique": str (what was lost and impact),
  "recommendations": str (how to improve)
}"""


class AuditorAgent(BaseAgent):
    """
    Data Utility Auditor — evaluates data utility preservation
    after masking by comparing original vs masked text.
    """

    def __init__(self):
        super().__init__(temperature=0.3)

    def audit(self, original_text: str, masked_text: str) -> dict:
        """
        Compare original vs masked text for utility preservation.

        Returns:
            dict with utility_score, fidelity_rating, critiques
        """
        if not original_text or not masked_text:
            return {
                "utility_score": 0,
                "fidelity_rating": "Low",
                "statistical_fidelity": "Cannot assess — missing text.",
                "information_loss_critique": "Missing input.",
                "recommendations": "Provide both original and masked text."
            }

        user_prompt = f"Original:\n{original_text}\n\nMasked:\n{masked_text}"

        try:
            result = self.call_llm(AUDITOR_SYSTEM_PROMPT, user_prompt)
            if "utility_score" not in result:
                result["utility_score"] = 50
            logger.info(f"AuditorAgent: utility_score={result['utility_score']}")
            return result
        except Exception as e:
            logger.error(f"AuditorAgent audit failed: {e}")
            return {
                "utility_score": 0,
                "fidelity_rating": "Low",
                "statistical_fidelity": f"Audit failed: {str(e)}",
                "information_loss_critique": "Error during audit.",
                "recommendations": "Retry the audit."
            }

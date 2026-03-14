import json
import logging
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

MASKER_SYSTEM_PROMPT = """You are a Privacy Masking Agent. Your job is to apply the masking plan to the original text, replacing PII with explicit redaction tags.

Rules:
1. ALWAYS use the REDACT strategy for every piece of detected PII. Do NOT use fake names or synthetic data.
2. Replace the PII string exactly with a bracketed tag matching its entity type. 
   - Example 1: If type is "PERSON", replace with "[PERSON]"
   - Example 2: If type is "LOCATION", replace with "[LOCATION]"
   - Example 3: If type is "DATE", replace with "[DATE]"
3. If an entity exists in the Consistency Map, you MUST reuse that exact replacement.
4. Maintain the original text structure and readability outside of the tags.

Return JSON:
{
  "masked_text": "the full text with all PII replaced by tags like [PERSON]",
  "new_mappings": {"Original PII Value": "[PERSON]", ...}
}"""


class MaskingAgent(BaseAgent):
    """
    Privacy Masking Agent — executes masking plan while maintaining
    cross-document consistency via a consistency map.
    """

    def __init__(self):
        super().__init__(temperature=0.3)
        self.consistency_map: dict = {}

    def mask(self, original_text: str, detected_pii: list, masking_plan: list = None) -> dict:
        """
        Apply masking to the text based on detected PII and optional masking plan.

        Args:
            original_text: Text containing PII
            detected_pii: List of detected PII entities
            masking_plan: Optional masking plan from StrategyAgent

        Returns:
            dict with "masked_text" and "new_mappings"
        """
        if not detected_pii:
            return {"masked_text": original_text, "new_mappings": {}}

        user_prompt = json.dumps({
            "original_text": original_text,
            "detected_pii": detected_pii,
            "masking_plan": masking_plan or [],
            "current_consistency_map": self.consistency_map
        })

        try:
            result = self.call_llm(MASKER_SYSTEM_PROMPT, user_prompt)

            # Update consistency map with new mappings
            if "new_mappings" in result:
                self.consistency_map.update(result["new_mappings"])

            if "masked_text" not in result:
                result["masked_text"] = original_text

            logger.info(f"MaskingAgent applied {len(result.get('new_mappings', {}))} replacements")
            return result
        except Exception as e:
            logger.error(f"MaskingAgent mask failed: {e}")
            return {"masked_text": original_text, "new_mappings": {}}

    def reset_consistency_map(self):
        """Clear the consistency map for a new session."""
        self.consistency_map = {}

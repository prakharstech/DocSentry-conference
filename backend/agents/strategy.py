import json
import logging
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

STRATEGY_SYSTEM_PROMPT = """You are a Privacy Strategy Agent. Your role is to analyze detected PII entities and decide the optimal masking strategy for each one, balancing privacy protection with data utility.

Available strategies:
1. REDACT — Replace with [REDACTED]. Use for high-risk PII: SSNs, exact IDs, critical identifiers.
   Privacy: ★★★ (highest), Utility: ★ (lowest)

2. SYNTHETIC — Replace with realistic synthetic data (fake names, fake numbers). Use for names, entities where referential integrity matters.
   Privacy: ★★, Utility: ★★★ (highest)

3. GENERALIZE — Replace with less specific values (e.g., exact age → age range, city → state). Use for dates, ages, locations when analytics need to be preserved.
   Privacy: ★★, Utility: ★★

Consider the full context when deciding — the same PII type might need different strategies depending on context.

Return JSON: {"masking_plan": [{"target_text": str, "pii_type": str, "strategy": "REDACT|SYNTHETIC|GENERALIZE", "reasoning": str}]}"""


class StrategyAgent(BaseAgent):
    """
    Privacy Strategy Agent — analyzes PII findings and context to decide
    the optimal masking approach per entity (REDACT, SYNTHETIC, GENERALIZE).
    """

    def __init__(self):
        super().__init__(temperature=0.3)

    def plan(self, text: str, findings: list) -> dict:
        """
        Create a masking plan for detected PII.

        Args:
            text: Original text with PII
            findings: List of PII findings from ScannerAgent

        Returns:
            dict with "masking_plan" list
        """
        if not findings:
            return {"masking_plan": []}

        user_prompt = json.dumps({"text": text, "findings": findings})

        try:
            result = self.call_llm(STRATEGY_SYSTEM_PROMPT, user_prompt)
            if "masking_plan" not in result:
                result = {"masking_plan": []}
            logger.info(f"StrategyAgent created plan with {len(result['masking_plan'])} entries")
            return result
        except Exception as e:
            logger.error(f"StrategyAgent plan failed: {e}")
            return {"masking_plan": []}

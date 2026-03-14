import logging
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

SCANNER_SYSTEM_PROMPT = """You are an expert PII Detection Agent. Analyze the provided text carefully and identify ALL Personally Identifiable Information (PII).

Categorize each finding using ONLY these categories:
- PERSON: Patient names, doctor names, any individual names
- LOCATION: Cities, ZIP codes, addresses, countries, states
- DATE: Birthdates, admission dates, any specific dates
- CONDITION: Medical diagnoses, health conditions, symptoms
- CONTACT: Phone numbers, email addresses, fax numbers
- SSN: Social Security Numbers, national IDs, government-issued IDs

For each PII found, provide:
1. The exact text segment containing the PII
2. The PII type (from categories above)
3. Risk level: "Critical" for SSN, "High" for PERSON/CONTACT/CONDITION, "Medium" for LOCATION/DATE
4. Brief reasoning for classification

Return your response as a JSON object with a "findings" array. 
CRITICAL: Use exactly these keys in each finding: "text_segment", "pii_type", "risk_level", "reasoning".
If no PII is found, return: {"findings": []}"""


class ScannerAgent(BaseAgent):
    """
    PII Detection Agent — uses LLM-based NER to detect and classify
    PII entities in unstructured text.
    """

    def __init__(self):
        super().__init__(temperature=0.3)  # Lower temp for consistent detection

    def scan(self, text: str) -> dict:
        """
        Scan text for PII entities.

        Returns:
            dict with "findings" list, each containing:
            - text_segment: str
            - pii_type: str (PERSON|LOCATION|DATE|CONDITION|CONTACT|SSN)
            - risk_level: str (Critical|High|Medium|Low)
            - reasoning: str
        """
        if not text or not text.strip():
            return {"findings": []}

        user_prompt = f"Analyze the following text for PII:\n\n{text}"

        try:
            result = self.call_llm(SCANNER_SYSTEM_PROMPT, user_prompt)
            if "findings" not in result:
                result = {"findings": []}
            logger.info(f"ScannerAgent found {len(result['findings'])} PII entities")
            return result
        except Exception as e:
            logger.error(f"ScannerAgent scan failed: {e}")
            return {"findings": []}

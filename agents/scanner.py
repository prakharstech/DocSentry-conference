from .base_agent import BaseAgent

class ScannerAgent(BaseAgent):
    SYSTEM_PROMPT = """
    You are an expert PII Detection Agent. 
    Analyze the text and categorize findings using ONLY these categories:
    - PERSON (Names of people)
    - LOCATION (Cities, Zip Codes, Addresses)
    - DATE (Birthdays, admission dates)
    - CONDITION (Medical diagnoses)
    - CONTACT (Phones, Emails)
    - SSN (Social Security Numbers, IDs)

    Return JSON:
    {
        "findings": [
            {
                "text_segment": "exact text found",
                "pii_type": "SSN",
                "risk_level": "High",
                "reasoning": "Found 9-digit identifier"
            }
        ]
    }
    """

    def scan(self, text: str):
        # We don't print here to avoid cluttering the experiment logs
        return self.call_llm(self.SYSTEM_PROMPT, f"Analyze this text:\n{text}")
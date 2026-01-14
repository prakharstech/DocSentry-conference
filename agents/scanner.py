from .base_agent import BaseAgent

class ScannerAgent(BaseAgent):
    SYSTEM_PROMPT = """
    You are an expert PII Detection Agent. Analyze the text for:
    1. EXPLICIT PII: Names, emails, phones, SSNs, IPs.
    2. OBFUSCATED PII: "dot com", "five-five-five", spaced out letters.
    3. CONTEXTUAL PII: Specific locations ("hospital on 5th"), rare job titles.

    Return JSON:
    {
        "findings": [
            {
                "text_segment": "exact text found",
                "pii_type": "CATEGORY",
                "risk_level": "High/Medium/Low",
                "reasoning": "brief explanation"
            }
        ]
    }
    """

    def scan(self, text: str):
        print("🕵️  Scanner Agent: Analyzing text...")
        return self.call_llm(self.SYSTEM_PROMPT, f"Analyze this text:\n{text}")
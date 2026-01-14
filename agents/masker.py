import json
from .base_agent import BaseAgent

class MaskingAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        # Memory to store mappings: {"Sarah Connor": "Jane Doe"}
        self.consistency_map = {}

    SYSTEM_PROMPT = """
    You are a Privacy Masking Agent. 
    You will receive:
    1. Original Text
    2. Detected PII List
    3. Existing Consistency Map (previous replacements)

    RULES:
    - If a PII entity exists in the Consistency Map, use that replacement.
    - If it's a NAME, generate a realistic synthetic name (e.g., "John" -> "Michael").
    - If it's a DATE, generalize it.
    - If it's CONTACT INFO, redact or use standard fake data (555-0199).
    
    Return JSON:
    {
        "masked_text": "final text",
        "new_mappings": {"Original Name": "New Name"} 
    }
    """

    def mask(self, text: str, findings: list):
        print("🛡️  Masking Agent: Applying strategies with consistency check...")
        
        payload = json.dumps({
            "original_text": text,
            "detected_pii": findings,
            "current_consistency_map": self.consistency_map
        })

        result = self.call_llm(self.SYSTEM_PROMPT, payload)
        
        # Update our memory with any new mappings the LLM created
        new_map = result.get("new_mappings", {})
        self.consistency_map.update(new_map)
        
        return result
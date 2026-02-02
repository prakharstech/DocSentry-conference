import json
from .base_agent import BaseAgent

class DataGeneratorAgent(BaseAgent):
    SYSTEM_PROMPT = """
    You are a Synthetic Medical Data Generator.
    Generate a SINGLE unique, realistic patient record (1-3 sentences).
    
    VARY THE STYLE:
    - Sometimes formal ("Patient presents with...")
    - Sometimes informal/messy ("saw john today, he has bad flu...")
    - Include noise (typos, abbreviations).
    
    Output JSON ONLY:
    {
        "text": "The generated text",
        "ground_truth": [
            {"text": "John Doe", "type": "PERSON"},
            {"text": "555-0199", "type": "PHONE"}
        ],
        "qis": {"age": 45, "zip": "90210"},
        "sensitive": "Diabetes"
    }
    """

    def generate(self):
        # We ask for a random scenario each time
        return self.call_llm(self.SYSTEM_PROMPT, "Generate one unique record.")
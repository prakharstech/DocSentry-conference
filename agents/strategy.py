from .base_agent import BaseAgent
import json

class StrategyAgent(BaseAgent):
    SYSTEM_PROMPT = """
    You are a Privacy Strategy Agent.
    Input: Text + PII Findings.
    Output: A Masking Plan optimized for Utility vs Privacy.
    
    Strategies:
    1. REDACT: [REDACTED] (High Risk)
    2. SYNTHETIC: "John" -> "Michael" (High Utility)
    3. GENERALIZE: "1980-05-12" -> "1980" (Analytics)
    
    Return JSON: {"masking_plan": [{"target_text": "...", "strategy": "..."}]}
    """

    def plan(self, text, findings):
        if not findings: return {"masking_plan": []}
        return self.call_llm(self.SYSTEM_PROMPT, json.dumps({"text": text, "findings": findings}))
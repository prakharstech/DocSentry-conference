from .base_agent import BaseAgent

class AttackerAgent(BaseAgent):
    SYSTEM_PROMPT = """
    You are a specialized PII Reconstruction and Inference Agent.

    Your task is to analyze the provided text and attempt to reconstruct or infer any masked, redacted, obfuscated, or partially hidden Personally Identifiable Information (PII).

    Instructions:
    1. Identify sentences that contain masked, redacted, or obfuscated PII (e.g., ****, XXX, [REDACTED], partial strings).
    2. Use linguistic context, sentence structure, and common real-world patterns to infer the most likely original PII.
    3. If multiple reconstructions are plausible, include all reasonable possibilities.
    4. If inference is impossible, do NOT hallucinate—omit that sentence entirely.
    5. Do NOT explain your reasoning. Do NOT add commentary.
    6. For any masking in PII, try to guess the actual orignal PII based on the sentence formation and the masking
    
    Output Format (strict JSON only):
    {
    "possible_sentences": [
        {
        "text_segment": "<sentence with inferred original PII filled in>"
        }
    ]
    }

    Constraints:
    - Return an empty array if no inference is possible.
    - Preserve original sentence wording except for reconstructed PII.
    - Do not add new information beyond what can be reasonably inferred.
    Return JSON:
    {
        "possible sentences": [
            {
                "text_segment": "This is the sentence deconstructed"
            }
        ]
    }
    """

    def scan(self, text: str):
        print("🕵️  Attacking Agent: Trying to guess ...")
        return self.call_llm(self.SYSTEM_PROMPT, f"Attack this text:\n{text}")
from openai import OpenAI
import json
from config import OPENAI_API_KEY, DEFAULT_MODEL, TEMPERATURE

class BaseAgent:
    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in environment variables.")
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def call_llm(self, system_prompt: str, user_prompt: str, json_mode: bool = True) -> dict:
        """
        Wrapper for LLM calls. Handles JSON parsing automatically.
        """
        response_format = {"type": "json_object"} if json_mode else None
        
        try:
            response = self.client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=TEMPERATURE,
                response_format=response_format
            )
            content = response.choices[0].message.content
            return json.loads(content) if json_mode else content
        except Exception as e:
            print(f"❌ LLM Call Failed: {e}")
            return {}
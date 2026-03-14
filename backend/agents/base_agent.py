import os
import json
import logging
import time
from groq import Groq

logger = logging.getLogger(__name__)


class BaseAgent:
    """
    Base agent wrapping Groq LLM (llama-3.1-8b-instant) with JSON-mode parsing.
    All LLM-powered agents inherit from this class.
    """

    def __init__(self, model: str = "llama-3.1-8b-instant", temperature: float = 0.7):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables.")
        self.client = Groq(api_key=api_key)
        self.model = model
        self.temperature = temperature

    def call_llm(self, system_prompt: str, user_prompt: str, json_mode: bool = True, retries: int = 3) -> dict | str:
        """
        Call the Groq LLM with a system + user prompt.
        Returns parsed JSON dict if json_mode=True, else raw text string.
        Includes simple exponential backoff for rate limits.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": 4096,
        }

        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        for attempt in range(retries):
            try:
                response = self.client.chat.completions.create(**kwargs)
                content = response.choices[0].message.content

                if json_mode:
                    return json.loads(content)
                return content

            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error: {e}. Raw content: {content}")
                return {"error": f"Failed to parse JSON: {str(e)}", "raw": content}
            except Exception as e:
                if "429" in str(e) and attempt < retries - 1:
                    wait_time = 2 ** (attempt + 1)
                    logger.warning(f"Rate limit hit. Retrying in {wait_time}s... (Attempt {attempt + 1}/{retries})")
                    time.sleep(wait_time)
                    continue
                logger.error(f"LLM call failed: {e}")
                raise

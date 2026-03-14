import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

load_dotenv(dotenv_path="backend/.env")

from agents.base_agent import BaseAgent

def test_llm():
    print("Testing LLM connection...")
    try:
        agent = BaseAgent()
        # Test with a simple prompt that doesn't require JSON mode first to be safe
        response = agent.call_llm(
            system_prompt="You are a helpful assistant.",
            user_prompt="Say 'Connected successfully!'",
            json_mode=False
        )
        print(f"Response: {response}")
        
        print("\nTesting JSON mode...")
        response_json = agent.call_llm(
            system_prompt="Return a JSON object with a key 'status' and value 'success'.",
            user_prompt="What is the status?",
            json_mode=True
        )
        print(f"JSON Response: {response_json}")
        
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_llm()

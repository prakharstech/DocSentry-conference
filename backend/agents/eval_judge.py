import logging
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

EVAL_JUDGE_SYSTEM_PROMPT = """You are an impartial judge evaluating AI-generated responses. Score on two dimensions:

1. **Answer Relevancy** (0-10): Does the response directly address the user's query?
   - 9-10: Fully answers the query with all key points
   - 7-8: Addresses query but misses minor details
   - 4-6: Partially relevant, significant gaps
   - 1-3: Mostly irrelevant to the query
   - 0: Completely off-topic

2. **Groundedness** (0-10): Is every claim in the response supported by the provided context?
   - 9-10: Every claim traceable to context
   - 7-8: Most claims supported, minor inferences
   - 4-6: Mix of supported and unsupported claims
   - 1-3: Mostly hallucinated or unsupported
   - 0: Entirely fabricated

Be strict and fair. Provide detailed reasoning for each score.

Return JSON:
{
  "relevancy_score": float (0-10),
  "groundedness_score": float (0-10),
  "relevancy_reasoning": str,
  "groundedness_reasoning": str
}"""


class EvalJudgeAgent(BaseAgent):
    """
    Evaluation Judge Agent — LLM-as-judge for automated quality
    assessment of RAG responses. Scores relevancy and groundedness.
    """

    def __init__(self):
        super().__init__(temperature=0.1)  # Very low temp for consistent scoring

    def evaluate(self, query: str, response: str, expected_answer: str = "",
                 context_chunks: list[str] = None) -> dict:
        """
        Judge a RAG response on relevancy and groundedness.

        Args:
            query: Original user query
            response: AI-generated response to evaluate
            expected_answer: Optional reference answer for comparison
            context_chunks: List of context strings used to generate the response

        Returns:
            dict with relevancy_score, groundedness_score, and reasoning
        """
        context_str = "\n\n".join(context_chunks) if context_chunks else "No context provided."

        user_prompt = (
            f"Query: {query}\n\n"
            f"AI Response: {response}\n\n"
            f"Expected Answer: {expected_answer or 'Not provided'}\n\n"
            f"Context Chunks Used:\n{context_str}"
        )

        try:
            result = self.call_llm(EVAL_JUDGE_SYSTEM_PROMPT, user_prompt)
            # Ensure scores are floats
            result["relevancy_score"] = float(result.get("relevancy_score", 0))
            result["groundedness_score"] = float(result.get("groundedness_score", 0))
            logger.info(
                f"EvalJudgeAgent: relevancy={result['relevancy_score']}, "
                f"groundedness={result['groundedness_score']}"
            )
            return result
        except Exception as e:
            logger.error(f"EvalJudgeAgent evaluate failed: {e}")
            return {
                "relevancy_score": 0.0,
                "groundedness_score": 0.0,
                "relevancy_reasoning": f"Evaluation failed: {str(e)}",
                "groundedness_reasoning": f"Evaluation failed: {str(e)}"
            }

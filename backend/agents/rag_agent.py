import logging
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

RAG_SYSTEM_PROMPT = """You are a document Q&A assistant powered by DocSentry. Answer the user's question based ONLY on the provided context chunks retrieved from the document store.

Strict Rules:
1. Only use information from the provided context — do not fabricate or assume.
2. If the information is not in the context, clearly state: "The provided documents do not contain information about this."
3. Quote relevant passages when possible to support your answer.
4. Be concise but thorough.
5. Note that the documents have been anonymized — PII has been replaced with placeholders like [PERSON_NAME], [REDACTED_SSN], etc. This is expected behavior.

Format your response clearly with proper structure."""


class RAGAgent(BaseAgent):
    """
    RAG Agent — orchestrates retrieval-augmented generation over
    the anonymized document store. Receives queries, retrieves
    relevant chunks from FAISS, and generates grounded answers.
    """

    def __init__(self):
        super().__init__(temperature=0.3)

    def answer(self, query: str, context_chunks: list[dict]) -> dict:
        """
        Generate a grounded answer using retrieved context chunks.

        Args:
            query: User's question
            context_chunks: List of dicts with 'text', 'doc_id', 'score'

        Returns:
            dict with answer, source_chunks, anonymized flag
        """
        if not context_chunks:
            return {
                "answer": "No documents have been uploaded or no relevant chunks were found.",
                "source_chunks": [],
                "anonymized": True
            }

        # Format context for the prompt
        formatted_context = "\n\n---\n\n".join(
            f"[Chunk {i+1}] (relevance: {c.get('score', 'N/A')}):\n{c['text']}"
            for i, c in enumerate(context_chunks)
        )

        user_prompt = f"Context Chunks:\n{formatted_context}\n\nUser Question: {query}"

        try:
            result = self.call_llm(RAG_SYSTEM_PROMPT, user_prompt, json_mode=False)
            return {
                "answer": result,
                "source_chunks": context_chunks,
                "anonymized": True
            }
        except Exception as e:
            logger.error(f"RAGAgent answer failed: {e}")
            return {
                "answer": f"Failed to generate answer: {str(e)}",
                "source_chunks": context_chunks,
                "anonymized": True
            }

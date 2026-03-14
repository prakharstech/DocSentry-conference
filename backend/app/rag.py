"""RAG pipeline: PDF extraction, chunking, FAISS storage, and retrieval."""

import logging
import numpy as np
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

logger = logging.getLogger(__name__)

# Global embedding model — initialized once
_embeddings = None


def _get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return _embeddings


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract raw text from a PDF file."""
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()
    full_text = "\n\n".join(doc.page_content for doc in documents)
    logger.info(f"Extracted {len(documents)} pages, {len(full_text)} chars")
    return full_text


def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    chunks = splitter.split_text(text)
    logger.info(f"Split text into {len(chunks)} chunks (size={chunk_size}, overlap={chunk_overlap})")
    return chunks


class RAGStore:
    """
    FAISS-backed vector store for anonymized document chunks.
    Supports adding documents and querying with top-K retrieval.
    """

    def __init__(self):
        self.vector_store = None
        self.chunks: list[str] = []
        self.metadata: dict = {}  # Store original PII data for evaluation

    def add_chunks(self, chunks: list[str], doc_id: str = "default"):
        """Add text chunks to the FAISS vector store."""
        embeddings = _get_embeddings()
        texts = chunks
        metadatas = [{"doc_id": doc_id, "chunk_index": i} for i in range(len(chunks))]

        if self.vector_store is None:
            self.vector_store = FAISS.from_texts(texts, embeddings, metadatas=metadatas)
        else:
            self.vector_store.add_texts(texts, metadatas=metadatas)

        self.chunks.extend(chunks)
        logger.info(f"Added {len(chunks)} chunks to FAISS store (doc_id={doc_id})")

    def query(self, query: str, top_k: int = 4) -> list[dict]:
        """
        Query the vector store and return top-K relevant chunks.

        Returns:
            List of dicts with 'text', 'doc_id', 'score'
        """
        if self.vector_store is None:
            return []

        results = self.vector_store.similarity_search_with_score(query, k=top_k)
        chunks = []
        for doc, score in results:
            chunks.append({
                "text": doc.page_content,
                "doc_id": doc.metadata.get("doc_id", "unknown"),
                "chunk_index": doc.metadata.get("chunk_index", -1),
                "score": float(score),
            })

        logger.info(f"Query returned {len(chunks)} chunks")
        return chunks

    def reset(self):
        """Clear the vector store."""
        self.vector_store = None
        self.chunks = []
        self.metadata = {}
        logger.info("RAG store reset")

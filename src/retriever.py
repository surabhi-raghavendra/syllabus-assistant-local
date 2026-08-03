"""
retriever.py
Given a student's question, find the most relevant syllabus chunks.

This is the "R" (Retrieval) in RAG:
question -> embed question -> search vector store -> top matching chunks
"""

from src.embeddings import embed_query
from src.vector_store import VectorStore


def retrieve_relevant_chunks(vector_store: VectorStore, question: str, top_k: int = 5):
    """
    Returns a list of chunk dicts sorted by relevance (most relevant first):
    {"text": ..., "metadata": {"page_number": .., "heading": .., "chunk_id": ..}, "distance": ..}
    """
    query_vector = embed_query(question)
    matches = vector_store.query(query_vector, top_k=top_k)
    return matches


def get_unique_pages(chunks: list[dict]) -> list[int]:
    """Pull out the distinct page numbers referenced by a list of chunks, in order."""
    seen = []
    for chunk in chunks:
        page = chunk["metadata"]["page_number"]
        if page not in seen:
            seen.append(page)
    return seen

"""
llm.py
The "Generation" half of RAG: takes the retrieved text chunks and asks a
LOCAL large language model (served by Ollama, e.g. Llama 3, Mistral, or
Gemma) to answer using ONLY that retrieved content.

Ollama runs entirely on your own machine -- no cloud API, no API key,
no internet needed once the model is downloaded. It exposes a simple
local server at http://localhost:11434.

This is the single place in the project responsible for stopping
hallucination -- the system prompt explicitly forbids using outside
knowledge.
"""

import os
import ollama
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

SYSTEM_PROMPT = (
    "You are a syllabus policy assistant. Answer the user's question only "
    "using the provided syllabus context. Do not use outside knowledge. Do "
    "not guess, assume, or invent policies. If the syllabus context does "
    "not contain enough information to answer the question, clearly say: "
    "\"I couldn't find this information in the uploaded syllabus.\" "
    "Keep answers short and direct -- a sentence or two is usually enough."
)


def _build_context_text(chunks: list[dict]) -> str:
    """Turn retrieved chunks into a labeled context block for the prompt."""
    parts = []
    for chunk in chunks:
        page = chunk["metadata"]["page_number"]
        heading = chunk["metadata"].get("heading", "Untitled Section")
        parts.append(f"[Page {page} - {heading}]\n{chunk['text']}")
    return "\n\n".join(parts)


def _build_sources(chunks: list[dict]) -> list[str]:
    """Build readable 'Page X, Heading' citation strings, de-duplicated."""
    sources = []
    for chunk in chunks:
        page = chunk["metadata"]["page_number"]
        heading = chunk["metadata"].get("heading", "Untitled Section")
        label = f"Page {page}, {heading}"
        if label not in sources:
            sources.append(label)
    return sources


def check_ollama_available(model: str = None) -> tuple[bool, str]:
    """
    Quick health check: is Ollama running, and is the requested model pulled?
    Returns (ok, message) so the UI can show a friendly instruction instead
    of a raw connection error.
    """
    model = model or DEFAULT_MODEL
    try:
        installed = ollama.list()
        names = [m.get("model", m.get("name", "")) for m in installed.get("models", [])]
        if not any(model in n for n in names):
            return False, (
                f"Ollama is running, but the model '{model}' is not pulled yet. "
                f"Run: ollama pull {model}"
            )
        return True, "ok"
    except Exception:
        return False, (
            "Could not reach Ollama. Make sure it is installed and running "
            "(run 'ollama serve' in a terminal, or open the Ollama app)."
        )


def generate_answer(question: str, retrieved_chunks: list[dict], model: str = None):
    """
    Args:
        question: the student's natural-language question
        retrieved_chunks: output of retriever.retrieve_relevant_chunks()
        model: optional Ollama model override (e.g. "mistral", "gemma2")

    Returns a dict:
        {"answer": str, "sources": list[str]}
    """
    if not retrieved_chunks:
        return {
            "answer": "I couldn't find this information in the uploaded syllabus.",
            "sources": [],
        }

    context_text = _build_context_text(retrieved_chunks)
    user_message = f"Syllabus context:\n\n{context_text}\n\nQuestion: {question}"

    response = ollama.chat(
        model=model or DEFAULT_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )

    answer_text = response["message"]["content"].strip()

    return {
        "answer": answer_text,
        "sources": _build_sources(retrieved_chunks),
    }

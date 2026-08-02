"""
embeddings.py
Turns text into vectors (embeddings) so we can do semantic search --
finding chunks that mean the same thing as the question, even if the exact
words are different.

We use a small, well known local model (all-MiniLM-L6-v2) from the
sentence-transformers library. It runs on CPU, needs no API key, and is
downloaded once (cached locally) the first time the app runs.
"""

from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"

_model = None  # loaded once and reused (see get_model)


def get_model() -> SentenceTransformer:
    """Load the embedding model once and reuse it (it's a bit slow to load)."""
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of chunk strings. Returns one vector per input string."""
    if not texts:
        return []
    model = get_model()
    vectors = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    return vectors.tolist()


def embed_query(text: str) -> list[float]:
    """Embed a single question string."""
    return embed_texts([text])[0]

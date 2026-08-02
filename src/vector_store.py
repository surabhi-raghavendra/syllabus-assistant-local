"""
vector_store.py
A thin wrapper around ChromaDB, a simple local vector database.

We always supply our OWN embeddings (computed in embeddings.py) when
adding or querying, so Chroma never needs to download or run its own
embedding model -- it is only used here as a fast, persistent place to
store vectors and search them by similarity.
"""

import shutil
import chromadb


class VectorStore:
    def __init__(self, persist_dir: str = "data/chroma_store", collection_name: str = "syllabus"):
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def reset(self):
        """
        Wipe out any previously uploaded syllabus. Called whenever a
        student uploads a NEW PDF, so old chunks don't leak into new
        answers.
        """
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass  # collection may not exist yet -- that's fine
        self.collection = self.client.get_or_create_collection(name=self.collection_name)

    def add_chunks(self, ids: list[str], texts: list[str], embeddings: list[list[float]], metadatas: list[dict]):
        """Store a batch of chunks with their embeddings and metadata."""
        if not ids:
            return
        self.collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    def query(self, query_embedding: list[float], top_k: int = 5):
        """
        Find the top_k most similar chunks to a query embedding.

        Returns a list of dicts:
        {"text": ..., "metadata": {...}, "distance": 0.12}
        (lower distance = more similar)
        """
        count = self.collection.count()
        if count == 0:
            return []

        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, count),
        )

        matches = []
        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        dists = result.get("distances", [[]])[0]

        for text, meta, dist in zip(docs, metas, dists):
            matches.append({"text": text, "metadata": meta, "distance": dist})
        return matches

    def wipe_disk(self):
        """Completely delete the on-disk store (used by tests / a full reset)."""
        shutil.rmtree(self.persist_dir, ignore_errors=True)

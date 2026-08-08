"""
evaluate.py
A simple, beginner-friendly way to demonstrate that the local RAG pipeline
works. Processes the sample syllabus, runs the 10 test questions from
evaluation/test_questions.json through the real pipeline (local LLM only --
image generation is skipped here to keep evaluation fast and repeatable),
and writes results to evaluation/results.csv.

Run it with:
    python evaluation/evaluate.py

Requires:
- Ollama running locally with a model pulled (see .env for OLLAMA_MODEL)
- The sample syllabus created first: python scripts/create_sample_syllabus.py

How to read the results:
- Retrieval accuracy = how often "page matches expected" is True.
- Answer accuracy = read each generated answer and compare it to the
  expected answer yourself, since this is a small local model, minor
  wording differences are normal.
- Hallucination rate = how many answers state something NOT actually in
  the syllabus (should be 0 -- the last test question exists specifically
  to check this: the correct behaviour is to say the answer isn't there).
"""

import csv
import json
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

from src.pdf_processor import process_pdf
from src.utils import chunk_text
from src.embeddings import embed_texts
from src.vector_store import VectorStore
from src.retriever import retrieve_relevant_chunks
from src.llm import generate_answer, check_ollama_available

load_dotenv()

SAMPLE_PDF = os.path.join("data", "sample_syllabus.pdf")
TEST_QUESTIONS_PATH = os.path.join("evaluation", "test_questions.json")
RESULTS_PATH = os.path.join("evaluation", "results.csv")


def build_index():
    """Process the sample syllabus and load it into a fresh vector store."""
    pages = process_pdf(SAMPLE_PDF, os.path.join("data", "page_images"))

    ids, texts, metadatas = [], [], []
    for page in pages:
        for i, chunk in enumerate(chunk_text(page["text"])):
            ids.append(str(uuid.uuid4()))
            texts.append(chunk)
            metadatas.append({
                "page_number": page["page_number"],
                "heading": page["heading"],
                "chunk_id": i,
            })

    embeddings = embed_texts(texts)
    store = VectorStore(persist_dir=os.path.join("data", "eval_chroma_store"))
    store.reset()
    store.add_chunks(ids, texts, embeddings, metadatas)
    return store


def main():
    ok, msg = check_ollama_available()
    if not ok:
        print(f"ERROR: {msg}")
        return

    if not os.path.exists(SAMPLE_PDF):
        print(f"Sample syllabus not found at {SAMPLE_PDF}.")
        print("Run: python scripts/create_sample_syllabus.py")
        return

    with open(TEST_QUESTIONS_PATH) as f:
        test_questions = json.load(f)

    print("Processing sample syllabus and building the vector index...")
    store = build_index()

    rows = []
    for item in test_questions:
        question = item["question"]
        print(f"\nAsking: {question}")

        chunks = retrieve_relevant_chunks(store, question, top_k=5)
        retrieved_page = chunks[0]["metadata"]["page_number"] if chunks else None

        result = generate_answer(question, chunks)

        page_match = (retrieved_page == item["expected_page"])
        print(f"  Answer: {result['answer']}")
        print(f"  Retrieved page: {retrieved_page} (expected {item['expected_page']}) -> {'MATCH' if page_match else 'CHECK'}")

        rows.append({
            "question": question,
            "expected_answer": item["expected_answer"],
            "expected_page": item["expected_page"],
            "retrieved_page": retrieved_page,
            "page_match": page_match,
            "generated_answer": result["answer"],
            "sources": "; ".join(result["sources"]),
            "grounded_manual_check": "",  # fill this in yourself: yes / no / partial
        })

    os.makedirs("evaluation", exist_ok=True)
    with open(RESULTS_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    matches = sum(1 for r in rows if r["page_match"])
    print(f"\nDone. {matches}/{len(rows)} questions retrieved the expected page.")
    print(f"Full results written to {RESULTS_PATH}")
    print("Open that file and fill in 'grounded_manual_check' for each row while presenting.")


if __name__ == "__main__":
    main()

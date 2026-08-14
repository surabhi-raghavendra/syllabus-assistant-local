"""
app.py
Streamlit front end for the AI-Powered Syllabus Assistant (fully local
version).

Single workflow, in order, every time a question is asked:
1. Retrieve the most relevant syllabus chunks (RAG).
2. Ask a LOCAL LLM (via Ollama) to answer using only those chunks.
3. If the question is about a structured policy (grading, attendance,
   calendar), also generate a summary infographic using a LOCAL image
   model (Stable Diffusion via AUTOMATIC1111's API).
4. Show both the text answer and (when generated) the image together.

No cloud APIs are used anywhere in this app.
"""

import os
import shutil
import uuid

import streamlit as st
from dotenv import load_dotenv

load_dotenv()  # src.llm and src.image_gen also call this defensively,
                # but calling it here too is harmless and explicit

from src.pdf_processor import process_pdf, EmptyPDFError
from src.utils import chunk_text, friendly_error
from src.embeddings import embed_texts
from src.vector_store import VectorStore
from src.retriever import retrieve_relevant_chunks
from src.llm import generate_answer, check_ollama_available, DEFAULT_MODEL as DEFAULT_LLM_MODEL
from src.image_gen import (
    should_generate_image,
    build_image_prompt,
    generate_image,
    create_readable_infographic,
    check_sd_available,
)

DATA_DIR = "data"
IMAGE_DIR = os.path.join("data", "page_images")
OUTPUT_DIR = "outputs"
TOP_K = 5

st.set_page_config(page_title="AI-Powered Syllabus Assistant (Local)", page_icon="📘", layout="centered")


# ---------------------------------------------------------------------------
# Session state setup
# ---------------------------------------------------------------------------
def init_state():
    defaults = {
        "processed": False,
        "filename": None,
        "chat_history": [],   # list of {"question", "answer", "sources", "image_path"}
        "vector_store": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_for_new_upload():
    if st.session_state.vector_store:
        st.session_state.vector_store.reset()
    st.session_state.processed = False
    st.session_state.filename = None
    st.session_state.chat_history = []
    shutil.rmtree(IMAGE_DIR, ignore_errors=True)
    os.makedirs(IMAGE_DIR, exist_ok=True)


init_state()


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("📘 AI-Powered Syllabus Assistant")
st.caption("Upload your syllabus and ask questions about course policies. Runs 100% locally: no cloud APIs.")


# ---------------------------------------------------------------------------
# Local model health checks (fail early with friendly messages)
# ---------------------------------------------------------------------------
with st.expander("🖥️ Local model status", expanded=False):
    llm_ok, llm_msg = check_ollama_available()
    sd_ok, sd_msg = check_sd_available()

    if llm_ok:
        st.success(f"Ollama LLM ready ('{DEFAULT_LLM_MODEL}')")
    else:
        st.error(f"Ollama: {llm_msg}")

    if sd_ok:
        st.success("Stable Diffusion WebUI ready")
    else:
        st.warning(f"Stable Diffusion: {sd_msg}")
        st.caption("Text answers will still work without this. Only image generation needs it.")


# ---------------------------------------------------------------------------
# 1. Upload + process
# ---------------------------------------------------------------------------
uploaded_file = st.file_uploader("Upload your syllabus (PDF)", type=["pdf"])

if uploaded_file is not None and uploaded_file.name != st.session_state.filename:
    process_clicked = st.button("Process Syllabus", type="primary")
    if process_clicked:
        try:
            with st.spinner("Reading your PDF and preparing page images..."):
                os.makedirs(DATA_DIR, exist_ok=True)
                pdf_path = os.path.join(DATA_DIR, uploaded_file.name)
                with open(pdf_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                pages = process_pdf(pdf_path, IMAGE_DIR)

            with st.spinner("Splitting text into chunks and generating embeddings..."):
                ids, texts, metadatas = [], [], []
                for page in pages:
                    chunks = chunk_text(page["text"])
                    for i, chunk in enumerate(chunks):
                        ids.append(str(uuid.uuid4()))
                        texts.append(chunk)
                        metadatas.append({
                            "page_number": page["page_number"],
                            "heading": page["heading"],
                            "chunk_id": i,
                        })

                if not texts:
                    st.error(
                        "No readable text was found in this PDF. It may be a scanned "
                        "document. Try a different file, or a PDF exported directly "
                        "from Word/Google Docs."
                    )
                else:
                    embeddings = embed_texts(texts)

                    store = VectorStore(persist_dir=os.path.join(DATA_DIR, "chroma_store"))
                    store.reset()
                    store.add_chunks(ids, texts, embeddings, metadatas)

                    st.session_state.vector_store = store
                    st.session_state.processed = True
                    st.session_state.filename = uploaded_file.name
                    st.session_state.chat_history = []

            if st.session_state.processed:
                st.success(f"'{uploaded_file.name}' processed successfully! You can now ask questions below.")

        except EmptyPDFError:
            st.error("This PDF appears to be empty. Please upload a valid syllabus file.")
        except Exception as exc:
            st.error(friendly_error(exc))


# ---------------------------------------------------------------------------
# 2. Chat interface (only after a syllabus has been processed)
# ---------------------------------------------------------------------------
if st.session_state.processed:
    st.divider()
    st.subheader(f"Ask about: {st.session_state.filename}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear conversation"):
            st.session_state.chat_history = []
            st.rerun()
    with col2:
        if st.button("📄 Upload a new syllabus"):
            reset_for_new_upload()
            st.rerun()

    # Show past chat turns
    for turn in st.session_state.chat_history:
        with st.chat_message("user"):
            st.write(turn["question"])
        with st.chat_message("assistant"):
            st.write(turn["answer"])
            if turn["sources"]:
                st.caption("Source: " + "; ".join(turn["sources"]))
            if turn.get("image_path"):
                st.image(turn["image_path"], caption="Generated policy visual (local Stable Diffusion)")

    question = st.chat_input("Ask a question about your syllabus...")

    if question:
        with st.chat_message("user"):
            st.write(question)

        with st.chat_message("assistant"):
            image_path = None
            try:
                with st.spinner("Searching your syllabus..."):
                    chunks = retrieve_relevant_chunks(st.session_state.vector_store, question, top_k=TOP_K)

                with st.spinner("Asking the local LLM..."):
                    result = generate_answer(question, chunks)

                st.write(result["answer"])
                if result["sources"]:
                    st.caption("Source: " + "; ".join(result["sources"]))

                                # Single workflow: the same question that produced the text
                # answer also decides whether to generate a visual.
                if should_generate_image(question):
                    sd_ok, sd_msg = check_sd_available()
                    if sd_ok:
                        with st.spinner("Generating a policy visual with local Stable Diffusion..."):
                            image_prompt = build_image_prompt(question, chunks)

                            background_path = generate_image(
                                image_prompt,
                                output_dir=OUTPUT_DIR
                            )

                            if background_path:
                                image_path = create_readable_infographic(
                                    background_path=background_path,
                                    question=question,
                                    answer=result["answer"],
                                    output_dir=OUTPUT_DIR
                                )

                        if image_path:
                            st.image(
                                image_path,
                                caption="Generated policy visual (local Stable Diffusion + local formatting)"
                            )
                    else:
                        st.caption(f"(Image generation skipped: {sd_msg})")

                st.session_state.chat_history.append({
                    "question": question,
                    "answer": result["answer"],
                    "sources": result["sources"],
                    "image_path": image_path,
                })
            except Exception as exc:
                friendly = friendly_error(exc)
                st.error(friendly)
                st.session_state.chat_history.append({
                    "question": question,
                    "answer": friendly,
                    "sources": [],
                    "image_path": None,
                })
else:
    st.info("Upload and process a syllabus PDF to start asking questions.")

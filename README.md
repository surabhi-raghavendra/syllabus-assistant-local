# AI-Powered Syllabus Assistant

A fully local AI application designed to help university students quickly find and understand information from syllabus documents.

The application combines Retrieval-Augmented Generation (RAG), Llama 3 through Ollama, and Stable Diffusion through AUTOMATIC1111. No cloud AI APIs are used.

---

## Problem Statement

University syllabi contain important information about grading schemes, attendance requirements, assessment structures, examination policies, and academic calendars. Finding specific information manually in lengthy PDF documents can be time-consuming.

The AI-Powered Syllabus Assistant allows students to upload a syllabus PDF and ask questions in natural language. Relevant syllabus sections are retrieved and provided to a locally hosted Llama 3 model for answer generation.

For structured academic policy questions, the system also generates a visual summary using a locally hosted Stable Diffusion model.

---

## Features

- Upload and process university syllabus PDFs
- Semantic search using embeddings and ChromaDB
- Local Llama 3 text generation through Ollama
- Source-aware answers based on syllabus content
- Local Stable Diffusion image generation
- Topic-specific visuals for:
  - Grading schemes
  - Attendance policies
  - Assessment structures
  - Academic calendars
  - Makeup/retest policies
- Streamlit conversational interface
- Fully local processing with no cloud AI APIs

---

## Architecture
![System Architecture](docs/architecture.png)

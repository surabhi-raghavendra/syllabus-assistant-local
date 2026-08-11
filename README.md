# AI-Powered Syllabus Assistant (Local Edition)

Upload your course syllabus PDF and ask questions about attendance,
grading, CIA exams, makeup exams, and academic calendars. The assistant
answers **only** from your uploaded syllabus, cites the exact page it
came from, and generates a visual summary poster for structural policies
(grading tables, attendance rules, exam calendars) — using **entirely
local AI models**. No cloud APIs are used anywhere in this project.

---

## 1. Problem Statement

Every semester, students ask the same policy questions over and over —
"How much attendance do I need?", "What's the CIA weightage?", "Can I
write a makeup exam?" — because syllabi are long, dense, and hard to
search. Faculty and department offices end up repeating the same answers
instead of doing academic work, and answers can be inconsistent between
staff members.

This project solves that with a syllabus-grounded RAG assistant that:
- answers instantly and only from the actual uploaded document (no
  hallucinated policies)
- cites the exact page and section for every answer
- turns structural policies (grading weightage, attendance thresholds,
  exam calendars) into a quick visual summary, generated locally
- runs completely offline after setup, with no per-question cost and no
  data leaving the machine

## 2. Features

- 📄 **PDF upload & processing** — extracts text and renders each page
  as an image
- 🔍 **Retrieval-Augmented Generation (RAG)** — semantic search over
  syllabus chunks using local embeddings + ChromaDB
- 🧠 **Local LLM answers** — powered by [Ollama](https://ollama.com)
  (Llama 3, Mistral, or Gemma — your choice), strictly grounded in the
  retrieved syllabus content
- 🎨 **Local image generation** — for questions about grading, attendance,
  or calendars, a summary infographic is generated with a local Stable
  Diffusion model via the AUTOMATIC1111 WebUI API
- 📌 **Citations** — every answer shows the page number and section
  heading it came from
- 🚫 **Refuses to guess** — if the syllabus doesn't contain the answer,
  the assistant says so instead of making something up
- 💬 **Simple chat interface** — built with Streamlit, no separate
  frontend needed
- 🔒 **100% local & free** — no API keys, no cloud services, no
  per-request cost

## 3. Architecture

![Architecture diagram](docs/architecture.png)

**Text path (RAG):**
```
Syllabus PDF → text extraction → chunking → local embeddings → ChromaDB
                                                                    │
Question → embed → semantic search → top chunks → Ollama (local LLM)
                                                        │
                                              Grounded text answer + citation
```

**Image path (multimodal generation, same workflow):**
```
Question (grading / attendance / calendar) → build image prompt from
retrieved section headings → Stable Diffusion WebUI (local) → summary
infographic → shown alongside the text answer
```

See [`docs/workflow.png`](docs/workflow.png) for the full 8-step,
single-workflow diagram from upload to displayed result.

### Why these tools

| Piece | Choice | Why |
|---|---|---|
| Frontend | Streamlit | Simple, pure Python, no separate build step |
| PDF processing | PyMuPDF | Extracts text AND renders page images, no extra binaries |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) | Small, fully local, no API key |
| Vector database | ChromaDB (local, persistent) | Zero setup, stores metadata alongside vectors |
| Local LLM | Ollama (Llama 3 / Mistral / Gemma) | Simple local server, easy model swapping, no cloud cost |
| Local image generation | Stable Diffusion via AUTOMATIC1111 WebUI | Well documented REST API, widely used, one flag (`--api`) to enable |

## 4. Repository Structure

```
Repository(Reg. No)/
│
├── README.md
├── LICENSE
├── .gitignore
├── requirements.txt
├── app.py                      ← Streamlit app (the whole UI + pipeline glue)
├── src/
│   ├── pdf_processor.py         ← PDF -> text + page images
│   ├── utils.py                  ← chunking, heading detection, friendly errors
│   ├── embeddings.py             ← local text -> vector embeddings
│   ├── vector_store.py           ← ChromaDB wrapper
│   ├── retriever.py              ← question -> relevant chunks
│   ├── llm.py                     ← local Ollama client (text answers)
│   └── image_gen.py               ← local Stable Diffusion client (visuals)
├── scripts/
│   ├── create_sample_syllabus.py  ← generates a test PDF with a real table
│   ├── make_architecture_diagram.py
│   └── make_workflow_diagram.py
├── evaluation/
│   ├── test_questions.json        ← 10 test questions with expected answers
│   └── evaluate.py                 ← runs the test set, writes results.csv
├── docs/
│   ├── architecture.png
│   ├── workflow.png
│   └── screenshots/
├── models/                         ← notes on which local models this was tested with
├── data/                            ← uploaded PDFs + local vector DB (generated at runtime)
├── outputs/                         ← generated policy visuals (generated at runtime)
└── demo/
    └── demo.mp4                     ← short demo recording
```

## 5. Installation

### Step 1 — Install and start Ollama (local LLM)

1. Download and install Ollama from [ollama.com](https://ollama.com)
2. Pull a model (any one of these works):
   ```bash
   ollama pull llama3
   # or: ollama pull mistral
   # or: ollama pull gemma2
   ```
3. Ollama runs automatically as a background service on
   `http://localhost:11434` after install. If it's not running, start it
   with:
   ```bash
   ollama serve
   ```

### Step 2 — Install and start Stable Diffusion WebUI (local image generation)

1. Clone AUTOMATIC1111's WebUI:
   ```bash
   git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui
   cd stable-diffusion-webui
   ```
2. Start it **with the API enabled**:
   ```bash
   ./webui.sh --api          # Mac/Linux
   webui-user.bat --api      # Windows (add --api to COMMANDLINE_ARGS)
   ```
3. The first run downloads a default model automatically and can take a
   while. Once ready, it serves the API at `http://127.0.0.1:7860`.
4. Leave this running in its own terminal window.

### Step 3 — Set up this project

```bash
git clone <this-repository-url>
cd syllabus-assistant-local

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# open .env if you want to change the default model names or ports
```

**Note:** `sentence-transformers` depends on PyTorch. The first
`pip install` may take a few minutes. The first time you run the app, it
also downloads the embedding model (~90 MB) once, then works offline.

## 6. Running the App

Make sure Ollama and Stable Diffusion WebUI (Steps 1–2 above) are both
running in their own terminals, then:

```bash
streamlit run app.py
```

This opens the app at `http://localhost:8501`. The app shows a
"Local model status" panel at the top so you can confirm both services
are reachable before uploading a syllabus.

## 7. Usage / Testing Workflow

No syllabus on hand yet? Generate a sample one with a real table:

```bash
python scripts/create_sample_syllabus.py
```

This creates `data/sample_syllabus.pdf` (6 pages: Course Overview,
Attendance Policy, Assessment Structure, Makeup Exam Policy, Academic
Calendar, Grading Scheme). Upload it in the app, click **Process
Syllabus**, and try the sample questions below.

### Sample questions to demo

1. What is the minimum attendance requirement?
2. How much is CIA 1 worth? *(triggers image generation — grading topic)*
3. How many marks is the end semester examination?
4. Can I write a makeup exam if I miss a CIA?
5. What happens if I miss two CIA exams?
6. When is the end semester examination? *(triggers image generation — calendar topic)*
7. What is the grading scheme? *(triggers image generation — grading topic)*
8. What score do I need for an A grade?
9. Can students below 65% attendance write the final exam? *(triggers image generation — attendance topic)*
10. Who teaches the ethics module? *(not in the syllabus — the assistant
    should say it can't find this, proving it doesn't hallucinate)*

## 8. Screenshots

See [`docs/screenshots/`](docs/screenshots/) for:
- Upload & processing screen
- A text-only answer with citation
- A question that triggers both the text answer and the generated image
- The "information not found" response (question 10 above)

## 9. Demo Video

See [`demo/demo.mp4`](demo/demo.mp4) for a short walkthrough: upload a
syllabus, ask a text question, ask a question that generates an image,
and ask a question with no answer in the document.

## 10. How the RAG Pipeline Works

1. **Upload** — student uploads a PDF.
2. **Extraction** — every page's text is pulled out, and each page is
   also saved as an image.
3. **Chunking** — long page text is split into overlapping ~800-character
   pieces so retrieval can find one specific sentence, not an entire page.
4. **Embedding** — each chunk becomes a vector using a local embedding
   model (`all-MiniLM-L6-v2`).
5. **Storage** — vectors + text + metadata (page number, heading) are
   stored in ChromaDB.
6. **Retrieval** — the question is embedded the same way and matched
   against stored chunks.
7. **Generation** — the retrieved chunks are handed to the local LLM
   (Ollama) with a strict instruction: answer only from this content, or
   say it isn't there.
8. **Citation** — the page number and heading are shown with the answer.

## 11. How the Image Generation Component Works

Some syllabus questions are about **structured** content — grading
weightage, attendance thresholds, exam dates — that reads better as a
visual than a sentence. `src/image_gen.py` checks the question for
keywords like "table", "%", "grading", "calendar", "attendance". If
matched:

1. The section headings of the retrieved chunks (e.g. "Assessment
   Structure") become the topic of an image prompt.
2. The prompt asks for a clean, minimalist infographic-style poster
   about that topic (not realistic photos, not exact numbers — image
   models can't reliably render small text, so the precise figures stay
   in the LLM's text answer).
3. The prompt is sent to the local Stable Diffusion WebUI API
   (`/sdapi/v1/txt2img`), which returns a base64-encoded image.
4. The image is saved to `outputs/` and shown next to the text answer in
   the same chat turn — this is the "single workflow" requirement: one
   question, one pipeline, both text and image generation triggered from
   the same retrieval step.

## 12. Common Errors and Fixes

| Problem | Likely cause | Fix |
|---|---|---|
| "Could not reach Ollama" | Ollama isn't running | Run `ollama serve`, or open the Ollama desktop app |
| "model is not pulled yet" | Model name in `.env` doesn't match an installed model | Run `ollama pull <model-name>` |
| "Could not reach the Stable Diffusion WebUI API" | WebUI not running, or started without `--api` | Restart it with the `--api` flag |
| Image generation is slow | Normal on CPU-only machines | Lower `SD_STEPS` in `.env`, or use a smaller image size |
| App says PDF has no readable text | Scanned/image-only PDF | Use a text-based PDF (exported from Word/Google Docs) |
| Answers seem generic / not from the PDF | Question asked before processing finished | Wait for the "processed successfully" message |
| First run is slow | Embedding model + PyTorch downloading | Normal on first run only; later runs use the local cache |

## 13. Evaluation

See `evaluation/evaluate.py`. It runs the 10 test questions in
`evaluation/test_questions.json` through the real local pipeline (text
answers only, to keep evaluation fast and repeatable) and writes
`evaluation/results.csv` with the question, expected answer, retrieved
page, generated answer, and whether the retrieved page matched what was
expected. Use that file to report:

- **Retrieval accuracy** — % of questions where the correct page was retrieved
- **Answer accuracy** — compare each generated answer to the expected one
- **Hallucination rate** — how many answers state something not actually
  in the syllabus (should be 0; test question 10 checks this directly)

## 14. Models Used

See [`models/NOTES.md`](models/NOTES.md) for the exact local model names
and versions this project was tested with.

## 15. Future Scope

- Multi-language question support
- Voice input
- OCR for fully scanned syllabi
- Direct integration with the college portal
- Caching generated images per syllabus so repeat questions don't
  regenerate the same visual

## 16. License

This project is licensed under the MIT License — see [`LICENSE`](LICENSE).

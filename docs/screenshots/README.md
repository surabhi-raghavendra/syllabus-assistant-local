# Screenshots

This folder is intentionally empty in the delivered project. Screenshots
need to come from an actual run of the app on your machine (with Ollama
and Stable Diffusion WebUI running), since this project was built in a
sandbox with no GPU and no internet access to download model weights —
so no real screenshots could be captured here.

## What to capture (matches the README's "Sample questions to demo")

1. **`01_upload.png`** — the upload screen, right after clicking
   "Process Syllabus", showing the success message.
2. **`02_text_answer.png`** — a text-only question and answer, e.g.
   *"Can I write a makeup exam if I miss a CIA?"*, with the page
   citation visible.
3. **`03_text_and_image.png`** — a question that triggers image
   generation, e.g. *"What is the grading scheme?"*, showing both the
   text answer and the generated infographic in the same chat turn.
4. **`04_not_found.png`** — the "information not found" response for
   *"Who teaches the ethics module?"* — this is the most important one
   to include, since it proves the assistant doesn't hallucinate.
5. **`05_local_status.png`** — the "Local model status" expander at the
   top of the app, showing both Ollama and Stable Diffusion WebUI as
   reachable.

## How to capture them

1. Run the app normally (`streamlit run app.py`).
2. Use your OS's screenshot tool (Windows: `Win+Shift+S`, Mac:
   `Cmd+Shift+4`) to capture the browser window for each step above.
3. Save them into this folder using the filenames above.
4. Reference them in the main `README.md` if you want them inlined,
   e.g. `![Text answer](docs/screenshots/02_text_answer.png)`.

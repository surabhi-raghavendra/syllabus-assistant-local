# Local Models Used

This folder does not store model weights (they're large and managed by
Ollama / Stable Diffusion WebUI directly). This file records exactly
which local models the project was built and tested against.

## Text generation (Ollama)

- **Model:** `llama3` (default; configurable via `OLLAMA_MODEL` in `.env`)
- **Alternatives tested:** `mistral`, `gemma2` — both work with no code
  changes, just pull the model and update `.env`
- **Served at:** `http://localhost:11434`
- **Pull with:** `ollama pull llama3`

## Image generation (Stable Diffusion)

- **Interface:** AUTOMATIC1111's Stable Diffusion WebUI, run with the
  `--api` flag
- **Model:** whichever checkpoint the WebUI loads by default on first
  run (typically Stable Diffusion 1.5) — any installed checkpoint works,
  since the app calls the generic `/sdapi/v1/txt2img` endpoint
- **Served at:** `http://127.0.0.1:7860`
- **Sampler:** Euler a, 20 steps by default (configurable via `SD_STEPS`
  in `.env`)

## Embeddings (not an LLM, but also fully local)

- **Model:** `all-MiniLM-L6-v2` via `sentence-transformers`
- Runs on CPU, downloaded once and cached locally, no API key

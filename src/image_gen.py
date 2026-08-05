"""
image_gen.py
The "image generation" half of the workflow. When a student asks about a
structured policy -- grading weightage, attendance rules, the academic
calendar -- this module turns the retrieved syllabus text into a prompt
for a LOCAL Stable Diffusion model, and asks it to draw a clean summary
poster/infographic of that policy.

This talks to AUTOMATIC1111's Stable Diffusion WebUI, which must be
running locally with its API enabled (start it with the --api flag).
It exposes a REST API at http://127.0.0.1:7860 -- no cloud service,
no API key.
"""

import base64
import os
import time

import requests
from dotenv import load_dotenv

from src.utils import needs_multimodal

load_dotenv()

SD_URL = os.getenv("SD_WEBUI_URL", "http://127.0.0.1:7860")
DEFAULT_STEPS = int(os.getenv("SD_STEPS", "20"))
NEGATIVE_PROMPT = "blurry, distorted text, extra digits, watermark, low quality"


def should_generate_image(question: str) -> bool:
    """
    Decide whether this question is about a structured policy that would
    benefit from a visual summary (grading tables, attendance %, exam
    calendars), rather than a simple yes/no policy question.
    """
    return needs_multimodal(question)


def build_image_prompt(question: str, retrieved_chunks: list[dict]) -> str:
    """
    Turn the retrieved syllabus text into a short, descriptive prompt for
    Stable Diffusion. We keep this simple and readable for a viva: we are
    not asking the model to draw the exact numbers (image models cannot
    render small text reliably) -- we ask for a clean, poster-style
    infographic representing the topic, which is paired with the LLM's
    exact text answer in the UI.
    """
    headings = []
    for chunk in retrieved_chunks:
        heading = chunk["metadata"].get("heading", "")
        if heading and heading not in headings:
            headings.append(heading)
    topic = ", ".join(headings) if headings else question

    return (
        f"a clean minimalist infographic poster about '{topic}' for a university course syllabus, "
        "flat design, simple icons, organized layout, soft color palette, "
        "professional academic style, no realistic photos"
    )


def check_sd_available() -> tuple[bool, str]:
    """
    Quick health check: is the Stable Diffusion WebUI API reachable?
    Returns (ok, message) for a friendly UI message instead of a raw
    connection error.
    """
    try:
        response = requests.get(f"{SD_URL}/sdapi/v1/sd-models", timeout=5)
        if response.status_code == 200:
            return True, "ok"
        return False, f"Stable Diffusion WebUI responded with status {response.status_code}."
    except requests.exceptions.RequestException:
        return False, (
            "Could not reach the Stable Diffusion WebUI API. Make sure it is "
            "running with the --api flag (e.g. webui-user.bat/.sh --api)."
        )


def generate_image(prompt: str, output_dir: str = "outputs", width: int = 512, height: int = 512):
    """
    Calls AUTOMATIC1111's txt2img endpoint and saves the returned image to
    disk.

    Returns the saved image path, or None if generation failed.
    """
    payload = {
        "prompt": prompt,
        "negative_prompt": NEGATIVE_PROMPT,
        "steps": DEFAULT_STEPS,
        "width": width,
        "height": height,
        "cfg_scale": 7,
        "sampler_name": "Euler a",
    }

    try:
        response = requests.post(f"{SD_URL}/sdapi/v1/txt2img", json=payload, timeout=180)
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        raise ConnectionError(f"Stable Diffusion WebUI request failed: {exc}")

    result = response.json()
    images = result.get("images", [])
    if not images:
        return None

    os.makedirs(output_dir, exist_ok=True)
    filename = f"policy_visual_{int(time.time())}.png"
    output_path = os.path.join(output_dir, filename)

    with open(output_path, "wb") as f:
        f.write(base64.b64decode(images[0]))

    return output_path

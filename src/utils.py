"""
utils.py
Small helper functions used across the project:
- splitting page text into overlapping chunks
- guessing a section heading for a page
- deciding when a question likely needs the page IMAGE (tables, calendars, etc.)
- turning exceptions into friendly, student-readable messages
"""

import re

# Keywords that usually mean the answer lives in a table / structured layout
# rather than plain sentences. If a question or a chunk contains any of these,
# we also send the page IMAGE to the model, not just the extracted text.
MULTIMODAL_KEYWORDS = [
    "table", "grading", "grade", "weightage", "weight", "percentage", "%",
    "attendance", "calendar", "schedule", "timetable", "cia", "marks",
    "exam pattern", "assessment structure", "dates", "credit", "credits",
]


def clean_text(text: str) -> str:
    """Collapse extra whitespace / blank lines so chunks look tidy."""
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def guess_section_heading(page_text: str) -> str:
    """
    Very simple heuristic: the first short, non-empty line of a page is
    usually its heading (e.g. 'Attendance Policy', 'Assessment Structure').
    This is not perfect, but it is good enough for a student project and
    makes citations far more readable than just a page number.
    """
    lines = [ln.strip() for ln in page_text.split("\n") if ln.strip()]
    if not lines:
        return "Untitled Section"

    first_line = lines[0]
    # Headings are usually short and don't end like a normal sentence.
    if len(first_line) <= 70 and not first_line.endswith((".", ",")):
        return first_line
    return "Untitled Section"


def chunk_text(page_text: str, chunk_size: int = 800, overlap: int = 120):
    """
    Split one page's text into overlapping chunks so that retrieval can
    find a specific policy sentence without pulling in the whole page.

    chunk_size and overlap are measured in characters (simple and easy to
    explain in a viva -- no tokenizer needed).

    Returns a list of plain strings.
    """
    text = clean_text(page_text)
    if not text:
        return []

    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk.strip())
        if end >= len(text):
            break
        start = end - overlap  # step back a little so context isn't cut off
    return [c for c in chunks if c]


def needs_multimodal(text: str) -> bool:
    """
    Returns True if the given text (a question OR a chunk/heading) suggests
    the answer depends on a table, grading scheme, calendar, or other
    visually structured content -- in which case we should also look at the
    page IMAGE, not just the extracted text.
    """
    lowered = text.lower()
    return any(keyword in lowered for keyword in MULTIMODAL_KEYWORDS)


def friendly_error(exc: Exception) -> str:
    """
    Convert a raw exception into a short, non-technical message that is
    safe to show a student in the Streamlit UI, instead of a scary
    Python traceback. This app talks to LOCAL services only (Ollama and
    Stable Diffusion WebUI), so most errors here are "service not running"
    style errors rather than cloud auth/rate-limit errors.
    """
    message = str(exc).lower()

    if "connection" in message or "refused" in message or "timeout" in message:
        return (
            "Could not reach a local AI service. Make sure Ollama is running "
            "('ollama serve') and, if you asked for a visual, that the "
            "Stable Diffusion WebUI is running with the --api flag."
        )
    if "model" in message and ("not found" in message or "pull" in message):
        return (
            "The requested local model isn't downloaded yet. Run "
            "'ollama pull <model-name>' in a terminal and try again."
        )
    if "no pages" in message or "empty" in message:
        return "This PDF does not seem to contain any readable pages. Please try a different file."
    if "not a pdf" in message or "cannot open" in message or "damaged" in message:
        return "This file could not be opened as a PDF. Please upload a valid .pdf file."

    # Fallback -- still friendly, but keeps the real reason for debugging.
    return f"Something went wrong while processing your request ({exc})."

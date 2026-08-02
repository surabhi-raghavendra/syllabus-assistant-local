"""
pdf_processor.py
Turns an uploaded syllabus PDF into two things, per page:
1. Extracted text (for fast semantic / text search)
2. A rendered PNG image of the page (for the vision LLM to read tables,
   grading schemes, calendars, and other layouts that plain text extraction
   often scrambles)

Uses PyMuPDF (imported as `fitz`), which needs no external system binaries.
"""

import os
import pymupdf as fitz  # PyMuPDF (the "fitz" import name is deprecated)

from src.utils import guess_section_heading


class EmptyPDFError(Exception):
    """Raised when a PDF has zero pages or no extractable text anywhere."""
    pass


def process_pdf(pdf_path: str, image_output_dir: str, dpi: int = 150):
    """
    Process every page of a PDF.

    Args:
        pdf_path: path to the uploaded PDF file on disk
        image_output_dir: folder where page images will be saved
        dpi: resolution used when rendering each page to an image

    Returns:
        A list of dicts, one per page:
        {
            "page_number": 1,
            "text": "...",
            "heading": "Attendance Policy",
            "image_path": "page_images/page_1.png",
        }
    """
    os.makedirs(image_output_dir, exist_ok=True)

    try:
        doc = fitz.open(pdf_path)
    except Exception as exc:
        raise ValueError(f"cannot open: {exc}")

    if doc.page_count == 0:
        raise EmptyPDFError("no pages found in this PDF")

    pages = []
    any_text_found = False

    for i, page in enumerate(doc):
        page_number = i + 1

        # 1. Extract plain text
        text = page.get_text("text") or ""
        if text.strip():
            any_text_found = True

        # 2. Render the page as an image (used for tables / layouts)
        pix = page.get_pixmap(dpi=dpi)
        image_path = os.path.join(image_output_dir, f"page_{page_number}.png")
        pix.save(image_path)

        pages.append({
            "page_number": page_number,
            "text": text,
            "heading": guess_section_heading(text),
            "image_path": image_path,
        })

    doc.close()

    if not any_text_found:
        # We still keep the page images (a scanned syllabus can sometimes
        # still be answered from the images alone), but we warn the caller
        # so the UI can tell the student text-based search will be limited.
        for p in pages:
            p["text_extraction_failed"] = True

    return pages

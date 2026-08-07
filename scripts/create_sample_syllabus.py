"""
create_sample_syllabus.py
Generates a small, realistic sample syllabus PDF so you can test the
assistant without needing your own course PDF first.

Run it with:
    python scripts/create_sample_syllabus.py

It creates: data/sample_syllabus.pdf (6 pages), including a real drawn
table for the assessment structure -- useful for testing the multimodal
(page-image) part of the pipeline, since a drawn table is exactly the
kind of layout that plain text extraction struggles with.
"""

import os
import pymupdf as fitz  # PyMuPDF (the "fitz" import name is deprecated)

OUTPUT_PATH = os.path.join("data", "sample_syllabus.pdf")
PAGE_SIZE = (595, 842)  # A4 in points


def add_text_page(doc, heading, body_lines):
    page = doc.new_page(width=PAGE_SIZE[0], height=PAGE_SIZE[1])
    page.insert_text((50, 60), heading, fontsize=16, fontname="helv", color=(0, 0, 0))
    y = 100
    for line in body_lines:
        page.insert_text((50, y), line, fontsize=11, fontname="helv", color=(0.15, 0.15, 0.15))
        y += 22
    return page


def add_table_page(doc, heading, rows, col_widths=(260, 260)):
    """Draws a simple 2-column table using rectangles + text (a real visual table,
    not just text), so the multimodal path has something meaningful to read."""
    page = doc.new_page(width=PAGE_SIZE[0], height=PAGE_SIZE[1])
    page.insert_text((50, 60), heading, fontsize=16, fontname="helv", color=(0, 0, 0))

    x0, y0 = 50, 100
    row_height = 32
    for i, (col1, col2) in enumerate(rows):
        y = y0 + i * row_height
        rect = fitz.Rect(x0, y, x0 + col_widths[0] + col_widths[1], y + row_height)
        page.draw_rect(rect, color=(0, 0, 0), width=0.7)
        page.draw_line((x0 + col_widths[0], y), (x0 + col_widths[0], y + row_height), color=(0, 0, 0), width=0.7)
        page.insert_text((x0 + 10, y + 21), col1, fontsize=11, fontname="helv", color=(0, 0, 0))
        page.insert_text((x0 + col_widths[0] + 10, y + 21), col2, fontsize=11, fontname="helv", color=(0, 0, 0))
    return page


def build():
    os.makedirs("data", exist_ok=True)
    doc = fitz.open()

    add_text_page(doc, "Course Overview", [
        "Course: Data Analytics Fundamentals",
        "Program: MSc Data Analytics",
        "Credits: 4",
        "",
        "This course introduces core statistical and machine learning",
        "concepts used in data analytics, with an emphasis on applied",
        "problem solving using real datasets.",
    ])

    add_text_page(doc, "Attendance Policy", [
        "Minimum attendance required to appear for the End Semester",
        "Examination is 75%.",
        "",
        "Students with attendance between 65% and 74% may be granted",
        "condonation only with valid medical documentation submitted",
        "within one week of resuming class.",
        "",
        "Students below 65% attendance will not be permitted to write",
        "the End Semester Examination.",
    ])

    add_table_page(doc, "Assessment Structure", [
        ("Component", "Weightage"),
        ("CIA 1", "20%"),
        ("CIA 2", "20%"),
        ("Assignment", "10%"),
        ("End Semester Examination", "50%"),
    ])

    add_text_page(doc, "Makeup Exam Policy", [
        "A makeup exam for a missed CIA will be granted only in case of",
        "a medical emergency or university-approved event participation,",
        "supported by valid documentation submitted within 3 working",
        "days of the missed exam.",
        "",
        "No makeup exam will be granted for unexcused absences.",
        "",
        "A student who misses two or more CIA exams without valid",
        "documentation will receive zero marks for those components",
        "and may not be eligible to pass the course.",
    ])

    add_table_page(doc, "Academic Calendar", [
        ("Event", "Date"),
        ("CIA 1", "15 September"),
        ("CIA 2", "20 October"),
        ("End Semester Examination", "5 - 15 December"),
    ])

    add_table_page(doc, "Grading Scheme", [
        ("Grade", "Marks Range"),
        ("O", "90 - 100"),
        ("A+", "80 - 89"),
        ("A", "70 - 79"),
        ("B+", "60 - 69"),
        ("B", "50 - 59"),
        ("F", "Below 50"),
    ])

    doc.save(OUTPUT_PATH)
    doc.close()
    print(f"Sample syllabus created at: {OUTPUT_PATH}")


if __name__ == "__main__":
    build()

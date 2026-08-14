"""
image_gen.py

Local visual generation for the AI-Powered Syllabus Assistant.

Stable Diffusion creates a topic-specific visual background.
Python/PIL creates the actual readable infographic so that exact
syllabus information is never left to Stable Diffusion's text generation.
"""

import base64
import os
import re
import time

import requests
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from src.utils import needs_multimodal

load_dotenv()

SD_URL = os.getenv("SD_WEBUI_URL", "http://127.0.0.1:7860")
DEFAULT_STEPS = int(os.getenv("SD_STEPS", "5"))

NEGATIVE_PROMPT = (
    "text, letters, words, numbers, watermark, logo, typography, "
    "misspelled writing, blurry text, distorted text, low quality"
)


# ---------------------------------------------------------------------------
# Policy / visual type detection
# ---------------------------------------------------------------------------

def should_generate_image(question: str) -> bool:
    """
    Decide whether the question is suitable for a visual summary.
    """
    return needs_multimodal(question)

def detect_visual_type(question: str) -> str:
    """
    Decide which type of infographic best matches the question.
    """

    q = question.lower()

    if any(word in q for word in [
        "grading",
        "grade",
        "grades",
        "marks",
        "mark range",
        "score"
    ]):
        return "grading"

    if any(word in q for word in [
        "attendance",
        "absent",
        "absence",
        "presence",
        "minimum attendance"
    ]):
        return "attendance"

    if any(word in q for word in [
        "calendar",
        "semester dates",
        "academic year",
        "academic calendar",
        "holiday",
        "holidays"
    ]):
        return "calendar"

    if any(word in q for word in [
        "exam",
        "examination",
        "test",
        "assessment",
        "evaluation",
        "internal",
        "cia",
        "marks distribution",
        "weightage",
        "weightage"
    ]):
        if any(word in q for word in [
            "makeup",
            "make-up",
            "missed",
            "miss",
            "retake",
            "retest"
        ]):
            return "makeup"

        return "assessment"

    if any(word in q for word in [
        "makeup",
        "make-up",
        "retake",
        "retest",
        "missed exam",
        "missed test"
    ]):
        return "makeup"

    return "policy"


# ---------------------------------------------------------------------------
# Stable Diffusion prompt
# ---------------------------------------------------------------------------

def build_image_prompt(question: str, retrieved_chunks: list[dict]) -> str:
    """
    Create a visual-only Stable Diffusion prompt.

    Stable Diffusion is intentionally NOT asked to write syllabus text.
    """

    visual_type = detect_visual_type(question)

    prompts = {
        "grading": (
            "professional university grading and academic achievement scene, "
            "graduation achievement symbols, award ribbons, score cards, "
            "ascending academic achievement levels, elegant educational design, "
            "modern university environment"
        ),

        "attendance": (
            "professional university attendance tracking scene, "
            "classroom, academic calendar, attendance checklist, "
            "student schedule, circular progress meter concept, "
            "organized educational dashboard"
        ),

        "calendar": (
            "professional university academic calendar scene, "
            "calendar pages, semester timeline, classroom, "
            "important academic milestones, organized schedule concept, "
            "modern educational planning design"
        ),

        "assessment": (
            "professional university assessment dashboard, "
            "examinations, assignments, academic score charts, "
            "checklist, evaluation sheets, classroom learning environment, "
            "modern educational analytics"
        ),

        "makeup": (
            "professional university examination retake concept, "
            "exam paper, calendar, clock, checklist, "
            "academic approval process, student examination environment, "
            "organized educational workflow"
        ),

        "policy": (
            "professional university academic policy concept, "
            "student handbook, university building, checklist, "
            "academic rules and organized information dashboard, "
            "modern educational design"
        ),
    }

    base = prompts.get(visual_type, prompts["policy"])

    return (
        f"{base}, "
        "clean professional presentation design, "
        "minimalist but visually interesting, "
        "soft blue and teal academic atmosphere, "
        "subtle depth, clean geometric shapes, "
        "high quality, sharp visual elements, "
        "no written words, no letters, no numbers, "
        "no typography, no watermark"
    )


# ---------------------------------------------------------------------------
# Stable Diffusion API
# ---------------------------------------------------------------------------

def check_sd_available() -> tuple[bool, str]:
    """Check whether Stable Diffusion WebUI API is reachable."""

    try:
        response = requests.get(
            f"{SD_URL}/sdapi/v1/sd-models",
            timeout=5
        )

        if response.status_code == 200:
            return True, "ok"

        return False, (
            f"Stable Diffusion WebUI responded with "
            f"status {response.status_code}."
        )

    except requests.exceptions.RequestException:
        return False, (
            "Could not reach the Stable Diffusion WebUI API. "
            "Make sure it is running with the --api flag."
        )


def generate_image(
    prompt: str,
    output_dir: str = "outputs",
    width: int = 512,
    height: int = 512
):
    """
    Generate the topic-specific background using Stable Diffusion.
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
        response = requests.post(
            f"{SD_URL}/sdapi/v1/txt2img",
            json=payload,
            timeout=600
        )
        response.raise_for_status()

    except requests.exceptions.RequestException as exc:
        raise ConnectionError(
            f"Stable Diffusion WebUI request failed: {exc}"
        )

    result = response.json()
    images = result.get("images", [])

    if not images:
        return None

    os.makedirs(output_dir, exist_ok=True)

    filename = f"policy_background_{int(time.time())}.png"
    output_path = os.path.join(output_dir, filename)

    with open(output_path, "wb") as f:
        f.write(base64.b64decode(images[0]))

    return output_path


# ---------------------------------------------------------------------------
# Fonts and drawing helpers
# ---------------------------------------------------------------------------

def _get_font(size: int, bold: bool = False):
    if bold:
        paths = [
            r"C:\Windows\Fonts\arialbd.ttf",
            r"C:\Windows\Fonts\segoeuib.ttf",
        ]
    else:
        paths = [
            r"C:\Windows\Fonts\arial.ttf",
            r"C:\Windows\Fonts\segoeui.ttf",
        ]

    for path in paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)

    return ImageFont.load_default()


def _wrap_text(draw, text, font, max_width):
    words = text.split()
    lines = []
    current = ""

    for word in words:
        candidate = current + (" " if current else "") + word
        bbox = draw.textbbox((0, 0), candidate, font=font)

        if bbox[2] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines


def _draw_centered(draw, box, text, font, fill):
    x1, y1, x2, y2 = box

    bbox = draw.textbbox((0, 0), text, font=font)

    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = x1 + (x2 - x1 - text_width) / 2
    y = y1 + (y2 - y1 - text_height) / 2 - 2

    draw.text(
        (x, y),
        text,
        font=font,
        fill=fill
    )


def _extract_answer_lines(answer: str):
    """
    Convert the LLM answer into clean readable lines.
    """

    lines = []

    for raw in answer.splitlines():
        line = raw.strip()

        if not line:
            continue

        line = re.sub(r"^[•*\-]+\s*", "", line)

        lines.append(line)

    return lines


def _draw_header(draw, visual_type, question):
    title_map = {
        "grading": "GRADING SCHEME",
        "attendance": "ATTENDANCE POLICY",
        "calendar": "ACADEMIC CALENDAR",
        "assessment": "ASSESSMENT STRUCTURE",
        "makeup": "MAKEUP / RETEST POLICY",
        "policy": "ACADEMIC POLICY",
    }

    title = title_map.get(visual_type, "ACADEMIC POLICY")

    title_font = _get_font(38, bold=True)
    subtitle_font = _get_font(18)

    draw.text(
        (70, 55),
        title,
        font=title_font,
        fill=(25, 48, 75)
    )

    draw.text(
        (72, 108),
        "AI-Powered Syllabus Assistant",
        font=subtitle_font,
        fill=(90, 110, 130)
    )

    draw.rounded_rectangle(
        (70, 140, 830, 147),
        radius=4,
        fill=(55, 120, 175)
    )


# ---------------------------------------------------------------------------
# Visual layouts
# ---------------------------------------------------------------------------

def _draw_grading_visual(draw, answer_lines):
    """
    Grading = ascending achievement ladder.
    """

    title_font = _get_font(22, bold=True)
    value_font = _get_font(20, bold=True)
    body_font = _get_font(18)

    y = 185

    # Find grade lines such as O (90-100)
    grade_lines = []

    for line in answer_lines:
        match = re.match(
            r"([A-Za-z+]+)\s*\((.*?)\)",
            line
        )

        if match:
            grade = match.group(1)
            marks = match.group(2)
            grade_lines.append((grade, marks))

    if grade_lines:
        max_items = min(len(grade_lines), 6)

        colors = [
            (40, 110, 170),
            (55, 125, 180),
            (70, 140, 190),
            (85, 150, 185),
            (100, 145, 170),
            (115, 135, 160),
        ]

        for i, (grade, marks) in enumerate(grade_lines[:max_items]):
            x = 90 + i * 115
            width = 100

            bar_height = 90 + i * 22
            bottom = 700
            top = bottom - bar_height

            draw.rounded_rectangle(
                (x, top, x + width, bottom),
                radius=15,
                fill=colors[i % len(colors)]
            )

            _draw_centered(
                draw,
                (x, top + 10, x + width, top + 55),
                grade,
                title_font,
                (255, 255, 255)
            )

            _draw_centered(
                draw,
                (x, bottom - 45, x + width, bottom - 10),
                marks,
                value_font,
                (255, 255, 255)
            )

        draw.text(
            (90, 735),
            "Higher marks correspond to higher academic grades.",
            font=body_font,
            fill=(55, 70, 85)
        )

    else:
        self_y = y
        for line in answer_lines[:8]:
            draw.text(
                (90, self_y),
                "• " + line,
                font=body_font,
                fill=(35, 45, 55)
            )
            self_y += 38


def _draw_attendance_visual(draw, answer_lines):
    """
    Attendance = large circular-style meter + policy details.
    """

    title_font = _get_font(30, bold=True)
    body_font = _get_font(19)

    cx, cy = 250, 430
    radius = 145

    # Circular meter background
    draw.ellipse(
        (cx - radius, cy - radius, cx + radius, cy + radius),
        outline=(210, 220, 230),
        width=30
    )

    # 75% illustrative progress arc
    draw.arc(
        (cx - radius, cy - radius, cx + radius, cy + radius),
        start=135,
        end=405,
        fill=(55, 125, 180),
        width=30
    )

    _draw_centered(
        draw,
        (cx - 90, cy - 55, cx + 90, cy + 55),
        "ATTENDANCE",
        _get_font(22, bold=True),
        (35, 65, 95)
    )

    # Checklist on right
    x = 470
    y = 240

    draw.text(
        (x, y),
        "POLICY DETAILS",
        font=title_font,
        fill=(35, 65, 95)
    )

    y += 65

    for line in answer_lines[:8]:
        wrapped = _wrap_text(
            draw,
            line,
            body_font,
            350
        )

        draw.ellipse(
            (x, y + 5, x + 15, y + 20),
            fill=(65, 135, 180)
        )

        tx = x + 28

        for wrapped_line in wrapped[:2]:
            draw.text(
                (tx, y),
                wrapped_line,
                font=body_font,
                fill=(45, 55, 65)
            )
            y += 30

        y += 18

        if y > 680:
            break


def _draw_calendar_visual(draw, answer_lines):
    """
    Calendar = timeline with milestone cards.
    """

    title_font = _get_font(25, bold=True)
    body_font = _get_font(18)

    # Calendar body
    draw.rounded_rectangle(
        (75, 190, 825, 690),
        radius=25,
        fill=(248, 251, 253),
        outline=(180, 200, 215),
        width=3
    )

    # Calendar rings
    for x in [130, 250, 370, 490, 610, 730]:
        draw.ellipse(
            (x, 175, x + 25, 200),
            fill=(55, 120, 175)
        )

    draw.text(
        (105, 225),
        "ACADEMIC TIMELINE",
        font=title_font,
        fill=(35, 65, 95)
    )

    y = 285

    for i, line in enumerate(answer_lines[:8]):
        # Timeline line
        if i < len(answer_lines[:8]) - 1:
            draw.line(
                (125, y + 18, 125, y + 70),
                fill=(160, 185, 200),
                width=4
            )

        draw.ellipse(
            (112, y, 138, y + 26),
            fill=(55, 125, 180)
        )

        wrapped = _wrap_text(
            draw,
            line,
            body_font,
            620
        )

        yy = y - 2

        for wrapped_line in wrapped[:2]:
            draw.text(
                (165, yy),
                wrapped_line,
                font=body_font,
                fill=(45, 55, 65)
            )
            yy += 29

        y += max(70, len(wrapped[:2]) * 35 + 30)

        if y > 650:
            break


def _draw_assessment_visual(draw, answer_lines):
    """
    Assessment = score cards and connected evaluation blocks.
    """

    title_font = _get_font(24, bold=True)
    body_font = _get_font(18)

    cards = min(max(len(answer_lines), 1), 6)

    cols = 2
    card_w = 330
    card_h = 130

    for i in range(cards):
        row = i // cols
        col = i % cols

        x = 80 + col * 380
        y = 190 + row * 155

        draw.rounded_rectangle(
            (x, y, x + card_w, y + card_h),
            radius=22,
            fill=(245, 249, 252),
            outline=(75, 130, 175),
            width=3
        )

        # Number badge
        draw.ellipse(
            (x + 18, y + 18, x + 60, y + 60),
            fill=(55, 125, 180)
        )

        _draw_centered(
            draw,
            (x + 18, y + 18, x + 60, y + 60),
            str(i + 1),
            _get_font(18, bold=True),
            (255, 255, 255)
        )

        wrapped = _wrap_text(
            draw,
            answer_lines[i],
            body_font,
            245
        )

        yy = y + 27

        for wrapped_line in wrapped[:3]:
            draw.text(
                (x + 78, yy),
                wrapped_line,
                font=body_font,
                fill=(40, 50, 60)
            )
            yy += 28


def _draw_makeup_visual(draw, answer_lines):
    """
    Makeup exam = process flow.
    """

    title_font = _get_font(23, bold=True)
    body_font = _get_font(18)

    steps = [
        ("1", "MISSED"),
        ("2", "ELIGIBILITY"),
        ("3", "APPROVAL"),
        ("4", "RETEST"),
    ]

    x_positions = [75, 285, 495, 705]

    for i, (number, label) in enumerate(steps):
        x = x_positions[i]

        draw.ellipse(
            (x, 220, x + 100, 320),
            fill=(55, 125, 180)
        )

        _draw_centered(
            draw,
            (x, 220, x + 100, 320),
            number,
            _get_font(34, bold=True),
            (255, 255, 255)
        )

        _draw_centered(
            draw,
            (x - 20, 335, x + 120, 380),
            label,
            _get_font(15, bold=True),
            (35, 65, 95)
        )

        if i < len(steps) - 1:
            draw.line(
                (x + 100, 270, x_positions[i + 1], 270),
                fill=(120, 155, 180),
                width=5
            )

    # Exact policy text below
    y = 445

    for line in answer_lines[:6]:
        wrapped = _wrap_text(
            draw,
            line,
            body_font,
            730
        )

        for wrapped_line in wrapped[:2]:
            draw.text(
                (85, y),
                "• " + wrapped_line,
                font=body_font,
                fill=(45, 55, 65)
            )
            y += 30

        y += 10

        if y > 730:
            break


def _draw_policy_visual(draw, answer_lines):
    """
    Generic academic policy dashboard.
    """

    title_font = _get_font(25, bold=True)
    body_font = _get_font(18)

    # Large academic icon
    draw.rounded_rectangle(
        (80, 205, 260, 385),
        radius=30,
        fill=(55, 125, 180)
    )

    draw.rectangle(
        (115, 275, 225, 330),
        fill=(255, 255, 255)
    )

    draw.polygon(
        [(105, 275), (170, 225), (235, 275)],
        fill=(255, 255, 255)
    )

    draw.text(
        (305, 215),
        "POLICY OVERVIEW",
        font=title_font,
        fill=(35, 65, 95)
    )

    y = 285

    for line in answer_lines[:8]:
        wrapped = _wrap_text(
            draw,
            line,
            body_font,
            500
        )

        for wrapped_line in wrapped[:2]:
            draw.text(
                (305, y),
                "• " + wrapped_line,
                font=body_font,
                fill=(45, 55, 65)
            )
            y += 30

        y += 10

        if y > 700:
            break


# ---------------------------------------------------------------------------
# Final infographic
# ---------------------------------------------------------------------------

def create_readable_infographic(
    background_path: str,
    question: str,
    answer: str,
    output_dir: str = "outputs"
):
    """
    Combine the Stable Diffusion background with a topic-specific
    readable infographic.
    """

    os.makedirs(output_dir, exist_ok=True)

    visual_type = detect_visual_type(question)

    background = Image.open(background_path).convert("RGB")
    background = background.resize(
        (900, 900),
        Image.Resampling.LANCZOS
    )

    # Blur background slightly so the information layer remains dominant.
    background = background.filter(
        ImageFilter.GaussianBlur(radius=1.5)
    )

    # Dark transparent overlay
    overlay = Image.new(
        "RGBA",
        background.size,
        (15, 30, 50, 65)
    )

    background = Image.alpha_composite(
        background.convert("RGBA"),
        overlay
    )

    draw = ImageDraw.Draw(background)

    # Main glass-like panel
    draw.rounded_rectangle(
        (35, 30, 865, 870),
        radius=35,
        fill=(255, 255, 255, 238)
    )

    _draw_header(
        draw,
        visual_type,
        question
    )

    answer_lines = _extract_answer_lines(answer)

    if visual_type == "grading":
        _draw_grading_visual(draw, answer_lines)

    elif visual_type == "attendance":
        _draw_attendance_visual(draw, answer_lines)

    elif visual_type == "calendar":
        _draw_calendar_visual(draw, answer_lines)

    elif visual_type == "assessment":
        _draw_assessment_visual(draw, answer_lines)

    elif visual_type == "makeup":
        _draw_makeup_visual(draw, answer_lines)

    else:
        _draw_policy_visual(draw, answer_lines)

    # Question footer
    footer_font = _get_font(15)

    draw.text(
        (70, 835),
        "Generated locally • Ollama + Stable Diffusion",
        font=footer_font,
        fill=(100, 115, 130)
    )

    filename = f"policy_visual_{visual_type}_{int(time.time())}.png"

    output_path = os.path.join(
        output_dir,
        filename
    )

    background.convert("RGB").save(
        output_path,
        quality=95
    )

    return output_path
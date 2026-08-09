from PIL import Image, ImageDraw, ImageFont

W, H = 1400, 900
NAVY = (27, 42, 74)
INK = (22, 33, 62)
ACCENT = (61, 107, 255)
ACCENT2 = (255, 138, 61)
GREEN = (46, 139, 87)
LIGHT = (244, 246, 251)
MUTE = (107, 114, 128)
WHITE = (255, 255, 255)
BORDER = (210, 216, 230)

img = Image.new("RGB", (W, H), WHITE)
draw = ImageDraw.Draw(img)


def font(size, bold=False):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


f_title = font(30, bold=True)
f_sub = font(15)
f_label = font(16, bold=True)
f_small = font(13)
f_tag = font(12, bold=True)


def box(x, y, w, h, fill, outline=BORDER, radius=14, width=2):
    draw.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill=fill, outline=outline, width=width)


def text_center(cx, y, s, f, fill=INK):
    bbox = draw.textbbox((0, 0), s, font=f)
    w = bbox[2] - bbox[0]
    draw.text((cx - w / 2, y), s, font=f, fill=fill)


def arrow(x1, y1, x2, y2, color=MUTE, width=3):
    draw.line([x1, y1, x2, y2], fill=color, width=width)
    import math
    angle = math.atan2(y2 - y1, x2 - x1)
    size = 10
    p1 = (x2 - size * math.cos(angle - 0.4), y2 - size * math.sin(angle - 0.4))
    p2 = (x2 - size * math.cos(angle + 0.4), y2 - size * math.sin(angle + 0.4))
    draw.polygon([p1, p2, (x2, y2)], fill=color)


# Title
text_center(W / 2, 24, "AI-Powered Syllabus Assistant — System Architecture", f_title, INK)
text_center(W / 2, 62, "Fully local: no cloud APIs anywhere in this diagram", f_sub, MUTE)

# --- Student / Browser box ---
box(60, 110, 260, 110, LIGHT)
text_center(190, 132, "Student", f_label, INK)
text_center(190, 158, "(Browser)", f_small, MUTE)

# --- Streamlit App box (center hub) ---
box(560, 100, 280, 700, WHITE, outline=ACCENT, width=3, radius=18)
text_center(700, 118, "Streamlit App", f_label, ACCENT)
text_center(700, 142, "app.py", f_small, MUTE)

# Sub-components inside Streamlit box
components = [
    ("PDF Processor", "pymupdf — text + page images"),
    ("Chunker", "src/utils.py"),
    ("Embeddings", "sentence-transformers (local)"),
    ("Vector Store", "ChromaDB (local, persistent)"),
    ("Retriever", "src/retriever.py"),
    ("LLM Client", "src/llm.py"),
    ("Image Client", "src/image_gen.py"),
]
cy = 175
for name, sub in components:
    box(585, cy, 230, 66, LIGHT, radius=10)
    text_center(700, cy + 10, name, f_small, INK)
    text_center(700, cy + 30, sub, f_small, MUTE)
    cy += 78

# --- Ollama box (right) ---
box(1020, 160, 320, 160, WHITE, outline=GREEN, width=3)
text_center(1180, 178, "Ollama (Local LLM)", f_label, GREEN)
text_center(1180, 202, "llama3 / mistral / gemma2", f_small, MUTE)
text_center(1180, 224, "http://localhost:11434", f_small, MUTE)
text_center(1180, 246, "Text answers, grounded in retrieved chunks", f_small, MUTE)
text_center(1180, 265, "No API key · no internet needed after pull", f_small, MUTE)

# --- Stable Diffusion box (right, below Ollama) ---
box(1020, 360, 320, 160, WHITE, outline=ACCENT2, width=3)
text_center(1180, 378, "Stable Diffusion WebUI", f_label, ACCENT2)
text_center(1180, 402, "AUTOMATIC1111 (--api)", f_small, MUTE)
text_center(1180, 424, "http://127.0.0.1:7860", f_small, MUTE)
text_center(1180, 446, "Generates policy infographic images", f_small, MUTE)
text_center(1180, 465, "No API key · no internet needed", f_small, MUTE)

# --- Local disk box (bottom) ---
box(60, 260, 260, 200, LIGHT)
text_center(190, 280, "Local Disk", f_label, INK)
text_center(190, 305, "data/  (uploads + vector DB)", f_small, MUTE)
text_center(190, 328, "outputs/  (generated images)", f_small, MUTE)
text_center(190, 351, "models/  (notes on local models)", f_small, MUTE)

# --- Arrows ---
arrow(320, 140, 560, 140)          # student -> streamlit (upload/question)
text_center(440, 145, "upload PDF / ask question", f_small, MUTE)

arrow(560, 195, 320, 195)          # streamlit -> student (final answer shown in browser)
text_center(440, 172, "answer (+ image) shown in chat", f_small, MUTE)

arrow(560, 300, 320, 320)          # streamlit -> disk (chunks/vectors)
text_center(440, 275, "store chunks", f_small, MUTE)
text_center(440, 290, "+ embeddings", f_small, MUTE)

arrow(840, 240, 1020, 210)         # streamlit LLM client -> Ollama (request)
text_center(930, 200, "text prompt", f_small, MUTE)

arrow(1020, 265, 840, 270)         # Ollama -> streamlit (response)
text_center(930, 280, "grounded answer", f_small, MUTE)

arrow(840, 340, 1020, 400)         # streamlit image client -> SD (request)
text_center(930, 375, "image prompt", f_small, MUTE)

arrow(1020, 440, 840, 360)         # SD -> streamlit (response)
text_center(940, 450, "generated image", f_small, MUTE)

# Legend
box(60, 780, 480, 90, LIGHT, radius=10)
text_center(300, 795, "Single workflow, one question:", f_tag, INK)
draw.text((80, 818), "1. Retrieve syllabus chunks   2. Ollama answers (text)", font=f_small, fill=INK)
draw.text((80, 840), "3. If policy is structural -> Stable Diffusion generates a visual   4. Both shown together", font=f_small, fill=INK)

img.save("docs/architecture.png")
print("saved docs/architecture.png")

from PIL import Image, ImageDraw, ImageFont

W, H = 1400, 500
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
    path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


f_title = font(28, bold=True)
f_sub = font(15)
f_step = font(16, bold=True)
f_body = font(13)
f_num = font(20, bold=True)


def box(x, y, w, h, fill, outline=BORDER, radius=12, width=2):
    draw.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill=fill, outline=outline, width=width)


def text_center(cx, y, s, f, fill=INK):
    bbox = draw.textbbox((0, 0), s, font=f)
    w = bbox[2] - bbox[0]
    draw.text((cx - w / 2, y), s, font=f, fill=fill)


def wrapped_text(x, y, s, f, fill, max_width, line_height=17):
    words = s.split(" ")
    line = ""
    ly = y
    for w in words:
        test = (line + " " + w).strip()
        bbox = draw.textbbox((0, 0), test, font=f)
        if bbox[2] - bbox[0] > max_width and line:
            draw.text((x, ly), line, font=f, fill=fill)
            ly += line_height
            line = w
        else:
            line = test
    if line:
        draw.text((x, ly), line, font=f, fill=fill)
    return ly + line_height


text_center(W / 2, 20, "AI-Powered Syllabus Assistant — Single Workflow", f_title, INK)
text_center(W / 2, 56, "One question triggers both the local LLM and, when relevant, local image generation", f_sub, MUTE)

steps = [
    ("1", "Upload Syllabus", "Student uploads a course PDF in the browser.", LIGHT, INK),
    ("2", "Process PDF", "Each page: text extracted, chunked, embedded (sentence-transformers), stored in ChromaDB. Page also rendered as an image.", LIGHT, INK),
    ("3", "Ask Question", "Student types a natural-language question in the chat box.", LIGHT, INK),
    ("4", "Retrieve Chunks", "Question is embedded and matched against stored chunks (semantic search).", LIGHT, INK),
    ("5", "Local LLM Answers", "Ollama (llama3/mistral/gemma2) answers using ONLY the retrieved chunks. Refuses to guess if not found.", (232, 245, 233), GREEN),
    ("6", "Structural Policy?", "If the question involves grading, attendance, or a calendar, continue to image generation. Otherwise skip to Step 8.", LIGHT, INK),
    ("7", "Local Image Generation", "Stable Diffusion WebUI (AUTOMATIC1111) generates a summary infographic from a prompt built off the retrieved section headings.", (255, 240, 227), ACCENT2),
    ("8", "Display Result", "Text answer + citation shown. Image (if generated) shown alongside it in the same chat turn.", LIGHT, INK),
]

box_w, box_h, gap = 300, 130, 40
cols = 4
start_x, start_y = 60, 110

for i, (num, title, desc, fill, accent) in enumerate(steps):
    col = i % cols
    row = i // cols
    x = start_x + col * (box_w + gap)
    y = start_y + row * (box_h + 90)

    box(x, y, box_w, box_h, fill, outline=accent, width=2)
    # number badge
    draw.ellipse([x + 14, y + 14, x + 46, y + 46], fill=accent)
    text_center(x + 30, y + 18, num, f_num, WHITE)
    draw.text((x + 56, y + 18), title, font=f_step, fill=INK)
    wrapped_text(x + 16, y + 56, desc, f_body, MUTE, box_w - 32)

    # arrow to next box (within row)
    if col < cols - 1:
        ax1 = x + box_w + 4
        ax2 = x + box_w + gap - 4
        ay = y + box_h / 2
        draw.line([ax1, ay, ax2, ay], fill=MUTE, width=3)
        draw.polygon([(ax2 - 8, ay - 6), (ax2 - 8, ay + 6), (ax2, ay)], fill=MUTE)
    elif row < (len(steps) - 1) // cols:
        # drop down to next row, back to column 0
        ax = x + box_w / 2
        ay1 = y + box_h + 4
        ay2 = y + box_h + 90 - 4
        next_y = start_y + (row + 1) * (box_h + 90)
        draw.line([ax, ay1, ax, ay1 + 20], fill=MUTE, width=3)
        draw.line([ax, ay1 + 20, start_x + box_w / 2, ay1 + 20], fill=MUTE, width=3)
        draw.line([start_x + box_w / 2, ay1 + 20, start_x + box_w / 2, next_y - 4], fill=MUTE, width=3)
        draw.polygon([
            (start_x + box_w / 2 - 6, next_y - 12),
            (start_x + box_w / 2 + 6, next_y - 12),
            (start_x + box_w / 2, next_y - 4),
        ], fill=MUTE)

# Note about branching at step 6/7
text_center(W / 2, H - 30, "Step 6 branches the workflow: text-only answers skip straight to Step 8, avoiding unnecessary image generation.", f_body, MUTE)

img.save("docs/workflow.png")
print("saved docs/workflow.png")

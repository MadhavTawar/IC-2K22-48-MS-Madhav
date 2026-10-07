import cv2
import numpy as np
import easyocr
import re
import sys

INPUT_FILE = sys.argv[1] if len(sys.argv) > 1 else "input.jpg"
OUTPUT_FILE = "enhanced.jpg"

# Small lexicon for 1-edit OCR cleanup (e/c, l/t, etc.)
COMMON_WORDS = {
    "hello", "this", "that", "with", "from", "test", "text", "image",
    "should", "read", "clearly", "testing", "voice", "clone", "project",
    "ocr", "sample", "document", "please", "thanks", "welcome", "name",
}


def enhance_for_ocr(bgr):
    """Upscale blurry text and add contrast without halo artifacts."""
    h, w = bgr.shape[:2]
    scale = 4 if max(h, w) < 1600 else 2
    up = cv2.resize(bgr, (w * scale, h * scale), interpolation=cv2.INTER_LANCZOS4)

    gray = cv2.cvtColor(up, cv2.COLOR_BGR2GRAY)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    contrast = clahe.apply(gray)

    # Gentle unsharp mask — the old 5-center kernel created rings around letters
    blur = cv2.GaussianBlur(contrast, (0, 0), sigmaX=0.8)
    sharp = cv2.addWeighted(contrast, 1.4, blur, -0.4, 0)
    return np.clip(sharp, 0, 255).astype(np.uint8)


def box_iou(a, b):
    ax1, ay1 = np.min(a, axis=0)
    ax2, ay2 = np.max(a, axis=0)
    bx1, by1 = np.min(b, axis=0)
    bx2, by2 = np.max(b, axis=0)
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    area_a = max(0, ax2 - ax1) * max(0, ay2 - ay1)
    area_b = max(0, bx2 - bx1) * max(0, by2 - by1)
    union = area_a + area_b - inter
    return inter / union if union else 0


def merge_detections(groups):
    """Keep the highest-confidence box when the same region is read twice."""
    merged = []
    for bbox, text, conf in groups:
        if conf < 0.25 or not str(text).strip():
            continue
        hit = None
        for i, (ob, _, oc) in enumerate(merged):
            if box_iou(np.array(bbox), np.array(ob)) > 0.4:
                hit = i
                break
        if hit is None:
            merged.append([bbox, text.strip(), conf])
        elif conf > merged[hit][2]:
            merged[hit] = [bbox, text.strip(), conf]
    return merged


def detections_to_lines(dets):
    rows = []
    for bbox, text, _ in dets:
        ys = [p[1] for p in bbox]
        xs = [p[0] for p in bbox]
        rows.append((sum(ys) / 4, sum(xs) / 4, text))
    rows.sort(key=lambda t: (t[0], t[1]))

    if not rows:
        return []

    heights = []
    for bbox, _, _ in dets:
        ys = [p[1] for p in bbox]
        heights.append(max(ys) - min(ys))
    gap = max(28, float(np.median(heights)) * 0.6) if heights else 40

    lines, current, current_y = [], [], None
    for y, x, word in rows:
        if current_y is None or abs(y - current_y) < gap:
            current.append((x, word))
            current_y = y if current_y is None else (current_y + y) / 2
        else:
            lines.append(" ".join(w for _, w in sorted(current)))
            current, current_y = [(x, word)], y
    if current:
        lines.append(" ".join(w for _, w in sorted(current)))
    return lines


def one_edits(word):
    letters = "abcdefghijklmnopqrstuvwxyz"
    splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
    deletes = [L + R[1:] for L, R in splits if R]
    transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]
    replaces = [L + c + R[1:] for L, R in splits if R for c in letters]
    inserts = [L + c + R for L, R in splits for c in letters]
    return set(deletes + transposes + replaces + inserts)


def correct_token(token):
    if token in {"&"}:
        return "a"
    if token in {"_", "—", "–"}:
        return "-"
    match = re.match(r"^(\W*)([A-Za-z]+)(\W*)$", token)
    if not match:
        return token
    prefix, core, suffix = match.groups()
    if suffix == ":":
        suffix = "."
    low = core.lower()
    if low in COMMON_WORDS or len(low) < 4:
        return prefix + core + suffix
    hits = [w for w in one_edits(low) if w in COMMON_WORDS]
    if len(hits) != 1:
        return prefix + core + suffix
    fixed = hits[0]
    if core.isupper():
        fixed = fixed.upper()
    elif core[0].isupper():
        fixed = fixed.capitalize()
    return prefix + fixed + suffix


def cleanup_text(text):
    tokens = text.split()
    tokens = [correct_token(t) for t in tokens]
    # Isolated "4" between words is a common OCR miss for "a"
    for i, tok in enumerate(tokens):
        if tok == "4" and 0 < i < len(tokens) - 1:
            if tokens[i - 1].isalpha() and re.match(r"^[A-Za-z]", tokens[i + 1]):
                tokens[i] = "a"
    joined = " ".join(tokens)
    joined = re.sub(r"([A-Za-z]);(\s+[a-z])", r"\1,\2", joined)
    return joined


img = cv2.imread(INPUT_FILE)
if img is None:
    raise FileNotFoundError(f"Could not read {INPUT_FILE}")

enhanced = enhance_for_ocr(img)
cv2.imwrite(OUTPUT_FILE, enhanced)
print(f"Saved enhanced image: {OUTPUT_FILE}")

reader = easyocr.Reader(["en"], gpu=False)
h, w = img.shape[:2]
upscaled = cv2.resize(
    cv2.cvtColor(img, cv2.COLOR_BGR2GRAY),
    (w * 4, h * 4),
    interpolation=cv2.INTER_LANCZOS4,
)

raw = []
for source in (upscaled, enhanced):
    raw.extend(
        reader.readtext(
            source,
            detail=1,
            mag_ratio=1.5,
            min_size=15,
            text_threshold=0.5,
            low_text=0.3,
            link_threshold=0.3,
        )
    )

lines = [cleanup_text(line) for line in detections_to_lines(merge_detections(raw))]
text = "\n".join(lines).strip()

print("\n--- Extracted Text ---")
print(text if text else "(no text detected)")

with open("extracted_text.txt", "w", encoding="utf-8") as f:
    f.write(text)
print("\nSaved extracted_text.txt")

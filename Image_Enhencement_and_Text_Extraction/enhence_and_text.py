"""
Image enhancement + text extraction (OCR).

Pipeline
  1. Pad the border   - text touching the image edge is often missed
  2. Upscale 2x       - small letters need more pixels
  3. Deblur           - Wiener deconvolution. Radius is chosen from letter size
                        (small text is distorted by a big radius); strength is
                        chosen from image noise (noisy images need a gentle fix)
  4. OCR              - EasyOCR reads the deblurred image. Low-confidence words
                        are KEPT (blurry text is often right at low confidence)
  5. Group into lines

Usage:  python enhence_and_text.py path/to/image.jpg
Output: enhanced.jpg (deblurred image), extracted_text.txt
"""
import re
import sys

import cv2
import numpy as np

INPUT_FILE = sys.argv[1] if len(sys.argv) > 1 else "input.jpg"
MIN_CONF = 0.05      # only drop pure junk; blurry text is often read correctly at low confidence
SCALE = 2


# ----------------------------------------------------------------- enhancement
def pad_border(gray, frac=0.06):
    """Add a border in the background colour so edge text isn't clipped."""
    h, w = gray.shape
    p = max(20, int(min(h, w) * frac))
    edge = np.concatenate([gray[0], gray[-1], gray[:, 0], gray[:, -1]])
    return cv2.copyMakeBorder(gray, p, p, p, p, cv2.BORDER_CONSTANT,
                              value=(float(np.median(edge)),))


def upscale(gray, s=SCALE):
    return cv2.resize(gray, None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC)


def _gauss_psf(shape, sigma):
    """Gaussian blur kernel laid out for FFT (centre at the corners)."""
    h, w = shape
    y, x = np.mgrid[:h, :w]
    y, x = np.minimum(y, h - y), np.minimum(x, w - x)
    psf = np.exp(-(x ** 2 + y ** 2) / (2 * sigma ** 2))
    return psf / psf.sum()


def wiener_deblur(gray, sigma, nsr=0.05):
    """Undo a Gaussian blur of radius `sigma` pixels (Wiener deconvolution).
    nsr = assumed noise/signal: higher = gentler, lower = sharper but halos."""
    pad = int(sigma * 6) + 4
    g = np.pad(gray.astype(np.float32) / 255.0, pad, mode="edge")
    H = np.fft.fft2(_gauss_psf(g.shape, sigma))
    F = np.conj(H) / (np.abs(H) ** 2 + nsr) * np.fft.fft2(g)
    out = np.real(np.fft.ifft2(F))[pad:-pad, pad:-pad]
    return np.clip(out * 255.0, 0, 255).astype(np.uint8)


def estimate_sigma(gray):
    """Blur radius from letter size: median height of the dark blobs
    (letters) x 0.08, limited to 2.5 .. 4.0 px."""
    binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    _, _, stats, _ = cv2.connectedComponentsWithStats(binary)
    heights = [s[cv2.CC_STAT_HEIGHT] for s in stats[1:]
               if 8 <= s[cv2.CC_STAT_HEIGHT] < gray.shape[0] * 0.5
               and s[cv2.CC_STAT_AREA] > 20]
    if not heights:
        return 3.0
    return float(np.clip(0.08 * np.median(heights), 2.5, 4.0))


def estimate_noise(gray):
    """Noise level (Immerkaer's method). ~0.1-0.5 = clean, 0.6+ = noticeably noisy."""
    k = np.array([[1, -2, 1], [-2, 4, -2], [1, -2, 1]], np.float32)
    h, w = gray.shape
    resp = np.abs(cv2.filter2D(gray.astype(np.float32), -1, k)[1:-1, 1:-1]).sum()
    return float(resp * np.sqrt(0.5 * np.pi) / (6 * (w - 2) * (h - 2)))


def choose_nsr(noise):
    """Clean image -> 0.01 (sharp). Noisy image -> up to 0.05 (gentle), because
    a sharp deblur would amplify the noise into the text."""
    return float(np.clip(0.01 + 0.04 * (noise - 0.4) / 0.4, 0.01, 0.05))


def enhance(gray):
    """Returns (plain_upscaled, deblurred, info)."""
    plain = upscale(pad_border(gray))
    sigma = estimate_sigma(plain)
    nsr = choose_nsr(estimate_noise(plain))
    return plain, wiener_deblur(plain, sigma, nsr), {"sigma": sigma, "nsr": nsr}


# ------------------------------------------------------------------------- OCR
def box_iou(a, b):
    ax1, ay1 = np.min(a, axis=0)
    ax2, ay2 = np.max(a, axis=0)
    bx1, by1 = np.min(b, axis=0)
    bx2, by2 = np.max(b, axis=0)
    inter = max(0, min(ax2, bx2) - max(ax1, bx1)) * max(0, min(ay2, by2) - max(ay1, by1))
    union = (ax2 - ax1) * (ay2 - ay1) + (bx2 - bx1) * (by2 - by1) - inter
    return inter / union if union else 0


def merge_detections(dets):
    """Same region read twice -> keep the more confident reading."""
    merged = []
    for bbox, text, conf in dets:
        if conf < MIN_CONF or not str(text).strip():
            continue
        for i, (ob, _, oc) in enumerate(merged):
            if box_iou(np.array(bbox), np.array(ob)) > 0.4:
                if conf > oc:
                    merged[i] = [bbox, text.strip(), conf]
                break
        else:
            merged.append([bbox, text.strip(), conf])
    return merged


def detections_to_lines(dets):
    """Sort words top-to-bottom, then left-to-right, and join into lines."""
    rows = [(np.mean([p[1] for p in b]), np.mean([p[0] for p in b]), t,
             max(p[1] for p in b) - min(p[1] for p in b)) for b, t, _ in dets]
    if not rows:
        return []
    rows.sort(key=lambda r: (r[0], r[1]))
    gap = max(10.0, float(np.median([r[3] for r in rows])) * 0.6)
    lines, cur, cur_y = [], [], None
    for y, x, word, _ in rows:
        if cur_y is None or abs(y - cur_y) < gap:
            cur.append((x, word))
            cur_y = y if cur_y is None else (cur_y + y) / 2
        else:
            lines.append(" ".join(w for _, w in sorted(cur)))
            cur, cur_y = [(x, word)], y
    if cur:
        lines.append(" ".join(w for _, w in sorted(cur)))
    return lines


def cleanup_line(line):
    """A few generic fixes for classic OCR slips. Deliberately small: there is
    no word list, so it cannot overfit to one test sentence."""
    line = re.sub(r"(?<=[A-Za-z]) [4&] (?=[A-Za-z])", " a ", line)   # lone "4" or "&" between words -> "a"
    line = re.sub(r"(?<=[A-Za-z]);(?= [a-z])", ",", line)             # "word; next" -> "word, next"
    line = re.sub(r":$", ".", line)                                   # line-final ":" -> "."
    return line


def extract_text(reader, deblurred):
    dets = merge_detections(reader.readtext(deblurred, detail=1))
    return "\n".join(cleanup_line(l) for l in detections_to_lines(dets)), dets


def main():
    import easyocr          # imported here so the enhancement code is importable alone

    img = cv2.imread(INPUT_FILE)
    if img is None:
        raise FileNotFoundError(f"Could not read {INPUT_FILE}")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    plain, deblurred, info = enhance(gray)
    cv2.imwrite("enhanced.jpg", deblurred)
    print(f"Saved enhanced.jpg  (blur radius {info['sigma']:.1f}px, strength nsr={info['nsr']:.3f})")

    reader = easyocr.Reader(["en"], gpu=False)
    text, dets = extract_text(reader, deblurred)

    print("\n--- Extracted Text ---")
    print(text or "(no text detected)")
    if dets:
        print(f"\nMean confidence: {np.mean([d[2] for d in dets]):.2f}")
    with open("extracted_text.txt", "w", encoding="utf-8") as f:
        f.write(text)
    print("Saved extracted_text.txt")


if __name__ == "__main__":
    main()
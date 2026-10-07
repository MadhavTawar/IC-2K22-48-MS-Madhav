# Image Enhancement + Text Extraction (OCR)

Takes a blurry/noisy image, sharpens it, and extracts any text found in it.

## Setup

```
pip install -r requirements.txt
```

No separate OCR engine install needed — this uses **EasyOCR**, a pure-Python
library. On first run it downloads its recognition model automatically
(one-time, needs internet).

## Usage

```
python enhence_and_text.py path/to/your/image.jpg
```

Outputs:
- `enhanced.jpg` — the sharpened/denoised/contrast-boosted version
- `extracted_text.txt` — any text found in the image (also printed to terminal)

## What it does

1. **Upscale** — 4x Lanczos so small/blurry letters are large enough for OCR
2. **Contrast boost** — CLAHE so faint strokes stand out
3. **Gentle sharpen** — unsharp mask (no halo kernel) to crisp edges
4. **OCR** — EasyOCR on the original upscale and the enhanced image, then merge
5. **Cleanup** — 1-edit spelling fix for common OCR mixes (e/c, etc.)

## Notes

- To read other languages, add their codes to the `Reader([...])` line in
  `enhence_and_text.py` — e.g. `easyocr.Reader(['en', 'hi'])` for English + Hindi.
- First run is slower (downloading the model); later runs are faster.
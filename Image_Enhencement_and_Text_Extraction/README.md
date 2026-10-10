# Image Enhancement + Text Extraction (OCR)

Takes a blurry image, deblurs it, and extracts the text with EasyOCR.

## Setup

```bash
pip install -r requirements.txt
```

EasyOCR downloads its English model on first run (needs internet once).
It also installs PyTorch, so the first install is large.

## Usage

```bash
python enhence_and_text.py path/to/image.jpg
```

Outputs: `enhanced.jpg` (deblurred image) and `extracted_text.txt`.

## How it works

1. **Pad border** - text touching the image edge is often missed by OCR.
2. **Upscale 2x** - small letters need more pixels.
3. **Deblur (Wiener deconvolution)** - mathematically reverses a Gaussian blur.
   - *Radius* is chosen from letter size (a big radius distorts small text).
   - *Strength* (`nsr`) is chosen from image noise: clean image -> sharp (0.01),
     noisy image -> gentle (0.05), so noise is not amplified into the letters.
4. **OCR** - EasyOCR reads the deblurred image. Words with low confidence are
   **kept** (threshold 0.05): blurry text is often correct at low confidence.
5. **Group into lines** and apply 3 small generic cleanup rules
   (a lone `4` between words -> `a`, `;` -> `,`, line-final `:` -> `.`).

## What was wrong with the first version

| Problem | Cause | Fix |
| --- | --- | --- |
| Image not improving | CLAHE + unsharp mask only adds contrast and grain; nothing removes blur | Real deblurring (Wiener deconvolution) |
| Text incomplete | Words under confidence 0.25 were thrown away, even when correct | Threshold lowered to 0.05 |
| Overfitted cleanup | A word list of the test sentence's own words | Removed; 3 generic rules instead |

## Measured results

Benchmark: 8 synthetic images with known text (blur, noise, low contrast, small
font, uneven light, motion blur), scored with EasyOCR text accuracy.

| Method | Mean accuracy (excl. motion blur) |
| --- | --- |
| Raw image, confidence >= 0.25 (original approach) | 74.5% |
| **This pipeline** | **94.9%** |

Heavily blurred image: 0% -> 86%.
Your test image now reads: `Hello Maddy, this Is a test image.` /
`OCR should read this text clearly.` / `Testing 1 2 3 - Voice Clone Projecl`.
Two small errors remain: "Is" (capital I) and "Projecl" (the cut-off final
"t", see below). The old version also misread `e` as `c` ("Hcllo", "rcad").

## Limitations

- **Cut-off text:** the sample image is clipped at the right edge, so the last
  "t" of "Project" is mostly missing. No enhancement can recover pixels that are
  not in the file.
- **Motion blur is not handled.** The Gaussian model does not fit a smeared
  image, and every method tried scored under 25% on it.
- Deblurring is a trade-off: strong settings add halos around letters.
- Accuracy numbers come from synthetic test images, not real photos.
- A mid-sentence capital `I` vs lowercase `l` (e.g. "Is") can still occur.

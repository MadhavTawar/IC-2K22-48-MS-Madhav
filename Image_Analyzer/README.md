# Image Metadata Analyzer

A small script that prints a metadata report for an image file: file
info (size, format, dimensions, resolution, color mode) plus any
embedded EXIF data.

## Requirements

- Python 3.8 or newer
- Pillow (install via `pip install -r requirements.txt`)

## Installation

Open a terminal in this project folder and run:

```bash
pip install -r requirements.txt
```

## Usage

```bash
python image_analyzer.py test_image.jpg
```

You can also provide a complete image path:

```bash
python image_analyzer.py "C:\Users\YourName\Pictures\photo.jpg"
```

If no path is given as an argument, the script will prompt for one.

## Sample Output

```text
================================
IMAGE METADATA REPORT
================================
File Name       : test_image.jpg
File Size       : 8.42 KB
File Format     : JPEG
Width           : 800 pixels
Height          : 600 pixels
Resolution      : Not available
Color Mode      : RGB

EXIF Metadata
-------------------------------
No EXIF metadata found.
```

## Supported Formats

Minimum:

- JPG / JPEG
- PNG

Also supported by Pillow:

- TIFF
- WEBP
- BMP

## Error Handling

- Missing file path -> clear error, exits without a traceback
- File exists but isn't a valid/readable image -> clear error
- No EXIF metadata found -> message instead of a hard failure

## Project Structure

```text
image-analyzer/
├── image_analyzer.py
├── requirements.txt
├── README.md
└── test_image.jpg
```

## How It Works

The program uses the Pillow library to open the image and read its
metadata. Python's `os` module is used for file information, while
`sys` is used to accept the image path from the command line.

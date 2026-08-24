# Image Metadata Analyzer

A simple Python program that analyzes an image and displays its basic metadata and EXIF information.

Features

File name

File size

File format

Width and height

Resolution / DPI

Color mode

## EXIF Metadata

Readable EXIF tag names

Basic error handling

Supported Formats

Minimum:

JPG / JPEG

PNG

Also supported by Pillow:

TIFF

WEBP

BMP

Requirements

Python 3.8 or newer

Pillow

Installation

Open a terminal in this project folder and run:

pip install -r requirements.txt

Usage

Place an image in the project folder and run:

python image_analyzer.py test_image.jpg

You can also provide a complete image path:

python image_analyzer.py "C:\Users\YourName\Pictures\photo.jpg"

Example Output

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

Project Structure

image-analyzer/
│
├── image_analyzer.py
├── requirements.txt
├── README.md
└── test_image.jpg

How It Works

The program uses the Pillow library to open the image and read its metadata. Python's os module is used for file information, while sys is used to accept the image path from the command line.

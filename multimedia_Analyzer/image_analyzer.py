"""
image_analyzer.py

Responsible for extracting metadata from image files using Pillow.
Returns a plain dictionary so report_generator.py can format or save
it however it needs to.
"""

import os

import file_utils


def analyze_image(path):
    """
    Analyze an image file and return a dict of its metadata.
    Returns a dict with an 'error' key if the file can't be read.
    """
    try:
        from PIL import Image, ExifTags
    except ImportError:
        return {"error": "Pillow is required for image files. Install with: pip install Pillow"}

    try:
        img = Image.open(path)
        img.load()
    except Exception as e:
        return {"error": f"could not open '{path}' as an image ({e})"}

    exif_data = {}
    exif = img.getexif()
    if exif:
        for tag_id, value in exif.items():
            tag = ExifTags.TAGS.get(tag_id, tag_id)
            exif_data[str(tag)] = str(value)

    return {
        "file_name": os.path.basename(path),
        "file_size": file_utils.get_file_size(path),
        "file_format": img.format,
        "width": img.width,
        "height": img.height,
        "resolution": img.info.get("dpi", "N/A"),
        "color_mode": img.mode,
        "exif": exif_data,
    }
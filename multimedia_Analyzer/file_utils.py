"""
file_utils.py

Responsible for basic file-level checks used by every analyzer:
- Does the file exist?
- What is its size?
- What is its extension?
- What type of media is it (image / audio / video / unknown)?
"""

import os

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".webp", ".bmp"}
AUDIO_EXTS = {".mp3", ".wav", ".flac", ".aac", ".m4a", ".ogg", ".wma"}
VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".wmv"}


def file_exists(path):
    """Return True if the given path points to an existing file."""
    return os.path.isfile(path)


def get_file_size(path):
    """Return the file size in bytes."""
    return os.path.getsize(path)


def get_file_extension(path):
    """Return the file's extension, lowercase, including the dot (e.g. '.mp3')."""
    return os.path.splitext(path)[1].lower()


def identify_file_type(path):
    """
    Return 'image', 'audio', 'video', or 'unknown' based on the file's
    extension.
    """
    ext = get_file_extension(path)
    if ext in IMAGE_EXTS:
        return "image"
    if ext in AUDIO_EXTS:
        return "audio"
    if ext in VIDEO_EXTS:
        return "video"
    return "unknown"
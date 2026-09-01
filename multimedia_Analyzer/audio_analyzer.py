"""
audio_analyzer.py

Responsible for extracting metadata from audio files using ffprobe.
Returns a plain dictionary so report_generator.py can format or save
it however it needs to.
"""

import json
import os
import subprocess

import file_utils


def _run_ffprobe(path):
    """Run ffprobe on a file and return parsed JSON, or None on failure."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", "-show_streams", path],
            capture_output=True, text=True
        )
    except FileNotFoundError:
        return None, "ffprobe not found. Install ffmpeg and make sure it's on your PATH."

    if result.returncode != 0:
        return None, f"ffprobe could not read '{path}'. Is it a valid file?"

    try:
        return json.loads(result.stdout), None
    except json.JSONDecodeError:
        return None, "could not parse ffprobe output."


def analyze_audio(path):
    """
    Analyze an audio file and return a dict of its metadata.
    Returns a dict with an 'error' key if the file can't be read.
    """
    data, error = _run_ffprobe(path)
    if error or data is None:
        return {"error": error or "ffprobe output unavailable."}

    fmt = data.get("format", {})
    streams = data.get("streams", [])
    audio = next((s for s in streams if s.get("codec_type") == "audio"), {})

    try:
        duration = round(float(fmt.get("duration", 0)), 2)
    except (TypeError, ValueError):
        duration = None

    return {
        "file_name": os.path.basename(path),
        "file_size": file_utils.get_file_size(path),
        "file_format": fmt.get("format_long_name", "N/A"),
        "duration_sec": duration,
        "bit_rate": fmt.get("bit_rate", "N/A"),
        "codec": audio.get("codec_long_name", "N/A"),
        "sample_rate": audio.get("sample_rate", "N/A"),
        "channels": audio.get("channels", "N/A"),
        "channel_layout": audio.get("channel_layout", "N/A"),
        "tags": fmt.get("tags", {}),
    }
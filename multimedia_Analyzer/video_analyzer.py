"""
video_analyzer.py

Responsible for extracting metadata from video files using ffprobe.
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


def analyze_video(path):
    """
    Analyze a video file and return a dict of its metadata, split into
    'video', 'audio', and 'metadata' sections.
    Returns a dict with an 'error' key if the file can't be read.
    """
    data, error = _run_ffprobe(path)
    if error or data is None:
        return {"error": error or "ffprobe returned no data."}

    fmt = data.get("format") or {}
    streams = data.get("streams") or []
    video = next((s for s in streams if isinstance(s, dict) and s.get("codec_type") == "video"), {})
    audio = next((s for s in streams if isinstance(s, dict) and s.get("codec_type") == "audio"), {})

    try:
        duration = round(float(fmt.get("duration", 0)), 2)
    except (TypeError, ValueError):
        duration = None

    return {
        "file_name": os.path.basename(path),
        "file_size": file_utils.get_file_size(path),
        "container": fmt.get("format_long_name", "N/A"),
        "duration_sec": duration,
        "video": {
            "resolution": f"{video.get('width', '?')}x{video.get('height', '?')}" if video else "N/A",
            "frame_rate": video.get("r_frame_rate", "N/A"),
            "bit_rate": video.get("bit_rate", fmt.get("bit_rate", "N/A")),
            "codec": video.get("codec_long_name", "N/A"),
        },
        "audio": {
            "codec": audio.get("codec_long_name", "N/A") if audio else "No audio stream",
            "channels": audio.get("channels", "N/A") if audio else "N/A",
            "sampling_rate": audio.get("sample_rate", "N/A") if audio else "N/A",
            "bit_rate": audio.get("bit_rate", "N/A") if audio else "N/A",
        },
        "metadata": fmt.get("tags", {}),
    }
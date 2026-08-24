"""
video_analyzer.py - Print basic metadata for a video file.

Usage: python video_analyzer.py <path-to-video>
Requires: ffprobe (part of ffmpeg) installed and on PATH.
"""

import json
import os
import subprocess
import sys

path = sys.argv[1] if len(sys.argv) > 1 else input("Video path: ")

if not os.path.isfile(path):
    print(f"Error: file not found: {path}")
    sys.exit(1)

try:
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_format", "-show_streams", path],
        capture_output=True, text=True
    )
except FileNotFoundError:
    print("Error: ffprobe not found. Install ffmpeg and make sure it's on your PATH.")
    sys.exit(1)

if result.returncode != 0:
    print(f"Error: ffprobe could not read '{path}'. Is it a valid video file?")
    sys.exit(1)

try:
    data = json.loads(result.stdout)
except json.JSONDecodeError:
    print("Error: could not parse ffprobe output.")
    sys.exit(1)

fmt = data.get("format", {})
streams = data.get("streams", [])
video = next((s for s in streams if s.get("codec_type") == "video"), {})
audio = next((s for s in streams if s.get("codec_type") == "audio"), {})

if not video:
    print("Warning: no video stream found in this file.\n")

print("================================")
print("VIDEO METADATA REPORT")
print("================================")
print(f"File Name       : {os.path.basename(path)}")
print(f"File Size       : {os.path.getsize(path)} bytes")
print(f"File Format     : {fmt.get('format_long_name', 'N/A')}")

try:
    duration = f"{float(fmt.get('duration', 0)):.2f} sec"
except (TypeError, ValueError):
    duration = "N/A"
print(f"Duration        : {duration}")
print(f"Bit Rate        : {fmt.get('bit_rate', 'N/A')} bps")

print("\nVideo Stream")
print("-------------------------------")
if video:
    print(f"Codec           : {video.get('codec_long_name', 'N/A')}")
    print(f"Resolution      : {video.get('width', '?')}x{video.get('height', '?')}")
    print(f"Frame Rate      : {video.get('r_frame_rate', 'N/A')}")
    print(f"Pixel Format    : {video.get('pix_fmt', 'N/A')}")
else:
    print("No video stream found.")

print("\nAudio Stream")
print("-------------------------------")
if audio:
    print(f"Codec           : {audio.get('codec_long_name', 'N/A')}")
    print(f"Sample Rate     : {audio.get('sample_rate', 'N/A')} Hz")
    print(f"Channels        : {audio.get('channels', 'N/A')}")
else:
    print("No audio stream found.")

tags = fmt.get("tags", {})
if tags:
    print("\nTags")
    print("-------------------------------")
    for k, v in tags.items():
        print(f"{k:<16}: {v}")
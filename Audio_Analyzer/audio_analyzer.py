#!/usr/bin/env python3
"""
audio_analyzer.py - Print basic metadata for an audio file.

Usage: python audio_analyzer.py <path-to-audio>
Requires: ffprobe (part of ffmpeg) installed and on PATH.
"""

import json
import os
import subprocess
import sys

path = sys.argv[1] if len(sys.argv) > 1 else input("Audio path: ")

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
    print(f"Error: ffprobe could not read '{path}'. Is it a valid audio file?")
    sys.exit(1)

try:
    data = json.loads(result.stdout)
except json.JSONDecodeError:
    print("Error: could not parse ffprobe output.")
    sys.exit(1)

fmt = data.get("format", {})
streams = data.get("streams", [])
audio = next((s for s in streams if s.get("codec_type") == "audio"), {})

if not audio:
    print("Warning: no audio stream found in this file.\n")

print("================================")
print("AUDIO METADATA REPORT")
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

print("\nAudio Stream")
print("-------------------------------")
if audio:
    print(f"Codec           : {audio.get('codec_long_name', 'N/A')}")
    print(f"Sample Rate     : {audio.get('sample_rate', 'N/A')} Hz")
    print(f"Channels        : {audio.get('channels', 'N/A')}")
    print(f"Channel Layout  : {audio.get('channel_layout', 'N/A')}")
    print(f"Bits Per Sample : {audio.get('bits_per_raw_sample', 'N/A')}")
else:
    print("No audio stream found.")

tags = fmt.get("tags", {})
if tags:
    print("\nTags")
    print("-------------------------------")
    for k, v in tags.items():
        print(f"{k:<16}: {v}")
"""
report_generator.py

Responsible for turning the dictionary produced by an analyzer into:
- a human-readable text report (printed to the console)
- a JSON file saved to disk
"""

import json
import os


def _print_row(label, value, width=16):
    print(f"{label:<{width}}: {value}")


def print_image_report(data):
    print("================================")
    print("IMAGE METADATA REPORT")
    print("================================")
    _print_row("File Name", data.get("file_name", "N/A"))
    _print_row("File Size", f"{data.get('file_size', 'N/A')} bytes")
    _print_row("File Format", data.get("file_format", "N/A"))
    _print_row("Width", f"{data.get('width', 'N/A')} px")
    _print_row("Height", f"{data.get('height', 'N/A')} px")
    _print_row("Resolution", data.get("resolution", "N/A"))
    _print_row("Color Mode", data.get("color_mode", "N/A"))

    print("\nEXIF Metadata")
    print("-------------------------------")
    exif = data.get("exif", {})
    if not exif:
        print("No EXIF metadata found.")
    else:
        for tag, value in exif.items():
            _print_row(tag, value)


def print_audio_report(data):
    print("================================")
    print("AUDIO METADATA REPORT")
    print("================================")
    _print_row("File Name", data.get("file_name", "N/A"))
    _print_row("File Size", f"{data.get('file_size', 'N/A')} bytes")
    _print_row("File Format", data.get("file_format", "N/A"))
    duration = data.get("duration_sec")
    _print_row("Duration", f"{duration} sec" if duration is not None else "N/A")
    _print_row("Bit Rate", f"{data.get('bit_rate', 'N/A')} bps")

    print("\nAudio Stream")
    print("-------------------------------")
    _print_row("Codec", data.get("codec", "N/A"))
    _print_row("Sample Rate", f"{data.get('sample_rate', 'N/A')} Hz")
    _print_row("Channels", data.get("channels", "N/A"))
    _print_row("Channel Layout", data.get("channel_layout", "N/A"))

    tags = data.get("tags", {})
    if tags:
        print("\nTags")
        print("-------------------------------")
        for k, v in tags.items():
            _print_row(k, v)


def print_video_report(data):
    print("================================")
    print("VIDEO METADATA REPORT")
    print("================================")
    _print_row("File Name", data.get("file_name", "N/A"))
    _print_row("File Size", f"{data.get('file_size', 'N/A')} bytes")
    _print_row("Container", data.get("container", "N/A"))
    duration = data.get("duration_sec")
    _print_row("Duration", f"{duration} sec" if duration is not None else "N/A")

    video = data.get("video", {})
    print("\nVIDEO")
    print("--------------------------------")
    _print_row("Resolution", video.get("resolution", "N/A"))
    _print_row("Frame Rate", video.get("frame_rate", "N/A"))
    _print_row("Bit Rate", f"{video.get('bit_rate', 'N/A')} bps")
    _print_row("Codec", video.get("codec", "N/A"))

    audio = data.get("audio", {})
    print("\nAUDIO")
    print("--------------------------------")
    _print_row("Codec", audio.get("codec", "N/A"))
    _print_row("Channels", audio.get("channels", "N/A"))
    _print_row("Sampling Rate", f"{audio.get('sampling_rate', 'N/A')} Hz")
    _print_row("Bit Rate", f"{audio.get('bit_rate', 'N/A')} bps")

    metadata = data.get("metadata", {})
    print("\nMETADATA")
    print("--------------------------------")
    if not metadata:
        print("No additional metadata found.")
    else:
        for k, v in metadata.items():
            _print_row(k, v)


def print_report(file_type, data):
    """Print the appropriate report for the given file type."""
    if "error" in data:
        print(f"Error: {data['error']}")
        return

    if file_type == "image":
        print_image_report(data)
    elif file_type == "audio":
        print_audio_report(data)
    elif file_type == "video":
        print_video_report(data)
    else:
        print(f"Error: cannot generate report for unknown file type.")


def save_report_json(file_type, data, output_path="reports/report.json"):
    """Save the metadata dict as a JSON file, including the file type."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    payload = {"file_type": file_type, **data}
    with open(output_path, "w") as f:
        json.dump(payload, f, indent=2)
    return output_path
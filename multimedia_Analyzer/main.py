#!/usr/bin/env python3
"""
main.py - Consolidated Multimedia Analyzer

Accepts an image, audio, or video file, automatically identifies its
type, runs the matching analyzer, and generates a report (printed to
the console and saved as JSON).

Usage:
    python main.py <path-to-file>

If no path is given, the script prompts for one.
"""

import sys

import file_utils
import image_analyzer
import audio_analyzer
import video_analyzer
import report_generator


def process_file(path):
    """
    Run the full pipeline for a single file:
    validate -> identify type -> analyze -> generate report.
    """
    # 1. File validation
    if not file_utils.file_exists(path):
        print(f"Error: file not found: {path}")
        return

    # 2. Identify file type
    file_type = file_utils.identify_file_type(path)

    if file_type == "unknown":
        ext = file_utils.get_file_extension(path)
        print(f"Error: unsupported file extension '{ext}'.")
        print("Supported types: image, audio, video.")
        return

    # 3. Dispatch to the matching analyzer
    if file_type == "image":
        data = image_analyzer.analyze_image(path)
    elif file_type == "audio":
        data = audio_analyzer.analyze_audio(path)
    else:  # video
        data = video_analyzer.analyze_video(path)

    # 4. Generate the report (console + JSON)
    report_generator.print_report(file_type, data)

    if "error" not in data:
        saved_path = report_generator.save_report_json(file_type, data)
        print(f"\nReport saved to: {saved_path}")


def main():
    if len(sys.argv) > 1:
        for path in sys.argv[1:]:
            process_file(path)
            print()
        return

    print("Enter a file path to analyze (blank line or 'q' to quit).")
    while True:
        path = input("File path: ").strip()
        if not path or path.lower() == "q":
            break
        process_file(path)
        print()


if __name__ == "__main__":
    main()
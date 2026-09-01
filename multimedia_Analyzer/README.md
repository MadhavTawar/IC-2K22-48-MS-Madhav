# Consolidated Multimedia Analyzer

Accepts an image, audio, or video file, automatically identifies its
type, and generates a metadata report — printed to the console and
saved as JSON.

## Architecture

```text
                 User Input
                     |
                     v
              File Validation
                     |
                     v
             Identify File Type
                     |
       +-------------+-------------+
       |             |             |
       v             v             v
    IMAGE          AUDIO         VIDEO
       |             |             |
       v             v             v
 ImageAnalyzer  AudioAnalyzer  VideoAnalyzer
       |             |             |
       +-------------+-------------+
                     |
                     v
             Metadata Extraction
                     |
                     v
              Report Generator
                     |
                     v
            Consolidated Report
```

## Project Structure

```text
multimedia_analyzer/
│
├── main.py                 - orchestrates the pipeline above
├── file_utils.py            - file exists / size / extension / type
├── image_analyzer.py        - image metadata via Pillow
├── audio_analyzer.py        - audio metadata via ffprobe
├── video_analyzer.py        - video metadata via ffprobe
├── report_generator.py      - formats + saves the report
│
├── samples/
│   ├── image.jpg
│   ├── song.mp3
│   └── video.mp4
│
└── reports/
    └── report.json           - written on each successful run
```

## Module Responsibilities

### file_utils.py

- `file_exists(path)` - does the file exist?
- `get_file_size(path)` - file size in bytes
- `get_file_extension(path)` - lowercase extension
- `identify_file_type(path)` - "image" / "audio" / "video" / "unknown"

### image_analyzer.py / audio_analyzer.py / video_analyzer.py

- Each exposes one `analyze_*(path)` function that returns a metadata
  dict (or `{"error": ...}` on failure). No printing happens here —
  these modules only extract data.

### report_generator.py

- `print_report(file_type, data)` - prints the correctly formatted
  report for the given type
- `save_report_json(file_type, data)` - writes the metadata to
  `reports/report.json`

### main.py

- Ties it all together: validates the file, identifies its type,
  dispatches to the right analyzer, then generates the report.

## Requirements

- Python 3.8 or newer
- Pillow (for images)
- `ffprobe` (part of `ffmpeg`, for audio and video) installed and on your PATH

```bash
pip install -r requirements.txt
```

## Usage

Analyze one file:

```bash
python main.py samples/image.jpg
```

Analyze multiple files of any mix of types in one run:

```bash
python main.py samples/image.jpg samples/song.mp3 samples/video.mp4
```

No arguments -> interactive prompt, one file at a time (blank line or
`q` to stop):

```bash
python main.py
Enter a file path to analyze (blank line or 'q' to quit).
File path: samples/image.jpg
...
File path: q
```

Each run prints the report to the console and also writes it to
`reports/report.json`.

## Sample Output

### Image

```text
================================
IMAGE METADATA REPORT
================================
File Name       : image.jpg
File Size       : 1616 bytes
File Format     : JPEG
Width           : 300 px
Height          : 200 px
Resolution      : N/A
Color Mode      : RGB

EXIF Metadata
-------------------------------
No EXIF metadata found.
```

### Audio

```text
================================
AUDIO METADATA REPORT
================================
File Name       : song.mp3
File Size       : 24507 bytes
File Format     : MP2/3 (MPEG audio layer 2/3)
Duration        : 3.03 sec
Bit Rate        : 64700 bps

Audio Stream
-------------------------------
Codec           : MP3 (MPEG audio layer 3)
Sample Rate     : 44100 Hz
Channels        : 1
Channel Layout  : mono

Tags
-------------------------------
title           : Test Tone
artist          : Claude
encoder         : Lavf60.16.100
```

### Video

```text
================================
VIDEO METADATA REPORT
================================
File Name       : video.mp4
File Size       : 30484 bytes
Container       : QuickTime / MOV
Duration        : 2.0 sec

VIDEO
--------------------------------
Resolution      : 320x240
Frame Rate      : 10/1
Bit Rate        : 42232 bps
Codec           : H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10

AUDIO
--------------------------------
Codec           : AAC (Advanced Audio Coding)
Channels        : 1
Sampling Rate   : 44100 Hz
Bit Rate        : 69615 bps

METADATA
--------------------------------
major_brand     : isom
minor_version   : 512
compatible_brands: isomiso2avc1mp41
encoder         : Lavf60.16.100
```

## Error Handling

- Missing file path -> clear error, no traceback
- Unsupported file extension -> clear error listing supported types
- File exists but isn't a valid/readable image, audio, or video -> clear error
- `ffprobe` not installed -> clear error telling you to install ffmpeg
- No audio/video stream in a video file -> falls back to "N/A" / "No audio stream" instead of crashing

## Notes

- File type is currently detected by **extension**, not file content.
  A mislabeled file (wrong or missing extension) will be misrouted or
  rejected as unsupported.
- `reports/report.json` is overwritten on each run. If you want to
  keep a report per file, rename it or pass a custom output path to
  `save_report_json()`.

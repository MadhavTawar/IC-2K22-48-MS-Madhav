# Video Analyzer

A small script that prints a metadata report for a video file: file info,
duration/bitrate, video stream details, audio stream details, and any
embedded tags.

## Requirements

- Python 3
- `ffprobe` (part of `ffmpeg`) installed and available on your PATH

Install ffmpeg:

| OS | Command |
| --- | --- |
| macOS | `brew install ffmpeg` |
| Linux | `sudo apt install ffmpeg` |
| Windows | [Download from ffmpeg.org](https://ffmpeg.org/download.html) or `choco install ffmpeg` |

No pip packages are required — see `requirements.txt`.

## Usage

```text
python video_analyzer.py path/to/video.mp4
```

If no path is given as an argument, the script will prompt for one.

## Sample Output

```text
================================
VIDEO METADATA REPORT
================================
File Name       : test.mp4
File Size       : 30484 bytes
File Format     : QuickTime / MOV
Duration        : 2.00 sec
Bit Rate        : 121936 bps

Video Stream
-------------------------------
Codec           : H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10
Resolution      : 320x240
Frame Rate      : 10/1
Pixel Format    : yuv444p

Audio Stream
-------------------------------
Codec           : AAC (Advanced Audio Coding)
Sample Rate     : 44100 Hz
Channels        : 1

Tags
-------------------------------
major_brand     : isom
minor_version   : 512
compatible_brands: isomiso2avc1mp41
encoder         : Lavf60.16.100
```

## Supported Formats

Any container/codec combination that ffmpeg supports, including:

- MP4
- MOV
- AVI
- MKV
- WEBM

## Notes

- If the file has no audio stream, the script reports that instead of
  audio details.
- Tags (like `encoder` or `major_brand`) are only shown if present in the
  file's container metadata.

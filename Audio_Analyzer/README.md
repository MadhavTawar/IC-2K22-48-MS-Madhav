# Audio Analyzer

A small script that prints a metadata report for an audio file: file
info, duration/bitrate, audio stream details, and any embedded tags
(title, artist, etc.).

## Requirements

- Python 3
- `ffprobe` (part of `ffmpeg`) installed and available on your PATH

Install ffmpeg:

| OS      | Command                                                                |
| ------- | ---------------------------------------------------------------------- |
| macOS   | `brew install ffmpeg`                                                 |
| Linux   | `sudo apt install ffmpeg`                                             |
| Windows | Download from <https://ffmpeg.org/download.html> or `choco install ffmpeg` |

No pip packages are required — see `requirements.txt`.

## Usage

```bash
python audio_analyzer.py path/to/audio.mp3
```

If no path is given as an argument, the script will prompt for one.

## Sample Output

```text
================================
AUDIO METADATA REPORT
================================
File Name       : test.mp3
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
Bits Per Sample : N/A

Tags
-------------------------------
title           : Test Tone
artist          : Claude
encoder         : Lavf60.16.100
```

## Supported Formats

Any audio format ffmpeg supports, including:

- MP3
- WAV
- FLAC
- AAC / M4A
- OGG

## Error Handling

- Missing file path -> clear error, exits without a traceback
- `ffprobe` not installed -> clear error telling you to install ffmpeg
- File exists but isn't a valid/readable audio file -> clear error
- No audio stream found -> warning instead of a hard failure

## Notes

- Tags (like `title`, `artist`, `encoder`) are only shown if present in
  the file's container metadata.

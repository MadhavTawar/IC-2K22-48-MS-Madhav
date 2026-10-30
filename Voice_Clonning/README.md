# Voice Clone TTS

Generate **one** speech file using a single Indian-English voice. The
reference voice is created with Edge TTS, then MegaTTS3 uses that sample to
read new text.

## Setup

Install the dependencies:

```powershell
pip install -r requirements.txt
```

## Generate the Indian-English reference voice

Run this when you want to use the included Indian voice instead of a personal
recording:

```powershell
python generate_sample.py
```

This creates `sample.mp3` with the Indian-English male voice
`en-IN-PrabhatNeural`. It replaces any existing `sample.mp3`. To use your own
voice, put a recording named `sample.mp3` in this folder and skip this step.
Only use recordings you own or have permission to clone.

## Create one cloned recording

Run the script and type the text when prompted:

```powershell
python clone_voice.py
```

The script sends the reference sample and the text you entered to MegaTTS3,
then saves a new recording as `output.mp3`. Run it again and enter different
text to generate another recording. By default, each run replaces the previous
`output.mp3`.

You can also provide text directly on the command line:

```powershell
python clone_voice.py --text "Namaste! Welcome to our class."
```

To keep separate recordings instead of replacing `output.mp3`, choose a
different output filename:

```powershell
python clone_voice.py --text "Namaste! Welcome to our class." --output welcome.mp3
```

The generated voice follows the speaker in `sample.mp3`. To get the Indian
accent, first create the Indian-English sample with `generate_sample.py`, or
provide your own Indian-English reference recording.

## Files

| File | Purpose |
|---|---|
| `generate_sample.py` | Creates one Indian-English reference sample |
| `clone_voice.py` | Clones that sample to speak one custom text |
| `requirements.txt` | Python dependencies |
| `sample.mp3` | Reference recording |
| `output.mp3` | Single generated recording |

The free, community-hosted MegaTTS3 Space may be slow or temporarily
unavailable. Voice cloning should only be used with appropriate consent.

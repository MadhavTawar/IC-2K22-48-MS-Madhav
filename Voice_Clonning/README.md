# Voice Clone TTS — Project Documentation

A simple pipeline to clone a voice from a short audio sample and make it speak
new text. Fully free, no API keys, no sign-up.

## How it works

The project has two stages:

1. **Create a reference voice sample** (`generate_sample.py`)
   Uses Microsoft Edge's free text-to-speech service to generate a short
   audio clip (`sample.mp3`). This clip is the "reference voice" — the voice
   that gets cloned in the next step. You can also skip this and use your
   own recording instead (just name it `sample.mp3`).

2. **Clone the voice and generate new speech** (`clone_voice.py`)
   Sends `sample.mp3` to a free, publicly hosted voice cloning model
   (MegaTTS3, running on Hugging Face Spaces). The model analyzes the tone,
   pitch, and speaking style of the sample, then generates a brand-new audio
   clip (`output.mp3`) saying different text — but in the same voice.

```
generate_sample.py → sample.mp3 → clone_voice.py → output.mp3
   (reference voice)                                (same voice, new words)
```

## Setup

### 1. Install dependencies
```
pip install -r requirements.txt
```

### 2. (Optional) Use your own voice instead of a generated one
Record a clear 15-30 second voice memo and save it as `sample.mp3` in the
project folder. If you skip this, `generate_sample.py` creates one for you.

## Usage

### Step 1 — Create the reference sample
```
python generate_sample.py
```
This creates `sample.mp3`. Edit the `TEXT` variable inside the script to
change what it says, or `VOICE` to change the generated voice:

| Voice | Gender/Accent |
|---|---|
| `en-US-GuyNeural` | Male, US |
| `en-US-JennyNeural` | Female, US |
| `en-US-AriaNeural` | Female, US |
| `en-GB-RyanNeural` | Male, UK |
| `en-GB-SoniaNeural` | Female, UK |
| `en-IN-PrabhatNeural` | Male, Indian |
| `en-IN-NeerjaNeural` | Female, Indian |

Skip this step entirely if you're using your own recording as `sample.mp3`.

### Step 2 — Clone the voice
```
python clone_voice.py
```
This creates `output.mp3`, speaking the `TEXT` inside `clone_voice.py` in
the cloned voice from `sample.mp3`. Edit that `TEXT` variable to change
what the cloned voice says.

## Files

| File | Purpose |
|---|---|
| `generate_sample.py` | Generates a reference voice sample via free Edge TTS |
| `clone_voice.py` | Clones the sample's voice and generates new speech |
| `requirements.txt` | Python dependencies (`edge-tts`, `gradio_client`) |
| `sample.mp3` | The reference voice (generated or your own recording) |
| `output.mp3` | The final cloned-voice output |

## Important notes

- **Voice cloning matches the input.** The output voice will always sound
  like whatever is in `sample.mp3`. To change the output's gender/accent,
  regenerate `sample.mp3` with a different `VOICE`, then rerun
  `clone_voice.py` — you cannot mix a female sample with a male output (or
  vice versa) through cloning; that would require generating two unrelated
  clips instead (no cloning involved).
- **Consent matters.** Only clone voices you own or have explicit permission
  to use.
- **Free tier limits.** The Hugging Face Space (`mrfakename/MegaTTS3-Voice-Cloning`)
  is community-hosted and free, but may occasionally be slow, rate-limited,
  or temporarily down if the owner takes it offline. If `clone_voice.py`
  fails, check the Space's status at huggingface.co/spaces/mrfakename/MegaTTS3-Voice-Cloning.
- **Quality tuning.** In `clone_voice.py`, you can adjust:
  - `infer_timestep` (default 32) — higher = better quality, slower to generate
  - `p_w` (default 1.4) — pronunciation/clarity weight
  - `t_w` (default 3.0) — how closely the output matches the reference voice's tone

## Troubleshooting

| Problem | Fix |
|---|---|
| `ValueError: space is in BUILD_ERROR` | That Space is temporarily broken upstream — wait and retry, or find an alternative Space and update the `Client(...)` name in `clone_voice.py` |
| Output sounds nothing like the sample | Make sure `sample.mp3` is at least ~15-30 seconds of clear, single-speaker audio |
| `ModuleNotFoundError` | Re-run `pip install -r requirements.txt` |
| Script hangs for a long time | The free Space may be queued behind other users' requests — this is normal, just wait |

## Background: why this version (and not paid APIs)

Earlier iterations of this project tried ElevenLabs and Fish Audio's direct
APIs. Both require payment for instant voice cloning on current free tiers
(ElevenLabs cloning is paid-plan-only; Fish Audio's free promotional access
ended August 31, 2026). This version uses a free, community-hosted model
instead, so there's no billing risk and no API key management.
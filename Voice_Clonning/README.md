# Voice Clone — Simple Version

Free, no API keys. Two steps:

```
pip install -r requirements.txt
python generate_sample.py   # creates sample.mp3 (or use your own recording, named sample.mp3)
python clone_voice.py       # creates output.mp3 in that voice, speaking TEXT
```

Edit `TEXT` in each file to change what's spoken. Edit `VOICE` in
generate_sample.py to change the sample's voice (any Edge TTS voice name).

import asyncio
from pathlib import Path

import edge_tts

TEXT = (
    "Namaste! This is a sample of Indian English for a voice cloning project. "
    "Technology helps people share ideas and connect across India."
)
VOICE = "en-IN-PrabhatNeural"

async def main():
    output_path = Path(__file__).resolve().parent / "sample.mp3"
    await edge_tts.Communicate(TEXT, VOICE).save(str(output_path))
    print(f"Saved {output_path}")

if __name__ == "__main__":
    asyncio.run(main())

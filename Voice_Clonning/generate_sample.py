import asyncio
import edge_tts

TEXT = (
    "This is a test recording for my voice cloning project. I'm generating "
    "this sample audio to check that the whole pipeline works correctly "
    "before trying it with a real recording of my own voice."
)
VOICE = "en-US-GuyNeural"  # change to en-US-JennyNeural for a female voice

async def main():
    await edge_tts.Communicate(TEXT, VOICE).save("sample.mp3")
    print("Saved sample.mp3")

if __name__ == "__main__":
    asyncio.run(main())

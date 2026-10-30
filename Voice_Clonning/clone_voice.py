import argparse
from pathlib import Path
import shutil

from gradio_client import Client, handle_file


BASE_DIR = Path(__file__).resolve().parent
REFERENCE_AUDIO = BASE_DIR / "sample.mp3"
DEFAULT_OUTPUT_AUDIO = BASE_DIR / "output.mp3"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate one cloned-voice audio file from text."
    )
    parser.add_argument(
        "--text",
        help="Text to speak. If omitted, the script asks for it interactively.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_AUDIO,
        help="Output audio path (default: Voice_Clonning/output.mp3).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    text = args.text if args.text is not None else input("Enter text to speak: ")
    text = text.strip()
    if not text:
        raise ValueError("Text cannot be empty. Enter the text to generate.")

    if not REFERENCE_AUDIO.is_file():
        raise FileNotFoundError(
            f"Reference audio not found: {REFERENCE_AUDIO}. "
            "Run generate_sample.py first, or add your own sample.mp3."
        )

    output_audio = args.output
    if not output_audio.is_absolute():
        output_audio = BASE_DIR / output_audio
    output_audio.parent.mkdir(parents=True, exist_ok=True)

    client = Client("mrfakename/MegaTTS3-Voice-Cloning")
    result = client.predict(
        inp_audio=handle_file(str(REFERENCE_AUDIO)),
        inp_text=text,
        infer_timestep=32,
        p_w=1.4,
        t_w=3.0,
        api_name="/generate_speech",
    )
    shutil.copy(result, output_audio)
    print(f"Saved cloned-voice recording: {output_audio}")


if __name__ == "__main__":
    main()

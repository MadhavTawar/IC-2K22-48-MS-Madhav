"""Generates all sound effects for FIREFLY MARSH as small .wav files.

Run once:  python make_sounds.py
The files are written to assets/sounds/. Only Python's standard library is used,
so the sounds are fully self-created (no downloads, no external assets).
"""
import math
import os
import random
import struct
import wave

SAMPLE_RATE = 22050
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "sounds")


def tone(freq_start, freq_end, duration, volume=0.5, shape="sine", decay=4.0):
    """One sweeping tone with a short attack and an exponential fade-out."""
    count = int(SAMPLE_RATE * duration)
    samples = []
    phase = 0.0
    for i in range(count):
        progress = i / count
        freq = freq_start + (freq_end - freq_start) * progress
        phase += 2 * math.pi * freq / SAMPLE_RATE
        wave_value = math.sin(phase)
        if shape == "square":
            wave_value = 1.0 if wave_value >= 0 else -1.0
        attack = min(1.0, i / (SAMPLE_RATE * 0.005))
        samples.append(wave_value * volume * attack * math.exp(-decay * progress))
    return samples


def silence(duration):
    return [0.0] * int(SAMPLE_RATE * duration)


def mix_at(base, extra, start_seconds):
    """Adds 'extra' on top of 'base' starting at a time offset."""
    offset = int(SAMPLE_RATE * start_seconds)
    for i, value in enumerate(extra):
        if offset + i < len(base):
            base[offset + i] += value


def save(name, samples):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, name + ".wav")
    with wave.open(path, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        frames = b"".join(
            struct.pack("<h", int(max(-1.0, min(1.0, s)) * 32767)) for s in samples
        )
        wav_file.writeframes(frames)
    print("wrote", path)


def make_dew():
    save("dew", tone(700, 1250, 0.14, 0.5, decay=5.0))


def make_berry():
    sound = silence(0.45)
    mix_at(sound, tone(880, 880, 0.30, 0.4), 0.0)
    mix_at(sound, tone(1320, 1320, 0.30, 0.4), 0.09)
    save("berry", sound)


def make_petal():
    sound = silence(0.5)
    for index, freq in enumerate((523, 659, 784)):
        mix_at(sound, tone(freq, freq, 0.22, 0.35), index * 0.09)
    save("petal", sound)


def make_hit():
    sound = tone(240, 70, 0.35, 0.55, shape="square", decay=3.5)
    noise = random.Random(7)
    for i in range(len(sound)):
        sound[i] += (noise.random() - 0.5) * 0.25 * math.exp(-6 * i / len(sound))
    save("hit", sound)


def make_flare():
    sound = tone(300, 1400, 0.6, 0.45, decay=1.5)
    mix_at(sound, tone(600, 2800, 0.5, 0.2, decay=2.0), 0.05)
    save("flare", sound)


def make_gameover():
    sound = silence(1.1)
    for index, freq in enumerate((523, 440, 349, 262)):
        mix_at(sound, tone(freq, freq * 0.97, 0.35, 0.4, decay=3.0), index * 0.2)
    save("gameover", sound)


def make_ambient():
    """Six seconds of quiet crickets plus a low night hum. Loops without a click."""
    total = 6.0
    sound = silence(total)
    rng = random.Random(3)
    chirp_times = [0.3, 1.1, 1.9, 2.4, 3.3, 4.1, 4.6, 5.3]
    for start in chirp_times:
        for pulse in range(3):
            chirp = tone(4300 + rng.randint(-120, 120), 4300, 0.035, 0.07, decay=2.0)
            mix_at(sound, chirp, start + pulse * 0.055)
    hum = tone(110, 110, total, 0.05, decay=0.0)
    for i in range(len(sound)):
        fade = min(1.0, i / (SAMPLE_RATE * 0.05), (len(sound) - i) / (SAMPLE_RATE * 0.05))
        sound[i] += hum[i] * fade
    save("ambient", sound)


if __name__ == "__main__":
    make_dew()
    make_berry()
    make_petal()
    make_hit()
    make_flare()
    make_gameover()
    make_ambient()

"""Synthesize the original Paper Club score and effects, with no sampled audio.

Run with Python/NumPy from the repository root. Output is 22,050 Hz mono PCM WAV.
The 24-second score uses eight bars at 80 BPM; release tails wrap into its start.
"""
from pathlib import Path
import wave

import numpy as np

RATE = 22050


def tone(frequency, duration, *, soft=False):
    t = np.arange(round(duration * RATE)) / RATE
    envelope = (1 - np.exp(-t / .018)) * np.exp(-t / (1.0 if soft else .12))
    envelope *= np.minimum(1, (duration - t) / .08)
    return envelope * (np.sin(2 * np.pi * frequency * t)
                       + .18 * np.sin(2 * np.pi * frequency * 2 * t)
                       + .035 * np.sin(2 * np.pi * frequency * 3 * t))


def note(midi):
    return 440 * 2 ** ((midi - 69) / 12)


def add(track, sound, at, gain=1, *, wrap=False):
    start = round(at * RATE)
    if wrap:
        np.add.at(track, (np.arange(len(sound)) + start) % len(track), sound * gain)
    else:
        length = min(len(sound), len(track) - start)
        track[start:start + length] += sound[:length] * gain


def write(path, track, peak):
    track = track / max(float(np.max(np.abs(track))), .001) * peak
    pcm = np.round(track * 32767).astype('<i2')
    with wave.open(str(path), 'wb') as stream:
        stream.setparams((1, 2, RATE, len(pcm), 'NONE', 'not compressed'))
        stream.writeframes(pcm.tobytes())


def generate(folder):
    folder.mkdir(parents=True, exist_ok=True)
    music = np.zeros(RATE * 24)
    chords = ((48, 55, 59, 64), (45, 52, 55, 60), (41, 48, 52, 57), (43, 50, 55, 59))
    melody = (76, 74, 72, 71, 72, 69, 67, 71)
    for bar in range(8):
        chord = chords[bar % 4]
        add(music, tone(note(chord[0]), 3.2, soft=True), bar * 3, .22, wrap=True)
        for beat, index in enumerate((1, 2, 3, 2)):
            add(music, tone(note(chord[index]), 2.3, soft=True), bar * 3 + beat * .75, .28, wrap=True)
        add(music, tone(note(melody[bar]), 2.8, soft=True), bar * 3 + .375, .19, wrap=True)
    write(folder / 'music.wav', music, .42)
    patterns = {
        'move': ((69, 0),),
        'menu': ((76, 0),),
        'capture': ((72, 0), (79, .10)),
        'result': ((72, 0), (76, .12), (79, .24), (84, .38)),
    }
    for name, pattern in patterns.items():
        length = {'move': .12, 'menu': .09, 'capture': .18, 'result': .38}[name]
        duration = pattern[-1][1] + length
        track = np.zeros(round(RATE * duration))
        for midi, at in pattern:
            add(track, tone(note(midi), length), at)
        write(folder / f'{name}.wav', track, .28 if name in ('move', 'menu') else .38)


if __name__ == '__main__':
    generate(Path(__file__).resolve().parents[1] / 'assets' / 'audio')

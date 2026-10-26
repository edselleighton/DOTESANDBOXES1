# Paper Club audio

These five PCM WAV files are original synthesized compositions for this game.
They contain no third-party recordings, sampled instruments, or licensed songs.
Regenerate them with `python tools/generate_audio.py` from the repository root.

`music.wav` is a seamless 24-second, eight-bar loop at 80 BPM, with soft harmonic
plucks and a simple original melody. Its release tails wrap across the loop.
`move.wav`, `capture.wav`, `menu.wav`, and `result.wav` are short tonal effects.
All files use 22,050 Hz, 16-bit mono PCM. Playback applies the user's independent
music/effect volumes and mute choices; defaults are 15% and 50% respectively.

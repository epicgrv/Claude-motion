"""The original score as data: shared by the audio stage (synthesis) and the picture (S07 piano keys).

100 BPM, D major. Chords per bar follow the brief's structure:
  0:00-7:20 marimba + soft keys + sub (no drums) -> 7:20 percussion enters -> 11:40 growth ->
  14:67 harmonic resolution -> 16:50 dramatic pause -> 16:80 full chord + low hit -> 18:07 fanfare
  -> 19:20 final resonance.
"""
from __future__ import annotations

import numpy as np

from .config import BAR, BEAT

NOTE = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}
CHORD_TONES = {            # root, third, fifth (pitch classes) - D major diatonic
    "D": (2, 6, 9), "A": (9, 1, 4), "Bm": (11, 2, 6), "G": (7, 11, 2), "Em": (4, 7, 11),
}
D_MAJOR = [2, 4, 6, 7, 9, 11, 1]    # D E F# G A B C#
PENTA = [2, 4, 6, 9, 11]            # D E F# A B  (marimba loves a pentatonic)

CHORDS = [(0.0, "D"), (2.4, "A"), (4.8, "Bm"), (7.2, "G"), (9.6, "D"), (12.0, "Bm"), (14.4, "A"), (14.67, "D"),
          (16.8, "D"), (19.2, "D"), (21.2, "D")]


def chord_at(t: float) -> str:
    c = CHORDS[0][1]
    for t0, name in CHORDS:
        if t >= t0 - 1e-9:
            c = name
    return c


def midi(pc: int, octave: int) -> int:
    return 12 * (octave + 1) + pc


def hz(m: float) -> float:
    return 440.0 * 2 ** ((m - 69) / 12)


def marimba_line(seed: int = 5):
    """[(t, midi, dur, vel)] - the main marimba voice: sparse -> 8ths -> 16ths as the film grows."""
    rng = np.random.default_rng(seed)
    out = []
    step = BEAT / 4          # 16th
    t = 0.45
    pat8 = [0, 2, 1, 3, 2, 4, 3, 1]
    k = 0
    while t < 19.0:
        if 16.45 <= t < 16.8:            # dramatic pause
            t += step
            continue
        # density by section
        if t < 4.8:
            every = 4            # quarters
        elif t < 7.2:
            every = 2            # 8ths
        elif t < 11.4:
            every = 2
        elif t < 16.45:
            every = 1            # 16ths
        else:
            every = 4
        idx = int(round((t - 0.45) / step))
        if idx % every == 0:
            ch = chord_at(t)
            tones = list(CHORD_TONES[ch])
            deg = pat8[k % 8]
            base_pc = [tones[0], PENTA[(deg + 1) % 5], tones[1], PENTA[(deg + 2) % 5], tones[2], PENTA[deg % 5], tones[0], tones[1]][k % 8]
            octv = 5 if (k % 8) < 5 else 6
            vel = 0.55 + 0.25 * rng.random() + (0.15 if idx % 4 == 0 else 0)
            out.append((t, midi(base_pc, octv), step * (3 if every == 4 else 1.8), float(min(vel, 1.0))))
            k += 1
        t += step
    return out


def keys_in(t0: float, t1: float):
    return [n for n in marimba_line() if t0 <= n[0] < t1]

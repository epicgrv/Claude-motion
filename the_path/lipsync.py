"""Jaw / waveform drivers.

If ``out/audio/voice_env.json`` exists (written by the audio stage from the *actual* take) the
envelopes come straight from the recorded dialogue; otherwise a syllable-timed fallback is used so
the picture never depends on the audio stage having run.
"""
from __future__ import annotations

import json
import math

import numpy as np

from .config import FPS, OUT

_ENV = None


def _load():
    global _ENV
    if _ENV is None:
        p = OUT / "audio" / "voice_env.json"
        _ENV = json.loads(p.read_text()) if p.exists() else {}
    return _ENV


def envelope(name, t, t0, dur, syllables, seed=0):
    """Mouth-openness in [0,1] at times ``t`` for the line ``name`` that starts at ``t0``."""
    t = np.asarray(t, float)
    env = _load().get(name)
    if env:
        arr = np.asarray(env["env"], float)
        rate = float(env.get("rate", 100.0))
        x = (t - t0) * rate
        out = np.interp(x, np.arange(len(arr)), arr, left=0.0, right=0.0)
        return np.clip(out, 0, 1)
    rng = np.random.default_rng(seed)
    out = np.zeros_like(t)
    per = dur / max(syllables, 1)
    for k in range(syllables):
        c = t0 + (k + 0.5) * per
        a = rng.uniform(0.55, 1.0)
        w = per * 0.34
        out = np.maximum(out, a * np.exp(-0.5 * ((t - c) / w) ** 2))
    return out


def duration(name, default):
    env = _load().get(name)
    if env:
        return len(env["env"]) / float(env.get("rate", 100.0))
    return default


def bands(name, t, t0, dur, syllables, seed=0):
    """Three envelopes (low / mid / high energy) for the line, shape (3, len(t)).

    From the recording's own band analysis when available (``bands`` key in voice_env.json), else
    derived from the fallback envelope with distinct modulations so bars do not move in unison."""
    t = np.asarray(t, float)
    env = _load().get(name)
    if env and "bands" in env:
        rate = float(env.get("rate", 100.0))
        out = []
        for b in env["bands"]:
            arr = np.asarray(b, float)
            out.append(np.clip(np.interp((t - t0) * rate, np.arange(len(arr)), arr, left=0.0, right=0.0), 0, 1))
        return np.stack(out)
    e = envelope(name, t, t0, dur, syllables, seed)
    lo = e * (0.8 + 0.2 * np.sin(t * 17 + seed))
    mid = e * (0.7 + 0.3 * np.sin(t * 29 + 1 + seed))
    hi = e ** 1.6 * (0.6 + 0.4 * np.sin(t * 41 + 2 + seed))
    return np.stack([lo, mid, hi])

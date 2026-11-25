"""Sound effects for the Infinite Money Glitch short (no music): reuses the shared SFX library (synth + real samples)
from finance_shorts/audio/sound.py and adds a few new ones. Cues follow the tightened voiceover (vo_tight.wav, 79.2 s).

    python3 -m finance_shorts.audio.glitch.sfx   ->  finance_shorts/audio/glitch/sfx.wav  (stereo, 48 kHz)
"""
from pathlib import Path

import numpy as np
import soundfile as sf

from finance_shorts.audio.sound import SR, sfx_lib, load_real, place, norm, osc, noise, filt, env, expd, t_

D = Path(__file__).resolve().parent
TOTAL = 79.5


def extra(L):
    d = 0.42  # error buzz: two short low square pulses
    n = int(d * SR)
    L["error"] = norm(filt(osc(140, d, "square"), "low", 1800) * np.concatenate([env(n // 2, 0.003, 0.1, 0.8, 0.02), env(n - n // 2, 0.003, 0.1, 0.8, 0.04)]))
    d = 1.0  # phone ring: 440 + 480 Hz trill, on 0.4 s / off 0.1 s, twice
    tt = t_(d)
    tone = (np.sin(2 * np.pi * 440 * tt) + np.sin(2 * np.pi * 480 * tt)) * (np.sin(2 * np.pi * 20 * tt) > -0.2)
    gate = ((tt % 0.5) < 0.4).astype(float)
    L["ring"] = norm(tone * gate * 0.6)
    d = 0.8  # digital glitch: stuttering band-passed noise bursts
    x = filt(noise(d), "band", [600, 6000]) * (np.floor(t_(d) * 24) % 2) * np.repeat(np.random.default_rng(3).random(int(d * 24) + 1), SR // 24 + 1)[: int(d * SR)]
    L["glitch"] = norm(x)
    d = 2.2  # snore: breathy low noise swelling twice
    tt = t_(d)
    L["snore"] = norm(filt(noise(d, "brown"), "low", 400) * np.clip(np.sin(2 * np.pi * tt / 1.1), 0, 1) ** 2)
    d = 1.0  # heartbeat: lub-dub
    hb = np.zeros(int(d * SR))
    for at, a in ((0.0, 1.0), (0.22, 0.7)):
        k = int(at * SR)
        thump = osc(55, 0.18) * expd(int(0.18 * SR), 0.05) * a
        hb[k:k + len(thump)] += thump
    L["heart"] = norm(hb)
    d = 0.25  # footstep
    L["step"] = norm(filt(noise(d), "band", [100, 900]) * expd(int(d * SR), 0.03))
    d = 0.5  # bills flutter (short paper swish)
    L["bills"] = norm(filt(noise(d, "pink"), "band", [1500, 7000]) * np.sin(np.linspace(0, np.pi, int(d * SR))) ** 3)
    return L


# (time, effect, gain dB, pan)
CUES = [
    (0.25, "whoosh", -12, 0), (0.5, "slots", -14, 0), (2.6, "kaching", -6, 0), (1.6, "bills", -14, -0.3), (2.4, "bills", -14, 0.3),
    (3.0, "kaching", -12, 0), (3.6, "bills", -14, 0.2), (4.6, "bills", -15, -0.2), (5.6, "bills", -15, 0.1),
    (7.6, "swish", -14, 0), (10.3, "click", -8, 0), (10.35, "ding", -14, 0),
    (11.3, "slam", -6, 0), (11.38, "clunk", -9, 0),
    (13.9, "clink", -12, 0.2), (16.4, "tink", -12, 0), (16.7, "tink", -14, 0), (17.6, "sigh", -12, 0),
    (19.0, "tick", -10, 0) if False else (19.0, "click", -16, 0), (20.0, "click", -16, 0),
    (24.85, "error", -10, 0), (26.25, "kaching", -8, 0),
    (28.3, "click", -12, 0), (28.35, "kaching", -12, 0), (29.6, "click", -12, 0), (29.65, "kaching", -11, 0), (30.9, "click", -12, 0), (30.95, "kaching", -10, 0),
    (32.3, "boop", -12, 0), (32.6, "hiss", -18, 0), (34.6, "snore", -14, 0.2),
    (36.95, "pop", -14, 0), (38.8, "beep", -16, 0), (39.2, "beep", -16, 0), (40.7, "clunk", -12, -0.5), (40.9, "murmur", -14, -0.3),
    (42.8, "jet", -8, 0), (44.4, "ding", -12, 0), (45.6, "pop", -10, 0), (45.7, "murmur", -12, 0), (46.2, "bills", -13, 0), (47.3, "kaching", -10, 0), (48.6, "bills", -14, 0.2),
    (51.3, "swish", -12, 0), (52.0, "swish", -12, 0), (53.3, "swish", -11, 0),
    (56.4, "glitch", -10, 0),
    (58.5, "crickets", -16, 0), (59.2, "heart", -10, 0), (60.2, "heart", -10, 0),
    (61.2, "ring", -12, 0.2), (62.4, "ring", -12, 0.2), (63.0, "heart", -10, 0),
    (64.4, "step", -14, 0), (64.9, "step", -14, 0), (65.4, "step", -14, 0), (65.9, "step", -14, 0), (66.4, "step", -14, 0),
    (66.95, "clunk", -12, 0), (67.4, "thud", -12, 0),
    (69.6, "slam", -6, 0), (69.68, "clunk", -9, 0),
    (72.0, "whoosh", -12, 0), (76.5, "pop", -10, 0), (76.6, "ding", -14, 0),
]


def main():
    L = extra(load_real(sfx_lib()))
    buf = np.zeros((int(TOTAL * SR), 2))
    for at, name, db, pan in CUES:
        if name in L:
            place(buf, L[name], at, 10 ** (db / 20), pan)
    buf = buf / max(1.0, np.abs(buf).max() / 0.9)
    sf.write(D / "sfx.wav", buf.astype(np.float32), SR)
    print("sfx.wav", round(len(buf) / SR, 2), "s,", len(CUES), "cues")


if __name__ == "__main__":
    main()

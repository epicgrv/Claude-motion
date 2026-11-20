"""Original score + synthesized SFX + final mix for the Pepsi-jet short (all generated in code, no samples).

    python -m finance_shorts.audio.sound      -> finance_shorts/audio/pepsi-jet/{music.wav,sfx.wav,mix.wav}
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt, fftconvolve

SR = 48000
DIR = Path(__file__).resolve().parent / "pepsi-jet"
RNG = np.random.default_rng(42)


# ------------------------------------------------------------------------------------------------ dsp
def t_(d):
    return np.arange(int(d * SR)) / SR


def env(n, a=0.003, d=0.2, s=0.0, r=0.05, hold=0.0):
    a_, d_, r_, h_ = int(a * SR), int(d * SR), int(r * SR), int(hold * SR)
    e = np.concatenate([np.linspace(0, 1, max(1, a_)), np.ones(h_), np.linspace(1, s, max(1, d_))])
    e = np.concatenate([e, np.full(max(0, n - len(e) - r_), s), np.linspace(s, 0, max(1, r_))])
    return np.pad(e, (0, max(0, n - len(e))))[:n]


def expd(n, tau):
    return np.exp(-np.arange(n) / (tau * SR))


def filt(x, kind, f, order=2):
    if isinstance(f, (list, tuple)):
        f = [min(v, SR / 2 - 100) for v in f]
    else:
        f = min(f, SR / 2 - 100)
    return sosfilt(butter(order, f, kind, fs=SR, output="sos"), x)


def noise(d, color="white"):
    x = RNG.standard_normal(int(d * SR))
    if color == "pink":
        x = filt(x, "low", 2500, 1) + 0.3 * x
    if color == "brown":
        x = np.cumsum(x)
        x = filt(x - x.mean(), "high", 20)
        x /= np.abs(x).max() + 1e-9
    return x


def osc(f, d, kind="sine", phase=0.0):
    tt = t_(d)
    if callable(f):
        ph = 2 * np.pi * np.cumsum(f(tt)) / SR
    else:
        ph = 2 * np.pi * f * tt
    ph += phase
    if kind == "sine":
        return np.sin(ph)
    if kind == "saw":
        return 2 * ((ph / (2 * np.pi)) % 1) - 1
    if kind == "square":
        return np.sign(np.sin(ph))
    if kind == "tri":
        return 2 * np.abs(2 * ((ph / (2 * np.pi)) % 1) - 1) - 1
    raise ValueError(kind)


def reverb(x, rt=1.2, wet=0.25):
    n = int(rt * SR)
    ir = RNG.standard_normal(n) * np.exp(-6.9 * np.arange(n) / n)
    ir = filt(ir, "low", 6000)
    y = fftconvolve(x, ir)
    y = np.pad(y, (0, max(0, len(x) + n - len(y))))[: len(x) + n]
    y /= np.abs(ir).sum() ** 0.5 * 4
    out = np.pad(x, (0, n)) * (1 - wet) + y * wet
    return out


def norm(x, peak=0.9):
    m = np.abs(x).max()
    return x * (peak / m) if m > 0 else x


# ------------------------------------------------------------------------------------------------ sfx library
def sfx_lib():
    L = {}
    d = 0.18
    L["slap"] = norm(filt(noise(d), "band", [400, 4000]) * expd(int(d * SR), 0.025) + 0.6 * osc(110, d) * expd(int(d * SR), 0.03))
    d = 0.6
    L["whoosh"] = norm(filt(noise(d, "pink"), "band", [300, 3000]) * np.sin(np.linspace(0, np.pi, int(d * SR))) ** 2)
    # jet flyby: rumble + roar + doppler whine
    d = 2.6
    n = int(d * SR)
    sw = np.sin(np.linspace(0, np.pi, n)) ** 1.5
    roar = filt(noise(d, "pink"), "band", [80, 2500]) * sw
    rumble = filt(noise(d, "brown"), "low", 120) * sw * 2
    whine = osc(lambda tt: 1800 - 900 * tt / d, d, "saw") * 0.08 * sw
    L["jet"] = norm(roar + rumble + filt(whine, "low", 4000))
    d = 2.2
    L["hover"] = norm(filt(osc(lambda tt: 900 + 30 * np.sin(tt * 9), d, "saw"), "band", [600, 2500]) * 0.3
                      + filt(noise(d), "band", [300, 1500]) * 0.6) * env(int(d * SR), 0.2, 0.1, 1, 0.3)
    d = 0.5
    L["hiss"] = norm(filt(noise(d), "high", 3000) * env(int(d * SR), 0.01, 0.4, 0, 0.05))
    d = 0.9
    L["ding"] = norm(sum(osc(f, d) * expd(int(d * SR), 0.35 / (i + 1)) for i, f in enumerate([1760, 2637, 3520])))
    d = 0.5
    L["boing"] = norm(osc(lambda tt: 180 + 220 * np.exp(-tt * 6) * np.cos(tt * 60), d) * expd(int(d * SR), 0.18))
    d = 0.35
    L["crunch"] = norm(sum(filt(noise(0.04), "band", [1500, 7000]) * 1.0 for _ in range(1)) if False else
                       np.concatenate([filt(noise(0.035), "band", [1200, 6000]) * expd(int(0.035 * SR), 0.01)
                                       for _ in range(10)])[: int(d * SR)])
    d = 0.08
    L["beep"] = norm(osc(2400, d, "square") * env(int(d * SR), 0.002, 0.02, 0.6, 0.01)) * 0.5
    d = 1.4
    bell = sum(osc(f, d) * expd(int(d * SR), 0.5 / (1 + i * 0.6)) for i, f in enumerate([2093, 2637, 3136, 4186]))
    drawer = filt(noise(0.3), "band", [200, 2000]) * expd(int(0.3 * SR), 0.06)
    L["kaching"] = norm(np.pad(drawer, (0, int(d * SR) - len(drawer))) * 0.8 + np.pad(np.zeros(int(0.12 * SR)), (0, 0)).sum() +
                        np.concatenate([np.zeros(int(0.1 * SR)), bell])[: int(d * SR)])
    d = 0.5
    L["thud"] = norm(osc(lambda tt: 90 * np.exp(-tt * 4) + 40, d) * expd(int(d * SR), 0.12) + filt(noise(d), "low", 300) * expd(int(d * SR), 0.05))
    d = 0.4
    L["tink"] = norm(osc(4200, d) * expd(int(d * SR), 0.12) + osc(6300, d) * expd(int(d * SR), 0.06) * 0.5)
    d = 0.45
    L["chalk"] = norm(filt(noise(d), "band", [2000, 9000]) * (0.5 + 0.5 * np.abs(np.sin(t_(d) * 38))) * env(int(d * SR), 0.01, 0.05, 1, 0.05)) * 0.6
    d = 2.0
    L["stampede"] = norm(sum(np.roll(filt(noise(d, "brown"), "low", 200) * (0.5 + 0.5 * np.sin(t_(d) * 2 * np.pi * (6 + k))), k * 800)
                             for k in range(4)) * env(int(d * SR), 0.3, 0.3, 1, 0.5))
    d = 0.3
    L["bonk"] = norm(osc(lambda tt: 600 * np.exp(-tt * 8) + 200, d) * expd(int(d * SR), 0.06))
    d = 2.0
    cr = np.zeros(int(d * SR))
    for k in range(8):
        s = int((0.1 + k * 0.23) * SR)
        chirp = osc(4300, 0.05) * (0.5 + 0.5 * osc(32, 0.05, "square")) * env(int(0.05 * SR), 0.005, 0.03, 0, 0.01)
        cr[s:s + len(chirp)] += chirp
    L["crickets"] = norm(cr) * 0.6
    d = 0.7
    L["scribble"] = norm(filt(noise(d), "band", [1500, 6000]) * (0.4 + 0.6 * np.abs(np.sin(t_(d) * 22))) * env(int(d * SR), 0.02, 0.1, 1, 0.1)) * 0.5
    d = 0.5
    L["clunk"] = norm(osc(140, d) * expd(int(d * SR), 0.08) + filt(noise(d), "band", [500, 3000]) * expd(int(d * SR), 0.03) * 0.7)
    d = 0.25
    L["boop"] = norm(osc(lambda tt: 900 + 700 * tt / d, d) * env(int(d * SR), 0.005, 0.1, 0.3, 0.05))
    d = 2.2  # angelic "aah" choir pad
    ch = sum(osc(f * (1 + 0.004 * np.sin(k)), d, "saw") for k, f in enumerate([523, 659, 784, 1047]))
    L["choir"] = norm(filt(filt(ch, "band", [500, 3200]), "low", 2500) * env(int(d * SR), 0.25, 0.3, 0.8, 0.8))
    d = 0.9
    L["spray"] = norm(filt(noise(d), "band", [1500, 8000]) * env(int(d * SR), 0.005, 0.5, 0, 0.1))
    d = 0.35
    L["swish"] = norm(filt(noise(d), "band", [800, 5000]) * np.sin(np.linspace(0, np.pi, int(d * SR))) ** 3)
    d = 0.6
    flutter = np.concatenate([filt(noise(0.05), "band", [600, 4000]) * expd(int(0.05 * SR), 0.015) for _ in range(12)])
    L["flutter"] = norm(flutter[: int(d * SR)])
    L["flap"] = norm(osc(220, 0.15) * expd(int(0.15 * SR), 0.03) + filt(noise(0.15), "band", [300, 2500]) * expd(int(0.15 * SR), 0.02))
    # sad trombone: wah wah wah waaah
    tb = []
    for f, du in [(293, 0.32), (277, 0.32), (262, 0.32), (247, 0.9)]:
        x = osc(lambda tt: f * (1 + 0.02 * np.sin(tt * 30 * (tt > 0.3))), du, "saw")
        x = filt(x, "low", 1200) * env(int(du * SR), 0.04, 0.1, 0.8, 0.12)
        tb.append(x)
    L["trombone"] = norm(np.concatenate(tb))
    d = 2.5
    L["murmur"] = norm(sum(filt(noise(d), "band", [200 + k * 60, 900 + k * 80]) * (0.5 + 0.5 * np.sin(t_(d) * (3 + k)))
                           for k in range(5)) * env(int(d * SR), 0.4, 0.3, 1, 0.6)) * 0.5
    d = 0.4
    L["scrape"] = norm(filt(osc(lambda tt: 160 + 60 * tt, d, "saw") * (0.6 + 0.4 * noise(d)), "band", [200, 1500]) * env(int(d * SR), 0.02, 0.2, 0.5, 0.1))
    d = 2.4  # gavel: wood crack + body + big room
    crack = filt(noise(0.03), "band", [800, 6000]) * expd(int(0.03 * SR), 0.006)
    body = osc(lambda tt: 180 * np.exp(-tt * 3) + 70, 0.4) * expd(int(0.4 * SR), 0.07)
    g = np.zeros(int(d * SR))
    g[: len(crack)] += crack * 1.2
    g[: len(body)] += body
    L["gavel"] = norm(reverb(g, 1.8, 0.35)[: int(d * SR)])
    d = 1.6
    L["sigh"] = norm(filt(noise(d, "pink"), "band", [300, 2500]) * env(int(d * SR), 0.25, 1.2, 0, 0.1) * (1 + 0.3 * osc(5, d))) * 0.7
    d = 2.0
    L["engine"] = norm(filt(osc(lambda tt: 38 + 2 * np.sin(tt * 3), d, "saw") + 0.4 * noise(d, "brown"), "low", 400)) * 0.6
    d = 0.12
    L["click"] = norm(filt(noise(d), "high", 2000) * expd(int(d * SR), 0.008))
    d = 1.4
    L["crt"] = norm(osc(15734, d) * 0.05 + filt(noise(d), "high", 6000) * 0.3 + osc(60, d) * 0.2) * env(int(d * SR), 0.01, 0.1, 1, 0.2) * 0.4
    d = 1.4  # slot machine roll
    rl = np.zeros(int(d * SR))
    for k in range(18):
        s = int(k * d / 18 * SR)
        b = osc(1200 + (k % 3) * 300, 0.04, "square") * expd(int(0.04 * SR), 0.01)
        rl[s:s + len(b)] += b
    L["slots"] = norm(rl) * 0.6
    L["slam"] = norm(L["thud"] * 1.0 + np.pad(L["slap"], (0, len(L["thud"]) - len(L["slap"]))))
    d = 1.6
    L["rocket"] = norm(filt(noise(d, "pink"), "band", [200, 4000]) * np.linspace(0.2, 1, int(d * SR)) +
                       osc(lambda tt: 200 + 1400 * (tt / d) ** 2, d, "saw") * 0.15 * np.linspace(0, 1, int(d * SR)))
    d = 0.8
    L["glass"] = norm(sum(osc(f, d) * expd(int(d * SR), 0.1 + 0.05 * k) for k, f in enumerate([3100, 4500, 5200, 6700, 8100]))
                      + filt(noise(d), "high", 3000) * expd(int(d * SR), 0.05))
    L["clink"] = L["tink"] * 0.7
    d = 0.06
    L["type"] = norm(filt(noise(d), "band", [1500, 6000]) * expd(int(d * SR), 0.008)) * 0.5
    d = 0.55  # record scratch
    L["scratch"] = norm(filt(noise(d), "band", [500, 4000]) * (0.5 + 0.5 * np.sin(2 * np.pi * np.cumsum(8 + 30 * np.sin(t_(d) * 9)) / SR))
                        * env(int(d * SR), 0.01, 0.4, 0, 0.05))
    d = 0.5
    L["canclank"] = norm(sum(osc(f, d) * expd(int(d * SR), 0.12) for f in [890, 1340, 2210]) + filt(noise(d), "high", 2000) * expd(int(d * SR), 0.02))
    d = 2.0
    L["traffic"] = norm(filt(noise(d, "brown"), "low", 500) + 0.2 * filt(noise(d), "band", [500, 2000])) * 0.4
    d = 0.9
    L["pour"] = norm(filt(noise(d), "band", [500, 3000]) * (0.6 + 0.4 * np.sin(t_(d) * 40)) * env(int(d * SR), 0.05, 0.2, 0.8, 0.2)) * 0.5
    d = 0.4
    L["pop"] = norm(osc(lambda tt: 600 * np.exp(-tt * 20) + 300, d) * expd(int(d * SR), 0.05))
    return L


REAL = Path(__file__).resolve().parent / "sfx_real"
REAL_MAP = {"jet": "jet", "kaching": "kaching", "gavel": "gavel", "scratch": "scratch", "spray": "spray",
            "stampede": "crowd", "trombone": "trombone", "choir": "choir", "slots": "slots", "glass": "glass",
            "crickets": "crickets", "flutter": "paper"}


def load_real(lib):
    """Replace synthesized effects with real generated recordings where available."""
    import subprocess
    for key, fn in REAL_MAP.items():
        f = REAL / f"{fn}.mp3"
        if not f.exists():
            continue
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(f), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                             capture_output=True, check=True).stdout
        x = np.frombuffer(raw, np.float32).astype(np.float64)
        lib[key] = norm(x)
    return lib


# (time, sfx, gain dB, pan -1..1)
CUES = [
    (0.0, "hover", -10, 0), (0.0, "engine", -12, 0), (0.0, "flutter", -14, 0.3), (0.6, "flutter", -16, -0.3),
    (1.45, "whoosh", -10, -0.2), (2.95, "flap", -10, 0.2), (3.2, "ding", -16, 0),
    (4.15, "jet", 0, 0), (4.4, "whoosh", -6, 0.3),
    (5.86, "click", -10, -0.3), (5.9, "crt", -16, -0.3), (7.44, "hover", -14, 0), (9.5, "hiss", -12, 0.2),
    (10.77, "ding", -10, 0), (11.53, "boing", -8, 0),
    (13.0, "crunch", -9, 0.2), (14.3, "crunch", -12, 0.2),
    (16.55, "ding", -12, 0.1), (17.6, "tink", -10, 0), (18.4, "beep", -14, 0),
    (19.95, "beep", -12, 0), (20.2, "beep", -12, 0), (20.45, "beep", -12, 0), (20.8, "beep", -12, 0), (21.1, "beep", -12, 0),
    (21.5, "kaching", -6, 0), (22.67, "whoosh", -8, 0), (23.3, "thud", -4, 0),
    (24.8, "swish", -8, 0), (25.05, "slap", -6, 0),
    (26.7, "stampede", -8, 0), (27.6, "pop", -12, 0),
    (29.35, "chalk", -10, 0), (29.8, "chalk", -10, 0), (30.3, "chalk", -10, 0), (30.85, "swish", -16, 0), (31.45, "chalk", -10, 0),
    (32.9, "bonk", -8, 0.2),
    (33.96, "pour", -12, 0.3), (34.0, "murmur", -18, 0),
    (36.0, "swish", -14, 0), (37.1, "crickets", -10, 0),
    (37.7, "scribble", -10, 0), (38.6, "scribble", -10, 0), (39.5, "scribble", -10, 0),
    (40.7, "clunk", -6, 0), (41.85, "boop", -10, 0), (43.2, "choir", -10, 0),
    (44.34, "whoosh", -10, 0), (45.6, "traffic", -18, 0),
    (46.12, "spray", -6, 0), (47.0, "swish", -10, 0), (47.3, "thud", -12, 0),
    (48.3, "flap", -8, 0), (48.6, "flutter", -8, 0), (49.1, "flutter", -10, 0.2),
    (50.6, "trombone", -9, 0),
    (53.82, "traffic", -14, 0), (54.6, "murmur", -14, 0),
    (59.7, "scrape", -9, 0.2),
    (61.84, "gavel", 0, 0),
    (62.7, "engine", -14, 0), (64.3, "sigh", -6, 0),
    (65.68, "click", -10, -0.3), (65.7, "crt", -16, -0.3), (66.6, "hover", -18, 0),
    (68.68, "slots", -8, 0), (70.1, "slam", -4, 0),
    (70.9, "rocket", -7, 0), (72.45, "glass", -6, 0),
    (73.8, "thud", -8, 0), (74.2, "clink", -8, 0.2),
    (75.12, "crt", -14, 0), (76.35, "type", -10, 0), (76.5, "type", -10, 0), (76.65, "type", -10, 0), (76.8, "type", -10, 0),
    (77.12, "scratch", -3, 0),
    (79.95, "canclank", -8, 0.2),
]


# ------------------------------------------------------------------------------------------------ score
BPM = 100.0
BEAT = 60 / BPM


def kick(d=0.4):
    return osc(lambda tt: 50 + 110 * np.exp(-tt * 30), d) * expd(int(d * SR), 0.12)


def snare(d=0.25):
    return filt(noise(d), "band", [1500, 8000]) * expd(int(d * SR), 0.05) * 0.7 + osc(190, d) * expd(int(d * SR), 0.03) * 0.5


def hat(d=0.06, open_=False):
    return filt(noise(d if not open_ else 0.25), "high", 7000) * expd(int((d if not open_ else 0.25) * SR), 0.015 if not open_ else 0.08)


def pluck(f, d, bright=3000):
    x = osc(f, d, "saw") * 0.6 + osc(f * 2, d, "square") * 0.15
    return filt(x, "low", bright) * expd(int(d * SR), 0.09)


def bass(f, d):
    x = osc(f, d, "saw") * 0.5 + osc(f, d) * 0.8
    return filt(x, "low", 700) * env(int(d * SR), 0.005, 0.15, 0.6, 0.04)


def pizz(f, d=0.25):
    return (osc(f, d, "tri") + 0.4 * osc(f * 2, d)) * expd(int(d * SR), 0.07)


def place(buf, x, at, gain=1.0, panv=0.0):
    i = int(at * SR)
    if i >= len(buf):
        return
    x = x[: len(buf) - i]
    l, r = np.cos((panv + 1) * np.pi / 4), np.sin((panv + 1) * np.pi / 4)
    buf[i:i + len(x), 0] += x * gain * l * 1.41
    buf[i:i + len(x), 1] += x * gain * r * 1.41


def score(total):
    buf = np.zeros((int(total * SR) + SR, 2))
    # D minor-ish funk: Dm7 - G7 - Bbmaj7 - A7 (2 bars each... 1 bar each here)
    prog = [(73.42, [293.7, 349.2, 440.0, 523.3]), (98.0, [293.7, 392.0, 493.9, 587.3]),
            (58.27, [293.7, 349.2, 440.0, 466.2]), (55.0, [277.2, 329.6, 440.0, 554.4])]
    mel = [587.3, 0, 698.5, 659.3, 587.3, 0, 523.3, 440.0, 466.2, 0, 523.3, 587.3, 554.4, 0, 659.3, 0]
    bar = 4 * BEAT
    stops = [(61.7, 62.7), (77.1, 78.35)]  # full stops: gavel, "just kidding"
    lift = [(10.7, 13.0), (68.6, 74.0)]  # double-time energy
    t = 0.0
    n_bar = 0
    while t < total:
        root, ch = prog[n_bar % 4]
        for b in range(4):
            bt = t + b * BEAT
            if any(a <= bt < e for a, e in stops):
                continue
            intro = bt < 4.2
            place(buf, kick(), bt, 0.0 if intro and b % 2 else (0.9 if b in (0, 2) else 0.0))
            if not intro:
                if b in (1, 3):
                    place(buf, snare(), bt, 0.45)
                for k in range(2 if not any(a <= bt < e for a, e in lift) else 4):
                    place(buf, hat(), bt + k * BEAT / (2 if k < 2 and not any(a <= bt < e for a, e in lift) else 4) + (0.035 if k % 2 else 0), 0.18, 0.3)
            # bass: syncopated
            for off, mul, du in ((0, 1, 0.35), (0.75, 1, 0.15), (1.5, 2, 0.2)):
                place(buf, bass(root * mul, du), bt + off * BEAT / 2, 0.35 if not intro else 0.2)
            # muted guitar chops on the offbeat
            if not intro:
                chop = sum(pluck(f, 0.12, 2400) for f in ch) * 0.25
                place(buf, chop, bt + BEAT / 2, 0.22, -0.4)
            # pizzicato hook
            f = mel[(n_bar * 4 + b) % len(mel)]
            if f and bt > 2.0:
                place(buf, pizz(f), bt, 0.16, 0.35)
                place(buf, pizz(f * 1.5, 0.15), bt + BEAT / 2, 0.06, 0.35)
        t += bar
        n_bar += 1
    # warm pad (filtered detuned saws) following the progression, plus sub-bass
    t = 0.0
    n_bar = 0
    while t < total:
        root, ch = prog[n_bar % 4]
        if not (t < 4.2):
            pad = sum(osc(f, bar, "saw") + osc(f * 1.004, bar, "saw") for f in ch[:3]) / 6
            pad = filt(pad, "low", 1400) * env(int(bar * SR), 0.4, 0.2, 0.8, 0.5)
            place(buf, pad, t, 0.05, -0.2)
            place(buf, osc(root / 2, bar) * env(int(bar * SR), 0.02, 0.2, 0.7, 0.2), t, 0.12)
        t += bar
        n_bar += 1
    for a, b in stops:
        ia, ib = int(a * SR), int(b * SR)
        buf[ia:ib] *= 0.0
    # space: stereo reverb send + gentle tape saturation
    wet = np.stack([reverb(buf[:, 0], 1.4, 1.0)[: len(buf)], reverb(np.roll(buf[:, 1], 300), 1.6, 1.0)[: len(buf)]], 1)
    buf = buf + 0.18 * wet
    buf = np.tanh(buf * 1.3) / 1.3
    # ending button after Buddy's last line
    place(buf, kick(0.6), 80.1, 0.9)
    place(buf, pluck(146.8, 0.5, 1500), 80.1, 0.9)
    return buf[: int(total * SR)]


# ------------------------------------------------------------------------------------------------ mix
def main():
    vo, sr = sf.read(DIR / "vo.wav")
    assert sr == SR
    vo = vo if vo.ndim == 1 else vo.mean(1)
    total = len(vo) / SR + 0.4
    lib = load_real(sfx_lib())
    whips = [1.42, 4.26, 12.97, 21.57, 24.77, 26.69, 33.96, 41.82, 46.1, 61.84, 68.68, 73.78, 78.39]
    for w in whips:
        CUES.append((w - 0.06, "swish", -11, 0))
    sfx = np.zeros((int(total * SR) + SR, 2))
    for at, name, gdb, pn in CUES:
        place(sfx, lib[name], at, 10 ** (gdb / 20), pn)
    sfx = sfx[: int(total * SR)]
    real_music = Path(__file__).resolve().parent / "music_real" / "score.mp3"
    if real_music.exists():
        import subprocess
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(real_music), "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                             capture_output=True, check=True).stdout
        m = np.frombuffer(raw, np.float32).astype(np.float64).reshape(-1, 2)
        m = np.pad(m, ((0, max(0, int(total * SR) - len(m))), (0, 0)))[: int(total * SR)]
        m = m / (np.abs(m).max() + 1e-9) * 0.9
        # comic stops: music drops out on the gavel and on the record scratch, then returns
        g = np.ones(len(m))
        for a, b in ((61.75, 62.75), (77.1, 78.4)):
            ia, ib = int(a * SR), int(b * SR)
            g[ia:ib] = 0.0
            r = int(0.25 * SR)
            g[ib:ib + r] = np.linspace(0, 1, len(g[ib:ib + r]))
            f = int(0.03 * SR)
            g[ia - f:ia] = np.linspace(1, 0, f)
        tail = int((total - 0.6) * SR)
        g[tail:] *= np.linspace(1, 0, len(g[tail:]))
        mus = m * g[:, None] * 1.6
    else:
        mus = score(total)
    # sidechain duck music under voice
    n = int(total * SR)
    v = np.pad(vo, (0, n - len(vo)))
    hop = 480
    e = np.sqrt(np.convolve(v ** 2, np.ones(hop) / hop, "same"))
    duck = np.clip(e / 0.03, 0, 1)
    duck = filt(duck, "low", 6, 1)
    mgain = 10 ** (-17 / 20) * (1 - 0.45 * np.clip(duck, 0, 1))
    mus *= mgain[:, None]
    vo2 = np.stack([v, v], 1)
    mix = vo2 * 1.0 + mus + sfx * 0.55
    sf.write(DIR / "music.wav", mus.astype(np.float32), SR)
    sf.write(DIR / "sfx.wav", sfx.astype(np.float32), SR)
    sf.write(DIR / "mix_raw.wav", (mix / max(1.0, np.abs(mix).max() / 0.98)).astype(np.float32), SR)
    import subprocess
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(DIR / "mix_raw.wav"), "-af",
                    "volume=2.5dB,alimiter=limit=0.85:attack=3:release=60:level=disabled,loudnorm=I=-14:TP=-1.0:LRA=11", "-ar", "48000", str(DIR / "mix.wav")], check=True)
    # exact loudness: measure, apply gain, true-peak limit; twice to converge on -14 LUFS
    import re as _re
    for _ in range(2):
        out = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(DIR / "mix.wav"), "-af", "ebur128=framelog=quiet", "-f", "null", "-"],
                             capture_output=True, text=True).stderr
        cur = float(_re.findall(r"I:\s+(-?[0-9.]+) LUFS", out)[-1])
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(DIR / "mix.wav"), "-af",
                        f"volume={-14.0 - cur:.2f}dB,alimiter=limit=0.89:attack=2:release=40:level=disabled",
                        "-ar", "48000", str(DIR / "mix_tmp.wav")], check=True)
        (DIR / "mix_tmp.wav").replace(DIR / "mix.wav")
    print("mix ok", total)


if __name__ == "__main__":
    main()

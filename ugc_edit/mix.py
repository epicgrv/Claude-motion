"""SFX bed from Drive pack + synthesized shutter. python3 mix.py sfx_dir out.wav"""
import sys, subprocess, numpy as np, wave
D, OUT = sys.argv[1], sys.argv[2]
SR, DUR = 48000, 13.417
bus = np.zeros((int(DUR * SR) + SR * 2, 2), np.float32)

def load(name):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f"{D}/{name}", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
    a = np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
    return a / (np.abs(a).max() + 1e-9)

def db(x): return 10 ** (x / 20)

def place(sig, t, gain_db, fade_out=None, lp=None):
    s = sig.copy()
    if fade_out:
        n = int(fade_out * SR); s = s[:n]
        s[-int(0.15 * SR):] *= np.linspace(1, 0, int(0.15 * SR))[:, None]
    if lp:   # simple one-pole lowpass to soften
        k = lp
        for c in range(2):
            y = np.empty(len(s), np.float32); v = 0.0
            for i, x in enumerate(s[:, c]): v += k * (x - v); y[i] = v
            s[:, c] = y
    i = int(t * SR)
    if i < 0: s = s[-i:]; i = 0
    n = min(len(s), len(bus) - i)
    bus[i:i + n] += s[:n] * db(gain_db)

def shutter():  # crisp camera shutter (two-blade click)
    rng = np.random.default_rng(1); n = int(0.18 * SR); out = np.zeros(n, np.float32)
    for off, g in [(0.0, 1.0), (0.045, 0.75)]:
        m = int(0.02 * SR); i = int(off * SR); tt = np.arange(m) / SR
        nz = rng.standard_normal(m) * np.exp(-tt / 0.0035)
        out[i:i + m] += (np.diff(np.r_[0, nz]) * 0.7 + np.sin(2 * np.pi * 4200 * tt) * np.exp(-tt / 0.003) * 0.6) * g
    out /= np.abs(out).max()
    return np.stack([out, out], 1)

click = load("click-button.mp3"); boom = load("Cinematic_boom_01.wav")
whoosh = load("Short whoose_1.mp3"); swoosh = load("smooth woosh.wav")[: int(1.6 * SR)]
riser = load("riser.mp3"); drop = load("Sinematic Short Synth Drop.wav")
pop = load("Pop sound effect 1pop up sound effectpop smokeballon pop sound effectpop sound effect youtuber.mp3")
ding = load("Correct.mp3")

# HOOK: shutter + click + cinematic boom + reverse woosh pulling out with zoom
place(shutter(), 0.0, -4)
place(click, 0.0, -8)
place(boom, -0.08, -9)
place(swoosh[::-1].copy()[-int(1.0 * SR):], -0.55, -17)        # tail lands at ~0.45
place(swoosh, 0.02, -16, fade_out=1.1)

# TRANSITIONS (peak of whoosh ~0.5s / ~0.4s into file)
place(riser[int(1.9 * SR):int(2.95 * SR)], 4.0 - 1.05, -24)
place(whoosh, 4.0 - 0.5, -10)
place(boom, 4.0 - 0.1, -19, fade_out=1.4)
place(swoosh, 7.958 - 0.4, -12, fade_out=1.0)
place(boom, 7.958 - 0.1, -21, fade_out=1.2)
place(whoosh, 12.0 - 0.5, -10)
place(drop, 12.0 - 0.33, -21, fade_out=1.75)                   # soft synth bloom on product hero

# PUNCH-INS: subtle click
for t in [3.32, 5.28, 8.70, 11.16]:
    place(click, t, -19)
# CAPTION ACCENTS: soft pops on key words
for t in [1.98, 5.28, 8.70]:
    place(pop, t, -24, lp=0.35)
place(ding, 11.16, -24)
place(ding, 12.40, -23)

bus = bus[: int(DUR * SR)]
peak = np.abs(bus).max()
if peak > 0.95: bus *= 0.95 / peak
w = wave.open(OUT, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(bus, -1, 1) * 32767).astype("<i2").tobytes()); w.close()
print("ok peak", peak)

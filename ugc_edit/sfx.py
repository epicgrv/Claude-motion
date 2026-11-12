"""Synthesize SFX bed (48k stereo) timed to edit. Usage: python3 sfx.py out.wav"""
import sys, json, numpy as np, wave
SR = 48000
DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 13.417
rng = np.random.default_rng(7)
L = int(DUR * SR) + SR
bus = np.zeros((L, 2))

def env(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)

def lp(x, k):  # one-pole lowpass, k in (0,1)
    y = np.empty_like(x); s = 0.0
    for i, v in enumerate(x):
        s += k * (v - s); y[i] = s
    return y

def place(sig, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if sig.ndim == 1:
        sig = np.stack([sig * (1 - max(pan, 0)), sig * (1 + min(pan, 0))], 1)
    n = min(len(sig), L - i)
    bus[i:i + n] += sig[:n] * gain

def click():  # camera shutter: two mechanical clicks + air
    n = int(0.25 * SR)
    out = np.zeros(n)
    for off, g, d in [(0, 1.0, 0.004), (0.055, 0.7, 0.006)]:
        m = int(0.03 * SR); i = int(off * SR)
        nz = rng.standard_normal(m)
        hi = nz - lp(nz, 0.35)
        tone = np.sin(2 * np.pi * 3200 * np.arange(m) / SR)
        out[i:i + m] += (hi * 0.8 + tone * 0.3) * env(m, 0.0003, d) * g
    nz = rng.standard_normal(n)
    out += (nz - lp(nz, 0.2)) * env(n, 0.002, 0.04) * 0.15
    return out / np.abs(out).max()

def boom():  # sub hit
    n = int(1.2 * SR); t = np.arange(n) / SR
    f = 38 + 70 * np.exp(-t * 18)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.003, 0.35)
    return s / np.abs(s).max()

def whoosh(d=0.45, up=True):
    n = int(d * SR); t = np.linspace(0, 1, n)
    nz = rng.standard_normal(n)
    # sweep filter cutoff
    k = (0.02 + 0.5 * (t if up else 1 - t) ** 2)
    y = np.empty(n); s = 0.0
    for i in range(n):
        s += k[i] * (nz[i] - s); y[i] = s
    shape = np.sin(np.pi * t) ** 1.5
    y = y * shape
    return y / np.abs(y).max()

def riser(d=0.6):
    n = int(d * SR); t = np.linspace(0, 1, n)
    nz = rng.standard_normal(n)
    y = (nz - lp(nz, 0.3)) * t ** 3
    tone = np.sin(2 * np.pi * np.cumsum(300 + 1500 * t ** 2) / SR) * t ** 3 * 0.25
    y = y * 0.6 + tone
    return y / np.abs(y).max()

def pop():
    n = int(0.08 * SR); t = np.arange(n) / SR
    s = np.sin(2 * np.pi * (900 - 4000 * t) * t) * env(n, 0.001, 0.015)
    return s / np.abs(s).max()

def shimmer():
    n = int(1.4 * SR); t = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * t) / (j + 1) for j, f in enumerate([2093, 2637, 3136, 4186]))
    s *= env(n, 0.01, 0.35)
    return s / np.abs(s).max()

ev = json.load(open(sys.argv[3])) if len(sys.argv) > 3 else {}
# hook
place(click(), 0.00, 0.9)
place(boom(), 0.00, 0.55)
place(whoosh(0.5, False), 0.02, 0.25, -0.2)
# transitions
for t in ev.get("cuts", []):
    place(riser(0.35), t - 0.35, 0.18)
    place(whoosh(0.4, True), t - 0.22, 0.42, 0.25)
    place(boom(), t, 0.22)
for t in ev.get("pops", []):
    place(pop(), t, 0.10)
for t in ev.get("shimmer", []):
    place(shimmer(), t, 0.16)

bus = bus[:int(DUR * SR)]
bus = np.tanh(bus * 1.1) * 0.85
w = wave.open(sys.argv[1], "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((bus * 32767).astype("<i2").tobytes()); w.close()

"""Small, dependable DSP toolkit (numpy/scipy) for the original score, the SFX library and the mix.

Everything is rendered offline at 48 kHz; nothing is sampled or downloaded - every sound is synthesised.
"""
from __future__ import annotations

import math
import wave
from pathlib import Path

import numpy as np
from scipy import signal

SR = 48000


# ------------------------------------------------------------------ basics
def n_of(dur):
    return int(round(dur * SR))


def tt(dur):
    return np.arange(n_of(dur)) / SR


def db(x):
    return 10 ** (x / 20.0)


def rng_for(seed):
    return np.random.default_rng(seed)


def exp_env(n, tau, attack=0.002):
    t = np.arange(n) / SR
    e = np.exp(-t / max(tau, 1e-4))
    if attack > 0:
        a = np.minimum(1.0, t / attack)
        e = e * a
    return e


def adsr(n, a=0.01, d=0.1, s=0.7, r=0.2):
    na, nd, nr = n_of(a), n_of(d), n_of(r)
    ns = max(0, n - na - nd - nr)
    parts = [np.linspace(0, 1, max(na, 1), endpoint=False), np.linspace(1, s, max(nd, 1), endpoint=False),
             np.full(ns, s), np.linspace(s, 0, max(nr, 1))]
    e = np.concatenate(parts)
    if len(e) < n:
        e = np.pad(e, (0, n - len(e)))
    return e[:n]


def sine(f, dur, phase=0.0):
    return np.sin(2 * math.pi * f * tt(dur) + phase)


def sweep(f0, f1, dur, curve="exp"):
    t = tt(dur)
    if curve == "exp":
        k = (f1 / f0) ** (1 / max(dur, 1e-6))
        ph = 2 * math.pi * f0 * (k ** t - 1) / math.log(k) if abs(k - 1) > 1e-9 else 2 * math.pi * f0 * t
    else:
        ph = 2 * math.pi * (f0 * t + (f1 - f0) * t ** 2 / (2 * dur))
    return np.sin(ph)


def saw(f, dur, detune=0.0):
    t = tt(dur)
    x = 2 * ((t * f * (1 + detune)) % 1.0) - 1
    return x


def noise(dur, seed=0, color="white"):
    r = rng_for(seed)
    x = r.standard_normal(n_of(dur))
    if color == "pink":
        b, a = [0.049922035, -0.095993537, 0.050612699, -0.004408786], [1, -2.494956002, 2.017265875, -0.522189400]
        x = signal.lfilter(b, a, x)
    return x / (np.std(x) + 1e-9)


def _sos(kind, fc, order, fs=SR):
    fc = np.clip(fc, 5, fs / 2 - 100)
    return signal.butter(order, fc, btype=kind, fs=fs, output="sos")


def lp(x, fc, order=2):
    return signal.sosfilt(_sos("low", fc, order), x, axis=0)


def hp(x, fc, order=2):
    return signal.sosfilt(_sos("high", fc, order), x, axis=0)


def bp(x, f0, f1, order=2):
    return signal.sosfilt(_sos("band", [max(f0, 5), min(f1, SR / 2 - 100)], order), x, axis=0)


def tilt_sweep_filter(x, f_start, f_end, kind="low", order=2, steps=24):
    """Time-varying one-pole style sweep by crossfading a handful of static filters (cheap & smooth)."""
    n = len(x)
    fcs = np.geomspace(f_start, f_end, steps)
    out = np.zeros(n)
    edges = np.linspace(0, n, steps + 1).astype(int)
    xs = [signal.sosfilt(_sos(kind, fc, order), x) for fc in fcs]
    pos = np.linspace(0, steps - 1, n)
    i0 = np.clip(pos.astype(int), 0, steps - 2)
    fr = pos - i0
    for k in range(steps - 1):
        m = i0 == k
        out[m] = xs[k][m] * (1 - fr[m]) + xs[k + 1][m] * fr[m]
    return out


def pan(x, p):
    """Equal-power pan of a mono signal, p in [-1,1] -> (n,2)."""
    a = (p + 1) * math.pi / 4
    return np.stack([x * math.cos(a), x * math.sin(a)], axis=1)


def stereo(x):
    return np.stack([x, x], axis=1) if x.ndim == 1 else x


def fit(x, n):
    if x.shape[0] >= n:
        return x[:n]
    pad = [(0, n - x.shape[0])] + [(0, 0)] * (x.ndim - 1)
    return np.pad(x, pad)


def fade(x, a=0.002, r=0.01):
    x = x.copy()
    na, nr = n_of(a), n_of(r)
    if na > 0:
        x[:na] *= np.linspace(0, 1, na)[(...,) + (None,) * (x.ndim - 1)]
    if nr > 0:
        x[-nr:] *= np.linspace(1, 0, nr)[(...,) + (None,) * (x.ndim - 1)]
    return x


def soft_clip(x, drive=1.0):
    return np.tanh(x * drive) / np.tanh(drive)


def normalize(x, peak=0.9):
    m = np.max(np.abs(x)) + 1e-9
    return x * (peak / m)


# ------------------------------------------------------------------ space
_IR_CACHE = {}


def reverb_ir(rt60=1.2, pre=0.012, damp=7000, seed=1, width=1.0):
    key = (round(rt60, 3), round(pre, 4), damp, seed, width)
    if key in _IR_CACHE:
        return _IR_CACHE[key]
    n = n_of(rt60 * 1.1)
    r = rng_for(seed)
    L = r.standard_normal(n)
    R = r.standard_normal(n) if width > 0 else L
    R = L * (1 - width) + R * width
    t = np.arange(n) / SR
    env = np.exp(-6.9 * t / rt60)
    ir = np.stack([L * env, R * env], axis=1)
    ir = signal.sosfilt(_sos("low", damp, 2), ir, axis=0)
    ir[: n_of(pre)] = 0
    ir = ir / (np.sqrt(np.sum(ir ** 2)) + 1e-9)
    _IR_CACHE[key] = ir
    return ir


def reverb(x, wet=0.25, rt60=1.2, pre=0.012, damp=7000, seed=1, tail=True):
    x = stereo(x)
    ir = reverb_ir(rt60, pre, damp, seed)
    n = x.shape[0] + (ir.shape[0] - 1 if tail else 0)
    wl = fit(signal.fftconvolve(x[:, 0], ir[:, 0]), n)
    wr = fit(signal.fftconvolve(x[:, 1], ir[:, 1]), n)
    wet_sig = np.stack([wl, wr], axis=1)
    dry = fit(x, n)
    return dry * (1 - wet * 0.5) + wet_sig * wet * 1.6


def delay(x, time, fb=0.35, mix=0.25, lp_hz=5000):
    x = stereo(x)
    n = n_of(time)
    out = np.zeros((x.shape[0] + n * 6, 2))
    out[: x.shape[0]] += x
    sig = x.copy()
    for k in range(1, 6):
        sig = lp(sig, lp_hz, 1) * fb
        out[k * n: k * n + sig.shape[0]] += sig * mix * (1 if k % 2 else 1)
    return out


# ------------------------------------------------------------------ timeline mixing
class Track:
    def __init__(self, dur):
        self.n = n_of(dur)
        self.buf = np.zeros((self.n, 2))

    def add(self, x, t0, gain=1.0, p=0.0):
        x = stereo(x) if x.ndim == 1 else x
        if x.ndim == 1:
            x = pan(x, p)
        elif p != 0.0 and np.allclose(x[:, 0], x[:, 1]):
            x = pan(x[:, 0], p)
        i0 = n_of(t0)
        if i0 >= self.n:
            return
        a = max(0, -i0)
        x = x[a:]
        i0 = max(i0, 0)
        m = min(x.shape[0], self.n - i0)
        if m > 0:
            self.buf[i0:i0 + m] += x[:m] * gain


def write_wav(path, x, sr=SR):
    """Write float stereo/mono as 24-bit PCM WAV."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    x = np.asarray(x)
    if x.ndim == 1:
        x = x[:, None]
    x = np.clip(x, -1.0, 1.0)
    i = (x * (2 ** 23 - 1)).astype(np.int32)
    b = np.empty((i.shape[0], i.shape[1], 3), dtype=np.uint8)
    b[..., 0] = i & 0xFF
    b[..., 1] = (i >> 8) & 0xFF
    b[..., 2] = (i >> 16) & 0xFF
    with wave.open(str(path), "wb") as w:
        w.setnchannels(x.shape[1])
        w.setsampwidth(3)
        w.setframerate(sr)
        w.writeframes(b.reshape(-1).tobytes())


def read_wav(path):
    """-> (float array (n,ch), sr). Handles 16/24-bit PCM via scipy."""
    from scipy.io import wavfile
    sr, d = wavfile.read(str(path))
    if d.dtype == np.int16:
        x = d.astype(np.float64) / 32768
    elif d.dtype == np.int32:
        x = d.astype(np.float64) / 2147483648
    elif d.dtype == np.uint8:
        x = (d.astype(np.float64) - 128) / 128
    else:
        x = d.astype(np.float64)
    if x.ndim == 1:
        x = x[:, None]
    return x, sr


def resample(x, sr_from, sr_to=SR):
    if sr_from == sr_to:
        return x
    g = math.gcd(int(sr_from), int(sr_to))
    return signal.resample_poly(x, sr_to // g, sr_from // g, axis=0)


def vary_rate(x, rate):
    """Play back at ``rate`` (>1 = faster/higher). Pitch and duration change together, like a sampler."""
    if abs(rate - 1.0) < 1e-3:
        return x
    from fractions import Fraction
    fr = Fraction(rate).limit_denominator(100)
    return signal.resample_poly(x, fr.denominator, fr.numerator, axis=0)

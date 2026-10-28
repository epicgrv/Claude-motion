"""Easing, spring dynamics and spline utilities (pure numpy; no bpy).

Nothing in the film is animated with plain linear interpolation: every move goes through one
of these curves so it has anticipation, overshoot, inertia or a controlled landing.
"""
from __future__ import annotations

import math
from typing import Callable, Sequence

import numpy as np


# ------------------------------------------------------------------ basics
def clamp(x, lo=0.0, hi=1.0):
    return np.minimum(np.maximum(x, lo), hi)


def remap(x, a, b, c=0.0, d=1.0):
    return c + (d - c) * clamp((x - a) / (b - a) if b != a else 0.0 * x)


def u(t, t0, t1):
    """Normalised, clamped progress of t within [t0,t1]."""
    return clamp((np.asarray(t, dtype=float) - t0) / (t1 - t0))


def lerp(a, b, k):
    return a + (b - a) * k


def smoothstep(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def smootherstep(x):
    x = clamp(x)
    return x * x * x * (x * (x * 6 - 15) + 10)


def in_cubic(x):
    x = clamp(x)
    return x ** 3


def out_cubic(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def in_out_cubic(x):
    x = clamp(x)
    return np.where(x < 0.5, 4 * x ** 3, 1 - (-2 * x + 2) ** 3 / 2)


def in_quart(x):
    return clamp(x) ** 4


def out_quart(x):
    return 1 - (1 - clamp(x)) ** 4


def in_out_quart(x):
    x = clamp(x)
    return np.where(x < 0.5, 8 * x ** 4, 1 - (-2 * x + 2) ** 4 / 2)


def out_expo(x):
    x = clamp(x)
    return np.where(x >= 1, 1.0, 1 - 2 ** (-10 * x))


def in_expo(x):
    x = clamp(x)
    return np.where(x <= 0, 0.0, 2 ** (10 * x - 10))


def out_back(x, c=1.70158):
    x = clamp(x)
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def in_back(x, c=1.70158):
    x = clamp(x)
    return (c + 1) * x ** 3 - c * x ** 2


def in_out_back(x, c=1.70158 * 1.525):
    x = clamp(x)
    return np.where(
        x < 0.5,
        ((2 * x) ** 2 * ((c + 1) * 2 * x - c)) / 2,
        ((2 * x - 2) ** 2 * ((c + 1) * (x * 2 - 2) + c) + 2) / 2,
    )


def bezier_ease(x1, y1, x2, y2):
    """CSS-style cubic-bezier(x1,y1,x2,y2) easing as a vectorised callable."""
    xs = np.linspace(0, 1, 513)
    s = xs
    bx = 3 * (1 - s) ** 2 * s * x1 + 3 * (1 - s) * s ** 2 * x2 + s ** 3
    by = 3 * (1 - s) ** 2 * s * y1 + 3 * (1 - s) * s ** 2 * y2 + s ** 3

    def f(x):
        return np.interp(clamp(x), bx, by)

    return f


# Named house curves used across the film
EXPLOSIVE = bezier_ease(0.05, 0.9, 0.12, 1.0)      # almost all the move in the first 15%
SNAP = bezier_ease(0.2, 0.0, 0.0, 1.0)               # quick start, long soft landing
GLIDE = bezier_ease(0.45, 0.0, 0.2, 1.0)             # elegant, balanced
ANTICIPATE = bezier_ease(0.55, -0.35, 0.25, 1.0)     # dips back before going
HEAVY = bezier_ease(0.6, 0.0, 0.3, 1.0)              # weighty start, soft stop


# ------------------------------------------------------------------ springs
def spring_step(x, v, target, k, c, dt, sub=4):
    """Semi-implicit Euler for x'' = -k(x-target) - c x'. Returns (x, v)."""
    h = dt / sub
    for _ in range(sub):
        a = -k * (x - target) - c * v
        v = v + a * h
        x = x + v * h
    return x, v


def spring_follow(series: Sequence[float], fps: float, freq: float, zeta: float,
                  x0=None, v0=0.0):
    """Drive a damped spring with a target series (one value per frame).

    ``freq`` in Hz, ``zeta`` damping ratio (<1 = overshoot). Returns the response series.
    Used for secondary motion: wings lag the torso, tiles settle, cards ring after impact.
    """
    series = np.asarray(series, dtype=float)
    k = (2 * math.pi * freq) ** 2
    c = 2 * zeta * 2 * math.pi * freq
    x = series[0] if x0 is None else x0
    v = v0
    out = np.empty_like(series)
    dt = 1.0 / fps
    for i, tgt in enumerate(series):
        x, v = spring_step(x, v, tgt, k, c, dt)
        out[i] = x
    return out


def damped_osc(t, amp, freq, zeta, phase=0.0):
    """Free damped oscillation a*exp(-zeta*w*t)*cos(sqrt(1-z^2)*w*t+phase) for t>=0."""
    t = np.asarray(t, dtype=float)
    w = 2 * math.pi * freq
    wd = w * math.sqrt(max(1e-6, 1 - zeta ** 2))
    return np.where(t >= 0, amp * np.exp(-zeta * w * np.maximum(t, 0)) * np.cos(wd * np.maximum(t, 0) + phase), 0.0)


def settle(t, t0, dur, overshoot=0.12, freq=3.2):
    """0->1 step with a physically damped overshoot/settle, starting at t0 (dur = rise time)."""
    t = np.asarray(t, dtype=float)
    rise = smootherstep((t - t0) / dur)
    zeta = -math.log(max(overshoot, 1e-4)) / math.sqrt(math.pi ** 2 + math.log(max(overshoot, 1e-4)) ** 2) if overshoot > 0 else 1.0
    tt = t - (t0 + dur)
    ring = np.where(tt > 0, -overshoot * 0.0 + damped_osc(tt, -overshoot, freq, max(zeta, 0.15)), 0.0)
    return rise + ring * (tt > 0)


def bounce_series(t, t0, v0, g, e, ground=0.0, max_b=6):
    """Height of a ball dropped/thrown at t0 with speed v0 (up), gravity g, restitution e."""
    t = np.asarray(t, dtype=float)
    out = np.full_like(t, ground, dtype=float)
    tt = t - t0
    y = ground
    v = v0
    tb = 0.0
    for _ in range(max_b):
        # time to land from height y with vertical speed v
        disc = v * v + 2 * g * (y - ground)
        if disc < 0:
            break
        tl = (v + math.sqrt(disc)) / g
        m = (tt >= tb) & (tt < tb + tl)
        local = tt - tb
        out = np.where(m, y + v * local - 0.5 * g * local ** 2, out)
        v = (v - g * tl) * -e
        y = ground
        tb += tl
        if abs(v) < 0.05:
            break
    return out


# ------------------------------------------------------------------ splines
def catmull_rom(points: np.ndarray, n: int = 200, closed=False, alpha=0.5):
    """Centripetal Catmull-Rom through ``points`` (N,3) -> (n,3) densely sampled curve."""
    P = np.asarray(points, dtype=float)
    if len(P) < 3:
        return np.linspace(P[0], P[-1], n)
    if not closed:
        P = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    segs = len(P) - 3
    per = max(2, int(math.ceil(n / segs)))
    out = []
    for i in range(segs):
        p0, p1, p2, p3 = P[i], P[i + 1], P[i + 2], P[i + 3]
        t0 = 0.0
        t1 = t0 + np.linalg.norm(p1 - p0) ** alpha + 1e-9
        t2 = t1 + np.linalg.norm(p2 - p1) ** alpha + 1e-9
        t3 = t2 + np.linalg.norm(p3 - p2) ** alpha + 1e-9
        tt = np.linspace(t1, t2, per, endpoint=(i == segs - 1))[:, None]
        a1 = (t1 - tt) / (t1 - t0) * p0 + (tt - t0) / (t1 - t0) * p1
        a2 = (t2 - tt) / (t2 - t1) * p1 + (tt - t1) / (t2 - t1) * p2
        a3 = (t3 - tt) / (t3 - t2) * p2 + (tt - t2) / (t3 - t2) * p3
        b1 = (t2 - tt) / (t2 - t0) * a1 + (tt - t0) / (t2 - t0) * a2
        b2 = (t3 - tt) / (t3 - t1) * a2 + (tt - t1) / (t3 - t1) * a3
        c = (t2 - tt) / (t2 - t1) * b1 + (tt - t1) / (t2 - t1) * b2
        out.append(c)
    return np.vstack(out)


class Polyline:
    """Arc-length parametrised dense curve: p(s) with s in [0, L]."""

    def __init__(self, pts: np.ndarray):
        self.pts = np.asarray(pts, dtype=float)
        d = np.linalg.norm(np.diff(self.pts, axis=0), axis=1)
        self.cum = np.concatenate([[0.0], np.cumsum(d)])
        self.length = float(self.cum[-1])

    def at(self, s):
        s = np.clip(np.asarray(s, dtype=float), 0, self.length)
        x = np.interp(s, self.cum, self.pts[:, 0])
        y = np.interp(s, self.cum, self.pts[:, 1])
        z = np.interp(s, self.cum, self.pts[:, 2])
        return np.stack([x, y, z], axis=-1)

    def tangent(self, s, eps=0.02):
        a = self.at(np.asarray(s) - eps)
        b = self.at(np.asarray(s) + eps)
        d = b - a
        n = np.linalg.norm(d, axis=-1, keepdims=True) + 1e-12
        return d / n

    def frac(self, f):
        return self.at(np.asarray(f) * self.length)


def hermite(p0, p1, m0, m1, h, x):
    """Cubic Hermite on a segment of duration h; x in [0,1]. Works for vectors."""
    x = np.asarray(x)[..., None] if np.ndim(p0) > 0 else np.asarray(x)
    x2, x3 = x * x, x * x * x
    return ((2 * x3 - 3 * x2 + 1) * p0 + (x3 - 2 * x2 + x) * h * m0 +
            (-2 * x3 + 3 * x2) * p1 + (x3 - x2) * h * m1)


class KeySpline:
    """C1 time-keyed spline through vector (or scalar) keys with per-key speed scaling.

    Tangents are non-uniform Catmull-Rom (so the motion flows through keys instead of
    stopping on them). ``tension[i]`` multiplies the tangent at key i: 1 = flow, 0 = come to
    rest exactly on the key (used for deliberate holds and landings). No overshoot clamp is
    applied - authors choose keys that make the move visually interesting.
    """

    def __init__(self, times: Sequence[float], values, tension: Sequence[float] | None = None):
        self.t = np.asarray(times, dtype=float)
        self.v = np.asarray(values, dtype=float)
        n = len(self.t)
        self.tension = np.ones(n) if tension is None else np.asarray(tension, dtype=float)
        scalar = self.v.ndim == 1
        V = self.v[:, None] if scalar else self.v
        m = np.zeros_like(V)
        for i in range(n):
            if i == 0:
                m[i] = (V[1] - V[0]) / (self.t[1] - self.t[0])
            elif i == n - 1:
                m[i] = (V[-1] - V[-2]) / (self.t[-1] - self.t[-2])
            else:
                m[i] = (V[i + 1] - V[i - 1]) / (self.t[i + 1] - self.t[i - 1])
            m[i] *= self.tension[i]
        self.m = m
        self.V = V
        self.scalar = scalar

    def __call__(self, t):
        t = np.atleast_1d(np.asarray(t, dtype=float))
        idx = np.clip(np.searchsorted(self.t, t, side="right") - 1, 0, len(self.t) - 2)
        t0 = self.t[idx]
        h = self.t[idx + 1] - t0
        x = clamp((t - t0) / h)[:, None]
        p0, p1 = self.V[idx], self.V[idx + 1]
        m0, m1 = self.m[idx], self.m[idx + 1]
        x2, x3 = x * x, x * x * x
        out = ((2 * x3 - 3 * x2 + 1) * p0 + (x3 - 2 * x2 + x) * h[:, None] * m0 +
               (-2 * x3 + 3 * x2) * p1 + (x3 - x2) * h[:, None] * m1)
        return out[:, 0] if self.scalar else out


def noise1d(t, seed=0, octaves=3):
    """Smooth deterministic 1-D value noise in [-1,1] (for subtle handheld drift)."""
    t = np.asarray(t, dtype=float)
    out = np.zeros_like(t)
    amp = 1.0
    norm = 0.0
    for o in range(octaves):
        f = 2 ** o
        x = t * f
        i = np.floor(x).astype(int)
        fr = x - i
        rng_a = _hash(i + seed * 131 + o * 977)
        rng_b = _hash(i + 1 + seed * 131 + o * 977)
        out += amp * (rng_a + (rng_b - rng_a) * smoothstep(fr))
        norm += amp
        amp *= 0.5
    return out / norm


def _hash(i):
    i = np.asarray(i, dtype=np.int64)
    h = (i * 374761393 + 668265263) & 0xFFFFFFFF
    h = (h ^ (h >> 13)) * 1274126177 & 0xFFFFFFFF
    h = h ^ (h >> 16)
    return (h & 0xFFFF) / 32767.5 - 1.0


def norm(v):
    v = np.asarray(v, dtype=float)
    return v / (np.linalg.norm(v, axis=-1, keepdims=True) + 1e-12)

"""The SFX library: ~100 synthesised effects in the brief's categories.

  Movimiento  whooshes of different scale, spatial passes, accelerations, decelerations, direction changes
  Materiales  soft contacts, button pulses, slides, muffled hits, vibrations, bounces, mechanical clacks
  Energía     light activations, propagation, transformations, ignitions, pulses
  Personaje   wing flaps, jumps, landings, reactions (non-verbal chirps)
  Marca       correct-answer chimes, check-on, tile/word ladder, signature
  Impactos    booms, cracks, glass shards, risers, reverse swells, sparkles, ticks

Original sounds only - nothing imitates Duolingo's own audio identity; official sounds may be dropped into
``assets/sfx/<name>.wav`` and they override the synthesised version of the same name.
"""
from __future__ import annotations

import math

import numpy as np

from ..config import ASSETS, OUT
from . import dsp
from .dsp import SR

AUDIO = OUT / "audio" / "sfx"
LIB: dict[str, np.ndarray] = {}
CAT: dict[str, str] = {}


def reg(cat, name, x):
    x = np.asarray(x, float)
    LIB[name] = x
    CAT[name] = cat


def _bell_env(n, peak=0.35, skew=2.0):
    t = np.linspace(0, 1, n)
    e = np.sin(np.pi * t ** (1 / skew)) ** 2
    return e


# ------------------------------------------------------------------ movement
def gen_movement():
    for i, (f0, f1, d) in enumerate(((900, 4200, 0.30), (1100, 3600, 0.36), (700, 5200, 0.28))):
        n = dsp.n_of(d)
        x = dsp.noise(d, 10 + i)
        x = dsp.tilt_sweep_filter(x, f0, f1, "low") * 0.0 + dsp.bp(x, f0, f1, 2) * _bell_env(n, skew=1.6)
        reg("movimiento", f"mv_whoosh_s_{i+1:02d}", dsp.stereo(x * 0.7))
    for i, (f0, f1, d) in enumerate(((400, 2800, 0.7), (350, 3300, 0.8), (500, 2400, 0.65))):
        n = dsp.n_of(d)
        x = dsp.noise(d, 20 + i, "pink")
        x = dsp.tilt_sweep_filter(x, f0, f1, "low", steps=20)
        x = dsp.hp(x, 180) * _bell_env(n, skew=1.8)
        reg("movimiento", f"mv_whoosh_m_{i+1:02d}", dsp.stereo(x * 0.6))
    for i, (f0, f1, d) in enumerate(((140, 2200, 1.3), (200, 1800, 1.2), (110, 2600, 1.5))):
        n = dsp.n_of(d)
        x = dsp.noise(d, 30 + i, "pink")
        x = dsp.tilt_sweep_filter(x, f0, f1, "low", steps=24) * _bell_env(n, skew=2.2)
        x += 0.5 * dsp.lp(dsp.noise(d, 40 + i), 90) * _bell_env(n, skew=1.4)
        reg("movimiento", f"mv_whoosh_l_{i+1:02d}", dsp.stereo(x * 0.55))
    for i, d in enumerate((0.8, 1.0)):
        n = dsp.n_of(d)
        x = dsp.tilt_sweep_filter(dsp.noise(d, 50 + i), 300, 6000, "low", steps=20) * (np.linspace(0, 1, n) ** 2.4)
        reg("movimiento", f"mv_whoosh_rev_{i+1:02d}", dsp.stereo(x * 0.6))
    for i, d in enumerate((0.9, 1.1)):
        n = dsp.n_of(d)
        x = dsp.tilt_sweep_filter(dsp.noise(d, 60 + i, "pink"), 1800, 220, "low") * _bell_env(n)
        t = np.arange(n) / SR
        x += 0.12 * np.sin(2 * math.pi * (900 - 520 * t / d) * t) * _bell_env(n)
        pan_l = np.linspace(-1, 1, n) * (1 if i == 0 else -1)
        a = (pan_l + 1) * math.pi / 4
        reg("movimiento", f"mv_pass_{i+1:02d}", np.stack([x * np.cos(a), x * np.sin(a)], axis=1) * 0.7)
    for i, (f0, f1) in enumerate(((180, 900), (220, 1200))):
        d = 0.8
        n = dsp.n_of(d)
        x = dsp.sweep(f0, f1, d) * 0.35 + dsp.bp(dsp.noise(d, 70 + i), f0 * 2, f1 * 3) * 0.35
        reg("movimiento", f"mv_accel_{i+1:02d}", dsp.stereo(x * np.linspace(0.1, 1, n) * dsp.exp_env(n, 2.0, 0.01)))
        y = dsp.sweep(f1, f0, d) * 0.35 + dsp.bp(dsp.noise(d, 72 + i), f0 * 2, f1 * 3) * 0.35
        reg("movimiento", f"mv_decel_{i+1:02d}", dsp.stereo(y * np.linspace(1, 0.05, n) ** 1.2 * dsp.exp_env(n, 1.0, 0.004)))
    for i, d in enumerate((0.5, 0.6)):
        n = dsp.n_of(d)
        x = dsp.noise(d, 80 + i)
        c = 1200 + 1800 * np.sin(np.linspace(0, math.pi, n))
        # up-then-down formant sweep for a change of direction
        xs = dsp.tilt_sweep_filter(x, 600, 3200, "low", steps=12)
        xs = xs[: n // 2].tolist() + dsp.tilt_sweep_filter(x, 3200, 600, "low", steps=12)[n // 2:].tolist()
        reg("movimiento", f"mv_turn_{i+1:02d}", dsp.stereo(np.array(xs) * _bell_env(n) * 0.6))


# ------------------------------------------------------------------ materials
def gen_materials():
    for i, (f, d) in enumerate(((70, 0.09), (85, 0.08), (60, 0.11), (95, 0.07))):
        n = dsp.n_of(d)
        x = dsp.sine(f, d) * dsp.exp_env(n, d * 0.35, 0.001) + 0.5 * dsp.lp(dsp.noise(d, 100 + i), 700) * dsp.exp_env(n, d * 0.2, 0.0005)
        reg("materiales", f"mt_contact_{i+1:02d}", dsp.stereo(x * 0.9))
    for i, f in enumerate((880, 1000, 760, 1150)):
        d = 0.11
        n = dsp.n_of(d)
        x = dsp.sine(f, 0.012) * dsp.exp_env(dsp.n_of(0.012), 0.004, 0.0003)
        body = dsp.sine(170 + 20 * i, d) * dsp.exp_env(n, 0.035, 0.001)
        y = body.copy()
        y[: len(x)] += x * 0.8
        reg("materiales", f"mt_button_{i+1:02d}", dsp.stereo(y * 0.8))
    for i, (f0, f1) in enumerate(((600, 2200), (900, 1500), (400, 1800))):
        d = 0.32
        n = dsp.n_of(d)
        x = dsp.tilt_sweep_filter(dsp.noise(d, 110 + i), f0, f1, "low") * _bell_env(n, skew=1.2) * 0.6
        x = dsp.bp(x, f0 * 0.6, f1 * 1.4)
        reg("materiales", f"mt_slide_{i+1:02d}", dsp.stereo(x))
    for i, f in enumerate((55, 70, 48, 62)):
        d = 0.2
        n = dsp.n_of(d)
        x = dsp.lp(dsp.noise(d, 120 + i), 420) * dsp.exp_env(n, 0.05, 0.001) + dsp.sine(f, d) * dsp.exp_env(n, 0.09, 0.001)
        reg("materiales", f"mt_muffled_{i+1:02d}", dsp.stereo(x * 0.9))
    for i, f in enumerate((130, 175, 220)):
        d = 0.55
        n = dsp.n_of(d)
        t = np.arange(n) / SR
        x = dsp.sine(f, d) * (1 + 0.5 * np.sin(2 * math.pi * 24 * t)) * dsp.exp_env(n, 0.18, 0.002)
        x += 0.3 * dsp.sine(f * 2.01, d) * dsp.exp_env(n, 0.1, 0.002)
        reg("materiales", f"mt_vibe_{i+1:02d}", dsp.stereo(x * 0.5))
    for i, f in enumerate((75, 90, 65)):
        d = 0.6
        out = np.zeros(dsp.n_of(d))
        tcur, amp = 0.0, 1.0
        gap = 0.16
        while tcur < d - 0.05 and amp > 0.08:
            h = (dsp.sine(f * (1 + 0.1 * (1 - amp)), 0.1) * dsp.exp_env(dsp.n_of(0.1), 0.03, 0.001)) * amp
            k = dsp.n_of(tcur)
            out[k:k + len(h)] += h[: max(0, len(out) - k)]
            tcur += gap
            gap *= 0.62
            amp *= 0.58
        reg("materiales", f"mt_bounce_{i+1:02d}", dsp.stereo(out * 0.9))
    for i, (fc, d) in enumerate(((3200, 0.035), (4200, 0.03), (2600, 0.04), (3600, 0.028))):
        n = dsp.n_of(d)
        x = dsp.bp(dsp.noise(d, 130 + i), fc * 0.7, fc * 1.5) * dsp.exp_env(n, d * 0.3, 0.0003)
        x += 0.5 * dsp.sine(fc * 0.55, d) * dsp.exp_env(n, d * 0.3, 0.0003)
        reg("materiales", f"mt_clack_{i+1:02d}", dsp.stereo(x * 0.7))


# ------------------------------------------------------------------ energy
def gen_energy():
    for i, (f0, f1) in enumerate(((600, 1800), (700, 2100), (500, 1500), (800, 2400), (650, 2000))):
        d = 0.32
        n = dsp.n_of(d)
        x = dsp.sweep(f0, f1, d * 0.6) * 0.5
        x = dsp.fit(x, n) + 0.25 * dsp.sine(f1 * 1.5, d) * dsp.exp_env(n, 0.12, 0.004) + 0.2 * dsp.hp(dsp.noise(d, 140 + i), 5000) * dsp.exp_env(n, 0.06, 0.002)
        reg("energia", f"en_light_{i+1:02d}", dsp.reverb(dsp.stereo(x * dsp.exp_env(n, 0.14, 0.003) * 0.5), 0.15, 0.4))
    for i, d in enumerate((0.9, 1.1, 0.8)):
        n = dsp.n_of(d)
        t = np.arange(n) / SR
        x = dsp.sine(240 + 80 * i, d) * (0.5 + 0.5 * np.sin(2 * math.pi * (9 + 3 * i) * t)) * _bell_env(n)
        x += 0.4 * dsp.bp(dsp.noise(d, 150 + i), 1500, 5000) * _bell_env(n, skew=1.4)
        a = np.linspace(-0.8, 0.8, n) * (1 if i % 2 == 0 else -1)
        ang = (a + 1) * math.pi / 4
        reg("energia", f"en_propagate_{i+1:02d}", np.stack([x * np.cos(ang), x * np.sin(ang)], axis=1) * 0.5)
    for i, d in enumerate((0.7, 0.9, 0.6)):
        n = dsp.n_of(d)
        t = np.arange(n) / SR
        x = dsp.sine(300 + 90 * i, d) * (1 + 0.8 * np.sin(2 * math.pi * 33 * t * (1 + t / d))) * _bell_env(n) * 0.4
        x += dsp.tilt_sweep_filter(dsp.noise(d, 160 + i), 400, 6000, "low") * _bell_env(n) * 0.25
        reg("energia", f"en_transform_{i+1:02d}", dsp.reverb(dsp.stereo(x), 0.2, 0.6))
    for i, d in enumerate((1.1, 0.9)):
        n = dsp.n_of(d)
        low = dsp.sweep(110, 42, d) * dsp.exp_env(n, 0.25, 0.002) * 0.9
        crackle = dsp.hp(dsp.noise(d, 170 + i), 2500) * (np.random.default_rng(i).random(n) > 0.9985) * 6
        crackle = dsp.lp(crackle, 9000) * dsp.exp_env(n, 0.35, 0.002)
        air = dsp.tilt_sweep_filter(dsp.noise(d, 175 + i), 3000, 600, "low") * dsp.exp_env(n, 0.22, 0.003) * 0.5
        reg("energia", f"en_ignite_{i+1:02d}", dsp.reverb(dsp.stereo(low + crackle * 0.5 + air), 0.15, 0.7))
    for i, f in enumerate((62, 72, 55, 80)):
        d = 0.4
        n = dsp.n_of(d)
        x = dsp.sine(f, d) * (np.sin(np.pi * np.linspace(0, 1, n)) ** 1.5) + 0.12 * dsp.hp(dsp.noise(d, 180 + i), 4000) * dsp.exp_env(n, 0.1, 0.004)
        reg("energia", f"en_pulse_{i+1:02d}", dsp.stereo(x * 0.85))


# ------------------------------------------------------------------ character
def gen_character():
    for i, (fc, d) in enumerate(((1800, 0.26), (2300, 0.22), (1500, 0.3), (2000, 0.24))):
        n = dsp.n_of(d)
        t = np.arange(n) / SR
        am = 0.5 + 0.5 * np.sin(2 * math.pi * (22 + 3 * i) * t)
        x = dsp.bp(dsp.noise(d, 200 + i), fc * 0.4, fc * 1.6) * am * _bell_env(n, skew=1.3)
        reg("personaje", f"ch_wing_{i+1:02d}", dsp.stereo(x * 0.8))
    for i, (f0, f1) in enumerate(((220, 640), (260, 760), (200, 560))):
        d = 0.28
        n = dsp.n_of(d)
        x = dsp.sweep(f0, f1, d) * 0.5 * dsp.exp_env(n, 0.12, 0.003) + dsp.bp(dsp.noise(d, 210 + i), 800, 3200) * 0.3 * _bell_env(n)
        reg("personaje", f"ch_jump_{i+1:02d}", dsp.stereo(x))
    for i, f in enumerate((72, 88, 64)):
        d = 0.3
        n = dsp.n_of(d)
        x = dsp.sine(f, d) * dsp.exp_env(n, 0.09, 0.001) + 0.4 * dsp.lp(dsp.noise(d, 220 + i), 900) * dsp.exp_env(n, 0.05, 0.0005)
        sq = dsp.sweep(520, 190, 0.12) * dsp.exp_env(dsp.n_of(0.12), 0.05, 0.002) * 0.2
        x[: len(sq)] += sq
        reg("personaje", f"ch_land_{i+1:02d}", dsp.stereo(x * 0.9))
    for i, (f, v) in enumerate(((880, 0.0), (1040, 0.5), (760, 0.0), (1200, 1.0))):
        d = 0.24 + 0.05 * i
        n = dsp.n_of(d)
        t = np.arange(n) / SR
        fm = f * (1 + 0.35 * np.sin(np.pi * t / d)) * (1 + 0.012 * np.sin(2 * math.pi * 6 * t) * v)
        ph = 2 * math.pi * np.cumsum(fm) / SR
        x = (np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.12 * np.sin(3 * ph)) * _bell_env(n, skew=1.6) * 0.35
        reg("personaje", f"ch_chirp_{i+1:02d}", dsp.reverb(dsp.stereo(x), 0.1, 0.3))


# ------------------------------------------------------------------ brand
def _bellnote(f, d, vel=1.0):
    n = dsp.n_of(d)
    t = np.arange(n) / SR
    return (np.sin(2 * math.pi * f * t) * np.exp(-t / 0.42) + 0.4 * np.sin(2 * math.pi * f * 2.76 * t) * np.exp(-t / 0.16)
            + 0.18 * np.sin(2 * math.pi * f * 5.4 * t) * np.exp(-t / 0.07)) * vel * dsp.exp_env(n, 5, 0.0008)


def gen_brand():
    # correct answer #1: bright rising two-note chime with a marimba body (original voicing in D)
    out = np.zeros(dsp.n_of(1.2))
    for k, (f, dt) in enumerate(((1174.7, 0.0), (1568.0, 0.11))):
        b = _bellnote(f, 1.0, 0.8) * 0.5
        out[dsp.n_of(dt): dsp.n_of(dt) + len(b)] += b[: len(out) - dsp.n_of(dt)]
    from . import music
    mb = music.marimba(587.3, 0.5, 0.9)[: dsp.n_of(0.6)]
    out[: len(mb)] += mb * 0.55
    reg("marca", "br_correct_01", dsp.reverb(dsp.stereo(out), 0.22, 0.9))
    # correct answer #2: three notes, a step higher, a little more sparkle
    out = np.zeros(dsp.n_of(1.5))
    for f, dt in ((1174.7, 0.0), (1480.0, 0.09), (1760.0, 0.18)):
        b = _bellnote(f, 1.2, 0.85) * 0.5
        out[dsp.n_of(dt): dsp.n_of(dt) + len(b)] += b[: len(out) - dsp.n_of(dt)]
    mb = music.marimba(880.0, 0.6, 0.9)[: dsp.n_of(0.7)]
    out[: len(mb)] += mb * 0.5
    sp = dsp.hp(dsp.noise(0.4, 230), 7000) * dsp.exp_env(dsp.n_of(0.4), 0.12, 0.005) * 0.12
    out[dsp.n_of(0.18): dsp.n_of(0.18) + len(sp)] += sp
    reg("marca", "br_correct_02", dsp.reverb(dsp.stereo(out), 0.25, 1.1))
    # check button waking up
    out = np.zeros(dsp.n_of(0.6))
    for f, dt in ((880.0, 0.0), (1318.5, 0.07)):
        b = _bellnote(f, 0.5, 0.7) * 0.4
        out[dsp.n_of(dt): dsp.n_of(dt) + len(b)] += b[: len(out) - dsp.n_of(dt)]
    reg("marca", "br_check_on", dsp.reverb(dsp.stereo(out), 0.15, 0.5))
    # word/tile ladder (D major pentatonic ascending): the click of each tile locking
    for i, f in enumerate((587.3, 659.3, 740.0, 880.0, 987.8, 1174.7, 1318.5, 1480.0)):
        d = 0.35
        n = dsp.n_of(d)
        mb = music.marimba(f, 0.3, 0.85)[:n]
        tick = dsp.bp(dsp.noise(0.012, 240 + i), 1500, 5000) * dsp.exp_env(dsp.n_of(0.012), 0.003, 0.0002)
        y = np.zeros(n)
        y[: len(mb)] += mb
        y[: len(tick)] += tick * 0.35
        reg("marca", f"br_ladder_{i+1:02d}", dsp.reverb(dsp.stereo(y * 0.9), 0.1, 0.3))
    # signature switching on: a low warm hum that settles, one soft tick
    d = 1.2
    n = dsp.n_of(d)
    t = np.arange(n) / SR
    hum = (dsp.sine(110, d) + 0.5 * dsp.sine(220, d) + 0.2 * dsp.sine(330, d)) * np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2 * 0.25
    hum[: dsp.n_of(0.01)] += 0.0
    tk = dsp.bp(dsp.noise(0.01, 250), 2000, 6000) * dsp.exp_env(dsp.n_of(0.01), 0.002, 0.0002) * 0.3
    hum[: len(tk)] += tk
    reg("marca", "br_signature_on", dsp.reverb(dsp.stereo(hum), 0.25, 1.2))


# ------------------------------------------------------------------ impacts & misc
def gen_impacts():
    for i, (f0, f1, d) in enumerate(((120, 34, 1.4), (100, 38, 1.1), (90, 40, 0.9))):
        n = dsp.n_of(d)
        low = dsp.sweep(f0, f1, d) * dsp.exp_env(n, d * 0.35, 0.0006)
        sub2 = dsp.sine(f1 * 1.02, d) * dsp.exp_env(n, d * 0.45, 0.002) * 0.6
        thump = dsp.lp(dsp.noise(0.25, 260 + i), 600) * dsp.exp_env(dsp.n_of(0.25), 0.05, 0.0005)
        y = low + sub2
        y[: len(thump)] += thump * 0.6
        y = dsp.hp(y, 38) + 0.35 * dsp.sine(f1 * 3.0, d) * dsp.exp_env(n, d * 0.2, 0.001)      # harmonics so it still reads on a phone
        reg("impactos", f"im_boom_{i+1:02d}", dsp.reverb(dsp.stereo(dsp.soft_clip(y * 1.0, 1.2) * 0.8), 0.12, 0.9))
    d = 0.5
    n = dsp.n_of(d)
    crack = dsp.hp(dsp.noise(d, 270), 1800) * dsp.exp_env(n, 0.04, 0.0003) * 0.9 + dsp.bp(dsp.noise(d, 271), 300, 1200) * dsp.exp_env(n, 0.12, 0.0005) * 0.5
    reg("impactos", "im_crack_01", dsp.reverb(dsp.stereo(crack), 0.2, 0.6))
    for i in range(3):
        d = 0.9
        n = dsp.n_of(d)
        out = np.zeros(n)
        r = np.random.default_rng(280 + i)
        for k in range(26):
            t0 = float(r.uniform(0, 0.55) ** 1.3)
            f = float(r.uniform(2500, 9000))
            h = dsp.sine(f, 0.05) * dsp.exp_env(dsp.n_of(0.05), float(r.uniform(0.006, 0.018)), 0.0002) * float(r.uniform(0.2, 0.7))
            j = dsp.n_of(t0)
            out[j:j + len(h)] += h[: n - j]
        reg("impactos", f"im_glass_{i+1:02d}", dsp.reverb(dsp.stereo(out * 0.6), 0.3, 1.0))
    for i, d in enumerate((1.2, 0.9)):
        n = dsp.n_of(d)
        x = dsp.tilt_sweep_filter(dsp.noise(d, 290 + i), 400, 10000, "high", steps=18) * np.linspace(0, 1, n) ** 2.2
        t = np.arange(n) / SR
        x += 0.25 * dsp.sweep(180, 1400, d) * np.linspace(0, 1, n) ** 2
        reg("impactos", f"im_riser_{i+1:02d}", dsp.stereo(x * 0.5))
    for i in range(4):
        d = 0.8
        n = dsp.n_of(d)
        out = np.zeros(n)
        r = np.random.default_rng(300 + i)
        for k in range(7):
            f = float(r.choice([1174.7, 1318.5, 1480.0, 1568.0, 1760.0, 1975.5, 2349.3]))
            t0 = float(r.uniform(0, 0.4))
            b = _bellnote(f, 0.45, 0.5) * 0.3
            j = dsp.n_of(t0)
            out[j:j + len(b)] += b[: n - j]
        reg("impactos", f"im_sparkle_{i+1:02d}", dsp.reverb(dsp.stereo(out), 0.3, 1.0))
    for i, f in enumerate((2400, 2000, 3000, 1800, 2700, 3400)):
        d = 0.05
        n = dsp.n_of(d)
        x = dsp.sine(f, d) * dsp.exp_env(n, 0.008, 0.0003) + 0.4 * dsp.bp(dsp.noise(d, 310 + i), 1500, 5000) * dsp.exp_env(n, 0.006, 0.0002)
        reg("impactos", f"im_tick_{i+1:02d}", dsp.stereo(x * 0.5))


def library(force=False):
    if LIB and not force:
        return LIB
    LIB.clear()
    for g in (gen_movement, gen_materials, gen_energy, gen_character, gen_brand, gen_impacts):
        g()
    # official/hand-made replacements
    for name in list(LIB):
        p = ASSETS / "sfx" / f"{name}.wav"
        if p.exists():
            x, sr = dsp.read_wav(p)
            LIB[name] = dsp.resample(x, sr)
    return LIB


def write_library():
    lib = library()
    for k, x in lib.items():
        y = dsp.normalize(x, 0.9) if np.max(np.abs(x)) > 1 else x
        dsp.write_wav(AUDIO / f"{k}.wav", y)
    cats = {}
    for k, c in CAT.items():
        cats.setdefault(c, []).append(k)
    print(f"[sfx] {len(lib)} effects:", {c: len(v) for c, v in cats.items()})
    return lib


if __name__ == "__main__":
    write_library()

"""Original soundtrack: 100 BPM, D major - marimba, melodic percussion, soft keys, round sub, kick, palmas,
shaker, very discreet synthetic harmonic layers. Entirely synthesised; no samples, no library tracks.

Arrangement follows the brief's anchors (seconds): percussion enters 7.20 -> growth 11.40 -> harmonic
resolution 14.67 -> dramatic pause 16.50 -> full chord + low hit 16.80 -> fanfare 18.07 -> final resonance 19.20.
"""
from __future__ import annotations

import math

import numpy as np

from .. import score
from ..config import A, BAR, BEAT, OUT, TOTAL
from . import dsp
from .dsp import SR, Track

AUDIO = OUT / "audio"
LEN = TOTAL + 1.2          # render a little past the end so tails ring out; the mix trims


# ------------------------------------------------------------------ instruments
def marimba(f, dur=0.8, vel=0.8, seed=0):
    tau1 = float(np.clip(1.15 * (261.6 / f) ** 0.55, 0.14, 1.5))
    n = dsp.n_of(max(dur, tau1 * 2.2) + 0.05)
    t = np.arange(n) / SR
    ratios = (1.0, 3.99, 9.9, 17.2)
    amps = (1.0, 0.34 * vel + 0.05, 0.10 * vel, 0.03)
    taus = (tau1, tau1 * 0.30, tau1 * 0.11, tau1 * 0.05)
    y = sum(a * np.exp(-t / tu) * np.sin(2 * math.pi * f * r * t + 0.3 * k) for k, (r, a, tu) in enumerate(zip(ratios, amps, taus)))
    # felt-mallet "tok"
    nz = dsp.bp(dsp.noise(0.02, seed), 1200, 4500) * np.exp(-np.arange(dsp.n_of(0.02)) / SR / 0.004)
    y[: len(nz)] += nz * 0.10 * vel
    y *= dsp.exp_env(n, 5.0, attack=0.0008)
    return y * (0.55 * vel)


def bell(f, dur=1.2, vel=0.8):
    """Glock-ish bright bell used for sparkle and the fanfare."""
    n = dsp.n_of(dur)
    t = np.arange(n) / SR
    y = (np.sin(2 * math.pi * f * t) * np.exp(-t / 0.55) + 0.45 * np.sin(2 * math.pi * f * 2.76 * t) * np.exp(-t / 0.22)
         + 0.25 * np.sin(2 * math.pi * f * 5.4 * t) * np.exp(-t / 0.09))
    return y * 0.38 * vel * dsp.exp_env(n, 5.0, attack=0.001)


def key_pad(notes_hz, dur, level=0.5, bright=1500):
    n = dsp.n_of(dur)
    y = np.zeros(n)
    for i, f in enumerate(notes_hz):
        s = 0.55 * np.sin(2 * math.pi * f * np.arange(n) / SR)
        s += 0.22 * dsp.lp(dsp.saw(f, dur, 0.0015)[:n], bright, 2) + 0.22 * dsp.lp(dsp.saw(f, dur, -0.0015)[:n], bright, 2)
        y += s
    e = dsp.adsr(n, a=min(0.35, dur * 0.3), d=0.2, s=0.8, r=min(0.9, dur * 0.4))
    return y * e * level / max(len(notes_hz), 1) ** 0.5


def sub(f, dur, level=0.8):
    n = dsp.n_of(dur)
    t = np.arange(n) / SR
    # fundamental + strong 2nd/3rd harmonics: the note still reads on phone speakers that cannot reproduce the fundamental
    y = np.sin(2 * math.pi * f * t) * 0.8 + 0.55 * np.sin(2 * math.pi * 2 * f * t) + 0.28 * np.sin(2 * math.pi * 3 * f * t)
    return y * dsp.adsr(n, a=0.012, d=0.08, s=0.85, r=min(0.25, dur * 0.4)) * level


def kick(level=1.0, deep=False):
    d = 0.42 if deep else 0.28
    n = dsp.n_of(d)
    body = dsp.sweep(160 if not deep else 120, 46 if not deep else 36, d) * dsp.exp_env(n, 0.10 if not deep else 0.18, 0.0005)
    click = dsp.hp(dsp.noise(0.006, 3), 2500) * np.exp(-np.arange(dsp.n_of(0.006)) / SR / 0.0015)
    y = body.copy()
    y[: len(click)] += click * 0.3
    return dsp.soft_clip(y * 1.4, 1.2) * level


def clap(level=0.8, seed=0):
    out = np.zeros(dsp.n_of(0.28))
    for k, dt in enumerate((0.0, 0.011, 0.021)):
        b = dsp.bp(dsp.noise(0.09, seed + k), 900, 3600, 2) * np.exp(-np.arange(dsp.n_of(0.09)) / SR / 0.012)
        i = dsp.n_of(dt)
        out[i:i + len(b)] += b
    tail = dsp.bp(dsp.noise(0.25, seed + 9), 1100, 2800, 2) * np.exp(-np.arange(dsp.n_of(0.25)) / SR / 0.06)
    out[:len(tail)] += tail * 0.5
    return out * level * 0.5


def shaker(level=0.4, seed=0):
    n = dsp.n_of(0.07)
    return dsp.hp(dsp.noise(0.07, seed), 6500) * np.exp(-np.arange(n) / SR / 0.018) * dsp.exp_env(n, 1.0, 0.004) * level * 0.35


def ping(f, level=0.5):
    n = dsp.n_of(0.18)
    t = np.arange(n) / SR
    y = np.sin(2 * math.pi * f * t) * np.exp(-t / 0.05) + 0.3 * np.sin(2 * math.pi * f * 2.1 * t) * np.exp(-t / 0.025)
    return y * level * 0.5


def riser(dur, level=0.6, seed=2):
    """Reversed-cymbal style swell: filtered noise whose cutoff rises into the downbeat."""
    x = dsp.noise(dur, seed) * (np.arange(dsp.n_of(dur)) / dsp.n_of(dur)) ** 2.2
    x = dsp.tilt_sweep_filter(x, 500, 9000, kind="high", steps=20)
    return x * level


def hz(m):
    return score.hz(m)


# ------------------------------------------------------------------ arrangement
def render():
    tr = {k: Track(LEN) for k in ("marimba", "keys", "sub", "drums", "perc", "layers", "fx", "bells")}
    rng = np.random.default_rng(17)
    root_pc = {"D": 2, "A": 9, "Bm": 11, "G": 7, "Em": 4}
    pause0, pause1 = A["music_pause"], A["landing"]

    # --- marimba line (from score) --------------------------------------------------------
    for i, (t, m, dur, vel) in enumerate(score.marimba_line()):
        if t >= 18.9:
            continue
        tr["marimba"].add(marimba(hz(m), dur, vel, seed=i), t, 1.0, p=(-0.35 if i % 2 else 0.35))

    # --- chord pads (soft keys): follow the chord table, bloom as the film grows -----------
    segs = [(t0, name) for t0, name in score.CHORDS]
    for k in range(len(segs) - 1):
        t0, name = segs[k]
        t1 = segs[k + 1][0]
        if t0 >= 19.2 or (t0 >= pause0 and t0 < A["landing"]):
            continue
        t1 = min(t1, pause0 if t0 < pause0 else t1)
        if t1 - t0 < 0.3:
            continue
        pcs = score.CHORD_TONES[name]
        notes = [hz(score.midi(pc, 3 if i == 0 else 4)) for i, pc in enumerate(pcs)]
        lvl = 0.22 if t0 < 7.2 else 0.32 if t0 < 11.4 else 0.42
        tr["keys"].add(dsp.reverb(key_pad(notes, t1 - t0 + 0.4, lvl), 0.18, 1.1), t0 - 0.02, 1.0)

    # --- sub bass: roots, sparse -> syncopated -> driving ---------------------------------
    t = 0.0
    while t < 16.45:
        ch = score.chord_at(t + 0.001)
        r = hz(score.midi(root_pc[ch], 1 if root_pc[ch] < 5 else 1))
        r = r if r > 30 else r * 2
        bar_t = t % BAR
        if t < 7.2:
            hits = [(0.0, BEAT * 1.6)] + ([(2 * BEAT, BEAT * 1.4)] if t > 4.7 else [])
        elif t < 11.4:
            hits = [(0.0, BEAT * 0.9), (1.5 * BEAT, BEAT * 0.5), (2 * BEAT, BEAT * 0.9), (3.5 * BEAT, BEAT * 0.4)]
        elif t < 14.67:
            hits = [(0.0, BEAT * 0.8), (BEAT * 0.75, BEAT * 0.3), (1.5 * BEAT, BEAT * 0.5), (2 * BEAT, BEAT * 0.8), (2.75 * BEAT, BEAT * 0.3), (3.5 * BEAT, BEAT * 0.4)]
        else:
            hits = [(0.0, BEAT * 3.0)]
        for dt, d in hits:
            tt0 = t + dt
            if tt0 < 16.45 and tt0 >= 0.3:
                tr["sub"].add(sub(r, d + 0.05, 0.50), tt0, 1.0)
        t += BAR
    tr["sub"].add(sub(hz(38), 1.78, 0.55), 14.67, 1.0)      # resolution: D under the new chord
    # --- drums: from 7:20 -----------------------------------------------------------------
    for b in range(int(round(7.2 / BEAT)), int(round(A["music_pause"] / BEAT))):
        tb = b * BEAT
        if tb >= pause0:
            break
        beat_in_bar = b % 4
        late = tb >= 11.4
        res = tb >= 14.67
        if res:
            if beat_in_bar == 0:
                tr["drums"].add(kick(0.8), tb, 1.0)
            continue
        if beat_in_bar in (0, 2) or (late and beat_in_bar in (1, 3) and False):
            tr["drums"].add(kick(0.95 if beat_in_bar == 0 else 0.8), tb, 1.0)
        if late and beat_in_bar in (1, 3):
            tr["drums"].add(kick(0.35), tb, 1.0)
        if beat_in_bar in (1, 3):
            tr["drums"].add(dsp.reverb(clap(0.85, seed=b), 0.12, 0.35), tb + 0.003, 1.0, p=0.1)
        # shaker 16ths with accents; denser/louder after the growth point
        for s in range(4):
            ts = tb + s * BEAT / 4
            lv = (0.55 if s % 2 == 0 else 0.3) * (1.0 if late else 0.6)
            tr["drums"].add(shaker(lv, seed=b * 8 + s), ts, 1.0, p=(-0.3 if s % 2 else 0.3))
    # --- melodic percussion: off-beat pings in the pentatonic, from 7:20, busier after 11:40 ---
    pents = [hz(score.midi(pc, 6)) for pc in score.PENTA]
    for b in range(int(round(7.2 / BEAT)), int(round(14.4 / BEAT))):
        tb = b * BEAT
        late = tb >= 11.4
        for s in ((2,) if not late else (1, 2, 3)):
            ts = tb + s * BEAT / 4
            if rng.random() < (0.55 if not late else 0.7):
                tr["perc"].add(ping(pents[int(rng.integers(0, 5))], 0.30), ts, 1.0, p=float(rng.uniform(-0.5, 0.5)))
    # --- discreet synthetic harmonic layers: open up at 11:40, resolve at 14:67 ---------------
    for (a, b, lvl) in ((11.4, 14.67, 0.22), (14.67, 16.45, 0.26)):
        ch = score.chord_at(a + 0.01)
        notes = [hz(score.midi(pc, 4)) for pc in score.CHORD_TONES[ch]] + [hz(score.midi(score.CHORD_TONES[ch][0], 5))]
        pad = key_pad(notes, b - a + 0.6, lvl, bright=3200)
        pad = dsp.tilt_sweep_filter(pad, 700, 4200, kind="low", steps=16) if len(pad) else pad
        tr["layers"].add(dsp.reverb(pad, 0.25, 1.4), a, 1.0)
    # resolution at 14:67 - warm full D chord swell + rising bell figure
    for i, m in enumerate((74, 78, 81, 86)):
        tr["bells"].add(dsp.reverb(bell(hz(m), 1.4, 0.55), 0.3, 1.5), 14.67 + 0.0 + i * 0.075, 1.0, p=-0.3 + 0.2 * i)

    # --- the pause (16:50) and the reversed build into 16:80 ------------------------------------
    rv = riser(pause1 - pause0 + 0.02, 0.5)
    tr["fx"].add(rv, pause0, 1.0)
    rev_chord = np.zeros(dsp.n_of(0.8))
    for m in (62, 66, 69, 74):
        rev_chord[: dsp.n_of(0.8)] += marimba(hz(m), 0.7, 0.8)[: dsp.n_of(0.8)]
    rev_chord = dsp.reverb(rev_chord, 0.5, 1.6)[::-1]
    tr["fx"].add(rev_chord[-dsp.n_of(pause1 - pause0 + 0.1):] * 0.6, pause0 - 0.05, 1.0)
    # 16:80 - complete chord and a low hit
    tL = pause1
    boom = dsp.sweep(95, 34, 1.1) * dsp.exp_env(dsp.n_of(1.1), 0.45, 0.0008)
    tr["sub"].add(dsp.hp(boom, 38) * 1.6, tL, 1.0)
    tr["drums"].add(kick(1.0, deep=True), tL, 1.0)
    for m in (50, 62, 66, 69, 74, 78):
        tr["marimba"].add(marimba(hz(m), 1.6, 0.95), tL, 0.9, p=((m % 12) - 6) / 14)
    tr["keys"].add(dsp.reverb(key_pad([hz(m) for m in (50, 57, 62, 66, 69)], 1.8, 0.5), 0.25, 1.6), tL, 1.0)
    # --- 18:07 fanfare (an original lesson-complete flourish) -------------------------------------
    tF = A["fanfare"]
    arp = [74, 78, 81, 86, 90, 93]
    for i, m in enumerate(arp):
        tr["bells"].add(dsp.reverb(bell(hz(m), 1.6, 0.9), 0.28, 1.6), tF + i * 0.065, 1.0, p=-0.4 + 0.16 * i)
        tr["marimba"].add(marimba(hz(m - 12), 0.6, 0.9), tF + i * 0.065, 0.9, p=0.0)
    tr["keys"].add(dsp.reverb(key_pad([hz(m) for m in (62, 66, 69, 74)], 1.6, 0.5, 2600), 0.25, 1.4), tF, 1.0)
    tr["drums"].add(kick(0.85), tF, 1.0)
    tr["drums"].add(dsp.reverb(clap(0.9, seed=3), 0.2, 0.5), tF + 0.002, 1.0)
    tr["bells"].add(dsp.reverb(bell(hz(98), 1.2, 0.5), 0.3, 1.6), tF + 0.42, 1.0, p=0.3)
    # --- 19:20 final resonance: a quiet D major ring that decays through the end card -------------------
    tE = A["signature"]
    for m, p in ((38, 0.0), (50, -0.1), (57, 0.15), (62, -0.2), (66, 0.2), (69, 0.0)):
        tr["marimba"].add(marimba(hz(m), 2.6, 0.55), tE, 0.8, p=p)
    tr["keys"].add(dsp.reverb(key_pad([hz(m) for m in (50, 57, 62, 66, 69)], 2.8, 0.30, 1800), 0.3, 2.2), tE, 1.0)
    tr["sub"].add(sub(hz(26), 2.2, 0.5), tE, 1.0)
    tr["bells"].add(dsp.reverb(bell(hz(86), 2.0, 0.35), 0.4, 2.2), tE + 0.04, 1.0, p=0.1)

    levels = dict(marimba=0.95, keys=0.8, sub=0.32, drums=0.72, perc=0.7, layers=0.6, fx=0.8, bells=0.8)
    # instrumentation grows progressively without saturating the spectrum: per-stem section gain curves
    tg = np.arange(tr["marimba"].n) / SR

    def curve(pts):
        xs, ys = zip(*pts)
        return np.interp(tg, xs, ys)[:, None]

    gains = dict(
        marimba=curve([(0, 0.30), (2.4, 0.42), (4.8, 0.55), (7.2, 0.72), (11.4, 0.95), (14.67, 1.0), (16.8, 1.0), (19.2, 0.8), (21.2, 0.7)]),
        keys=curve([(0, 0.35), (4.8, 0.55), (7.2, 0.7), (11.4, 1.0), (16.8, 1.0)]),
        sub=curve([(0, 0.0), (2.3, 0.0), (2.4, 0.45), (7.2, 0.8), (11.4, 1.0)]),
        drums=curve([(0, 1.0), (21.2, 1.0)]), perc=curve([(0, 1.0), (21.2, 1.0)]), layers=curve([(0, 1.0), (21.2, 1.0)]),
        fx=curve([(0, 1.0), (21.2, 1.0)]), bells=curve([(0, 1.0), (21.2, 1.0)]),
    )
    for k in tr:
        tr[k].buf = tr[k].buf * gains[k]
    mix = sum(tr[k].buf * levels[k] for k in tr)
    # glue: tiny bus saturation
    mix = dsp.soft_clip(mix * 1.05, 1.1)
    AUDIO.mkdir(parents=True, exist_ok=True)
    for k in tr:
        dsp.write_wav(AUDIO / f"stem_music_{k}.wav", tr[k].buf * levels[k])
    dsp.write_wav(AUDIO / "music.wav", mix)
    return mix


if __name__ == "__main__":
    m = render()
    print("music rendered", m.shape, "peak", float(np.max(np.abs(m))))

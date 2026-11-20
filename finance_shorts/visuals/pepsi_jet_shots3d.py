"""v3: shots rendered as true 3-D camera moves (Blender) with 2-D cut-out characters placed in the 3-D world.
Shots without a 3-D version fall back to the v2 shot functions."""
from __future__ import annotations

import math

import numpy as np
import skia

from finance_shorts.engine.comp import H, W, Shot, shot_frames
from finance_shorts.engine.gfx import calculator, cheque, speed_lines
from finance_shorts.visuals import pepsi_jet_shots as v2
from finance_shorts.visuals.pepsi_jet_shots import (EXEC, JOHN, WARM, actor, dust_swirl, flying_papers, head_pos, sweat)


def char3d(fx, ch, who, anchor, height_m, **kw):
    """Place a 2-D character at a 3-D anchor; size from perspective (height in metres)."""
    x, y, ppm = fx.anchor(anchor)
    r = height_m / 4.7 * ppm
    actor(fx, ch, who, x, y, r, **kw)
    return x, y, r


def frame_of(t, start, sid):
    return min(shot_frames(sid) - 1, int((t - start) * 30))


# ----------------------------------------------------------------------------------------------- 3-D shots
def s01(fx, t, u):  # HOOK: dolly toward John + giant cheque, Harrier hovering behind him (real 3-D)
    fx.shot3d("H01_hook", frame_of(t, 0.0, "H01_hook"))
    fx.rays(W * 0.5, H * 0.33, 90, 160, 2200, "#FFC27A", 0.18, 11, seed=1)
    dust_swirl(fx, t, W * 0.5, H * 0.9, 60, 700)
    x, y, r = char3d(fx, JOHN, "JOHN", "JOHN", 1.75, tint=(1.08, 0.94, 0.82), pose="hold2", expr="grin",
                     look=(0, 0.3), mouth=0.0)
    w = 4.6 * r
    cheque(fx, skia.Rect.MakeXYWH(x - w / 2, y - 1.55 * r - w * 0.24, w, w * 0.48), t,
           rot=-3 + 2 * math.sin(t * 2), write=1.0)
    flying_papers(fx, t, 6, (0, H * 0.45, W, H * 0.75), seed=9, size=28, wind=(320, -70))


def s12(fx, t, u):  # kitchen orbit: John behind the table hammering the calculator
    fx.shot3d("K12_calc", frame_of(t, 19.95, "K12_calc"), shake=3 if t > 20.4 else 0)
    x, y, r = char3d(fx, JOHN, "JOHN", "JOHN", 1.7, tint=WARM, pose="hold2", expr="squint", look=(0, 0.6))
    fx.occlude3d()
    cx, cy, ppm = fx.anchor("CALC")
    keys_ = ["7", "×", "0", ".", "1", "="]
    k = keys_[int((t - 19.95) / 0.27) % len(keys_)]
    calculator(fx, cx, cy - 0.12 * ppm, 0.3 * ppm, ["7000000", "7000000×", "0.1", "0.1", "0.1", "700000."][keys_.index(k)],
               t, press=k)
    hx, hy = head_pos(x, y, r)
    sweat(fx, hx + r * 0.95, hy - r * 0.4 + (t * 120) % 50, r * 0.16)


def s27(fx, t, u):  # office crane: exec spit-take then laughing behind his giant desk
    fx.shot3d("O27_exec", frame_of(t, 46.1, "O27_exec"), shake=6 if t > 46.4 else 0)
    spit = 46.1 <= t < 46.5
    pose = "hold" if t < 46.4 else ("kick" if int(t * 6) % 2 else "hips")
    x, y, r = char3d(fx, EXEC, "EXEC", "EXEC", 1.8, tint=WARM, pose=pose, expr="laugh" if t > 46.4 else "wide",
                     look=(0, 0), prop={"kind": "mug", "hand": "r"} if t < 46.4 else None)
    hx, hy = head_pos(x, y, r)
    c = fx.c
    if spit:
        rng = np.random.default_rng(int(t * 30))
        k = (t - 46.1) / 0.4
        for i in range(70):
            a = rng.uniform(-0.5, 0.5)
            d = rng.uniform(0.8, 5.0) * r * k
            c.drawCircle(hx + math.cos(a) * d, hy + 0.5 * r + math.sin(a) * d * 0.6 + d * d * 0.0006,
                         rng.uniform(0.03, 0.1) * r, skia.Paint(AntiAlias=True, Color=skia.Color(107, 58, 30, 220)))
    fx.occlude3d()
    if t > 46.5:
        flying_papers(fx, t - 46.5, 10, (W * 0.1, H * 0.25, W * 0.9, H * 0.6), seed=8, size=50, wind=(200, -180))


THREE_D = {"S01": s01, "S12": s12, "S27": s27}

SHOTS = []
for sh in v2.SHOTS:
    fn = THREE_D.get(sh.name, sh.draw)
    SHOTS.append(Shot(sh.name, sh.start, sh.end, fn, cap_y=sh.cap_y, dust=sh.dust, vignette=sh.vignette, warm=sh.warm,
                      bloom=sh.bloom, whip=0))  # the reference channels use 100% hard cuts

"""ESCENA 09 - EL CIERRE PERFECTO  (16:50 - 19:20)

The music withdraws. The last luminous fragments of the message drift away slowly and, for a fraction of a
second, the frame is clear. A reversed sound grows; Duo drops in from above while the camera anticipates
with an extremely subtle move. 16:80: Duo hits the imaginary floor exactly on the low musical impact - body
compresses, wings keep moving by inertia, a small energy ring spreads from the contact point, the camera
answers softly. The green line crosses the scene and the wordmark springs up, perfectly centred, on 17:33
(the voice says «Duolingo»); 18:07 lesson-complete fanfare - Duo's glad little wing flutter. The camera
steadies and the final composition stays clean and legible.
"""
from __future__ import annotations

import math

import numpy as np
from mathutils import Matrix

from .. import anim, duo as duolib, fx, geo, mat, thread
from ..config import A, FPS, lin
from ..easing import (Polyline, damped_osc, in_cubic, in_out_cubic, noise1d, out_cubic, settle, smoothstep, smootherstep,
                      spring_follow, u)
from ..logo import build_logo_local
from . import s01_impact

T_LAND = A["landing"]
T_FAN = A["fanfare"]
T_VOICE = A["voice_duolingo"]


def build(ctx):
    P = ctx.portrait
    F8 = ctx.state["F8"]
    letters = ctx.state["text_letters"]
    c = ctx.coll("s09", window=(14.8, 20.1))
    root = F8.empty("F9", c)
    fr = np.arange(int(14.8 * FPS), int(21.3 * FPS))
    t = fr / FPS
    if not P:
        floor_y, logo_w, logo_y, dscale, dz = -2.45, 6.2, 0.75, 1.4, 1.2
    else:
        floor_y, logo_w, logo_y, dscale, dz = -3.7, 5.6, 2.3, 1.7, 0.8
    lights = []

    # ------------------------------------------------------------------ imaginary floor (glossy, fades radially)
    fm = mat.floor("s9_floor", "#0A1319", 0.12, 18.0, fade0=0.22, coat=0.5)
    fl = geo.slab("s9_floor", c, 38, 38, 0.02, R=19, rb=0.005, mat=fm, loc=(0, floor_y - 0.011, -3.0), parent=root, seg_arc=32)
    fl.rotation_euler = (-math.pi / 2, 0, 0)

    # ------------------------------------------------------------------ the message breaks into slow, last fragments
    T_BREAK = 16.50
    shard_m = mat.emissive("txt_shard", "#E9FFD0", 4.0)
    ii = 0
    for gi, ln in enumerate(letters):
        for o, xx in zip(ln["letters"], ln["xs"]):
            ts_ = T_BREAK + 0.011 * ii
            ii += 1
            fs_ = np.arange(int(ts_ * FPS) - 1, int((ts_ + 0.45) * FPS))
            sink = out_cubic(u(fs_ / FPS, ts_, ts_ + 0.30))
            on = (sink < 0.999).astype(float)
            anim.key_vec(o, "scale", fs_, np.stack([on, 1 - sink, on], 1))      # letters sink back into the baseline
            o["sink_t"] = ts_
            fx.burst(ctx, c, f"frag{ii}", ts_ + 0.04, tuple(F8.p(xx, ln["y"] + ln["size"] * 0.35, 0.05)), n=2, spd=(0.3, 1.5),
                     size=(0.012, 0.03), life=(0.9, 1.5), axis=tuple(F8.d(0, 1, 0.4)), cone=1.0, mat_=shard_m, drag=1.6, seed=100 + ii,
                     ring=(0.0, 0.25), stretch=1.4, gravity=tuple(F8.d(0, 0.35, 0)))
    ctx.ev("text_break", T_BREAK)
    # the baselines are consumed too (they retract along the line, none pops away)
    for b in ctx.state.get("bars", []):
        sx0 = out_cubic(u(t, 16.60, 16.92))
        keep = np.stack([np.maximum(1 - sx0, 1e-4), np.ones_like(t), np.ones_like(t)], 1)
        fs_ = np.arange(int(16.58 * FPS), int(17.0 * FPS))
        anim.key_vec(b["pv"], "scale", fs_, keep[fs_ - fr[0]])
    # the baselines are consumed with them: handled by scaling their pivots (they live in s08's collection)

    # ------------------------------------------------------------------ Duo drops in and lands on 16:80
    D = duolib.Duo(ctx, "D9", c, scale=dscale, unique_catch=True)
    ctx.objs["duo9"] = D
    holder = duolib.mount(D, root, loc=(0, floor_y, dz))
    Fd = np.arange(int(16.45 * FPS), int(19.4 * FPS))
    td = Fd / FPS
    t_a = 16.53
    uu = np.clip((td - t_a) / (T_LAND - t_a), 0, 1)
    height = 10.0 * (1 - uu ** 2) * (td < T_LAND)
    tau = td - T_LAND
    comp = np.where(tau < 0, 0.0, np.where(tau < 0.045, out_cubic(tau / 0.045) * 0.40, 0.0))
    ring = np.where(tau >= 0.045, damped_osc(tau - 0.045, 0.40, 3.3, 0.24), 0.0)
    comp = np.where(tau < 0.045, comp, ring)
    sz = 1 - comp + 0.10 * (td < T_LAND) * uu
    # fanfare hop
    ft = td - T_FAN
    hop = np.where((ft >= 0) & (ft < 0.40), np.sin(math.pi * np.clip(ft / 0.40, 0, 1)) * 0.38 * dscale, 0.0)
    stf = 1 + 0.11 * np.sin(math.pi * np.clip(ft / 0.2, 0, 1)) * (ft >= 0) * (ft < 0.2) - 0.09 * damped_osc(ft - 0.40, 1.0, 4.2, 0.3) * (ft >= 0.4)
    sz = sz * stf
    sxy = 1 / np.sqrt(np.clip(sz, 0.3, 2))
    idle = duolib.idle(td, seed=9, rest=0.0, blinks=[17.02, 17.9, 18.55], energy=0.7)
    squash = np.stack([sxy, sxy, sz], 1) * idle["squash"]
    # wings: raised in the fall, then they keep moving by inertia after impact; flutter on the fanfare
    flap_t = np.where(td < T_LAND, 0.95, 0.10)
    fold_t = np.where(td < T_LAND, 0.25, 0.0)
    flapL = spring_follow(flap_t, FPS, 2.7, 0.30)
    flapR = spring_follow(flap_t, FPS, 2.4, 0.33)
    foldL = spring_follow(fold_t, FPS, 3.0, 0.3)
    foldR = spring_follow(fold_t, FPS, 2.6, 0.3)
    flut = ((ft >= 0) & (ft < 0.7)) * np.sin(2 * math.pi * 3.8 * np.clip(ft, 0, 0.7)) ** 2 * np.exp(-2.2 * np.clip(ft, 0, 1))
    wl = np.stack([flapL + 1.0 * flut, foldL], 1) + idle["wing_l"] * np.array([[0.5, 0.5]])
    wr = np.stack([flapR + 1.0 * np.roll(flut, 3), foldR], 1) + idle["wing_r"] * np.array([[0.5, 0.5]])
    happy = smoothstep(u(td, T_FAN + 0.02, T_FAN + 0.08)) * (1 - smoothstep(u(td, T_FAN + 0.6, T_FAN + 0.9)))
    lid = idle["lid"] - 0.08 * (td < T_LAND) + happy * 0.45
    tuft = spring_follow(np.where(td < T_LAND, 0.5, 0.0), FPS, 3.2, 0.22)
    lean = idle["lean"] + np.stack([damped_osc(tau, 0.06, 3.2, 0.25) * (tau >= 0), 0 * td, 0 * td], 1)
    D.key(Fd, pos=np.stack([0 * td, 0 * td, height + hop], 1), squash=squash, lean=lean, wing_l=wl, wing_r=wr, lid_l=lid, lid_r=lid,
          gaze_l=idle["gaze"] * 0.2, gaze_r=idle["gaze"] * 0.2, tuft=tuft)
    ctx.ev("landing", T_LAND)
    ctx.ev("fanfare", T_FAN)
    # impact ring on the floor + reflections come alive
    n_eul = (Matrix(F8.R.tolist()) @ Matrix.Rotation(-math.pi / 2, 3, "X")).to_euler("XYZ")
    fx.shockwave(ctx, c, "land_ring", T_LAND, tuple(F8.p(0, floor_y + 0.01, dz)), n_eul, r0=0.4, r1=6.5, dur=0.55, tube=0.012, color="#B8FF7A", strength=3.5)
    fx.shockwave(ctx, c, "land_ring2", T_LAND, tuple(F8.p(0, floor_y + 0.01, dz)), n_eul, r0=0.3, r1=4.0, dur=0.40, tube=0.010, color="#58CC02", strength=2.0, delay=0.04)
    kit = s01_impact.duo_kit(ctx, D, c, power=0.30 * dscale ** 2 * 1.15)
    lights += list(kit)

    # ------------------------------------------------------------------ the line crosses the scene; the wordmark springs up, centred
    m_logo = mat.principled("logo9", "feather", 0.32, coat=0.55, coat_rough=0.1, sheen=0.3, emit="feather", emit_strength=0.14)
    lg = build_logo_local(c, root, logo_w, m_logo, loc=(0, logo_y, 0.0))
    ctx.state["logo9"] = lg
    ts0, ts1 = 17.04, 17.30
    wl_ = lg["width"]
    x0, x1 = -wl_ / 2 - 3.5, wl_ / 2 + 3.5
    ypath = logo_y + 0.12
    pts = np.array([F8.p(x0 + (x1 - x0) * k, ypath + 0.10 * math.sin(k * math.pi * 2.0) * 0.4, 0.15) for k in np.linspace(0, 1, 60)])
    seg = thread.Segment(ctx, "th9", c, pts, ts0, ts1 + 0.04, ease=smootherstep, radius=0.020 if not P else 0.015, halo=2.8, tail=2.8, fade=(ts1 + 0.04, ts1 + 0.30))
    fh = np.arange(int(ts0 * FPS) - 1, int((ts1 + 0.34) * FPS))
    th = fh / FPS
    hd = thread.Head(ctx, "h9", c, radius=0.08 if not P else 0.06)
    vis = 1 - smoothstep(u(th, ts1 + 0.03, ts1 + 0.08))
    hd.key(fh, seg.head_pos(th), size=vis, power=300 * vis, color=lin("mask"), bead_strength=14)
    for i, (o, xx) in enumerate(zip(lg["letters"], lg["xs"])):
        fx_ = (xx - x0) / (x1 - x0)
        tcross = ts0 + (ts1 + 0.04 - ts0) * float(np.clip(fx_, 0, 1))
        fs = np.arange(int(tcross * FPS) - 1, int((tcross + 0.5) * FPS))
        ts_ = fs / FPS - tcross
        k = 1 - np.exp(-ts_.clip(0) * 14) * np.cos(ts_.clip(0) * 38)
        sc_ = np.where(ts_ < 0, 0.0, np.clip(k, 0, 1.2))
        anim.key_vec(o, "scale", fs, np.stack([sc_, sc_, sc_], 1))
        anim.key_vec(o, "scale", np.array([0, fs[0] - 1]), np.zeros((2, 3)))
        ctx.ev("logo_letter", tcross, i=i)
    ctx.ev("logo_sweep", ts0)
    ctx.ev("voice_duolingo", T_VOICE)

    # ------------------------------------------------------------------ lights (all dim out for the end card)
    kp = F8.p(-3.5, 4.2, 9.5 if not P else 5.0)
    k1 = geo.area_light("s9_key", c, (0.85, 0.95, 1.0), 1100 if not P else 420, size=5.5, loc=tuple(kp), rot=geo.look_rot(kp, F8.p(0, -0.4, 0)))
    rp = F8.p(4.5, 2.5, -4.0)
    k2 = geo.area_light("s9_rim", c, lin("mask"), 800 if not P else 360, size=4.0, loc=tuple(rp), rot=geo.look_rot(rp, F8.p(0, -0.4, 0)))
    bp = F8.p(0.0, floor_y + 0.4, 6.0)
    k3 = geo.area_light("s9_bounce", c, (0.5, 0.95, 0.6), 160, size=5.0, loc=tuple(bp), rot=geo.look_rot(bp, F8.p(0, 0, 0)))
    lights += [k1, k2, k3]
    dim = 1 - smoothstep(u(t, 19.25, 19.95))
    # the key/rim wake up as the message dissolves (S08's own lights end with it)
    wake = smoothstep(u(t, 16.30, 16.60))
    for L in lights:
        base = L.data.energy
        anim.key(L.data, "energy", fr, base * wake * dim)
        L.visible_glossy = False          # no mirror image of the studio lights on the floor
    anim.key(D.catch_mat.node_tree, mat.e_strength() if False else 'nodes["E"].inputs["Strength"].default_value', fr, 5.0 * dim)
    anim.key(m_logo.node_tree, mat.path_emit_strength(m_logo), fr, 0.14 * dim)
    ctx.state["rig_dim"] = (19.25, 19.95)

    # ------------------------------------------------------------------ camera: subtle anticipation, a soft answer to the hit, then steady
    D0 = 14.3 if not P else 6.4
    lens = 35.0 if not P else 24.0
    ty = -0.9 if not P else -1.0
    ctx.cam(16.62, F8.p(0.0, 0.62, D0 + 0.12), F8.p(0, ty + 0.03, 0.0), lens=lens, fstop=5.0, focus=None, tension=0.0)
    ctx.cam(16.92, F8.p(0.0, 0.40, D0 - 0.05), F8.p(0, ty - 0.04, 0.0), lens=lens, fstop=5.0, focus=None, tension=0.3)
    ctx.cam(17.80, F8.p(0.0, 0.50, D0 - 0.45), F8.p(0, ty - 0.02, 0.0), lens=lens, fstop=5.0, focus=None, tension=0.2)
    ctx.cam(19.20, F8.p(0.0, 0.55, D0 - 0.90), F8.p(0, ty, 0.0), lens=lens, fstop=5.0, focus=None, tension=0.1)
    ctx.shake(T_LAND, tuple(F8.d(0.0, -0.10, 0.06)), freq=6.0, decay=8.0, dur=0.6)
    return dict()

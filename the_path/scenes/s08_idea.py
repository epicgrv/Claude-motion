"""ESCENA 08 - LA GRAN IDEA  (14:67 - 16:50)

The four paths run back into the hub, the energy gathers into one trajectory and the camera follows the
union of the lines. The line becomes a luminous typographic baseline and the message appears:
UN SOLO CAMINO. - a breath - TODAS LAS HABILIDADES. The type is extraordinarily clean (flat, white, no 3-D
tricks). The baseline briefly splits into the four skill colours and re-unites while the camera slows
almost to a stop: the world seems to hold its breath.
"""
from __future__ import annotations

import math

import numpy as np

from .. import anim, geo, mat, thread, typo, ui
from ..config import A, FPS, lin
from ..easing import (Polyline, catmull_rom, damped_osc, out_cubic, settle, smoothstep, smootherstep, u)
from ..world import Frame

T_SWEEP1 = 15.03
T_SWEEP2 = 15.86
T_SPLIT = 16.02


def build(ctx):
    P = ctx.portrait
    H = ctx.state["hub"]
    c = ctx.coll("s08", window=(14.4, 17.3))
    O8 = H + np.array([-3.0, -9.0, 3.0])
    F8 = Frame(O8, facing=(0, 1, 0), up_hint=(0, 0, 1))
    ctx.state["F8"] = F8
    root = F8.empty("F8", c)
    fr = np.arange(int(14.5 * FPS), int(16.75 * FPS))
    t = fr / FPS

    if not P:
        lines = [[("UN SOLO CAMINO.", 1.02, 0.0)], [("TODAS LAS HABILIDADES.", 0.64, -1.95)]]
        Wb = 10.0
        D, lens = 14.3, 35.0
    else:
        lines = [[("UN SOLO", 1.25, 1.55), ("CAMINO.", 1.25, 0.0)], [("TODAS LAS", 0.90, -2.10), ("HABILIDADES.", 0.80, -3.30)]]
        Wb = 6.6
        D, lens = 6.4, 24.0
    ink = mat.principled("big_text", "snow", 0.55, emit="snow", emit_strength=0.55, spec=0.2)
    # --------------------------------------------------------------- the thread: hub -> baseline start (the single trajectory)
    base_y = -0.30 if not P else -0.30
    start = F8.p(-Wb / 2, base_y, 0.0)
    mid = H + (start - H) * 0.5 + np.array([0, 0, 1.8])
    pth = catmull_rom(np.array([H, H + (mid - H) * 0.5 + np.array([0, 0, 0.6]), mid, start - (start - mid) * 0.1, start]), 220)
    seg = thread.Segment(ctx, "th8", c, pth, 14.76, 15.02, ease=thread.profile([(14.76, 0.0), (14.86, 0.30), (14.95, 0.72), (15.02, 1.0)]),
                         radius=0.028, halo=2.8, tail=None, fade=(15.22, 15.52))
    ctx.state["th8"] = seg
    # --------------------------------------------------------------- typography, baseline slabs, bead
    h8 = thread.Head(ctx, "h8", c, radius=0.09)
    fh = np.arange(int(14.76 * FPS), int(16.1 * FPS))
    th = fh / FPS
    pos_h = np.zeros((len(fh), 3))
    vis_h = np.zeros(len(fh))
    path_pos = seg.head_pos(th)
    all_letters = []
    heads = []          # (t0, t1, p0, p1) sweeps of the bead
    sweeps = [(T_SWEEP1, T_SWEEP1 + 0.16, lines[0]), (T_SWEEP2, T_SWEEP2 + 0.16, lines[1])]
    bars = []
    colors = ["#58CC02", "#1CB0F6", "#CE82FF", "#FFC800"]
    for gi, (ts0, ts1, grp) in enumerate(sweeps):
        # a thin baseline under the group's last line; reveals as the bead sweeps left->right
        by = grp[-1][2] - 0.30 * grp[-1][1]
        nseg = 4 if gi == 0 else 1
        for si in range(nseg):
            w = Wb / nseg
            xl = -Wb / 2 + si * w
            pv = geo.empty(f"bar{gi}{si}_pv", c, loc=(xl, by, 0.0), parent=root)
            bm = mat.emissive(f"bar{gi}{si}_m", colors[0], 5.0)
            slab = geo.slab(f"bar{gi}{si}", c, w - 0.04, 0.075 if not P else 0.07, 0.07, R=0.035, rb=0.015, mat=bm, loc=((w - 0.04) / 2, 0, 0), parent=pv)
            tsa = ts0 + (ts1 - ts0) * si / nseg
            tsb = ts0 + (ts1 - ts0) * (si + 1) / nseg
            grow = smoothstep(u(t, tsa, tsb))
            gap = 0.0
            bars.append(dict(pv=pv, mat=bm, si=si, gi=gi, xl=xl, w=w))
            sx = np.maximum(grow, 0.0001)
            if gi == 0:
                # the split: 4 skill colours drift apart (and a touch in z), then re-unify
                tsp0, tsp1 = T_SPLIT, T_SPLIT + 0.40
                k = np.sin(math.pi * np.clip(u(t, tsp0, tsp1), 0, 1)) ** 2
                off = (si - 1.5) * 0.28 * k
                col = np.array(lin(colors[si]))
                g = np.array(lin(colors[0]))
                cc = g[None] + (col - g)[None] * k[:, None]
                anim.key_vec(bm.node_tree, mat.e_color(), fr, np.concatenate([cc, np.ones((len(fr), 1))], 1))
                anim.key_vec(pv, "location", fr, np.stack([xl + off, by + 0 * t, 0 * t], 1))
                anim.key_vec(pv, "scale", fr, np.stack([sx, np.ones_like(t), np.ones_like(t)], 1))
                ctx.ev("split", tsp0, dur=0.4)
            else:
                anim.key_vec(pv, "scale", fr, np.stack([sx, np.ones_like(t), np.ones_like(t)], 1))
        # letters of every line in the group sprout as the bead passes their x
        for (body, sz, ly) in grp:
            ln = typo.text_line(c, f"t{gi}{len(all_letters)}", body, sz, ink, root, y=ly, z=0.0)
            all_letters.append(ln)
            xmin, xmax = -Wb / 2, Wb / 2
            for o, xx in zip(ln["letters"], ln["xs"]):
                ts_ = ts0 + (ts1 - ts0) * float((xx - xmin) / (xmax - xmin)) + 0.02
                rise = out_cubic(u(t, ts_, ts_ + 0.16))
                on = (rise > 1e-3).astype(float)          # exactly zero before the sprout: no sliver left behind
                anim.key_vec(o, "scale", fr, np.stack([on, rise, on], 1))
                ctx.ev("letter8", ts_)
        heads.append((ts0, ts1, F8.p(-Wb / 2, by, 0.1), F8.p(Wb / 2, by, 0.1)))
    ctx.state["text_letters"] = all_letters
    ctx.state["bars"] = bars
    ctx.state["text_root"] = root
    ctx.ev("msg1", T_SWEEP1)
    ctx.ev("msg2", T_SWEEP2)
    # bead: along the trajectory, then along each baseline
    for k in range(len(fh)):
        tk = th[k]
        if tk <= 15.02:
            pos_h[k] = path_pos[k]
            vis_h[k] = smoothstep(u(tk, 14.76, 14.80))
            continue
        placed = False
        for (a, b, p0, p1) in heads:
            if a <= tk <= b + 0.03:
                f = float(np.clip((tk - a) / (b - a), 0, 1))
                pos_h[k] = p0 + (p1 - p0) * f
                vis_h[k] = 1 - smoothstep(u(tk, b, b + 0.03))
                placed = True
        if not placed:
            pos_h[k] = path_pos[k] if tk < T_SWEEP1 else heads[-1][3]
            vis_h[k] = 0.0
    h8.key(fh, pos_h, size=vis_h, power=260 * vis_h, color=lin("mask"), bead_strength=14)

    # --------------------------------------------------------------- the world holds its breath: faint key on the type
    kp = F8.p(-2.0, 3.0, 9.0 if not P else 5.0)
    geo.area_light("s08_key", c, (0.9, 0.97, 1.0), 900 if not P else 300, size=6.0, loc=tuple(kp), rot=geo.look_rot(kp, F8.p(0, -0.8, 0)))
    gp = F8.p(0, -1.2, 4.0)
    ga = geo.area_light("s08_glow", c, lin("mask"), 0.0, size=8.0, loc=tuple(gp), rot=geo.look_rot(gp, F8.p(0, -0.8, 0)))
    anim.key(ga.data, "energy", fr, 420 * smoothstep(u(t, T_SWEEP1, T_SWEEP1 + 0.2)) * (1 - 0.4 * smoothstep(u(t, 16.2, 16.5))))

    # --------------------------------------------------------------- camera: follow the union, then almost stop
    HH = H
    ctx.cam(14.80, HH + np.array([-3.1, 12.5, 10.5]), HH + np.array([-1.2, 0.0, 0.5]), lens=30 if not P else 22, fstop=4.0, focus=None)
    ctx.cam(14.98, HH + np.array([-3.0, 9.5, 6.2]), F8.p(0, base_y + 0.4, 0.0) * 0.55 + H * 0.45, lens=32 if not P else 22, fstop=4.0, focus=None)
    cam_c = F8.p(0.0, -0.6 + (0.0 if not P else -0.5), D)
    ctx.cam(15.35, F8.p(0.0, 1.2, D * 1.12), F8.p(0, -0.7, 0.0), lens=lens, fstop=4.5, focus=None, tension=0.5)
    ctx.cam(15.90, F8.p(0.0, 0.7, D * 1.04), F8.p(0, -0.9 if not P else -1.0, 0.0), lens=lens, fstop=5.0, focus=None, tension=0.2)
    ctx.cam(16.50, F8.p(0.0, 0.55, D * 1.0), F8.p(0, -0.9 if not P else -1.0, 0.0), lens=lens, fstop=5.0, focus=None, tension=0.0)
    return dict()

"""ESCENA 06 - EL MOMENTO HUMANO  (9:33 - 11:40)

The energy becomes the outline of a video-call window which materialises in space. Duo pops up
inside, looks straight at the user and speaks (beak synced to the voice). The green line leaves the
right edge of the window and becomes a three-dimensional audio wave whose bars follow the real
low/mid/high energy of the user's line «¡Muy bien! Pedí un café en español». Duo smiles and does a
small happy hop while the camera begins to pull away, the wave still alive.
"""
from __future__ import annotations

import math

import numpy as np

from .. import anim, duo as duolib, fx, geo, lipsync, mat, thread, ui
from ..config import A, FPS, lin
from ..easing import (Polyline, catmull_rom, damped_osc, in_cubic, in_out_cubic, noise1d, out_cubic, settle, smoothstep,
                      smootherstep, u)
from ..world import Frame
from . import s01_impact

T_HI = 9.60
T_USER = 10.40


def rounded_rect_path(w, h, R, n_arc=10, start="right"):
    """Closed rounded-rectangle perimeter (CCW) starting at the middle of the right edge."""
    R = min(R, w / 2 - 1e-3, h / 2 - 1e-3)
    cx, cy = w / 2 - R, h / 2 - R
    pts = [(w / 2, 0.0)]
    for (ox, oy), a0 in (((cx, cy), 0.0), ((-cx, cy), math.pi / 2), ((-cx, -cy), math.pi), ((cx, -cy), 3 * math.pi / 2)):
        for k in range(n_arc + 1):
            a = a0 + (math.pi / 2) * k / n_arc
            pts.append((ox + R * math.cos(a), oy + R * math.sin(a)))
    pts.append((w / 2, 0.0))
    return np.array(pts)


def build(ctx):
    P = ctx.portrait
    F5 = ctx.state["F5"]
    F6 = Frame(F5.p(0, -17.0, 0.0), facing=(0, -1, 0))
    ctx.state["F6"] = F6
    c = ctx.coll("s06", window=(9.1, 11.7))
    root = F6.empty("F6", c)
    ww, wh = (4.7, 6.0) if P else (6.6, 4.2)
    dscale = 2.0 if P else 1.7
    fr = np.arange(int(9.2 * FPS), int(11.6 * FPS))
    t = fr / FPS

    # ------------------------------------------------------------ window (materialises as the outline closes)
    win = geo.empty("win", c, parent=root)
    bez = geo.bezel("win_bezel", c, ww, wh, 0.5, 0.20, 0.45, rb=0.05, mat=ui.M("alu"), parent=win)
    back = geo.slab("win_back", c, ww - 0.3, wh - 0.3, 0.10, R=0.38, rb=0.02, mat=mat.principled("win_back_m", "#0E3640", 0.65, emit="#1C7E8E", emit_strength=0.10, rvar=0.04),
                    loc=(0, 0, -0.65), parent=win)
    # soft studio floor/ledge Duo stands on
    ledge = geo.slab("win_ledge", c, ww - 0.5, 1.5, 0.08, R=0.3, rb=0.02, mat=ui.M("card2"), loc=(0, -wh / 2 + 0.55 - 0.06, -0.3), parent=win)
    ledge.rotation_euler = (-math.pi / 2, 0, 0)
    chip = ui.card(ctx, c, "chip", 0.95, 0.34, d=0.06, R=0.12, material="card", parent=win, loc=(-ww / 2 + 0.85, -wh / 2 + 0.45, 0.02))
    ui.text(c, "chip_t", "Duo", 0.19, ui.M("text"), loc=(0, 0, 0.04), parent=chip)
    # call controls under the window
    ctrl = geo.empty("ctrl", c, parent=root)
    for i, (nm, col) in enumerate((("mic", "#3A4A54"), ("end", "cardinal"), ("cam", "#3A4A54"))):
        m = mat.principled(f"call_{nm}", col, 0.38, coat=0.3, rvar=0.03)
        geo.slab(f"call_{nm}", c, 0.62, 0.62, 0.16, R=0.31, rb=0.035, mat=m, loc=((i - 1) * 0.95, -wh / 2 - 0.65, 0.0), parent=ctrl)
    # materialise: scale/settle once the outline is complete
    t_mat = 9.58
    s = settle(t, t_mat, 0.20, overshoot=0.12, freq=3.2)
    s = np.clip(s, 0.001, 1.3)
    for o, off in ((win, 0.0), (ctrl, 0.1)):
        k = np.clip(settle(t, t_mat + off, 0.20, overshoot=0.12, freq=3.2), 0.001, 1.3)
        anim.key_vec(o, "scale", fr, np.stack([k, k, k], 1))
    ctx.ev("window_on", t_mat)

    # ------------------------------------------------------------ outline thread: wave_end -> top -> around -> right edge -> out
    loop = rounded_rect_path(ww - 0.2, wh - 0.2, 0.42)
    loop3 = np.array([F6.p(x, y, 0.28) for x, y in loop])
    start = np.asarray(ctx.state["wave_end"], float)
    lead = catmull_rom(np.array([start, F6.p(0.0, wh / 2 + 3.5, 0.8), F6.p(ww / 2 - 0.1, wh / 2 + 0.3, 0.4), loop3[0] + np.array([0, 0, 0.0])]), 60)
    # leave through the right edge: out and toward the viewer, the baseline of the wave
    # path = lead-in, loop, and the baseline
    path = np.vstack([lead[:-1], loop3])
    seg = thread.Segment(ctx, "th6", c, path, 9.24, 9.62, ease=thread.profile([(9.24, 0.0), (9.34, 0.18), (9.44, 0.42), (9.62, 1.0)]),
                         radius=0.024, halo=2.6, tail=None, fade=(10.34, 10.50))
    ctx.state["th6"] = seg
    frh = np.arange(int(9.24 * FPS), int(10.55 * FPS))
    th = frh / FPS
    hp = seg.head_pos(th)
    head = thread.Head(ctx, "h6", c, radius=0.06)
    vis = 1 - smoothstep(u(th, 9.60, 9.66))
    head.key(frh, hp, size=vis, power=190 * vis, color=lin("mask"), bead_strength=14)

    # ------------------------------------------------------------ Duo inside the window
    D = duolib.Duo(ctx, "D6", c, scale=dscale)
    ctx.objs["duo6"] = D
    holder = duolib.mount(D, root, loc=(0, -wh / 2 + 0.55 - 0.02, -0.15))
    Fd = np.arange(int(9.5 * FPS), int(11.6 * FPS))
    td = Fd / FPS
    idle = duolib.idle(td, seed=6, rest=0.1, blinks=[10.05, 10.95], energy=1.0)
    # pops up from below the window edge with a springy arrival
    t_pop = 9.66
    rise = settle(td, t_pop, 0.20, overshoot=0.14, freq=3.4)
    z_off = -(wh / 2 + 1.0) * (1 - rise)           # in Duo space z is up
    # speech
    dur_hi = lipsync.duration("duo_hi", 0.80)
    dur_us = lipsync.duration("user_line", 0.90)
    jaw = 0.42 * lipsync.envelope("duo_hi", td, T_HI, dur_hi, 7, seed=7)
    ctx.ev("duo_hi", T_HI, dur=dur_hi)
    ctx.ev("user_line", T_USER, dur=dur_us)
    # looks straight at the user; leans in while the user talks; smiles + hops after the user line
    t_happy = T_USER + dur_us + 0.05
    ht = td - t_happy
    hop = np.where((ht >= 0) & (ht < 0.36), np.sin(math.pi * np.clip(ht / 0.36, 0, 1)) * 0.28, 0.0)
    land = damped_osc(ht - 0.36, 0.10, 4.5, 0.3) * (ht >= 0.36)
    stre = 1 + 0.12 * np.sin(math.pi * np.clip(ht / 0.18, 0, 1)) * (ht >= 0) * (ht < 0.18)
    squash = idle["squash"] * np.stack([1 / np.sqrt(stre), 1 / np.sqrt(stre), stre], 1) * np.stack([1 + land, 1 + land, 1 - land], 1)
    smile = smoothstep(u(td, t_happy, t_happy + 0.06)) * (1 - smoothstep(u(td, t_happy + 0.6, t_happy + 0.9)))
    lid = idle["lid"] + smile * 0.5
    nod = 0.07 * np.sin(2 * math.pi * 2.2 * (td - T_USER)) * ((td > T_USER) & (td < T_USER + dur_us))
    lean = idle["lean"] + np.stack([-0.05 * smoothstep(u(td, T_USER, T_USER + 0.1)) * (1 - smoothstep(u(td, t_happy, t_happy + 0.1)))
                                    + nod, 0 * td, 0 * td], 1)
    flap = ((ht >= 0) & (ht < 0.5)) * np.sin(2 * math.pi * 3.6 * np.clip(ht, 0, 0.5)) ** 2 * np.exp(-3 * np.clip(ht, 0, 1))
    wl = idle["wing_l"] + np.stack([1.0 * flap, 0 * flap], 1)
    wr = idle["wing_r"] + np.stack([1.0 * np.roll(flap, 2), 0 * flap], 1)
    gz = idle["gaze"] * 0.3
    D.key(Fd, pos=np.stack([0 * td, 0 * td, z_off + hop], 1), squash=squash, lean=lean, wing_l=wl, wing_r=wr, lid_l=lid, lid_r=lid,
          gaze_l=gz, gaze_r=gz, jaw=jaw + 0.15 * np.exp(-(td - t_happy).clip(0) * 8) * (td >= t_happy))
    s01_impact.duo_kit(ctx, D, c, power=0.30 * dscale ** 2 * 0.5)
    ctx.ev("duo_happy", t_happy)

    # ------------------------------------------------------------ the 3-D audio wave
    nb = 40
    bm = mat.emissive("wave_bar", "#9CFF52", 3.2)
    bm2 = mat.principled("wave_bar_b", "feather", 0.35, coat=0.3, emit="feather", emit_strength=0.6)
    fw = np.arange(int(10.25 * FPS), int(11.6 * FPS))
    tw = fw / FPS
    bands = lipsync.bands("user_line", tw, T_USER, dur_us, 11, seed=11)
    # wave baseline in F6 coordinates
    pts = []
    for k in range(nb):
        f = k / (nb - 1)
        if not P:
            x = ww / 2 + 0.35 + f * 6.2
            y = -0.5 - 0.55 * math.sin(f * 2.4) - 0.5 * f
            z = 0.3 + f * 3.4
        else:
            x = (f - 0.5) * 4.2
            y = -wh / 2 - 1.5 - 0.15 * math.sin(f * 3.0)
            z = 0.4 + 0.9 * math.sin(f * math.pi)
        pts.append(F6.p(x, y, z))
    ctx.state["wave_pts"] = [np.array(p) for p in pts]
    bars = []
    t_emit = 10.30
    for k in range(nb):
        o = geo.slab(f"bar{k}", c, 0.13, 1.0, 0.13, R=0.065, rb=0.03, mat=bm, loc=tuple(pts[k]), seg_arc=6, seg_bev=3)
        o.rotation_euler = F6.euler()
        bars.append(o)
        lag = k * 0.011
        band = bands[k % 3] * (0.55 + 0.45 * np.sin(k * 1.9 + 0.7) ** 2)
        e = np.interp(tw - lag, tw, bands[(k + 1) % 3]) * 0.4 + band * 0.9
        t_k = t_emit + 0.20 * k / (nb - 1)
        grow = smoothstep(u(tw, t_k, t_k + 0.07))
        h = (0.09 + 1.35 * np.clip(e, 0, 1)) * grow + 0.02
        h = 0.02 + (h - 0.02) * (1 - smoothstep(u(tw, 11.30 + 0.004 * k, 11.50 + 0.004 * k)))
        anim.key_vec(o, "scale", fw, np.stack([np.ones_like(tw), h, np.ones_like(tw)], 1))
        anim.key_vec(o, "location", fw, pts[k][None] + (F6.y[None] * (h / 2)[:, None]))
    ctx.ev("wave", t_emit, dur=1.1)
    # the line's bead runs out along the baseline; every bar springs up as it passes
    wb = Polyline(np.array(pts))
    hb = thread.Head(ctx, "h6b", c, radius=0.07)
    tb = np.arange(int(10.26 * FPS), int(10.52 * FPS)) / FPS
    fb = (np.clip((tb - t_emit) / 0.20, 0, 1))
    visb = smoothstep(u(tb, 10.26, 10.30)) * (1 - smoothstep(u(tb, 10.48, 10.52)))
    hb.key(np.round(tb * FPS).astype(int), wb.frac(fb) + F6.y[None] * 0.12, size=visb, power=160 * visb, color=lin("mask"), bead_strength=14)

    # ------------------------------------------------------------ lights
    kp = F6.p(-4.0, 3.0, 8.0)
    geo.area_light("s06_key", c, (0.85, 0.94, 1.0), 900, size=4.5, loc=tuple(kp), rot=geo.look_rot(kp, F6.p(0, 0, 0)))
    rp = F6.p(3.8, 2.5, -2.0)
    geo.area_light("s06_rim", c, lin("mask"), 520, size=3.0, loc=tuple(rp), rot=geo.look_rot(rp, F6.p(0, 0, 0)))

    # ------------------------------------------------------------ camera: a calm approach, then a slow pull away
    if not P:
        ks = [(9.50, (0.7, 1.4, 10.8), (0.0, 0.0, 0.0), 32), (9.80, (0.5, 0.55, 9.6), (0.0, -0.1, 0.0), 34),
              (10.30, (0.8, 0.15, 8.4), (0.5, -0.2, 0.0), 34), (10.90, (2.2, -0.15, 8.8), (2.2, -0.55, 0.0), 32),
              (11.40, (3.4, 0.4, 11.6), (3.0, -0.6, 0.0), 30)]
    else:
        ks = [(9.50, (0.5, 1.8, 8.8), (0.0, 0.0, 0.0), 32), (9.80, (0.3, 0.7, 8.0), (0.0, -0.3, 0.0), 32),
              (10.30, (0.3, -0.2, 7.2), (0.0, -1.2, 0.0), 32), (10.90, (0.2, -0.9, 7.4), (0.0, -2.0, 0.0), 32),
              (11.40, (0.3, -1.2, 9.4), (0.0, -2.2, 0.0), 30)]
    for tk, p, tg, lens in ks:
        ctx.cam(tk, F6.p(*p), F6.p(*tg), lens=lens, fstop=3.2, focus=None)
    return dict()

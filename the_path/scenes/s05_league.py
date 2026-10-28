"""ESCENA 05 - EL ASCENSO  (7:20 - 9:33)

The camera falls and finds an enormous floating leaderboard: LIGA DIAMANTE. The user starts at #7; the
thread touches their card and it lights up, lifts off the board and climbs - every place gained
physically shoves the overtaken card down one slot. At 8:70 the card reaches #1, the correct-answer
sound plays, a green wave runs down the board, decelerates under control and the camera follows it on
to the next station.

The rank numbers are fixed slots engraved in the board; the cards slide over them, so every change of
position is clear and legible.
"""
from __future__ import annotations

import math

import numpy as np

from .. import anim, duo as duolib, fx, geo, mat, thread, ui
from ..config import A, FONT_BLACK, FONT_BOLD, FPS, lin
from ..easing import (Polyline, catmull_rom, damped_osc, in_cubic, out_cubic, noise1d, settle, smoothstep, smootherstep, u)
from ..world import Frame

NAMES = ["Valentina", "Mateo", "Sofía", "Lucas", "Camila", "Diego", "Tú", "Emma", "Noah", "Mía"]
XP = ["2480", "2210", "1960", "1745", "1530", "1310", "2650", "1180", "1040", "910"]
AV = ["macaw", "beetle", "fox", "bee", "cardinal", "humpback", "feather", "#FF86D0", "#7CE0FF", "#B4FF6B"]
ROW_H = 1.0
Y_RANK1 = 4.5


def y_of(rank):
    return Y_RANK1 - (rank - 1) * ROW_H


def build(ctx):
    P = ctx.portrait
    F5 = ctx.state["F5"]
    c = ctx.coll("s05", window=(7.0, 9.6))
    root = F5.empty("F5", c)
    t = np.arange(int(7.0 * FPS), int(9.6 * FPS)) / FPS
    fr = np.arange(int(7.0 * FPS), int(9.6 * FPS))

    # ------------------------------------------------------------ board
    bd = geo.slab("board", c, 6.5, 13.4, 0.30, R=0.5, rb=0.05, mat=mat.principled("board_m", "#0E171C", 0.55, coat=0.15, rvar=0.04), loc=(0, 0.4, -0.45), parent=root)
    geo.bezel("board_frame", c, 6.5, 13.4, 0.5, 0.14, 0.34, rb=0.04, mat=ui.M("edge"), loc=(0, 0.4, -0.40), parent=root)
    gem_m = mat.principled("gem_m", "#1CB0F6", 0.08, coat=1.0, coat_rough=0.02, spec=1.0, emit="#1CB0F6", emit_strength=0.35)
    gm = geo.gem("gem", c, gem_m, loc=(-2.9, 6.05, 0.15), parent=root)
    gm.scale = (0.55, 0.55, 0.55)
    gm.rotation_euler = (math.radians(90), 0, 0)
    anim.key_vec(gm, "rotation_euler", fr, np.stack([np.full_like(t, math.radians(90)), 0 * t, 0.9 * (t - 7.0)], 1))
    ui.text(c, "league", "LIGA DIAMANTE", 0.62, mat.principled("league_t", "#6FD1FF", 0.4, emit="#1CB0F6", emit_strength=0.55), loc=(0.3, 5.85, 0.10), parent=root, extrude=0.04)
    medal = {1: "bee", 2: "#C9D3DA", 3: "#D98A4A"}
    for r in range(1, 11):
        col = medal.get(r, "#6C8190")
        ui.text(c, f"slot{r}", str(r), 0.46, mat.principled(f"slot{r}_m", col, 0.4, emit=col, emit_strength=0.18), loc=(-2.62, y_of(r) - 0.01, -0.22), parent=root, extrude=0.02)
        geo.slab(f"slotbed{r}", c, 5.7, 0.86, 0.04, R=0.2, rb=0.01, mat=ui.M("trough"), loc=(0.1, y_of(r), -0.26), parent=root)

    # ------------------------------------------------------------ rows
    rows = []
    for i in range(10):
        rank = i + 1
        user = NAMES[i] == "Tú"
        rt = geo.empty(f"row{i}", c, loc=(0, y_of(rank), 0.0), parent=root)
        cm = mat.principled(f"row{i}_card", "#1B2B34" if not user else "#1F3B16", 0.5, coat=0.12, rvar=0.04, emit="feather", emit_strength=0.0)
        card = geo.slab(f"row{i}_c", c, 5.2, 0.80, 0.16, R=0.22, rb=0.025, mat=cm, parent=rt)
        if user:
            frame = geo.slab(f"row{i}_frame", c, 5.34, 0.94, 0.12, R=0.28, rb=0.02, mat=mat.principled("user_frame", "feather", 0.35, coat=0.3, emit="feather", emit_strength=0.8), loc=(0, 0, -0.03), parent=rt)
        av = ui.avatar(ctx, c, f"row{i}_av", AV[i], r=0.27, parent=rt, loc=(-1.95, 0, 0.12), initial=NAMES[i][0])
        ui.text(c, f"row{i}_n", NAMES[i], 0.30, ui.M("text"), loc=(-1.45, -0.02, 0.095), parent=rt, align="LEFT", font=FONT_BLACK)
        ui.text(c, f"row{i}_x", XP[i] + " XP", 0.24, ui.M("text_dim"), loc=(2.35, -0.02, 0.095), parent=rt, align="RIGHT", font=FONT_BOLD)
        rows.append(dict(root=rt, card=card, mat=cm, user=user, rank=rank))
    uidx = 6
    U_row = rows[uidx]
    ulight = geo.point_light("user_light", c, lin("feather"), 0.0, radius=0.2, loc=(0, 0, 0.9), parent=U_row["root"])

    # ------------------------------------------------------------ user trajectory
    t_card, t_up0 = 7.78, 7.88
    keys = [(7.0, y_of(7)), (t_up0, y_of(7)), (7.94, y_of(7) - 0.14), (8.06, 0.1), (8.28, 2.15), (8.48, 3.75), (8.60, 4.32), (A["rank1"], y_of(1)), (9.6, y_of(1))]
    from scipy.interpolate import PchipInterpolator
    kt = np.array([k[0] for k in keys])
    ky = np.array([k[1] for k in keys])
    yu = PchipInterpolator(kt, ky)(t)
    # passes: when the card centre crosses an overtaken row's centre (minus a little)
    pass_t = {}
    for rk in range(6, 0, -1):
        yr = y_of(rk)
        k = int(np.argmax(yu >= yr - 0.28))
        pass_t[rk] = float(t[k])
        ctx.ev("rank_pass", pass_t[rk], to=rk)
    lift = settle(t, t_card + 0.0, 0.16, overshoot=0.10, freq=3.2) * 0.42 * (t < A["rank1"] + 0.03) + \
        (settle(t, A["rank1"], 0.16, overshoot=0.15, freq=3.2) - 1.0) * 0.0
    z_u = 0.0 + 0.42 * settle(t, t_card, 0.16, overshoot=0.10, freq=3.2) * (1 - smoothstep(u(t, A["rank1"], A["rank1"] + 0.12))) + \
        0.14 * smoothstep(u(t, A["rank1"], A["rank1"] + 0.12))
    z_u += 0.07 * damped_osc(t - A["rank1"], 1.0, 4.5, 0.25) * (t >= A["rank1"])
    sc_u = 1 + 0.05 * smoothstep(u(t, t_card, t_card + 0.1)) * (1 - smoothstep(u(t, A["rank1"], A["rank1"] + 0.2)))
    sc_u += 0.03 * damped_osc(t - A["rank1"], 1.0, 5.0, 0.25) * (t >= A["rank1"])
    rollu = np.radians(1.6) * np.sin(2 * math.pi * 1.8 * (t - t_up0)) * ((t > t_up0) & (t < A["rank1"])) * 1.0
    anim.key_vec(U_row["root"], "location", fr, np.stack([0 * t, yu, z_u], 1))
    anim.key_vec(U_row["root"], "scale", fr, np.stack([sc_u, sc_u, sc_u], 1))
    anim.key_vec(U_row["root"], "rotation_euler", fr, np.stack([0 * t, 0 * t, rollu], 1))
    glow = smoothstep(u(t, t_card, t_card + 0.05))
    anim.key(U_row["mat"].node_tree, mat.path_emit_strength(U_row["mat"]), fr, 0.35 * glow + 0.5 * np.exp(-(t - A["rank1"]).clip(0) * 6) * (t >= A["rank1"]))
    anim.key(ulight.data, "energy", fr, 55 * glow)
    ctx.ev("card_light", t_card)
    ctx.ev("card_lift", t_up0)

    # overtaken rows are shoved down one slot, with a little physical ring-down
    for rk in range(1, 7):
        r = rows[rk - 1]
        tp = pass_t[rk]
        shove = settle(t, tp, 0.10, overshoot=0.16, freq=4.5)
        y = y_of(rk) - ROW_H * shove
        tilt = np.radians(2.5) * damped_osc(t - tp, 1.0, 5.0, 0.3) * (t >= tp)
        anim.key_vec(r["root"], "location", fr, np.stack([0 * t, y, -0.04 * np.abs(damped_osc(t - tp, 1.0, 6.0, 0.3)) * (t >= tp)], 1))
        anim.key_vec(r["root"], "rotation_euler", fr, np.stack([tilt, 0 * t, 0 * t], 1))
    # untouched rows breathe very slightly (the whole board floats)
    for i in (7, 8, 9):
        anim.key_vec(rows[i]["root"], "location", fr, np.stack([0 * t, y_of(i + 1) + 0.006 * np.sin(2 * math.pi * 0.5 * t + i), 0 * t], 1))

    # ------------------------------------------------------------ wave at #1
    t1 = A["rank1"]
    ctx.ev("rank1", t1)
    wm = mat.emissive("wave_m", "#A8FF5A", 8.0)
    wave = geo.slab("wave", c, 6.1, 0.07, 0.10, R=0.03, rb=0.015, mat=wm, loc=(0, y_of(1) + 0.5, 0.35), parent=root)
    t_w1 = 9.22
    wy = y_of(1) + 0.5 - (y_of(1) + 0.5 + 7.6) * out_cubic(u(t, t1, t_w1))
    wsx = 1 - 0.97 * smoothstep(u(t, t_w1 - 0.18, t_w1))
    anim.key_vec(wave, "location", fr, np.stack([0 * t, wy, 0.35 + 0 * t], 1))
    anim.key_vec(wave, "scale", fr, np.stack([wsx, np.ones_like(t), np.ones_like(t)], 1))
    wl = geo.point_light("wave_light", c, lin("mask"), 0.0, radius=0.2, parent=root)
    anim.key_vec(wl, "location", fr, np.stack([0 * t, wy, 1.0 + 0 * t], 1))
    anim.key(wl.data, "energy", fr, 140 * smoothstep(u(t, t1 - 0.01, t1 + 0.03)))
    for i in range(10):
        # row y at the time the wave reaches it (final slot positions)
        slot_rank = {0: 2, 1: 3, 2: 4, 3: 5, 4: 6, 5: 7}.get(i, i + 1)
        if i == 6:
            slot_rank = 1
        ys = y_of(slot_rank)
        k = int(np.argmax(wy <= ys))
        tw = float(t[k]) if (wy <= ys).any() else 9.3
        base = anim.__dict__  # noqa
        em = 0.9 * np.exp(-(t - tw).clip(0) * 7.0) * (t >= tw)
        if i != 6:
            anim.key(rows[i]["mat"].node_tree, mat.path_emit_strength(rows[i]["mat"]), fr, em)
    # thread: touches the card at 7:78 (arrives from S04); the wave collapses into the next head
    wave_end = F5.p(0, -7.6, 0.4)
    ctx.state["wave_end"] = wave_end
    hd = thread.Head(ctx, "h5", c, radius=0.07)
    hp = np.stack([0 * t, wy, 0.35 + 0 * t], 1)
    wpos = np.array([F5.p(*p) for p in hp])
    vis = smoothstep(u(t, t_w1 - 0.12, t_w1))
    hd.key(fr, wpos, size=vis, power=90 * vis, color=lin("mask"), bead_strength=14)
    fx.burst(ctx, c, "rank_burst", t1, tuple(F5.p(0, y_of(1), 0.35)), n=30, spd=(2.5, 8.0), size=(0.012, 0.035), life=(0.3, 0.6), axis=tuple(F5.z),
             cone=0.7, color="#9CFF52", strength=8, seed=21, ring=(0.3, 2.4))
    fx.shockwave(ctx, c, "rank_ring", t1, tuple(F5.p(0, y_of(1), 0.3)), F5.euler(), r0=0.4, r1=4.2, dur=0.30, tube=0.014, strength=5)

    # ------------------------------------------------------------ lights
    kp = F5.p(-4.0, 3.0, 9.0)
    geo.area_light("s05_key", c, (0.82, 0.93, 1.0), 900, size=4.5, loc=tuple(kp), rot=geo.look_rot(kp, F5.p(0, 0.3, 0)))
    rp = F5.p(4.5, 4.0, -3.0)
    geo.area_light("s05_rim", c, (0.2, 0.7, 1.0), 700, size=3.0, loc=tuple(rp), rot=geo.look_rot(rp, F5.p(0, 0.3, 0)))
    gp = F5.p(0, 6.6, 3.0)
    geo.area_light("s05_gem", c, (0.5, 0.85, 1.0), 260, size=2.0, loc=tuple(gp), rot=geo.look_rot(gp, F5.p(-2.9, 6.05, 0.2)))

    # ------------------------------------------------------------ camera
    if not P:
        ks = [(7.50, (2.2, 1.0, 11.0), (0.0, -0.8, 0.0), 30), (7.80, (0.6, -0.8, 9.4), (0.0, -1.4, 0.0), 32),
              (8.05, (0.2, 0.2, 8.9), (0.0, 0.1, 0.0), 32), (8.30, (0.1, 2.0, 8.3), (0.0, 2.2, 0.0), 32),
              (8.55, (0.0, 3.8, 7.7), (0.0, 4.0, 0.0), 34), (A["rank1"], (0.0, 4.3, 7.4), (0.0, 4.4, 0.0), 34),
              (8.95, (0.0, -0.8, 8.2), (0.0, -1.4, 0.0), 32), (9.22, (0.0, -7.4, 8.6), (0.0, -8.0, 0.0), 32)]
    else:
        ks = [(7.50, (1.6, 0.6, 7.6), (0.0, -0.5, 0.0), 30), (7.80, (0.5, -0.5, 6.7), (0.0, -1.1, 0.0), 32),
              (8.05, (0.1, 0.0, 6.4), (0.0, 0.0, 0.0), 32), (8.30, (0.0, 1.0, 6.3), (0.0, 1.3, 0.0), 32),
              (8.55, (0.0, 2.2, 6.2), (0.0, 2.4, 0.0), 32), (A["rank1"], (0.0, 2.6, 6.1), (0.0, 2.7, 0.0), 32),
              (8.95, (0.0, -0.8, 6.6), (0.0, -1.2, 0.0), 32), (9.22, (0.0, -7.2, 7.0), (0.0, -8.0, 0.0), 32)]
    for tk, p, tg, lens in ks:
        ctx.cam(tk, F5.p(*p), F5.p(*tg), lens=lens, fstop=4.0, focus=None)
    return dict()

"""ESCENA 04 - 365 DIAS  (4:80 - 7:20)

The camera follows the energy as it leaves the screen. The line spirals and bends as if an invisible
force were sculpting it, then ignites at 5:00 into a three-dimensional flame (one anamorphic streak
crosses the frame, the ambient light slides to orange, nearby surfaces take an orange bounce).
The flame reveals a mechanical odometer - three drums with fixed-width cells click through
1 -> 7 -> 30 -> 100 -> 200 -> 365 - and a plate slides out: DÍAS. Below, the seven days of the week
light up one after another. A small orbit around the flame; the green energy leaves its core for the
next station.
"""
from __future__ import annotations

import math

import numpy as np

from .. import anim, fx, geo, mat, thread, ui
from ..config import A, FONT_BLACK, FPS, lin
from ..easing import (Polyline, catmull_rom, damped_osc, in_cubic, in_out_cubic, noise1d, norm, out_cubic, settle,
                      smoothstep, smootherstep, u)
from ..world import Frame

T_IGN = A["ignition"]


def flame_profile(H, Rb, n=48):
    z = np.concatenate([np.linspace(0, 0.25, n // 3, endpoint=False), np.linspace(0.25, 1.0, n - n // 3)])
    f = (z ** 0.45) * ((1 - z) ** 0.9)
    f = f / f.max()
    return [(float(Rb * fi), float(zi * H)) for fi, zi in zip(f, z)]


def flame_mat(name, color, strength):
    m = mat.emissive(name, color, strength)
    nt = m.node_tree
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.5
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value = 1.0
    mr.inputs["To Max"].default_value = 0.45
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.name = "M"
    mul.inputs[1].default_value = strength
    nt.links.new(lw.outputs["Facing"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], mul.inputs[0])
    nt.links.new(mul.outputs["Value"], nt.nodes["E"].inputs["Strength"])
    return m


def build(ctx):
    P = ctx.portrait
    U = ctx.state["U"]
    c = ctx.coll("s04", window=(4.6, 7.95))
    F4 = Frame(U.p(0.3, 0.5, -15.0), facing=(0, -1, 0))
    ctx.state["F4"] = F4
    F5 = Frame(F4.p(0, -14.0, 0.0), facing=(0, -1, 0))
    ctx.state["F5"] = F5
    kz = 0.55 if P else 1.0           # portrait: camera sits closer, scene reads bigger
    root = F4.empty("F4", c)

    # ---------------------------------------------------------------- spiral that sculpts itself into the flame
    W_s = np.asarray(ctx.state["th3_exit_world"], float)
    d0 = np.asarray(ctx.state["th3_exit_dir"], float)
    E = F4.p(0, -0.35, 0.0)
    line = E - W_s
    Ld = np.linalg.norm(line)
    ax = line / Ld
    e1 = norm(np.cross(ax, (0, 0, 1.0)))
    e2 = np.cross(ax, e1)
    s = np.linspace(0, 1, 260)
    rho = 1.15 * (1 - s) ** 0.9 * (0.35 + 0.65 * np.sin(math.pi * np.clip(s * 1.1, 0, 1))) + 0.02
    ang = 2 * math.pi * 1.7 * s ** 1.15
    # start tangent matches the incoming thread: blend the straight run into the helix
    blend = smoothstep(np.clip(s / 0.18, 0, 1))
    helix = (W_s[None] + (line[None] * s[:, None]) + (e1[None] * (rho * np.cos(ang))[:, None] + e2[None] * (rho * np.sin(ang))[:, None]) * blend[:, None])
    # a straight lead-in along the incoming direction so there is no kink at the hand-off
    lead = W_s[None] + d0[None] * np.linspace(0.0, 0.6, 12)[:, None]
    path = np.vstack([lead[:-1], helix])
    seg = thread.Segment(ctx, "th4", c, path, 4.80, T_IGN + 0.01, ease=thread.profile([(4.80, 0.0), (4.88, 0.18), (4.96, 0.62), (T_IGN + 0.01, 1.0)]),
                         radius=0.011, halo=2.8, tail=4.0, fade=(T_IGN - 0.01, T_IGN + 0.10))
    ctx.state["th4"] = seg
    fr = np.arange(int(4.80 * FPS), int((T_IGN + 0.12) * FPS))
    tt = fr / FPS
    hp = seg.head_pos(tt)
    h4 = thread.Head(ctx, "h4", c, radius=0.03)
    vis = 1 - smoothstep(u(tt, T_IGN, T_IGN + 0.05))
    h4.key(fr, hp, size=vis, power=70 * vis, color=lin("mask"), bead_strength=14)

    # ---------------------------------------------------------------- the flame (3 nested emissive layers + two tongues)
    Hf, Rb = 2.7, 0.88
    fl = geo.empty("flame", c, loc=tuple(F4.p(0, -1.05, 0.0)), parent=root)
    fl.location = (0, -1.05, 0)
    fl.parent = root
    layers = []
    spec = [("outer", "#FF8A00", 2.4, 1.0, 1.0, (0, 0, 0.0)), ("mid", "#FFC200", 3.4, 0.68, 0.64, (0.0, 0.08, 0.20)),
            ("core", "#FFF3BE", 5.0, 0.36, 0.34, (0.0, 0.13, 0.36)), ("tongueL", "#FF7A00", 2.2, 0.36, 0.45, (-0.66, 0.0, 0.06)),
            ("tongueR", "#FF9A00", 2.2, 0.32, 0.40, (0.64, 0.0, 0.10))]
    for nm, col, st, kr, kh, (ox, oz, dz) in spec:
        m = flame_mat(f"fl_{nm}", col, st)
        o = geo.revolve(f"fl_{nm}", c, flame_profile(Hf * kh, Rb * kr), mat=m, parent=fl, seg=48, lean=0.10 if nm == "outer" else 0.06)
        o.rotation_euler = (-math.pi / 2, 0, 0)
        o.location = (ox, oz * Hf, dz)
        layers.append((o, m, st))
    # ignition: scale up with a hard overshoot, flicker, sway
    f0, f1 = int((T_IGN - 0.02) * FPS), int(7.45 * FPS)
    ff = np.arange(f0, f1)
    t = ff / FPS
    grow = settle(t, T_IGN, 0.11, overshoot=0.20, freq=3.6)
    for k, (o, m, st) in enumerate(layers):
        n1 = noise1d(t * 7.5, 40 + k) * 0.045
        n2 = noise1d(t * 9.0, 60 + k) * 0.07
        sx = np.maximum(grow, 0.001) * (1 + n1)
        sz = np.maximum(grow, 0.001) * (1 + n2)
        anim.key_vec(o, "scale", ff, np.stack([sx, sx * 0.48, sz], 1))
        rot = np.stack([np.full_like(t, -math.pi / 2) + noise1d(t * 3.0, 80 + k) * 0.03, 0 * t, noise1d(t * 4.0, 90 + k) * 0.08 + 0 * t], 1)
        anim.key_vec(o, "rotation_euler", ff, rot)
        flash = 1 + 2.2 * np.exp(-(t - T_IGN).clip(0) * 14) * (t >= T_IGN)
        anim.key(m.node_tree, 'nodes["M"].inputs[1].default_value', ff, st * flash * (0.95 + 0.08 * noise1d(t * 11, 20 + k)))
    # flame lights: orange key that throws the bounce on the neighbours
    ctx.ev("ignition", T_IGN)
    fx.shockwave(ctx, c, "fl_ring", T_IGN, tuple(F4.p(0, 0.0, 0.2)), F4.euler(), r0=0.6, r1=7.5, dur=0.30, tube=0.02, color="#FFB347", strength=5)
    fx.burst(ctx, c, "fl_sparks", T_IGN, tuple(F4.p(0, -0.2, 0.3)), n=44, spd=(2.5, 11.0), size=(0.012, 0.04), life=(0.35, 0.8),
             axis=tuple(F4.z), cone=0.6, color="#FFB020", strength=9, seed=9, ring=(0.0, 0.7), gravity=tuple(F4.d(0, 2.2, 0)))
    fl_light = geo.point_light("fl_light", c, (1.0, 0.55, 0.12), 0.0, radius=0.4, loc=tuple(F4.p(0, 0.2, 1.3)))
    amb = geo.area_light("fl_amb", c, (1.0, 0.6, 0.2), 0.0, size=6.0, loc=tuple(F4.p(-3.5, 2.5, 6.0)), rot=geo.look_rot(F4.p(-3.5, 2.5, 6.0), F4.p(0, -1, 0)))
    bounce = geo.area_light("fl_bounce", c, (1.0, 0.5, 0.15), 0.0, size=4.0, loc=tuple(F4.p(0, -3.6, 3.0)), rot=geo.look_rot(F4.p(0, -3.6, 3.0), F4.p(0, -1.5, 0)))
    pw = (1 + 3.0 * np.exp(-(t - T_IGN).clip(0) * 12)) * smoothstep(u(t, T_IGN - 0.01, T_IGN + 0.04)) * (0.95 + 0.08 * noise1d(t * 13, 5))
    anim.key(fl_light.data, "energy", ff, 380 * pw)
    ramp = smoothstep(u(t, T_IGN, T_IGN + 0.35)) * (1 - 0.8 * smoothstep(u(t, 6.95, 7.2)))
    anim.key(amb.data, "energy", ff, 420 * ramp * (0.95 + 0.05 * noise1d(t * 9, 7)))
    anim.key(bounce.data, "energy", ff, 120 * ramp)

    # ---------------------------------------------------------------- odometer (3 mechanical drums + DÍAS plate)
    oy = -1.95
    og = geo.empty("odo", c, loc=(-0.45, oy, 0.0), parent=root)
    m_house = ui.M("panel")
    m_bar = mat.principled("odo_bar", "#1B262D", 0.35, metal=0.6, coat=0.2, rvar=0.04)
    m_drum = mat.principled("odo_drum", "#0F171C", 0.5, rvar=0.05)
    m_dig = mat.principled("odo_digit", "#FFE9B0", 0.45, emit="#FFB020", emit_strength=0.9)
    win_h = 0.64
    geo.slab("odo_back", c, 2.1, 2.1, 0.12, R=0.14, rb=0.02, mat=m_house, loc=(0, 0, -0.30), parent=og)
    geo.slab("odo_top", c, 2.1, 0.78, 0.30, R=0.12, rb=0.03, mat=m_bar, loc=(0, win_h / 2 + 0.39, 0.06), parent=og)
    geo.slab("odo_bot", c, 2.1, 0.78, 0.30, R=0.12, rb=0.03, mat=m_bar, loc=(0, -win_h / 2 - 0.39, 0.06), parent=og)
    for sx in (-1.02, 1.02):
        geo.slab(f"odo_side{sx}", c, 0.10, win_h + 0.1, 0.26, R=0.04, rb=0.02, mat=m_bar, loc=(sx, 0, 0.04), parent=og)
    for sx in (-0.31, 0.31):
        geo.slab(f"odo_sep{sx}", c, 0.045, win_h + 0.1, 0.22, R=0.02, rb=0.01, mat=m_bar, loc=(sx, 0, 0.03), parent=og)
    rD = 0.95
    drums = []
    for d, xx in enumerate((-0.62, 0.0, 0.62)):
        nf = 10 if d == 2 else 11               # hundreds, tens: 0-9 + blank; ones: 0-9
        dr = geo.empty(f"drum{d}", c, loc=(xx, 0, -rD + 0.05), parent=og)
        geo.cylinder(f"drum{d}_body", c, rD, 0.52, mat=m_drum, parent=dr, seg=72)
        for k in range(nf):
            ch = str(k) if k < 10 else ""
            phi = 2 * math.pi * k / nf
            if ch:
                tx = ui.text(c, f"d{d}_{k}", ch, 0.62, m_dig, loc=(0, rD * math.sin(phi) * 1.003, rD * math.cos(phi) * 1.003), parent=dr, extrude=0.01)
                tx.rotation_euler = (-phi, 0, 0)
        drums.append((dr, nf))
    # drum states: (time, cumulative index) for hundreds, tens, ones
    DT = [5.10, 5.38, 5.58, 5.78, 5.98, 6.20]
    seqs = [[10, 10, 10, 12, 13, 14],      # hundreds  B B B 1 2 3
            [10, 10, 14, 22, 22, 28],      # tens      B B 3 0 0 6
            [1, 7, 10, 10, 10, 15]]        # ones      1 7 0 0 0 5
    ff2 = np.arange(int(4.9 * FPS), int(7.45 * FPS))
    t2 = ff2 / FPS
    for (dr, nf), seq in zip(drums, seqs):
        a = np.full_like(t2, seq[0] * 2 * math.pi / nf)
        for i in range(1, len(seq)):
            if seq[i] != seq[i - 1]:
                dur = 0.12
                a = a + (seq[i] - seq[i - 1]) * 2 * math.pi / nf * settle(t2, DT[i] - dur, dur, overshoot=0.07, freq=4.5)
        anim.key_vec(dr, "rotation_euler", ff2, np.stack([a, 0 * t2, 0 * t2], 1))
    # housing 'clack' on every value change + reveal: the odometer slides up from behind the flame base
    rise = settle(t2, T_IGN + 0.05, 0.22, overshoot=0.05, freq=3.0)
    clack = np.zeros_like(t2)
    for T in DT[1:]:
        clack += 0.012 * damped_osc(t2 - T, 1.0, 9.0, 0.2) * (t2 >= T)
    anim.key_vec(og, "location", ff2, np.stack([-0.45 + 0 * t2, oy - 1.6 * (1 - rise) + clack, 0.0 * t2], 1))
    for i, T in enumerate(DT):
        ctx.ev("odo_tick", T, i=i, value=[1, 7, 30, 100, 200, 365][i])
    # DÍAS plate slides out of the housing
    plate = geo.slab("dias_plate", c, 1.12, 0.78, 0.2, R=0.14, rb=0.025, mat=m_bar, loc=(0.45, 0, -0.1), parent=og)
    dias = ui.text(c, "dias", "DÍAS", 0.40, ui.M("orange"), loc=(0, 0, 0.11), parent=plate, extrude=0.02)
    slide = settle(t2, 6.20, 0.16, overshoot=0.10, freq=3.5)
    anim.key_vec(plate, "location", ff2, np.stack([0.45 + 1.75 * slide, 0 * t2, -0.1 + 0 * t2], 1))
    ctx.ev("dias_plate", 6.20)

    # ---------------------------------------------------------------- the week lights up
    wy = -3.1
    days = ["L", "M", "M", "J", "V", "S", "D"]
    base_off = np.array(lin("#26343C"))
    on_col = np.array(lin("fox"))
    for i, dch in enumerate(days):
        x = (i - 3) * 0.62
        dm = mat.principled(f"day{i}_m", "#26343C", 0.45, coat=0.15, emit="#FF9600", emit_strength=0.0)
        dg = geo.slab(f"day{i}", c, 0.46, 0.46, 0.14, R=0.23, rb=0.03, mat=dm, loc=(x, wy, 0.0), parent=root)
        tx = ui.text(c, f"day{i}_t", dch, 0.22, ui.M("text_dim"), loc=(0, 0, 0.075), parent=dg, extrude=0.01)
        ti = 6.35 + 0.095 * i
        w = smoothstep(u(t2, ti, ti + 0.05))
        pulse = np.exp(-(t2 - ti).clip(0) * 8.0) * (t2 >= ti)
        anim.key_vec(dm.node_tree, mat.path_color(dm), ff2, np.concatenate([base_off[None] + (np.array(lin("fox")) - base_off)[None] * w[:, None], np.ones((len(ff2), 1))], 1))
        anim.key(dm.node_tree, mat.path_emit_strength(dm), ff2, 0.15 * w + 2.4 * pulse)
        bnc = damped_osc(t2 - ti, 0.12, 5.0, 0.3) * (t2 >= ti)
        anim.key_vec(dg, "location", ff2, np.stack([x + 0 * t2, wy + bnc * 1.0, 0.0 * t2 + 0.1 * pulse], 1))
        ctx.ev("day_on", ti, i=i)
        # entrance from below: the row rises with the odometer
    # the week row rises too (as if lifted by the same mechanism)
    # ---------------------------------------------------------------- energy leaves the flame's core towards the next station
    way = np.array([F4.p(0, 0.15, 0.05), F4.p(0.1, -0.1, 0.9), F4.p(1.1, -1.5, 1.4), F4.p(2.4, -4.5, 1.9), F5.p(4.2, 6.2, 1.7),
                    F5.p(3.9, 1.2, 1.3), F5.p(1.9, -1.0, 0.9), F5.p(0.0, -1.5, 0.45)])
    pe = catmull_rom(way, 420)
    T_leave, T_card = 6.95, 7.78
    seg_e = thread.Segment(ctx, "th4b", c, pe, T_leave, T_card, ease=thread.profile([(T_leave, 0.0), (7.10, 0.07), (7.20, 0.18), (7.45, 0.55), (7.65, 0.86), (T_card, 1.0)]),
                           radius=0.012, halo=2.8, tail=3.0, fade=(T_card - 0.02, T_card + 0.12))
    ctx.state["th4b"] = seg_e
    fe = np.arange(int(T_leave * FPS), int(T_card * FPS) + 1)
    te = fe / FPS
    h5 = thread.Head(ctx, "h4b", c, radius=0.035)
    visb = smoothstep(u(te, T_leave, T_leave + 0.04))
    h5.key(fe, seg_e.head_pos(te), size=visb, power=140 * visb, color=lin("mask"), bead_strength=14)
    ctx.state["card_hit_pos"] = pe[-1].copy()
    ctx.ev("energy_leaves", T_leave)

    ctx.tint(T_IGN, 7.0, (1.0, 0.55, 0.15), 70, attack=0.30, release=0.35)
    # ---------------------------------------------------------------- station lights
    kp = F4.p(-3.6, 3.2, 6.5)
    geo.area_light("s04_key", c, (0.8, 0.92, 1.0), 380, size=4.0, loc=tuple(kp), rot=geo.look_rot(kp, F4.p(0, -1.2, 0)))

    # ---------------------------------------------------------------- camera
    ks = [(4.92, (1.5, 0.9, 12.5), (0.2, 0.2, 0.0), 32, 1.0), (T_IGN, (0.7, 0.4, 10.2), (0.0, -0.2, 0.0), 32, 1.0),
          (5.35, (0.3, 0.1, 9.6), (0.0, -0.5, 0.0), 34, 1.0), (6.00, (-0.15, -0.1, 9.2), (0.0, -0.8, 0.0), 34, 1.0),
          (6.30, (-0.20, -0.5, 8.8), (0.0, -1.2, 0.0), 34, 1.0), (6.50, (-0.10, -1.2, 8.6), (0.0, -1.7, 0.0), 34, 1.0),
          (6.95, (1.0, -1.0, 8.6), (0.0, -1.5, 0.0), 34, 1.0), (7.20, (2.4, -0.6, 8.0), (0.5, -2.6, 0.0), 32, 1.0)]
    if P:
        ks = [(4.92, (1.2, 0.9, 7.0), (0.2, 0.2, 0.0), 32, 1.0), (T_IGN, (0.5, 0.8, 5.8), (0.0, -0.4, 0.0), 32, 1.0),
              (5.35, (0.2, 0.35, 5.2), (0.0, -0.8, 0.0), 34, 1.0), (6.00, (-0.1, 0.0, 4.9), (0.0, -1.1, 0.0), 34, 1.0),
              (6.30, (-0.1, -0.5, 4.6), (0.0, -1.5, 0.0), 34, 1.0), (6.50, (0.0, -1.1, 4.3), (0.0, -1.9, 0.0), 34, 1.0),
              (6.95, (0.6, -1.1, 4.4), (0.0, -1.5, 0.0), 34, 1.0), (7.20, (1.5, -0.9, 4.3), (0.3, -2.4, 0.0), 32, 1.0)]
    for tk, p, tg, lens, ten in ks:
        ctx.cam(tk, F4.p(*p), F4.p(*tg), lens=lens, fstop=3.6, focus=None, tension=ten)
    return dict()

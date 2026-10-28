"""ESCENA 02 - EL UNIVERSO DEL APRENDIZAJE  (1:67 - 2:93)

The camera follows the thread as it falls beneath the logo into a three-dimensional universe:
a winding path of heavy lesson nodes that the line lights one by one (each activation = light
reaction + a physical bounce), accelerating towards a giant EMPEZAR keycap at 2:40. The line
presses it: the face sinks, the base compresses, a shock-wave and sparks fly, the hatch flips
open and a phone slides out of the interior; the case falls away and the camera dives through the
screen without a cut.
"""
from __future__ import annotations

import math

import numpy as np

from .. import anim, duo as duolib, fx, geo, mat, thread, ui
from ..config import A, FPS, lin
from ..easing import (Polyline, catmull_rom, damped_osc, in_cubic, in_out_cubic, norm, out_cubic, smoothstep,
                      smootherstep, spring_follow, u)
from ..world import Frame

B_ORIGIN = (0.0, 46.0, -37.0)
PHONE_Z = 3.0            # phone glass plane in the button frame (z toward viewer)
PHONE_W, PHONE_H = 1.8, 3.7


def build(ctx):
    c = ctx.coll("s02", window=(1.6, 3.05))
    P = ctx.portrait
    Bf = Frame(B_ORIGIN, facing=(0, -1, 0))
    ctx.state["B"] = Bf
    ctx.state["U"] = Frame(Bf.p(0, 0, PHONE_Z), facing=(0, -1, 0))
    t0, t_press = 1.70, A["press"]

    # ------------------------------------------------------------------ thread path (continues from the logo)
    W0 = np.asarray(ctx.state["th1_end"], float)
    way = np.array([W0, (3.6, 2.1, -6.0), (1.2, 5.6, -9.8), (-2.6, 9.8, -13.8), (-4.0, 14.4, -18.2), (-1.6, 19.2, -22.6),
                    (2.4, 23.5, -26.8), (3.0, 28.0, -30.6), (1.0, 32.6, -34.0), (0.0, 37.4, -36.6),
                    tuple(Bf.p(0, 0, 0.62))])
    path = catmull_rom(way, 700)
    pl = Polyline(path)
    L = pl.length
    keys = [(t0, 0.0), (1.78, 0.066), (1.90, 0.21), (2.05, 0.45), (2.20, 0.70), (2.33, 0.92), (t_press, 1.0)]
    prof = thread.profile(keys)
    seg = thread.Segment(ctx, "th2", c, path, t0, t_press, ease=prof, radius=0.020, halo=2.8, tail=3.2)
    ctx.state["th2"] = seg
    fr = np.arange(int(t0 * FPS), int((t_press + 0.25) * FPS))
    tt = fr / FPS
    hp = seg.head_pos(tt)
    head = thread.Head(ctx, "h2", c, radius=0.07)
    head.key(fr, hp, size=1.0, power=170, color=lin("mask"), bead_strength=14)

    def s_of(t):
        return np.asarray(prof(np.asarray(t, float))) * L

    # ------------------------------------------------------------------ lesson nodes
    m_star_off = mat.principled("node_star_off", "#4A5D69", 0.5)
    m_star_on = mat.principled("node_star_on", "#FFFFFF", 0.3, emit="#FFFFFF", emit_strength=0.5, coat=0.4)
    nodes = []
    sN = 3.2
    k = 0
    while sN < L - 7.5:
        nodes.append(sN)
        sN += 3.1
    s_grid = np.linspace(0, L, 4000)
    for i, sn in enumerate(nodes):
        p = pl.at(sn)
        T = pl.tangent(sn)
        fr_n = Frame(p, facing=-T, up_hint=(0, 1, 0))
        root = fr_n.empty(f"node{i}", c)
        top_m = mat.principled(f"node{i}_top", "#33444E", 0.42, coat=0.15, rvar=0.04)
        base_m = mat.principled(f"node{i}_base", "#1C282F", 0.55, rvar=0.04)
        star_m = mat.principled(f"node{i}_star", "#5B6F7C", 0.4, emit="#FFFFFF", emit_strength=0.0)
        base = geo.slab(f"node{i}_b", c, 1.8, 1.8, 0.40, R=0.9, rb=0.08, mat=base_m, loc=(0, 0, -0.17), parent=root)
        top = geo.slab(f"node{i}_t", c, 1.58, 1.58, 0.26, R=0.79, rb=0.08, mat=top_m, loc=(0, 0, 0.10), parent=root)
        star = geo.prism(f"node{i}_s", c, geo.star_poly(0.50, 0.24), 0.12, bevel=0.03, mat=star_m, loc=(0, 0, 0.28), parent=root)
        # activation: the head crosses sn
        ta = float(tt[int(np.argmin(np.abs(s_of(tt) - sn)))])
        ctx.ev("node", ta, i=i)
        f0 = int(round(ta * FPS)) - 1
        fs = np.arange(f0, f0 + 28)
        ts = (fs - f0) / FPS - 1 / FPS
        on = smoothstep(u(ts, 0.0, 0.05))
        bounce = damped_osc(ts - 0.0, 0.26, 4.2, 0.28) * (ts >= 0)
        sc_ = 1 + bounce
        anim.key_vec(top, "scale", fs, np.stack([sc_, sc_, 1 + 0.4 * bounce], 1))
        # physical bounce: node is pushed away from the thread then springs back
        anim.key_vec(top, "location", fs, np.stack([0 * ts, 0 * ts, 0.08 + 0.34 * damped_osc(ts, 1.0, 3.8, 0.26) * (ts >= 0)], 1))
        anim.key_vec(star, "location", fs, np.stack([0 * ts, 0 * ts, 0.24 + 0.34 * damped_osc(ts, 1.0, 3.8, 0.26) * (ts >= 0) + 0.06 * np.clip(bounce, 0, 1)], 1))
        # colour: slate -> brand green, star -> white; plus a light-reaction pulse on the surface
        gr = np.array(lin("feather"))
        sl = np.array(lin("#33444E"))
        col = sl[None] + (gr - sl)[None] * on[:, None]
        anim.key_vec(top_m.node_tree, mat.path_color(top_m), fs, np.concatenate([col, np.ones((len(fs), 1))], 1))
        gd = np.array(lin("feather_dark"))
        sb = np.array(lin("#1C282F"))
        colb = sb[None] + (gd - sb)[None] * on[:, None]
        anim.key_vec(base_m.node_tree, mat.path_color(base_m), fs, np.concatenate([colb, np.ones((len(fs), 1))], 1))
        anim.key_vec(star_m.node_tree, mat.path_color(star_m), fs,
                     np.concatenate([np.array(lin("#5B6F7C"))[None] + (np.array(lin("#FFFFFF")) - np.array(lin("#5B6F7C")))[None] * on[:, None], np.ones((len(fs), 1))], 1))
        pulse = np.exp(-ts.clip(0) * 9.0) * (ts >= 0)
        anim.key(top_m.node_tree, mat.path_emit_strength(top_m), fs, 0.45 * pulse)
        anim.key_vec(top_m.node_tree, mat.path_emit_color(top_m), fs, np.tile([*lin("mask"), 1], (len(fs), 1)))
        anim.key(star_m.node_tree, mat.path_emit_strength(star_m), fs, 0.05 + 0.9 * pulse + 0.35 * on)
    ctx.state["node_times"] = None

    # ------------------------------------------------------------------ the EMPEZAR keycap + hatch case
    Bobj = Bf.empty("B", c)
    case = geo.empty("case", c, parent=Bobj)
    dkg = mat.principled("case_bar", "#2A6A02", 0.5, rvar=0.04)
    dk_in = mat.principled("case_in", "#04080A", 0.8)
    for nm, (w, h, loc) in dict(top=(6.7, 0.25, (0, 2.025, -0.85)), bot=(6.7, 0.25, (0, -2.025, -0.85)),
                               l=(0.25, 3.8, (-3.225, 0, -0.85)), r=(0.25, 3.8, (3.225, 0, -0.85))).items():
        geo.slab(f"case_{nm}", c, w, h, 2.3, R=0.09, rb=0.03, mat=dkg, loc=loc, parent=case)
    geo.slab("case_back", c, 6.7, 4.3, 0.2, R=0.3, rb=0.04, mat=dk_in, loc=(0, 0, -2.0), parent=case)
    hinge = geo.empty("hinge", c, loc=(0, -1.9, 0.0), parent=case)
    btn = ui.button3d(ctx, c, "go", 6.2, 3.8, "EMPEZAR", depth=0.5, lip=0.28, text_size=1.05, parent=hinge, loc=(0, 1.9, 0))
    ctx.state["go"] = btn

    # phone (hollow bezel + glass; no back so the camera can pass through)
    phone = geo.empty("phone", c, loc=(0, 0, -1.55), parent=Bobj)
    m_alu = ui.M("alu")
    geo.bezel("phone_bezel", c, PHONE_W, PHONE_H, 0.30, 0.10, 0.18, rb=0.03, mat=m_alu, parent=phone)
    scr_m = mat.principled("phone_screen", "#06100C", 0.07, coat=1.0, coat_rough=0.02, emit="#58CC02", emit_strength=0.04)
    glass = geo.slab("phone_glass", c, PHONE_W - 0.1, PHONE_H - 0.1, 0.03, R=0.26, rb=0.01, mat=scr_m, loc=(0, 0, 0.075), parent=phone)
    ctx.state["phone"] = phone
    ctx.state["phone_screen_mat"] = scr_m

    # --- timeline: press, hatch, slide, fall
    f0, f1 = int(2.30 * FPS), int(3.02 * FPS)
    fr = np.arange(f0, f1)
    t = fr / FPS
    # press: face sinks 0.28 -> 0.02 in 3 frames, base compresses, holds, then the hatch opens
    pr = out_cubic(u(t, t_press, t_press + 0.05)) * (1 - smoothstep(u(t, t_press + 0.10, t_press + 0.18)))
    lid_z = 0.28 - 0.26 * pr
    anim.key_vec(btn["lid"], "location", fr, np.stack([0 * t, 0 * t, lid_z], 1))
    anim.key_vec(btn["base"], "scale", fr, np.stack([1 + 0.03 * pr, 1 + 0.03 * pr, 1 - 0.12 * pr], 1))
    anim.key_vec(btn["text"], "location", fr, np.stack([0 * t, 0 * t, 0.254 * np.ones_like(t)], 1))
    # hatch flips open about the bottom hinge with overshoot
    t_h = t_press + 0.10
    ang = np.radians(112) * (in_cubic(u(t, t_h, t_h + 0.07)) * 0.0 + smootherstep(u(t, t_h, t_h + 0.13)))
    ang = ang + np.radians(9) * damped_osc(t - (t_h + 0.13), 1.0, 5.0, 0.3) * (t > t_h + 0.13)
    anim.key_vec(hinge, "rotation_euler", fr, np.stack([ang, 0 * t, 0 * t], 1))
    # phone slides out of the interior, overshoots, settles
    t_s = A["phone_rise"]
    slide = in_out_cubic(u(t, t_s, t_s + 0.20))
    zph = -1.55 + (PHONE_Z + 1.55) * slide + 0.10 * damped_osc(t - (t_s + 0.20), 1.0, 4.0, 0.3) * (t > t_s + 0.2)
    anim.key_vec(phone, "location", fr, np.stack([0 * t, 0 * t, zph], 1))
    anim.key_vec(phone, "rotation_euler", fr, np.stack([0 * t, 0 * t, np.radians(2.0) * (1 - slide)], 1))
    # the case, relieved of its phone, tips forward and drops away
    t_f = t_s + 0.06
    tf = np.clip(t - t_f, 0, None)
    g = 110.0
    anim.key_vec(case, "location", fr, np.stack([0 * t, -0.5 * g * tf ** 2, 0.6 * tf * 0 + 0 * t], 1))
    anim.key_vec(case, "rotation_euler", fr, np.stack([np.radians(-60) * np.clip(tf / 0.25, 0, 1.4) ** 1.5, 0 * t, np.radians(8) * np.clip(tf / 0.25, 0, 1)], 1))
    # screen glow rises as we dive in (we pass through a luminous pane, no cut)
    t_e = A["enter_screen"]
    glow = 0.04 + 2.2 * smoothstep(u(t, t_e - 0.07, t_e + 0.02))
    anim.key(scr_m.node_tree, mat.path_emit_strength(scr_m), fr, glow)
    ctx.ev("press", t_press)
    ctx.ev("hatch", t_h)
    ctx.ev("phone_rise", t_s)
    ctx.ev("enter_screen", t_e)

    # shockwave + sparks at the face
    face = Bf.p(0, 0, 0.62)
    fx.shockwave(ctx, c, "ring1", t_press + 0.02, face, Bf.euler(), r0=0.8, r1=9.5, dur=0.34, tube=0.022, strength=7)
    fx.shockwave(ctx, c, "ring2", t_press + 0.02, face, Bf.euler(), r0=0.6, r1=6.0, dur=0.26, tube=0.016, strength=4, color="#58CC02", delay=0.05)
    fx.burst(ctx, c, "pressfx", t_press + 0.01, face, n=34, spd=(4, 16), size=(0.015, 0.045), life=(0.3, 0.65), axis=tuple(Bf.z),
             cone=0.8, seed=5, ring=(0.2, 2.2))

    # station lights
    kl = geo.area_light("s02_key", c, (0.8, 0.93, 1.0), 2200, size=5.0, loc=tuple(Bf.p(-5, 4.5, 8.5)),
                        rot=geo.look_rot(Bf.p(-5, 4.5, 8.5), Bf.p(0, 0, 0)))
    rl = geo.area_light("s02_rim", c, lin("mask"), 1800, size=3.5, loc=tuple(Bf.p(4, 3.5, -3.0)),
                        rot=geo.look_rot(Bf.p(4, 3.5, -3.0), Bf.p(0, 0, 0)))
    # make the lights live only while needed (they are in the s02 collection window already)

    # ------------------------------------------------------------------ camera: chase the head, then dive
    ext_len = 14.0
    T0 = pl.tangent(0.0)
    back_pts = np.array([path[0] - T0 * d for d in np.linspace(ext_len, 0.5, 8)])
    chase = Polyline(np.vstack([back_pts, path]))
    hold_pos = np.array((0, ctx.cam_keys[-1]["pos"][1], ctx.cam_keys[-1]["pos"][2]))
    hold_tgt = np.array(ctx.cam_keys[-1]["tgt"])
    lens_chase = 26.0
    tkeys = np.arange(1.72, 2.31, 0.04)
    back = 5.4 if not P else 4.6
    for tk in tkeys:
        sh = float(s_of(tk))
        bk = back + 4.5 * float(smoothstep(u(tk, 1.9, 2.3)))
        Tc = chase.tangent(sh + ext_len - bk + 0.5)
        Rc = norm(np.cross(Tc, (0, 0, 1.0)))
        off = Rc * (2.7 if not P else 2.1) + np.array([0, 0, 1.8 if not P else 2.0])
        pc = chase.at(sh + ext_len - bk + 0.5) + off
        tg = chase.at(sh + ext_len + 3.2)
        w = float(smoothstep(u(tk, 1.70, 2.04)))
        pos = hold_pos * (1 - w) + pc * w
        tgt = hold_tgt * (1 - w) + tg * w
        # bank into the turns
        Tn = chase.tangent(sh + ext_len)
        Tn2 = chase.tangent(sh + ext_len + 3.0)
        lat = float(np.cross(Tn, Tn2)[2])
        roll = float(np.clip(-lat * 25.0, -9, 9)) * w
        lens = 35 * (1 - w) + lens_chase * w
        ctx.cam(tk, pos, tgt, lens=lens, roll=roll, fstop=2.8, focus=None)
    # button hit and dive in button-frame coordinates (x = 0 throughout: a clean straight push)
    zs = [(2.40, 10.4, 0.55), (2.55, 9.3, 0.42), (2.68, 8.1, 0.25), (2.77, 6.2, 0.10), (2.85, 3.05, 0.02), (2.93, 2.60, 0.18)]
    for tk, z, y in zs:
        look_z = 0.5 if tk < 2.5 else PHONE_Z - 0.2
        ctx.cam(tk, Bf.p(0, y, z), Bf.p(0, y * 0.5 + (0.1 if tk >= 2.85 else 0), look_z - 4.0 if tk >= 2.85 else look_z),
                lens=28 if tk < 2.7 else 32, fstop=3.2, focus=None if tk < 2.85 else 1.8, tension=1.0 if tk < 2.85 else 0.35)
    ctx.shake(t_press + 0.01, tuple(Bf.d(0.0, 0.05, 0.28)), freq=7.5, decay=9.0, dur=0.5)
    return dict()

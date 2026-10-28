"""ESCENA 07 - CUATRO UNIVERSOS, UN CAMINO  (11:40 - 14:67)

The camera pulls away, the audio wave collapses back into one continuous line, and at the hub the line
splits into four branches. Each branch leads to its own universe on a ring around the hub, every
one with its own identity but the same material language:

  11:67 IDIOMAS      eight flag tiles orbit in a precise 3-D composition and light up as we pass
  12:42 MATEMÁTICAS  the ambient takes a blue cast; numbers and shapes slide together mechanically
  12:98 MÚSICA       a purple node reveals physical piano keys that play the score; ripples spread
  13:70 AJEDREZ      a minimalist board rises, the knight anticipates, leaps in an arc and lands

The four paths stay visible; the camera climbs out of the ring and reveals them as one structure.
"""
from __future__ import annotations

import math

import bpy
import numpy as np

from .. import anim, flags, fx, geo, mat, score, thread, ui
from ..config import A, FONT_BLACK, FPS, lin
from ..easing import (Polyline, catmull_rom, damped_osc, in_cubic, in_out_cubic, noise1d, norm, out_cubic, out_expo, settle,
                      smoothstep, smootherstep, u)
from ..world import Frame

RING = 10.5
THETA = dict(lang=225.0, math=135.0, music=45.0, chess=-45.0)
T_MOD = dict(lang=A["langs"], math=A["math_"], music=A["music"], chess=A["chess"])


def hub_world(ctx):
    F6 = ctx.state["F6"]
    return F6.p(21.0, -1.0, 6.0)


def mod_frame(H, name):
    th = math.radians(THETA[name])
    pos = H + np.array([RING * math.cos(th), RING * math.sin(th), 0.0])
    return Frame(pos, facing=H - pos, up_hint=(0, 0, 1))


def build(ctx):
    P = ctx.portrait
    H = hub_world(ctx)
    ctx.state["hub"] = H
    ctx.state["arm_paths"] = {}
    c = ctx.coll("s07", window=(11.2, 15.3))
    FL, FM, FU, FC = (mod_frame(H, n) for n in ("lang", "math", "music", "chess"))
    ctx.state["mods"] = dict(lang=FL, math=FM, music=FU, chess=FC)
    fr = np.arange(int(11.2 * FPS), int(15.4 * FPS))
    t = fr / FPS

    # ------------------------------------------------------------------ hub + the line coming back together
    hub_m = mat.emissive("hub_m", "#A8FF5A", 8.0)
    hub = geo.sphere("hub", c, 0.16, mat=hub_m, loc=tuple(H), seg=24, rings=12)
    s_hub = smoothstep(u(t, 11.55, 11.65)) * (1 + 0.12 * np.sin(2 * math.pi * 3 * t)) * (1 - smoothstep(u(t, 14.86, 15.06)))
    anim.key_vec(hub, "scale", fr, np.stack([s_hub, s_hub, s_hub], 1) * 0.16)
    hl = geo.point_light("hub_light", c, lin("mask"), 0.0, radius=0.2, loc=tuple(H))
    anim.key(hl.data, "energy", fr, 260 * s_hub)
    wave_pts = ctx.state["wave_pts"]
    lead_in = catmull_rom(np.array([wave_pts[-1], wave_pts[-1] + (H - wave_pts[-1]) * 0.35 + np.array([0, 0, 2.0]), H - (H - wave_pts[-1]) * 0.08]), 60)
    pth = np.vstack([np.array(wave_pts), lead_in[1:]])
    seg_in = thread.Segment(ctx, "th7in", c, pth, 11.38, 11.64, ease=thread.profile([(11.38, 0.0), (11.50, 0.45), (11.64, 1.0)]), radius=0.022, halo=2.8,
                            tail=None, fade=(11.64, 11.78))
    fh = np.arange(int(11.38 * FPS), int(11.80 * FPS))
    th_ = fh / FPS
    hin = thread.Head(ctx, "h7in", c, radius=0.07)
    visi = (1 - smoothstep(u(th_, 11.62, 11.68)))
    hin.key(fh, seg_in.head_pos(th_), size=visi, power=210 * visi, color=lin("mask"), bead_strength=14)

    # ------------------------------------------------------------------ four arms (stay visible) + wake-up pulses
    arm_end = {}
    rng = np.random.default_rng(31)
    for k, (name, F) in enumerate((("lang", FL), ("math", FM), ("music", FU), ("chess", FC))):
        C = F.p(0, 0, 0.0)
        mid = H + (C - H) * 0.5 + np.array([0, 0, 2.4 * (1 if k % 2 == 0 else -1)]) + rng.normal(0, 0.4, 3)
        arm = catmull_rom(np.array([H, H + (mid - H) * 0.55, mid, C - (C - mid) * 0.18, C]), 160)
        sg = thread.Segment(ctx, f"arm_{name}", c, arm, 11.62, 11.86, ease=smootherstep, radius=0.020, halo=2.8, tail=None, retract=(14.70, 14.98))
        arm_end[name] = arm
        ctx.state["arm_paths"][name] = arm
        # pulse head runs hub -> module just before the camera gets there
        tp0, tp1 = dict(lang=(11.64, 11.82), math=(12.20, 12.42), music=(12.74, 12.98), chess=(13.45, 13.70))[name]
        fp = np.arange(int(tp0 * FPS), int(tp1 * FPS) + 2)
        tp = fp / FPS
        pl = Polyline(arm)
        hp = pl.frac(smootherstep(u(tp, tp0, tp1)))
        pulse = thread.Head(ctx, f"pulse_{name}", c, radius=0.09)
        pv = smoothstep(u(tp, tp0, tp0 + 0.03)) * (1 - smoothstep(u(tp, tp1 - 0.02, tp1 + 0.02)))
        pulse.key(fp, hp, size=pv, power=300 * pv, color=lin("mask"), bead_strength=14)
        ctx.ev("arm_pulse", tp0, name=name)

    # ================================================================== IDIOMAS
    paths = flags.ensure()
    tl_w, tl_h = 1.5, 1.0
    tiles = []

    def flag_mat(code):
        m = mat.principled(f"flag_{code}", "#FFFFFF", 0.42, coat=0.25, coat_rough=0.12, emit="#FFFFFF", emit_strength=0.0)
        nt = m.node_tree
        img = nt.nodes.new("ShaderNodeTexImage")
        img.image = bpy.data.images.load(paths[code])
        img.image.colorspace_settings.name = "sRGB"
        uv = nt.nodes.new("ShaderNodeUVMap")
        nt.links.new(uv.outputs["UV"], img.inputs["Vector"])
        nt.links.new(img.outputs["Color"], nt.nodes["P"].inputs["Base Color"])
        nt.links.new(img.outputs["Color"], nt.nodes["P"].inputs["Emission Color"])
        return m

    rootL = FL.empty("LANG", c)
    tilt = math.radians(38)
    rings = [(8, 3.0, 1.35, 1), (5, 1.55, 1.9, -1)]
    codes = ["ES", "MX", "FR", "DE", "IT", "BR", "JP", "GB"]
    ci = 0
    t_l = T_MOD["lang"]
    for n, R, om, sgn in rings:
        for i in range(n):
            code = codes[ci % 8]
            ci += 1
            m = flag_mat(code)
            tl = geo.slab(f"flag_{code}_{ci}", c, tl_w * (0.75 if R < 2 else 1.0), tl_h * (0.75 if R < 2 else 1.0), 0.09, R=0.11, rb=0.018, mat=m, parent=rootL)
            phi = 2 * math.pi * i / n + sgn * om * (t - t_l)
            pos = np.stack([R * np.cos(phi), R * np.sin(phi) * math.cos(tilt), R * np.sin(phi) * math.sin(tilt)], 1)
            # tiles settle into the orbit with a spring-in from far away, then orbit
            fly = settle(t, t_l - 0.45 + 0.02 * ci, 0.30, overshoot=0.08, freq=3.0)
            pos = pos + np.stack([0 * t, 0 * t, -9.0 * (1 - fly)], 1)
            anim.key_vec(tl, "location", fr, pos)
            rz = 0.12 * np.sin(phi * 2)
            anim.key_vec(tl, "rotation_euler", fr, np.stack([0 * t, 0.35 * np.cos(phi), rz], 1))
            # light up as the camera sweeps past (staggered) - emission pulse, then a gentle glow
            tp = t_l + 0.10 + 0.045 * ci
            pulse = np.exp(-(t - tp).clip(0) * 6.0) * (t >= tp)
            anim.key(m.node_tree, mat.path_emit_strength(m), fr, 0.05 + 0.9 * pulse + 0.18 * (t >= tp))
            ctx.ev("flag_on", tp, i=ci)
            tiles.append(tl)
    gc = geo.sphere("lang_core", c, 0.28, mat=mat.emissive("lang_core_m", "#58CC02", 3.0), parent=rootL, seg=24, rings=12)
    gk = geo.area_light("lang_key", c, (0.8, 0.95, 1.0), 380, size=3.5, loc=tuple(FL.p(-1.5, 3.0, 5.0)), rot=geo.look_rot(FL.p(-1.5, 3.0, 5.0), FL.p(0, 0, 0)))
    gl = geo.area_light("lang_rim", c, lin("mask"), 380, size=3.0, loc=tuple(FL.p(2.0, 0.5, -3.0)), rot=geo.look_rot(FL.p(2.0, 0.5, -3.0), FL.p(0, 0, 0)))

    # ================================================================== MATEMATICAS
    rootM = FM.empty("MATH", c)
    t_m = T_MOD["math"]
    plate = geo.slab("math_plate", c, 7.6, 4.6, 0.20, R=0.4, rb=0.03, mat=mat.principled("math_plate_m", "#0F2230", 0.5, coat=0.15, rvar=0.04), loc=(0, -0.2, -0.45), parent=rootM)
    blue = mat.principled("math_blue", "macaw", 0.34, coat=0.35, rvar=0.03)
    blue2 = mat.principled("math_blue2", "humpback", 0.38, coat=0.3, rvar=0.03)
    white = mat.principled("math_white", "#EAF6FF", 0.35, coat=0.3)
    pieces = []
    xs = [-2.6, -1.3, 0.0, 1.3, 2.6]
    for i, (lab, x) in enumerate(zip(["2", "+", "3", "=", "5"], xs)):
        b = geo.slab(f"mb{i}", c, 1.05, 1.05, 0.50, R=0.20, rb=0.05, mat=blue if lab not in "+=" else blue2, loc=(x, 0.62, 0.0), parent=rootM)
        ui.text(c, f"mb{i}_t", lab, 0.82, white, loc=(0, -0.01, 0.255), parent=b, extrude=0.04)
        pieces.append((b, np.array([x, 0.62, 0.0])))
    shapes = []
    tri = [(0, 0.55), (-0.55, -0.40), (0.55, -0.40)]
    hexa = [(0.55 * math.cos(math.radians(30 + 60 * k)), 0.55 * math.sin(math.radians(30 + 60 * k))) for k in range(6)]
    s0 = geo.slab("ms0", c, 1.0, 1.0, 0.45, R=0.5, rb=0.06, mat=blue2, loc=(xs[0], -1.15, 0), parent=rootM)
    s1 = geo.slab("ms1", c, 1.0, 1.0, 0.45, R=0.14, rb=0.06, mat=blue, loc=(xs[1], -1.15, 0), parent=rootM)
    s2 = geo.prism("ms2", c, tri, 0.45, bevel=0.06, mat=white, loc=(xs[2], -1.12, 0), parent=rootM)
    s3 = geo.prism("ms3", c, hexa, 0.45, bevel=0.06, mat=blue2, loc=(xs[3], -1.15, 0), parent=rootM)
    s4 = geo.slab("ms4", c, 1.0, 1.0, 0.45, R=0.5, rb=0.06, mat=blue, loc=(xs[4], -1.15, 0), parent=rootM)
    for o, x in ((s0, xs[0]), (s1, xs[1]), (s2, xs[2]), (s3, xs[3]), (s4, xs[4])):
        pieces.append((o, np.array(o.location)))
    rngm = np.random.default_rng(12)
    for k, (o, fin) in enumerate(pieces):
        ta = t_m + 0.02 + 0.055 * k
        d = rngm.normal(0, 1, 3)
        d = d / np.linalg.norm(d) * rngm.uniform(5.0, 9.0)
        d[2] = abs(d[2]) * 0.6 + 2.0
        # mechanical: straight-line slide, sharp stop, tiny rebound + click-scale; no soft floaty easing
        ph = out_expo(u(t, ta - 0.22, ta))
        rb = 0.045 * damped_osc(t - ta, 1.0, 9.0, 0.18) * (t >= ta)
        pos = fin[None] + d[None] * (1 - ph)[:, None] + np.stack([0 * t, 0 * t, rb], 1)
        click = 1 + 0.06 * np.exp(-(t - ta).clip(0) * 14) * (t >= ta)
        anim.key_vec(o, "location", fr, pos)
        anim.key_vec(o, "scale", fr, np.stack([click, click, click], 1))
        anim.key_vec(o, "rotation_euler", fr, np.stack([0.9 * (1 - ph), 0.6 * (1 - ph), 0.4 * (1 - ph)], 1) * 0 + np.stack([0 * t, 0 * t, 1.6 * (1 - ph)], 1))
        ctx.ev("math_click", ta, i=k)
    ml = geo.area_light("math_blue_l", c, (0.15, 0.5, 1.0), 0.0, size=6.0, loc=tuple(FM.p(0, 1.5, 4.5)), rot=geo.look_rot(FM.p(0, 1.5, 4.5), FM.p(0, 0, 0)))
    anim.key(ml.data, "energy", fr, 900 * smoothstep(u(t, t_m - 0.10, t_m + 0.12)))
    geo.area_light("math_key", c, (0.85, 0.95, 1.0), 420, size=3.0, loc=tuple(FM.p(-2.5, 3.0, 5.0)), rot=geo.look_rot(FM.p(-2.5, 3.0, 5.0), FM.p(0, 0, 0)))
    ctx.tint(t_m - 0.10, t_m + 0.75, (0.20, 0.55, 1.0), 110, attack=0.2, release=0.4)

    # ================================================================== MUSICA
    rootU = FU.empty("MUSIC", c)
    t_u = T_MOD["music"]
    geo.slab("mus_plate", c, 8.2, 5.0, 0.22, R=0.4, rb=0.03, mat=mat.principled("mus_plate_m", "#17102A", 0.18, coat=0.5, coat_rough=0.06), loc=(0, -0.3, -0.5), parent=rootU)
    pm = mat.principled("mus_node", "beetle", 0.34, coat=0.4, rvar=0.03, emit="beetle", emit_strength=0.0)
    node = geo.slab("mus_node", c, 1.5, 1.5, 0.42, R=0.75, rb=0.07, mat=pm, loc=(0, 0.55, 0.15), parent=rootU)
    star = geo.prism("mus_star", c, geo.star_poly(0.40, 0.19), 0.1, bevel=0.025, mat=ui.M("tile"), loc=(0, 0, 0.26), parent=node)
    pulse_n = np.exp(-(t - t_u - 0.02).clip(0) * 7.0) * (t >= t_u + 0.02)
    anim.key(pm.node_tree, mat.path_emit_strength(pm), fr, 0.15 + 2.2 * pulse_n)
    sc_n = 1 + 0.14 * damped_osc(t - t_u - 0.02, 1.0, 5.0, 0.3) * (t >= t_u + 0.02)
    anim.key_vec(node, "scale", fr, np.stack([sc_n, sc_n, sc_n], 1))
    ivory = mat.principled("key_white", "#F3EEF8", 0.30, coat=0.4, coat_rough=0.1, emit="beetle", emit_strength=0.0)
    ebony = mat.principled("key_black", "#1B1230", 0.28, coat=0.5, emit="beetle", emit_strength=0.0)
    kmap = {0: ("w", 0), 1: ("b", 0), 2: ("w", 1), 3: ("b", 1), 4: ("w", 2), 5: ("w", 3), 6: ("b", 3), 7: ("w", 4), 8: ("b", 4), 9: ("w", 5),
            10: ("b", 5), 11: ("w", 6)}
    wx = [(i - 3.5) * 0.92 for i in range(8)]
    keysW, keysB = [], {}
    for i, x in enumerate(wx):
        mk = mat.clone(ivory, f"kw{i}_m")
        k = geo.slab(f"kw{i}", c, 0.84, 2.35, 0.30, R=0.10, rb=0.03, mat=mk, loc=(x, -1.35, 0.05), parent=rootU)
        keysW.append((k, mk, np.array([x, -1.35, 0.05])))
    for i in (0, 1, 3, 4, 5):
        x = (wx[i] + wx[i + 1]) / 2
        mk = mat.clone(ebony, f"kb{i}_m")
        k = geo.slab(f"kb{i}", c, 0.52, 1.40, 0.36, R=0.07, rb=0.03, mat=mk, loc=(x, -0.87, 0.22), parent=rootU)
        keysB[i] = (k, mk, np.array([x, -0.87, 0.22]))
    # keys slide out of the node (staggered), then play
    allk = [(k, m_, p, 0.0) for (k, m_, p) in keysW] + [(k, m_, p, 0.04) for (k, m_, p) in keysB.values()]
    for j, (k, m_, p, dly) in enumerate(allk):
        ta = t_u + 0.10 + 0.012 * j + dly
        ph = out_cubic(u(t, ta, ta + 0.20))
        start = np.array([0.0, 0.55, 0.20])
        pos = start[None] + (p - start)[None] * ph[:, None]
        sy = 0.05 + 0.95 * ph
        anim.key_vec(k, "location", fr, pos)
        anim.key_vec(k, "scale", fr, np.stack([0.25 + 0.75 * ph, sy, np.ones_like(t)], 1))
    ctx.ev("keys_out", t_u + 0.10)
    # the keys play the actual score, ripples spread over the plate
    notes = score.keys_in(t_u + 0.30, t_u + 0.95)
    press = {id(k): np.zeros_like(t) for (k, _, _, _) in allk}
    for (tn, mnote, dur, vel) in notes:
        typ, idx = kmap[mnote % 12]
        k, mk, p = (keysW[idx] if typ == "w" else keysB[idx])
        env = np.where(t >= tn, np.where(t < tn + 0.03, (t - tn) / 0.03, np.exp(-(t - tn - 0.03) * 7.0)), 0.0)
        press[id(k)] = np.maximum(press[id(k)], env * (0.5 + 0.5 * vel))
        ctx.ev("key_hit", tn, note=int(mnote))
        fx.shockwave(ctx, c, f"rip{tn:.2f}", tn, tuple(FU.p(p[0], -1.0, 0.0)), FU.euler(), r0=0.2, r1=2.6, dur=0.42, tube=0.012, color="#D9A8FF", strength=3.0)
    for j, (k, mk, p, d_) in enumerate(allk):
        pr = press[id(k)]
        ph0 = out_cubic(u(t, t_u + 0.10 + 0.012 * j + d_, t_u + 0.30 + 0.012 * j + d_))
        pos = (np.array([0.0, 0.55, 0.20])[None] + (p - np.array([0.0, 0.55, 0.20]))[None] * ph0[:, None]) - np.stack([0 * t, 0 * t, 0.12 * pr], 1)
        anim.key_vec(k, "location", fr, pos)
        anim.key_vec(k, "rotation_euler", fr, np.stack([0.05 * pr, 0 * t, 0 * t], 1))
        anim.key(mk.node_tree, mat.path_emit_strength(mk), fr, 1.8 * pr)
    ul = geo.area_light("mus_purple", c, (0.75, 0.4, 1.0), 0.0, size=5.0, loc=tuple(FU.p(0, 2.0, 5.0)), rot=geo.look_rot(FU.p(0, 2.0, 5.0), FU.p(0, 0, 0)))
    anim.key(ul.data, "energy", fr, 700 * smoothstep(u(t, t_u - 0.1, t_u + 0.15)))
    geo.area_light("mus_key", c, (0.9, 0.9, 1.0), 360, size=3.0, loc=tuple(FU.p(-2.5, 3.0, 5.0)), rot=geo.look_rot(FU.p(-2.5, 3.0, 5.0), FU.p(0, -0.5, 0)))
    ctx.tint(t_u - 0.10, t_u + 0.85, (0.75, 0.40, 1.0), 110, attack=0.2, release=0.4)

    # ================================================================== AJEDREZ
    rootC = FC.empty("CHESS", c)
    t_c = T_MOD["chess"]
    bd = geo.empty("board", c, loc=(0, -0.2, 0.0), parent=rootC)
    bd.rotation_euler = (math.radians(-48), 0, 0)
    sqs = 0.84
    sq_light = mat.principled("sq_light", "#35505F", 0.38, coat=0.25, rvar=0.03, emit="bee", emit_strength=0.0)
    sq_dark = mat.principled("sq_dark", "#142129", 0.45, coat=0.15, rvar=0.03, emit="bee", emit_strength=0.0)
    geo.slab("board_base", c, 8 * sqs + 0.5, 8 * sqs + 0.5, 0.26, R=0.28, rb=0.04, mat=mat.principled("board_base_m", "#0B1217", 0.45, coat=0.2), loc=(0, 0, -0.22), parent=bd)
    squares = {}
    for i in range(8):
        for j in range(8):
            light = (i + j) % 2 == 0
            mk = mat.clone(sq_light if light else sq_dark, f"sq{i}{j}_m")
            o = geo.slab(f"sq{i}{j}", c, sqs - 0.03, sqs - 0.03, 0.12, R=0.05, rb=0.015, mat=mk, loc=((i - 3.5) * sqs, (j - 3.5) * sqs, 0.0), parent=bd)
            squares[(i, j)] = (o, mk)
            # the board rises into place, rank by rank
            ta = t_c - 0.10 + 0.035 * (i + j) * 0.5 + 0.02 * j
            ph = out_cubic(u(t, ta, ta + 0.22))
            anim.key_vec(o, "location", fr, np.stack([0 * t + (i - 3.5) * sqs, 0 * t + (j - 3.5) * sqs, -1.4 * (1 - ph)], 1))
    # knight (stylised from primitives): base, collar, tapered body, head, snout, ears
    ym = mat.principled("knight_m", "bee", 0.26, coat=0.55, coat_rough=0.08, rvar=0.02, emit="bee", emit_strength=0.0)
    kn = geo.empty("knight", c, parent=bd)
    geo.cylinder("kn_base", c, 0.30, 0.10, mat=ym, loc=(0, 0, 0.11), parent=kn, seg=48, axis="Z")
    geo.cylinder("kn_collar", c, 0.20, 0.07, mat=ym, loc=(0, 0, 0.20), parent=kn, seg=40, axis="Z")
    body = geo.revolve("kn_body", c, [(0.0, 0.0), (0.20, 0.0), (0.17, 0.18), (0.13, 0.46), (0.11, 0.62), (0.0, 0.62)], mat=ym, loc=(0, 0, 0.24), parent=kn, seg=40)
    head = geo.sphere("kn_head", c, (0.15, 0.34, 0.20), mat=ym, loc=(0, 0.05, 0.92), parent=kn, seg=32, rings=16)
    head.rotation_euler = (math.radians(-38), 0, 0)
    snout = geo.sphere("kn_snout", c, (0.11, 0.18, 0.11), mat=ym, loc=(0, 0.28, 0.80), parent=kn, seg=24, rings=12)
    snout.rotation_euler = (math.radians(-60), 0, 0)
    for sx in (-0.07, 0.07):
        ear = geo.sphere(f"kn_ear{sx}", c, (0.04, 0.05, 0.11), mat=ym, loc=(sx, -0.10, 1.12), parent=kn, seg=14, rings=8)
    mane = geo.sphere("kn_mane", c, (0.05, 0.12, 0.34), mat=ym, loc=(0, -0.16, 0.86), parent=kn, seg=20, rings=10)
    mane.rotation_euler = (math.radians(20), 0, 0)
    sq_from, sq_to = (2, 1), (3, 3)
    p0 = np.array([(sq_from[0] - 3.5) * sqs, (sq_from[1] - 3.5) * sqs, 0.06])
    p1 = np.array([(sq_to[0] - 3.5) * sqs, (sq_to[1] - 3.5) * sqs, 0.06])
    t_ant, t_jump, t_land = t_c + 0.10, t_c + 0.20, t_c + 0.52
    ph = u(t, t_jump, t_land)
    along = in_out_cubic(ph) * 0.35 + ph * 0.65
    arc = 1.55 * np.sin(math.pi * ph)
    pos = p0[None] + (p1 - p0)[None] * along[:, None] + np.stack([0 * t, 0 * t, arc], 1)
    # anticipation: dip + lean back; stretch in flight; squash on landing, then ring-down
    ant = np.sin(math.pi * np.clip(u(t, t_ant, t_jump), 0, 1))
    sz = 1 - 0.20 * ant + 0.14 * np.sin(math.pi * np.clip(ph, 0, 1)) * (t >= t_jump) * (t < t_land)
    tl = t - t_land
    land = damped_osc(tl, 1.0, 5.0, 0.22) * (tl >= 0)
    sz = sz - 0.22 * land
    sxy = 1 / np.sqrt(np.clip(sz, 0.5, 2))
    pos = pos - np.stack([0 * t, 0 * t, 0.08 * ant + 0.0 * land], 1)
    lean = np.radians(14) * ant - np.radians(10) * np.sin(math.pi * np.clip(ph, 0, 1))
    anim.key_vec(kn, "location", fr, pos)
    anim.key_vec(kn, "scale", fr, np.stack([sxy, sxy, sz], 1))
    anim.key_vec(kn, "rotation_euler", fr, np.stack([lean, 0 * t, 0 * t], 1))
    ctx.ev("knight_anticipate", t_ant)
    ctx.ev("knight_jump", t_jump)
    ctx.ev("knight_land", t_land)
    # landing square flashes, ripples run across the board, the camera rig feels the beat
    o, mk = squares[sq_to]
    anim.key(mk.node_tree, mat.path_emit_strength(mk), fr, 3.0 * np.exp(-(t - t_land).clip(0) * 7) * (t >= t_land))
    al = math.radians(-48)
    yb = p1[1] * math.cos(al) - 0.1 * math.sin(al)
    zb = p1[1] * math.sin(al) + 0.1 * math.cos(al)
    land_w = FC.p(p1[0], yb - 0.2, zb)
    from mathutils import Matrix
    n_eul = (Matrix(FC.R.tolist()) @ Matrix.Rotation(al, 3, "X")).to_euler("XYZ")
    fx.shockwave(ctx, c, "knight_ring", t_land, tuple(land_w), n_eul, r0=0.3, r1=3.8, dur=0.40, tube=0.012, color="#FFD84A", strength=5.0)
    cl = geo.area_light("chess_warm", c, (1.0, 0.8, 0.3), 0.0, size=4.0, loc=tuple(FC.p(0, 3.5, 4.5)), rot=geo.look_rot(FC.p(0, 3.5, 4.5), FC.p(0, 0, 0)))
    anim.key(cl.data, "energy", fr, 520 * smoothstep(u(t, t_c, t_c + 0.2)))
    geo.area_light("chess_key", c, (0.85, 0.95, 1.0), 420, size=3.0, loc=tuple(FC.p(-3, 3.0, 5.0)), rot=geo.look_rot(FC.p(-3, 3.0, 5.0), FC.p(0, 0, 0)))

    # ------------------------------------------------------------------ camera: one continuous orbit round the hub.
    # The gaze is always on the ring point opposite the camera, so each universe takes its hero moment as the
    # orbit comes round (no whip pans), then the camera climbs out and looks down on the single structure.
    from scipy.interpolate import PchipInterpolator
    kt = [11.40, 11.62, 12.06, 12.70, 13.34, 14.12, 14.40]
    kdeg = [118.0, 105.0, 45.0, -45.0, -135.0, -225.0, -247.0]
    ang = PchipInterpolator(kt, np.radians(kdeg))
    lens = 30.0 if not P else 21.0
    for tk in np.arange(11.62, 14.41, 0.04):
        a = float(ang(tk))
        # slow push in/out while each hero is on screen; a touch of height drift and bank
        Rc = 7.5 + 1.6 * math.sin(2 * math.pi * (tk - 11.62) / 1.30)
        hz = 0.5 * math.sin(2.1 * (tk - 11.6))
        pos = H + np.array([Rc * math.cos(a), Rc * math.sin(a), hz])
        tgt = H + np.array([RING * 0.92 * math.cos(a + math.pi), RING * 0.92 * math.sin(a + math.pi), 0.0])
        ctx.cam(float(tk), pos, tgt, lens=lens, fstop=4.5, focus=None, roll=float(4 * math.sin(2.0 * (tk - 11.9))))
    a_end = float(ang(14.4))
    ctx.cam(14.55, H + np.array([12.5 * math.cos(a_end - 0.08), 12.5 * math.sin(a_end - 0.08), 6.5]), H + np.array([0, 0, -1.0]), lens=lens, fstop=5.0, focus=None)
    ctx.cam(14.67, H + np.array([14.5 * math.cos(a_end - 0.20), 14.5 * math.sin(a_end - 0.20), 13.5]), H + np.array([0, 0, -1.0]), lens=lens, fstop=5.0, focus=None)
    return dict()

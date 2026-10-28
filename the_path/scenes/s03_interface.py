"""ESCENA 03 - LA SATISFACCION DE APRENDER  (2:93 - 4:80)

Behind the glass the interface is a physical 3-D space. Its elements fly in from the depth and lock
into place around the camera. "Traduce esta oración"; Duo says «Quiero un café, por favor»; the five
answer tiles rise at slightly different depths and snap into their slots magnetically (each contact
compresses the tile and makes the others tremble). COMPROBAR wakes up, the thread presses it, 4:23 is
the correct-answer moment (feedback sheet, confetti, Duo's hop), then the line fills the progress bar
and escapes through its end - the camera follows it out.

UI frame ``U``: x right, y up, z towards the viewer. The glass is z=0, the layers sit ~3 m behind.
The layout is format-specific: a wide two-column stage for 16:9, the tall phone column for 9:16.
"""
from __future__ import annotations

import math

import numpy as np

from .. import anim, duo as duolib, fx, geo, lipsync, mat, thread, ui
from ..config import A, FONT_BLACK, FPS, lin
from ..easing import (Polyline, catmull_rom, damped_osc, in_cubic, in_out_cubic, norm, out_back, out_cubic, settle,
                      smoothstep, smootherstep, spring_follow, u)
from . import s01_impact

ZL = -3.2           # main UI plane (behind the glass)
WORDS = ["Quiero", "un", "café,", "por", "favor"]
LOCKS = [3.62, 3.72, 3.82, 3.92, 4.02]


def layout(P):
    if P:   # tall phone column
        return dict(bar=(0.10, 1.55, 1.25), x_icon=(-0.66, 1.55), title=(-0.72, 1.17, 0.105), ledge=(-0.52, 0.0), duo_scale=0.30,
                    bubble=(0.42, 0.44, 1.08, 0.52), btext=0.083, rows_x0=-0.72, rows_y=(-0.30, -0.60), line_w=1.5, bank_x0=-0.72,
                    bank_y=(-1.00, -1.32), btn=(0.0, -1.72, 1.5), floor_y=-2.12, sheet=(0.0, -1.60, 1.92, 0.95), sz=0.108)
    return dict(bar=(0.15, 1.05, 2.9), x_icon=(-1.50, 1.05), title=(-1.65, 0.74, 0.13), ledge=(-1.00, -0.84), duo_scale=0.42,
                bubble=(-0.98, 0.20, 1.50, 0.56), btext=0.10, rows_x0=0.05, rows_y=(0.34, 0.02), line_w=1.85, bank_x0=0.05,
                bank_y=(-0.45, -0.77), btn=(0.96, -1.12, 1.55), floor_y=-1.36, sheet=(0.0, -1.0, 3.5, 0.82), sz=0.118)


def build(ctx):
    P = ctx.portrait
    U = ctx.state["U"]
    c = ctx.coll("s03", window=(2.7, 5.15))
    root = U.empty("UI", c)
    ctx.state["UI_root"] = root
    k_in = 2.88
    LAY = layout(P)
    ctx.state["s03_layout"] = LAY

    # ---------------------------------------------------------------- floor (glossy, fades out)
    fm = mat.floor("ui_floor", "#0B1419", 0.16, 13.0, fade0=0.25, coat=0.3)
    fl = geo.slab("ui_floor", c, 26, 26, 0.02, R=13, rb=0.005, mat=fm, loc=(0, LAY["floor_y"], ZL - 3.0), parent=root, seg_arc=24)
    fl.rotation_euler = (-math.pi / 2, 0, 0)

    fly = []        # (obj, final_loc, t_in, off)

    def reg(o, t_in, off=(0.3, -0.25, -6.5)):
        fly.append((o, np.array(o.location, float), t_in, np.array(off, float)))
        return o

    # ---------------------------------------------------------------- app bar: close, progress trough + fill
    bx, bar_y, bw = LAY["bar"]
    bar_z = ZL + 0.45
    trough = reg(ui.card(ctx, c, "trough", bw, 0.10, d=0.05, R=0.05, material="trough", parent=root, loc=(bx, bar_y, bar_z)), k_in)
    fpiv = geo.empty("fill_pivot", c, loc=(bx - bw / 2, bar_y, bar_z + 0.03), parent=root)
    fill = geo.slab("fill", c, bw, 0.10, 0.06, R=0.05, rb=0.015, mat=mat.clone(ui.M("green_top"), "fill_m"), loc=(bw / 2, 0, 0), parent=fpiv)
    fly.append((fpiv, np.array(fpiv.location, float), k_in + 0.01, np.array((0.3, -0.25, -6.5))))
    xg = ui.M("gray_top")
    for sgn in (-1, 1):
        b = geo.slab(f"x{sgn}", c, 0.13, 0.028, 0.03, R=0.014, rb=0.005, mat=xg, loc=(LAY["x_icon"][0], LAY["x_icon"][1], bar_z), parent=root)
        b.rotation_euler = (0, 0, math.radians(45 * sgn))
        reg(b, k_in + 0.01)
    tx, ty, ts_ = LAY["title"]
    reg(ui.text(c, "title", "Traduce esta oración", ts_, loc=(tx, ty, bar_z + 0.02), parent=root, align="LEFT"), k_in + 0.02)

    # ---------------------------------------------------------------- Duo on a ledge + speech bubble
    lx, ly = LAY["ledge"]
    ledge = geo.slab("ledge", c, 1.15 if not P else 0.95, 0.95 if not P else 0.80, 0.08, R=0.40 if not P else 0.34, rb=0.02, mat=ui.M("card2"),
                     loc=(lx, ly - 0.045, ZL), parent=root)
    ledge.rotation_euler = (-math.pi / 2, 0, 0)
    reg(ledge, k_in + 0.03)
    D = duolib.Duo(ctx, "D3", c, scale=LAY["duo_scale"])
    ctx.objs["duo3"] = D
    holder = duolib.mount(D, root, loc=(lx, ly, ZL))
    fly.append((holder, np.array(holder.location, float), k_in + 0.04, np.array((-0.4, -0.2, -6.5))))
    bxc, byc, bwid, bhei = LAY["bubble"]
    bub = reg(ui.card(ctx, c, "bubble", bwid, bhei, d=0.07, R=0.16, material="card2", parent=root, loc=(bxc, byc, ZL + 0.08)), k_in + 0.05)
    tail = geo.slab("tail", c, 0.14, 0.14, 0.07, R=0.025, rb=0.01, mat=ui.M("card2"), loc=(bxc - bwid / 2 + 0.28, byc - bhei / 2 - 0.02, ZL + 0.08), parent=root)
    tail.rotation_euler = (0, 0, math.radians(45))
    reg(tail, k_in + 0.05)
    btxt = ui.text(c, "btext", "I want a coffee,\nplease", LAY["btext"], ui.M("text_dim"), loc=(-bwid / 2 + 0.10, 0.04, 0.045), parent=bub, align="LEFT")
    btxt.data.space_line = 1.15

    # ---------------------------------------------------------------- answer lines, bank slots, tiles
    th, pad, gap = 0.22 * LAY["sz"] / 0.108, 0.09 * LAY["sz"] / 0.108, 0.06
    sz = LAY["sz"]
    widths = [geo.text_width(w, sz, FONT_BLACK) + 2 * pad for w in WORDS]
    x0 = LAY["rows_x0"]
    y1, y2 = LAY["rows_y"]
    ans = {}
    for row, y in (([0, 1, 2], y1), ([3, 4], y2)):
        x = x0
        for i in row:
            ans[i] = np.array([x + widths[i] / 2, y, ZL])
            x += widths[i] + gap
    for y in (y1, y2):
        ln = geo.slab(f"line{y}", c, LAY["line_w"], 0.014, 0.02, R=0.007, rb=0.003, mat=ui.M("edge"), loc=(x0 + LAY["line_w"] / 2, y - th * 0.62, ZL - 0.02), parent=root)
        reg(ln, k_in + 0.07)
    bank = {}
    for order, y in (([4, 1, 0], LAY["bank_y"][0]), ([3, 2], LAY["bank_y"][1])):
        x = LAY["bank_x0"]
        for i in order:
            bank[i] = np.array([x + widths[i] / 2, y, ZL])
            x += widths[i] + gap
    zjit = {0: 0.0, 1: -0.10, 2: 0.07, 3: -0.05, 4: 0.12}
    for i in range(5):
        slot = geo.slab(f"slot{i}", c, widths[i], th, 0.03, R=th * 0.28, rb=0.008, mat=ui.M("trough"), loc=tuple(bank[i] + np.array([0, -0.02, -0.03])), parent=root)
        reg(slot, k_in + 0.08)
    tiles = [ui.tile(ctx, c, f"t{i}", w, size=sz, parent=root, loc=tuple(bank[i] + np.array([0, 0, zjit[i]])), pad=pad, h=th, d=0.09)
             for i, w in enumerate(WORDS)]
    F = int(2.80 * FPS), int(4.9 * FPS)
    fr = np.arange(F[0], F[1])
    t = fr / FPS
    for i, tl in enumerate(tiles):
        t_in = k_in + 0.08 + 0.012 * i
        off = np.array((0.25 - 0.1 * i, -0.2, -6.5))
        fin = settle(t, t_in, 0.24, overshoot=0.07, freq=3.0)
        lock = LOCKS[i]
        pb = bank[i] + np.array([0, 0, zjit[i]])
        pa = ans[i]
        # levitate -> magnetic flight (accelerating into contact) -> compression -> later arrivals make it tremble
        t_lift, t_fly = lock - 0.42, lock - 0.17
        lift = settle(t, t_lift, 0.14, overshoot=0.12, freq=3.4)
        ph = u(t, t_fly, lock)
        flight = in_cubic(ph) * 0.78 + smoothstep(ph) * 0.22
        pos = pb[None] + off[None] * (1 - fin)[:, None] + np.stack([0 * t, 0.03 * lift, 0.17 * lift], 1)
        arc = np.sin(math.pi * np.clip(ph, 0, 1))
        carried = (pb + np.array([0, 0.03, 0.17]))[None] * (1 - flight)[:, None] + pa[None] * flight[:, None] + np.stack([0 * t, 0.10 * arc, 0.10 * arc], 1)
        pos = np.where((t >= t_fly)[:, None], carried, pos)
        g = damped_osc(t - lock, 1.0, 5.5, 0.22) * (t >= lock)
        seated = pa[None] + np.stack([0 * t, 0.012 * g, -0.012 * np.abs(g)], 1)
        for j in range(i + 1, 5):
            tt2 = t - LOCKS[j]
            seated = seated + np.stack([0 * t, 0.0035 * damped_osc(tt2, 1.0, 9.0, 0.25) * (tt2 >= 0), 0 * t], 1)
        pos = np.where((t >= lock)[:, None], seated, pos)
        tilt = np.radians(7) * np.sin(math.pi * np.clip(u(t, t_lift, lock), 0, 1)) * (1 if i % 2 == 0 else -1)
        anim.key_vec(tl["root"], "location", fr, pos)
        anim.key_vec(tl["root"], "rotation_euler", fr, np.stack([0 * t, 0 * t, tilt], 1))
        anim.key_vec(tl["body"], "scale", fr, np.stack([1 + 0.04 * g, 1 + 0.04 * g, 1 - 0.20 * g], 1))
        ctx.ev("tile_lock", lock, i=i)

    # ---------------------------------------------------------------- COMPROBAR button (wakes at check_on)
    cx, cy, cw = LAY["btn"]
    chk = ui.button3d(ctx, c, "chk", cw, 0.30 * (sz / 0.108) ** 0.5, "COMPROBAR", depth=0.12, lip=0.05, top="gray_top", base="gray_base",
                      text_size=0.085 * (sz / 0.108) ** 0.5, parent=root, loc=(cx, cy, ZL + 0.2))
    reg(chk["root"], k_in + 0.10)
    t_on = A["check_on"]
    on = smoothstep(u(t, t_on, t_on + 0.07))
    gr, sl = np.array(lin("feather")), np.array(lin("#3A4A54"))
    anim.key_vec(chk["mtop"].node_tree, mat.path_color(chk["mtop"]), fr, np.concatenate([sl[None] + (gr - sl)[None] * on[:, None], np.ones((len(fr), 1))], 1))
    gd, sb = np.array(lin("feather_dark")), np.array(lin("#26323A"))
    anim.key_vec(chk["mbase"].node_tree, mat.path_color(chk["mbase"]), fr, np.concatenate([sb[None] + (gd - sb)[None] * on[:, None], np.ones((len(fr), 1))], 1))
    pop = 1 + 0.10 * damped_osc(t - t_on, 1.0, 5.0, 0.3) * (t >= t_on)
    anim.key_vec(chk["root"], "scale", fr, np.stack([pop, pop, pop], 1))
    t_press = 4.18
    pr = out_cubic(u(t, t_press, t_press + 0.03)) * (1 - smoothstep(u(t, t_press + 0.05, t_press + 0.12)))
    anim.key_vec(chk["lid"], "location", fr, np.stack([0 * t, 0 * t, 0.05 - 0.04 * pr], 1))
    ctx.ev("check_on", t_on)
    ctx.ev("check_press", t_press)

    # ---------------------------------------------------------------- correct: feedback sheet, confetti, celebration
    t_ok = A["correct1"]
    sx, sy_end, sw, sh = LAY["sheet"]
    sheet = geo.slab("sheet", c, sw, sh, 0.10, R=0.16, rb=0.02, mat=mat.principled("sheet_m", "#15380B", 0.5, coat=0.2, rvar=0.04),
                     loc=(sx, LAY["floor_y"] - 1.0, ZL + 0.42), parent=root)
    ex = ui.text(c, "excel", "¡Excelente!", 0.17 if not P else 0.16, ui.M("green_text"), loc=(-sw / 2 + 0.12, sh * 0.2, 0.06), parent=sheet, align="LEFT")
    cont = ui.button3d(ctx, c, "cont", 1.2, 0.22, "CONTINUAR", depth=0.08, lip=0.035, text_size=0.075, parent=sheet,
                       loc=((sw / 2 - 0.75) if not P else 0.0, -sh * 0.25 if P else 0.0, 0.05))
    rise = settle(t, t_ok, 0.22, overshoot=0.10, freq=3.0)
    y_start = LAY["floor_y"] - 1.0
    sy = y_start + (sy_end - y_start) * rise
    anim.key_vec(sheet, "location", fr, np.stack([sx + 0 * t, sy, np.full_like(t, ZL + 0.42)], 1))
    ctx.ev("correct", t_ok)
    for nm, colr, seed in (("conf_g", "#58CC02", 1), ("conf_y", "#FFC800", 2), ("conf_b", "#1CB0F6", 3)):
        fx.burst(ctx, c, nm, t_ok + 0.02, tuple(U.p(sx, sy_end + sh / 2, ZL + 0.45)), n=14, spd=(0.8, 2.4), size=(0.012, 0.022), life=(0.5, 0.9),
                 axis=tuple(U.d(0, 1, 0.25)), cone=1.0, color=colr, strength=2.5, drag=2.5, seed=seed, ring=(0.0, 0.9 if not P else 0.6), stretch=1.6,
                 gravity=tuple(U.d(0, -1.6, 0)))
    for i, tl in enumerate(tiles):
        tc = t_ok + 0.03 + 0.025 * i
        anim.key_vec(tl["body"], "location", fr, np.stack([0 * t, 0.045 * damped_osc(t - tc, 1.0, 4.5, 0.25) * (t >= tc), 0 * t], 1))

    # ---------------------------------------------------------------- Duo: speech, gaze, celebration
    Fd = np.arange(int(2.84 * FPS), int(4.9 * FPS))
    td = Fd / FPS
    idle = duolib.idle(td, seed=3, rest=0.0, blinks=[3.35, 3.95, 4.55], energy=0.8)
    t_say0 = A["voice_duo"]
    dur_say = lipsync.duration("duo_line", 0.92)
    jaw = 0.42 * lipsync.envelope("duo_line", td, t_say0, dur_say, 8, seed=4)
    ctx.ev("duo_line", t_say0, dur=dur_say)
    hop_t = td - t_ok
    hop = np.where((hop_t >= 0) & (hop_t < 0.42), np.sin(math.pi * np.clip(hop_t / 0.42, 0, 1)) * 0.5, 0.0)
    st = (1 + 0.16 * np.sin(math.pi * np.clip(hop_t / 0.2, 0, 1)) * (hop_t >= 0) * (hop_t < 0.2)
          - 0.10 * damped_osc(hop_t - 0.42, 1.0, 4.0, 0.3) * (hop_t >= 0.42))
    land = damped_osc(hop_t - 0.42, 0.12, 4.5, 0.3) * (hop_t >= 0.42)
    squash = idle["squash"] * np.stack([1 / np.sqrt(st), 1 / np.sqrt(st), st], 1) * np.stack([1 + land, 1 + land, 1 - land], 1)
    happy = smoothstep(u(td, t_ok + 0.04, t_ok + 0.10)) * (1 - smoothstep(u(td, t_ok + 0.55, t_ok + 0.75)))
    lid = idle["lid"] + happy * 0.55
    gz = idle["gaze"].copy()
    gz[:, 0] += -np.interp(td, [3.4, 3.62, 3.92, 4.05], [0.0, 0.25, 0.30, 0.0]) * 0.5
    gz[:, 1] += np.interp(td, [3.4, 3.62, 4.05], [0.0, -0.18, -0.1])
    wflap = ((hop_t >= 0) & (hop_t < 0.5)) * np.sin(2 * math.pi * 3.4 * np.clip(hop_t, 0, 0.5)) ** 2 * np.exp(-3 * np.clip(hop_t, 0, 1))
    wl = idle["wing_l"] + np.stack([1.1 * wflap, 0 * wflap], 1)
    wr = idle["wing_r"] + np.stack([1.1 * np.roll(wflap, 2), 0 * wflap], 1)
    D.key(Fd, pos=np.stack([0 * td, 0 * td, hop], 1), squash=squash, lean=idle["lean"], wing_l=wl, wing_r=wr, lid_l=lid, lid_r=lid,
          gaze_l=gz, gaze_r=gz, jaw=jaw)
    s01_impact.duo_kit(ctx, D, c, power=0.30 * LAY["duo_scale"] ** 2 * 1.2)

    # ---------------------------------------------------------------- the thread inside: glass -> COMPROBAR -> progress bar -> out
    by_btn = cy + 0.18
    way_a = np.array([U.p(0, 0.02, 0.0), U.p(cx - 0.9, 0.5, ZL * 0.35), U.p(cx + 0.4, 0.1, ZL * 0.6), U.p(cx - 0.3, by_btn + 0.9, ZL * 0.85),
                      U.p(cx, by_btn, ZL + 0.30)])
    pa = catmull_rom(way_a, 160)
    seg_a = thread.Segment(ctx, "th3a", c, pa, 2.86, t_press, ease=lambda x: smootherstep(x) * 0.9 + 0.1 * x, radius=0.006, halo=2.6, tail=0.55)
    xl = bx - bw / 2
    xr = bx + bw / 2
    way_b = np.array([U.p(cx, cy + 0.05, ZL + 0.30), U.p(xl - 0.30, cy + 0.5, ZL + 0.1), U.p(xl - 0.35, 0.2, ZL + 0.0), U.p(xl - 0.25, bar_y - 0.25, ZL + 0.0),
                      U.p(xl, bar_y, ZL + 0.48), U.p(bx, bar_y, ZL + 0.48), U.p(xr, bar_y, ZL + 0.48),
                      U.p(xr + 0.28, bar_y - 0.05, ZL + 0.30), U.p(xr + 0.8, bar_y - 0.5, ZL - 1.2), U.p(xr + 0.7, 0.1, ZL - 4.0),
                      U.p(xr + 0.1, -0.2, ZL - 8.0), U.p(xr - 0.3, -0.35, ZL - 12.0)])
    pb = catmull_rom(way_b, 520)
    plb = Polyline(pb)
    Lb = plb.length
    xs_loc = (U.R.T @ (pb - U.o).T).T
    iL = int(np.argmin(np.abs(xs_loc[:, 0] - xl) + 3 * np.abs(xs_loc[:, 1] - bar_y)))
    iR = int(np.argmin(np.abs(xs_loc[:, 0] - xr) + 3 * np.abs(xs_loc[:, 1] - bar_y)))
    sL, sR = plb.cum[iL] / Lb, plb.cum[iR] / Lb
    f_exit = min(1.0, sR + (1 - sR) * 0.45)
    prof_b = thread.profile([(t_press, 0.0), (t_ok + 0.06, 0.05), (4.40, sL), (4.62, sR), (4.80, f_exit), (5.10, f_exit)])
    seg_b = thread.Segment(ctx, "th3b", c, pb, t_press, 5.10, ease=prof_b, radius=0.007, halo=2.6, tail=0.9, fade=(4.97, 5.10))
    ctx.state["th3b"] = seg_b
    ctx.state["th3_end_world"] = pb[-1].copy()
    ctx.state['th3_exit_world'] = seg_b.head_pos(np.array([4.80]))[0]
    ctx.state['th3_exit_dir'] = seg_b.head_dir(np.array([4.80]))[0]
    frH = np.arange(int(2.86 * FPS), int(4.80 * FPS) + 1)
    tH = frH / FPS
    hp = np.where((tH < t_press)[:, None], seg_a.head_pos(tH), seg_b.head_pos(tH))
    h3 = thread.Head(ctx, "h3", c, radius=0.022)
    vis = smoothstep(u(tH, 2.86, 2.90))
    h3.key(frH, hp, size=vis, power=34 * vis, color=lin("mask"), bead_strength=14)
    hl = (U.R.T @ (seg_b.head_pos(tH) - U.o).T).T
    prog = np.where(tH > 4.62, 1.0, 0.55 + 0.45 * np.clip((hl[:, 0] - xl) / (xr - xl), 0, 1) * (tH >= 4.38))
    anim.key_vec(fpiv, "scale", frH, np.stack([prog, np.ones_like(prog), np.ones_like(prog)], 1))
    ctx.ev("bar_fill", 4.40, dur=0.22)
    ctx.ev("line_escape", 4.62)

    # ---------------------------------------------------------------- fly-in keys
    for obj, fin_loc, t_in, off in fly:
        f0 = int((t_in - 0.02) * FPS)
        ff = np.arange(f0, f0 + int(0.5 * FPS))
        s = settle(ff / FPS, t_in, 0.24, overshoot=0.07, freq=3.0)
        anim.key_vec(obj, "location", ff, fin_loc[None] + off[None] * (1 - s)[:, None])

    # ---------------------------------------------------------------- lights
    kp = U.p(-1.8, 1.8, -0.2)
    geo.area_light("ui_key", c, (0.82, 0.93, 1.0), 170 if not P else 120, size=2.6, loc=tuple(kp), rot=geo.look_rot(kp, U.p(0, 0, ZL)))
    rp = U.p(1.8, 0.8, ZL - 2.5)
    geo.area_light("ui_rim", c, lin("mask"), 220, size=2.4, loc=tuple(rp), rot=geo.look_rot(rp, U.p(0, 0, ZL)))
    up_ = U.p(0, LAY["floor_y"] + 0.3, -0.2)
    geo.area_light("ui_under", c, (0.55, 0.9, 0.7), 45, size=2.4, loc=tuple(up_), rot=geo.look_rot(up_, U.p(0, 0.2, ZL)))

    # ---------------------------------------------------------------- camera
    if not P:
        cams = [(2.86, (0, 0.02, 0.05), (0, 0.1, ZL), 35), (2.93, (0.0, 0.40, -0.45), (0.0, 0.35, ZL), 35),
                (3.10, (-0.45, 0.10, -1.15), (-0.95, 0.12, ZL), 35), (3.38, (-0.20, -0.05, -1.25), (-0.35, 0.05, ZL), 35),
                (3.55, (0.55, 0.00, -1.05), (0.62, -0.05, ZL), 35), (3.85, (0.72, -0.05, -1.00), (0.62, -0.08, ZL), 37),
                (4.05, (0.85, -0.45, -0.95), (0.96, -0.80, ZL), 35), (4.20, (0.93, -0.70, -0.90), (0.96, -1.05, ZL), 33),
                (4.40, (0.40, 0.10, -0.80), (0.5, 0.40, ZL), 32), (4.60, (0.45, 0.90, -0.95), (0.45, 1.05, ZL), 32),
                (4.80, (1.15, 0.95, -1.7), (1.9, 0.5, ZL - 5.0), 30)]
    else:
        cams = [(2.86, (0, 0.02, 0.05), (0, 0.0, ZL), 35), (2.93, (0.0, 0.10, -0.75), (0, 0.10, ZL), 35),
                (3.30, (0.0, 0.10, -1.15), (0, 0.05, ZL), 35), (3.60, (0.0, -0.45, -1.15), (0.0, -0.50, ZL), 35),
                (4.00, (0.0, -0.50, -1.20), (0.0, -0.52, ZL), 35), (4.20, (0.0, -0.60, -1.10), (0.0, -0.70, ZL), 35),
                (4.45, (0.2, 0.30, -1.20), (0.1, 0.60, ZL), 34), (4.62, (0.15, 1.00, -1.20), (0.1, 1.40, ZL), 34),
                (4.80, (0.7, 1.20, -1.8), (1.5, 0.9, ZL - 4.0), 30)]
    for tk, p, tg, lens in cams:
        ctx.cam(tk, U.p(*p), U.p(*tg), lens=lens, fstop=5.6, focus=None, tension=1.0 if tk > 2.9 else 0.4)
    ctx.shake(t_ok, tuple(U.d(0.0, -0.008, 0.012)), freq=9, decay=10, dur=0.4)
    return dict()

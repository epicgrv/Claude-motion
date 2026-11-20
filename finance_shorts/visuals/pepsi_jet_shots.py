"""Shot list for "The $700,000 Pepsi Loophole" (80.6 s). Plate coordinates are plate pixels (1440x2560).
Every shot has camera motion and at least one visual gag; cuts land on the voiceover word timings."""
from __future__ import annotations

import math

import numpy as np
import skia

from finance_shorts.engine.character import INK, Char, Costume, CAST, P, col, draw_can
from finance_shorts.engine.comp import H, SAMP, W, Shot, blink, ease, keys, plate, spring
from finance_shorts.engine.gfx import (ad_card, burst, calculator, chalk_arrow, chalk_text, cheque, crt, dollar_eyes, fine_print,
                                       halo, icon_bulb, inflation_chart, magnifier, paper_rect, progress_bar, ruling_card, speed_lines,
                                       sweat, tag)

JOHN, BUDDY, INV, EXEC, TEEN, JUDGE, DRIVER = (Char(n) for n in ("JOHN", "BUDDY", "INVESTOR", "EXEC", "TEEN", "JUDGE", "DRIVER"))
INV_SHADES = Char("INVESTOR", Costume(**{**CAST["INVESTOR"].__dict__, "glasses": "aviator"}))
EXTRAS = [Char("SHADOW", Costume(torso=c, style=st, hair=h, hair_col=hc, beard=b))
          for c, st, h, hc, b in [("#7A5BA8", "tee", "slick", "#2b1d14", False), ("#3C8D7E", "suit", "messy", "#8a5a2b", False),
                                   ("#C24E4E", "vest", "slick", "#555555", True), ("#D9A441", "tee", "bun", "#3b2a20", False),
                                   ("#4F6DB8", "windbreaker", "shaggy", "#2a2a2a", False), ("#8EA34A", "tee", "slick", "#6b4226", False),
                                   ("#B8648F", "suit", "bun", "#c9a35f", False), ("#5C5C66", "vest", "messy", "#1d1d1d", True),
                                   ("#E07B39", "tee", "shaggy", "#3b2a20", False)]]
SEED = {"JOHN": 1, "BUDDY": 4, "INVESTOR": 6, "EXEC": 2, "TEEN": 3, "JUDGE": 5, "DRIVER": 8}

NIGHT = (0.93, 0.91, 0.97)
WARM = (1.03, 0.95, 0.84)
DAY = (1.0, 0.98, 0.95)
DUSK = (1.02, 0.88, 0.85)


def talk(fx, who):
    return fx.audio.speaking(who, fx.t)


# ------------------------------------------------------------------------------- acting system
GESTURES = {"JOHN": ["present", "point", "shrug", "hold2", "point_up"], "BUDDY": ["hold", "shrug"],
            "EXEC": ["hips", "present", "arms_up"], "INVESTOR": ["point", "relaxed"], "TEEN": ["point_up", "present"],
            "JUDGE": ["present"], "DRIVER": ["arms_up"]}
_BEATS = {}


def beats(fx, who):
    """Stressed-word times for a speaker: long words, words before punctuation, ALL-CAPS script words."""
    if who in _BEATS:
        return _BEATS[who]
    out = []
    for ln in fx.audio.tl["lines"]:
        if ln["who"] != who and not (who == "JOHN" and ln["who"] == "NAR"):
            continue
        caps = {w.strip(".,?!:;\"").lower() for w in ln["text"].split() if w.isupper() and len(w) > 2}
        for w in ln["words"]:
            word = w["w"].strip(".,?!:;\"-").lower()
            dur = w["e"] - w["s"]
            if dur > 0.3 or w["w"][-1:] in ".?!" or len(word) >= 7 or word in caps:
                out.append((w["s"], ln["who"] == who))
    _BEATS[who] = out
    return out


def gesture_weight(t, t0):
    """Anticipation dip -> hit -> hold -> settle, around a beat at t0."""
    d = t - t0
    if d < -0.12 or d > 0.75:
        return 0.0, 0.0
    if d < 0:
        return 0.0, -0.6 * (1 + d / 0.12) * (-d / 0.12)  # tiny anticipation squash
    if d < 0.12:
        return ease(d / 0.12, "out"), 1.0 - d / 0.12
    if d < 0.4:
        return 1.0, 0.0
    return 1.0 - ease((d - 0.4) / 0.35), 0.0


def actor(fx, ch, who, x, y, r, tint=WARM, act=True, enter=None, **kw):
    """Place a character with automatic acting: breathing, talk nods, beat gestures, eye darts, entrances."""
    from finance_shorts.engine.character import POSES, lerp_pose
    t = fx.t
    sd = SEED.get(who, 9)
    kw.setdefault("blink", blink(t, sd))
    kw.setdefault("mouth", talk(fx, who))
    base = kw.pop("pose", "stand")
    pose = POSES[base] if isinstance(base, str) else base
    if act:
        speaking = kw["mouth"] > 0 or fx.audio.speaking(who, t + 0.15) > 0
        # breathing + idle sway
        kw["bob"] = kw.get("bob", 0.0) + 0.035 * math.sin(t * 2.4 + sd)
        pose = dict(pose)
        pose["lean"] = pose.get("lean", 0) + 1.8 * math.sin(t * 0.9 + sd)
        # beat gestures (strong when this character speaks; soft when the narrator talks about John)
        if not pose.get("sit") and base not in ("kick", "jaw_drop", "slump", "walk_a", "walk_b"):
            best = (0.0, 0.0, None)
            for i, (bt, own) in enumerate(beats(fx, who)):
                w, sq = gesture_weight(t, bt)
                if w > best[0] or sq < best[1]:
                    best = (w * (1.0 if own else 0.55), sq, i)
            w, sq, i = best
            if i is not None and w > 0:
                g = GESTURES.get(who, ["present"])
                pose = lerp_pose(pose, POSES[g[i % len(g)]], w)
            kw["squash"] = kw.get("squash", 1.0) * (1.0 + 0.05 * sq + (0.03 * w if w else 0))
        # talking head nod / tilt
        if speaking:
            kw["head_tilt"] = kw.get("head_tilt", 0.0) + 5 * math.sin(t * 7.3 + sd) * (0.4 + kw["mouth"])
        # eye darts (saccades) unless the shot fixes the gaze hard
        lx, ly = kw.get("look", (0.0, 0.0))
        k = int(t * 1.1 + sd)
        jitter = ((k * 7919 % 13) / 13 - 0.5) * 0.5, ((k * 104729 % 11) / 11 - 0.5) * 0.3
        kw["look"] = (max(-1, min(1, lx + jitter[0])), max(-1, min(1, ly + jitter[1])))
    if enter:  # ("left"|"right"|"bottom", t0, dur) slide/hop in with overshoot
        side, t0, dur = enter
        k = spring(t - t0, 1.6, 6.0) if t > t0 else 0.0
        off = (1 - k) * {"left": -900, "right": 900, "bottom": 0}[side]
        x += off
        if side == "bottom":
            y += (1 - k) * 1200
    fx.char(ch, x, y, r, tint=tint, pose=pose, **kw)


def head_pos(x, y, r, pose="stand", face=1):
    """Approximate head centre of a character (for overlays like bulbs / $ eyes)."""
    sit = pose in ("sit", "sit_hold")
    return x, y - (2.93 if sit else 3.68) * r


def tv_flicker(t):
    return 0.75 + 0.25 * math.sin(t * 13) * math.sin(t * 7.3)


def plate_in(fx, name, w, h, cx, cy, zoom, t=0.0):
    """Draw a plate into the current local box (0..w,0..h) - used inside CRT screens."""
    img = plate(name)
    s = (w / img.width()) * zoom
    sw, sh = w / s, h / s
    src = skia.Rect.MakeXYWH(cx - sw / 2, cy - sh / 2, sw, sh)
    fx.c.drawImageRect(img, src, skia.Rect.MakeWH(w, h), SAMP)
    return s, src


def flying_papers(fx, t, n, box, seed=1, size=40, wind=(300, -60)):
    c = fx.c
    rng = np.random.default_rng(seed)
    for i in range(n):
        x0, y0 = rng.uniform(box[0], box[2]), rng.uniform(box[1], box[3])
        ph = rng.uniform(0, 6.28)
        x = (x0 + wind[0] * t * rng.uniform(0.5, 1.5) + math.sin(t * 3 + ph) * 40 - box[0]) % (box[2] - box[0]) + box[0]
        y = y0 + wind[1] * t + math.cos(t * 2.3 + ph) * 50
        c.save()
        c.translate(x, y)
        c.rotate(t * 220 * rng.uniform(-1, 1) + ph * 57)
        c.scale(1, abs(math.cos(t * 4 + ph)) * 0.8 + 0.2)
        r = skia.Rect.MakeXYWH(-size / 2, -size * 0.65, size, size * 1.3)
        c.drawRect(r, P(col("#F5F2E8")))
        c.drawRect(r, P(INK, 2))
        c.restore()


def back_heads(fx, t, glow=1.0):
    """Over-the-shoulder foreground: backs of John's (cap) and Buddy's (shaggy hair) heads, rim-lit by the TV."""
    c = fx.c
    for (x, y, r, kind) in ((290, 1730, 270, "cap"), (810, 1760, 280, "hair")):
        bob = math.sin(t * 2.3 + x) * 6
        y += bob
        c.drawCircle(x, y, r, P(col("#16110F")))
        if kind == "cap":
            p = skia.Path()
            p.moveTo(x - r * 0.95, y - r * 0.25)
            p.cubicTo(x - r * 0.9, y - r * 1.2, x + r * 0.9, y - r * 1.2, x + r * 0.95, y - r * 0.25)
            p.close()
            c.drawPath(p, P(col("#5A1512")))
            c.drawRect(skia.Rect.MakeXYWH(x - r * 0.22, y - r * 0.4, r * 0.44, r * 0.18), P(col("#3A0E0C")))
        else:
            for k in range(9):
                a = math.pi * (1.05 + k * 0.11)
                c.drawCircle(x + math.cos(a) * r * 0.92, y + math.sin(a) * r * 0.92, r * 0.28, P(col("#4A3F22")))
        rim = skia.Paint(AntiAlias=True, Color=col("#8EC9FF", int(150 * glow * tv_flicker(t))), Style=skia.Paint.kStroke_Style,
                         StrokeWidth=10, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 8))
        c.drawArc(skia.Rect.MakeXYWH(x - r, y - r, 2 * r, 2 * r), 200, 140, False, rim)


def tv_full(fx, t, u, content, push=0.05, ots=True):
    """Full-screen CRT on a blurred dark bedroom background."""
    fx.plate("P03_bedroom", 360, 1300, 3.2, blur=26, dim=0.5)
    fx.end()
    c = fx.c
    k = 1.0 + push * ease(u)
    c.save()
    c.translate(W / 2, H * 0.45)
    c.scale(k, k)
    c.translate(-W / 2, -H * 0.45)
    rect = skia.Rect.MakeXYWH(80, 520, 920, 690)
    crt(fx, rect, content, t)
    fx.glow(W / 2, 860, 900, "#7FB0FF", 0.16 * tv_flicker(t))
    c.restore()
    if ots:
        back_heads(fx, t)
    return rect


def hand_arm(fx, x0, y0, x1, y1, w=34):
    """Cartoon arm (stick line + ball hand) entering frame - for macro shots."""
    c = fx.c
    c.drawLine(x0, y0, x1, y1, skia.Paint(AntiAlias=True, Color=INK, StrokeWidth=w, StrokeCap=skia.Paint.kRound_Cap))
    c.drawCircle(x1, y1, w * 0.85, P(INK))


def hearts(fx, x, y, t, n=4):
    c = fx.c
    for i in range(n):
        tt = (t * 0.9 + i / n) % 1.0
        hx, hy = x + math.sin(tt * 6 + i) * 30 + (i - n / 2) * 25, y - tt * 220
        s = 26 * (1 - tt * 0.4)
        p = skia.Path()
        p.moveTo(hx, hy + s * 0.9)
        p.cubicTo(hx - s * 1.4, hy - s * 0.2, hx - s * 0.5, hy - s * 1.1, hx, hy - s * 0.35)
        p.cubicTo(hx + s * 0.5, hy - s * 1.1, hx + s * 1.4, hy - s * 0.2, hx, hy + s * 0.9)
        c.drawPath(p, P(col("#FF4F6D", int(255 * (1 - tt)))))


# ===================================================================================== shots
def giant_cheque(fx, x, y, w, rot=0.0):
    """Novelty-size cheque held up by John (drawn in plate space)."""
    cheque(fx, skia.Rect.MakeXYWH(x - w / 2, y - w * 0.24, w, w * 0.48), fx.t, rot=rot, write=1.0)


def dust_swirl(fx, t, cx, cy, n=60, spread=900, seed=3, color="#FFD9A0"):
    c = fx.c
    rng = np.random.default_rng(seed)
    for i in range(n):
        a0, r0, sp, sz = rng.uniform(0, 6.28), rng.uniform(80, spread), rng.uniform(0.6, 1.8), rng.uniform(2, 9)
        a = a0 + t * sp * 0.8
        x = cx + math.cos(a) * r0 * 1.3
        y = cy + math.sin(a) * r0 * 0.35 - (t * 60 * sp) % 300
        c.drawCircle(x, y, sz, skia.Paint(AntiAlias=True, Color=col(color, int(150 * rng.uniform(0.3, 1))),
                                          MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, sz * 0.7),
                                          BlendMode=skia.BlendMode.kScreen))


def s01(fx, t, u):  # HOOK: John + giant cheque, Harrier hovering behind him at golden hour
    k = ease(u, "out")
    fx.plate("P20_hero_street", 720, keys(t, [(0, 1600), (1.42, 1560)]), 1.2 + 0.16 * k, par=(-40 * k, 10 * k, 0.05 * k))
    fx.rays(720, 1150, 90, 160, 2400, "#FFC27A", 0.2, 11, seed=1)
    c = fx.c
    c.save()  # jet bobs in its downwash
    c.translate(0, math.sin(t * 5.5) * 10)
    fx.fg()
    c.restore()
    fx.glow(720, 1180, 520, "#FFB060", 0.35)
    dust_swirl(fx, t, 720, 1900, 70, 800)
    actor(fx, JOHN, "JOHN", 700, 2700, 210, tint=(1.08, 0.94, 0.82), pose="hold2", expr="grin", look=(0, 0.3),
          act=True, mouth=0.0)
    giant_cheque(fx, 700, 2370 + math.sin(t * 3) * 6, 900, rot=-3 + 2 * math.sin(t * 2))
    flying_papers(fx, t, 6, (0, 1250, 1440, 1800), seed=9, size=38, wind=(420, -90))
    fx.end()


def s02(fx, t, u):  # John kisses the envelope and posts it
    fx.plate("P22_mailbox_ai", 820, 1560, 1.4 + 0.1 * ease(u), par=(50 * ease(u), 0, 0.06 * ease(u)))
    kiss = 1.75 < t < 2.3
    actor(fx, JOHN, "JOHN", 560, 2160, 138, tint=DUSK, pose="hold" if t < 2.35 else "present",
          expr="happy" if kiss else "grin", prop={"kind": "envelope", "hand": "r"} if t < 2.6 else None, look=(0.5, 0))
    if kiss:
        hearts(fx, 640, 1560, t)
    fx.glow(1000, 900, 700, "#FFB060", 0.15)
    fx.end()


def s03(fx, t, u):  # push into the amount
    z = keys(t, [(2.86, 1.25), (4.26, 2.0)], "inout")
    fx.plate("P16_countertop", keys(t, [(2.86, 720), (4.26, 1010)]), keys(t, [(2.86, 1280), (4.26, 1240)]), z)
    cheque(fx, skia.Rect.MakeXYWH(170, 1020, 1100, 520), t, rot=-1, write=1.0)
    c = fx.c
    if t > 3.4:  # pen circles the amount
        a = min(1.0, (t - 3.4) / 0.6)
        c.drawArc(skia.Rect.MakeXYWH(965, 1190, 320, 130), -90, 360 * a, False,
                  skia.Paint(AntiAlias=True, Color=col("#D7261E"), StrokeWidth=9, Style=skia.Paint.kStroke_Style,
                             StrokeCap=skia.Paint.kRound_Cap))
    fx.end()


def anim_frame(name, i):
    from finance_shorts.engine.comp import ROOT
    from functools import lru_cache
    p = ROOT / "visuals" / "pepsi-jet" / "plates" / name / f"{i:04d}.png"
    return skia.Image.open(str(p))


def s04(fx, t, u):  # REAL 3-D flyby (Blender animation, motion blur) + shake + speed lines
    from finance_shorts.engine.comp import ROOT
    i = max(0, min(47, int((t - 4.26) * 30)))
    if not (ROOT / "visuals" / "pepsi-jet" / "plates" / "P21_flyby" / "0047.png").exists():  # animation not finished
        fx.plate("P02_street_jet", 720, keys(t, [(4.26, 1500), (5.86, 1150)]), keys(t, [(4.26, 1.05), (5.86, 1.32)]),
                 shake=18 * math.sin(u * math.pi), rot=keys(t, [(4.26, -2), (5.86, 3)]))
        fx.end()
        speed_lines(fx, W / 2, H * 0.3, t, 30, 420, 0.35 * math.sin(u * math.pi))
        return
    img = anim_frame("P21_flyby", i)
    c = fx.c
    shake = 22 * math.exp(-((t - 5.35) / 0.25) ** 2)
    c.save()
    c.translate(math.sin(t * 61) * shake, math.cos(t * 53) * shake)
    c.drawImageRect(img, skia.Rect.MakeXYWH(-20, -36, W + 40, H + 72), SAMP)
    c.restore()
    speed_lines(fx, W / 2, H * 0.3, t, 34, 420, 0.4 * math.exp(-((t - 5.35) / 0.35) ** 2))


def s05(fx, t, u):  # bedroom wide
    fx.plate("P03_bedroom", 690, 1560, 1.45 + 0.12 * ease(u), par=(60 * ease(u), 0, 0.08 * ease(u)))
    scr = skia.Rect.MakeLTRB(292, 1228, 392, 1352)
    crt(fx, scr, lambda f, w, h, tt: plate_in(f, "P04_school_jet", w, h, 900, 1100, 2.2), t, bezel=False)
    fx.glow(340, 1290, 520, "#6FB8FF", 0.30 * tv_flicker(t))
    actor(fx, JOHN, "JOHN", 590, 1690, 92, tint=NIGHT, pose="sit", expr="neutral", look=(-1, 0))
    spoon_up = t > 6.6
    actor(fx, BUDDY, "BUDDY", 880, 1700, 94, tint=NIGHT, pose="sit_hold" if not spoon_up else "sit", expr="wide" if spoon_up else "deadpan",
          look=(-1, 0), prop={"kind": "bowl", "hand": "r"})
    fx.glow(420, 1500, 300, "#6FB8FF", 0.12 * tv_flicker(t))
    fx.end()


def s06(fx, t, u):  # the TV ad: jet lands at school
    def content(f, w, h, tt):
        s, src = plate_in(f, "P04_school_jet", w, h, keys(tt, [(7.44, 820), (9.56, 900)]), keys(tt, [(7.44, 1250), (9.56, 1150)]),
                          keys(tt, [(7.44, 1.3), (9.56, 1.6)]))
        f.c.save()
        f.c.translate(math.sin(tt * 40) * 3, math.cos(tt * 37) * 3)
        flying_papers(f, tt - 7.44, 14, (0, h * 0.3, w, h), seed=3, size=w * 0.04, wind=(w * 0.5, -h * 0.05))
        f.c.restore()
    tv_full(fx, t, u, content)


def s07(fx, t, u):  # TV teen: "Sure beats the bus."
    def content(f, w, h, tt):
        plate_in(f, "P04_school_jet", w, h, 1050, 1500, 1.35)
        c = f.c
        c.save()
        k = w / 1440 * 1.35
        f.char(TEEN, w * 0.45, h * 1.02, h * 0.15, tint=DAY, pose="point_up" if tt > 9.9 else "present", expr="grin",
               mouth=f.audio.speaking("TEEN", tt), blink=False)
        if tt > 10.15:  # tooth sparkle
            a = min(1, (tt - 10.15) / 0.15)
            f.glow(w * 0.47, h * 1.02 - h * 0.15 * 3.5, w * 0.06, "#FFFFFF", 0.9 * a)
        c.restore()
    tv_full(fx, t, u, content, push=0.08)


def s08(fx, t, u):  # price card
    pop = spring(t - 11.53, 2.6, 5.0) if t >= 11.53 else 0.0

    def content(f, w, h, tt):
        if tt < 11.5:
            ad_card(f, w, h, tt, "HARRIER FIGHTER", "", "")
        else:
            ad_card(f, w, h, tt, "HARRIER FIGHTER", "7,000,000", "POINTS", big_scale=max(0.01, pop))
    tv_full(fx, t, u, content)


def s09(fx, t, u):  # Buddy: drink Pepsi forever; a can falls off the pyramid
    fx.plate("P03_bedroom", 900, 1560, 2.25 + 0.2 * ease(u), par=(-50 * ease(u), 0, 0.06 * ease(u)))
    fx.glow(340, 1290, 700, "#6FB8FF", 0.22 * tv_flicker(t))
    fall = max(0.0, t - 14.35)
    for row, n in enumerate((4, 3, 2, 1)):
        for i in range(n):
            x, y = 1170 + (i - (n - 1) / 2) * 50, 1790 - row * 88
            if row == 3 and fall > 0:
                fx.c.save()
                fx.c.translate(x + fall * 260, y + min(fall, 0.35) ** 2 * 3000)
                fx.c.rotate(fall * 500)
                draw_can(fx.c, 0, 44, 88)
                fx.c.restore()
                continue
            draw_can(fx.c, x, y, 88)
    actor(fx, BUDDY, "BUDDY", 905, 1660, 98, tint=NIGHT, pose="sit_hold", expr="deadpan", look=(0.25, 0),
          prop={"kind": "bowl", "hand": "r"})
    fx.end()


def s10(fx, t, u):  # John reads the fine print: idea bulb
    z = keys(t, [(15.39, 2.6), (16.6, 2.8), (16.75, 3.3), (17.63, 3.4)])
    fx.plate("P03_bedroom", 600, 1420, z)
    fx.glow(340, 1290, 600, "#6FB8FF", 0.25 * tv_flicker(t))
    idea = t > 16.65
    actor(fx, JOHN, "JOHN", 600, 1690, 92, tint=NIGHT, pose="sit", expr="wide" if idea else "squint", look=(0.3, 0))
    if idea:
        hx, hy = head_pos(600, 1690, 92, "sit")
        icon_bulb(fx, hx + 30, hy - 180 - 20 * spring(t - 16.65), 55, min(1, (t - 16.65) / 0.1))
    fx.end()


def s11(fx, t, u):  # magnifier on the fine print
    c = fx.c
    page = skia.Rect.MakeXYWH(-40, 120, W + 80, H - 160)

    def draw_page(f, zoom=1.0, ox=0.0, oy=0.0):
        f.c.save()
        f.c.translate(ox, oy)
        f.c.scale(zoom, zoom)
        f.c.translate(page.left(), page.top())
        fine_print(f, page.width(), page.height(), highlight=max(0.0, min(1.0, (t - 18.4) / 0.8)))
        f.c.restore()
    c.save()
    c.drawRect(skia.Rect.MakeWH(W, H), P(col("#2A1F17")))
    draw_page(fx)
    c.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Color=skia.Color(20, 12, 5, 90)))
    c.restore()
    key_y = page.top() + 0.13 * page.height() + 17 * page.height() * 0.026
    mx = keys(t, [(17.63, 300), (18.4, 560), (19.95, 620)])
    my = keys(t, [(17.63, 600), (18.4, key_y - 10), (19.95, key_y)])
    zoom = 2.2
    magnifier(fx, mx, my, 330, lambda f: draw_page(f, zoom, mx * (1 - zoom), my * (1 - zoom)), t)


def s12(fx, t, u):  # kitchen: calculator frenzy
    fx.plate("P06_kitchen", 700, 1250, 1.55 + 0.1 * ease(u), shake=3 if t > 20.0 else 0, par=(-60 * u, 20 * u, 0.04 * u))
    actor(fx, JOHN, "JOHN", 700, 1640, 110, tint=WARM, pose="hold2", expr="squint", look=(0, 0.6))
    keys_ = ["7", "×", "0", ".", "1", "="]
    k = keys_[int((t - 19.95) / 0.27) % len(keys_)]
    calculator(fx, 980, 1720, 260, ["7000000", "7000000×", "0.1", "0.1", "0.1", "700000."][keys_.index(k)], t, press=k)
    hx, hy = head_pos(700, 1640, 110)
    sweat(fx, hx + 105, hy - 40 + (t * 120) % 60, 18)
    fx.end()


def s13(fx, t, u):  # KA-CHING + dollar eyes
    fx.plate("P06_kitchen", 700, 1150, 2.6, blur=14)
    actor(fx, JOHN, "JOHN", 700, 1640, 120, tint=WARM, pose="arms_up", expr="grin", look=(0, 0))
    hx, hy = head_pos(700, 1640, 120)
    dollar_eyes(fx, hx, hy, 120)
    fx.end()
    calculator(fx, W / 2, H * 0.73, 420, "700000.", t, glow=1.0)
    burst(fx, W * 0.78, H * 0.3, 190 * min(1, spring(t - 21.57)), "KA-CHING!", t=t)


def s14(fx, t, u):  # $20M tag vs $700K
    fx.plate("P04_school_jet", keys(t, [(22.67, 1000), (24.77, 1060)]), 1130, keys(t, [(22.67, 1.5), (24.77, 1.7)]),
             par=(-50 * u, math.sin(t * 5) * 12, 0.03 * u))
    drop = spring(t - 23.0, 1.8, 5.0) if t > 23.0 else 0
    fx.fg()
    tag(fx, 700, 1080 - (1 - drop) * 900, "$20,000,000+", "ONE (1) JET", rot=8 - 6 * drop, w=600,
        string_to=(760, 860 - (1 - drop) * 900))
    fx.end()
    c = fx.c
    if t > 23.6:  # tiny $700K sticky note
        a = min(1, (t - 23.6) / 0.15)
        c.save()
        c.translate(250, 1560)
        c.rotate(-8)
        c.scale(a, a)
        r = skia.Rect.MakeXYWH(-120, -90, 240, 180)
        c.drawRect(r.makeOffset(6, 10), skia.Paint(Color=skia.Color(0, 0, 0, 80), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 10)))
        c.drawRect(r, P(col("#FFF07A")))
        fx.text("$700K", 0, 20, 70, "caveat-700", "#1D2C7A")
        c.restore()


def s15(fx, t, u):  # 96% OFF tag swings in; John sweats
    fx.plate("P06_kitchen", 700, 1200, 2.3 + 0.1 * u, blur=6)
    actor(fx, JOHN, "JOHN", 700, 1700, 125, tint=WARM, pose="jaw_drop", expr="jaw", look=(0, 0))
    hx, hy = head_pos(700, 1700, 125)
    dollar_eyes(fx, hx, hy, 125)
    fx.end()
    sw = spring(t - 24.85, 1.4, 2.6)
    ang = (1 - sw) * 70
    c = fx.c
    c.save()
    c.translate(W / 2, -40)
    c.rotate(ang)
    tag(fx, -230, 560, "96% OFF", "", rot=0, w=470, color="#E8352B", ink="#FFFFFF", string_to=(0, 0))
    c.restore()


def s16(fx, t, u):  # Black Friday crowd turns to stare
    fx.plate("P17_store", 720, 1520, 1.5 + 0.08 * ease(u), par=(60 * u, 0, 0.05 * u))
    turn = t > 27.6
    for i, ch in enumerate(EXTRAS):
        x = 330 + i * 95 + (i % 2) * 20
        y = 1880 + (i % 3) * 30
        jit = math.sin(t * 25 + i) * 6 if not turn else 0
        fx.char(ch, x + jit, y, 46, tint=(0.85, 0.85, 0.95), pose="arms_up" if not turn else "stand",
                expr="angry" if not turn else "wide", mouth=0.6 if not turn else 0, look=(0, 1) if turn else (0, -1),
                blink=False, face=1 if i % 2 else -1)
    fx.end()
    if turn:
        burst(fx, W * 0.5, H * 0.32, 170 * min(1, spring(t - 27.6)), "96%?!", t=t, fill="#FFFFFF", text_col="#E8352B")


def s17(fx, t, u):  # classroom: arbitrage
    zoom = keys(t, [(28.6, 1.22), (32.85, 1.3)])
    cx = keys(t, [(28.6, 900), (32.85, 940)])
    fx.plate("P07_classroom", cx, 1330, zoom, par=(70 * u, 0, 0.05 * u))
    fx.rays(150, 700, 30, 40, 1800, "#FFE2B0", 0.12, 6, seed=2)
    chalk_text(fx, "ARBITRAGE", 935, 975, 150, (t - 29.35) / 0.8, align="center")
    chalk_text(fx, "BUY 10¢", 480, 1170, 100, (t - 30.3) / 0.5)
    chalk_arrow(fx, 835, 1135, 960, 1135, (t - 30.85) / 0.4)
    chalk_text(fx, "WORTH $$$", 980, 1170, 88, (t - 31.45) / 0.6)
    pose = "point_up" if t > 29.3 else "present"
    actor(fx, JOHN, "JOHN", 560, 1880, 122, tint=WARM, pose=pose, expr="grin" if t > 31.4 else "smug",
          nerd_glasses=True, prop={"kind": "pointer", "hand": "r"}, look=(0.4, 0))
    fx.end()


def s18(fx, t, u):  # Buddy: "This is insanity." + paper airplane bonk
    fx.plate("P07_classroom", 800, 1900, 1.75 + 0.1 * u, par=(-40 * u, 0, 0.05 * u))
    hit = t > 33.2
    actor(fx, BUDDY, "BUDDY", 800, 2330, 150, tint=WARM, pose="hold", expr="dead" if hit else "deadpan",
          prop={"kind": "bowl", "hand": "r"}, head_tilt=-6 if hit else 0)
    hx, hy = head_pos(800, 2330, 150)
    c = fx.c
    if not hit:
        k = (t - 32.85) / 0.35
        px, py = 1450 - k * 560, hy - 200 + k * 120
    else:
        px, py = hx + 120, hy - 60 + (t - 33.2) * 400
    c.save()
    c.translate(px, py)
    c.rotate(-15 if not hit else 60 + (t - 33.2) * 300)
    plane_ = skia.Path()
    plane_.moveTo(-70, 0)
    plane_.lineTo(70, -18)
    plane_.lineTo(-40, 30)
    plane_.close()
    c.drawPath(plane_, P(col("#F6F3EA")))
    c.drawPath(plane_, P(INK, 4))
    c.restore()
    if hit and t < 33.6:
        burst(fx, hx + 80, hy - 90, 60, "", t=t, fill="#FFFFFF")
    fx.end()


def s19(fx, t, u):  # diner: five investors crammed in one booth
    fx.plate("P08_diner", 720, 1360, 1.3 + 0.08 * ease(u), par=(80 * ease(u), 0, 0.05 * ease(u)))
    actor(fx, JOHN, "JOHN", 290, 1520, 92, tint=WARM, pose="sit_hold", expr="grin", look=(1, 0),
          prop={"kind": "napkin", "hand": "r"}, face=1)
    for i, ch in enumerate(EXTRAS[:4]):
        fx.char(ch, 1080 + i * 55 + (25 if i % 2 else 0), 1480 - (i % 2) * 40 - (60 if i == 3 else 0), 64,
                tint=WARM, pose="sit" if i != 3 else "stand", expr="squint" if i % 2 else "neutral", look=(-1, 0),
                blink=blink(t, 11 + i), face=-1)
    actor(fx, INV, "INVESTOR", 990, 1530, 92, tint=WARM, pose="sit", expr="smug", look=(-1, 0), face=-1)
    fx.end()


def s20(fx, t, u):  # investor lowers sunglasses
    fx.plate("P08_diner", 1050, 1180, 2.6 + 0.15 * u)
    ch = INV_SHADES if t > 35.95 else INV
    actor(fx, ch, "INVESTOR", 1010, 1530, 92, tint=WARM, pose="sit", expr="suspicious", look=(-1, 0), face=-1)
    fx.end()


def s21(fx, t, u):  # John: "...School?" + crickets
    fx.plate("P08_diner", 260, 1180, 2.6)
    actor(fx, JOHN, "JOHN", 210, 1520, 92, tint=WARM, pose="shrug", expr="wide", look=(0.5, 0), face=1)
    hx, hy = head_pos(210, 1520, 92, "sit")
    sweat(fx, hx + 80, hy - 50, 14)
    fx.end()


def s22(fx, t, u):  # cheque written for $700,008.50
    fx.plate("P16_countertop", 720, 1280, 1.35 + 0.1 * ease(u), par=(0, 0, 0.05 * u))
    w = max(0.0, min(1.0, (t - 37.7) / 2.6))
    cheque(fx, skia.Rect.MakeXYWH(170, 1020, 1100, 520), t, rot=-2, write=w)
    pen_x = 300 + (w * 6 % 1) * 700
    pen_y = 1130 + int(w * 5) * 75
    c = fx.c
    c.drawLine(pen_x + 220, pen_y - 260, pen_x, pen_y, skia.Paint(AntiAlias=True, Color=col("#1B3FA0"), StrokeWidth=26,
                                                                StrokeCap=skia.Paint.kRound_Cap))
    hand_arm(fx, pen_x + 600, pen_y + 300, pen_x + 160, pen_y - 150, 40)
    fx.end()


def s23(fx, t, u):  # envelope into the mailbox slot
    fx.plate("P22_mailbox_ai", 960, 1400, 2.6 + 0.2 * u, par=(30 * u, 0, 0.04 * u))
    c = fx.c
    k = min(1.0, (t - 40.45) / 0.35)
    c.save()
    c.clipRect(skia.Rect.MakeLTRB(0, 0, 868, 2560))
    r = skia.Rect.MakeXYWH(560 + k * 420, 1330, 190, 120)
    c.drawRect(r, P(col("#F3EBD9")))
    c.drawRect(r, P(INK, 5))
    c.restore()
    fx.end()


def s24(fx, t, u):  # order form: S&H $10.00 ticked
    fx.plate("P16_countertop", 720, 1280, 1.1, blur=8)
    fx.end()
    c = fx.c
    r = paper_rect(fx, skia.Rect.MakeXYWH(110, 380, 860, 1100), "#FFFDF4", 2)
    fx.text("PEPSI STUFF ORDER FORM", 430, 110, 46, "anton-400", "#1B2A6B")
    rows = [("HARRIER JET (1)", "7,000,000 PTS"), ("ORIGINAL POINTS", "15"), ("POINTS PURCHASED", "6,999,985"),
            ("x $0.10", "$699,998.50"), ("SHIPPING & HANDLING", "$10.00"), ("TOTAL", "$700,008.50")]
    for i, (a, b) in enumerate(rows):
        y = 260 + i * 130
        fx.text(a, 50, y, 40, "courier-prime-700", "#222222", align="left")
        fx.text(b, 810, y, 40, "courier-prime-700", "#1D2C7A", align="right")
        c.drawLine(50, y + 25, 810, y + 25, P(col("#BBBBBB"), 2))
    if t > 42.5:
        a = min(1.0, (t - 42.5) / 0.2)
        c.drawRect(skia.Rect.MakeXYWH(40, 260 + 4 * 130 - 55, 790, 75), P(col("#FFE94D", int(150 * a))))
        ck = skia.Path()
        ck.moveTo(835, 260 + 4 * 130 - 20)
        ck.lineTo(860, 260 + 4 * 130 + 10)
        ck.lineTo(905, 260 + 4 * 130 - 60)
        c.drawPath(ck, skia.Paint(AntiAlias=True, Color=col("#1E9E3E", int(255 * a)), StrokeWidth=14,
                                  Style=skia.Paint.kStroke_Style, StrokeCap=skia.Paint.kRound_Cap))
    c.restore()
    if t > 42.6:
        burst(fx, W * 0.72, H * 0.72, 150 * min(1, spring(t - 42.6)), "HONEST!", t=t, fill="#9FE3FF", text_col="#1B2A6B")


def s25(fx, t, u):  # "What is he, a criminal?" halo + choir
    fx.plate("P22_mailbox_ai", 700, 1620, 1.6, par=(0, 0, 0.05 * u))
    fx.rays(600, 300, 90, 55, 1900, "#FFF3C4", 0.25, 9, seed=7)
    actor(fx, JOHN, "JOHN", 560, 2160, 145, tint=(1.1, 1.05, 0.95), pose="hold2", expr="happy", look=(0, 0))
    hx, hy = head_pos(560, 2160, 145)
    halo(fx, hx, hy - 170, 100, t)
    fx.end()


def s26(fx, t, u):  # HQ tower crane-up
    fx.plate("P10_hq_tower", 720, keys(t, [(44.34, 1900), (46.1, 1300)]), keys(t, [(44.34, 1.25), (46.1, 1.1)]), par=(0, -90 * u, 0.1 * u))
    fx.rays(1200, 200, 120, 40, 2200, "#FFFFFF", 0.12, 6, seed=9)
    fx.end()


def s27(fx, t, u):  # exec spit-take + laugh kick
    fx.plate("P11_exec_office", 720, 1330, 1.95 + 0.12 * ease(u), shake=6 if t > 46.4 else 0, par=(0, 30 * u, 0.06 * u))
    spit = 46.1 <= t < 46.5
    pose = "hold" if t < 46.4 else ("kick" if int(t * 6) % 2 else "hips")
    actor(fx, EXEC, "EXEC", 720, 1700, 120, tint=WARM, pose=pose, expr="laugh" if t > 46.4 else "wide", look=(0, 0),
          prop={"kind": "mug", "hand": "r"} if t < 46.4 else None)
    hx, hy = head_pos(720, 1700, 120)
    c = fx.c
    if spit:  # coffee spray
        rng = np.random.default_rng(int(t * 30))
        for i in range(70):
            k = (t - 46.1) / 0.4
            a = rng.uniform(-0.5, 0.5)
            d = rng.uniform(100, 600) * k
            c.drawCircle(hx + math.cos(a) * d, hy + 60 + math.sin(a) * d * 0.6 + d * d * 0.0006, rng.uniform(4, 13),
                         P(col("#6B3A1E", 220)))
    if t > 46.5:
        flying_papers(fx, t - 46.5, 10, (200, 900, 1300, 1500), seed=8, size=70, wind=(260, -220))
    fx.end()


def s28(fx, t, u):  # envelope back through the slot; coupons cascade
    fx.plate("P23_porch_ai", 720, 1500, 1.5 + 0.1 * u, par=(50 * u, 0, 0.06 * u))
    c = fx.c
    rng = np.random.default_rng(12)
    for i in range(36):
        t0 = 48.5 + i * 0.04
        if t < t0:
            continue
        k = t - t0
        x = 724 + rng.uniform(-50, 50) + rng.uniform(-300, 300) * min(1, k * 1.5)
        y = min(1200 + 900 * k * k * 2.2, 1800 + rng.uniform(-60, 60))
        c.save()
        c.translate(x, y)
        c.rotate(rng.uniform(-180, 180) * min(1, k * 2))
        r = skia.Rect.MakeXYWH(-60, -28, 120, 56)
        c.drawRect(r, P(col("#FFF4C7")))
        c.drawRect(r, skia.Paint(AntiAlias=True, Color=col("#B23A2E"), Style=skia.Paint.kStroke_Style, StrokeWidth=3,
                                 PathEffect=skia.DashPathEffect.Make([8, 5], 0)))
        c.restore()
    if t < 48.7:
        e = skia.Rect.MakeXYWH(634, 1190 + (t - 48.24) * 300, 180, 90)
        c.drawRect(e, P(col("#F3EBD9")))
        c.drawRect(e, P(INK, 4))
    fx.end()


def s29(fx, t, u):  # FREE 2-LITER + jet progress bar
    fx.plate("P23_porch_ai", 720, 1720, 1.45 + 0.06 * u, par=(-40 * u, 0, 0.05 * u))
    actor(fx, JOHN, "JOHN", 720, 2440, 185, tint=DAY, pose="present", expr="dead", look=(0, 0.2),
          prop={"kind": "coupon", "hand": "r"})
    fx.end()
    frac = 0.0 if t < 50.9 else 0.004
    progress_bar(fx, 110, 330, 860, 80, frac, "JET PROGRESS", "0.00000%" if t < 50.9 else "0.00004%")
    if t > 50.4:
        fx.text("FREE 2-LITER", W * 0.68, H * 0.6, 54, "anton-400", "#B23A2E", stroke=6, stroke_col="#FFF4C7")


def s30(fx, t, u):  # courthouse, crane down, John marching up the steps
    fx.plate("P13_courthouse", 720, keys(t, [(53.82, 900), (55.18, 1400)]), 1.2, par=(0, -80 * u, 0.06 * u))
    k = (t - 53.82) / 1.36
    actor(fx, JOHN, "JOHN", 850 + k * 30, 1960 - k * 140, 60, tint=(0.95, 0.95, 1.0), pose="walk_a" if int(t * 5) % 2 else "walk_b",
          expr="squint", look=(0, -1))
    fx.end()


def s31(fx, t, u):  # courtroom ruling
    fx.plate("P14_courtroom", 720, keys(t, [(55.18, 1250), (59.75, 1200)]), keys(t, [(55.18, 1.6), (59.75, 1.85)]), par=(0, 40 * u, 0.08 * u))
    actor(fx, JUDGE, "JUDGE", 720, 1450, 100, tint=WARM, pose="hold2", expr="neutral", look=(0, 0.4),
          prop={"kind": "paper", "hand": "r"})
    fx.rays(0, 900, 20, 30, 1800, "#FFE2B0", 0.14, 6, seed=5)
    fx.end()
    rev = max(0.0, min(1.0, (t - 56.0) / 3.3))
    if t > 55.9:
        ruling_card(fx, skia.Rect.MakeXYWH(90, 1060 + (1 - spring(t - 55.9)) * 900, 900, 700), rev, t)


def s32(fx, t, u):  # Buddy: "Unreasonable person, right here."
    fx.plate("P14_courtroom", 720, 1350, 1.25 + 0.05 * u, par=(-50 * u, 0, 0.04 * u))
    actor(fx, JUDGE, "JUDGE", 720, 1450, 92, tint=WARM, pose="stand", expr="wide", look=(-0.6, 0.5))
    up = t > 59.9
    actor(fx, BUDDY, "BUDDY", 330, 2560, 210, tint=WARM, pose="raise_hand" if up else "hold", expr="grin",
          prop={"kind": "bowl", "hand": "l"}, look=(0.3, 0), face=1)
    fx.end()


def s33(fx, t, u):  # GAVEL
    k = max(0.0, 1 - (t - 61.84) / 0.25)
    fx.plate("P15_gavel", 720, 1300, 1.25 + 0.2 * (1 - k), shake=40 * k)
    fx.end()
    burst(fx, W * 0.5, H * 0.42, 330 * min(1, spring(t - 61.84, 3, 6)), "BANG!", t=t)
    if t < 61.95:
        fx.c.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Color=skia.Color(255, 255, 255, 140)))


def s34(fx, t, u):  # bus driver: sigh of relief, hugs the wheel
    fx.plate("P18_school_bus", 580, 1250, keys(t, [(62.7, 2.0), (65.68, 2.6)]), par=(0, 0, 0.12 * u))
    relief = t > 64.3
    actor(fx, DRIVER, "DRIVER", 560, 1335, 62, tint=DAY, pose="hold2" if relief else "hold",
          expr="happy" if relief else "neutral", look=(0, 0), mouth=0.4 if 64.3 < t < 65.4 else 0.0,
          head_tilt=8 * math.sin((t - 64.3) * 3) if relief else 0)
    if relief:
        hearts(fx, 560, 1080, t, 3)
    fx.end()


def s35(fx, t, u):  # bedroom: the ad re-airs
    fx.plate("P03_bedroom", 560, keys(t, [(65.68, 1500), (68.68, 1420)]), keys(t, [(65.68, 1.6), (68.68, 2.1)]))
    scr = skia.Rect.MakeLTRB(292, 1228, 392, 1352)
    crt(fx, scr, lambda f, w, h, tt: plate_in(f, "P04_school_jet", w, h, 900, 1100, 2.2), t, bezel=False)
    fx.glow(340, 1290, 520, "#6FB8FF", 0.30 * tv_flicker(t))
    actor(fx, JOHN, "JOHN", 590, 1690, 92, tint=NIGHT, pose="sit", expr="squint", look=(-1, 0))
    actor(fx, BUDDY, "BUDDY", 880, 1700, 94, tint=NIGHT, pose="sit_hold", expr="deadpan", look=(-1, 0),
          prop={"kind": "bowl", "hand": "r"})
    fx.end()


def s36(fx, t, u):  # 7,000,000 -> 700,000,000 (slot roll + slam)
    def content(f, w, h, tt):
        if tt < 68.9:
            ad_card(f, w, h, tt, "HARRIER FIGHTER", "7,000,000", "POINTS")
        elif tt < 70.1:
            rng = np.random.default_rng(int(tt * 30))
            ad_card(f, w, h, tt, "HARRIER FIGHTER", str(int(rng.integers(1e8, 9.9e8))), "POINTS")
        else:
            ad_card(f, w, h, tt, "HARRIER FIGHTER", "700,000,000", "POINTS", big_scale=1.0 + 0.3 * max(0, 1 - (tt - 70.1) / 0.2))
    tv_full(fx, t, u, content, push=0.1)
    if t > 70.1:
        fx.c.save()
        fx.c.translate(math.sin(t * 90) * 10 * max(0, 1 - (t - 70.1) / 0.3), 0)
        fx.c.restore()


def s37(fx, t, u):  # inflation chart cracks the screen
    k = max(0.0, min(1.0, (t - 70.9) / 1.55))
    rect = tv_full(fx, t, u, lambda f, w, h, tt: inflation_chart(f, w, h, k, tt), push=0.04)
    if t > 72.45:
        c = fx.c
        rng = np.random.default_rng(5)
        cx, cy = rect.left() + rect.width() * 0.82, rect.top() + 30
        for i in range(14):
            a = rng.uniform(0.2, 2.9)
            p = skia.Path()
            p.moveTo(cx, cy)
            x, y = cx, cy
            for j in range(5):
                x += math.cos(a + rng.uniform(-0.4, 0.4)) * rng.uniform(30, 90)
                y += math.sin(a + rng.uniform(-0.4, 0.4)) * rng.uniform(30, 90)
                p.lineTo(x, y)
            c.drawPath(p, P(skia.Color(255, 255, 255, 200), 3))
        burst(fx, cx, cy - 40, 120 * min(1, spring(t - 72.45)), "", t=t, fill="#FFFFFF")


def s38(fx, t, u):  # jaws on the floor
    fx.plate("P03_bedroom", 760, 1500, 2.0 + 0.15 * spring(t - 73.78, 2, 5))
    fx.glow(340, 1290, 700, "#6FB8FF", 0.28 * tv_flicker(t))
    actor(fx, JOHN, "JOHN", 600, 1690, 92, tint=NIGHT, pose="jaw_drop", expr="jaw", look=(-1, 0))
    actor(fx, BUDDY, "BUDDY", 890, 1700, 94, tint=NIGHT, pose="sit", expr="jaw", look=(-1, 0))
    c = fx.c
    if t > 74.0:  # spoon falling
        k = t - 74.0
        c.save()
        c.translate(1010, 1520 + min(k, 0.45) ** 2 * 1400)
        c.rotate(k * 600)
        c.drawLine(0, -40, 0, 40, P(col("#BFC4CA"), 10))
        c.drawOval(skia.Rect.MakeXYWH(-14, -62, 28, 34), P(col("#BFC4CA")))
        c.restore()
    fx.end()


def s39(fx, t, u):  # tiny words at the bottom of the screen
    def content(f, w, h, tt):
        ad_card(f, w, h, tt, "HARRIER FIGHTER", "700,000,000", "POINTS")
        txt = "(just kidding)"
        n = int(max(0, min(len(txt), (tt - 76.3) / 0.7 * len(txt))))
        if n:
            f.text(txt[:n], w * 0.97, h * 0.965, h * 0.035, "courier-prime-700", "#FFFFFF", align="right")
    rect = skia.Rect.MakeXYWH(80, 520, 920, 690)
    z = keys(t, [(75.12, 1.0), (77.2, 3.4)], "in")
    c = fx.c
    c.save()
    fx.plate("P03_bedroom", 360, 1300, 3.2, blur=26, dim=0.5)
    fx.end()
    c.translate(rect.right() - 60, rect.bottom() - 30)
    c.scale(z, z)
    c.translate(-(rect.right() - 60), -(rect.bottom() - 30))
    crt(fx, rect, content, t)
    c.restore()


def s40(fx, t, u):  # "(just kidding)" fills the frame - record scratch freeze
    c = fx.c
    c.drawRect(skia.Rect.MakeWH(W, H), P(col("#0F2A4A")))
    c.save()
    c.translate(W / 2, H * 0.47)
    c.rotate(-4)
    s = 1.0 + 0.04 * math.sin(t * 2)
    c.scale(s, s)
    fx.text("(just", 0, -40, 230, "anton-400", "#FFFFFF", stroke=14, stroke_col="#14082E")
    fx.text("kidding)", 0, 200, 230, "anton-400", "#FFD23F", stroke=14, stroke_col="#14082E")
    c.restore()
    for yy in range(0, H, 6):
        c.drawRect(skia.Rect.MakeXYWH(0, yy, W, 2.5), P(skia.Color(0, 0, 0, 50)))


def s41(fx, t, u):  # "So, we're keeping the cans?"
    fx.plate("P03_bedroom", 1000, 1600, 2.2 + 0.1 * u)
    fx.glow(340, 1290, 700, "#6FB8FF", 0.22 * tv_flicker(t))
    for row, n in enumerate((4, 3, 2, 1)):
        for i in range(n):
            if t > 79.9 and row == 3:
                continue
            draw_can(fx.c, 1170 + (i - (n - 1) / 2) * 50, 1790 - row * 88, 88)
    actor(fx, BUDDY, "BUDDY", 960, 1840, 110, tint=NIGHT, pose="hold2", expr="happy" if t < 79.4 else "wide", look=(0.4, 0),
          prop={"kind": "spoon", "hand": "r"})
    fx.end()


SHOTS = [
    Shot("S01", 0.0, 1.42, s01, cap_y=0.5, bloom=0.5, vignette=0.5), Shot("S02", 1.42, 2.86, s02, cap_y=0.84, whip=1), Shot("S03", 2.86, 4.26, s03, cap_y=0.8),
    Shot("S04", 4.26, 5.86, s04, cap_y=0.72, bloom=0.8, dust=0.2, whip=-1), Shot("S05", 5.86, 7.44, s05, cap_y=0.84),
    Shot("S06", 7.44, 9.56, s06, cap_y=0.79, dust=0.25), Shot("S07", 9.56, 10.77, s07, cap_y=0.79, dust=0.25),
    Shot("S08", 10.77, 12.97, s08, cap_y=0.79, dust=0.25), Shot("S09", 12.97, 15.39, s09, cap_y=0.84, whip=1),
    Shot("S10", 15.39, 17.63, s10, cap_y=0.84), Shot("S11", 17.63, 19.95, s11, cap_y=0.86, dust=0.2),
    Shot("S12", 19.95, 21.57, s12, cap_y=0.78), Shot("S13", 21.57, 22.67, s13, cap_y=0.3, whip=-1),
    Shot("S14", 22.67, 24.77, s14, cap_y=0.72), Shot("S15", 24.77, 26.69, s15, cap_y=0.8, whip=1),
    Shot("S16", 26.69, 28.6, s16, cap_y=0.62, bloom=0.8, whip=-1), Shot("S17", 28.6, 32.85, s17, cap_y=0.66, dust=0.7),
    Shot("S18", 32.85, 33.96, s18, cap_y=0.62, dust=0.7), Shot("S19", 33.96, 35.71, s19, cap_y=0.66, whip=1),
    Shot("S20", 35.71, 36.95, s20, cap_y=0.66), Shot("S21", 36.95, 37.64, s21, cap_y=0.84),
    Shot("S22", 37.64, 40.4, s22, cap_y=0.82), Shot("S23", 40.4, 41.82, s23, cap_y=0.66),
    Shot("S24", 41.82, 43.2, s24, cap_y=0.86, dust=0.2, whip=-1), Shot("S25", 43.2, 44.34, s25, cap_y=0.66, bloom=0.9),
    Shot("S26", 44.34, 46.1, s26, cap_y=0.66, bloom=0.7), Shot("S27", 46.1, 48.24, s27, cap_y=0.62, whip=1),
    Shot("S28", 48.24, 50.34, s28, cap_y=0.62), Shot("S29", 50.34, 53.82, s29, cap_y=0.78),
    Shot("S30", 53.82, 55.18, s30, cap_y=0.62), Shot("S31", 55.18, 59.75, s31, cap_y=0.48),
    Shot("S32", 59.75, 61.84, s32, cap_y=0.6), Shot("S33", 61.84, 62.7, s33, cap_y=0.75, bloom=0.8, whip=-1),
    Shot("S34", 62.7, 65.68, s34, cap_y=0.66, bloom=0.8), Shot("S35", 65.68, 68.68, s35, cap_y=0.84),
    Shot("S36", 68.68, 70.88, s36, cap_y=0.79, dust=0.25, whip=1), Shot("S37", 70.88, 73.78, s37, cap_y=0.79, dust=0.25),
    Shot("S38", 73.78, 75.12, s38, cap_y=0.84, whip=-1), Shot("S39", 75.12, 77.2, s39, cap_y=0.84, dust=0.2),
    Shot("S40", 77.2, 78.39, s40, cap_y=None, dust=0.0), Shot("S41", 78.39, 80.6, s41, cap_y=0.84, whip=1),
]

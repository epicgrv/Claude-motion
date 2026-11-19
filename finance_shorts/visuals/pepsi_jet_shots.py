"""Shot list for "The $700,000 Pepsi Loophole". Plate coordinates are in plate pixels (1440x2560)."""
from __future__ import annotations

import math

import skia

from finance_shorts.engine.character import Char, draw_can, col
from finance_shorts.engine.comp import H, W, Shot, blink, ease, keys, spring
from finance_shorts.engine.gfx import ad_card, chalk_arrow, chalk_text, crt

JOHN, BUDDY, INV, EXEC, TEEN, JUDGE, DRIVER = (Char(n) for n in ("JOHN", "BUDDY", "INVESTOR", "EXEC", "TEEN", "JUDGE", "DRIVER"))
SEED = {"JOHN": 1, "BUDDY": 4, "INVESTOR": 6, "EXEC": 2, "TEEN": 3, "JUDGE": 5, "DRIVER": 8}

NIGHT = (0.93, 0.91, 0.97)
WARM = (1.03, 0.95, 0.84)


def talk(fx, who):
    return fx.audio.speaking(who, fx.t)


def actor(fx, ch, who, x, y, r, tint=WARM, **kw):
    kw.setdefault("blink", blink(fx.t, SEED[who]))
    kw.setdefault("mouth", talk(fx, who))
    fx.char(ch, x, y, r, tint=tint, **kw)


def tv_flicker(t):
    return 0.75 + 0.25 * math.sin(t * 13) * math.sin(t * 7.3)


# ----------------------------------------------------------------------------------------- S05 bedroom wide
def s05(fx, t, u):
    zoom = 1.45 + 0.12 * ease(u)
    fx.plate("P03_bedroom", 690, 1560, zoom)
    # tiny ad playing on the TV in the plate
    scr = skia.Rect.MakeLTRB(292, 1228, 392, 1352)
    crt(fx, scr, lambda f, w, h, tt: ad_card(f, w, h, tt, "", "", ""), t, bezel=False)
    fx.glow(340, 1290, 520, "#6FB8FF", 0.30 * tv_flicker(t))
    actor(fx, JOHN, "JOHN", 590, 1690, 92, tint=NIGHT, pose="sit", expr="neutral", look=(-1, 0))
    actor(fx, BUDDY, "BUDDY", 880, 1700, 94, tint=NIGHT, pose="sit_hold", expr="deadpan", look=(-1, 0),
          prop={"kind": "bowl", "hand": "r"})
    fx.glow(420, 1500, 300, "#6FB8FF", 0.12 * tv_flicker(t))
    fx.end()


# ----------------------------------------------------------------------------------------- S08 TV price card
def s08(fx, t, u):
    zoom = 3.2
    fx.plate("P03_bedroom", 360, 1300, zoom, blur=26, dim=0.45)
    fx.end()
    c = fx.c
    k = 1.0 + 0.05 * ease(u)
    c.save()
    c.translate(W / 2, H * 0.45)
    c.scale(k, k)
    c.translate(-W / 2, -H * 0.45)
    rect = skia.Rect.MakeXYWH(80, 520, 920, 690)
    pop = spring(t - 11.53, 2.6, 5.0) if t >= 11.53 else 0.0

    def content(f, w, h, tt):
        if tt < 11.5:
            ad_card(f, w, h, tt, "HARRIER FIGHTER", "", "")
        else:
            ad_card(f, w, h, tt, "HARRIER FIGHTER", "7,000,000", "POINTS", big_scale=max(0.01, pop))

    crt(fx, rect, content, t)
    fx.glow(W / 2, 860, 900, "#7FB0FF", 0.18 * tv_flicker(t))
    c.restore()


# ----------------------------------------------------------------------------------------- S09 Buddy "drink forever"
def s09(fx, t, u):
    zoom = 2.25 + 0.2 * ease(u)
    fx.plate("P03_bedroom", 900, 1560, zoom)
    fx.glow(340, 1290, 700, "#6FB8FF", 0.22 * tv_flicker(t))
    # can pyramid
    for row, n in enumerate((4, 3, 2, 1)):
        for i in range(n):
            draw_can(fx.c, 1170 + (i - (n - 1) / 2) * 50, 1790 - row * 88, 88)
    actor(fx, BUDDY, "BUDDY", 905, 1660, 98, tint=NIGHT, pose="sit_hold", expr="deadpan", look=(0.25, 0),
          prop={"kind": "bowl", "hand": "r"})
    fx.end()


# ----------------------------------------------------------------------------------------- S17 classroom: arbitrage
def s17(fx, t, u):
    zoom = keys(t, [(28.6, 1.22), (32.85, 1.3)])
    cx = keys(t, [(28.6, 900), (32.85, 940)])
    fx.plate("P07_classroom", cx, 1330, zoom)
    chalk_text(fx, "ARBITRAGE", 935, 975, 150, (t - 29.35) / 0.8, align="center")
    chalk_text(fx, "BUY 10¢", 480, 1170, 100, (t - 30.3) / 0.5)
    chalk_arrow(fx, 835, 1135, 960, 1135, (t - 30.85) / 0.4)
    chalk_text(fx, "WORTH $$$", 980, 1170, 88, (t - 31.45) / 0.6)
    pose = "point_up" if t > 29.3 else "present"
    actor(fx, JOHN, "JOHN", 560, 1880, 122, tint=WARM, pose=pose, expr="grin" if t > 31.4 else "smug",
          nerd_glasses=True, prop={"kind": "pointer", "hand": "r"}, look=(0.4, 0))
    fx.end()


# ----------------------------------------------------------------------------------------- S18 Buddy: "This is insanity."
def s18(fx, t, u):
    fx.plate("P07_classroom", 800, 1900, 1.75 + 0.1 * u)
    actor(fx, BUDDY, "BUDDY", 800, 2330, 150, tint=WARM, pose="hold", expr="deadpan", look=(0, 0),
          prop={"kind": "bowl", "hand": "r"})
    fx.end()


SHOTS = [
    Shot("S05", 5.86, 7.44, s05, cap_y=0.66, dust=0.5),
    Shot("S08", 10.77, 12.97, s08, cap_y=0.79, dust=0.25),
    Shot("S09", 12.97, 15.39, s09, cap_y=0.64, dust=0.5),
    Shot("S17", 28.6, 32.85, s17, cap_y=0.66, dust=0.7),
    Shot("S18", 32.85, 33.96, s18, cap_y=0.62, dust=0.7),
]

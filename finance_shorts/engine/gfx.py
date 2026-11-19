"""In-world graphics drawn in code: CRT TV + 90s ad cards, chalk write-on, and helpers."""
from __future__ import annotations

import math
from functools import lru_cache

import numpy as np
import skia

from finance_shorts.engine.character import INK, P, col
from finance_shorts.engine.comp import SAMP, Frame, ease, font


def starburst(c, cx, cy, r_in, r_out, n, color, rot=0.0):
    p = skia.Path()
    for i in range(n * 2):
        a = math.pi * i / n + rot
        r = r_out if i % 2 == 0 else r_in
        x, y = cx + math.cos(a) * r, cy + math.sin(a) * r
        p.moveTo(x, y) if i == 0 else p.lineTo(x, y)
    p.close()
    c.drawPath(p, P(color))
    return p


def ad_card(fx: Frame, w: int, h: int, t: float, top="HARRIER FIGHTER", big="7,000,000", unit="POINTS",
            roll=None, big_scale=1.0):
    """90s infomercial price card drawn into the current canvas at (0,0,w,h)."""
    c = fx.c
    sh = skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(w, h)],
                                        [col("#3B1D78"), col("#1E6E8C"), col("#0F2A4A")], [0, 0.6, 1])
    c.drawRect(skia.Rect.MakeWH(w, h), skia.Paint(Shader=sh))
    for k in range(14):  # rotating light rays
        a = t * 0.4 + k * math.pi / 7
        p = skia.Path()
        p.moveTo(w / 2, h * 0.55)
        p.lineTo(w / 2 + math.cos(a) * w * 2, h * 0.55 + math.sin(a) * w * 2)
        p.lineTo(w / 2 + math.cos(a + 0.12) * w * 2, h * 0.55 + math.sin(a + 0.12) * w * 2)
        p.close()
        c.drawPath(p, skia.Paint(AntiAlias=True, Color=skia.Color(255, 255, 255, 18)))
    starburst(c, w * 0.5, h * 0.56, h * 0.33, h * 0.42, 18, col("#FFD23F"), rot=t * 0.3)
    starburst(c, w * 0.5, h * 0.56, h * 0.29, h * 0.36, 18, col("#FF5A36"), rot=-t * 0.25)
    fx.text(top, w / 2, h * 0.2, h * 0.13, "anton-400", "#FFFFFF", stroke=h * 0.012, stroke_col="#14082E",
            shadow=h * 0.01)
    txt = big if roll is None else roll
    c.save()
    c.translate(w / 2, h * 0.63)
    c.scale(big_scale, big_scale)
    fx.text(txt, 0, 0, h * 0.2 * (1.0 if len(txt) <= 9 else 9 / len(txt) * 1.08), "anton-400", "#FFFFFF",
            stroke=h * 0.016, stroke_col="#14082E", shadow=h * 0.012)
    c.restore()
    fx.text(unit, w / 2, h * 0.86, h * 0.1, "anton-400", "#FFD23F", stroke=h * 0.01, stroke_col="#14082E")


def crt(fx: Frame, rect: skia.Rect, content, t: float, power=1.0, bezel=True, glass=True):
    """Draw content(fx, w, h, t) into a CRT screen rect with scanlines, curvature shading and glow."""
    c = fx.c
    w, h = int(rect.width()), int(rect.height())
    rad = min(w, h) * 0.07
    if bezel:
        b = rect.makeOutset(w * 0.07, w * 0.07)
        bez = skia.RRect.MakeRectXY(b, rad * 2.2, rad * 2.2)
        sh = skia.GradientShader.MakeLinear([skia.Point(0, b.top()), skia.Point(0, b.bottom())],
                                            [col("#D9CDB4"), col("#B7A98C"), col("#8E8168")], [0, 0.6, 1])
        c.drawRRect(bez, skia.Paint(AntiAlias=True, Shader=sh))
        c.drawRRect(bez, P(col("#3a2e22"), w * 0.006))
        inner = skia.RRect.MakeRectXY(rect.makeOutset(w * 0.018, w * 0.018), rad * 1.3, rad * 1.3)
        c.drawRRect(inner, P(col("#2A2620")))
    scr = skia.RRect.MakeRectXY(rect, rad, rad)
    c.save()
    c.clipRRect(scr, doAntiAlias=True)
    c.save()
    c.translate(rect.left(), rect.top())
    content(fx, w, h, t)
    c.restore()
    # scanlines
    sl = skia.Paint(Color=skia.Color(0, 0, 0, 46))
    step = max(3, h // 180)
    for yy in range(int(rect.top()), int(rect.bottom()), step):
        c.drawRect(skia.Rect.MakeXYWH(rect.left(), yy, w, step * 0.45), sl)
    # flicker + curvature shading
    c.drawRect(rect, skia.Paint(Color=skia.Color(255, 255, 255, int(10 + 8 * math.sin(t * 50)))))
    shv = skia.GradientShader.MakeRadial(skia.Point(rect.centerX(), rect.centerY()), max(w, h) * 0.75,
                                         [skia.Color(0, 0, 0, 0), skia.Color(0, 0, 0, 150)], [0.55, 1.0])
    c.drawRect(rect, skia.Paint(Shader=shv))
    if glass:
        g = skia.Path()
        g.moveTo(rect.left(), rect.top())
        g.lineTo(rect.left() + w * 0.55, rect.top())
        g.lineTo(rect.left() + w * 0.25, rect.top() + h * 0.45)
        g.lineTo(rect.left(), rect.top() + h * 0.5)
        g.close()
        c.drawPath(g, skia.Paint(AntiAlias=True, Color=skia.Color(255, 255, 255, 22)))
    c.restore()


def chalk_text(fx: Frame, s: str, x: float, y: float, size: float, reveal: float, color="#F4F1E6", align="left",
               fnt="caveat-700", rot=0.0):
    """Chalk text revealed left->right (reveal 0..1) with a grainy, slightly broken stroke."""
    c = fx.c
    f = skia.Font(font(fnt), size)
    wdt = f.measureText(s)
    ox = {"left": 0, "center": -wdt / 2, "right": -wdt}[align]
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.clipRect(skia.Rect.MakeLTRB(ox - 10, -size * 1.2, ox + wdt * max(0.0, min(1.0, reveal)), size * 0.5))
    shader = _chalk_shader()
    paint = skia.Paint(AntiAlias=True, Color=col(color), Shader=shader)
    c.drawTextBlob(skia.TextBlob(s, f), ox, 0, paint)
    c.restore()
    return wdt


@lru_cache(None)
def _chalk_shader():
    rng = np.random.default_rng(3)
    n = rng.random((256, 256))
    a = (np.clip((n - 0.18) * 1.6, 0, 1) * 255).astype(np.uint8)
    rgba = np.dstack([np.full_like(a, 244), np.full_like(a, 241), np.full_like(a, 230), a])
    img = skia.Image.fromarray(rgba, colorType=skia.kRGBA_8888_ColorType)
    return img.makeShader(skia.TileMode.kRepeat, skia.TileMode.kRepeat, SAMP)


def chalk_arrow(fx: Frame, x0, y0, x1, y1, reveal, width=9):
    c = fx.c
    u = max(0.0, min(1.0, reveal))
    xe, ye = x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
    paint = skia.Paint(AntiAlias=True, Shader=_chalk_shader(), Style=skia.Paint.kStroke_Style, StrokeWidth=width,
                       StrokeCap=skia.Paint.kRound_Cap)
    c.drawLine(x0, y0, xe, ye, paint)
    if u > 0.95:
        a = math.atan2(y1 - y0, x1 - x0)
        for d in (2.5, -2.5):
            c.drawLine(x1, y1, x1 - math.cos(a + d / 6) * 40, y1 - math.sin(a + d / 6) * 40, paint)

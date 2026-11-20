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


# ================================================================================================ paper props
def paper_rect(fx, rect, color="#F6F1E3", rot=0.0, shadow=18, texture=True):
    """A sheet of paper with soft drop shadow and fibre texture; returns after translating/rotating into it."""
    c = fx.c
    c.save()
    c.translate(rect.centerX(), rect.centerY())
    c.rotate(rot)
    r = skia.Rect.MakeXYWH(-rect.width() / 2, -rect.height() / 2, rect.width(), rect.height())
    if shadow:
        c.drawRect(r.makeOffset(shadow * 0.4, shadow * 0.7),
                   skia.Paint(Color=skia.Color(0, 0, 0, 90), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, shadow)))
    c.drawRect(r, P(col(color)))
    if texture:
        c.drawRect(r, skia.Paint(Shader=_chalk_shader(), Alpha=18, BlendMode=skia.BlendMode.kMultiply))
    c.translate(r.left(), r.top())
    return r  # caller: c.restore() when done


def cheque(fx, rect, t, amount="$700,008.50", words="Seven hundred thousand eight and 50/100", write=1.0, rot=0.0,
           memo="1 HARRIER JET"):
    c = fx.c
    r = paper_rect(fx, rect, "#E9F1E4", rot)
    w, h = r.width(), r.height()
    for k in range(26):  # security guilloche
        p = skia.Path()
        for i in range(60):
            x = w * i / 59
            y = h * (0.05 + k * 0.035) + math.sin(i * 0.35 + k) * h * 0.012
            p.moveTo(x, y) if i == 0 else p.lineTo(x, y)
        c.drawPath(p, P(col("#9DBF9A", 70), h * 0.003))
    fx.text("FIRST CASCADE BANK", w * 0.05, h * 0.14, h * 0.07, "libre-baskerville-700", "#2F5B3A", align="left")
    fx.text("No. 1996", w * 0.95, h * 0.14, h * 0.06, "courier-prime-700", "#2F5B3A", align="right")
    fx.text("DATE  March 27, 1996", w * 0.95, h * 0.28, h * 0.06, "courier-prime-400", "#333333", align="right")
    fx.text("PAY TO THE", w * 0.05, h * 0.43, h * 0.05, "courier-prime-700", "#333333", align="left")
    fx.text("ORDER OF", w * 0.05, h * 0.5, h * 0.05, "courier-prime-700", "#333333", align="left")
    c.drawLine(w * 0.2, h * 0.52, w * 0.7, h * 0.52, P(col("#555555"), 2))
    box = skia.Rect.MakeLTRB(w * 0.73, h * 0.4, w * 0.96, h * 0.56)
    c.drawRect(box, P(col("#FFFFFF")))
    c.drawRect(box, P(col("#555555"), 2))
    c.drawLine(w * 0.05, h * 0.7, w * 0.85, h * 0.7, P(col("#555555"), 2))
    fx.text("DOLLARS", w * 0.95, h * 0.7, h * 0.045, "courier-prime-700", "#333333", align="right")
    c.drawLine(w * 0.05, h * 0.88, w * 0.45, h * 0.88, P(col("#555555"), 2))
    fx.text("MEMO", w * 0.05, h * 0.86, h * 0.04, "courier-prime-700", "#333333", align="left")
    c.drawLine(w * 0.55, h * 0.88, w * 0.95, h * 0.88, P(col("#555555"), 2))
    ink = "#1D2C7A"
    chalk_free = [("Pepsi-Cola Company", w * 0.22, h * 0.5, h * 0.09, 0.0, 0.25),
                  (amount, w * 0.745, h * 0.53, h * 0.085, 0.25, 0.5),
                  (words, w * 0.06, h * 0.68, h * 0.075, 0.5, 0.8),
                  (memo, w * 0.13, h * 0.86, h * 0.07, 0.8, 0.9),
                  ("J. Leonard", w * 0.6, h * 0.86, h * 0.1, 0.9, 1.0)]
    for txt, x, y, sz, a, b in chalk_free:
        u = (write - a) / (b - a)
        if u <= 0:
            continue
        f = skia.Font(font("caveat-700"), sz)
        tw_ = f.measureText(txt)
        c.save()
        c.clipRect(skia.Rect.MakeLTRB(x - 5, y - sz, x + tw_ * min(1.0, u), y + sz * 0.4))
        c.drawTextBlob(skia.TextBlob(txt, f), x, y, P(col(ink)))
        c.restore()
    c.restore()


def fine_print(fx, w, h, highlight=1.0):
    """Catalogue page: grey copy blocks + the key line (drawn in local coords 0..w,0..h)."""
    c = fx.c
    c.drawRect(skia.Rect.MakeWH(w, h), P(col("#FBF8EE")))
    fx.text("PEPSI STUFF CATALOG — OFFICIAL RULES", w * 0.06, h * 0.07, h * 0.035, "anton-400", "#1B2A6B", align="left")
    rng = np.random.default_rng(4)
    y = h * 0.13
    line_h = h * 0.026
    key_y = None
    for i in range(30):
        if i == 17:
            key_y = y
            y += line_h * 1.4
            continue
        lw = w * rng.uniform(0.55, 0.88)
        for j in range(int(lw / (w * 0.06))):
            ww = w * rng.uniform(0.02, 0.07)
            x0 = w * 0.06 + j * w * 0.075
            c.drawRoundRect(skia.Rect.MakeXYWH(x0, y - line_h * 0.55, ww, line_h * 0.45), 2, 2, P(col("#9C9A92")))
        y += line_h
    hl = skia.Rect.MakeXYWH(w * 0.05, key_y - line_h * 1.0, w * 0.9 * min(1, highlight), line_h * 1.3)
    c.drawRect(hl, P(col("#FFE94D", 200)))
    fx.text("Additional Pepsi Points may be purchased for 10¢ each.", w * 0.06, key_y, line_h * 0.95,
            "courier-prime-700", "#111111", align="left")


def magnifier(fx, cx, cy, rad, content, t):
    """POV through a magnifying glass: content(fx) drawn zoomed inside the lens, brass ring, glass glint."""
    c = fx.c
    lens = skia.Path()
    lens.addCircle(cx, cy, rad)
    c.save()
    c.clipPath(lens, doAntiAlias=True)
    content(fx)
    sh = skia.GradientShader.MakeRadial(skia.Point(cx, cy), rad, [skia.Color(0, 0, 0, 0), skia.Color(0, 0, 0, 120)], [0.7, 1])
    c.drawCircle(cx, cy, rad, skia.Paint(Shader=sh))
    c.drawArc(skia.Rect.MakeXYWH(cx - rad * 0.8, cy - rad * 0.8, rad * 1.6, rad * 1.6), 200, 50, False,
              P(skia.Color(255, 255, 255, 120), rad * 0.05))
    c.restore()
    sh = skia.GradientShader.MakeLinear([skia.Point(cx - rad, cy - rad), skia.Point(cx + rad, cy + rad)],
                                        [col("#F6D58A"), col("#9C6B22"), col("#F3CF7E"), col("#6B4515")], [0, 0.4, 0.6, 1])
    c.drawCircle(cx, cy, rad + rad * 0.045, skia.Paint(AntiAlias=True, Shader=sh, Style=skia.Paint.kStroke_Style,
                                                     StrokeWidth=rad * 0.09))
    hp = skia.Path()
    a = math.radians(55)
    hx, hy = cx + math.cos(a) * rad * 1.08, cy + math.sin(a) * rad * 1.08
    c.drawLine(hx, hy, hx + math.cos(a) * rad * 0.9, hy + math.sin(a) * rad * 0.9,
               skia.Paint(AntiAlias=True, Color=col("#3B2416"), StrokeWidth=rad * 0.16, Style=skia.Paint.kStroke_Style,
                          StrokeCap=skia.Paint.kRound_Cap))


def calculator(fx, cx, cy, s, display="0", t=0.0, press=None, glow=0.0):
    """Chunky 90s solar calculator, centred at (cx,cy), s = width in px."""
    c = fx.c
    w, h = s, s * 1.45
    r = skia.Rect.MakeXYWH(cx - w / 2, cy - h / 2, w, h)
    c.drawRoundRect(r.makeOffset(w * 0.03, w * 0.05), w * 0.08, w * 0.08,
                    skia.Paint(Color=skia.Color(0, 0, 0, 110), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, w * 0.04)))
    sh = skia.GradientShader.MakeLinear([skia.Point(0, r.top()), skia.Point(0, r.bottom())], [col("#4A4A52"), col("#26262C")])
    c.drawRoundRect(r, w * 0.08, w * 0.08, skia.Paint(AntiAlias=True, Shader=sh))
    c.drawRoundRect(r, w * 0.08, w * 0.08, P(INK, w * 0.012))
    c.drawRect(skia.Rect.MakeXYWH(r.left() + w * 0.55, r.top() + w * 0.06, w * 0.35, w * 0.08), P(col("#3B2A1E")))
    lcd = skia.Rect.MakeXYWH(r.left() + w * 0.08, r.top() + w * 0.2, w * 0.84, w * 0.3)
    c.drawRoundRect(lcd, w * 0.03, w * 0.03, P(col("#9DB08A")))
    if glow:
        fx.glow(lcd.centerX(), lcd.centerY(), w * 0.8, "#D8FFB0", 0.25 * glow)
    fx.text(display, lcd.right() - w * 0.05, lcd.bottom() - w * 0.07, w * 0.17, "courier-prime-700", "#1F2A18", align="right")
    keys_ = ["7", "8", "9", "/", "4", "5", "6", "×", "1", "2", "3", "-", "0", ".", "=", "+"]
    kw = w * 0.17
    for i, k in enumerate(keys_):
        kx = r.left() + w * 0.09 + (i % 4) * w * 0.215
        ky = r.top() + w * 0.62 + (i // 4) * w * 0.2
        down = press == k
        kr = skia.Rect.MakeXYWH(kx, ky + (w * 0.015 if down else 0), kw, kw * 0.78)
        if not down:
            c.drawRoundRect(kr.makeOffset(0, w * 0.018), w * 0.03, w * 0.03, P(col("#111114")))
        kc = "#E2603A" if k in "/×-+=" else "#DADAD2"
        c.drawRoundRect(kr, w * 0.03, w * 0.03, P(col(kc)))
        fx.text(k, kr.centerX(), kr.centerY() + kw * 0.17, kw * 0.45, "montserrat-800", "#222222")


def tag(fx, x, y, text, sub="", rot=0.0, w=420, color="#F2E6C8", ink="#1C1C1C", string_to=None):
    """Luggage-style price tag; (x,y) = hole position."""
    c = fx.c
    if string_to:
        c.drawLine(string_to[0], string_to[1], x, y, P(col("#6B5844"), 5))
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    h = w * 0.48
    p = skia.Path()
    p.moveTo(0, 0)
    p.lineTo(h * 0.42, -h / 2)
    p.lineTo(w, -h / 2)
    p.lineTo(w, h / 2)
    p.lineTo(h * 0.42, h / 2)
    p.close()
    c.drawPath(p.makeTransform(skia.Matrix.Translate(8, 14)) if hasattr(p, "makeTransform") else p,
               skia.Paint(Color=skia.Color(0, 0, 0, 90), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 12)))
    c.drawPath(p, P(col(color)))
    c.drawPath(p, P(INK, 6))
    c.drawCircle(h * 0.28, 0, h * 0.09, P(col("#3A2C20")))
    fx.text(text, w * 0.62, h * (0.12 if sub else 0.17), h * (0.36 if len(text) < 8 else 0.28), "anton-400", ink)
    if sub:
        fx.text(sub, w * 0.62, h * 0.38, h * 0.16, "montserrat-800", ink)
    c.restore()


def burst(fx, x, y, r, text="", fill="#FFD23F", stroke="#1A1410", t=0.0, n=14, text_col="#C8231B", rot=0.0):
    """Comic impact burst (BANG / KA-CHING)."""
    c = fx.c
    p = starburst(c, x, y, r * 0.7, r, n, col(fill), rot=rot + t * 0.5)
    c.drawPath(p, P(col(stroke), r * 0.05))
    if text:
        c.save()
        c.translate(x, y)
        c.rotate(-8)
        fx.text(text, 0, r * 0.14, r * 0.42, "anton-400", text_col, stroke=r * 0.05, stroke_col="#FFFFFF")
        c.restore()


def speed_lines(fx, cx, cy, t, n=40, inner=380, alpha=0.5, color="#FFFFFF"):
    c = fx.c
    rng = np.random.default_rng(int(t * 12))
    for i in range(n):
        a = rng.uniform(0, 2 * math.pi)
        r0 = inner * rng.uniform(0.9, 1.3)
        r1 = r0 + rng.uniform(200, 700)
        c.drawLine(cx + math.cos(a) * r0, cy + math.sin(a) * r0, cx + math.cos(a) * r1, cy + math.sin(a) * r1,
                   skia.Paint(AntiAlias=True, Color=col(color, int(255 * alpha)), StrokeWidth=rng.uniform(2, 7),
                              StrokeCap=skia.Paint.kRound_Cap))


def icon_bulb(fx, x, y, s, on=1.0):
    c = fx.c
    fx.glow(x, y, s * 2.2, "#FFF2A0", 0.55 * on)
    c.drawCircle(x, y, s * 0.55, P(col("#FFF4A8")))
    c.drawCircle(x, y, s * 0.55, P(INK, s * 0.07))
    c.drawRect(skia.Rect.MakeXYWH(x - s * 0.22, y + s * 0.5, s * 0.44, s * 0.3), P(col("#9A9AA0")))
    c.drawRect(skia.Rect.MakeXYWH(x - s * 0.22, y + s * 0.5, s * 0.44, s * 0.3), P(INK, s * 0.06))
    for k in range(8):
        a = k * math.pi / 4
        c.drawLine(x + math.cos(a) * s * 0.75, y + math.sin(a) * s * 0.75, x + math.cos(a) * s * 1.0,
                   y + math.sin(a) * s * 1.0, P(INK, s * 0.07))


def halo(fx, x, y, s, t):
    c = fx.c
    fx.glow(x, y, s * 2.0, "#FFF0B0", 0.4)
    c.drawOval(skia.Rect.MakeXYWH(x - s, y - s * 0.28 + math.sin(t * 3) * s * 0.05, 2 * s, s * 0.56),
               skia.Paint(AntiAlias=True, Color=col("#FFE46B"), Style=skia.Paint.kStroke_Style, StrokeWidth=s * 0.16))


def sweat(fx, x, y, s):
    c = fx.c
    p = skia.Path()
    p.moveTo(x, y - s)
    p.cubicTo(x + s * 0.7, y, x + s * 0.6, y + s * 0.8, x, y + s * 0.8)
    p.cubicTo(x - s * 0.6, y + s * 0.8, x - s * 0.7, y, x, y - s)
    c.drawPath(p, P(col("#8FD3FF")))
    c.drawPath(p, P(INK, s * 0.12))


def dollar_eyes(fx, x, y, s):
    """Overlay '$' eyes on a character face centred at (x,y) (head radius s)."""
    for dx in (-0.36, 0.36):
        fx.c.drawCircle(x + dx * s, y - 0.05 * s, 0.25 * s, P(col("#FFFFFF")))
        fx.text("$", x + dx * s, y + 0.12 * s, 0.44 * s, "anton-400", "#1E8E3E")


def progress_bar(fx, x, y, w, h, frac, label="JET PROGRESS", value="0.00004%"):
    c = fx.c
    fx.text(label, x, y - h * 0.4, h * 0.55, "anton-400", "#FFFFFF", align="left", stroke=6, stroke_col="#15100D")
    r = skia.Rect.MakeXYWH(x, y, w, h)
    c.drawRoundRect(r, h / 2, h / 2, P(col("#2A2A2E")))
    c.drawRoundRect(skia.Rect.MakeXYWH(x, y, max(h * 0.2, w * frac), h), h / 2, h / 2, P(col("#5BE36B")))
    c.drawRoundRect(r, h / 2, h / 2, P(col("#FFFFFF"), 5))
    fx.text(value, x + w, y - h * 0.4, h * 0.55, "anton-400", "#5BE36B", align="right", stroke=6, stroke_col="#15100D")


def ruling_card(fx, rect, reveal, t):
    """Parchment with the actual line from the 1999 opinion."""
    c = fx.c
    r = paper_rect(fx, rect, "#F1E5C6", -2)
    w, h = r.width(), r.height()
    fx.text("UNITED STATES DISTRICT COURT", w / 2, h * 0.1, h * 0.05, "libre-baskerville-700", "#3A2A18")
    fx.text("Leonard v. PepsiCo, Inc. — 1999", w / 2, h * 0.17, h * 0.04, "libre-baskerville-400", "#3A2A18")
    c.drawLine(w * 0.1, h * 0.21, w * 0.9, h * 0.21, P(col("#3A2A18"), 2))
    lines = ["“No objective person could", "reasonably have concluded", "that the commercial actually",
             "offered consumers a", "Harrier Jet.”"]
    for i, ln in enumerate(lines):
        u = reveal * len(lines) - i
        if u <= 0:
            break
        f = skia.Font(font("libre-baskerville-700"), h * 0.068)
        tw_ = f.measureText(ln)
        c.save()
        c.clipRect(skia.Rect.MakeLTRB(0, 0, w / 2 - tw_ / 2 + tw_ * min(1, u), h))
        fx.text(ln, w / 2, h * (0.34 + i * 0.105), h * 0.068, "libre-baskerville-700", "#1E150B")
        c.restore()
    if reveal > 0.98:
        a = min(1.0, (reveal - 0.98) * 50)
        c.save()
        c.translate(w * 0.73, h * 0.88)
        c.rotate(-14)
        c.drawRoundRect(skia.Rect.MakeXYWH(-w * 0.2, -h * 0.07, w * 0.4, h * 0.12), 10, 10, P(col("#B3261E", int(220 * a)), 8))
        fx.text("DENIED", 0, h * 0.025, h * 0.08, "anton-400", "#B3261E", alpha=a)
        c.restore()
    c.restore()


def inflation_chart(fx, w, h, u, t):
    """'Price of a jet' line chart that rockets off the top of the screen (local 0..w,0..h)."""
    c = fx.c
    c.drawRect(skia.Rect.MakeWH(w, h), P(col("#0E1B2E")))
    for k in range(1, 6):
        c.drawLine(0, h * k / 6, w, h * k / 6, P(col("#2A4566"), 2))
        c.drawLine(w * k / 6, 0, w * k / 6, h, P(col("#2A4566"), 2))
    fx.text("PRICE OF ONE (1) JET, IN POINTS", w / 2, h * 0.1, h * 0.06, "anton-400", "#9CC7FF")
    p = skia.Path()
    n = 40
    for i in range(n + 1):
        x = w * 0.08 + w * 0.84 * i / n
        k = i / n
        yv = h * 0.82 - (h * 0.06 * k if k < 0.6 else h * 0.036 + (k - 0.6) ** 3 * h * 45)
        if k > u:
            break
        p.moveTo(x, yv) if i == 0 else p.lineTo(x, yv)
    c.drawPath(p, skia.Paint(AntiAlias=True, Color=col("#FF4D4D"), StrokeWidth=h * 0.018, Style=skia.Paint.kStroke_Style,
                             StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join))
    fx.text("7M", w * 0.12, h * 0.9, h * 0.06, "anton-400", "#FFFFFF")
    if u > 0.85:
        fx.text("+9,900%", w * 0.62, h * 0.45, h * 0.14 * (1 + 0.05 * math.sin(t * 20)), "anton-400", "#FF4D4D",
                stroke=h * 0.012, stroke_col="#FFFFFF")

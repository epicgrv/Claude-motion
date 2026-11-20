"""Original 2D cast drawn with skia, in the genre of the reference: big white round heads, single-line stick limbs with
ball hands, flat costume shapes, one thick dark outline weight for everything.

Local space: feet on y=0, up is negative y, unit = head radius r (pixels = r * scale passed to draw()).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import skia

INK = skia.Color(43, 27, 23)
SKIN = skia.Color(250, 249, 245)
OUT = 0.1  # outline width in r units
LIMB = 0.17  # limb stroke width in r units


def col(h: str, a: int = 255) -> int:
    h = h.lstrip("#")
    return skia.Color(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def P(color, stroke=None, cap=skia.Paint.kRound_Cap, join=skia.Paint.kRound_Join, aa=True):
    p = skia.Paint(AntiAlias=aa, Color=color)
    if stroke is not None:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeCap(cap)
        p.setStrokeJoin(join)
    return p


_FAB = None


def fabric_shader():
    """Fine woven-noise texture in local (head-radius) units."""
    global _FAB
    if _FAB is None:
        import numpy as np
        rng = np.random.default_rng(11)
        n = rng.random((128, 128))
        weave = (np.sin(np.arange(128) * 1.6)[None, :] * np.sin(np.arange(128) * 1.6)[:, None]) * 0.25
        a = np.clip((n * 0.7 + weave + 0.15) * 255, 0, 255).astype(np.uint8)
        rgba = np.dstack([a, a, a, np.full_like(a, 255)])
        img = skia.Image.fromarray(rgba, colorType=skia.kRGBA_8888_ColorType)
        _FAB = img.makeShader(skia.TileMode.kRepeat, skia.TileMode.kRepeat,
                              skia.SamplingOptions(skia.FilterMode.kLinear), skia.Matrix.Scale(0.012, 0.012))
    return _FAB


def shade_volume(c: skia.Canvas, path: skia.Path, bounds: skia.Rect, strength=0.32, fabric=True):
    """Soft 3-D form on a flat shape: top-left key highlight, bottom-right core shadow, fabric grain."""
    c.save()
    c.clipPath(path, doAntiAlias=True)
    cx, cy = bounds.centerX(), bounds.centerY()
    rad = max(bounds.width(), bounds.height()) * 0.75
    sh = skia.GradientShader.MakeRadial(skia.Point(cx - bounds.width() * 0.28, cy - bounds.height() * 0.3), rad,
                                        [skia.Color(255, 255, 255, 70), skia.Color(255, 255, 255, 0),
                                         skia.Color(30, 15, 40, int(255 * strength))], [0.0, 0.45, 1.0])
    c.drawRect(bounds.makeOutset(0.2, 0.2), skia.Paint(Shader=sh, AntiAlias=True))
    if fabric:
        c.drawRect(bounds, skia.Paint(Shader=fabric_shader(), Alpha=34, BlendMode=skia.BlendMode.kOverlay))
    # rim light on the shadow side edge
    rim = skia.Paint(AntiAlias=True, Color=skia.Color(255, 240, 220, 70), Style=skia.Paint.kStroke_Style,
                     StrokeWidth=0.09, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 0.03))
    c.save()
    c.clipRect(skia.Rect.MakeLTRB(cx + bounds.width() * 0.15, bounds.top(), bounds.right() + 1, bounds.bottom() + 1))
    c.drawPath(path, rim)
    c.restore()
    c.restore()


def fill_outline(c: skia.Canvas, path: skia.Path, color, ow=OUT, volume=True):
    c.drawPath(path, P(color))
    if volume:
        shade_volume(c, path, path.computeTightBounds(), 0.3, fabric=False)
    c.drawPath(path, P(INK, ow))


# --------------------------------------------------------------------------------------------- poses
# angles in degrees, 0 = straight down, positive = towards the character's facing side (forward)
POSES = {
    "stand":      dict(ls=(-12, 0), rs=(12, 0), ll=(-6, 0), rl=(6, 0)),
    "relaxed":    dict(ls=(-18, 10), rs=(16, -8), ll=(-7, 0), rl=(7, 0)),
    "hips":       dict(ls=(-55, -110), rs=(55, 110), ll=(-8, 0), rl=(8, 0)),
    "point":      dict(ls=(-14, 0), rs=(100, 0), ll=(-7, 0), rl=(7, 0)),
    "point_up":   dict(ls=(-14, 0), rs=(150, 10), ll=(-7, 0), rl=(7, 0)),
    "raise_hand": dict(ls=(-14, 0), rs=(170, -5), ll=(-7, 0), rl=(7, 0)),
    "arms_up":    dict(ls=(-150, 10), rs=(150, -10), ll=(-12, 0), rl=(12, 0)),
    "shrug":      dict(ls=(-55, 100), rs=(55, -100), ll=(-6, 0), rl=(6, 0)),
    "hold":       dict(ls=(-14, 0), rs=(55, 50), ll=(-6, 0), rl=(6, 0)),
    "hold2":      dict(ls=(-45, -60), rs=(45, 60), ll=(-6, 0), rl=(6, 0)),
    "present":    dict(ls=(-14, 0), rs=(75, -25), ll=(-7, 0), rl=(7, 0)),
    "slump":      dict(ls=(-6, 0), rs=(6, 0), ll=(-4, 0), rl=(4, 0), lean=8, drop=0.15),
    "kick":       dict(ls=(-50, -110), rs=(55, 110), ll=(-6, 0), rl=(70, -90), lean=-6),
    "walk_a":     dict(ls=(25, 10), rs=(-25, 10), ll=(-22, 15), rl=(22, 0)),
    "walk_b":     dict(ls=(-25, 10), rs=(25, 10), ll=(22, 0), rl=(-22, 15)),
    "sit":        dict(ls=(-20, 30), rs=(25, 45), ll=(80, -85), rl=(85, -80), sit=True),
    "sit_hold":   dict(ls=(-35, -60), rs=(40, 60), ll=(80, -85), rl=(85, -80), sit=True),
    "jaw_drop":   dict(ls=(-25, 15), rs=(25, -15), ll=(-8, 0), rl=(8, 0)),
    "facepalm":   dict(ls=(-14, 0), rs=(150, 120), ll=(-6, 0), rl=(6, 0)),
}


def lerp_pose(a: dict, b: dict, t: float) -> dict:
    out = {}
    for k in set(a) | set(b):
        va, vb = a.get(k, b.get(k)), b.get(k, a.get(k))
        if isinstance(va, tuple):
            out[k] = tuple(x + (y - x) * t for x, y in zip(va, vb))
        elif isinstance(va, bool):
            out[k] = vb if t > 0.5 else va
        else:
            out[k] = va + (vb - va) * t
    return out


# --------------------------------------------------------------------------------------------- costume
@dataclass
class Costume:
    torso: str = "#3a7bd5"
    torso2: str | None = None      # stripe / lapel / secondary colour
    style: str = "tee"             # tee | windbreaker | suit | vest | robe | flight | uniform
    hair: str | None = None        # messy | shaggy | slick | bun | none
    hair_col: str = "#5a3a22"
    hat: str | None = None         # cap_back | helmet | none
    hat_col: str = "#c8332d"
    beard: bool = False
    glasses: str | None = None     # nerd | half | aviator | shades_on_head
    tie: str | None = None
    width: float = 1.0             # torso width multiplier
    height: float = 1.0            # torso height multiplier
    legs: float = 1.0


CAST = {
    "JOHN": Costume(torso="#E8B33A", torso2="#6B3FA0", style="windbreaker", hair="messy", hair_col="#6b4226",
                    hat="cap_back", hat_col="#D23B32"),
    "BUDDY": Costume(torso="#9BD13B", torso2="#6E9A24", style="tee", hair="shaggy", hair_col="#F2DC8A", width=1.08),
    "INVESTOR": Costume(torso="#E8742A", torso2="#7A8590", style="vest", hair="slick", hair_col="#3b2a20", beard=True,
                        glasses="shades_on_head", width=1.12),
    "EXEC": Costume(torso="#1F2E5A", torso2="#F4F4F0", style="suit", hair="slick", hair_col="#111111", tie="#2F6FD6",
                    width=1.05),
    "TEEN": Costume(torso="#5E6B4E", torso2="#3E4733", style="flight", hat="helmet", hat_col="#F0F0EC",
                    glasses="aviator"),
    "JUDGE": Costume(torso="#141414", torso2="#F4F4F0", style="robe", hair="bun", hair_col="#B9B9B9", glasses="half",
                     height=1.15),
    "DRIVER": Costume(torso="#5B7FA8", torso2="#3E5878", style="uniform", hair="slick", hair_col="#8b8b8b",
                      hat="cap_front", hat_col="#2E4A6B", beard=False),
    "SHADOW": Costume(torso="#3a3a44", style="tee", hair="slick", hair_col="#2a2a30"),
}


# --------------------------------------------------------------------------------------------- character
@dataclass
class Char:
    name: str
    costume: Costume = field(default=None)

    def __post_init__(self):
        if self.costume is None:
            self.costume = CAST[self.name]

    def draw(self, c: skia.Canvas, x: float, y: float, r: float, pose="stand", expr="neutral", mouth=0.0,
             face=1, look=(0.0, 0.0), blink=False, head_tilt=0.0, bob=0.0, prop=None, prop_t=0.0,
             nerd_glasses=False, squash=1.0):
        """x,y = point between the feet on the ground (pixels). r = head radius in pixels."""
        if isinstance(pose, str):
            pose = POSES[pose]
        cs = self.costume
        c.save()
        c.translate(x, y)
        c.scale(r * face, r * squash)  # face=-1 mirrors
        lean = pose.get("lean", 0)
        sit = pose.get("sit", False)
        drop = pose.get("drop", 0.0)
        legL = 1.55 * cs.legs
        hipy = -legL + (0.75 if sit else 0) + drop + bob
        th = 1.35 * cs.height
        tw = 0.62 * cs.width
        neck = hipy - th
        c.save()
        c.rotate(lean, 0, hipy)
        # ---- legs (behind torso)
        for side, key in ((-1, "ll"), (1, "rl")):
            a1, a2 = pose[key]
            hx = side * 0.24 * cs.width
            self._limb(c, (hx, hipy), a1, a2, legL * 0.52, legL * 0.5, foot=True, side=side)
        # ---- back arm
        sy = neck + 0.32
        self._arm(c, -1, pose["ls"], tw, sy, prop if prop and prop.get("hand") == "l" else None, prop_t)
        # ---- torso
        self._torso(c, tw, th, hipy, neck)
        # ---- head
        hx, hy = 0.0, neck - 0.78
        c.save()
        c.rotate(head_tilt, 0, neck)
        self._head(c, hx, hy, expr, mouth, look, blink, nerd_glasses)
        c.restore()
        # ---- front arm (over torso)
        self._arm(c, 1, pose["rs"], tw, sy, prop if prop and prop.get("hand", "r") == "r" else None, prop_t)
        c.restore()
        c.restore()

    # -- parts
    def _limb(self, c, start, a1, a2, l1, l2, foot=False, side=1):
        x0, y0 = start
        r1 = math.radians(a1)
        x1, y1 = x0 + math.sin(r1) * l1, y0 + math.cos(r1) * l1
        r2 = math.radians(a1 + a2)
        x2, y2 = x1 + math.sin(r2) * l2, y1 + math.cos(r2) * l2
        path = skia.Path()
        path.moveTo(x0, y0)
        path.lineTo(x1, y1)
        path.lineTo(x2, y2)
        c.drawPath(path, P(INK, LIMB))
        if foot:
            c.drawOval(skia.Rect.MakeXYWH(x2 - 0.05, y2 - 0.07, 0.24, 0.12), P(INK))
        return x2, y2

    def _arm(self, c, side, ang, tw, sy, prop, prop_t):
        a1, a2 = ang
        sx = side * (tw * 0.92)
        # convert: side -1 arm swings with negative angles to the back side
        hx, hy = self._limb(c, (sx, sy), a1, a2, 0.82, 0.78)
        if prop:
            self._prop(c, prop, hx, hy, prop_t)
        c.drawCircle(hx, hy, 0.13, P(INK))

    def _torso(self, c, tw, th, hipy, neck):
        cs = self.costume
        rect = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-tw, neck, tw, hipy + 0.12), tw * 0.85, tw * 0.75)
        path = skia.Path()
        path.addRRect(rect)
        c.drawPath(path, P(col(cs.torso)))
        c.save()
        c.clipPath(path, doAntiAlias=True)
        if cs.torso2:
            t2 = col(cs.torso2)
        else:
            h_ = cs.torso.lstrip("#")
            t2 = skia.Color(*(int(int(h_[i:i + 2], 16) * 0.6) for i in (0, 2, 4)))
        if cs.style == "windbreaker":
            c.drawRect(skia.Rect.MakeLTRB(-tw, neck + th * 0.42, tw, neck + th * 0.56), P(t2))
            c.drawLine(0, neck + 0.1, 0, hipy + 0.1, P(INK, 0.04))
            c.drawRect(skia.Rect.MakeLTRB(-tw, hipy - 0.08, tw, hipy + 0.2), P(col("#B98A22")))
            p = skia.Path(); p.moveTo(-0.28, neck); p.lineTo(0, neck + 0.28); p.lineTo(0.28, neck); p.close()
            c.drawPath(p, P(col("#C9952B")))
        elif cs.style == "tee":
            c.drawRect(skia.Rect.MakeLTRB(-tw, hipy - 0.05, tw, hipy + 0.2), P(t2 or col("#555555")))
            c.drawArc(skia.Rect.MakeLTRB(-0.25, neck - 0.18, 0.25, neck + 0.2), 0, 180, False, P(INK, 0.04))
        elif cs.style == "vest":
            c.drawRect(skia.Rect.MakeLTRB(-0.2, neck, 0.2, hipy + 0.2), P(t2))
            for k in range(1, 5):
                yy = neck + th * k / 5
                c.drawLine(-tw, yy, -0.2, yy, P(col("#B5541A"), 0.035))
                c.drawLine(0.2, yy, tw, yy, P(col("#B5541A"), 0.035))
            c.drawLine(-0.2, neck, -0.2, hipy + 0.2, P(INK, 0.035))
            c.drawLine(0.2, neck, 0.2, hipy + 0.2, P(INK, 0.035))
        elif cs.style == "suit":
            p = skia.Path(); p.moveTo(-0.24, neck); p.lineTo(0, neck + th * 0.55); p.lineTo(0.24, neck); p.close()
            c.drawPath(p, P(t2))
            if cs.tie:
                t = skia.Path(); t.moveTo(-0.07, neck + 0.05); t.lineTo(0.07, neck + 0.05); t.lineTo(0.1, neck + th * 0.5)
                t.lineTo(0, neck + th * 0.6); t.lineTo(-0.1, neck + th * 0.5); t.close()
                c.drawPath(t, P(col(cs.tie)))
            c.drawLine(-0.24, neck, 0, neck + th * 0.62, P(INK, 0.04))
            c.drawLine(0.24, neck, 0, neck + th * 0.62, P(INK, 0.04))
            for k in range(2):
                c.drawCircle(0.0, neck + th * (0.72 + 0.14 * k), 0.045, P(INK))
        elif cs.style == "robe":
            c.drawRect(skia.Rect.MakeLTRB(-0.12, neck, 0.12, neck + 0.22), P(t2))
            for xx in (-0.35, 0.0, 0.35):
                c.drawLine(xx, neck + 0.35, xx * 1.2, hipy + 0.2, P(col("#2a2a2a"), 0.035))
        elif cs.style == "flight":
            c.drawLine(0, neck + 0.05, 0, hipy + 0.1, P(INK, 0.04))
            c.drawRect(skia.Rect.MakeLTRB(0.15, neck + 0.35, 0.45, neck + 0.55), P(t2))
            c.drawCircle(-0.35, neck + 0.4, 0.09, P(col("#C8332D")))
        elif cs.style == "uniform":
            c.drawLine(0, neck + 0.05, 0, hipy + 0.1, P(INK, 0.04))
            for k in range(3):
                c.drawCircle(0.0, neck + 0.3 + 0.32 * k, 0.04, P(col("#E8C64A")))
            c.drawRect(skia.Rect.MakeLTRB(0.2, neck + 0.3, 0.45, neck + 0.42), P(t2))
        c.restore()
        shade_volume(c, path, rect.rect(), 0.38)
        c.drawPath(path, P(INK, OUT))

    def _head(self, c, hx, hy, expr, mouth, look, blink, nerd):
        cs = self.costume
        R = 1.0
        lx, ly = look[0] * 0.18, look[1] * 0.12
        # hair behind head
        if cs.hair == "shaggy":
            p = skia.Path()
            pts = [(-1.05, 0.15), (-1.15, -0.4), (-0.9, -0.95), (-0.45, -1.2), (0.1, -1.25), (0.6, -1.1), (1.0, -0.75),
                   (1.15, -0.2), (1.05, 0.2)]
            p.moveTo(*[pts[0][0] + hx, pts[0][1] + hy])
            for (ax, ay) in pts[1:]:
                p.lineTo(ax + hx, ay + hy)
            p.close()
            fill_outline(c, p, col(cs.hair_col))
        if cs.hair == "bun":
            c.drawCircle(hx, hy - 1.05, 0.38, P(col(cs.hair_col)))
            c.drawCircle(hx, hy - 1.05, 0.38, P(INK, OUT))
        # head
        c.drawCircle(hx, hy, R, P(SKIN))
        hp = skia.Path()
        hp.addCircle(hx, hy, R)
        shade_volume(c, hp, skia.Rect.MakeLTRB(hx - R, hy - R, hx + R, hy + R), 0.2, fabric=False)
        c.drawCircle(hx, hy, R, P(INK, OUT))
        # hair on top
        if cs.hair == "messy":
            p = skia.Path()
            p.moveTo(hx - 0.95, hy - 0.3)
            p.cubicTo(hx - 0.9, hy - 1.1, hx + 0.9, hy - 1.25, hx + 0.97, hy - 0.25)
            for k, (ax, ay) in enumerate([(0.75, -0.45), (0.55, -0.25), (0.35, -0.5), (0.1, -0.3), (-0.15, -0.55),
                                          (-0.4, -0.35), (-0.65, -0.55)]):
                p.lineTo(hx + ax, hy + ay)
            p.close()
            fill_outline(c, p, col(cs.hair_col))
        elif cs.hair == "shaggy":
            p = skia.Path()
            p.moveTo(hx - 0.98, hy - 0.2)
            p.cubicTo(hx - 0.95, hy - 1.15, hx + 0.95, hy - 1.15, hx + 0.98, hy - 0.2)
            for (ax, ay) in [(0.8, -0.05), (0.62, -0.42), (0.38, -0.12), (0.12, -0.48), (-0.15, -0.1), (-0.42, -0.45),
                             (-0.65, -0.08), (-0.82, -0.4)]:
                p.lineTo(hx + ax, hy + ay)
            p.close()
            fill_outline(c, p, col(cs.hair_col))
        elif cs.hair == "slick":
            p = skia.Path()
            p.moveTo(hx - 0.97, hy - 0.15)
            p.cubicTo(hx - 1.0, hy - 1.15, hx + 1.0, hy - 1.15, hx + 0.97, hy - 0.15)
            p.cubicTo(hx + 0.7, hy - 0.6, hx - 0.2, hy - 0.75, hx - 0.97, hy - 0.15)
            p.close()
            fill_outline(c, p, col(cs.hair_col))
        elif cs.hair == "bun":
            p = skia.Path()
            p.moveTo(hx - 0.97, hy - 0.05)
            p.cubicTo(hx - 1.0, hy - 1.15, hx + 1.0, hy - 1.15, hx + 0.97, hy - 0.05)
            p.cubicTo(hx + 0.6, hy - 0.65, hx - 0.6, hy - 0.65, hx - 0.97, hy - 0.05)
            fill_outline(c, p, col(cs.hair_col))
        # beard
        if cs.beard:
            p = skia.Path()
            p.moveTo(hx - 0.92, hy + 0.15)
            p.cubicTo(hx - 0.8, hy + 1.25, hx + 0.8, hy + 1.25, hx + 0.92, hy + 0.15)
            p.cubicTo(hx + 0.5, hy + 0.55, hx - 0.5, hy + 0.55, hx - 0.92, hy + 0.15)
            fill_outline(c, p, col(cs.hair_col))
        # face
        self._face(c, hx + lx, hy + ly, expr, mouth, blink, cs.beard)
        # glasses
        g = "nerd" if nerd else cs.glasses
        if g == "nerd":
            for sx in (-0.36, 0.36):
                c.drawCircle(hx + lx + sx, hy + ly - 0.05, 0.27, P(INK, 0.07))
            c.drawLine(hx + lx - 0.09, hy + ly - 0.05, hx + lx + 0.09, hy + ly - 0.05, P(INK, 0.06))
        elif g == "half":
            for sx in (-0.36, 0.36):
                c.drawArc(skia.Rect.MakeXYWH(hx + lx + sx - 0.24, hy + ly - 0.12, 0.48, 0.34), 0, 180, False, P(INK, 0.06))
        elif g == "aviator":
            for sx in (-0.38, 0.38):
                p = skia.Path()
                p.addOval(skia.Rect.MakeXYWH(hx + lx + sx - 0.3, hy + ly - 0.25, 0.6, 0.46))
                fill_outline(c, p, col("#2B2F38"), 0.05)
                c.drawLine(hx + lx + sx - 0.12, hy + ly - 0.14, hx + lx + sx + 0.05, hy + ly - 0.18, P(col("#9BB8D8"), 0.05))
            c.drawLine(hx + lx - 0.08, hy + ly - 0.15, hx + lx + 0.08, hy + ly - 0.15, P(INK, 0.05))
        elif g == "shades_on_head":
            for sx in (-0.33, 0.33):
                p = skia.Path()
                p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(hx + sx - 0.26, hy - 0.98, 0.52, 0.26), 0.1, 0.1))
                fill_outline(c, p, col("#1E1E22"), 0.05)
        # hats
        if cs.hat == "cap_back":
            p = skia.Path()
            p.moveTo(hx - 0.92, hy - 0.42)
            p.cubicTo(hx - 0.85, hy - 1.28, hx + 0.85, hy - 1.28, hx + 0.92, hy - 0.42)
            p.close()
            fill_outline(c, p, col(cs.hat_col))
            b = skia.Path()  # brim pointing backwards
            b.moveTo(hx - 0.85, hy - 0.5)
            b.cubicTo(hx - 1.35, hy - 0.55, hx - 1.45, hy - 0.35, hx - 1.3, hy - 0.28)
            b.lineTo(hx - 0.88, hy - 0.36)
            b.close()
            fill_outline(c, b, col(cs.hat_col))
            c.drawCircle(hx, hy - 1.07, 0.07, P(INK))
        elif cs.hat == "cap_front":
            p = skia.Path()
            p.moveTo(hx - 0.92, hy - 0.42)
            p.cubicTo(hx - 0.85, hy - 1.28, hx + 0.85, hy - 1.28, hx + 0.92, hy - 0.42)
            p.close()
            fill_outline(c, p, col(cs.hat_col))
            b = skia.Path()
            b.moveTo(hx + 0.3, hy - 0.5); b.cubicTo(hx + 1.2, hy - 0.55, hx + 1.45, hy - 0.4, hx + 1.35, hy - 0.3)
            b.lineTo(hx + 0.2, hy - 0.38); b.close()
            fill_outline(c, b, col("#1d3047"))
            c.drawCircle(hx + 0.1, hy - 0.8, 0.12, P(col("#E8C64A")))
        elif cs.hat == "helmet":
            p = skia.Path()
            p.moveTo(hx - 1.08, hy - 0.05)
            p.cubicTo(hx - 1.15, hy - 1.45, hx + 1.15, hy - 1.45, hx + 1.08, hy - 0.05)
            p.lineTo(hx + 0.85, hy - 0.05)
            p.cubicTo(hx + 0.8, hy - 0.55, hx - 0.8, hy - 0.55, hx - 0.85, hy - 0.05)
            p.close()
            fill_outline(c, p, col(cs.hat_col))
            c.drawRect(skia.Rect.MakeXYWH(hx - 0.12, hy - 1.3, 0.24, 0.5), P(col("#C8332D")))

    def _face(self, c, fx, fy, expr, mouth, blink, beard):
        ink = P(INK)
        line = P(INK, 0.075)
        ey = fy - 0.05
        ex = 0.36
        e = expr
        # ---- eyes
        if blink and e not in ("happy", "laugh"):
            for sx in (-ex, ex):
                c.drawLine(fx + sx - 0.12, ey, fx + sx + 0.12, ey, line)
        elif e in ("happy", "laugh"):
            for sx in (-ex, ex):
                c.drawArc(skia.Rect.MakeXYWH(fx + sx - 0.15, ey - 0.08, 0.3, 0.26), 180, 180, False, line)
        elif e in ("wide", "shock", "jaw"):
            for sx in (-ex, ex):
                c.drawCircle(fx + sx, ey, 0.21, P(SKIN))
                c.drawCircle(fx + sx, ey, 0.21, P(INK, 0.06))
                c.drawCircle(fx + sx, ey, 0.075, ink)
        elif e in ("squint", "suspicious"):
            for sx in (-ex, ex):
                c.drawLine(fx + sx - 0.14, ey + 0.02, fx + sx + 0.14, ey - 0.02, line)
        elif e in ("dead", "smug", "deadpan"):
            for sx in (-ex, ex):
                c.drawArc(skia.Rect.MakeXYWH(fx + sx - 0.14, ey - 0.06, 0.28, 0.24), 0, 180, True, ink)
                c.drawLine(fx + sx - 0.16, ey + 0.05, fx + sx + 0.16, ey + 0.05, P(INK, 0.06))
        else:
            for sx in (-ex, ex):
                c.drawOval(skia.Rect.MakeXYWH(fx + sx - 0.085, ey - 0.11, 0.17, 0.22), ink)
        # ---- brows
        bw = 0.06
        if e in ("angry", "suspicious", "squint"):
            c.drawLine(fx - 0.5, ey - 0.32, fx - 0.2, ey - 0.22, P(INK, bw))
            c.drawLine(fx + 0.5, ey - 0.32, fx + 0.2, ey - 0.22, P(INK, bw))
        elif e in ("wide", "shock", "jaw"):
            c.drawLine(fx - 0.5, ey - 0.42, fx - 0.22, ey - 0.47, P(INK, bw))
            c.drawLine(fx + 0.5, ey - 0.42, fx + 0.22, ey - 0.47, P(INK, bw))
        elif e in ("smug", "deadpan", "dead"):
            c.drawLine(fx - 0.5, ey - 0.25, fx - 0.2, ey - 0.27, P(INK, bw))
            c.drawLine(fx + 0.5, ey - 0.33, fx + 0.2, ey - 0.3, P(INK, bw))
        elif e in ("sad",):
            c.drawLine(fx - 0.5, ey - 0.25, fx - 0.2, ey - 0.35, P(INK, bw))
            c.drawLine(fx + 0.5, ey - 0.25, fx + 0.2, ey - 0.35, P(INK, bw))
        # ---- mouth
        my = fy + 0.42
        m = max(0.0, min(1.0, mouth))
        if e == "laugh":
            m = max(m, 0.75)
        if e in ("jaw",):
            p = skia.Path(); p.addOval(skia.Rect.MakeXYWH(fx - 0.26, my - 0.12, 0.52, 0.85))
            fill_outline(c, p, col("#5A1E1E"), 0.06)
            c.drawOval(skia.Rect.MakeXYWH(fx - 0.17, my + 0.4, 0.34, 0.25), P(col("#E06A6A")))
            return
        if m > 0.08:
            w = 0.34 if e not in ("grin", "happy", "laugh") else 0.46
            h = 0.08 + 0.42 * m
            p = skia.Path()
            if e in ("grin", "happy", "laugh"):
                p.moveTo(fx - w, my - 0.04)
                p.cubicTo(fx - w * 0.6, my + h * 1.4, fx + w * 0.6, my + h * 1.4, fx + w, my - 0.04)
                p.close()
            else:
                p.addOval(skia.Rect.MakeXYWH(fx - w * 0.75, my - h * 0.4, w * 1.5, h))
            c.save()
            c.drawPath(p, P(col("#5A1E1E")))
            c.clipPath(p, doAntiAlias=True)
            c.drawRect(skia.Rect.MakeXYWH(fx - w, my - h, 2 * w, h * 0.55 + 0.02), P(SKIN))  # teeth
            c.drawOval(skia.Rect.MakeXYWH(fx - w * 0.5, my + h * 0.35, w, h * 0.7), P(col("#E06A6A")))
            c.restore()
            c.drawPath(p, P(INK, 0.06))
        else:
            if e in ("grin", "happy"):
                c.drawArc(skia.Rect.MakeXYWH(fx - 0.3, my - 0.22, 0.6, 0.35), 15, 150, False, line)
            elif e == "smug":
                p = skia.Path(); p.moveTo(fx - 0.22, my + 0.02); p.quadTo(fx + 0.05, my + 0.06, fx + 0.25, my - 0.08)
                c.drawPath(p, line)
            elif e in ("sad", "dead"):
                c.drawArc(skia.Rect.MakeXYWH(fx - 0.2, my, 0.4, 0.25), 200, 140, False, line)
            elif e in ("shock", "wide"):
                c.drawOval(skia.Rect.MakeXYWH(fx - 0.09, my - 0.05, 0.18, 0.22), P(INK, 0.06))
            else:
                c.drawLine(fx - 0.16, my, fx + 0.16, my, line)

    # -- props held in hand
    def _prop(self, c, prop, hx, hy, t):
        k = prop["kind"]
        if k == "bowl":
            c.drawPath(_bowl(hx, hy), P(col("#E9E4D6")))
            c.drawPath(_bowl(hx, hy), P(INK, 0.06))
            for i in range(6):
                c.drawCircle(hx - 0.3 + i * 0.12, hy - 0.17 + (i % 2) * 0.04, 0.07, P(col("#E3A33B")))
        elif k == "spoon":
            c.drawLine(hx, hy, hx + 0.1, hy - 0.6, P(col("#BFC4CA"), 0.07))
            c.drawOval(skia.Rect.MakeXYWH(hx + 0.02, hy - 0.8, 0.18, 0.26), P(col("#BFC4CA")))
        elif k == "envelope":
            r = skia.Rect.MakeXYWH(hx - 0.1, hy - 0.45, 0.9, 0.58)
            c.drawRect(r, P(col("#F3EBD9"))); c.drawRect(r, P(INK, 0.05))
            p = skia.Path(); p.moveTo(r.left(), r.top()); p.lineTo(r.centerX(), r.centerY()); p.lineTo(r.right(), r.top())
            c.drawPath(p, P(INK, 0.04))
        elif k == "coupon":
            r = skia.Rect.MakeXYWH(hx - 0.2, hy - 0.75, 1.0, 0.5)
            c.drawRect(r, P(col("#FFF4C7"))); c.drawRect(r, P(INK, 0.04))
            ins = skia.Rect.MakeXYWH(r.left() + 0.05, r.top() + 0.05, r.width() - 0.1, r.height() - 0.1)
            dash = skia.Paint(AntiAlias=True, Color=col("#B23A2E"), Style=skia.Paint.kStroke_Style, StrokeWidth=0.025,
                              PathEffect=skia.DashPathEffect.Make([0.06, 0.04], 0))
            c.drawRect(ins, dash)
        elif k == "pointer":
            c.drawLine(hx, hy, hx + 0.9, hy - 1.3, P(col("#8A5A2B"), 0.07))
        elif k == "calculator":
            r = skia.Rect.MakeXYWH(hx - 0.35, hy - 0.8, 0.7, 1.0)
            c.drawRoundRect(r, 0.08, 0.08, P(col("#3B3B40"))); c.drawRoundRect(r, 0.08, 0.08, P(INK, 0.05))
            c.drawRect(skia.Rect.MakeXYWH(hx - 0.27, hy - 0.72, 0.54, 0.22), P(col("#A9B89A")))
        elif k == "napkin":
            r = skia.Rect.MakeXYWH(hx - 0.1, hy - 0.6, 0.8, 0.8)
            c.drawRect(r, P(col("#FAFAFA"))); c.drawRect(r, P(INK, 0.04))
            pth = skia.Path(); pth.moveTo(hx + 0.05, hy + 0.05); pth.lineTo(hx + 0.3, hy - 0.4); pth.lineTo(hx + 0.55, hy - 0.1)
            c.drawPath(pth, P(col("#2F6FD6"), 0.05))
        elif k == "paper":
            r = skia.Rect.MakeXYWH(hx - 0.1, hy - 0.9, 0.75, 1.0)
            c.drawRect(r, P(col("#F7F3E8"))); c.drawRect(r, P(INK, 0.04))
            for i in range(5):
                c.drawLine(r.left() + 0.1, r.top() + 0.18 + i * 0.15, r.right() - 0.1, r.top() + 0.18 + i * 0.15,
                           P(col("#9A9A9A"), 0.03))
        elif k == "mug":
            r = skia.Rect.MakeXYWH(hx - 0.25, hy - 0.45, 0.42, 0.5)
            c.drawRoundRect(r, 0.05, 0.05, P(col("#E9E4D6"))); c.drawRoundRect(r, 0.05, 0.05, P(INK, 0.05))
            c.drawArc(skia.Rect.MakeXYWH(hx + 0.08, hy - 0.35, 0.25, 0.28), -90, 180, False, P(INK, 0.05))


def _bowl(hx, hy):
    p = skia.Path()
    p.moveTo(hx - 0.45, hy - 0.15)
    p.lineTo(hx + 0.45, hy - 0.15)
    p.cubicTo(hx + 0.42, hy + 0.3, hx - 0.42, hy + 0.3, hx - 0.45, hy - 0.15)
    p.close()
    return p


def draw_can(c: skia.Canvas, x, y, h, tint="#2E64C8"):
    """Plain unbranded soda can, standing on (x,y)."""
    w = h * 0.55
    body = skia.Rect.MakeXYWH(x - w / 2, y - h, w, h)
    c.drawRoundRect(body, w * 0.12, w * 0.12, P(col(tint)))
    c.drawRect(skia.Rect.MakeXYWH(x - w / 2, y - h * 0.62, w, h * 0.16), P(col("#F2F2F2")))
    c.drawRect(skia.Rect.MakeXYWH(x - w / 2, y - h, w, h * 0.08), P(col("#C9CED6")))
    c.drawLine(x - w * 0.28, y - h * 0.9, x - w * 0.28, y - h * 0.1, P(skia.Color(255, 255, 255, 70), w * 0.08))
    c.drawRoundRect(body, w * 0.12, w * 0.12, P(INK, h * 0.035))

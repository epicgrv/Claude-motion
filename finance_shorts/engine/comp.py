"""Frame compositor: plates + camera, characters integrated into the plate, in-world graphics, captions, finishing.

A video is a list of Shot objects (start, end, draw(fx, t, u)) where t is absolute seconds and u is 0..1 inside the shot.
render() draws every frame with skia at 1080x1920 and pipes RGBA into ffmpeg; frames are split across processes.
"""
from __future__ import annotations

import json
import math
import os
import re
import subprocess
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Callable

import numpy as np
import skia

from finance_shorts.engine.character import INK, P, col

W, H, FPS = 1080, 1920, 30
ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT / "assets" / "fonts"


# ------------------------------------------------------------------------------------------------ utils
def ease(u: float, kind="inout") -> float:
    u = max(0.0, min(1.0, u))
    if kind == "in":
        return u * u * u
    if kind == "out":
        return 1 - (1 - u) ** 3
    if kind == "linear":
        return u
    return u * u * (3 - 2 * u) if kind == "smooth" else (4 * u ** 3 if u < 0.5 else 1 - (-2 * u + 2) ** 3 / 2)


def lerp(a, b, u):
    return a + (b - a) * u


def keys(t: float, ks: list, kind="inout"):
    """ks = [(t0, v0), (t1, v1), ...] with v float or tuple; eased between keys."""
    if t <= ks[0][0]:
        return ks[0][1]
    for (t0, v0), (t1, v1) in zip(ks, ks[1:]):
        if t <= t1:
            u = ease((t - t0) / max(1e-6, t1 - t0), kind)
            if isinstance(v0, tuple):
                return tuple(lerp(a, b, u) for a, b in zip(v0, v1))
            return lerp(v0, v1, u)
    return ks[-1][1]


def spring(t: float, freq=3.0, damp=4.0):
    """0 -> 1 overshooting settle."""
    if t <= 0:
        return 0.0
    return 1 - math.exp(-damp * t) * math.cos(2 * math.pi * freq * t)


@lru_cache(None)
def font(name: str) -> skia.Typeface:
    return skia.Typeface.MakeFromFile(str(FONTS / f"{name}.ttf"))


@lru_cache(None)
def plate(name: str) -> skia.Image:
    p = ROOT / "visuals" / "pepsi-jet" / "plates" / f"{name}.png"
    img = skia.Image.open(str(p))
    if img.width() != 1440:  # low-res preview: scale into plate space so coordinates stay valid
        surf = skia.Surface(1440, 2560)
        surf.getCanvas().drawImageRect(img, skia.Rect.MakeWH(1440, 2560), SAMP)
        img = surf.makeImageSnapshot()
    return img


SAMP = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)


@lru_cache(None)
def _plate_np(name: str):
    import cv2
    p = ROOT / "visuals" / "pepsi-jet" / "plates" / f"{name}.png"
    im = cv2.cvtColor(cv2.imread(str(p), cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGBA)
    return np.ascontiguousarray(im)


@lru_cache(None)
def _depth_np(name: str):
    import cv2
    p = ROOT / "visuals" / "pepsi-jet" / "plates" / f"{name}_depth.png"
    d = cv2.imread(str(p), cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255.0
    return cv2.GaussianBlur(d, (0, 0), 3)


@lru_cache(None)
def _grid():
    gx, gy = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
    return gx, gy


# ------------------------------------------------------------------------------------------------ frame context
class Frame:
    def __init__(self, canvas: skia.Canvas, t: float, audio: "AudioInfo"):
        self.c = canvas
        self.t = t
        self.audio = audio

    # --- plates / camera
    def plate(self, name, cx, cy, zoom, rot=0.0, shake=0.0, blur=0.0, dim=0.0, par=(0.0, 0.0, 0.0)):
        """Draw a plate with a virtual camera (centre cx,cy in plate px; zoom 1 = full width).
        par = parallax (dx, dy, dz): layered sets move their foreground layer by (dx,dy) px and dz extra zoom;
        single-image sets with a depth map warp per pixel. Leaves the canvas in plate space; call end()."""
        self._fg = None
        has_layers = (ROOT / "visuals" / "pepsi-jet" / "plates" / f"{name}_fg.png").exists()
        has_depth = (ROOT / "visuals" / "pepsi-jet" / "plates" / f"{name}_depth.png").exists()
        if any(par) and not has_layers and has_depth and not blur and not rot:
            s_ = self.plate_warp(name, cx, cy, zoom, par, shake)
            if dim:
                self.c.drawRect(skia.Rect.MakeWH(5000, 5000), skia.Paint(Color=skia.Color(0, 0, 0, int(255 * dim))))
            return s_
        img = plate(name + "_bg") if has_layers else plate(name)
        c = self.c
        s = (W / img.width()) * max(1.0, zoom)
        hw, hh = W / (2 * s), H / (2 * s)
        cx = min(max(cx, hw), img.width() - hw)
        cy = min(max(cy, hh), img.height() - hh)
        if shake:
            n = self.t * 37.0
            cx += shake * (math.sin(n * 1.7) + 0.5 * math.sin(n * 3.1)) / s
            cy += shake * (math.cos(n * 1.3) + 0.5 * math.sin(n * 2.3)) / s
        c.save()
        c.translate(W / 2, H / 2)
        c.rotate(rot)
        c.scale(s, s)
        c.translate(-cx, -cy)
        paint = None
        if blur:
            paint = skia.Paint(ImageFilter=skia.ImageFilters.Blur(blur / s, blur / s))
        c.drawImage(img, 0, 0, SAMP, paint)
        if dim:
            c.drawRect(skia.Rect.MakeWH(img.width(), img.height()), skia.Paint(Color=skia.Color(0, 0, 0, int(255 * dim))))
        if has_layers:
            self._fg = (name, cx, cy, par, paint, dim)
        return s  # caller must self.end()

    def fg(self):
        """Draw the pending foreground layer now (call before drawing characters that stand in front of it)."""
        if not self._fg:
            return
        name, cx, cy, par, paint, dim = self._fg
        self._fg = None
        c = self.c
        img = plate(name + "_fg")
        c.save()
        c.translate(cx, cy)
        k = 1.0 + par[2]
        c.scale(k, k)
        c.translate(-cx + par[0] / k, -cy + par[1] / k)
        c.drawImage(img, 0, 0, SAMP, paint)
        if dim:
            c.drawImage(img, 0, 0, SAMP, skia.Paint(ColorFilter=skia.ColorFilters.Blend(skia.Color(0, 0, 0, int(255 * dim)),
                                                                                       skia.BlendMode.kSrcATop)))
        c.restore()

    def plate_warp(self, name, cx, cy, zoom, par=(0.0, 0.0, 0.0), shake=0.0):
        """2.5-D parallax for a single-image plate using its depth map (plates/<name>_depth.png, 1 = near).
        par = (dx, dy, dz): near pixels shift by up to dx,dy plate px and zoom by dz extra relative to far ones.
        Leaves the canvas in plate space (like plate()); call end() afterwards."""
        import cv2
        img, dep = _plate_np(name), _depth_np(name)
        ph, pw = dep.shape
        s = (W / pw) * max(1.0, zoom)
        hw, hh = W / (2 * s), H / (2 * s)
        cx = min(max(cx, hw), pw - hw)
        cy = min(max(cy, hh), ph - hh)
        if shake:
            n = self.t * 37.0
            cx += shake * (math.sin(n * 1.7) + 0.5 * math.sin(n * 3.1)) / s
            cy += shake * (math.cos(n * 1.3) + 0.5 * math.sin(n * 2.3)) / s
        gx, gy = _grid()
        px = (cx + (gx - W / 2) / s).astype(np.float32)
        py = (cy + (gy - H / 2) / s).astype(np.float32)
        d = cv2.remap(dep, px, py, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE) - 0.5
        mx = px - par[0] * d - (px - cx) * par[2] * d
        my = py - par[1] * d - (py - cy) * par[2] * d
        out = cv2.remap(img, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        self.c.drawImage(skia.Image.fromarray(out, colorType=skia.kRGBA_8888_ColorType), 0, 0)
        c = self.c
        c.save()
        c.translate(W / 2, H / 2)
        c.scale(s, s)
        c.translate(-cx, -cy)
        return s

    def occlude(self, name, shape):
        """Redraw part of the plate on top (foreground furniture in front of a character). shape: Rect, RRect-able
        rect or Path in plate coordinates. Call between plate() and end()."""
        c = self.c
        c.save()
        if isinstance(shape, skia.Path):
            c.clipPath(shape, doAntiAlias=True)
        else:
            c.clipRect(shape, doAntiAlias=True)
        c.drawImage(plate(name), 0, 0, SAMP)
        c.restore()

    def end(self):
        if getattr(self, "_fg", None):
            self.fg()
        self.c.restore()

    # --- character integration in plate space
    def char(self, ch, x, y, r, tint=(1.0, 0.96, 0.9), light=1.0, shadow=0.42, **kw):
        c = self.c
        if shadow:
            sp = skia.Paint(AntiAlias=True, Color=skia.Color(10, 6, 4, int(255 * shadow)),
                            MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, r * 0.18))
            c.drawOval(skia.Rect.MakeXYWH(x - r * 1.25, y - r * 0.2, r * 2.5, r * 0.42), sp)
        m = [tint[0] * light, 0, 0, 0, 0,
             0, tint[1] * light, 0, 0, 0,
             0, 0, tint[2] * light, 0, 0,
             0, 0, 0, 1, 0]
        c.saveLayer(None, skia.Paint(ColorFilter=skia.ColorFilters.Matrix(m)))
        ch.draw(c, x, y, r, **kw)
        c.restore()

    # --- text
    def text(self, s, x, y, size, fnt="montserrat-900", color="#FFFFFF", align="center", stroke=0.0,
             stroke_col="#1A1410", shadow=0.0, alpha=1.0, skew=0.0, scale_x=1.0):
        if not s:
            return 0.0
        c = self.c
        f = skia.Font(font(fnt), size)
        f.setSkewX(skew)
        f.setScaleX(scale_x)
        blob = skia.TextBlob(s, f)
        wdt = f.measureText(s)
        ox = {"center": -wdt / 2, "left": 0, "right": -wdt}[align]
        a = int(255 * alpha)
        if shadow:
            sp = skia.Paint(AntiAlias=True, Color=skia.Color(0, 0, 0, int(a * 0.55)),
                            MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, shadow))
            c.drawTextBlob(blob, x + ox + shadow * 0.3, y + shadow * 0.6, sp)
        if stroke:
            sp = skia.Paint(AntiAlias=True, Color=col(stroke_col, a), Style=skia.Paint.kStroke_Style,
                            StrokeWidth=stroke, StrokeJoin=skia.Paint.kRound_Join)
            c.drawTextBlob(blob, x + ox, y, sp)
        c.drawTextBlob(blob, x + ox, y, skia.Paint(AntiAlias=True, Color=col(color, a)))
        return wdt

    # --- light
    def rays(self, x, y, angle, spread, length, color="#FFE2B0", alpha=0.18, n=7, seed=0):
        """Volumetric-looking light shafts fanning from (x,y) towards `angle` (deg, 90 = down)."""
        c = self.c
        rng = np.random.default_rng(seed)
        for i in range(n):
            a = math.radians(angle + (i / max(1, n - 1) - 0.5) * spread + math.sin(self.t * 0.6 + i) * 1.2)
            wdt = math.radians(spread / n * rng.uniform(0.3, 0.9))
            p = skia.Path()
            p.moveTo(x, y)
            p.lineTo(x + math.cos(a - wdt) * length, y + math.sin(a - wdt) * length)
            p.lineTo(x + math.cos(a + wdt) * length, y + math.sin(a + wdt) * length)
            p.close()
            sh = skia.GradientShader.MakeLinear([skia.Point(x, y), skia.Point(x + math.cos(a) * length, y + math.sin(a) * length)],
                                                [col(color, int(255 * alpha * rng.uniform(0.5, 1.0))), col(color, 0)])
            c.drawPath(p, skia.Paint(AntiAlias=True, Shader=sh, BlendMode=skia.BlendMode.kScreen,
                                     MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, length * 0.012)))

    def glow(self, x, y, rad, color="#7FC8FF", alpha=0.35):
        c = self.c
        sh = skia.GradientShader.MakeRadial(skia.Point(x, y), rad, [col(color, int(255 * alpha)), col(color, 0)])
        c.drawCircle(x, y, rad, skia.Paint(Shader=sh, BlendMode=skia.BlendMode.kScreen))


# ------------------------------------------------------------------------------------------------ audio-driven data
class AudioInfo:
    def __init__(self, timeline_json: Path, vo_wav: Path):
        import soundfile as sf
        self.tl = json.loads(Path(timeline_json).read_text())
        x, sr = sf.read(vo_wav)
        x = x if x.ndim == 1 else x.mean(1)
        hop = sr // FPS
        n = len(x) // hop
        rms = np.sqrt(np.array([np.mean(x[i * hop:(i + 1) * hop] ** 2) for i in range(n)]) + 1e-10)
        db = 20 * np.log10(rms)
        self.env = np.clip((db + 38) / 22, 0, 1)

    def speaking(self, who: str, t: float) -> float:
        for ln in self.tl["lines"]:
            if ln["who"] == who and ln["start"] - 0.02 <= t <= ln["end"] + 0.02:
                i = int(t * FPS)
                v = self.env[i] if i < len(self.env) else 0
                return round(v * 3) / 3  # cartoon mouth: 4 levels
        return 0.0


def blink(t: float, seed: int) -> bool:
    period = 2.6 + (seed % 7) * 0.31
    ph = (t + seed * 0.77) % period
    return ph < 0.1


# ------------------------------------------------------------------------------------------------ captions
def _norm(w: str) -> str:
    return re.sub(r"[^a-z0-9]", "", w.lower())


def caption_words(tl: dict) -> list[tuple[str, float, float]]:
    """Script words with times: align script tokens of each line to whisper word timings."""
    out = []
    for ln in tl["lines"]:
        script = ln["text"].replace("…", " ").replace("—", " ").split()
        ws = []
        for w in ln["words"]:  # merge whisper fragments like ",000" ".50" "%" "-aired"
            if ws and re.match(r"^[,.%\-]", w["w"]):
                ws[-1] = (ws[-1][0] + w["w"], ws[-1][1], w["e"])
            else:
                ws.append((w["w"], w["s"], w["e"]))
        if not ws:
            continue
        if len(ws) == len(script):
            out += [(s, a, b) for s, (_, a, b) in zip(script, ws)]
        else:  # proportional by character position
            tot = sum(len(s) for s in script)
            t0, t1 = ws[0][1], ws[-1][2]
            acc = 0
            for s in script:
                a = t0 + (t1 - t0) * acc / tot
                acc += len(s)
                out.append((s, a, t0 + (t1 - t0) * acc / tot))
    return out


def chunk_captions(words, max_words=2, max_chars=13, min_dur=0.28):
    chunks, cur = [], []
    for w in words:
        if cur and (len(cur) >= max_words or len(" ".join(x[0] for x in cur + [w])) > max_chars
                    or re.search(r"[.?!,:]$", cur[-1][0]) or w[1] - cur[-1][2] > 0.35):
            chunks.append(cur)
            cur = []
        cur.append(w)
    if cur:
        chunks.append(cur)
    res = []
    for i, ch in enumerate(chunks):
        s = ch[0][1]
        e = chunks[i + 1][0][1] if i + 1 < len(chunks) and chunks[i + 1][0][1] - ch[-1][2] < 0.6 else ch[-1][2] + 0.25
        res.append((" ".join(x[0] for x in ch).replace('"', ""), s, max(e, s + min_dur)))
    return res


# ------------------------------------------------------------------------------------------------ finishing
class Finisher:
    def __init__(self, seed=7):
        rng = np.random.default_rng(seed)
        self.grain = []
        for _ in range(6):
            g = rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
            a = np.clip(128 + g * 22, 0, 255).astype(np.uint8)
            rgba = np.dstack([a, a, a, np.full_like(a, 26)])
            self.grain.append(skia.Image.fromarray(rgba, colorType=skia.kRGBA_8888_ColorType))
        self.dust = rng.random((70, 5))

        self.small = skia.Surface(W // 4, H // 4)

    def bloom(self, c: skia.Canvas, surf: skia.Surface, amount: float, thresh=0.72):
        """Glow on bright areas: threshold -> quarter-res blur -> screen back over the frame."""
        img = surf.makeImageSnapshot()
        k = 1.0 / (1.0 - thresh)
        m = [k, 0, 0, 0, -thresh * k, 0, k, 0, 0, -thresh * k, 0, 0, k, 0, -thresh * k, 0, 0, 0, 1, 0]
        sc = self.small.getCanvas()
        sc.clear(skia.Color(0, 0, 0, 0))
        sc.drawImageRect(img, skia.Rect.MakeWH(W // 4, H // 4), SAMP,
                         skia.Paint(ColorFilter=skia.ColorFilters.Matrix(m)))
        glow = self.small.makeImageSnapshot()
        sc.clear(skia.Color(0, 0, 0, 0))
        sc.drawImage(glow, 0, 0, SAMP, skia.Paint(ImageFilter=skia.ImageFilters.Blur(9, 9)))
        glow = self.small.makeImageSnapshot()
        c.drawImageRect(glow, skia.Rect.MakeWH(W, H), SAMP,
                        skia.Paint(BlendMode=skia.BlendMode.kScreen, Alpha=int(255 * min(1.0, amount))))

    def __call__(self, c: skia.Canvas, t: float, dust=0.6, vignette=0.42, warm=None, surf=None, bloom=0.0):
        if bloom and surf is not None:
            self.bloom(c, surf, bloom)
        # dust motes (screen space, slow drift, depth-sized)
        if dust:
            for i, (px, py, sz, sp, ph) in enumerate(self.dust):
                x = (px * W + math.sin(t * 0.4 + ph * 6) * 30 + t * 8 * (sp - 0.5)) % W
                y = (py * H - t * (10 + sp * 25)) % H
                rad = 1.5 + sz * 4.5
                a = int(255 * dust * (0.25 + 0.5 * sz) * (0.6 + 0.4 * math.sin(t * 2 + ph * 9)))
                c.drawCircle(x, y, rad, skia.Paint(AntiAlias=True, Color=skia.Color(255, 236, 200, a),
                                                   MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, rad * 0.8),
                                                   BlendMode=skia.BlendMode.kScreen))
        if warm:
            c.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Color=col(warm[0], int(255 * warm[1])),
                                                          BlendMode=skia.BlendMode.kSoftLight))
        if vignette:
            sh = skia.GradientShader.MakeRadial(skia.Point(W / 2, H * 0.47), H * 0.72,
                                                [skia.Color(0, 0, 0, 0), skia.Color(0, 0, 0, 0),
                                                 skia.Color(0, 0, 0, int(255 * vignette))], [0, 0.55, 1])
            c.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Shader=sh))
        g = self.grain[int(t * FPS) % len(self.grain)]
        c.drawImageRect(g, skia.Rect.MakeWH(W, H), SAMP, skia.Paint(BlendMode=skia.BlendMode.kOverlay))


def draw_caption(fx: Frame, text: str, y: float, age: float):
    size = 92 if len(text) <= 9 else (84 if len(text) <= 12 else 74)
    pop = 1.0 + 0.06 * max(0.0, 1 - age / 0.08)  # tiny settle, mostly a hard cut like the reference
    c = fx.c
    c.save()
    c.translate(W / 2, y)
    c.scale(pop, pop)
    fx.text(text, 0, 0, size, "montserrat-900", "#FFFFFF", stroke=9, stroke_col="#15100D", shadow=10)
    c.restore()


# ------------------------------------------------------------------------------------------------ render
@dataclass
class Shot:
    name: str
    start: float
    end: float
    draw: Callable  # draw(fx, t, u)
    cap_y: float = 0.63  # caption baseline as fraction of H (None = no captions)
    dust: float = 0.5
    vignette: float = 0.4
    warm: tuple | None = None
    bloom: float = 0.55
    whip: int = 0  # whip-pan into this shot: +1 from the right, -1 from the left


def _whip(surf: skia.Surface, k: float, direction: int):
    """Directional motion-blur slide for the first frames of a shot (k: 1 -> 0)."""
    img = surf.makeImageSnapshot()
    c = surf.getCanvas()
    c.clear(skia.Color(0, 0, 0))
    c.drawImage(img, direction * W * 0.18 * k * k, 0, SAMP,
                skia.Paint(ImageFilter=skia.ImageFilters.Blur(90 * k, 2, skia.TileMode.kClamp)))


def _render_range(args):
    shots_mod, shot_names, f0, f1, out_path, timeline, vo, caps_on = args
    import importlib
    mod = importlib.import_module(shots_mod)
    shots = [s for s in mod.SHOTS if s.name in shot_names] if shot_names else mod.SHOTS
    audio = AudioInfo(timeline, vo)
    caps = chunk_captions(caption_words(audio.tl)) if caps_on else []
    fin = Finisher()
    surf = skia.Surface(W, H)
    c = surf.getCanvas()
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
                           "-pix_fmt", "yuv420p", str(out_path)], stdin=subprocess.PIPE)
    for fi in range(f0, f1):
        t = fi / FPS
        shot = next((s for s in shots if s.start <= t < s.end), shots[-1])
        c.clear(skia.Color(0, 0, 0))
        fx = Frame(c, t, audio)
        u = (t - shot.start) / max(1e-6, shot.end - shot.start)
        c.save()
        shot.draw(fx, t, u)
        c.restore()
        if shot.whip and t - shot.start < 0.13:
            _whip(surf, 1 - (t - shot.start) / 0.13, shot.whip)
        fin(c, t, dust=shot.dust, vignette=shot.vignette, warm=shot.warm, surf=surf, bloom=shot.bloom)
        if shot.cap_y is not None:
            for txt, s, e in caps:
                if s <= t < e:
                    draw_caption(fx, txt, shot.cap_y * H, t - s)
                    break
        ff.stdin.write(surf.makeImageSnapshot().tobytes())
    ff.stdin.close()
    ff.wait()
    return out_path


def render(shots_mod: str, out: Path, timeline: Path, vo: Path, t0: float, t1: float, workers=4,
           shot_names=None, caps=True, segments=None):
    """Render [t0,t1) (or a list of (t0,t1) segments concatenated) to out (video only)."""
    out = Path(out)
    tmp = out.parent / (out.stem + "_parts")
    tmp.mkdir(parents=True, exist_ok=True)
    segs = segments or [(t0, t1)]
    jobs = []
    for si, (a, b) in enumerate(segs):
        fa, fb = int(round(a * FPS)), int(round(b * FPS))
        n = max(1, min(workers, (fb - fa) // 30 or 1))
        step = math.ceil((fb - fa) / n)
        for k in range(n):
            s0, s1 = fa + k * step, min(fb, fa + (k + 1) * step)
            if s0 < s1:
                jobs.append((shots_mod, shot_names, s0, s1, tmp / f"p{si:02d}_{k:02d}.mp4", str(timeline), str(vo), caps))
    with ProcessPoolExecutor(workers) as ex:
        parts = list(ex.map(_render_range, jobs))
    lst = tmp / "list.txt"
    lst.write_text("".join(f"file '{p.name}'\n" for p in parts))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out)],
                   check=True)
    return out

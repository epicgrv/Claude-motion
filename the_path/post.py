"""Compositing & finishing in scene-linear float, then one display transform.

EXR (linear half-float beauty + depth) -> atmospheric depth fog -> contained optical bloom
(+ a single anamorphic streak on the ignition) -> hue-preserving filmic shoulder with highlight
desaturation -> gentle contrast -> sRGB -> fine temporal grain + blue-ish dither -> 8-bit.

The background constant #060A0C passes through untouched (the toe is the identity) so the
brief's ambient colour is exactly what the viewer gets in empty space.
"""
from __future__ import annotations

import math
import os

os.environ.setdefault("OPENCV_IO_ENABLE_OPENEXR", "1")
import cv2
import numpy as np

from .config import A, FPS, lin

try:
    import OpenEXR
except Exception:  # pragma: no cover
    OpenEXR = None

BG_LIN = np.array(lin("bg"), dtype=np.float32)
FOG_COL = np.array([0.0030, 0.0062, 0.0074], dtype=np.float32)

DEFAULT = dict(exposure=1.0, fog=0.0036, fog_start=6.0, bloom=0.22, streak=0.0, vignette=0.14,
               grain=0.010, saturation=1.02, contrast=1.06, shoulder=0.72, highlight_desat=0.55,
               fade=0.0)


def read_exr(path):
    """-> (beauty float32 HxWx3 scene-linear, depth float32 HxW or None). Multipart EXR."""
    f = OpenEXR.File(str(path))
    img, depth = None, None
    for part in f.parts:
        for name, ch in part.channels.items():
            px = ch.pixels
            if name.startswith("Beauty") or name in ("RGBA", "Image"):
                img = px[..., :3].astype(np.float32)
            elif name.startswith("Depth"):
                depth = (px[..., 0] if px.ndim == 3 else px).astype(np.float32)
    if img is None:
        raise RuntimeError(f"no beauty layer in {path}")
    return img, depth


def _blur(x, sigma):
    k = int(sigma * 3) * 2 + 1
    return cv2.GaussianBlur(x, (max(3, k), max(3, k)), sigma, borderType=cv2.BORDER_REFLECT)


def bloom(img, amount, W, streak=0.0):
    if amount <= 0 and streak <= 0:
        return img
    lum = img @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    knee = np.clip((lum - 0.7) / 0.6, 0, 1)
    hi = img * (knee * knee * (3 - 2 * knee))[..., None]
    s = W / 1920.0
    out = (0.50 * _blur(hi, 2.0 * s) + 0.34 * _blur(hi, 7.0 * s) + 0.24 * _blur(hi, 22.0 * s) +
           0.16 * _blur(hi, 60.0 * s))
    res = img + amount * out
    if streak > 0:
        k = int(W * 0.5) | 1
        hs = cv2.GaussianBlur(hi, (k, 1), W * 0.09, borderType=cv2.BORDER_REFLECT)
        hs = cv2.GaussianBlur(hs, (1, 5), 1.2)
        tint = np.array([0.55, 0.9, 1.0], np.float32)   # cool anamorphic blue-green streak
        res = res + streak * hs * tint * 2.2
    return res


def tonemap(img, p):
    img = img * p["exposure"]
    lum = img @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    # highlight desaturation: very hot energy goes toward a light core (never a neon blob)
    k = np.clip((lum - 1.2) / 6.0, 0, 1)[..., None] * p["highlight_desat"]
    img = img * (1 - k) + lum[..., None] * k
    lum = img @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    s0 = p["shoulder"]
    over = np.maximum(lum - s0, 0)
    y = np.where(lum <= s0, lum, s0 + (1 - s0) * (1 - np.exp(-over / (1 - s0))))
    img = img * (y / np.maximum(lum, 1e-6))[..., None]
    # saturation (about luminance), then contrast about mid grey in display space
    l2 = img @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    img = l2[..., None] + (img - l2[..., None]) * p["saturation"]
    img = np.clip(img, 0, None)
    return img


def oetf(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.power(x, 1 / 2.4) - 0.055)


def grade_display(x, p):
    c = p["contrast"]
    pivot = 0.42
    # contrast that leaves blacks alone (the toe region keeps #060A0C intact)
    w = np.clip(x / 0.10, 0, 1)
    w = w * w * (3 - 2 * w)
    y = pivot + (x - pivot) * c
    return x + (np.clip(y, 0, 1) - x) * w


def process(beauty, depth, frame, params=None, size=None, sharpen=0.0):
    p = dict(DEFAULT)
    if params:
        p.update(params)
    img = beauty.astype(np.float32)
    if size is not None and (img.shape[1], img.shape[0]) != tuple(size):
        # internal render resolution -> master resolution (Lanczos on linear data; depth is only used for fog)
        img = cv2.resize(img, tuple(size), interpolation=cv2.INTER_LANCZOS4)
        img = np.maximum(img, 0)
        if depth is not None:
            depth = cv2.resize(depth, tuple(size), interpolation=cv2.INTER_LINEAR)
    h, w = img.shape[:2]
    if depth is not None and p["fog"] > 0:
        d = np.where(depth > 1e9, 1e4, depth)
        f = 1 - np.exp(-p["fog"] * np.maximum(d - p["fog_start"], 0))
        img = img * (1 - f[..., None]) + FOG_COL * f[..., None]
    img = bloom(img, p["bloom"], w, p["streak"])
    img = tonemap(img, p)
    # vignette in scene-linear exposure terms
    if p["vignette"] > 0:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        r2 = ((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2
        img = img * (1 - p["vignette"] * np.clip(r2 / 2, 0, 1) ** 1.2)[..., None]
    disp = oetf(img)
    disp = grade_display(disp, p)
    if sharpen > 0:
        bl = cv2.GaussianBlur(disp, (0, 0), 1.1)
        disp = np.clip(disp + sharpen * (disp - bl), 0, 1)
    if p["fade"] > 0:
        disp = disp * (1 - p["fade"]) + oetf(BG_LIN)[None, None, :] * p["fade"] if False else disp * (1 - p["fade"])
    # temporal grain (fine, luma-weighted) + triangular dither against banding
    rng = np.random.default_rng(1234 + frame)
    g = rng.standard_normal((h, w)).astype(np.float32)
    g = cv2.GaussianBlur(g, (0, 0), 0.65) * 1.9
    lum = disp.mean(axis=2)
    gw = (0.55 + 0.9 * (1 - np.clip(lum * 2.2, 0, 1))) * p["grain"]
    disp = disp + (g * gw)[..., None]
    tri = (rng.random((h, w, 1), dtype=np.float32) + rng.random((h, w, 1), dtype=np.float32) - 1.0) / 255.0
    disp = disp + tri
    return (np.clip(disp, 0, 1) * 255.0 + 0.5).astype(np.uint8)


def frame_params(frame: int) -> dict:
    """Per-frame finishing parameters driven by the timeline (anamorphic streak, fades...)."""
    t = frame / FPS
    p = {}
    # single anamorphic flare across the screen at the flame ignition (brief 5:00)
    x = (t - A["ignition"]) / 0.22
    if 0 <= x <= 1.0:
        p["streak"] = 0.95 * math.sin(math.pi * x) ** 2
    return p


def exr_to_png(exr_path, png_path, frame):
    b, d = read_exr(exr_path)
    out = process(b, d, frame, frame_params(frame))
    cv2.imwrite(str(png_path), cv2.cvtColor(out, cv2.COLOR_RGB2BGR))
    return out

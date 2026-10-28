"""Procedurally drawn flag textures (no external assets): ES MX FR DE IT BR JP GB."""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw

from .config import ASSETS

W, H = 600, 400
FLAGS = ["ES", "MX", "FR", "DE", "IT", "BR", "JP", "GB"]


def _tri(d, cols, vertical=True):
    n = len(cols)
    for i, c in enumerate(cols):
        if vertical:
            d.rectangle([W * i // n, 0, W * (i + 1) // n, H], fill=c)
        else:
            d.rectangle([0, H * i // n, W, H * (i + 1) // n], fill=c)


def draw(code):
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    if code == "ES":
        d.rectangle([0, 0, W, H], fill=(198, 11, 30))
        d.rectangle([0, H // 4, W, H * 3 // 4], fill=(255, 196, 0))
    elif code == "MX":
        _tri(d, [(0, 104, 71), (255, 255, 255), (206, 17, 38)])
        d.ellipse([W // 2 - 48, H // 2 - 48, W // 2 + 48, H // 2 + 48], fill=(150, 110, 60))
        d.ellipse([W // 2 - 30, H // 2 - 30, W // 2 + 30, H // 2 + 30], fill=(60, 140, 70))
    elif code == "FR":
        _tri(d, [(0, 85, 164), (255, 255, 255), (239, 65, 53)])
    elif code == "DE":
        _tri(d, [(0, 0, 0), (221, 0, 0), (255, 206, 0)], vertical=False)
    elif code == "IT":
        _tri(d, [(0, 146, 70), (255, 255, 255), (206, 43, 55)])
    elif code == "BR":
        d.rectangle([0, 0, W, H], fill=(0, 156, 59))
        d.polygon([(W // 2, 30), (W - 50, H // 2), (W // 2, H - 30), (50, H // 2)], fill=(255, 223, 0))
        d.ellipse([W // 2 - 95, H // 2 - 95, W // 2 + 95, H // 2 + 95], fill=(0, 39, 118))
        d.arc([W // 2 - 95, H // 2 - 60, W // 2 + 95, H // 2 + 130], 200, 340, fill="white", width=10)
    elif code == "JP":
        d.rectangle([0, 0, W, H], fill=(255, 255, 255))
        d.ellipse([W // 2 - 120, H // 2 - 120, W // 2 + 120, H // 2 + 120], fill=(188, 0, 45))
    elif code == "GB":
        d.rectangle([0, 0, W, H], fill=(1, 33, 105))
        for w, col in ((70, "white"), (34, (200, 16, 46))):
            d.line([0, 0, W, H], fill=col, width=w)
            d.line([0, H, W, 0], fill=col, width=w)
        d.rectangle([W // 2 - 60, 0, W // 2 + 60, H], fill="white")
        d.rectangle([0, H // 2 - 60, W, H // 2 + 60], fill="white")
        d.rectangle([W // 2 - 34, 0, W // 2 + 34, H], fill=(200, 16, 46))
        d.rectangle([0, H // 2 - 34, W, H // 2 + 34], fill=(200, 16, 46))
    return im


def ensure(dirpath: Path | None = None):
    dirpath = Path(dirpath or ASSETS / "generated" / "flags")
    dirpath.mkdir(parents=True, exist_ok=True)
    out = {}
    for code in FLAGS:
        p = dirpath / f"{code}.png"
        if not p.exists():
            draw(code).save(p)
        out[code] = str(p)
    return out

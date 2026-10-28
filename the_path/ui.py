"""Shared physical-UI building blocks: pill buttons with a heavy lip, cards, tiles, avatars.

Everything is real geometry (rounded slabs with true bevels), lit by real lights.
Convention for UI parts: built in a local frame with +Z towards the viewer; thickness along Z.
"""
from __future__ import annotations

import math

import numpy as np

from . import anim, geo, mat
from .config import FONT_BLACK, FONT_BOLD, PAL, lin

_CACHE: dict = {}


def reset():
    _CACHE.clear()


def M(name):
    """Shared, lazily-created materials."""
    if name in _CACHE:
        return _CACHE[name]
    mk = mat.principled
    table = dict(
        card=lambda: mk("ui_card", "surf1", 0.62, coat=0.05, rvar=0.05, spec=0.35),
        card2=lambda: mk("ui_card2", "surf2", 0.55, coat=0.08, rvar=0.05, spec=0.4),
        panel=lambda: mk("ui_panel", "surf0", 0.7, rvar=0.04, spec=0.3),
        edge=lambda: mk("ui_edge", "edge", 0.5, coat=0.2),
        trough=lambda: mk("ui_trough", "#10181D", 0.8, spec=0.2),
        text=lambda: mk("ui_text", "snow", 0.5, emit="snow", emit_strength=0.25, spec=0.3),
        text_dim=lambda: mk("ui_text_dim", "#AFC0CC", 0.55, emit="#AFC0CC", emit_strength=0.12),
        green_top=lambda: mk("ui_green_top", "feather", 0.34, coat=0.25, coat_rough=0.2, sheen=0.2, rvar=0.05),
        green_base=lambda: mk("ui_green_base", "feather_dark", 0.5, rvar=0.04),
        gray_top=lambda: mk("ui_gray_top", "#3A4A54", 0.42, coat=0.1, rvar=0.04),
        gray_base=lambda: mk("ui_gray_base", "#26323A", 0.55, rvar=0.04),
        glass=lambda: mk("ui_glass", "#0A1015", 0.08, coat=1.0, coat_rough=0.03, spec=0.9),
        alu=lambda: mk("ui_alu", "#1E2A31", 0.28, metal=0.9, rvar=0.04),
        tile=lambda: mk("ui_tile", "#E9F1F5", 0.38, coat=0.35, coat_rough=0.12, rvar=0.03),
        tile_edge=lambda: mk("ui_tile_edge", "#A9BAC4", 0.5),
        dark_text=lambda: mk("ui_dark_text", "#2F3B44", 0.55),
        green_text=lambda: mk("ui_green_text", "feather", 0.4, emit="feather", emit_strength=0.8),
        orange=lambda: mk("ui_orange", "fox", 0.35, coat=0.3, emit="fox", emit_strength=0.4),
        blue=lambda: mk("ui_blue", "macaw", 0.35, coat=0.3),
        purple=lambda: mk("ui_purple", "beetle", 0.35, coat=0.3),
        yellow=lambda: mk("ui_yellow", "bee", 0.35, coat=0.3),
    )
    _CACHE[name] = table[name]()
    return _CACHE[name]


def text(coll, name, body, size, material=None, loc=(0, 0, 0), parent=None, font=FONT_BLACK, extrude=0.012,
         align="CENTER", rot=(0, 0, 0)):
    o = geo.text(name, coll, body, size=size, mat=material or M("text"), loc=loc, extrude=extrude, bevel=0.0015,
                 align=align, font_path=font, parent=parent)
    o.rotation_euler = rot
    return o


def button3d(ctx, coll, name, w, h, label, depth=0.30, lip=0.12, top="green_top", base="green_base",
             text_size=None, parent=None, loc=(0, 0, 0), text_mat=None):
    """Duolingo-style physical button: a darker base slab under a raised face. Returns dict.

    ``lid`` (face) moves along -Z by up to ``lip`` when pressed; the base never moves.
    """
    R = min(h * 0.5, w * 0.5)
    root = geo.empty(f"{name}_btn", coll, loc=loc, parent=parent)
    mt = mat.clone(M(top), f"{name}_top") if isinstance(top, str) else top
    mb = mat.clone(M(base), f"{name}_base") if isinstance(base, str) else base
    bs = geo.slab(f"{name}_base", coll, w, h, depth, R=R, rb=min(0.05 * h + 0.02, R * 0.5), mat=mb, loc=(0, -lip * 0.6, 0), parent=root)
    lid = geo.slab(f"{name}_lid", coll, w, h, depth, R=R, rb=min(0.05 * h + 0.02, R * 0.5), mat=mt, loc=(0, 0, lip), parent=root)
    ts = text_size or h * 0.36
    tx = text(coll, f"{name}_label", label, ts, text_mat or M("text"), loc=(0, 0, depth / 2 + 0.004), parent=lid)
    return dict(root=root, lid=lid, base=bs, text=tx, mtop=mt, mbase=mb, lip=lip, depth=depth)


def card(ctx, coll, name, w, h, d=0.1, R=0.14, material="card", parent=None, loc=(0, 0, 0)):
    m = M(material) if isinstance(material, str) else material
    return geo.slab(name, coll, w, h, d, R=R, rb=min(0.02 + d * 0.15, R * 0.4), mat=m, loc=loc, parent=parent)


def tile(ctx, coll, name, word, size=0.2, parent=None, loc=(0, 0, 0), pad=0.18, h=0.36, d=0.1):
    w = geo.text_width(word, size, FONT_BLACK) + 2 * pad
    root = geo.empty(f"{name}_tile", coll, loc=loc, parent=parent)
    body = geo.slab(f"{name}_body", coll, w, h, d, R=h * 0.28, rb=0.018, mat=M("tile"), parent=root)
    base = geo.slab(f"{name}_base", coll, w, h, d * 0.9, R=h * 0.28, rb=0.018, mat=M("tile_edge"), loc=(0, -0.035, -0.02), parent=root)
    tx = text(coll, f"{name}_word", word, size, M("dark_text"), loc=(0, 0, d / 2 + 0.003), parent=body)
    return dict(root=root, body=body, base=base, text=tx, w=w, h=h)


def avatar(ctx, coll, name, color, r=0.13, parent=None, loc=(0, 0, 0), initial=""):
    m = mat.principled(f"{name}_av", color, 0.45, coat=0.3)
    o = geo.slab(name, coll, r * 2, r * 2, r * 0.7, R=r, rb=r * 0.18, mat=m, loc=loc, parent=parent)
    if initial:
        text(coll, f"{name}_i", initial, r * 1.1, M("text"), loc=(0, 0, r * 0.35 + 0.003), parent=o)
    return o

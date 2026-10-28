"""The 'duolingo' wordmark as separate letters (so each can be sprung into existence by the line).

No official brand file is available in this environment; the wordmark is therefore a typographic
stand-in (Nunito Black, brand green).  If ``assets/official/duolingo_wordmark.svg`` is added later
this is the single place to swap it in.
"""
from __future__ import annotations

import math

import numpy as np
from fontTools.ttLib import TTFont

from . import geo
from .config import FONT_BLACK


def advances(body, size, font_path=FONT_BLACK):
    tt = TTFont(font_path)
    cmap, hmtx, upm = tt.getBestCmap(), tt["hmtx"], tt["head"].unitsPerEm
    return [hmtx[cmap[ord(c)]][0] / upm * size for c in body]


def build_logo(ctx, name, coll, width, mat, body="duolingo", loc=(0, 0, 0), extrude=0.10, bevel=0.012):
    """Create one text object per letter, baseline-centred pivots, wordmark centred on ``loc``.

    Faces -Y (towards a camera that looks along +Y).  Returns dict(letters, xs, size, height).
    """
    adv1 = advances(body, 1.0)
    size = width / sum(adv1)
    adv = [a * size for a in adv1]
    total = sum(adv)
    x = -total / 2
    letters, xs = [], []
    for i, (ch, a) in enumerate(zip(body, adv)):
        cx = x + a / 2
        o = geo.text(f"{name}_{ch}{i}", coll, ch, size=size, mat=mat, extrude=extrude, bevel=bevel,
                     loc=(loc[0] + cx, loc[1], loc[2]), align="CENTER", align_y="BOTTOM_BASELINE")
        o.rotation_euler = (math.pi / 2, 0, 0)
        letters.append(o)
        xs.append(loc[0] + cx)
        x += a
    return dict(letters=letters, xs=xs, size=size, height=size * 0.74, width=total)


def build_logo_local(coll, parent, width, mat, body="duolingo", loc=(0, 0, 0), extrude=0.10, bevel=0.012):
    """Same wordmark, parented to a station frame (faces its local +Z = towards the viewer)."""
    adv1 = advances(body, 1.0)
    size = width / sum(adv1)
    adv = [a * size for a in adv1]
    total = sum(adv)
    x = -total / 2
    letters, xs = [], []
    for i, (ch, a) in enumerate(zip(body, adv)):
        cx = x + a / 2
        o = geo.text(f"logoL_{ch}{i}", coll, ch, size=size, mat=mat, extrude=extrude, bevel=bevel,
                     loc=(loc[0] + cx, loc[1], loc[2]), align="CENTER", align_y="BOTTOM_BASELINE", parent=parent)
        letters.append(o)
        xs.append(loc[0] + cx)
        x += a
    return dict(letters=letters, xs=xs, size=size, height=size * 0.74, width=total)

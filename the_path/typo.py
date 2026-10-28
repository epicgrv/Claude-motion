"""Per-letter typography (clean, flat, no 3-D effects) whose letters can sprout from a baseline."""
from __future__ import annotations

import math

import numpy as np

from . import geo
from .logo import advances
from .config import FONT_BLACK


def text_line(coll, name, body, size, mat, parent, y=0.0, z=0.0, extrude=0.015, tracking=1.0):
    """One text object per glyph, centred as a line on x=0. Returns dict(letters, xs, width).

    Each letter's pivot is its baseline centre so scaling in y makes it rise from the baseline.
    """
    adv = [a * tracking for a in advances(body, size, FONT_BLACK)]
    total = sum(adv)
    x = -total / 2
    letters, xs = [], []
    for ch, a in zip(body, adv):
        cx = x + a / 2
        x += a
        if ch == " ":
            continue
        o = geo.text(f"{name}_{ch}{len(letters)}", coll, ch, size=size, mat=mat, extrude=extrude, bevel=0.0,
                     loc=(cx, y, z), align="CENTER", align_y="BOTTOM_BASELINE", parent=parent)
        letters.append(o)
        xs.append(cx)
    return dict(letters=letters, xs=np.array(xs), width=total, y=y, size=size)

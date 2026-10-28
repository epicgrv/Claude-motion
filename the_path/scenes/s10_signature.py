"""ESCENA 10 - FIRMA  (19:20 - 21:20)

A soft transition to a minimal end screen: the key light drains away so Duo and the wordmark sink back into
the dark (no fade-by-opacity: the lights simply go out), then the signature lights up like a sign being
switched on - clean, centred, still. Nothing animates after that; the piece ends with confidence.

The signature is the literal placeholder from the brief: [TU FIRMA].
"""
from __future__ import annotations

import numpy as np

from .. import anim, geo, mat, typo
from ..config import A, FPS, lin
from ..easing import smoothstep, smootherstep, u


def build(ctx):
    P = ctx.portrait
    F8 = ctx.state["F8"]
    c = ctx.coll("s10", window=(19.0, 21.35))
    root = F8.empty("F10", c)
    fr = np.arange(int(19.0 * FPS), int(21.3 * FPS))
    t = fr / FPS
    size = 0.62 if not P else 0.62
    sig_y = -0.35
    ink = mat.emissive("sig_ink", "snow", 0.0)
    ln = typo.text_line(c, "sig", "[TU FIRMA]", size, ink, root, y=sig_y, z=0.0)
    on0 = A["signature"] + 0.45
    # one shared material: drive the whole word with the average ramp, letters ride a per-letter scale-in instead
    e_all = smoothstep(u(t, on0, on0 + 0.55))
    anim.key(ink.node_tree, mat.e_strength(), fr, 0.9 * e_all)
    # a thin hairline under the signature grows from its centre
    bar_w = ln["width"] * 1.08
    bm = mat.emissive("sig_bar", "#58CC02", 2.2)
    bar = geo.slab("sig_bar", c, bar_w, 0.03, 0.03, R=0.015, rb=0.006, mat=bm, loc=(0, sig_y - 0.28, 0.0), parent=root)
    g = smootherstep(u(t, on0 + 0.20, on0 + 0.75))
    anim.key_vec(bar, "scale", fr, np.stack([np.maximum(g, 1e-4), np.ones_like(g), np.ones_like(g)], 1))
    ctx.ev("signature", on0)
    # camera: nearly still; a hair of pull-back so the screen breathes out
    D0 = 14.3 if not P else 6.4
    lens = 35.0 if not P else 24.0
    ty = -0.9 if not P else -1.0
    ctx.cam(20.20, F8.p(0.0, 0.58, D0 - 0.78), F8.p(0, ty + 0.35, 0.0), lens=lens, fstop=5.0, focus=None, tension=0.0)
    ctx.cam(21.20, F8.p(0.0, 0.58, D0 - 0.78), F8.p(0, ty + 0.35, 0.0), lens=lens, fstop=5.0, focus=None, tension=0.0)
    return dict()

"""Build context shared by every scene module (runs inside bpy)."""
from __future__ import annotations

import numpy as np
import bpy

from . import geo
from .config import FORMATS, FPS, N_FRAMES


class Ctx:
    def __init__(self, fmt: str):
        self.fmt = fmt
        self.portrait = fmt == "v"
        self.W, self.H = FORMATS[fmt]["w"], FORMATS[fmt]["h"]
        self.aspect = self.W / self.H
        self.cam_keys: list[dict] = []
        self.events: list[dict] = []
        self.windows: dict[str, tuple[float, float]] = {}
        self.colls: dict[str, bpy.types.Collection] = {}
        self.shakes: list[dict] = []
        self.mats: dict[str, bpy.types.Material] = {}
        self.objs: dict[str, bpy.types.Object] = {}
        self.static_points: list = []     # (t, xyz) of things the camera should avoid / dust seeding
        self.state: dict = {}             # cross-scene hand-offs (thread end points, frames...)
        self.tints: list[dict] = []       # ambient colour influences that ride with the camera
        self.scene = bpy.context.scene

    # ------------------------------------------------------------ collections
    def coll(self, name: str, window: tuple[float, float] | None = None):
        c = self.colls.get(name)
        if c is None:
            c = geo.new_collection(name)
            self.colls[name] = c
        if window is not None:
            self.windows[name] = window
        return c

    # ------------------------------------------------------------ sync events (audio cues)
    def ev(self, kind: str, t: float, **kw):
        self.events.append(dict(kind=kind, t=float(t), **kw))

    # ------------------------------------------------------------ camera keys
    def cam(self, t, pos, tgt, lens=35.0, roll=0.0, fstop=4.0, focus=None, tension=1.0):
        """Add a key on the single camera trajectory.

        ``focus``: None -> distance to target; float -> metres; tuple -> world point.
        ``tension`` 1 = flow through the key, 0 = come to rest on it.
        """
        self.cam_keys.append(dict(t=float(t), pos=tuple(map(float, pos)), tgt=tuple(map(float, tgt)),
                                  lens=float(lens), roll=float(roll), fstop=float(fstop),
                                  focus=focus, tension=float(tension)))

    def tint(self, t0, t1, color, energy, attack=0.15, release=0.4):
        """Ambient colour influence (a big soft light riding with the camera) between t0 and t1."""
        self.tints.append(dict(t0=float(t0), t1=float(t1), color=tuple(color), energy=float(energy), attack=attack, release=release))

    def shake(self, t0, amp, freq=7.0, decay=9.0, dur=0.6):
        """Directional damped camera impulse (amp = world-space vector, metres)."""
        self.shakes.append(dict(t0=float(t0), amp=tuple(map(float, amp)), freq=freq, decay=decay, dur=dur))

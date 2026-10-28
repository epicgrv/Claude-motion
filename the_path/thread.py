"""The light thread: one luminous object that travels the whole film.

It is a real 3-D tube (emissive core + faint halo tube) whose visible span is driven by the
curve's bevel factors, plus a ``Head`` (bead + practical point light) that lights nearby
surfaces with the thread's current colour - so a button the line passes gets a green rim and
the flame ignition throws orange, exactly as the brief's lighting rules ask.
"""
from __future__ import annotations

import bpy
import numpy as np

from . import anim, geo, mat
from .config import FPS, N_FRAMES, lin
from .easing import GLIDE, Polyline, clamp, smootherstep, u


def profile(keys):
    """Monotone C1 speed profile: [(t, frac_of_length), ...] -> callable t -> frac (clamped)."""
    from scipy.interpolate import PchipInterpolator
    ts = np.array([k[0] for k in keys], float)
    fs = np.array([k[1] for k in keys], float)
    pc = PchipInterpolator(ts, fs)

    def f(t):
        t = np.asarray(t, float)
        return np.where(t <= ts[0], fs[0], np.where(t >= ts[-1], fs[-1], pc(np.clip(t, ts[0], ts[-1]))))

    f.absolute = True
    return f


def thread_mats(ctx):
    if "th_core" in ctx.mats:
        return ctx.mats["th_core"], ctx.mats["th_halo"]
    out = []
    for nm, col, st in (("th_core", "#A8FF5A", 7.0), ("th_halo", "#58CC02", 1.1)):
        m = mat.emissive(nm, col, st)
        nt = m.node_tree
        # facing falloff: bright spine, softer rim -> reads as a volumetric energy object
        lw = nt.nodes.new("ShaderNodeLayerWeight")
        lw.inputs["Blend"].default_value = 0.55
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = 0.0
        mr.inputs["From Max"].default_value = 1.0
        mr.inputs["To Min"].default_value = 1.0
        mr.inputs["To Max"].default_value = 0.35 if nm == "th_core" else 0.15
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        mul.name = "M"
        nt.links.new(lw.outputs["Facing"], mr.inputs["Value"])
        nt.links.new(mr.outputs["Result"], mul.inputs[0])
        mul.inputs[1].default_value = st
        nt.links.new(mul.outputs["Value"], nt.nodes["E"].inputs["Strength"])
        ctx.mats[nm] = m
        out.append(m)
    return out


class Segment:
    """A stretch of thread along a dense polyline, revealed between t0 and t1."""

    def __init__(self, ctx, name, coll, pts, t0, t1, ease=GLIDE, radius=0.035, tail=None,
                 fade=None, halo=3.0, strength=1.0, retract=None):
        core_m, halo_m = thread_mats(ctx)
        self.pl = Polyline(np.asarray(pts, float))
        self.t0, self.t1, self.ease, self.tail = t0, t1, ease, tail
        self.fade = fade        # (t_start, t_end): tail catches the head -> thread consumed from behind
        self.retract = retract  # (t_start, t_end): the tip runs back to the start (energy flowing home)
        self.core = geo.tube(f"{name}_core", coll, self.pl.pts, radius, core_m, resolution=6)
        self.halo = geo.tube(f"{name}_halo", coll, self.pl.pts, radius * halo, halo_m, resolution=5)
        for o in (self.core, self.halo):
            o.data.bevel_factor_start = 0.0
        f0 = int(t0 * FPS) - 1
        f1 = (int(max(fade[1] if fade else t1, retract[1] if retract else t1) * FPS) + 2)
        f0, f1 = max(0, f0), min(N_FRAMES - 1, f1)
        fr = np.arange(f0, f1 + 1)
        tt = fr / FPS
        head = self.head_frac(tt)
        start = self.start_frac(tt, head)
        for o in (self.core, self.halo):
            anim.key(o.data, "bevel_factor_end", fr, head)
            anim.key(o.data, "bevel_factor_start", fr, start)
        self.frames = fr

    def head_frac(self, t):
        t = np.asarray(t, dtype=float)
        if getattr(self.ease, "absolute", False):
            h = np.asarray(self.ease(t), dtype=float)
        else:
            h = np.asarray(self.ease(u(t, self.t0, self.t1)), dtype=float)
        if self.retract:
            h = h * (1 - smootherstep(u(t, *self.retract)))
        return h

    def start_frac(self, t, head=None):
        head = self.head_frac(t) if head is None else head
        L = self.pl.length
        st = np.zeros_like(head)
        if self.tail:
            st = np.maximum(0.0, head - self.tail / L)
        if self.fade:
            k = u(t, *self.fade)
            st = np.maximum(st, head * k + st * (1 - k)) if self.tail else head * k
        return np.minimum(st, head)

    def head_pos(self, t):
        return self.pl.frac(self.head_frac(t))

    def head_dir(self, t):
        return self.pl.tangent(self.head_frac(t) * self.pl.length)


class Head:
    """Bead + practical light that rides the thread tip."""

    def __init__(self, ctx, name, coll, radius=0.07):
        self.bead_mat = mat.emissive(f"{name}_bead", "#E8FFC4", 14.0)
        self.bead = geo.sphere(f"{name}_bead", coll, radius, mat=self.bead_mat, seg=20, rings=10)
        self.light = geo.point_light(f"{name}_light", coll, lin("mask"), 0.0, radius=0.12)
        self.r = radius

    def key(self, frames, pos, size=None, power=None, color=None, bead_strength=None):
        n = len(frames)
        anim.key_vec(self.bead, "location", frames, pos)
        anim.key_vec(self.light, "location", frames, pos)
        if size is not None:
            s = np.broadcast_to(np.asarray(size, float), (n,)) * self.r
            anim.key_vec(self.bead, "scale", frames, np.stack([s, s, s], 1))
        if power is not None:
            anim.key(self.light.data, "energy", frames, np.broadcast_to(np.asarray(power, float), (n,)))
        if color is not None:
            col = np.asarray(color, float)
            anim.key_vec(self.light.data, "color", frames, np.broadcast_to(col, (n, 3)))
        if bead_strength is not None:
            anim.key(self.bead_mat.node_tree, 'nodes["E"].inputs["Strength"].default_value', frames,
                     np.broadcast_to(np.asarray(bead_strength, float), (n,)))

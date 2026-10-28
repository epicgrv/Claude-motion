"""Physical effects: shard bursts (ballistic with drag) and expanding shock-wave rings."""
from __future__ import annotations

import math

import numpy as np

from . import anim, geo, mat
from .config import FPS, lin
from .easing import out_cubic, smoothstep, u


def burst(ctx, coll, name, t0, origin, n=24, spd=(2.0, 9.0), size=(0.012, 0.035), life=(0.3, 0.6), axis=(0, -1, 0),
          cone=1.0, color="#9CFF52", strength=9.0, drag=6.0, seed=0, ring=(0.1, 0.6), stretch=2.4, gravity=(0, 0, 0),
          mat_=None):
    """Spray ``n`` glowing shards from ``origin``; they exist only between spawn and burn-out
    (scale 0 before/after - nothing pops via opacity)."""
    rng = np.random.default_rng(seed)
    m = mat_ or mat.emissive(f"{name}_m", color, strength)
    ax = np.asarray(axis, float)
    ax = ax / np.linalg.norm(ax)
    helper = np.array([0, 0, 1.0]) if abs(ax[2]) < 0.9 else np.array([1.0, 0, 0])
    e1 = np.cross(ax, helper)
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(ax, e1)
    objs = []
    for i in range(n):
        a = rng.uniform(0, 2 * math.pi)
        r0 = rng.uniform(*ring)
        p0 = np.asarray(origin, float) + (e1 * math.cos(a) + e2 * math.sin(a)) * r0
        lat = (e1 * math.cos(a) + e2 * math.sin(a)) * rng.uniform(0.3, 1.0)
        v = (ax * rng.uniform(0.15, 1.0) * cone + lat) * rng.uniform(*spd)
        lf = rng.uniform(*life)
        sz = rng.uniform(*size)
        o = geo.sphere(f"{name}{i}", coll, (sz, sz, sz * stretch), mat=m, seg=10, rings=6)
        o.rotation_euler = geo.Vector(v).to_track_quat("Z", "Y").to_euler()
        f0 = int(round(t0 * FPS))
        fs = np.arange(f0, f0 + int(lf * FPS) + 2)
        ts = (fs - f0) / FPS
        d = (1 - np.exp(-drag * ts)) / drag
        pp = p0[None] + v[None] * d[:, None] + 0.5 * np.asarray(gravity)[None] * (ts ** 2)[:, None]
        shrink = 1 - smoothstep(u(ts, lf * 0.35, lf))
        anim.key_vec(o, "location", fs, pp)
        anim.key_vec(o, "scale", fs, np.stack([sz * shrink, sz * shrink, sz * stretch * shrink], 1))
        anim.key_vec(o, "scale", np.array([0, max(f0 - 1, 0)]), np.zeros((2, 3)))
        anim.key_vec(o, "location", np.array([0, max(f0 - 1, 0)]), np.repeat(p0[None], 2, 0))
        objs.append(o)
    return objs


def shockwave(ctx, coll, name, t0, frame_obj_loc, normal_euler, r0=0.5, r1=7.0, dur=0.30, tube=0.02,
              color="#B8FF7A", strength=6.0, delay=0.0):
    """Expanding ring (a thin torus that thins as it grows) lying in the plane normal to local Z."""
    m = mat.emissive(f"{name}_m", color, strength)
    ring = geo.torus(name, coll, 1.0, tube, m, loc=tuple(frame_obj_loc), seg_major=128, seg_minor=8)
    ring.rotation_euler = normal_euler
    f0 = int(round((t0 + delay) * FPS))
    fs = np.arange(f0, f0 + int(dur * FPS) + 4)
    ts = (fs - f0) / FPS
    k = out_cubic(np.clip(ts / dur, 0, 1))
    R = r0 + (r1 - r0) * k
    thin = 1 - 0.85 * k
    # scale.xy = radius, scale.z = tube thickness factor relative to radius
    zscale = np.maximum(thin / np.maximum(R, 1e-3) * r0, 0.05)
    anim.key_vec(ring, "scale", fs, np.stack([R, R, R * thin], 1))
    anim.key_vec(ring, "scale", np.array([0, max(f0 - 1, 0)]), np.zeros((2, 3)))
    anim.key(m.node_tree, 'nodes["E"].inputs["Strength"].default_value', fs, strength * (1 - smoothstep(u(ts, dur * 0.2, dur * 1.1))))
    return ring

"""Keyframing for Blender >= 5.0 (slotted actions). Per-frame sampled curves, LINEAR interpolation.

The film is authored as analytic functions of time (springs, splines, easings). We bake them
to one key per frame so that Cycles' real motion blur sees the true motion and nothing is
re-interpreted by Blender's own handles.

Usage: call ``key``/``key_vec`` freely while building the scene, then ``flush()`` once.
Later segments override earlier ones where frames overlap.
"""
from __future__ import annotations

import math

import numpy as np
import bpy

_PENDING: dict = {}   # (id_ptr, data_path, index) -> dict(idb, frames[], values[])


def reset():
    _PENDING.clear()


def key(idb, data_path: str, frames, values, index: int = -1):
    """Record ``values`` at ``frames`` for ``data_path`` (``index`` for array props, -1 = scalar)."""
    frames = np.atleast_1d(np.asarray(frames, dtype=float))
    values = np.atleast_1d(np.asarray(values, dtype=float))
    assert frames.shape == values.shape, (data_path, frames.shape, values.shape)
    k = (idb.as_pointer(), data_path, index)
    d = _PENDING.get(k)
    if d is None:
        d = _PENDING[k] = dict(idb=idb, f=[], v=[])
    d["f"].append(frames)
    d["v"].append(values)


def key_vec(idb, data_path: str, frames, vecs):
    vecs = np.asarray(vecs, dtype=float)
    for i in range(vecs.shape[1]):
        key(idb, data_path, frames, vecs[:, i], index=i)


def sample(func, f0: int, f1: int, fps: float = 60.0):
    """Evaluate func(t_array) at frames f0..f1 inclusive -> (frames, values)."""
    frames = np.arange(f0, f1 + 1)
    return frames, np.asarray(func(frames / fps))


def flush():
    """Bake every recorded curve into slotted actions."""
    actions: dict = {}
    for (ptr, path, index), d in _PENDING.items():
        idb = d["idb"]
        st = actions.get(ptr)
        if st is None:
            act = bpy.data.actions.new(f"A_{idb.name}")
            slot = act.slots.new(id_type=idb.id_type, name=idb.name)
            layer = act.layers.new("L")
            strip = layer.strips.new(type="KEYFRAME")
            bag = strip.channelbag(slot, ensure=True)
            if idb.animation_data is None:
                idb.animation_data_create()
            idb.animation_data.action = act
            idb.animation_data.action_slot = slot
            st = actions[ptr] = bag
        f = np.concatenate(d["f"])
        v = np.concatenate(d["v"])
        # later segments win on duplicate frames: stable sort keeps insertion order for ties
        order = np.argsort(f, kind="stable")
        f, v = f[order], v[order]
        keep = np.ones(len(f), bool)
        keep[:-1] = f[:-1] != f[1:]          # last of each run of equal frames wins
        f, v = f[keep], v[keep]
        fc = st.fcurves.new(path, index=max(index, 0))
        n = len(f)
        fc.keyframe_points.add(n)
        co = np.empty(2 * n)
        co[0::2] = f
        co[1::2] = v
        fc.keyframe_points.foreach_set("co", co)
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
        fc.update()
    _PENDING.clear()


def lookat_euler(pos, target, roll_deg=0.0, prev=None):
    """Blender camera Euler (XYZ) looking from pos to target (camera looks down -Z, up +Y)."""
    from mathutils import Vector, Matrix
    p = Vector(pos)
    f = Vector(target) - p
    if f.length < 1e-9:
        f = Vector((0, 1, 0))
    f.normalize()
    up = Vector((0, 0, 1))
    r = f.cross(up)
    if r.length < 1e-6:
        r = Vector((1, 0, 0))
    r.normalize()
    u = r.cross(f)
    if roll_deg:
        c, s = math.cos(math.radians(roll_deg)), math.sin(math.radians(roll_deg))
        r, u = r * c + u * s, u * c - r * s
    m = Matrix(((r.x, u.x, -f.x), (r.y, u.y, -f.y), (r.z, u.z, -f.z)))
    return m.to_euler("XYZ", prev) if prev is not None else m.to_euler("XYZ")

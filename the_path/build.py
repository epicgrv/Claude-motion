"""Assemble the whole film inside Blender (one call per aspect ratio)."""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import bpy
import numpy as np

from . import anim, camera, env, geo
from .config import FPS, N_FRAMES, OUT
from .ctx import Ctx

SCENE_MODULES = [
    "s01_impact", "s02_universe", "s03_interface", "s04_streak", "s05_league",
    "s06_call", "s07_skills", "s08_idea", "s09_close", "s10_signature",
]


def build(fmt: str, scenes=None, spp=None, threads=0, scale=100, preview=False):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    anim.reset()
    geo.reset()
    from . import duo as _duo, mat as _mat
    _duo._MATS.clear()
    ctx = Ctx(fmt)
    env.setup_render(ctx, spp, threads, scale)
    env.setup_world(ctx)
    for name in (scenes or SCENE_MODULES):
        try:
            mod = importlib.import_module(f"the_path.scenes.{name}")
        except ModuleNotFoundError as e:
            if e.name and e.name.endswith(name):
                print(f"[build] scene module {name} not present yet - skipped")
                continue
            raise
        print(f"[build] {name}")
        mod.build(ctx)
    camera.build(ctx)
    env.camera_rig(ctx)
    env.far_field(ctx)
    env.animate_far(ctx)
    ctx.dust_objs = env.dust(ctx)
    anim.flush()
    for m in bpy.data.materials:          # emission is for what the camera sees, not for sampling as lights (practical lights do the lighting)
        m.cycles.emission_sampling = "NONE"
    for o in bpy.data.objects:
        if o.type in ("MESH", "FONT", "CURVE"):
            o.cycles.use_camera_cull = True
    ctx.scene.frame_set(0)
    if preview:
        ctx.scene.view_settings.view_transform = "AgX"
    return ctx


# ------------------------------------------------------------------ per-frame visibility
def _layer_coll(lc, name):
    if lc.name == name:
        return lc
    for ch in lc.children:
        r = _layer_coll(ch, name)
        if r:
            return r
    return None


def apply_windows(ctx, frame: int, margin=2.0 / FPS):
    t = frame / FPS
    root = bpy.context.view_layer.layer_collection
    for name, (t0, t1) in ctx.windows.items():
        lc = _layer_coll(root, name)
        if lc is not None:
            lc.exclude = not (t0 - margin <= t <= t1 + margin)
    for o in getattr(ctx, "dust_objs", []):
        w = o.get("win")
        if w:
            o.hide_render = not (w[0] <= t <= w[1])


def dump_events(ctx, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    ev = sorted(ctx.events, key=lambda e: e["t"])
    Path(path).write_text(json.dumps(ev, indent=1))

"""True-3D shots: animated Blender camera + animated props, with 2D characters placed into the 3D world.

For a shot we render (Cycles, 720x1280 by default):
  plates/shots/<id>/####.png      beauty frames (motion blur, denoised)
  plates/shots/<id>/m####.png     occluder mask (white = scene objects that stand in front of characters)
  plates/shots/<id>/anchors.json  per frame: screen x,y (0..1) + pixels-per-metre for each named 3D anchor point
The compositor draws a frame, places characters at their projected anchors (scaled by perspective), then redraws
the occluders on top using the mask - exactly the "2D cut-out in a 3D engine" look.

    python -m finance_shorts.engine.shot3d <shot_id>      (shot specs live in finance_shorts/engine/shots3d_pepsi.py)
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

from finance_shorts.engine import set3d

SHOTS = set3d.OUT / "shots"


def _empty(name, loc):
    e = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(e)
    e.location = loc
    return e


def setup_camera(cam_keys, tgt_keys, lens):
    """cam_keys/tgt_keys: [(frame, (x,y,z)), ...]; camera tracks an animated target (smooth bezier)."""
    sc = bpy.context.scene
    cam = sc.camera
    cam.constraints.clear()
    cam.animation_data_clear()
    cam.data.lens = lens
    tgt = _empty("ShotTarget", tgt_keys[0][1])
    for f, p in cam_keys:
        cam.location = p
        cam.keyframe_insert("location", frame=f)
    for f, p in tgt_keys:
        tgt.location = p
        tgt.keyframe_insert("location", frame=f)
    con = cam.constraints.new("TRACK_TO")
    con.target = tgt
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"
    return cam


def export_anchors(cam, anchors, frames, path):
    sc = bpy.context.scene
    out = {"res": [sc.render.resolution_x, sc.render.resolution_y], "frames": []}
    for f in range(frames):
        sc.frame_set(f)
        row = {}
        for name, p in anchors.items():
            obj = bpy.data.objects.get(name)
            pw = obj.matrix_world.translation.copy() if obj else Vector(p)
            a = world_to_camera_view(sc, cam, pw)
            b = world_to_camera_view(sc, cam, pw + Vector((0, 0, 1.0)))
            ppm = math.hypot((b.x - a.x) * sc.render.resolution_x, (b.y - a.y) * sc.render.resolution_y)
            row[name] = [a.x, 1 - a.y, ppm / sc.render.resolution_y, a.z]  # ppm as fraction of frame height
        out["frames"].append(row)
    path.write_text(json.dumps(out))


def render_beauty(folder, frames, spp, res):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.5
    sc.render.use_persistent_data = True  # keep static geometry/BVH between frames
    sc.cycles.samples = spp
    sc.cycles.use_adaptive_sampling = False
    sc.cycles.use_denoising = True
    sc.render.fps = 30
    sc.frame_start, sc.frame_end = 0, frames - 1
    sc.render.image_settings.file_format = "PNG"
    sc.render.filepath = str(folder / "####")
    bpy.ops.render.render(animation=True)


def render_masks(folder, frames, occluders):
    """Flat Workbench pass: occluder objects white, everything else black."""
    sc = bpy.context.scene
    occ = set3d._descendants(occluders) if occluders else set()
    for ob in bpy.data.objects:
        if ob.type == "MESH":
            ob.color = (1, 1, 1, 1) if ob in occ else (0, 0, 0, 1)
    sc.render.engine = "BLENDER_WORKBENCH"
    sh = sc.display.shading
    sh.light = "FLAT"
    sh.color_type = "OBJECT"
    sh.show_shadows = False
    sh.show_cavity = False
    sh.show_object_outline = False
    sc.display.render_aa = "8"
    sc.render.use_motion_blur = False
    sc.world.color = (0, 0, 0)
    sc.render.film_transparent = False
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "BW"
    sc.render.filepath = str(folder / "m####")
    sc.frame_start, sc.frame_end = 0, frames - 1
    bpy.ops.render.render(animation=True)


def build_and_render(spec: dict, shot_id: str):
    from finance_shorts.engine import sets_pepsi
    set3d.reset()
    getattr(sets_pepsi, spec["set"])()
    frames = spec["frames"]
    cam = setup_camera(spec["cam"], spec["target"], spec.get("lens", 24))
    for name, p in spec.get("anchors", {}).items():
        if not bpy.data.objects.get(name):
            _empty(name, p)
    if spec.get("anim"):
        from finance_shorts.engine import shots3d_pepsi
        getattr(shots3d_pepsi, spec["anim"])(frames)
    folder = SHOTS / shot_id
    folder.mkdir(parents=True, exist_ok=True)
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = tuple(spec.get("res", (720, 1280)))
    sc.render.resolution_percentage = 100
    export_anchors(cam, spec.get("anchors", {}), frames, folder / "anchors.json")
    render_beauty(folder, frames, spec.get("spp", 8), tuple(spec.get("res", (720, 1280))))
    if spec.get("occluders"):
        render_masks(folder, frames, spec["occluders"])


def main():
    from finance_shorts.engine import shots3d_pepsi
    sid = sys.argv[1]
    build_and_render(shots3d_pepsi.SPECS[sid], sid)


if __name__ == "__main__":
    main()

"""Render a range of frames of one master inside Blender.

    python -m the_path.render_worker --fmt h --frames 0-1271 --outdir out/exr/h
    python -m the_path.render_worker --fmt h --frames 60,66,72 --preview --scale 50 --spp 12

Production writes multilayer EXR (scene-linear half-float beauty + depth) through the
compositor File Output node; ``--preview`` writes display-referred PNGs for quick inspection.
Resumable: existing frames are skipped.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import bpy

from . import build as B
from .config import FPS, N_FRAMES, OUT


def parse_frames(spec: str):
    out = []
    for part in spec.split(","):
        if "-" in part and not part.startswith("-"):
            a, b = part.split("-")
            step = 1
            if ":" in b:
                b, step = b.split(":")
            out += list(range(int(a), int(b) + 1, int(step)))
        else:
            out.append(int(part))
    return out


def setup_exr_output(ctx, outdir: Path):
    sc = ctx.scene
    ng = bpy.data.node_groups.new("Comp", "CompositorNodeTree")
    sc.compositing_node_group = ng
    sc.render.compositor_device = "CPU"
    rl = ng.nodes.new("CompositorNodeRLayers")
    fo = ng.nodes.new("CompositorNodeOutputFile")
    fo.directory = str(outdir)
    fo.file_name = "f_"
    fo.format.file_format = "OPEN_EXR_MULTILAYER"
    fo.format.color_depth = "16"
    fo.format.exr_codec = "DWAA"
    fo.file_output_items.new("RGBA", "Beauty")
    fo.file_output_items.new("FLOAT", "Depth")
    ng.links.new(rl.outputs["Image"], fo.inputs["Beauty"])
    ng.links.new(rl.outputs["Depth"], fo.inputs["Depth"])
    return fo


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--fmt", default="h", choices=["h", "v"])
    ap.add_argument("--frames", default="0-1271")
    ap.add_argument("--outdir", default=None)
    ap.add_argument("--spp", type=int, default=None)
    ap.add_argument("--threads", type=int, default=0)
    ap.add_argument("--scale", type=int, default=100)
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--scenes", default=None, help="comma list of scene modules (default: all)")
    ap.add_argument("--events", default=None, help="write sync events json and exit")
    a = ap.parse_args(argv)
    ctx = B.build(a.fmt, scenes=a.scenes.split(",") if a.scenes else None, spp=a.spp, threads=a.threads,
                  scale=a.scale, preview=a.preview)
    if a.events:
        B.dump_events(ctx, a.events)
        print("events ->", a.events)
        return
    sc = ctx.scene
    frames = parse_frames(a.frames)
    outdir = Path(a.outdir or (OUT / ("preview" if a.preview else "exr") / a.fmt))
    outdir.mkdir(parents=True, exist_ok=True)
    exrdir = outdir / "exr" if a.preview else outdir
    exrdir.mkdir(parents=True, exist_ok=True)
    fo = setup_exr_output(ctx, exrdir)
    t_all = time.time()
    done = 0
    for f in frames:
        target = exrdir / f"f_{f:04d}.exr"
        if target.exists() and not a.preview:
            continue
        if target.exists():
            target.unlink()
        t0 = time.time()
        fo.file_name = f"f_{f:04d}"
        sc.frame_set(f)
        B.apply_windows(ctx, f)
        bpy.ops.render.render(write_still=False)
        if a.preview:
            from . import post
            post.exr_to_png(target, outdir / f"p_{f:04d}.png", f)
        done += 1
        print(f"[render] frame {f:4d} {time.time() - t0:5.1f}s  ({done}/{len(frames)})", flush=True)
    print(f"[render] done {done} frames in {time.time() - t_all:.0f}s")


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    main(argv)

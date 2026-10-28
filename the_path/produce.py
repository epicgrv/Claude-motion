"""Frames (EXR) -> finished master (MP4 with the mastered audio).

    python -m the_path.produce --fmt h            # needs out/exr/h/f_*.exr and out/audio/master.wav
Frames after STATIC_FROM share one render (the end card is deliberately still); every output frame still gets
its own film grain, so the picture stays alive without any animation.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np

from . import post
from .config import FORMATS, FPS, N_FRAMES, OUT

STATIC_FROM = 1212          # 20.20 s: signature is lit, camera at rest


def src_index(f):
    return min(f, STATIC_FROM)


def _work(args):
    f, exr, size, sharpen = args
    b, d = post.read_exr(exr)
    return post.process(b, d, f, post.frame_params(f), size=size, sharpen=sharpen).tobytes()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--fmt", default="h")
    ap.add_argument("--exrdir", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--frames", default=None, help="a-b (test clips)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--crf", type=int, default=19)
    ap.add_argument("--preset", default="medium")
    ap.add_argument("--sharpen", type=float, default=0.30)
    ap.add_argument("--noaudio", action="store_true")
    a = ap.parse_args(argv)
    W, H = FORMATS[a.fmt]["w"], FORMATS[a.fmt]["h"]
    exrdir = Path(a.exrdir or OUT / "exr" / a.fmt)
    f0, f1 = (0, N_FRAMES - 1)
    if a.frames:
        f0, f1 = map(int, a.frames.split("-"))
    out = Path(a.out or OUT / "final" / f"THE_PATH_{FORMATS[a.fmt]['name']}_{W}x{H}_60fps.mp4")
    out.parent.mkdir(parents=True, exist_ok=True)
    audio = OUT / "audio" / "master.wav"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    if not a.noaudio and audio.exists():
        cmd += ["-i", str(audio)]
    cmd += ["-c:v", "libx264", "-preset", a.preset, "-crf", str(a.crf), "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "5.1",
            "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
            "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
            "-r", str(FPS), "-g", "60", "-movflags", "+faststart"]
    if not a.noaudio and audio.exists():
        cmd += ["-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-shortest"]
    cmd += [str(out)]
    jobs = []
    for f in range(f0, f1 + 1):
        exr = exrdir / f"f_{src_index(f):04d}.exr"
        if not exr.exists():
            sys.exit(f"missing {exr}")
        jobs.append((f, str(exr), (W, H), a.sharpen))
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    with Pool(a.workers) as pool:
        for i, buf in enumerate(pool.imap(_work, jobs, chunksize=2)):
            ff.stdin.write(buf)
            if i % 100 == 0:
                print(f"[produce] {i}/{len(jobs)} {time.time() - t0:.0f}s", flush=True)
    ff.stdin.close()
    ff.wait()
    print("[produce] wrote", out)


if __name__ == "__main__":
    main()

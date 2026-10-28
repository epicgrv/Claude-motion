"""Technical QC of a finished master: duration / resolution / fps / frame count / integrity, accidental black
frames, camera continuity (no teleports), audio loudness + true peak, audio/picture sync of the impact, key-frame
contact sheet. Writes out/final/qc_<fmt>.json and prints a table. Exit code 1 if any hard check fails.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

from ..config import FORMATS, FPS, N_FRAMES, OUT, TOTAL


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def probe(path):
    r = sh(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
            "stream=width,height,r_frame_rate,nb_read_frames,pix_fmt,codec_name,color_space:format=duration", "-of", "json", str(path)])
    js = json.loads(r.stdout)
    s, f = js["streams"][0], js["format"]
    a = sh(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_name,sample_rate,channels,duration", "-of", "json", str(path)])
    aj = json.loads(a.stdout)["streams"]
    return s, f, (aj[0] if aj else None)


def luma_series(path, w=96):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf", f"scale={w}:-2,format=gray", "-f", "rawvideo", "-"], capture_output=True)
    buf = np.frombuffer(r.stdout, np.uint8)
    s = sh(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", str(path)]).stdout.strip().split(",")
    ar = int(s[1]) / int(s[0])
    h = int(round(w * ar / 2) * 2)
    return buf[: len(buf) // (w * h) * (w * h)].reshape(-1, h, w).astype(np.float32)


def run(fmt):
    W, H = FORMATS[fmt]["w"], FORMATS[fmt]["h"]
    path = OUT / "final" / f"THE_PATH_{FORMATS[fmt]['name']}_{W}x{H}_60fps.mp4"
    rep, fails = {}, []
    s, f, a = probe(path)
    dur = float(f["duration"])
    nb = int(s["nb_read_frames"])
    rep.update(file=str(path), width=s["width"], height=s["height"], fps=s["r_frame_rate"], frames=nb, duration=dur, codec=s["codec_name"],
               pix_fmt=s["pix_fmt"], audio=a)

    def chk(name, ok, detail=""):
        rep.setdefault("checks", {})[name] = dict(ok=bool(ok), detail=detail)
        if not ok:
            fails.append(name)

    chk("duration_21.2s", abs(dur - TOTAL) < 0.04, f"{dur:.3f}s")
    chk("resolution", (s["width"], s["height"]) == (W, H), f"{s['width']}x{s['height']}")
    chk("fps_60", s["r_frame_rate"] == "60/1", s["r_frame_rate"])
    chk("frame_count_1272", nb == N_FRAMES, str(nb))
    chk("audio_present", a is not None and int(a["sample_rate"]) == 48000, str(a))
    dec = sh(["ffmpeg", "-v", "error", "-i", str(path), "-f", "null", "-"])
    chk("stream_integrity", dec.stderr.strip() == "", dec.stderr[:200])
    L = luma_series(path)
    mean = L.mean(axis=(1, 2))
    black = np.where(mean < 2.0)[0]
    chk("no_accidental_black_frames", len(black) == 0, f"{len(black)} frames < 2/255: {black[:10].tolist()}")
    # abrupt global luminance jumps (cuts / popping) - the impact and flame ignition are intended, so list, don't fail
    dm = np.abs(np.diff(mean))
    jumps = np.where(dm > 18)[0]
    rep["big_luma_jumps_frames"] = jumps.tolist()
    # camera continuity (from the build's solved camera path)
    cam = OUT / "audio" / f"events_{fmt}.cam.npz"
    if cam.exists():
        d = np.load(cam)
        v = np.linalg.norm(np.diff(d["pos"], axis=0), axis=1)
        dirs = d["tgt"] - d["pos"]
        dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
        ang = np.degrees(np.arccos(np.clip(np.sum(dirs[1:] * dirs[:-1], axis=1), -1, 1)))
        rep["camera"] = dict(max_step_m=float(v.max()), max_step_frame=int(v.argmax()), max_turn_deg_per_frame=float(ang.max()), max_turn_frame=int(ang.argmax()))
        chk("camera_continuous_no_teleport", v.max() < 6.0 and ang.max() < 12.0, f"max {v.max():.2f} m/frame, {ang.max():.1f} deg/frame")
    # audio loudness on the muxed file
    r = sh(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"])
    tail = r.stderr.split("Summary:")[-1]
    lufs = float(re.search(r"I:\s+(-?[\d.]+) LUFS", tail).group(1))
    tp = float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", tail).group(1))
    chk("loudness_-14_LUFS", abs(lufs + 14) <= 0.5, f"{lufs} LUFS")
    chk("true_peak_<=-1.25", tp <= -1.2, f"{tp} dBTP")
    # sync: the low impact in the audio vs the frame where Duo hits (picture)
    mp = OUT / "audio" / "master.wav"
    if mp.exists():
        from ..audio import dsp
        x, sr = dsp.read_wav(mp)
        m = np.abs(x.mean(axis=1))
        lo = dsp.lp(x.mean(axis=1), 150)
        win = int(0.005 * sr)
        e = np.convolve(np.abs(lo) ** 2, np.ones(win) / win, "same")
        seg = e[int(0.9 * sr): int(1.5 * sr)]
        t_audio = 0.9 + np.argmax(seg > 0.25 * seg.max()) / sr
        i0, i1 = int(1.0 * FPS), int(1.5 * FPS)
        k = i0 + int(np.argmax(np.diff(mean[i0:i1 + 1]) ** 2))
        t_pic = (k + 1) / FPS
        rep["sync_impact"] = dict(audio_onset_s=float(t_audio), picture_jump_s=float(t_pic), delta_ms=float((t_audio - t_pic) * 1000))
        chk("impact_sync_within_50ms", abs(t_audio - t_pic) < 0.05, f"{(t_audio - t_pic) * 1000:.0f} ms")
    rep["fails"] = fails
    (OUT / "final" / f"qc_{fmt}.json").write_text(json.dumps(rep, indent=1, default=float))
    for k, v in rep["checks"].items():
        print(f"  [{'OK ' if v['ok'] else 'FAIL'}] {k:34s} {v['detail']}")
    return 1 if fails else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fmt", default="h")
    sys.exit(run(ap.parse_args().fmt))

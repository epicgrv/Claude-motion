"""One camera, one journey.

Scenes append keys with ``ctx.cam``; this module turns them into a single C1-continuous
trajectory (position spline + look-at target spline + roll/lens/aperture/focus splines),
adds impact shakes and a whisper of handheld drift, and bakes one key per frame.
"""
from __future__ import annotations

import math

import bpy
import numpy as np

from . import anim
from .config import FPS, N_FRAMES, RENDER
from .easing import KeySpline, noise1d, norm, smoothstep


def solve(ctx):
    """Evaluate the camera for every frame -> dict of arrays (N_FRAMES,...)."""
    keys = sorted(ctx.cam_keys, key=lambda k: k["t"])
    # drop keys closer than 1 frame (they would create a stop)
    clean = [keys[0]]
    for k in keys[1:]:
        if k["t"] - clean[-1]["t"] > 1.0 / FPS * 0.99:
            clean.append(k)
    keys = clean
    t = np.array([k["t"] for k in keys])
    pos = KeySpline(t, np.array([k["pos"] for k in keys]), [k["tension"] for k in keys])
    tgt = KeySpline(t, np.array([k["tgt"] for k in keys]), [k["tension"] for k in keys])
    lens = KeySpline(t, np.array([k["lens"] for k in keys]), [min(1.0, k["tension"]) for k in keys])
    roll = KeySpline(t, np.array([k["roll"] for k in keys]), [min(1.0, k["tension"]) for k in keys])
    fst = KeySpline(t, np.array([k["fstop"] for k in keys]), [min(1.0, k["tension"]) for k in keys])

    tt = np.arange(N_FRAMES) / FPS
    P = pos(tt)
    T = tgt(tt)
    L = lens(tt)
    R = roll(tt)
    F = np.maximum(fst(tt), 0.8)

    # focus distance: key.focus None -> |tgt-pos| ; float -> that ; tuple -> distance to world point
    fd_keys = []
    for k in keys:
        f = k["focus"]
        if f is None:
            fd_keys.append(float(np.linalg.norm(np.array(k["tgt"]) - np.array(k["pos"]))))
        elif isinstance(f, (int, float)):
            fd_keys.append(float(f))
        else:
            fd_keys.append(float(np.linalg.norm(np.array(f) - np.array(k["pos"]))))
    FD = np.maximum(KeySpline(t, np.array(fd_keys), [min(1.0, k["tension"]) for k in keys])(tt), 0.05)

    # --- handheld whisper (very small, slow) so the frame never feels locked-off
    drift = np.stack([noise1d(tt * 0.9, 11), noise1d(tt * 0.9, 12), noise1d(tt * 0.9, 13)], axis=1) * 0.012
    fwd = norm(T - P)
    P = P + drift * np.linalg.norm(T - P, axis=1, keepdims=True).clip(0.5, 8) * 0.25
    # --- impact shakes
    for s in ctx.shakes:
        dt = tt - s["t0"]
        env = np.where((dt >= 0) & (dt < s["dur"]), np.exp(-s["decay"] * np.maximum(dt, 0)), 0.0)
        osc = np.cos(2 * math.pi * s["freq"] * np.maximum(dt, 0)) * env
        amp = np.array(s["amp"])
        P = P + osc[:, None] * amp
        T = T + osc[:, None] * amp * 0.35      # target moves less -> a touch of rotation too
    return dict(pos=P, tgt=T, lens=L, roll=R, fstop=F, focus=FD)


def build(ctx):
    sc = ctx.scene
    data = solve(ctx)
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.sensor_fit = "HORIZONTAL"
    cam_data.sensor_width = 36.0
    cam_data.clip_start = 0.03
    cam_data.clip_end = 2500.0
    cam_data.dof.use_dof = True
    cam_data.dof.aperture_blades = 7
    cam = bpy.data.objects.new("Camera", cam_data)
    sc.collection.objects.link(cam)
    sc.camera = cam
    frames = np.arange(N_FRAMES)
    eul = []
    prev = None
    for i in range(N_FRAMES):
        e = anim.lookat_euler(data["pos"][i], data["tgt"][i], data["roll"][i], prev)
        prev = e
        eul.append((e.x, e.y, e.z))
    eul = np.array(eul)
    anim.key_vec(cam, "location", frames, data["pos"])
    anim.key_vec(cam, "rotation_euler", frames, eul)
    anim.key(cam_data, "lens", frames, data["lens"])
    anim.key(cam_data, "dof.aperture_fstop", frames, data["fstop"])
    anim.key(cam_data, "dof.focus_distance", frames, data["focus"])
    ctx.objs["camera"] = cam
    ctx.cam_data = data
    return cam

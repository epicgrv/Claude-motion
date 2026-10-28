"""Duo - the emotional protagonist, built as a separated rig of analytic primitives.

Local frame: origin at the floor between the feet, +Z up, front = -Y (faces a camera that looks
along +Y), +X = viewer's right.  Hierarchy:

    root ─ tilt ─ sq ─ body, belly, tufts, feet, eye rigs, beak, wing pivots

* ``root``  world placement / rotation
* ``tilt``  lean about the feet (anticipation, impacts)
* ``sq``    squash & stretch about the feet
* eyes      white eyeball + gaze rig (pupil + catch-light) + eyelid dome (blink)
* wings     shoulder pivot with flap (roll) and fold (pitch) so they can lag the torso
* jaw       lower beak hinge for speech

Official artwork is used by the brief "when available and permitted"; none is available in this
environment, so the character is rebuilt procedurally (see README, limitations).
"""
from __future__ import annotations

import math

import numpy as np

from . import anim, geo, mat
from .config import FPS
from .easing import damped_osc, in_out_cubic, noise1d, smoothstep, u

BODY_R = (0.72, 0.62, 0.78)
BODY_C = (0.0, 0.02, 0.78)
EYE_R = (0.30, 0.235, 0.31)
EYE_C = ((-0.31, -0.50, 1.14), (0.31, -0.50, 1.14))
LID_OPEN = -1.80
LID_CLOSED = 1.55

_MATS: dict = {}


def materials():
    if _MATS:
        return _MATS
    _MATS["body"] = mat.principled("duo_body", "feather", 0.40, coat=0.14, coat_rough=0.3, sheen=0.55, rvar=0.05, spec=0.5)
    _MATS["wing"] = mat.principled("duo_wing", "#4DB802", 0.44, coat=0.1, sheen=0.5, rvar=0.05)
    _MATS["belly"] = mat.principled("duo_belly", "#9AE63C", 0.5, sheen=0.6, rvar=0.05)
    _MATS["eye"] = mat.principled("duo_eye", "#F7FAFC", 0.16, coat=0.7, coat_rough=0.05)
    _MATS["pupil"] = mat.principled("duo_pupil", "#05080A", 0.06, coat=1.0, coat_rough=0.02, spec=0.8)
    _MATS["catch"] = mat.emissive("duo_catch", (1, 1, 1), 5.0)
    _MATS["beak"] = mat.principled("duo_beak", "beak", 0.30, coat=0.35, coat_rough=0.15, rvar=0.03)
    _MATS["mouth"] = mat.principled("duo_mouth", "#3A0F08", 0.5)
    return _MATS


class Duo:
    def __init__(self, ctx, name, coll, scale=1.0, unique_catch=False):
        self.ctx, self.name, self.coll = ctx, name, coll
        M = dict(materials())
        if unique_catch:
            M["catch"] = mat.clone(M["catch"], f"{name}_catch")
        self.catch_mat = M["catch"]
        self.parts = {}
        P = self.parts
        P["root"] = geo.empty(f"{name}_root", coll)
        P["tilt"] = geo.empty(f"{name}_tilt", coll, parent=P["root"])
        P["sq"] = geo.empty(f"{name}_sq", coll, parent=P["tilt"])
        sq = P["sq"]
        self.scale = scale
        P["root"].scale = (scale, scale, scale)

        def sph(nm, r, loc, m, parent=sq, seg=40, rings=20, taper=0.0):
            o = geo.sphere(f"{name}_{nm}", coll, r, mat=m, loc=loc, parent=parent, seg=seg, rings=rings, taper=taper)
            P[nm] = o
            return o

        sph("body", BODY_R, BODY_C, M["body"], seg=64, rings=32, taper=0.16)
        sph("belly", (0.52, 0.36, 0.58), (0, -0.28, 0.62), M["belly"], seg=48, rings=24)
        # ear tufts
        for s, sx in (("L", -1), ("R", 1)):
            o = sph(f"tuft{s}", (0.11, 0.09, 0.21), (sx * 0.40, 0.02, 1.50), M["wing"], seg=24, rings=12)
            o.rotation_euler = (0, math.radians(-22 * sx), 0)
        # feet
        for s, sx in (("L", -1), ("R", 1)):
            sph(f"foot{s}", (0.17, 0.23, 0.075), (sx * 0.27, -0.17, 0.065), M["beak"], seg=28, rings=14)
            for k, dx in enumerate((-0.10, 0.0, 0.10)):
                sph(f"toe{s}{k}", (0.055, 0.075, 0.045), (sx * 0.27 + dx, -0.36, 0.05), M["beak"], seg=14, rings=8)
        # eyes
        for i, s in enumerate(("L", "R")):
            ec = EYE_C[i]
            base = geo.empty(f"{name}_eye{s}", coll, loc=ec, parent=sq)
            P[f"eye{s}"] = base
            sph(f"ball{s}", EYE_R, (0, 0, 0), M["eye"], parent=base, seg=40, rings=20)
            gz = geo.empty(f"{name}_gaze{s}", coll, parent=base)
            P[f"gaze{s}"] = gz
            sph(f"pupil{s}", (0.118, 0.06, 0.130), (0, -0.215, 0), M["pupil"], parent=gz, seg=28, rings=14)
            sph(f"catch{s}", (0.034, 0.02, 0.034), (0.042, -0.262, 0.05), M["catch"], parent=gz, seg=12, rings=8)
            sph(f"catch2{s}", (0.016, 0.012, 0.016), (-0.040, -0.258, -0.045), M["catch"], parent=gz, seg=10, rings=6)
            hemi = geo.hemisphere_mesh()
            lid = bpyobj(name, f"lid{s}", hemi, M["body"], coll, base, scale=(EYE_R[0] * 1.045, EYE_R[1] * 1.12, EYE_R[2] * 1.05))
            lid.rotation_euler = (LID_OPEN, 0, 0)
            P[f"lid{s}"] = lid
        # beak + jaw
        sph("beakU", (0.15, 0.12, 0.085), (0, -0.585, 0.875), M["beak"], seg=32, rings=16)
        P["beakU"].rotation_euler = (math.radians(-12), 0, 0)
        P["jaw"] = geo.empty(f"{name}_jaw", coll, loc=(0, -0.545, 0.815), parent=sq)
        sph("beakL", (0.115, 0.09, 0.058), (0, -0.04, -0.045), M["beak"], parent=P["jaw"], seg=28, rings=14)
        sph("mouth", (0.09, 0.05, 0.03), (0, -0.012, -0.018), M["mouth"], parent=P["jaw"], seg=16, rings=8)
        # wings: shoulder pivots
        for s, sx in (("L", -1), ("R", 1)):
            piv = geo.empty(f"{name}_wing{s}", coll, loc=(sx * 0.62, 0.06, 1.0), parent=sq)
            P[f"wing{s}"] = piv
            sph(f"wingm{s}", (0.15, 0.36, 0.54), (sx * 0.11, 0, -0.42), M["wing"], parent=piv, seg=32, rings=16)
            for k, dy in enumerate((-0.15, 0.0, 0.15)):
                sph(f"wingt{s}{k}", (0.12, 0.17, 0.22), (sx * 0.11, dy * 1.15, -0.86 + (0.03 if k == 1 else 0.0)), M["wing"], parent=piv, seg=20, rings=10)
            piv.rotation_euler = (0, 0, 0)

    # ------------------------------------------------------------------ animation API
    def key(self, frames, *, pos=None, rot=None, scl=None, lean=None, squash=None, wing_l=None, wing_r=None,
            lid_l=None, lid_r=None, gaze_l=None, gaze_r=None, jaw=None, tuft=None):
        """Bake channels (arrays aligned with ``frames``). Everything optional."""
        P = self.parts
        if pos is not None:
            anim.key_vec(P["root"], "location", frames, pos)
        if rot is not None:
            anim.key_vec(P["root"], "rotation_euler", frames, rot)
        if scl is not None:
            anim.key_vec(P["root"], "scale", frames, np.asarray(scl) * self.scale)
        if lean is not None:
            anim.key_vec(P["tilt"], "rotation_euler", frames, lean)
        if squash is not None:
            anim.key_vec(P["sq"], "scale", frames, squash)
        for s, w, sx in (("L", wing_l, -1), ("R", wing_r, 1)):
            if w is not None:
                w = np.asarray(w)       # (N,2): flap(roll about Y, + = tip outward), fold(pitch about X, + = forward)
                anim.key_vec(P[f"wing{s}"], "rotation_euler", frames,
                             np.stack([w[:, 1], sx * w[:, 0], sx * 0.38 * np.ones(len(w))], axis=1))
        for s, l in (("L", lid_l), ("R", lid_r)):
            if l is not None:
                a = np.asarray(l)
                anim.key_vec(P[f"lid{s}"], "rotation_euler", frames, np.stack([a, 0 * a, 0 * a], axis=1))
        for s, g in (("L", gaze_l), ("R", gaze_r)):
            if g is not None:
                g = np.asarray(g)   # (N,2) yaw (about Z, + = viewer's right... ), pitch (about X, + = up)
                anim.key_vec(P[f"gaze{s}"], "rotation_euler", frames, np.stack([g[:, 1], 0 * g[:, 0], g[:, 0]], axis=1))
        if jaw is not None:
            j = np.asarray(jaw)
            anim.key_vec(P["jaw"], "rotation_euler", frames, np.stack([j, 0 * j, 0 * j], axis=1))
        if tuft is not None:
            tf = np.asarray(tuft)
            for s, sx in (("L", -1), ("R", 1)):
                anim.key_vec(P[f"tuft{s}"], "rotation_euler", frames,
                             np.stack([0 * tf, np.radians(-22 * sx) + sx * tf * 0.6, 0 * tf], axis=1))

    def head_pos(self):
        return np.array(BODY_C) + np.array([0, 0, 0.5])


def bpyobj(name, nm, mesh, material, coll, parent, scale=(1, 1, 1)):
    import bpy
    o = bpy.data.objects.new(f"{name}_{nm}", mesh)
    o.scale = scale
    coll.objects.link(o)
    o.parent = parent
    geo.assign(o, material)
    return o


# ---------------------------------------------------------------------- generators (pure numpy)
def blink(t, times, dur=0.14):
    """Eyelid angle series. ``times`` = blink start times. closes in 45% of dur, opens in 55%."""
    t = np.asarray(t, dtype=float)
    a = np.full_like(t, LID_OPEN)
    for t0 in times:
        x = (t - t0) / dur
        down = in_out_cubic(np.clip(x / 0.45, 0, 1))
        up = in_out_cubic(np.clip((x - 0.45) / 0.55, 0, 1))
        k = np.where(x < 0.45, down, 1 - up)
        k = np.where((x < 0) | (x > 1), 0.0, k)
        a = np.maximum(a, LID_OPEN + (LID_CLOSED - LID_OPEN) * k * 0.97) if False else a + (LID_CLOSED - LID_OPEN) * k * 0.97
    return a


def lid_rest(t, amount=0.0):
    """Constant partial lid droop (0 = wide open, 1 = ~half closed) as a base to add blinks on."""
    return np.full_like(np.asarray(t, dtype=float), LID_OPEN + amount * 1.1)


def idle(t, seed=0, rest=0.0, blinks=None, energy=1.0):
    """Breathing, sway, wing and gaze micro-motion + natural blinks. Returns dict of arrays.

    Never perfectly still: Duo must feel alive even when not speaking.
    """
    t = np.asarray(t, dtype=float)
    br = np.sin(2 * math.pi * 0.55 * t + seed) * 0.5 + 0.5
    squash = np.stack([1 - 0.008 * br * energy, 1 - 0.008 * br * energy, 1 + 0.014 * br * energy], axis=1)
    sway = np.stack([noise1d(t * 0.7, seed + 1) * 0.020, noise1d(t * 0.6, seed + 2) * 0.020, noise1d(t * 0.5, seed + 3) * 0.04], axis=1) * energy
    flapL = np.stack([noise1d(t * 1.1, seed + 4) * 0.05 + 0.10, noise1d(t * 0.9, seed + 5) * 0.04], axis=1)
    flapR = np.stack([noise1d(t * 1.0, seed + 6) * 0.05 + 0.10, noise1d(t * 0.8, seed + 7) * 0.04], axis=1)
    gz = np.stack([noise1d(t * 0.5, seed + 8) * 0.10, noise1d(t * 0.5, seed + 9) * 0.06], axis=1) * energy
    if blinks is None:
        rng = np.random.default_rng(seed + 100)
        blinks = list(np.cumsum(rng.uniform(1.6, 3.2, 12)) + rng.uniform(0, 1))
    lid = blink(t, blinks) + (lid_rest(t, rest) - LID_OPEN)
    return dict(squash=squash, lean=sway, wing_l=flapL, wing_r=flapR, gaze=gz, lid=lid)


def flap_pulse(t, t0, n=2, period=0.22, amp=0.9, decay=3.0):
    """Wing flap burst: (N,2) flap/fold; right wing uses a small time offset elsewhere."""
    t = np.asarray(t, dtype=float)
    out = np.zeros_like(t)
    tt = t - t0
    m = (tt >= 0) & (tt < n * period * 1.8)
    out = np.where(m, amp * np.exp(-decay * tt.clip(0)) * np.sin(2 * math.pi * tt.clip(0) / period) ** 2, 0.0) * 1.0
    return out


def squash_stretch(sx_target, sy_target, sz_target):
    """Volume-preserving helper: given sz, return (sx, sy) with sx*sy*sz = 1."""
    return None


def mount(D, parent, loc=(0, 0, 0)):
    """Place a Duo inside a UI-style frame (+Y up, +Z toward the viewer): returns the holder empty."""
    holder = geo.empty(f"{D.name}_holder", D.coll, loc=loc, parent=parent)
    holder.rotation_euler = (-math.pi / 2, 0, 0)
    D.parts["root"].parent = holder
    return holder

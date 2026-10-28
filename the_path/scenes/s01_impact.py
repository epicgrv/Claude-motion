"""ESCENA 01 - EL IMPACTO  (0:00 - 1:67)

Near-black. A green energy concentration far in the depth, fibres of light crossing at different
speeds (real parallax), the camera hangs for a heartbeat, then Duo rushes out of the spark at
vertiginous speed and hits the picture plane: body compresses, wings lag, the camera takes a
directional hit, shards scatter. Duo looks at us and blinks, the camera glides back, the thread
of light sweeps the wordmark into existence and Duo leaps out of frame.
"""
from __future__ import annotations

import math

import numpy as np

from .. import anim, duo as duolib, geo, mat, thread
from ..config import A, FPS, lin
from ..easing import (EXPLOSIVE, GLIDE, SNAP, catmull_rom, damped_osc, in_cubic, in_out_cubic, norm,
                      out_cubic, smoothstep, spring_follow, u)
from ..logo import build_logo

YP = -1.0           # picture plane (Duo's front face meets it)
YL = -0.05          # logo plane (just behind Duo)
BODY_DEPTH = 0.62
FLOOR_Z = -0.78     # Duo's feet height so his body centre sits at z = 0


def build(ctx):
    P = ctx.portrait
    c = ctx.coll("s01", window=(0.0, 1.95))
    cf = ctx.coll("s01_fibers", window=(0.15, 1.2))
    t_imp, t_launch = A["impact"], A["duo_launch"]
    d_imp = 3.1 if P else 5.0
    cam_y = YP - d_imp
    end_dist = 6.3 if P else 9.4
    logo_w = 3.7 if P else 5.4
    aspect = ctx.aspect
    tan_h = math.tan(math.radians(54.4 / 2))

    # ------------------------------------------------------------------ spark
    SPARK_Y = 140.0
    m_spark = mat.emissive("spark", "#7CFF3A", 30.0)
    spark = geo.sphere("spark", c, 0.5, mat=m_spark, loc=(0, SPARK_Y, 0), seg=24, rings=12)
    m_glow = mat.emissive("spark_glow", "#58CC02", 0.5)
    glow = geo.sphere("spark_glow", c, 6.0, mat=m_glow, loc=(0, SPARK_Y + 2, 0), seg=24, rings=12)
    fr = np.arange(0, int(1.05 * FPS))
    t = fr / FPS
    on = smoothstep(u(t, A["spark_on"], A["spark_on"] + 0.28))
    pulse = 1 + 0.18 * np.sin(2 * math.pi * 6.0 * t) * u(t, 0.3, 0.5)
    collapse = 1 - smoothstep(u(t, t_launch + 0.02, t_launch + 0.12))
    s = on * pulse * collapse
    anim.key_vec(spark, "scale", fr, np.stack([s, s, s], 1) * 1.0)
    g = on * (1 + 0.5 * smoothstep(u(t, 0.5, 0.85))) * (1 - smoothstep(u(t, t_launch, t_launch + 0.2)))
    anim.key_vec(glow, "scale", fr, np.stack([g, g, g], 1))

    # ------------------------------------------------------------------ fibres of light (parallax)
    rng = np.random.default_rng(3)
    fib_mats = [mat.emissive(f"fib{i}", col, st) for i, (col, st) in enumerate(
        [("#3FA800", 2.2), ("#7CFF3A", 3.2), ("#B8FF7A", 4.0), ("#58CC02", 1.6)])]
    nfib = 44
    t_off = A["fibers_out"]
    for i in range(nfib):
        d = 3.0 + 70.0 * rng.uniform() ** 1.7
        y = cam_y + d
        hw = tan_h * d
        hh = hw / aspect
        sgn = -1.0 if rng.uniform() < 0.72 else 1.0
        x0 = -sgn * rng.uniform(1.05, 1.5) * hw
        z0 = rng.uniform(-0.85, 0.85) * hh
        L = rng.uniform(0.35, 1.1) * d * 0.55
        rad = max(0.0011 * d, 0.0035)
        o = geo.tube(f"fib{i}", cf, [(-L / 2, 0, 0), (L / 2, 0, 0)], rad, fib_mats[i % 4], resolution=4, caps=True)
        v = sgn * d * rng.uniform(1.5, 3.6)
        ts = rng.uniform(0.18, 0.60)
        f = np.arange(int(0.16 * FPS), int(1.16 * FPS))
        tt = f / FPS
        # clock warp: 1x until 0.78 -> eases to a near hang by 0.95 (the camera "suspends")
        w = 1 - 0.95 * smoothstep(u(tt, 0.76, 0.95))
        W = np.cumsum(w) / FPS
        W = np.maximum(W - ts, 0) if False else W
        started = np.clip((tt - ts) / 0.001, 0, 1)
        x = x0 + v * np.maximum(np.cumsum(w * (tt >= ts)) / FPS, 0)
        # retract into the vanishing point as Duo emerges (a tunnel effect in reverse)
        rr = in_cubic(u(tt, 0.93, 1.12))
        yy = y + rr * 190.0
        anim.key_vec(o, "location", f, np.stack([x, yy, np.full_like(tt, z0)], 1))
        ctx.static_points.append((ts, (x0, y, z0)))
    ctx.ev("fibers", A["fibers_in"], dur=A["fibers_out"] - A["fibers_in"])

    # ------------------------------------------------------------------ Duo
    D = duolib.Duo(ctx, "D1", c)
    ctx.objs["duo1"] = D
    f0, f1 = int(0.78 * FPS), int(1.70 * FPS)
    fr = np.arange(f0, f1 + 1)
    t = fr / FPS
    # --- flight path: constant-ish speed with a slight acceleration into the hit
    uu = u(t, t_launch, t_imp)
    dist = 0.0 + (SPARK_Y - (YP + BODY_DEPTH)) * (1 - uu) ** 0.85
    root_y = YP + BODY_DEPTH + dist
    # --- impact squash: compress 0.55 on the depth axis in 3 frames, then damped rebound
    tau = t - t_imp
    comp = np.where(tau < 0, 0.0, 0.45 * np.where(tau < 0.05, out_cubic(tau / 0.05), 1.0))
    ring = np.where(tau >= 0.05, damped_osc(tau - 0.05, 0.45, 3.4, 0.24), 0.0)
    comp = np.where(tau < 0.05, comp, ring)
    sy = 1 - comp
    sx = sz = 1 / np.sqrt(np.clip(sy, 0.3, 2))
    # --- crouch / jump
    t_c0, t_j = 1.42, A["duo_leaves"]
    cr = in_out_cubic(u(t, t_c0, t_j - 0.005)) * (t < t_j)
    sz_c = 1 - 0.24 * cr
    sx_c = sy_c = 1 / np.sqrt(sz_c)
    st = in_out_cubic(u(t, t_j, t_j + 0.045)) * (1 - smoothstep(u(t, t_j + 0.09, t_j + 0.22)))
    sz_j = np.where(t >= t_j, 1 + 0.42 * st, 1.0)
    sx_j = sy_j = 1 / np.sqrt(sz_j)
    # blend the three regimes
    jumped = (t >= t_j)
    crouched = (t >= t_c0) & (t < t_j)
    SX = np.where(jumped, sx_j, np.where(crouched, sx_c, sx))
    SY = np.where(jumped, sy_j, np.where(crouched, sy_c, sy))
    SZ = np.where(jumped, sz_j, np.where(crouched, sz_c, sz))
    squash = np.stack([SX, SY, SZ], 1)
    # pinned to the plane while in contact (front face at YP), then free
    root_y = np.where(t >= t_imp, YP + BODY_DEPTH * SY, root_y)
    pos = np.stack([np.zeros_like(t), root_y, np.full_like(t, FLOOR_Z)], 1)
    # leap: ballistic path out of frame (up and to the left, towards the lens)
    tj = np.clip(t - t_j, 0, None)
    v0 = np.array([-9.5 if not P else -4.5, -3.5, 22.0 if not P else 16.0])
    gr = 28.0
    leap = np.stack([v0[0] * tj, v0[1] * tj, v0[2] * tj - 0.5 * gr * tj ** 2], 1) * (t >= t_j)[:, None]
    pos = pos + leap
    # roll tumble in flight, spin when leaping
    roll = 0.55 * (1 - uu) ** 2 * (t < t_imp)
    spin = 6.5 * tj * (t >= t_j)
    rot = np.stack([np.zeros_like(t), roll + spin * 0.4, spin * 0.25], 1)
    # emerging from the spark: scale 0.02 -> 1 while it is still ~140 m away
    emerge = 0.02 + 0.98 * smoothstep(u(t, t_launch - 0.04, t_launch + 0.05))
    scl = np.stack([emerge, emerge, emerge], 1)
    # --- wings / tufts: lagging springs driven by the compression and the flight
    drive = 1.25 * (1 - SY) + 0.12 * (SZ - 1)
    swept = -0.95 * (t < t_imp)                    # swept back in flight
    wing_target = np.where(t < t_imp, swept, drive * 1.2 + 0.10)
    flap = spring_follow(np.where(t < t_imp, 0.10, 0.10 + 1.1 * (1 - SY)), FPS, 2.6, 0.30)
    fold = spring_follow(np.where(t < t_imp, -0.95, 0.15 - 0.9 * (1 - SY) + 0.5 * (SZ - 1)), FPS, 3.0, 0.28)
    fold_r = spring_follow(np.where(t < t_imp, -0.95, 0.15 - 0.9 * (1 - SY) + 0.5 * (SZ - 1)), FPS, 2.7, 0.30)  # offset timing
    flap_r = spring_follow(np.where(t < t_imp, 0.10, 0.10 + 1.1 * (1 - SY)), FPS, 2.4, 0.33)
    tuft = spring_follow(np.where(t < t_imp, 0.4, 0.1 - 0.6 * (1 - SY)), FPS, 3.4, 0.2)
    # --- eyes: wide in flight, look at us after the hit, blink at A['blink']
    base = duolib.LID_OPEN - 0.12
    lid = duolib.blink(t, [A["blink"]], dur=0.13) - 0.12 * (t < t_imp)
    lid = np.where(t < t_imp, base, lid)
    gaze = np.stack([damped_osc(t - t_imp, 0.05, 4, 0.4), np.zeros_like(t)], 1)
    lean = np.stack([np.where(t < t_imp, -0.12 * uu, damped_osc(t - t_imp, 0.10, 3.2, 0.25)) - 0.18 * cr, 0 * t, 0 * t], 1)
    jaw = np.where((t > t_imp) & (t < t_imp + 0.12), 0.35 * np.sin(math.pi * u(t, t_imp, t_imp + 0.12)), 0.0)
    D.key(fr, pos=pos, rot=rot, scl=scl, lean=lean, squash=squash,
          wing_l=np.stack([flap, fold], 1), wing_r=np.stack([flap_r, fold_r], 1),
          lid_l=lid, lid_r=lid, gaze_l=gaze, gaze_r=gaze, jaw=jaw, tuft=tuft)

    # Duo's own light kit (so he reads while 140 m away and after): cool key, green rim, warm bounce
    kit = duo_kit(ctx, D, c, power=0.30)

    # ------------------------------------------------------------------ impact shards
    shard_mat = mat.emissive("shard", "#9CFF52", 10.0)
    rng2 = np.random.default_rng(11)
    ns = 34
    for i in range(ns):
        ang = rng2.uniform(0, 2 * math.pi)
        r0 = rng2.uniform(0.15, 0.75)
        p0 = np.array([r0 * math.cos(ang), YP - 0.04, r0 * math.sin(ang) * 0.9 + 0.1])
        spd = rng2.uniform(2.5, 11.0)
        vel = np.array([math.cos(ang) * 0.9, -rng2.uniform(0.25, 1.3), math.sin(ang) * 0.9]) * spd
        life = rng2.uniform(0.28, 0.6)
        sz = rng2.uniform(0.010, 0.03)
        o = geo.sphere(f"shard{i}", c, (sz, sz, sz * 2.4), mat=shard_mat, seg=10, rings=6)
        fs = np.arange(int(t_imp * FPS), int((t_imp + life) * FPS) + 2)
        ts_ = fs / FPS - t_imp
        k = 6.0                               # drag
        d = (1 - np.exp(-k * ts_)) / k
        pp = p0[None] + vel[None] * d[:, None]
        o.rotation_euler = geo.Vector(vel).to_track_quat("Z", "Y").to_euler()
        shrink = 1 - smoothstep(u(ts_, life * 0.35, life))
        anim.key_vec(o, "location", fs, pp)
        anim.key_vec(o, "scale", fs, np.stack([sz * shrink, sz * shrink, sz * 2.4 * shrink], 1))
        anim.key_vec(o, "scale", np.array([0, fs[0] - 1]), np.zeros((2, 3)))      # absent until the hit
    ctx.ev("impact", t_imp)
    ctx.ev("shards", t_imp, n=ns)

    # logo lighting: soft cool key from front-top-left, faint kicker from the right
    geo.area_light("logo_key", c, (0.85, 0.95, 1.0), 380 * (logo_w / 5.4) ** 2, size=3.5, loc=(-2.5, YL - 6.0, 3.2),
                   rot=geo.look_rot((-2.5, YL - 6.0, 3.2), (0, YL, -0.3)))
    geo.area_light("logo_kick", c, (0.6, 1.0, 0.7), 140 * (logo_w / 5.4) ** 2, size=2.5, loc=(3.0, YL - 4.0, 0.5),
                   rot=geo.look_rot((3.0, YL - 4.0, 0.5), (0, YL, -0.3)))
    # ------------------------------------------------------------------ wordmark + sweeping thread
    m_logo = mat.principled("logo", "feather", 0.34, coat=0.5, coat_rough=0.1, sheen=0.3, emit="feather", emit_strength=0.12)
    logo = build_logo(ctx, "logo1", c, logo_w, m_logo, loc=(0, YL, -0.42 * logo_w / 5.4 * 1.0))
    ctx.objs["logo1"] = logo
    zb = -0.42 * logo_w / 5.4                       # baseline height
    wl = logo_w
    # path: chest -> out left -> baseline sweep -> drops away to the right (continues in S02)
    way = [(0.0, YP - 0.06, -0.05), (-0.25 * wl, -0.5, 0.18 * wl * 0.5), (-0.64 * wl, YL - 0.15, zb + 0.18),
           (-0.58 * wl, YL - 0.05, zb - 0.05), (-0.3 * wl, YL - 0.06, zb - 0.13), (0.0, YL - 0.06, zb - 0.13),
           (0.3 * wl, YL - 0.06, zb - 0.13), (0.58 * wl, YL - 0.06, zb - 0.1), (0.7 * wl, YL - 0.05, zb - 0.28),
           (0.66 * wl, YL, zb - 0.9), (0.52 * wl, YL + 0.4, zb - 2.2)]
    path = catmull_rom(np.array(way), 420)
    pl = np.asarray(path)
    # speed profile keys: fraction of arc length at given times
    seg_pl = thread.Polyline(pl)
    L = seg_pl.length

    def frac_at_x(xx):
        # arc fraction where the sweep crosses x (searching the baseline part only)
        xs = pl[:, 0]
        k0 = int(np.argmin(np.abs(pl[:, 2] - (zb - 0.13)) + (np.arange(len(pl)) < len(pl) * 0.3) * 9))
        idx = k0 + int(np.argmin(np.abs(xs[k0:] - xx)))
        return seg_pl.cum[idx] / L

    t_a, t_b = A["retreat"] + 0.01, 1.62
    f_start = frac_at_x(-0.55 * wl)
    f_end = frac_at_x(0.6 * wl)
    keys = [(t_imp + 0.015, 0.0), (t_imp + 0.09, f_start * 0.45), (t_a + 0.02, f_start), (t_a + 0.1, f_start + 0.22 * (f_end - f_start)),
            (t_b, f_end), (1.70, 1.0)]
    seg = thread.Segment(ctx, "th1", c, pl, keys[0][0], keys[-1][0], ease=thread.profile(keys), radius=0.010 * logo_w / 5.4 + 0.005, halo=2.8,
                         tail=1.6 * logo_w / 5.4)
    ctx.objs["th1"] = seg
    ctx.state["th1_end"] = pl[-1].copy()
    ctx.state["th1_t_end"] = 1.70
    fr = np.arange(int(t_imp * FPS), int(1.80 * FPS))
    tt = fr / FPS
    hp = seg.head_pos(tt)
    head = thread.Head(ctx, "h1", c, radius=0.075 * logo_w / 5.4 + 0.02)
    ctx.objs["head1"] = head
    vis = smoothstep(u(tt, t_imp + 0.01, t_imp + 0.05))
    head.key(fr, hp, size=vis, power=(900 * vis) * (logo_w / 5.4) ** 2, color=lin("mask"), bead_strength=14)

    # letters spring up as the head passes their x (baseline sprout with overshoot)
    for i, (o, xx) in enumerate(zip(logo["letters"], logo["xs"])):
        fx = frac_at_x(xx)
        # time the head crosses fx
        tcross = tt[int(np.argmin(np.abs(seg.head_frac(tt) - fx)))]
        ctx.ev("letter", tcross, i=i)
        fs = np.arange(int(tcross * FPS) - 1, int((tcross + 0.5) * FPS))
        ts_ = fs / FPS - tcross
        k = 1 - np.exp(-ts_ * 14) * np.cos(ts_ * 38) * (ts_ >= 0)          # damped overshoot to 1
        sc_ = np.where(ts_ < 0, 0.0, np.clip(k, 0, 1.25))
        sc_ = np.maximum(sc_, 0.0)
        anim.key_vec(o, "scale", fs, np.stack([sc_, sc_, sc_], 1))
        # hide before sprout: scale key at 0 from frame 0
        anim.key_vec(o, "scale", np.array([0, fs[0]]), np.zeros((2, 3)))
        # ignition flash: emission spikes as the head passes, then settles
        # (material shared; flash handled by the head's practical light instead)

    # ------------------------------------------------------------------ camera
    cy0 = cam_y
    z0 = 0.04
    far = SPARK_Y
    # the look-at target stays on the optical axis (x=z=0) so changing it never swings the view;
    # keys that move it carry zero tension -> monotone, no overshoot behind the lens
    ctx.cam(0.00, (0, cy0 - 0.8, z0), (0, far, 0), lens=35, fstop=1.8, focus=far + 10, tension=0.3)
    ctx.cam(0.50, (0, cy0 - 0.45, z0), (0, far, 0), lens=35, fstop=1.8, focus=far, tension=0.6)
    ctx.cam(0.84, (0, cy0 - 0.30, z0), (0, far, 0), lens=35, fstop=2.2, focus=far * 0.4, tension=0.1)
    ctx.cam(1.00, (0, cy0 - 0.26, z0), (0, far, 0), lens=35, fstop=3.0, focus=60, tension=0.1)
    ctx.cam(t_imp, (0, cy0, z0), (0, far, 0.0), lens=35, fstop=4.0, focus=d_imp, tension=0.0)
    ctx.cam(1.28, (0, cy0 - 0.12, z0), (0, far, 0.0), lens=35, fstop=3.2, focus=d_imp + 0.1, tension=0.0)
    ctx.cam(1.67, (0, YL - end_dist, 0.22), (0, 10.0, -0.12), lens=35, fstop=4.0, focus=end_dist, tension=0.0)
    ctx.shake(t_imp, (0.03, 0.20, -0.06) if not P else (0.05, 0.16, -0.05), freq=6.5, decay=8.5, dur=0.7)
    ctx.ev("blink", A["blink"])
    ctx.ev("jump", t_j)
    ctx.ev("launch", t_launch)
    return dict(duo=D)


def duo_kit(ctx, D, coll, power=1.0, key_col=(0.82, 0.94, 1.0), rim_col=None):
    """Cool key + green rim + warm bounce riding on a Duo so he reads wherever he is."""
    rim_col = rim_col or lin("mask")
    r = D.parts["root"]
    key = geo.area_light(f"{D.name}_key", coll, key_col, 600 * power, size=2.6, loc=(-2.2, -3.2, 2.4), parent=r)
    key.rotation_euler = geo.look_rot((-2.2, -3.2, 2.4), (0, 0, 0.9))
    rim = geo.area_light(f"{D.name}_rim", coll, rim_col, 900 * power, size=1.8, loc=(2.6, 2.4, 2.6), parent=r)
    rim.rotation_euler = geo.look_rot((2.6, 2.4, 2.6), (0, 0, 0.9))
    bounce = geo.area_light(f"{D.name}_bounce", coll, (1.0, 0.72, 0.4), 90 * power, size=2.5, loc=(0.8, -2.2, -1.2), parent=r)
    bounce.rotation_euler = geo.look_rot((0.8, -2.2, -1.2), (0, 0, 0.8))
    return key, rim, bounce

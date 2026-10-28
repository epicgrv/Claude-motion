"""Render settings, world, camera-rig lights, far-field geometry and sparse dust."""
from __future__ import annotations

import math

import bpy
import numpy as np

from . import anim, geo, mat
from .config import FPS, N_FRAMES, PAL, RENDER, lin
from .easing import noise1d


def setup_render(ctx, spp=None, threads=0, scale=100):
    sc = ctx.scene
    sc.render.engine = "CYCLES"
    cy = sc.cycles
    cy.device = "CPU"
    cy.samples = spp or RENDER["samples_max"]
    cy.use_adaptive_sampling = True
    cy.adaptive_threshold = RENDER["noise_threshold"]
    cy.adaptive_min_samples = RENDER["samples_min"]
    cy.use_denoising = True
    cy.denoiser = "OPENIMAGEDENOISE"
    cy.denoising_quality = RENDER["denoise_quality"]
    cy.denoising_prefilter = RENDER["denoise_prefilter"]
    cy.max_bounces = RENDER["max_bounces"]
    cy.diffuse_bounces = RENDER["diffuse_bounces"]
    cy.glossy_bounces = RENDER["glossy_bounces"]
    cy.transmission_bounces = 2
    cy.volume_bounces = 0
    cy.transparent_max_bounces = 4
    cy.sample_clamp_indirect = RENDER["clamp_indirect"]
    cy.filter_width = RENDER["filter_width"]
    cy.use_animated_seed = False
    cy.use_light_tree = True
    cy.caustics_reflective = False
    cy.caustics_refractive = False
    cy.use_camera_cull = True
    cy.camera_cull_margin = 0.12
    sc.render.resolution_x = ctx.W
    sc.render.resolution_y = ctx.H
    sc.render.resolution_percentage = scale
    sc.render.fps = FPS
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = RENDER["motion_shutter"]
    sc.render.film_transparent = False
    sc.render.threads_mode = "AUTO" if not threads else "FIXED"
    if threads:
        sc.render.threads = threads
    sc.frame_start = 0
    sc.frame_end = N_FRAMES - 1
    # Scene-linear in, scene-linear out: all colour work happens in post.py
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.view_settings.exposure = 0.0
    sc.view_settings.gamma = 1.0
    sc.display_settings.display_device = "sRGB"
    vl = bpy.context.view_layer
    vl.use_pass_z = True
    vl.use_pass_mist = False


def setup_world(ctx):
    w = bpy.data.worlds.new("World")
    ctx.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
    # extremely soft vertical gradient around the brief's #060A0C
    ramp.color_ramp.elements[0].position = 0.28
    ramp.color_ramp.elements[1].position = 0.72
    base = lin("bg")
    ramp.color_ramp.elements[0].color = (base[0] * 0.8, base[1] * 0.85, base[2] * 0.9, 1)
    ramp.color_ramp.elements[1].color = (base[0] * 1.35, base[1] * 1.3, base[2] * 1.25, 1)
    m = nt.nodes.new("ShaderNodeMapRange")
    m.inputs["From Min"].default_value = -1
    m.inputs["From Max"].default_value = 1
    nt.links.new(sep.outputs["Z"], m.inputs["Value"])
    nt.links.new(m.outputs["Result"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 1.0
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    return w


def camera_rig(ctx):
    """Soft lights that ride with the camera: big cool key, very low fill, faint warm kicker.

    They keep every surface legible wherever the journey goes; scenes add their own
    station lights, rims and practicals on top.
    """
    cam = ctx.objs["camera"]
    c = ctx.coll("rig")
    key = geo.area_light("rig_key", c, (0.72, 0.9, 1.0), 90, size=3.5, size_y=2.4,
                         loc=(-1.6, 0.4, 2.4), rot=(math.radians(-60), math.radians(0), math.radians(-20)))
    key.rotation_euler = (math.radians(120), 0, math.radians(-18))   # camera space: looks along -Z
    key.parent = cam
    key.location = (-1.8, 2.2, -1.2)
    key.rotation_euler = geo.look_rot((-1.8, 2.2, -1.2), (0, 0, -6))
    dim = ctx.state.get("rig_dim")
    fill = geo.area_light("rig_fill", c, (0.5, 0.75, 0.9), 12, size=5.0, loc=(2.5, -1.0, 0.0))
    fill.parent = cam
    fill.rotation_euler = geo.look_rot((2.5, -1.0, 0.0), (0, 0, -6))
    ctx.objs["rig_key"] = key
    if dim:
        from .easing import smoothstep as _ss, u as _u
        frd = np.arange(N_FRAMES)
        td_ = frd / FPS
        k_ = 1 - _ss(_u(td_, dim[0], dim[1]))
        anim.key(key.data, "energy", frd, key.data.energy * k_)
        anim.key(fill.data, "energy", frd, fill.data.energy * k_)
    # ambient tint: orange when the flame lights, blue for maths, purple for music...
    tint = geo.area_light("rig_tint", c, (1, 1, 1), 0.0, size=7.0, loc=(0.0, 1.5, 2.5))
    tint.parent = cam
    tint.rotation_euler = geo.look_rot((0.0, 1.5, 2.5), (0, 0, -8))
    if ctx.tints:
        from .easing import smoothstep, u
        fr = np.arange(N_FRAMES)
        t = fr / FPS
        E = np.zeros(N_FRAMES)
        C = np.zeros((N_FRAMES, 3))
        for tn in ctx.tints:
            w = smoothstep(u(t, tn["t0"], tn["t0"] + tn["attack"])) * (1 - smoothstep(u(t, tn["t1"], tn["t1"] + tn["release"])))
            e = tn["energy"] * w
            E += e
            C += e[:, None] * np.array(tn["color"])[None]
        C = np.where(E[:, None] > 1e-6, C / np.maximum(E[:, None], 1e-6), 1.0)
        anim.key(tint.data, "energy", fr, E)
        anim.key_vec(tint.data, "color", fr, C)
    return key


def far_field(ctx):
    """Distant abstract geometry that rides with the camera at ~92% parallax.

    Dark, satin, softly rim-lit: it supplies atmospheric depth without 'stars' or sci-fi
    clichés. Big simple solids - control over quantity.
    """
    cam = ctx.objs["camera"]
    c = ctx.coll("far")
    rig = geo.empty("far_rig", c)
    ctx.objs["far_rig"] = rig
    rng = np.random.default_rng(7)
    m_dark = mat.principled("far_dark", "#16262C", 0.55, metal=0.0, coat=0.2, coat_rough=0.4)
    m_teal = mat.principled("far_teal", "#1B3236", 0.40, metal=0.2)
    shapes = []
    for i in range(14):
        ang = rng.uniform(0, 2 * math.pi)
        dist = rng.uniform(70, 150)
        x, y = math.cos(ang) * dist, math.sin(ang) * dist
        # keep the forward and the lateral hemispheres populated; slight bias forward
        z = rng.uniform(-60, 40)
        kind = rng.choice(["slab", "pillar"])
        if kind == "slab":
            s = rng.uniform(18, 44)
            o = geo.slab(f"far_{i}", c, s, s * rng.uniform(0.5, 1.0), rng.uniform(3, 8), R=s * 0.08, rb=0.4,
                         mat=m_teal if i % 3 == 0 else m_dark, loc=(x, y, z), parent=rig)
        elif kind == "ring":
            o = geo.torus(f"far_{i}", c, R=rng.uniform(16, 34), r=rng.uniform(0.8, 1.8), mat=m_dark, loc=(x, y, z), parent=rig)
        else:
            s = rng.uniform(6, 12)
            o = geo.slab(f"far_{i}", c, s, s, rng.uniform(40, 90), R=s * 0.4, rb=0.6, mat=m_dark, loc=(x, y, z), parent=rig)
        o.rotation_euler = (rng.uniform(0, 3.1), rng.uniform(0, 3.1), rng.uniform(0, 3.1))
        shapes.append(o)
    # rim lights for the far field (cool, faint) travel with the rig as well
    dim = ctx.state.get("rig_dim")
    for j, (col, e, loc) in enumerate([((0.25, 0.9, 0.55), 40000, (80, 60, 70)), ((0.2, 0.55, 1.0), 26000, (-90, 90, -50))]):
        L = geo.area_light(f"far_rim_{j}", c, col, e, size=50, loc=loc, parent=rig)
        L.rotation_euler = geo.look_rot(loc, (0, 0, 0))
        if dim:
            from .easing import smoothstep as _ss, u as _u
            frd = np.arange(N_FRAMES)
            anim.key(L.data, "energy", frd, e * (1 - _ss(_u(frd / FPS, dim[0], dim[1]))))
    return rig


def animate_far(ctx):
    P = ctx.cam_data["pos"]
    frames = np.arange(N_FRAMES)
    # moves with 92% of the camera translation -> a hint of parallax, never reached
    anim.key_vec(ctx.objs["far_rig"], "location", frames, P * 0.92)


def dust(ctx, n=90):
    """Sparse, deliberate motes seeded along the camera path (static in world -> real parallax)."""
    c = ctx.coll("dust")
    rng = np.random.default_rng(21)
    P = ctx.cam_data["pos"]
    T = ctx.cam_data["tgt"]
    m = mat.emissive("dust", (0.55, 0.95, 0.7), 1.6)
    objs = []
    for i in range(n):
        k = int(rng.integers(0, N_FRAMES))
        base = P[k] + (T[k] - P[k]) * rng.uniform(0.15, 0.9)
        off = rng.normal(0, 1, 3) * np.array([2.6, 2.6, 2.0])
        loc = base + off
        r = rng.uniform(0.012, 0.03)
        o = geo.sphere(f"dust_{i}", c, r, mat=m, loc=tuple(loc), seg=10, rings=6)
        objs.append(o)
        f = np.arange(max(0, k - 120), min(N_FRAMES, k + 120))
        t = f / FPS
        drift = np.stack([noise1d(t * 0.4, 100 + i), noise1d(t * 0.4, 200 + i), noise1d(t * 0.4, 300 + i)], axis=1) * 0.25
        anim.key_vec(o, "location", f, np.asarray(loc)[None, :] + drift)
        o["win"] = (float(f[0] / FPS), float(f[-1] / FPS))
    return objs

"""Procedural 3-D set kit (Blender/Cycles) for environment plates.

Every set is built from primitives + procedural PBR materials (wood, brick, carpet, tile, asphalt, glass, chrome...),
lit with real lights, rendered portrait 1440x2560 with OIDN denoising. Characters are NOT in the plates; they're
composited later, so sets leave clear floor space where the action happens.

    python -m finance_shorts.engine.set3d <set_name> [--spp 64] [--scale 100]
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

OUT = Path(__file__).resolve().parents[1] / "visuals" / "pepsi-jet" / "plates"


# ------------------------------------------------------------------------------------------------ scene setup
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.render.resolution_x, sc.render.resolution_y = 1440, 2560
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "AgX"
    try:
        sc.view_settings.look = "AgX - Punchy"
    except TypeError:
        pass
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = "OPENIMAGEDENOISE"
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.max_bounces = 6
    sc.cycles.glossy_bounces = 3
    sc.cycles.transmission_bounces = 4
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.cycles.blur_glossy = 1.0
    w = bpy.data.worlds.new("W")
    sc.world = w
    w.use_nodes = True
    return sc


def world(color=(0.05, 0.06, 0.08), strength=1.0, sky=None):
    w = bpy.context.scene.world
    nt = w.node_tree
    bg = nt.nodes["Background"]
    if sky:  # vertical gradient sky: [(pos, (r,g,b)), ...]
        tc = nt.nodes.new("ShaderNodeTexCoord")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        nt.links.new(tc.outputs["Generated"], sep.inputs[0])
        mr = nt.nodes.new("ShaderNodeMapRange")
        nt.links.new(sep.outputs["Z"], mr.inputs[0])
        mr.inputs[1].default_value, mr.inputs[2].default_value = 0.45, 0.85
        nt.links.new(mr.outputs[0], ramp.inputs[0])
        _ramp(ramp, sky)
        nt.links.new(ramp.outputs[0], bg.inputs[0])
    else:
        bg.inputs[0].default_value = (*color, 1)
    bg.inputs[1].default_value = strength


def _ramp(ramp, stops):
    cr = ramp.color_ramp
    while len(cr.elements) > 2:
        cr.elements.remove(cr.elements[-1])
    for i, (p, c) in enumerate(stops):
        if i < 2:
            el = cr.elements[i]
            el.position = p
        else:
            el = cr.elements.new(p)
        el.color = (*c, 1) if len(c) == 3 else c


def camera(loc, look, lens=24, dof=None, fstop=2.8, shift=(0, 0)):
    cam = bpy.data.cameras.new("Cam")
    cam.lens = lens
    cam.shift_x, cam.shift_y = shift
    cam.sensor_fit = "VERTICAL"
    ob = bpy.data.objects.new("Cam", cam)
    bpy.context.collection.objects.link(ob)
    ob.location = loc
    d = Vector(look) - Vector(loc)
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    if dof:
        cam.dof.use_dof = True
        cam.dof.focus_distance = dof
        cam.dof.aperture_fstop = fstop
    bpy.context.scene.camera = ob
    return ob


def render(name, spp=64, scale=100):
    sc = bpy.context.scene
    sc.cycles.samples = spp
    sc.cycles.adaptive_threshold = 0.02
    sc.render.resolution_percentage = scale
    sc.render.image_settings.file_format = "PNG"
    sc.render.filepath = str(OUT / f"{name}.png")
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.render.render(write_still=True)


# ------------------------------------------------------------------------------------------------ materials
_MATS = {}


def mat(name, color=(0.8, 0.8, 0.8), rough=0.5, metal=0.0, emit=None, emit_str=1.0, trans=0.0, ior=1.45,
        coat=0.0, alpha=1.0):
    key = name
    if key in _MATS:
        return _MATS[key]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["IOR"].default_value = ior
    b.inputs["Transmission Weight"].default_value = trans
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Alpha"].default_value = alpha
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = emit_str
    _MATS[key] = m
    return m


def _nodes(m):
    return m.node_tree.nodes, m.node_tree.links, m.node_tree.nodes["Principled BSDF"]


def _coord(nt, scale=(1, 1, 1), kind="Object"):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = scale
    nt.links.new(tc.outputs[kind], mp.inputs[0])
    return mp.outputs[0]


def wood(name, c1=(0.35, 0.17, 0.07), c2=(0.18, 0.07, 0.02), rough=0.35, scale=6.0, planks=0.0, stretch=8.0,
         coat=0.3):
    """Procedural wood: stretched noise + wave rings, optional plank seams (planks = plank width in m)."""
    if name in _MATS:
        return _MATS[name]
    m = mat(name, rough=rough, coat=coat)
    nodes, links, b = _nodes(m)
    nt = m.node_tree
    co = _coord(nt, (scale, scale * stretch, scale))
    wave = nodes.new("ShaderNodeTexWave")
    wave.wave_type = "RINGS"
    wave.inputs["Scale"].default_value = 0.6
    wave.inputs["Distortion"].default_value = 8
    wave.inputs["Detail"].default_value = 6
    links.new(co, wave.inputs["Vector"])
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3
    noise.inputs["Detail"].default_value = 10
    links.new(co, noise.inputs["Vector"])
    mix = nodes.new("ShaderNodeMix")
    mix.data_type = "FLOAT"
    mix.inputs[0].default_value = 0.5
    links.new(wave.outputs["Fac"], mix.inputs[2])
    links.new(noise.outputs["Fac"], mix.inputs[3])
    ramp = nodes.new("ShaderNodeValToRGB")
    _ramp(ramp, [(0.25, c2), (0.75, c1)])
    links.new(mix.outputs[0], ramp.inputs[0])
    col = ramp.outputs[0]
    if planks:
        br = nodes.new("ShaderNodeTexBrick")
        br.inputs["Scale"].default_value = 1.0
        br.inputs["Mortar Size"].default_value = 0.004
        br.inputs["Brick Width"].default_value = 2.5
        br.inputs["Row Height"].default_value = planks
        br.inputs["Color1"].default_value = (1, 1, 1, 1)
        br.inputs["Color2"].default_value = (0.82, 0.82, 0.82, 1)
        br.inputs["Mortar"].default_value = (0.15, 0.15, 0.15, 1)
        links.new(_coord(nt, (1, 1, 1)), br.inputs["Vector"])
        mm = nodes.new("ShaderNodeMix")
        mm.data_type = "RGBA"
        mm.blend_type = "MULTIPLY"
        mm.inputs[0].default_value = 1.0
        links.new(col, mm.inputs[6])
        links.new(br.outputs["Color"], mm.inputs[7])
        col = mm.outputs[2]
        bump = nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.3
        links.new(br.outputs["Fac"], bump.inputs["Height"])
        links.new(bump.outputs[0], b.inputs["Normal"])
    links.new(col, b.inputs["Base Color"])
    rn = nodes.new("ShaderNodeMapRange")
    rn.inputs[3].default_value, rn.inputs[4].default_value = rough * 0.7, rough * 1.4
    links.new(noise.outputs["Fac"], rn.inputs[0])
    links.new(rn.outputs[0], b.inputs["Roughness"])
    return m


def noisy(name, c1, c2, scale=40.0, rough=0.8, bump=0.3, detail=8, metal=0.0, voronoi=False):
    """Two-colour noise surface with bump (carpet, asphalt, concrete, grass, plaster, granite)."""
    if name in _MATS:
        return _MATS[name]
    m = mat(name, rough=rough, metal=metal)
    nodes, links, b = _nodes(m)
    tex = nodes.new("ShaderNodeTexVoronoi" if voronoi else "ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = scale
    if not voronoi:
        tex.inputs["Detail"].default_value = detail
    links.new(_coord(m.node_tree), tex.inputs["Vector"])
    out = tex.outputs["Distance" if voronoi else "Fac"]
    ramp = nodes.new("ShaderNodeValToRGB")
    _ramp(ramp, [(0.3, c2), (0.7, c1)])
    links.new(out, ramp.inputs[0])
    links.new(ramp.outputs[0], b.inputs["Base Color"])
    bp = nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = bump
    links.new(out, bp.inputs["Height"])
    links.new(bp.outputs[0], b.inputs["Normal"])
    return m


def checker(name, c1, c2, scale=8.0, rough=0.15, coat=0.6):
    """Glossy checkered tile (diner/kitchen floors) - gives real reflections of the set."""
    if name in _MATS:
        return _MATS[name]
    m = mat(name, rough=rough, coat=coat)
    nodes, links, b = _nodes(m)
    ch = nodes.new("ShaderNodeTexChecker")
    ch.inputs["Scale"].default_value = scale
    ch.inputs["Color1"].default_value = (*c1, 1)
    ch.inputs["Color2"].default_value = (*c2, 1)
    links.new(_coord(m.node_tree), ch.inputs["Vector"])
    nz = nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 30
    links.new(_coord(m.node_tree), nz.inputs["Vector"])
    mx = nodes.new("ShaderNodeMix")
    mx.data_type = "RGBA"
    mx.blend_type = "MULTIPLY"
    mx.inputs[0].default_value = 0.25
    links.new(ch.outputs["Color"], mx.inputs[6])
    links.new(nz.outputs["Color"], mx.inputs[7])
    links.new(mx.outputs[2], b.inputs["Base Color"])
    rr = nodes.new("ShaderNodeMapRange")
    rr.inputs[3].default_value, rr.inputs[4].default_value = rough * 0.5, rough * 2.5
    links.new(nz.outputs["Fac"], rr.inputs[0])
    links.new(rr.outputs[0], b.inputs["Roughness"])
    return m


def brick(name, c1=(0.45, 0.16, 0.09), c2=(0.32, 0.1, 0.06), mortar=(0.6, 0.57, 0.52), scale=3.0, rough=0.85):
    if name in _MATS:
        return _MATS[name]
    m = mat(name, rough=rough)
    nodes, links, b = _nodes(m)
    br = nodes.new("ShaderNodeTexBrick")
    br.inputs["Scale"].default_value = scale
    br.inputs["Color1"].default_value = (*c1, 1)
    br.inputs["Color2"].default_value = (*c2, 1)
    br.inputs["Mortar"].default_value = (*mortar, 1)
    br.inputs["Mortar Size"].default_value = 0.015
    br.inputs["Bias"].default_value = 0.3
    links.new(_coord(m.node_tree), br.inputs["Vector"])
    links.new(br.outputs["Color"], b.inputs["Base Color"])
    bp = nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.6
    links.new(br.outputs["Fac"], bp.inputs["Height"])
    links.new(bp.outputs[0], b.inputs["Normal"])
    return m


def stripes(name, c1, c2, scale=5.0, rough=0.6, axis="Z", kind="BANDS"):
    """Wallpaper / flag stripes / awning."""
    if name in _MATS:
        return _MATS[name]
    m = mat(name, rough=rough)
    nodes, links, b = _nodes(m)
    w = nodes.new("ShaderNodeTexWave")
    w.wave_type = kind
    w.bands_direction = axis
    w.wave_profile = "SAW"
    w.inputs["Scale"].default_value = scale
    links.new(_coord(m.node_tree), w.inputs["Vector"])
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    _ramp(ramp, [(0.0, c1), (0.5, c2)])
    links.new(w.outputs["Fac"], ramp.inputs[0])
    links.new(ramp.outputs[0], b.inputs["Base Color"])
    return m


def glass(name="Glass", tint=(0.85, 0.92, 0.95), rough=0.02):
    return mat(name, tint, rough=rough, trans=1.0, ior=1.45)


def chrome(name="Chrome", c=(0.9, 0.9, 0.92), rough=0.12):
    return mat(name, c, rough=rough, metal=1.0)


def emit(name, c, strength=5.0):
    return mat(name, (0, 0, 0), emit=c, emit_str=strength)


# ------------------------------------------------------------------------------------------------ geometry
def _link(ob):
    bpy.context.collection.objects.link(ob)
    return ob


def box(name, size, loc, m=None, bevel=0.02, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        mod = ob.modifiers.new("bev", "BEVEL")
        mod.width = bevel
        mod.segments = 3
        mod.limit_method = "ANGLE"
    if m:
        ob.data.materials.append(m)
    return ob


def cyl(name, r, h, loc, m=None, rot=(0, 0, 0), verts=48, bevel=0.0, r2=None):
    if r2 is not None:
        bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=r2, depth=h, location=loc, rotation=rot)
    else:
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=h, location=loc, rotation=rot)
    ob = bpy.context.active_object
    ob.name = name
    bpy.ops.object.shade_smooth()
    if bevel:
        mod = ob.modifiers.new("bev", "BEVEL")
        mod.width = bevel
        mod.segments = 3
        mod.limit_method = "ANGLE"
    if m:
        ob.data.materials.append(m)
    return ob


def sphere(name, r, loc, m=None, scale=(1, 1, 1), sub=3):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = scale
    bpy.ops.object.shade_smooth()
    if m:
        ob.data.materials.append(m)
    return ob


def torus(name, R, r, loc, m=None, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, location=loc, rotation=rot,
                                     major_segments=64, minor_segments=16)
    ob = bpy.context.active_object
    ob.name = name
    bpy.ops.object.shade_smooth()
    if m:
        ob.data.materials.append(m)
    return ob


def plane(name, size, loc, m=None, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = (size[0], size[1], 1)
    bpy.ops.object.transform_apply(scale=True)
    if m:
        ob.data.materials.append(m)
    return ob


def prism(name, w, d, h, loc, m=None, rot=(0, 0, 0)):
    """Triangular prism (roof / pediment): base w (x) by d (y), apex height h."""
    mesh = bpy.data.meshes.new(name)
    v = [(-w / 2, -d / 2, 0), (w / 2, -d / 2, 0), (0, -d / 2, h), (-w / 2, d / 2, 0), (w / 2, d / 2, 0), (0, d / 2, h)]
    f = [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (1, 4, 5, 2), (0, 2, 5, 3)]
    mesh.from_pydata(v, [], f)
    ob = _link(bpy.data.objects.new(name, mesh))
    ob.location = loc
    ob.rotation_euler = rot
    if m:
        ob.data.materials.append(m)
    return ob


# ------------------------------------------------------------------------------------------------ lights
def area(name, loc, look, size, energy, color=(1, 0.9, 0.8), shape="RECTANGLE", size_y=None):
    li = bpy.data.lights.new(name, "AREA")
    li.energy = energy
    li.color = color
    li.shape = shape
    li.size = size
    if size_y:
        li.size_y = size_y
    ob = _link(bpy.data.objects.new(name, li))
    ob.location = loc
    ob.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return ob


def point(name, loc, energy, color=(1, 0.8, 0.6), radius=0.05):
    li = bpy.data.lights.new(name, "POINT")
    li.energy = energy
    li.color = color
    li.shadow_soft_size = radius
    ob = _link(bpy.data.objects.new(name, li))
    ob.location = loc
    return ob


def spot(name, loc, look, energy, color=(1, 0.85, 0.65), angle=60, blend=0.5, radius=0.05):
    li = bpy.data.lights.new(name, "SPOT")
    li.energy = energy
    li.color = color
    li.spot_size = math.radians(angle)
    li.spot_blend = blend
    li.shadow_soft_size = radius
    ob = _link(bpy.data.objects.new(name, li))
    ob.location = loc
    ob.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return ob


def sun(name, rot_deg, energy, color=(1, 0.85, 0.65), angle=2.0):
    li = bpy.data.lights.new(name, "SUN")
    li.energy = energy
    li.color = color
    li.angle = math.radians(angle)
    ob = _link(bpy.data.objects.new(name, li))
    ob.rotation_euler = tuple(math.radians(a) for a in rot_deg)
    return ob


# ------------------------------------------------------------------------------------------------ reusable props
def room(w, d, h, floor_m, wall_m, ceil_m=None, open_front=True):
    plane("Floor", (w, d), (0, 0, 0), floor_m)
    plane("Back", (w, h), (0, d / 2, h / 2), wall_m, rot=(math.radians(90), 0, 0))
    plane("Left", (d, h), (-w / 2, 0, h / 2), wall_m, rot=(math.radians(90), 0, math.radians(90)))
    plane("Right", (d, h), (w / 2, 0, h / 2), wall_m, rot=(math.radians(90), 0, math.radians(-90)))
    plane("Ceil", (w, d), (0, 0, h), ceil_m or mat("Ceil", (0.75, 0.72, 0.66), 0.9), rot=(math.radians(180), 0, 0))
    if not open_front:
        plane("Front", (w, h), (0, -d / 2, h / 2), wall_m, rot=(math.radians(-90), 0, 0))


def table_round(loc, r=0.55, h=0.75, top_m=None, leg_m=None):
    x, y, z = loc
    cyl("TableTop", r, 0.05, (x, y, z + h), top_m, bevel=0.01)
    cyl("TableLeg", 0.05, h, (x, y, z + h / 2), leg_m)
    cyl("TableFoot", 0.28, 0.03, (x, y, z + 0.015), leg_m, bevel=0.01)


def chair(loc, rotz=0, seat_m=None, frame_m=None):
    x, y, z = loc
    c, s = math.cos(rotz), math.sin(rotz)

    def p(dx, dy, dz):
        return (x + dx * c - dy * s, y + dx * s + dy * c, z + dz)

    box("Seat", (0.42, 0.42, 0.05), p(0, 0, 0.45), seat_m, rot=(0, 0, rotz))
    box("Back", (0.42, 0.04, 0.42), p(0, 0.2, 0.72), seat_m, rot=(0, 0, rotz))
    for dx in (-0.18, 0.18):
        for dy in (-0.18, 0.18):
            cyl("Leg", 0.018, 0.45, p(dx, dy, 0.225), frame_m)


def tree(loc, h=5.0, canopy=(0.25, 0.42, 0.12), seed=0):
    x, y, z = loc
    cyl("Trunk", 0.18, h * 0.5, (x, y, z + h * 0.25), noisy("Bark", (0.25, 0.17, 0.11), (0.12, 0.08, 0.05), 20))
    leaf = noisy(f"Leaf{seed}", canopy, tuple(c * 0.55 for c in canopy), 6, 0.7, 0.8)
    for i, (dx, dy, dz, r) in enumerate([(0, 0, 0.62, 0.32), (0.25, 0.1, 0.52, 0.24), (-0.22, -0.05, 0.55, 0.25),
                                         (0.05, 0.2, 0.75, 0.22), (-0.1, -0.2, 0.7, 0.2)]):
        s = sphere("Canopy", h * r, (x + dx * h, y + dy * h, z + dz * h), leaf, sub=2)
        d = s.modifiers.new("disp", "DISPLACE")
        tx = bpy.data.textures.new(f"cl{seed}{i}", "CLOUDS")
        tx.noise_scale = 0.6
        d.texture = tx
        d.strength = 0.35


def house(loc, w=9, d=8, h=3.2, wall=(0.85, 0.82, 0.74), roof=(0.25, 0.22, 0.24), rotz=0, door=(0.75, 0.15, 0.12)):
    x, y, z = loc
    wm = noisy(f"Siding{wall}", wall, tuple(c * 0.9 for c in wall), 3, 0.7, 0.05)
    box("House", (w, d, h), (x, y, z + h / 2), wm, rot=(0, 0, rotz), bevel=0.03)
    prism("Roof", w + 0.6, d + 0.6, 2.2, (x, y, z + h), mat(f"Roof{roof}", roof, 0.8), rot=(0, 0, rotz + math.radians(90)))
    win = emit("WinWarm", (1.0, 0.75, 0.42), 3.0)
    for k in (-0.3, 0.3):
        box("Win", (1.3, 0.05, 1.2), (x + k * w, y - d / 2 - 0.02, z + 1.6), win, bevel=0)
    box("Door", (1.0, 0.06, 2.1), (x, y - d / 2 - 0.02, z + 1.05), mat(f"Door{door}", door, 0.4), bevel=0.01)


def car(loc, color=(0.6, 0.12, 0.1), rotz=0):
    x, y, z = loc
    paint = mat(f"Paint{color}", color, 0.25, coat=1.0)
    box("CarBody", (1.8, 4.4, 0.75), (x, y, z + 0.6), paint, rot=(0, 0, rotz), bevel=0.15)
    box("CarCab", (1.6, 2.3, 0.6), (x, y + 0.2, z + 1.25), glass("CarGlass", (0.3, 0.35, 0.4), 0.05), rot=(0, 0, rotz), bevel=0.12)
    tire = mat("Tire", (0.03, 0.03, 0.03), 0.8)
    for dx in (-0.85, 0.85):
        for dy in (-1.4, 1.4):
            cyl("Wheel", 0.36, 0.25, (x + dx, y + dy, z + 0.36), tire, rot=(0, math.radians(90), 0))


def jet(loc, rot=(0, 0, 0), scale=1.0):
    """Stylised toy-like Harrier-ish jump jet built from primitives (grey, chunky, bevelled)."""
    grey = mat("JetGrey", (0.32, 0.35, 0.38), 0.45, coat=0.3)
    dark = mat("JetDark", (0.1, 0.11, 0.12), 0.5)
    can = glass("Canopy", (0.25, 0.3, 0.35), 0.03)
    parts = []
    parts.append(cyl("Fuse", 0.75, 9.0, (0, 0, 0), grey, rot=(math.radians(90), 0, 0), r2=0.55))
    parts.append(cyl("Nose", 0.55, 2.2, (0, -5.6, 0.05), grey, rot=(math.radians(-90), 0, 0), r2=0.02))
    parts.append(sphere("Cockpit", 0.62, (0, -3.2, 0.55), can, scale=(0.8, 2.1, 0.8)))
    parts.append(box("Wing", (9.0, 2.4, 0.16), (0, 0.6, 0.35), grey, bevel=0.06))
    parts.append(box("Tail", (0.14, 2.0, 2.2), (0, 4.0, 1.2), grey, bevel=0.05, rot=(math.radians(-15), 0, 0)))
    parts.append(box("Stab", (4.0, 1.4, 0.12), (0, 4.2, 0.2), grey, bevel=0.04))
    for s in (-1, 1):
        parts.append(cyl("Intake", 0.55, 2.0, (s * 0.95, -1.6, 0.0), dark, rot=(math.radians(90), 0, 0)))
        parts.append(cyl("Nozzle", 0.32, 0.8, (s * 1.0, 0.2, -0.7), dark, rot=(0, 0, 0), r2=0.38))
        parts.append(sphere("Glow", 0.3, (s * 1.0, 0.2, -1.15), emit("Afterburn", (1.0, 0.55, 0.2), 25)))
    root = bpy.data.objects.new("Jet", None)
    _link(root)
    for p in parts:
        p.parent = root
    root.location = loc
    root.rotation_euler = rot
    root.scale = (scale, scale, scale)
    return root


# ------------------------------------------------------------------------------------------------ CLI
def main():
    from finance_shorts.engine import sets_pepsi
    name = sys.argv[1]
    spp = int(sys.argv[sys.argv.index("--spp") + 1]) if "--spp" in sys.argv else 64
    scale = int(sys.argv[sys.argv.index("--scale") + 1]) if "--scale" in sys.argv else 100
    reset()
    getattr(sets_pepsi, name)()
    render(name, spp, scale)


if __name__ == "__main__":
    main()

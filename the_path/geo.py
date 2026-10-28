"""Procedural geometry with analytic smooth normals (no modifiers, no faceting).

``slab``    rounded-rectangle prism with a true circular edge bevel (buttons, cards, tiles,
            nodes, phone bodies, progress troughs).  Corner radius R, edge bevel rb.
``sphere``  UV sphere (shared mesh) - Duo's body parts are scaled spheres.
``egg``     sphere with a taper (Duo's body).
``torus``   shock-wave rings.
``text``    extruded font text.
``tube``    bevelled curve through points (the light thread).
"""
from __future__ import annotations

import math

import bmesh
import bpy
import numpy as np
from mathutils import Vector

from .config import FONT_BLACK, FONT_BOLD

_MESHES: dict = {}
_FONTS: dict = {}


def assign(o, m):
    """Per-object material link (meshes are shared between instances)."""
    me = o.data
    if len(me.materials) == 0:
        me.materials.append(None)
    o.material_slots[0].link = "OBJECT"
    o.material_slots[0].material = m


def reset():
    _MESHES.clear()
    _FONTS.clear()


def link(obj, coll):
    coll.objects.link(obj)
    return obj


def new_collection(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(c)
    return c


def empty(name, coll, loc=(0, 0, 0), parent=None, display="PLAIN_AXES", size=0.1):
    o = bpy.data.objects.new(name, None)
    o.empty_display_type = display
    o.empty_display_size = size
    o.location = loc
    coll.objects.link(o)
    if parent is not None:
        o.parent = parent
    return o


def _finish(mesh, normals=None):
    mesh.update()
    for p in mesh.polygons:
        p.use_smooth = True
    if normals is not None:
        mesh.normals_split_custom_set_from_vertices([tuple(n) for n in normals])


# ---------------------------------------------------------------- rounded slab
def _footprint(w, h, R, seg):
    """Rounded-rect outline (CCW) -> points (N,2) and outward normals (N,2)."""
    R = min(R, w / 2 - 1e-4, h / 2 - 1e-4)
    cx, cy = w / 2 - R, h / 2 - R
    pts, nrm = [], []
    corners = [((cx, cy), 0.0), ((-cx, cy), math.pi / 2), ((-cx, -cy), math.pi), ((cx, -cy), 3 * math.pi / 2)]
    for (ox, oy), a0 in corners:
        for k in range(seg + 1):
            a = a0 + (math.pi / 2) * k / seg
            n = (math.cos(a), math.sin(a))
            pts.append((ox + R * n[0], oy + R * n[1]))
            nrm.append(n)
    return np.array(pts), np.array(nrm), R


def slab_mesh(w, h, d, R, rb, seg_arc=10, seg_bev=5, name="slab"):
    """Mesh of a rounded-rect prism centred at origin; top face at +d/2 (normal +Z)."""
    key = ("slab", round(w, 5), round(h, 5), round(d, 5), round(R, 5), round(rb, 5), seg_arc, seg_bev)
    if key in _MESHES:
        return _MESHES[key]
    pts, nrm, R = _footprint(w, h, R, seg_arc)
    rb = min(rb, R * 0.98, d / 2 * 0.98)
    N = len(pts)
    verts, normals, rings = [], [], []

    def add_ring(off, z, nz_dir, nxy):
        idx = []
        for i in range(N):
            p = pts[i] - nrm[i] * off
            verts.append((p[0], p[1], z))
            nn = nrm[i] * nxy + np.array([0, 0]) if nxy else np.zeros(2)
            normals.append((nn[0], nn[1], nz_dir))
            idx.append(len(verts) - 1)
        rings.append(idx)

    zt = d / 2
    # top cap ring (inset by rb), normal +z
    add_ring(rb, zt, 1.0, 0.0)
    for j in range(1, seg_bev + 1):
        ph = (math.pi / 2) * j / seg_bev
        add_ring(rb * (1 - math.sin(ph)), zt - rb * (1 - math.cos(ph)), math.cos(ph), math.sin(ph))
    # bottom half (mirror)
    for j in range(seg_bev, -1, -1):
        ph = (math.pi / 2) * j / seg_bev
        add_ring(rb * (1 - math.sin(ph)), -(zt - rb * (1 - math.cos(ph))), -math.cos(ph), math.sin(ph))
    faces = []
    for a, b in zip(rings[:-1], rings[1:]):
        for i in range(N):
            j = (i + 1) % N
            faces.append((a[i], b[i], b[j], a[j]))
    # caps (fan)
    ct = len(verts)
    verts.append((0, 0, zt)); normals.append((0, 0, 1))
    for i in range(N):
        faces.append((ct, rings[0][i], rings[0][(i + 1) % N]))
    cb = len(verts)
    verts.append((0, 0, -zt)); normals.append((0, 0, -1))
    for i in range(N):
        faces.append((cb, rings[-1][(i + 1) % N], rings[-1][i]))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    # planar UVs (top-face mapping) so textures/flags can be applied
    uv = me.uv_layers.new(name="UV")
    for li, loop in enumerate(me.loops):
        v = verts[loop.vertex_index]
        uv.data[li].uv = (v[0] / w + 0.5, v[1] / h + 0.5)
    _finish(me, normals)
    _MESHES[key] = me
    return me


def slab(name, coll, w, h, d, R=None, rb=None, mat=None, loc=(0, 0, 0), parent=None, seg_arc=None, seg_bev=3):
    R = min(w, h) * 0.18 if R is None else R
    rb = min(d * 0.22, R * 0.5) if rb is None else rb
    if seg_arc is None:     # enough segments for a smooth silhouette at this corner radius, no more
        seg_arc = int(min(14, max(5, 5 + R * 7)))
    me = slab_mesh(w, h, d, R, rb, seg_arc, seg_bev)
    o = bpy.data.objects.new(name, me)
    o.location = loc
    coll.objects.link(o)
    if parent is not None:
        o.parent = parent
    if mat is not None:
        assign(o, mat)
    return o


# ---------------------------------------------------------------- sphere / egg / torus
def sphere_mesh(seg=48, rings=24, taper=0.0, name="sphere"):
    key = ("sphere", seg, rings, round(taper, 4))
    if key in _MESHES:
        return _MESHES[key]
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=1.0)
    if taper:
        for v in bm.verts:
            f = 1.0 - taper * max(0.0, v.co.z) ** 1.4
            v.co.x *= f
            v.co.y *= f
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    _MESHES[key] = me
    return me


def sphere(name, coll, r=(1, 1, 1), mat=None, loc=(0, 0, 0), parent=None, seg=48, rings=24, taper=0.0):
    me = sphere_mesh(seg, rings, taper)
    o = bpy.data.objects.new(name, me)
    o.scale = (r, r, r) if isinstance(r, (int, float)) else tuple(r)
    o.location = loc
    coll.objects.link(o)
    if parent is not None:
        o.parent = parent
    if mat is not None:
        assign(o, mat)
    return o


def hemisphere_mesh(seg=40, rings=14, name="hemi"):
    key = ("hemi", seg, rings)
    if key in _MESHES:
        return _MESHES[key]
    verts, faces = [], []
    # +Z pole dome (open at z=0)
    for j in range(rings + 1):
        th = (math.pi / 2) * j / rings
        for i in range(seg):
            ph = 2 * math.pi * i / seg
            verts.append((math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), math.cos(th)))
    for j in range(rings):
        for i in range(seg):
            a = j * seg + i
            b = j * seg + (i + 1) % seg
            c = (j + 1) * seg + (i + 1) % seg
            d = (j + 1) * seg + i
            faces.append((a, d, c, b))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    for p in me.polygons:
        p.use_smooth = True
    me.normals_split_custom_set_from_vertices([v for v in verts])
    _MESHES[key] = me
    return me


def torus(name, coll, R=1.0, r=0.05, mat=None, loc=(0, 0, 0), seg_major=96, seg_minor=14, parent=None):
    key = ("torus", round(R, 4), round(r, 4), seg_major, seg_minor)
    if key in _MESHES:
        me = _MESHES[key]
    else:
        verts, faces, normals = [], [], []
        for i in range(seg_major):
            a = 2 * math.pi * i / seg_major
            ca, sa = math.cos(a), math.sin(a)
            for j in range(seg_minor):
                b = 2 * math.pi * j / seg_minor
                cb, sb = math.cos(b), math.sin(b)
                verts.append(((R + r * cb) * ca, (R + r * cb) * sa, r * sb))
                normals.append((cb * ca, cb * sa, sb))
        for i in range(seg_major):
            for j in range(seg_minor):
                a = i * seg_minor + j
                b = i * seg_minor + (j + 1) % seg_minor
                c = ((i + 1) % seg_major) * seg_minor + (j + 1) % seg_minor
                d = ((i + 1) % seg_major) * seg_minor + j
                faces.append((a, b, c, d))
        me = bpy.data.meshes.new(name)
        me.from_pydata(verts, [], faces)
        _finish(me, normals)
        _MESHES[key] = me
    o = bpy.data.objects.new(name, me)
    o.location = loc
    coll.objects.link(o)
    if parent is not None:
        o.parent = parent
    if mat is not None:
        assign(o, mat)
    return o


# ---------------------------------------------------------------- polygon prism (stars, arrows, icons)
def prism(name, coll, poly2d, depth, bevel=0.0, mat=None, loc=(0, 0, 0), parent=None):
    """Extrude a 2-D polygon (list of (x,y), CCW) to ``depth`` with a small soft bevel."""
    bm = bmesh.new()
    vs = [bm.verts.new((x, y, -depth / 2)) for x, y in poly2d]
    f = bm.faces.new(vs)
    res = bmesh.ops.extrude_face_region(bm, geom=[f])
    ext = [e for e in res["geom"] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=(0, 0, depth), verts=ext)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bevel, segments=3, affect="EDGES", profile=0.5)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    o = bpy.data.objects.new(name, me)
    o.location = loc
    coll.objects.link(o)
    if parent is not None:
        o.parent = parent
    if mat is not None:
        assign(o, mat)
    return o


def star_poly(r_out=1.0, r_in=0.5, n=5, round_pts=3):
    pts = []
    for i in range(2 * n):
        a = math.pi / 2 + math.pi * i / n
        r = r_out if i % 2 == 0 else r_in
        pts.append((r * math.cos(a), r * math.sin(a)))
    return pts


# ---------------------------------------------------------------- text
def font(path=None):
    path = path or FONT_BLACK
    if path not in _FONTS:
        _FONTS[path] = bpy.data.fonts.load(path)
    return _FONTS[path]


def text(name, coll, body, size=1.0, mat=None, loc=(0, 0, 0), extrude=0.0, bevel=0.0, align="CENTER",
         font_path=None, parent=None, spacing=1.0, line_spacing=1.0, align_y="CENTER"):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.font = font(font_path)
    cu.size = size
    cu.extrude = extrude
    cu.bevel_depth = bevel
    cu.bevel_resolution = 1
    cu.resolution_u = 5 if size < 0.45 else 8      # glyph outlines: plenty smooth at this size, 10x fewer triangles
    cu.align_x = align
    cu.align_y = align_y
    cu.space_character = spacing
    cu.space_line = line_spacing
    o = bpy.data.objects.new(name, cu)
    o.location = loc
    coll.objects.link(o)
    if parent is not None:
        o.parent = parent
    if mat is not None:
        assign(o, mat)
    return o


def text_width(body, size, font_path=None):
    """Approximate advance width of ``body`` at ``size`` using the font's own metrics."""
    from fontTools.ttLib import TTFont
    fp = font_path or FONT_BLACK
    tt = TTFont(fp)
    cmap = tt.getBestCmap()
    hmtx = tt["hmtx"]
    upm = tt["head"].unitsPerEm
    w = 0
    for ch in body:
        g = cmap.get(ord(ch))
        w += hmtx[g][0] if g else upm * 0.5
    return w / upm * size


# ---------------------------------------------------------------- tubes
def tube(name, coll, pts, radius, mat=None, resolution=6, caps=True, mapping="SPLINE", parent=None):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    cu.bevel_resolution = resolution
    cu.use_fill_caps = caps
    cu.resolution_u = 2
    cu.bevel_factor_mapping_start = mapping
    cu.bevel_factor_mapping_end = mapping
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for p, c in zip(sp.points, pts):
        p.co = (float(c[0]), float(c[1]), float(c[2]), 1.0)
        p.radius = 1.0
    o = bpy.data.objects.new(name, cu)
    coll.objects.link(o)
    if parent is not None:
        o.parent = parent
    if mat is not None:
        assign(o, mat)
    return o


# ---------------------------------------------------------------- lights
def point_light(name, coll, color, energy, radius=0.1, loc=(0, 0, 0), parent=None):
    L = bpy.data.lights.new(name, "POINT")
    L.color = color
    L.energy = energy
    L.shadow_soft_size = radius
    o = bpy.data.objects.new(name, L)
    o.location = loc
    coll.objects.link(o)
    if parent is not None:
        o.parent = parent
    return o


def area_light(name, coll, color, energy, size=2.0, loc=(0, 0, 0), rot=(0, 0, 0), size_y=None, parent=None, spread=None):
    L = bpy.data.lights.new(name, "AREA")
    L.color = color
    L.energy = energy
    L.size = size
    if size_y:
        L.shape = "RECTANGLE"
        L.size_y = size_y
    if spread is not None:
        L.spread = spread
    o = bpy.data.objects.new(name, L)
    o.location = loc
    o.rotation_euler = rot
    coll.objects.link(o)
    if parent is not None:
        o.parent = parent
    return o


def look_rot(from_pos, to_pos):
    """Euler for a light/object whose -Z axis points from ``from_pos`` towards ``to_pos``."""
    d = Vector(to_pos) - Vector(from_pos)
    return d.to_track_quat("-Z", "Y").to_euler()


# ---------------------------------------------------------------- bezel (hollow rounded frame)
def bezel_mesh(w, h, R, t, d, rb, seg_arc=10, seg_rb=4, name="bezel"):
    """Rounded-rect frame: footprint centre-line swept with a rounded-rect profile (t wide, d deep)."""
    key = ("bezel", round(w, 4), round(h, 4), round(R, 4), round(t, 4), round(d, 4), round(rb, 4))
    if key in _MESHES:
        return _MESHES[key]
    Rc = max(R - t / 2, 0.02)
    pts, nrm, _ = _footprint(w - t, h - t, Rc, seg_arc)
    rb = min(rb, t / 2 * 0.95, d / 2 * 0.95)
    # profile (offset along outward normal, z) going around a rounded rectangle, CCW, with normals
    prof, pn = [], []
    hx, hz = t / 2 - rb, d / 2 - rb
    corners = [((hx, hz), 0.0), ((-hx, hz), math.pi / 2), ((-hx, -hz), math.pi), ((hx, -hz), 3 * math.pi / 2)]
    for (ox, oz), a0 in corners:
        for k in range(seg_rb + 1):
            a = a0 + (math.pi / 2) * k / seg_rb
            n = (math.cos(a), math.sin(a))
            prof.append((ox + rb * n[0], oz + rb * n[1]))
            pn.append(n)
    N, P = len(pts), len(prof)
    verts, normals = [], []
    for i in range(N):
        for (px, pz), (nx, nz) in zip(prof, pn):
            v = pts[i] + nrm[i] * px
            verts.append((v[0], v[1], pz))
            nn = nrm[i] * nx
            normals.append((nn[0], nn[1], nz))
    faces = []
    for i in range(N):
        j = (i + 1) % N
        for k in range(P):
            m = (k + 1) % P
            faces.append((i * P + k, i * P + m, j * P + m, j * P + k))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    _finish(me, normals)
    _MESHES[key] = me
    return me


def bezel(name, coll, w, h, R, t, d, rb=None, mat=None, loc=(0, 0, 0), parent=None):
    me = bezel_mesh(w, h, R, t, d, rb if rb is not None else min(t, d) * 0.25)
    o = bpy.data.objects.new(name, me)
    o.location = loc
    coll.objects.link(o)
    if parent is not None:
        o.parent = parent
    if mat is not None:
        assign(o, mat)
    return o


# ---------------------------------------------------------------- cylinder & revolved solids
def cylinder(name, coll, radius, length, mat=None, loc=(0, 0, 0), parent=None, seg=64, axis="X"):
    """Smooth cylinder (closed) with its axis along local X (or Z). Radius/length baked into the mesh."""
    key = ("cyl", seg)
    if key in _MESHES:
        me = _MESHES[key]
    else:
        verts, faces, normals = [], [], []
        for i in range(seg):
            a = 2 * math.pi * i / seg
            ca, sa = math.cos(a), math.sin(a)
            verts += [(ca, sa, -0.5), (ca, sa, 0.5)]
            normals += [(ca, sa, 0), (ca, sa, 0)]
        for i in range(seg):
            j = (i + 1) % seg
            faces.append((2 * i, 2 * j, 2 * j + 1, 2 * i + 1))
        # caps (flat)
        c0 = len(verts)
        for z in (-0.5, 0.5):
            base = len(verts)
            for i in range(seg):
                a = 2 * math.pi * i / seg
                verts.append((math.cos(a), math.sin(a), z))
                normals.append((0, 0, 1 if z > 0 else -1))
            verts.append((0, 0, z)); normals.append((0, 0, 1 if z > 0 else -1))
            ctr = len(verts) - 1
            for i in range(seg):
                j = (i + 1) % seg
                faces.append((ctr, base + i, base + j) if z > 0 else (ctr, base + j, base + i))
        me = bpy.data.meshes.new(name)
        me.from_pydata(verts, [], faces)
        _finish(me, normals)
        _MESHES[key] = me
    o = bpy.data.objects.new(name, me)
    o.location = loc
    if axis == "X":
        o.rotation_euler = (0, math.pi / 2, 0)
        o.scale = (radius, radius, length)
    else:
        o.scale = (radius, radius, length)
    coll.objects.link(o)
    if parent is not None:
        o.parent = parent
    if mat is not None:
        assign(o, mat)
    return o


def revolve(name, coll, profile, mat=None, loc=(0, 0, 0), parent=None, seg=48, lean=0.0, zs=None):
    """Solid of revolution about Z from ``profile`` = [(r, z), ...] (r>=0), optional lean x-offset(z)."""
    verts, faces = [], []
    n = len(profile)
    for (r, z) in profile:
        off = lean * (z ** 2)
        for i in range(seg):
            a = 2 * math.pi * i / seg
            verts.append((r * math.cos(a) + off, r * math.sin(a), z))
    for k in range(n - 1):
        for i in range(seg):
            j = (i + 1) % seg
            faces.append((k * seg + i, k * seg + j, (k + 1) * seg + j, (k + 1) * seg + i))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    for p in me.polygons:
        p.use_smooth = True
    o = bpy.data.objects.new(name, me)
    o.location = loc
    coll.objects.link(o)
    if parent is not None:
        o.parent = parent
    if mat is not None:
        assign(o, mat)
    return o


def gem(name, coll, mat=None, loc=(0, 0, 0), parent=None, n=8):
    """Faceted diamond (flat-shaded): table, crown, girdle, pavilion. Local +Z is up, unit radius."""
    verts = [(0, 0, 0.45)]
    for i in range(n):                       # table ring
        a = 2 * math.pi * i / n
        verts.append((0.5 * math.cos(a), 0.5 * math.sin(a), 0.45))
    for i in range(n):                       # girdle ring (rotated half a step for brilliant-cut look)
        a = 2 * math.pi * (i + 0.5) / n
        verts.append((math.cos(a), math.sin(a), 0.0))
    verts.append((0, 0, -1.0))
    b = len(verts) - 1
    faces = []
    for i in range(n):
        j = (i + 1) % n
        T0, T1 = 1 + i, 1 + j
        G0, G1 = 1 + n + i, 1 + n + j
        faces.append((0, T0, T1))            # table
        faces.append((T0, G0, G1, T1))       # crown
        faces.append((G0, b, G1))            # pavilion
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.update()
    o = bpy.data.objects.new(name, me)
    o.location = loc
    coll.objects.link(o)
    if parent is not None:
        o.parent = parent
    if mat is not None:
        assign(o, mat)
    return o

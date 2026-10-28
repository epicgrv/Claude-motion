"""Physically-parametrised materials (Principled BSDF) with named nodes for animation."""
from __future__ import annotations

import bpy

from .config import lin


def _p(mat):
    return mat.node_tree.nodes["P"]


def principled(name, color, rough=0.5, metal=0.0, coat=0.0, coat_rough=0.12, sheen=0.0,
               spec=0.5, emit=None, emit_strength=0.0, alpha=1.0, rvar=0.0, sss=0.0,
               aniso=0.0):
    """Create a Principled material. ``color`` may be a palette key / hex / linear tuple.

    ``rvar`` adds subtle low-frequency roughness variation (noise) so surfaces are not CG-flat.
    Node named "P" is the BSDF; use ``set_input`` / animation paths on it.
    """
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (600, 0)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.name = "P"
    b.location = (300, 0)
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    col = lin(color) if isinstance(color, str) else tuple(color)
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Coat Roughness"].default_value = coat_rough
    b.inputs["Sheen Weight"].default_value = sheen
    b.inputs["Specular IOR Level"].default_value = spec
    b.inputs["Alpha"].default_value = alpha
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss
        b.inputs["Subsurface Radius"].default_value = (0.05, 0.05, 0.02)
        b.inputs["Subsurface Scale"].default_value = 0.2
    if aniso:
        b.inputs["Anisotropic"].default_value = aniso
    if emit is not None:
        ec = lin(emit) if isinstance(emit, str) else tuple(emit)
        b.inputs["Emission Color"].default_value = (*ec, 1)
        b.inputs["Emission Strength"].default_value = emit_strength
    if rvar:
        tc = nt.nodes.new("ShaderNodeTexCoord")
        tc.location = (-400, -200)
        nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.location = (-200, -200)
        nz.inputs["Scale"].default_value = 3.0
        nz.inputs["Detail"].default_value = 4.0
        nz.inputs["Roughness"].default_value = 0.6
        nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.location = (50, -200)
        mr.inputs["To Min"].default_value = max(0.0, rough - rvar)
        mr.inputs["To Max"].default_value = min(1.0, rough + rvar)
        nt.links.new(nz.outputs["Fac"], mr.inputs["Value"])
        nt.links.new(mr.outputs["Result"], b.inputs["Roughness"])
    if alpha < 1.0:
        m.blend_method = "BLEND" if hasattr(m, "blend_method") else None
    return m


def emissive(name, color, strength=5.0, mix_dark=0.0):
    """Pure emission material; node "E" holds colour/strength (animatable)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    e = nt.nodes.new("ShaderNodeEmission")
    e.name = "E"
    col = lin(color) if isinstance(color, str) else tuple(color)
    e.inputs["Color"].default_value = (*col, 1)
    e.inputs["Strength"].default_value = strength
    nt.links.new(e.outputs["Emission"], out.inputs["Surface"])
    return m


def path_color(mat):
    return 'nodes["P"].inputs["Base Color"].default_value'


def path_emit_color(mat):
    return 'nodes["P"].inputs["Emission Color"].default_value'


def path_emit_strength(mat):
    return 'nodes["P"].inputs["Emission Strength"].default_value'


def path_rough(mat):
    return 'nodes["P"].inputs["Roughness"].default_value'


def e_strength():
    return 'nodes["E"].inputs["Strength"].default_value'


def e_color():
    return 'nodes["E"].inputs["Color"].default_value'


def clone(mat, name):
    m = mat.copy()
    m.name = name
    return m


def floor(name, color, rough, radius, fade0=0.30, coat=0.0):
    """Glossy ground disc whose alpha falls off radially (object space) - reflections that end softly."""
    m = principled(name, color, rough, coat=coat, coat_rough=0.05, spec=0.6)
    nt = m.node_tree
    b = nt.nodes["P"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vl = nt.nodes.new("ShaderNodeVectorMath")
    vl.operation = "LENGTH"
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = radius * fade0
    mr.inputs["From Max"].default_value = radius
    mr.inputs["To Min"].default_value = 1.0
    mr.inputs["To Max"].default_value = 0.0
    nt.links.new(tc.outputs["Object"], vl.inputs[0])
    nt.links.new(vl.outputs["Value"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], b.inputs["Alpha"])
    return m

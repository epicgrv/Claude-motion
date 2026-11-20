"""True-3D shot specs for the Pepsi-jet short (Blender world units = metres).

Each spec: set (builder in sets_pepsi), frames (@30fps), cam/target keyframes, lens, anchors (3D points where 2D
characters/props stand), occluders (object-name prefixes that must hide characters), optional anim(frames) hook."""
from __future__ import annotations

import math

import bpy


def _obj(name):
    return bpy.data.objects.get(name)


# ------------------------------------------------------------------------------------------- prop animation hooks
def anim_jet_hover(frames):
    """Harrier hovering in its own downwash: bob, wobble, slow yaw drift."""
    j = _obj("Jet")
    base = j.location.copy()
    rot = j.rotation_euler.copy()
    for f in range(0, frames, 2):
        t = f / 30
        j.location = (base.x + 0.15 * math.sin(t * 2.1), base.y, base.z + 0.25 * math.sin(t * 5.5))
        j.rotation_euler = (rot.x + 0.03 * math.sin(t * 4.3), rot.y + 0.05 * math.sin(t * 3.1), rot.z + 0.04 * math.sin(t * 1.7))
        j.keyframe_insert("location", frame=f)
        j.keyframe_insert("rotation_euler", frame=f)


def anim_none(frames):
    return None


# ------------------------------------------------------------------------------------------- shot specs
SPECS = {
    # HOOK: low dolly toward John on the golden street, Harrier hovering behind him
    "H01_hook": dict(set="P20_hero_street", frames=43, lens=22,
                     cam=[(0, (0.9, -7.2, 0.55)), (42, (0.25, -5.2, 0.95))],
                     target=[(0, (0.0, 10, 3.0)), (42, (0.0, 10, 3.6))],
                     anchors={"JOHN": (0.25, -1.6, 0.0)}, occluders=[], anim="anim_jet_hover"),
    # KITCHEN: slow orbit around the table, John sitting behind it punching the calculator
    "K12_calc": dict(set="P06_kitchen", frames=49, lens=24,
                     cam=[(0, (-1.3, -2.3, 1.15)), (48, (0.9, -2.15, 1.3))],
                     target=[(0, (0.0, 0.95, 0.95)), (48, (0.1, 0.9, 1.0))],
                     anchors={"JOHN": (0.0, 1.35, 0.0), "CALC": (0.15, 0.45, 0.78)},
                     occluders=["Table", "Chair", "Mug", "Apple", "Notepad", "Pencil"]),
    # OFFICE: crane up past the desk onto the laughing exec
    "O27_exec": dict(set="P11_exec_office", frames=65, lens=26,
                     cam=[(0, (0.8, -3.6, 0.85)), (64, (-0.35, -2.7, 1.5))],
                     target=[(0, (0.0, 1.3, 1.25)), (64, (0.0, 1.45, 1.5))],
                     anchors={"EXEC": (0.0, 1.5, 0.0)},
                     occluders=["Desk", "Blotter", "Lamp", "Pen", "Opener", "Trophy"]),
}

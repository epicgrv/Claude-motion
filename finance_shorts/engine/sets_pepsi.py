"""Set builders for the Pepsi-jet short. Each function builds one set; set3d.main() renders it.
Blender units are metres; z is up; cameras look roughly along +y."""
from __future__ import annotations

import math
import random

from finance_shorts.engine.set3d import (area, box, brick, camera, car, chair, checker, chrome, cyl, emit, glass, house,
                                         jet, mat, noisy, plane, point, prism, room, sphere, spot, stripes, sun, table_round,
                                         torus, tree, wood, world)

R = math.radians


def _plant(loc, s=1.0):
    x, y, z = loc
    cyl("Pot", 0.22 * s, 0.4 * s, (x, y, z + 0.2 * s), mat("Terracotta", (0.55, 0.25, 0.12), 0.7), r2=0.17 * s, bevel=0.01)
    lf = noisy("PlantLeaf", (0.15, 0.4, 0.12), (0.05, 0.2, 0.05), 8, 0.5, 0.6)
    for i in range(7):
        a = i * 0.9
        sphere("Leaf", 0.18 * s, (x + math.cos(a) * 0.15 * s, y + math.sin(a) * 0.15 * s, z + (0.55 + 0.1 * (i % 3)) * s), lf,
               scale=(1, 0.6, 1.4))


# ------------------------------------------------------------------------------------------------ interiors
def P06_kitchen():
    world((0.008, 0.01, 0.02), 1.0)
    room(6.5, 6.0, 2.8, checker("KitFloor", (0.82, 0.76, 0.62), (0.07, 0.06, 0.06), 3.2, 0.1),
         stripes("Wallpaper", (0.2, 0.36, 0.33), (0.16, 0.29, 0.27), 16, 0.8, axis="X"))
    cab = wood("CabWood", (0.55, 0.32, 0.15), (0.38, 0.2, 0.08), 0.35, coat=0.5)
    top = noisy("Counter", (0.88, 0.84, 0.74), (0.72, 0.68, 0.6), 30, 0.25, 0.05)
    box("Lower", (3.6, 0.6, 0.9), (0.7, 2.7, 0.45), cab, bevel=0.02)
    box("Top", (3.7, 0.66, 0.05), (0.7, 2.7, 0.92), top, bevel=0.01)
    for i in range(5):
        box("Door", (0.62, 0.02, 0.7), (-0.8 + i * 0.7, 2.39, 0.45), cab, bevel=0.015)
        cyl("Knob", 0.02, 0.04, (-0.6 + i * 0.7, 2.37, 0.62), chrome(), rot=(R(90), 0, 0))
    box("Upper", (2.0, 0.35, 0.75), (-0.2, 2.82, 2.0), cab, bevel=0.02)
    fr = mat("Avocado", (0.36, 0.42, 0.1), 0.18, coat=0.9)
    box("Fridge", (0.9, 0.75, 1.9), (-2.4, 2.55, 0.95), fr, bevel=0.07)
    box("FridgeGap", (0.91, 0.01, 0.02), (-2.4, 2.17, 1.32), mat("Gap", (0.02, 0.02, 0.02), 0.6), bevel=0)
    box("Handle", (0.04, 0.05, 0.5), (-2.05, 2.15, 1.05), chrome(), bevel=0.01)
    for i, c in enumerate([(0.9, 0.2, 0.15), (0.95, 0.8, 0.2), (0.2, 0.5, 0.9)]):  # fridge magnets
        cyl("Magnet", 0.035, 0.02, (-2.6 + i * 0.12, 2.16, 1.55 - i * 0.07), mat(f"Mag{i}", c, 0.4), rot=(R(90), 0, 0))
    box("WinFrame", (1.3, 0.08, 1.0), (1.7, 2.98, 1.75), mat("WinWhite", (0.9, 0.88, 0.82), 0.4), bevel=0.02)
    box("WinGlass", (1.15, 0.02, 0.85), (1.7, 2.93, 1.75), emit("Night", (0.03, 0.06, 0.18), 1.0), bevel=0)
    box("Mullion", (0.03, 0.03, 0.85), (1.7, 2.91, 1.75), mat("WinWhite"), bevel=0)
    sphere("Moon", 0.08, (1.9, 2.92, 2.0), emit("Moon", (0.9, 0.95, 1.0), 6))
    cyl("Clock", 0.22, 0.05, (-0.9, 2.97, 2.3), mat("ClockFace", (0.95, 0.94, 0.88), 0.3), rot=(R(90), 0, 0))
    torus("ClockRim", 0.22, 0.025, (-0.9, 2.94, 2.3), chrome(), rot=(R(90), 0, 0))
    # counter props: toaster, kettle, cereal boxes, fruit
    box("Toaster", (0.32, 0.2, 0.22), (1.6, 2.65, 1.06), chrome("Toaster", (0.85, 0.85, 0.88), 0.08), bevel=0.05)
    cyl("Kettle", 0.13, 0.24, (2.2, 2.7, 1.07), mat("Enamel", (0.85, 0.2, 0.12), 0.25, coat=0.8), r2=0.09, bevel=0.02)
    for i, c in enumerate([(0.9, 0.55, 0.1), (0.15, 0.35, 0.8)]):
        box("Cereal", (0.24, 0.08, 0.36), (0.4 + i * 0.3, 2.85, 1.13), mat(f"Box{i}", c, 0.5), bevel=0.005)
    tw = wood("Table", (0.52, 0.29, 0.12), (0.32, 0.16, 0.06), 0.25, coat=0.7, scale=3)
    table_round((0, 0.7, 0), 0.7, 0.75, tw, chrome("TableChrome"))
    vinyl = mat("Vinyl", (0.62, 0.14, 0.08), 0.3, coat=0.6)
    for a in (R(200), R(340)):
        chair((math.cos(a) * 1.05, 0.7 + math.sin(a) * 1.05 + 0.6, 0), a + R(90), vinyl, chrome())
    cyl("Mug", 0.05, 0.1, (-0.35, 0.6, 0.83), mat("MugW", (0.92, 0.9, 0.85), 0.3, coat=0.5), bevel=0.005)
    sphere("Apple", 0.06, (-0.15, 0.95, 0.83), mat("Apple", (0.75, 0.08, 0.05), 0.3, coat=0.6))
    box("Notepad", (0.32, 0.24, 0.015), (0.25, 0.55, 0.785), mat("Paper", (0.95, 0.93, 0.82), 0.7), rot=(0, 0, R(12)), bevel=0.002)
    cyl("Pencil", 0.008, 0.2, (0.45, 0.62, 0.79), mat("PencilY", (0.95, 0.75, 0.1), 0.4), rot=(0, R(90), R(30)))
    # pendant lamp = key light
    cyl("Cord", 0.006, 0.9, (0, 0.7, 2.35), mat("Cord", (0.02, 0.02, 0.02)))
    cyl("Shade", 0.34, 0.3, (0, 0.7, 1.82), mat("Shade", (0.9, 0.5, 0.1), 0.35, trans=0.2), r2=0.08)
    sphere("Bulb", 0.07, (0, 0.7, 1.72), emit("Bulb", (1, 0.75, 0.45), 60))
    spot("Pendant", (0, 0.7, 1.74), (0, 0.7, 0), 650, (1, 0.68, 0.38), angle=100, blend=0.8, radius=0.08)
    point("ShadeGlow", (0, 0.7, 1.95), 25, (1, 0.6, 0.3), 0.2)
    area("WindowSpill", (1.7, 2.7, 1.75), (0.3, 0, 0.6), 1.0, 25, (0.35, 0.5, 1.0))
    area("MoonRim", (-3.0, -1.5, 2.5), (0, 1, 1), 2.0, 35, (0.4, 0.5, 1.0))
    camera((-0.35, -2.5, 1.2), (-0.15, 0.9, 0.95), lens=21, dof=3.2, fstop=3.5)
    return {"fg": ["Table", "Chair", "Mug", "Apple", "Notepad", "Pencil"]}


def P08_diner():
    world((0.02, 0.015, 0.02), 1.0)
    room(7.0, 7.0, 3.0, checker("DinerFloor", (0.9, 0.87, 0.8), (0.06, 0.05, 0.05), 3.0, 0.08),
         mat("DinerWall", (0.92, 0.85, 0.7), 0.6))
    # teal tile wainscot + chrome trim
    box("Wainscot", (7.0, 0.04, 1.1), (0, 3.47, 0.55), noisy("TealTile", (0.1, 0.5, 0.5), (0.08, 0.42, 0.42), 60, 0.2, 0.1),
        bevel=0)
    box("Trim", (7.0, 0.06, 0.05), (0, 3.45, 1.12), chrome(), bevel=0.01)
    # windows with sunset
    for x in (-2.2, 0, 2.2):
        box("Win", (1.8, 0.04, 1.2), (x, 3.47, 1.85), emit("Sunset", (1.0, 0.5, 0.22), 2.2), bevel=0)
        box("WinFrame", (1.9, 0.06, 0.06), (x, 3.44, 2.47), chrome(), bevel=0.01)
    area("SunsetKey", (0, 3.2, 1.9), (0, 0, 0.8), 6.0, 350, (1.0, 0.55, 0.28), size_y=1.2)
    # neon strip
    cyl("Neon", 0.03, 6.5, (0, 3.4, 2.75), emit("NeonPink", (1.0, 0.2, 0.6), 30), rot=(0, R(90), 0))
    point("NeonL", (0, 3.0, 2.7), 120, (1.0, 0.25, 0.65), 1.0)
    # booth (foreground, empty) + table
    red = mat("BoothRed", (0.7, 0.05, 0.05), 0.3, coat=0.8)
    for side in (-1, 1):
        box("BoothSeat", (0.6, 1.6, 0.45), (side * 1.15, 1.2, 0.225), red, bevel=0.08)
        box("BoothBack", (0.22, 1.6, 0.95), (side * 1.5, 1.2, 0.85), red, bevel=0.1)
    formica = noisy("Formica", (0.62, 0.85, 0.82), (0.55, 0.78, 0.75), 80, 0.2, 0.02)
    box("Table", (1.4, 1.2, 0.05), (0, 1.2, 0.78), formica, bevel=0.02)
    box("TableEdge", (1.42, 1.22, 0.03), (0, 1.2, 0.76), chrome(), bevel=0.01)
    cyl("TableLeg", 0.05, 0.75, (0, 1.2, 0.375), chrome())
    for x in (-0.4, 0.4):
        cyl("Mug", 0.05, 0.1, (x, 0.75, 0.86), mat("MugW", (0.95, 0.93, 0.88), 0.25, coat=0.6), bevel=0.005)
        cyl("Coffee", 0.045, 0.005, (x, 0.75, 0.905), mat("Coffee", (0.12, 0.05, 0.02), 0.05))
    box("Napkins", (0.14, 0.09, 0.16), (0.05, 1.12, 0.89), chrome(), bevel=0.02)
    cyl("Ketchup", 0.035, 0.2, (-0.2, 1.15, 0.9), mat("Ketchup", (0.75, 0.05, 0.03), 0.2, trans=0.3), r2=0.025)
    cyl("Mustard", 0.035, 0.2, (-0.1, 1.17, 0.9), mat("Mustard", (0.95, 0.75, 0.05), 0.3), r2=0.025)
    # counter + stools in the back right
    box("Counter", (0.6, 3.0, 1.05), (2.9, 1.5, 0.52), mat("CounterRed", (0.6, 0.06, 0.05), 0.35, coat=0.6), bevel=0.04)
    box("CounterTop", (0.75, 3.1, 0.05), (2.9, 1.5, 1.07), formica, bevel=0.01)
    for i in range(4):
        cyl("Stool", 0.2, 0.08, (2.3, 0.4 + i * 0.75, 0.75), red, bevel=0.03)
        cyl("StoolPost", 0.03, 0.72, (2.3, 0.4 + i * 0.75, 0.36), chrome())
    # pendant lamps
    for x in (-1.5, 1.5):
        cyl("Pend", 0.18, 0.18, (x, 1.4, 2.4), chrome(), r2=0.05)
        sphere("PBulb", 0.05, (x, 1.4, 2.3), emit("Bulb2", (1, 0.8, 0.5), 50))
        point("PLight", (x, 1.4, 2.25), 80, (1, 0.75, 0.45), 0.1)
    area("Fill", (0, -3, 2.5), (0, 1, 1), 3, 80, (0.6, 0.7, 1.0))
    camera((0.2, -2.6, 1.35), (0, 1.5, 0.95), lens=20, dof=3.6, fstop=4)
    return {"fg": ["Booth", "Table", "Mug", "Coffee", "Napkins", "Ketchup", "Mustard"]}


def P11_exec_office():
    world((0.6, 0.75, 0.95), 0.4)
    panel = wood("Panel", (0.38, 0.17, 0.07), (0.22, 0.09, 0.03), 0.35, scale=2, planks=0.5, coat=0.4)
    room(9.0, 8.0, 3.6, noisy("ExecCarpet", (0.32, 0.06, 0.08), (0.22, 0.03, 0.05), 90, 0.95, 0.4), panel)
    # window wall with skyline
    box("WinWall", (6.0, 0.05, 3.0), (0, 3.95, 1.8), glass("OfficeGlass", (0.9, 0.95, 1.0), 0.02), bevel=0)
    for x in (-3, -1.5, 0, 1.5, 3):
        box("Mull", (0.08, 0.1, 3.0), (x, 3.92, 1.8), mat("Bronze", (0.25, 0.18, 0.1), 0.3, metal=1.0), bevel=0.01)
    plane("Sky", (60, 30), (0, 30, 10), emit("SkyDay", (0.55, 0.75, 1.0), 2.0), rot=(R(90), 0, 0))
    random.seed(3)
    city = mat("City", (0.45, 0.55, 0.68), 0.3, metal=0.6)
    for i in range(18):
        h = random.uniform(6, 24)
        box("Bldg", (random.uniform(2, 4), 2.5, h), (-18 + i * 2.2, random.uniform(14, 26), h / 2 - 3), city, bevel=0)
    sun("Sun", (55, 0, 200), 3.5, (1.0, 0.85, 0.65))
    # desk
    mahog = wood("Mahogany", (0.42, 0.12, 0.05), (0.2, 0.04, 0.02), 0.15, scale=2.5, coat=1.0)
    box("Desk", (3.4, 1.3, 0.82), (0, 0.9, 0.41), mahog, bevel=0.05)
    box("DeskTop", (3.6, 1.45, 0.06), (0, 0.9, 0.85), mahog, bevel=0.02)
    box("Blotter", (1.2, 0.6, 0.01), (0, 0.85, 0.885), mat("Leather", (0.06, 0.18, 0.1), 0.5), bevel=0.003)
    # chair (huge, high back - visual joke: way too big)
    leather = mat("ChairLeather", (0.15, 0.06, 0.03), 0.4, coat=0.5)
    box("ChairBack", (1.3, 0.3, 2.3), (0, 2.1, 1.55), leather, bevel=0.15)
    box("ChairSeat", (1.1, 0.9, 0.25), (0, 1.75, 0.55), leather, bevel=0.1)
    # banker's lamp
    cyl("LampBase", 0.1, 0.03, (-1.2, 0.8, 0.9), mat("Brass", (0.8, 0.6, 0.25), 0.2, metal=1.0))
    cyl("LampStem", 0.012, 0.35, (-1.2, 0.8, 1.07), mat("Brass"))
    cyl("LampShade", 0.11, 0.42, (-1.2, 0.72, 1.27), mat("GreenGlass", (0.05, 0.4, 0.15), 0.1, trans=0.5), rot=(0, R(90), 0))
    point("LampLight", (-1.2, 0.72, 1.18), 60, (1, 0.8, 0.5), 0.05)
    # pen set + letter opener + golf trophy
    box("PenBase", (0.25, 0.12, 0.05), (0.9, 0.7, 0.91), mat("Marble", (0.9, 0.9, 0.88), 0.15), bevel=0.01)
    for dx in (-0.05, 0.05):
        cyl("Pen", 0.008, 0.2, (0.9 + dx, 0.72, 1.02), mat("PenBlack", (0.02, 0.02, 0.02), 0.2), rot=(R(20), 0, 0))
    cyl("Opener", 0.006, 0.22, (0.5, 0.6, 0.89), chrome(), rot=(0, R(90), R(25)))
    cyl("TrophyCup", 0.12, 0.25, (1.4, 1.1, 1.05), mat("Gold", (1.0, 0.75, 0.3), 0.15, metal=1.0), r2=0.06)
    cyl("TrophyBase", 0.09, 0.12, (1.4, 1.1, 0.94), mat("Marble"))
    # globe + plant
    sphere("Globe", 0.35, (-3.2, 2.6, 1.25), noisy("GlobeTex", (0.15, 0.45, 0.2), (0.1, 0.25, 0.6), 2.5, 0.3, 0.1))
    cyl("GlobeStand", 0.04, 0.9, (-3.2, 2.6, 0.45), mat("Brass"))
    _plant((3.4, 2.8, 0), 1.6)
    area("Key", (2.5, -2.0, 3.0), (0, 1, 1), 2.5, 500, (1.0, 0.85, 0.7))
    area("WinFill", (0, 3.5, 2.0), (0, 0, 1), 5, 300, (0.75, 0.85, 1.0))
    camera((0.2, -3.6, 1.15), (0, 1.2, 1.2), lens=22, dof=4.5, fstop=4)
    return {"fg": ["Desk", "Blotter", "Lamp", "Pen", "Opener", "Trophy"]}


def P14_courtroom():
    world((0.03, 0.025, 0.02), 1.0)
    panel = wood("CourtPanel", (0.45, 0.24, 0.1), (0.3, 0.14, 0.05), 0.35, scale=2, planks=0.6, coat=0.4)
    room(12.0, 12.0, 6.0, noisy("CourtCarpet", (0.4, 0.08, 0.06), (0.28, 0.04, 0.03), 80, 0.95, 0.3),
         panel, mat("CourtCeil", (0.82, 0.76, 0.62), 0.8))
    oak = wood("Oak", (0.55, 0.32, 0.14), (0.35, 0.18, 0.07), 0.3, scale=3, coat=0.6)
    # raised bench
    box("Dais", (6.0, 2.5, 0.5), (0, 4.5, 0.25), oak, bevel=0.03)
    box("Bench", (4.6, 0.9, 1.4), (0, 4.0, 1.2), oak, bevel=0.05)
    box("BenchTop", (4.8, 1.1, 0.08), (0, 4.0, 1.93), oak, bevel=0.02)
    for x in (-1.5, 0, 1.5):
        box("Inset", (1.2, 0.03, 0.9), (x, 3.54, 1.15), wood("Inset", (0.4, 0.2, 0.08), (0.25, 0.11, 0.04), 0.3, scale=4), bevel=0.02)
    leather = mat("CourtLeather", (0.12, 0.05, 0.03), 0.35, coat=0.6)
    box("JudgeChair", (1.0, 0.3, 2.2), (0, 5.2, 1.6), leather, bevel=0.12)
    # seal (blank, gold) + flag
    cyl("Seal", 0.8, 0.08, (0, 5.95, 3.9), mat("SealGold", (0.85, 0.65, 0.25), 0.25, metal=1.0), rot=(R(90), 0, 0))
    torus("SealRim", 0.8, 0.06, (0, 5.9, 3.9), mat("SealGold"), rot=(R(90), 0, 0))
    cyl("SealInner", 0.55, 0.1, (0, 5.92, 3.9), mat("SealBlue", (0.08, 0.15, 0.35), 0.4), rot=(R(90), 0, 0))
    cyl("FlagPole", 0.04, 3.4, (3.3, 4.5, 1.7), mat("Brass2", (0.8, 0.6, 0.25), 0.2, metal=1.0))
    sphere("FlagTop", 0.09, (3.3, 4.5, 3.45), mat("Brass2"))
    flag = stripes("FlagStripes", (0.7, 0.05, 0.08), (0.95, 0.94, 0.9), 6.5, 0.7, axis="Z")
    box("Flag", (0.03, 1.3, 1.8), (3.3, 4.5, 2.4), flag, rot=(0, 0, R(20)), bevel=0)
    box("Canton", (0.04, 0.6, 0.95), (3.31, 4.22, 2.82), mat("Canton", (0.08, 0.12, 0.35), 0.7), rot=(0, 0, R(20)), bevel=0)
    # counsel tables + rail + gallery
    for x in (-2.4, 2.4):
        box("Counsel", (2.2, 1.0, 0.06), (x, 0.8, 0.78), oak, bevel=0.02)
        box("CounselBase", (2.0, 0.9, 0.72), (x, 0.8, 0.38), oak, bevel=0.02)
        cyl("Mic", 0.01, 0.3, (x + 0.4, 0.6, 0.95), mat("Black", (0.02, 0.02, 0.02), 0.4), rot=(R(25), 0, 0))
    box("Rail", (11.0, 0.12, 0.1), (0, -0.6, 0.95), oak, bevel=0.02)
    for i in range(16):
        cyl("Baluster", 0.035, 0.9, (-5 + i * 0.66, -0.6, 0.45), oak)
    # tall windows (left wall) = god-ray key
    for y in (-1.5, 1.5):
        box("TallWin", (0.05, 1.4, 3.5), (-5.97, y, 3.0), emit("CourtWin", (1.0, 0.85, 0.6), 6), bevel=0)
    area("WinKey", (-5.5, 0, 3.2), (0, 1.5, 1.0), 3, 1400, (1.0, 0.82, 0.6), size_y=3.5)
    # brass lamps on bench
    for x in (-1.8, 1.8):
        cyl("BLamp", 0.12, 0.08, (x, 3.9, 2.25), mat("GreenGlass2", (0.05, 0.4, 0.15), 0.1, trans=0.5), rot=(0, R(90), 0))
        point("BLampL", (x, 3.9, 2.15), 40, (1, 0.8, 0.5), 0.05)
    area("Fill", (0, -5, 4), (0, 3, 1.5), 4, 400, (0.8, 0.85, 1.0))
    camera((0.3, -4.8, 1.55), (0, 3.0, 1.9), lens=22, dof=6, fstop=5)
    return {"fg": ["Bench", "Inset", "Counsel", "Mic", "Rail", "Baluster", "BLamp"]}


def P18_school_bus():
    world((0.7, 0.85, 1.0), 1.0)
    ivory = mat("BusWall", (0.86, 0.82, 0.68), 0.5)
    plane("BusFloor", (2.5, 12), (0, 2, 0), noisy("BusRubber", (0.22, 0.22, 0.2), (0.12, 0.12, 0.11), 120, 0.8, 0.4))
    cyl("BusRoof", 1.25, 12, (0, 2, 1.25), mat("BusCeil", (0.9, 0.88, 0.8), 0.6), rot=(R(90), 0, 0))
    for side in (-1, 1):
        box("Wall", (0.05, 12, 1.0), (side * 1.25, 2, 0.5), ivory, bevel=0)
        for i in range(9):
            box("Window", (0.04, 0.9, 0.6), (side * 1.24, -2.5 + i * 1.1, 1.35), emit("BusSky", (0.85, 0.92, 1.0), 2.2), bevel=0)
            box("WinPost", (0.06, 0.18, 0.75), (side * 1.22, -2.5 + i * 1.1 + 0.55, 1.35), ivory, bevel=0.02)
        for i in range(8):
            y = -2.6 + i * 1.0
            seat = mat("BusSeat", (0.15, 0.38, 0.22), 0.4, coat=0.5)
            box("Seat", (0.78, 0.42, 0.16), (side * 0.78, y, 0.45), seat, bevel=0.06)
            box("SeatBack", (0.78, 0.12, 0.55), (side * 0.78, y + 0.25, 0.75), seat, bevel=0.06)
    # front: windshield, dashboard, driver seat, steering wheel
    box("Windshield", (2.4, 0.05, 1.0), (0, 8.0, 1.45), emit("Road", (1.0, 0.92, 0.75), 5), bevel=0)
    box("Dash", (2.4, 0.6, 0.85), (0, 7.6, 0.42), mat("Dash", (0.12, 0.12, 0.13), 0.6), bevel=0.05)
    box("DriverSeat", (0.6, 0.55, 0.15), (-0.7, 6.6, 0.55), mat("DriverSeat", (0.1, 0.1, 0.12), 0.5), bevel=0.05)
    box("DriverBack", (0.6, 0.15, 0.8), (-0.7, 6.3, 0.95), mat("DriverSeat"), bevel=0.06)
    torus("Wheel", 0.28, 0.03, (-0.7, 7.15, 1.05), mat("Black2", (0.03, 0.03, 0.03), 0.4), rot=(R(55), 0, 0))
    cyl("Column", 0.04, 0.6, (-0.7, 7.35, 0.85), mat("Black2"), rot=(R(55), 0, 0))
    cyl("DoorLever", 0.02, 0.6, (0.6, 7.2, 0.9), chrome(), rot=(R(30), 0, 0))
    sphere("LeverKnob", 0.05, (0.6, 7.05, 1.15), mat("RedKnob", (0.8, 0.05, 0.05), 0.3))
    box("Mirror", (0.5, 0.04, 0.15), (0, 7.8, 2.05), chrome("Mirror", (0.9, 0.9, 0.9), 0.02), bevel=0.02)
    sun("Sun", (55, 0, 140), 4.0, (1.0, 0.85, 0.6))
    area("Fill", (0, 0, 2.2), (0, 3, 0), 2.0, 50, (1.0, 0.95, 0.85), size_y=8)
    camera((0.0, -3.0, 1.55), (-0.25, 6.5, 1.0), lens=24, dof=8.0, fstop=6)


# ------------------------------------------------------------------------------------------------ exteriors
def _sky(top=(0.18, 0.4, 0.85), mid=(0.55, 0.72, 0.95), hor=(1.0, 0.8, 0.55), s=1.0):
    world(sky=[(0.0, hor), (0.4, mid), (1.0, top)], strength=s)


def _street(asphalt_rough=0.3, wet=True):
    a = noisy("Asphalt", (0.2, 0.2, 0.21), (0.08, 0.08, 0.09), 60, asphalt_rough, 0.5)
    if wet:
        a.node_tree.nodes["Principled BSDF"].inputs["Coat Weight"].default_value = 0.6
    plane("Street", (9, 160), (0, 40, 0), a)
    for i in range(40):
        box("Lane", (0.14, 1.6, 0.01), (0, -6 + i * 3.2, 0.005), mat("LaneY", (0.95, 0.75, 0.1), 0.5), bevel=0)
    conc = noisy("Concrete", (0.72, 0.7, 0.66), (0.6, 0.58, 0.55), 25, 0.8, 0.2)
    grass = noisy("Grass", (0.3, 0.55, 0.15), (0.15, 0.35, 0.08), 70, 0.9, 0.6)
    for s in (-1, 1):
        box("Curb", (0.3, 160, 0.15), (s * 4.6, 40, 0.075), conc, bevel=0.02)
        box("Sidewalk", (2.0, 160, 0.12), (s * 5.8, 40, 0.06), conc, bevel=0)
        plane("Lawn", (30, 160), (s * 21.8, 40, 0.01), grass)


def P02_street_jet():
    _sky((0.12, 0.35, 0.85), (0.5, 0.7, 0.95), (1.0, 0.72, 0.45), 1.2)
    _street()
    cols = [(0.86, 0.82, 0.72), (0.65, 0.78, 0.85), (0.92, 0.88, 0.7), (0.75, 0.62, 0.55)]
    for i in range(6):
        for s in (-1, 1):
            house((s * 15, 4 + i * 16, 0), wall=cols[(i + (s > 0)) % 4], rotz=R(90 if s < 0 else -90))
            tree((s * 8.5, 10 + i * 16, 0), 6.5, seed=i * 2 + (s > 0))
    car((-3.4, 6, 0), (0.6, 0.1, 0.08))
    car((3.4, 20, 0), (0.15, 0.3, 0.6), rotz=R(180))
    jet((0, 10, 13), rot=(R(-8), R(10), R(180)), scale=1.2)
    sun("Sun", (82, 0, 180), 4.5, (1.0, 0.8, 0.55))
    camera((0.6, -6, 0.35), (0, 20, 8), lens=17, dof=12, fstop=8)
    return {"fg": ["Jet"]}


def P04_school_jet():
    _sky((0.15, 0.42, 0.9), (0.55, 0.75, 0.97), (0.95, 0.85, 0.7), 1.1)
    plane("Lawn", (80, 60), (0, 10, 0), noisy("Grass2", (0.32, 0.58, 0.16), (0.16, 0.38, 0.08), 60, 0.9, 0.7))
    plane("Path", (3, 20), (0, 0, 0.01), noisy("Concrete", (0.72, 0.7, 0.66), (0.6, 0.58, 0.55), 25, 0.8, 0.2))
    br = brick("SchoolBrick", (0.5, 0.18, 0.1), (0.38, 0.12, 0.07), (0.7, 0.66, 0.6), 2.0)
    box("School", (40, 6, 10), (0, 22, 5), br, bevel=0.05)
    trim = mat("Trim", (0.9, 0.88, 0.82), 0.5)
    box("Cornice", (40.5, 6.5, 0.6), (0, 22, 10.2), trim, bevel=0.05)
    win = glass("SchoolWin", (0.35, 0.45, 0.55), 0.05)
    for r in range(2):
        for i in range(14):
            x = -18.2 + i * 2.8
            if abs(x) < 2.5:
                continue
            box("SWin", (1.6, 0.1, 2.2), (x, 18.95, 2.6 + r * 4.0), win, bevel=0)
            box("SWinFrame", (1.8, 0.12, 0.12), (x, 18.92, 1.45 + r * 4.0), trim, bevel=0.01)
    box("Entrance", (5, 1.2, 5), (0, 18.6, 2.5), trim, bevel=0.05)
    box("Doors", (3, 0.1, 3), (0, 17.95, 1.5), glass("DoorGlass", (0.4, 0.5, 0.6), 0.05), bevel=0)
    for i in range(3):
        box("Step", (6, 0.6, 0.2), (0, 17.6 - i * 0.6, 0.1 + (2 - i) * 0.2), trim, bevel=0.02)
    cyl("FlagPole", 0.08, 14, (-9, 14, 7), chrome())
    flag = stripes("FlagStripes", (0.7, 0.05, 0.08), (0.95, 0.94, 0.9), 6.5, 0.7, axis="Z")
    box("Flag", (0.04, 3.0, 1.9), (-9, 15.55, 12.8), flag, bevel=0)
    box("Canton", (0.05, 1.3, 1.0), (-9.01, 14.75, 13.25), mat("Canton", (0.08, 0.12, 0.35), 0.7), bevel=0)
    for x in (-15, 13, 19):
        tree((x, 12, 0), 7.5, seed=int(x))
    jet((1.5, 9, 6.0), rot=(R(4), R(-6), R(155)), scale=0.95)
    # blank papers blowing around
    random.seed(7)
    pap = mat("PaperW", (0.96, 0.95, 0.9), 0.6)
    for i in range(26):
        box("Paper", (0.42, 0.3, 0.003), (random.uniform(-6, 7), random.uniform(1, 12), random.uniform(0.5, 5)), pap,
            rot=(random.uniform(0, 3), random.uniform(0, 3), random.uniform(0, 3)), bevel=0)
    sun("Sun", (50, 0, 215), 4.5, (1.0, 0.88, 0.7))
    camera((0, -9, 1.5), (0, 8, 4.8), lens=19, dof=16, fstop=8)
    return {"fg": ["Jet"]}


def P09_mailbox():
    _sky((0.12, 0.08, 0.3), (0.55, 0.25, 0.45), (1.0, 0.5, 0.25), 1.0)
    _street(0.35)
    cols = [(0.86, 0.82, 0.72), (0.65, 0.78, 0.85), (0.92, 0.88, 0.7)]
    for i in range(4):
        house((15, 6 + i * 16, 0), wall=cols[i % 3], rotz=R(-90))
        house((-15, 12 + i * 16, 0), wall=cols[(i + 1) % 3], rotz=R(90))
    for y in (8, 26):
        tree((9.5, y, 0), 5.0, (0.6, 0.32, 0.08), seed=y)
    blue = mat("MailBlue", (0.05, 0.16, 0.5), 0.3, coat=0.8)
    box("Mailbox", (0.55, 0.5, 0.9), (6.2, 1.5, 0.85), blue, bevel=0.03)
    cyl("MailTop", 0.275, 0.5, (6.2, 1.5, 1.3), blue, rot=(R(90), 0, 0))
    box("Slot", (0.3, 0.02, 0.05), (6.2, 1.24, 1.15), mat("SlotDark", (0.02, 0.02, 0.02), 0.5), bevel=0.005)
    for dx in (-0.22, 0.22):
        for dy in (-0.2, 0.2):
            cyl("MLeg", 0.025, 0.4, (6.2 + dx, 1.5 + dy, 0.32), mat("MailBlue"))
    cyl("LampPost", 0.07, 5, (7.0, 3.5, 2.5), mat("Iron", (0.05, 0.05, 0.06), 0.5, metal=0.8))
    sphere("LampHead", 0.25, (7.0, 3.5, 5.1), emit("StreetLamp", (1.0, 0.7, 0.35), 25))
    point("LampLight", (7.0, 3.5, 4.8), 700, (1.0, 0.65, 0.3), 0.3)
    sun("Dusk", (85, 0, 250), 2.0, (1.0, 0.5, 0.25))
    camera((3.4, -3.2, 1.25), (6.2, 3.5, 1.4), lens=24, dof=5.5, fstop=4)


def P12_porch():
    boards = wood("Porch", (0.62, 0.45, 0.32), (0.48, 0.33, 0.22), 0.55, scale=4, planks=0.14, coat=0.1)
    plane("PorchFloor", (6, 5), (0, 0.5, 0), boards)
    siding = stripes("Siding", (0.86, 0.85, 0.8), (0.76, 0.75, 0.7), 18, 0.7, axis="Z")
    box("Wall", (6, 0.2, 3.2), (0, 2.6, 1.6), siding, bevel=0)
    box("DoorFrame", (1.3, 0.1, 2.35), (0, 2.48, 1.17), mat("WhiteTrim", (0.95, 0.94, 0.9), 0.4), bevel=0.02)
    box("Door", (1.0, 0.08, 2.1), (0, 2.43, 1.05), mat("DoorWhite", (0.93, 0.92, 0.88), 0.35, coat=0.4), bevel=0.02)
    for (x, z) in ((-0.22, 0.6), (0.22, 0.6), (-0.22, 1.45), (0.22, 1.45)):
        box("Panel", (0.34, 0.02, 0.6 if z < 1 else 0.7), (x, 2.38, z), mat("DoorWhite"), bevel=0.02)
    brass = mat("Brass3", (0.85, 0.65, 0.3), 0.2, metal=1.0)
    box("MailSlot", (0.36, 0.03, 0.09), (0, 2.37, 1.05), brass, bevel=0.01)
    sphere("Knob", 0.045, (0.38, 2.36, 1.0), brass)
    box("Doormat", (1.1, 0.7, 0.03), (0, 1.65, 0.015), noisy("Coir", (0.55, 0.4, 0.2), (0.35, 0.24, 0.1), 200, 1.0, 0.8), bevel=0.01)
    for x in (-1.6, 1.6):
        cyl("Pot", 0.25, 0.4, (x, 2.1, 0.2), mat("Terracotta", (0.6, 0.27, 0.13), 0.7), r2=0.2, bevel=0.01)
        for k in range(6):
            sphere("Geranium", 0.09, (x + math.cos(k) * 0.12, 2.1 + math.sin(k) * 0.12, 0.5 + 0.05 * (k % 2)),
                   mat("Geranium", (0.85, 0.08, 0.12), 0.5))
        sphere("Foliage", 0.2, (x, 2.1, 0.45), noisy("PlantLeaf", (0.15, 0.4, 0.12), (0.05, 0.2, 0.05), 8, 0.5, 0.6),
               scale=(1.2, 1.2, 0.6))
    cyl("PorchLight", 0.08, 0.2, (0.85, 2.45, 2.1), mat("Brass3"))
    for i in range(7):  # railing posts that cast stripe shadows
        box("Post", (0.07, 0.07, 0.9), (2.9, -1.5 + i * 0.5, 0.45), mat("WhiteTrim"), bevel=0.01)
    box("Rail", (0.08, 4, 0.08), (2.9, 0, 0.92), mat("WhiteTrim"), bevel=0.01)
    sun("Sun", (55, 0, 60), 6.5, (1.0, 0.82, 0.6), angle=1.0)
    world((0.35, 0.45, 0.65), 0.5)
    camera((0.15, -1.8, 0.45), (0, 2.2, 1.0), lens=22, dof=2.6, fstop=3.5)


def P13_courthouse():
    _sky((0.45, 0.5, 0.58), (0.7, 0.72, 0.75), (0.85, 0.83, 0.8), 1.2)
    gran = noisy("Granite", (0.78, 0.76, 0.72), (0.6, 0.58, 0.56), 40, 0.6, 0.2)
    plane("Ground", (100, 100), (0, 10, 0), noisy("Asphalt", (0.2, 0.2, 0.21), (0.08, 0.08, 0.09), 60, 0.3, 0.5))
    for i in range(10):
        box("Step", (26, 1.0, 0.25), (0, 8 + i * 0.6, 0.125 + i * 0.25), gran, bevel=0.02)
    base_z = 2.5
    box("Podium", (28, 8, base_z), (0, 16, base_z / 2), gran, bevel=0.03)
    for i in range(8):
        x = -10.5 + i * 3.0
        cyl("Column", 0.75, 11, (x, 14, base_z + 5.5), gran, verts=24)
        box("Capital", (2.0, 2.0, 0.5), (x, 14, base_z + 11.2), gran, bevel=0.05)
        box("ColBase", (1.9, 1.9, 0.4), (x, 14, base_z + 0.2), gran, bevel=0.05)
    box("Entablature", (26, 3.5, 2.0), (0, 15, base_z + 12.4), gran, bevel=0.05)
    prism("Pediment", 26, 3.5, 4.0, (0, 15, base_z + 13.4), gran, rot=(0, 0, 0))
    box("Facade", (24, 1, 13), (0, 18, base_z + 6.5), noisy("GraniteDark", (0.55, 0.53, 0.5), (0.45, 0.43, 0.4), 30, 0.7, 0.2))
    for x in (-3, 0, 3):
        box("Door", (2.0, 0.2, 5), (x, 17.45, base_z + 2.5), wood("Bronze", (0.25, 0.15, 0.08), (0.15, 0.08, 0.04), 0.3), bevel=0.02)
    car((-2.5, -1.5, 0), (0.95, 0.75, 0.05), rotz=R(90))
    sun("Overcast", (40, 0, 160), 2.5, (0.95, 0.95, 1.0), angle=25)
    camera((1.0, -6.5, 0.9), (0, 12, 9), lens=17, dof=16, fstop=4)


def P10_hq_tower():
    _sky((0.08, 0.3, 0.8), (0.4, 0.62, 0.95), (0.85, 0.85, 0.85), 1.3)
    plane("Plaza", (120, 120), (0, 20, 0), noisy("Plaza", (0.75, 0.72, 0.68), (0.6, 0.58, 0.55), 6, 0.6, 0.1))
    glass_wall = brick("Curtain", (0.05, 0.12, 0.24), (0.08, 0.17, 0.3), (0.78, 0.8, 0.83), 0.3, 0.15)
    gn = glass_wall.node_tree.nodes
    for n in gn:
        if n.bl_idname == "ShaderNodeTexBrick":
            n.offset = 0.0
            n.inputs["Brick Width"].default_value = 1.0
            n.inputs["Row Height"].default_value = 0.35
            n.inputs["Mortar Size"].default_value = 0.06
            n.inputs["Bias"].default_value = 0.0
    gn["Principled BSDF"].inputs["Coat Weight"].default_value = 0.7
    box("Tower", (22, 22, 140), (0, 30, 70), glass_wall, bevel=0.3)
    box("Crown", (23, 23, 3), (0, 30, 141), mat("Steel", (0.7, 0.72, 0.75), 0.3, metal=1.0), bevel=0.2)
    box("Lobby", (26, 26, 6), (0, 30, 3), glass("Lobby", (0.6, 0.7, 0.8), 0.05), bevel=0.1)
    flagc = [(0.8, 0.1, 0.1), (0.95, 0.95, 0.95), (0.1, 0.25, 0.7)]
    for i, x in enumerate((-6, 0, 6)):
        cyl("Pole", 0.12, 14, (x, 10, 7), chrome())
        box("PFlag", (0.05, 3.0, 1.8), (x, 11.6, 13), mat(f"PF{i}", flagc[i], 0.7), bevel=0)
    hedge = noisy("Hedge", (0.2, 0.42, 0.12), (0.08, 0.22, 0.05), 25, 0.9, 0.8)
    for x in (-10, 10):
        box("Hedge", (6, 1.5, 1.2), (x, 8, 0.6), hedge, bevel=0.3)
    sun("Sun", (35, 0, 210), 5.0, (1.0, 0.92, 0.8))
    box("Side1", (14, 14, 70), (-26, 45, 35), noisy("Stone", (0.75, 0.7, 0.62), (0.6, 0.56, 0.5), 3, 0.6, 0.2), bevel=0.2)
    box("Side2", (14, 14, 55), (26, 42, 27.5), noisy("Stone", (0.75, 0.7, 0.62), (0.6, 0.56, 0.5)), bevel=0.2)
    camera((4, -48, 1.5), (0, 30, 52), lens=20, dof=60, fstop=11)


# ------------------------------------------------------------------------------------------------ macros / top-down
def P15_gavel():
    world((0.02, 0.015, 0.01), 1.0)
    oak = wood("BenchTop2", (0.45, 0.2, 0.07), (0.25, 0.1, 0.03), 0.12, scale=6, coat=1.0)
    plane("Bench", (3, 3), (0, 0.5, 0), oak)
    block = wood("Block", (0.4, 0.17, 0.06), (0.22, 0.08, 0.03), 0.2, scale=12, coat=0.8)
    cyl("SoundBlock", 0.12, 0.05, (0.0, 0.02, 0.025), block, bevel=0.008)
    head = wood("GavelHead", (0.45, 0.2, 0.07), (0.25, 0.1, 0.03), 0.18, scale=14, coat=0.9)
    gold = mat("GoldBand", (0.9, 0.7, 0.3), 0.15, metal=1.0)
    cyl("Head", 0.045, 0.17, (0.0, 0.02, 0.105), head, rot=(0, R(90), 0), bevel=0.008)
    for dx in (-0.055, 0.055):
        cyl("Band", 0.047, 0.012, (dx, 0.02, 0.105), gold, rot=(0, R(90), 0))
    cyl("Handle", 0.013, 0.28, (0.0, -0.12, 0.1), head, rot=(R(90), 0, 0), bevel=0.004)
    sphere("HandleEnd", 0.018, (0.0, -0.26, 0.1), head)
    random.seed(2)
    for i in range(22):  # bokeh lamps
        sphere("Bokeh", 0.02, (random.uniform(-1.4, 1.4), random.uniform(1.8, 3.5), random.uniform(0.2, 1.4)),
               emit("BokehE", (1.0, 0.7, 0.35), random.choice([15, 25, 40])))
    area("Key", (0.6, -0.3, 0.6), (0, 0, 0.05), 0.4, 25, (1.0, 0.85, 0.65))
    area("Rim", (-0.4, 0.6, 0.35), (0, 0, 0.08), 0.3, 18, (1.0, 0.7, 0.4))
    camera((0.18, -0.75, 0.32), (0, 0.0, 0.08), lens=50, dof=0.78, fstop=2.0)


def P16_countertop():
    world((0.1, 0.09, 0.08), 1.0)
    top = wood("Countertop", (0.72, 0.5, 0.28), (0.55, 0.35, 0.18), 0.4, scale=3, planks=0.12, coat=0.3)
    plane("Top", (2, 3), (0, 0, 0), top)
    paper = mat("Env", (0.96, 0.93, 0.85), 0.7)
    random.seed(5)
    for i in range(4):
        box("Envelope", (0.24, 0.12, 0.002), (-0.38 + random.uniform(-0.02, 0.02), 0.62 + i * 0.008, 0.002 + i * 0.002), paper,
            rot=(0, 0, random.uniform(-0.25, 0.25)), bevel=0)
    for i in range(5):
        box("Stamp", (0.025, 0.03, 0.001), (0.38 + i * 0.03, -0.6, 0.001), mat(f"Stamp{i % 2}", [(0.8, 0.15, 0.1), (0.15, 0.3, 0.7)][i % 2], 0.6),
            rot=(0, 0, random.uniform(-0.2, 0.2)), bevel=0)
    cyl("Pen", 0.006, 0.15, (0.32, 0.68, 0.006), mat("PenBlue", (0.1, 0.2, 0.6), 0.3), rot=(0, R(90), R(-15)))
    for i in range(12):
        sphere("Chain", 0.004, (0.25 + i * 0.012, 0.74 + math.sin(i) * 0.005, 0.004), chrome())
    box("Paperclip", (0.03, 0.008, 0.002), (-0.4, -0.55, 0.002), chrome(), bevel=0.001)
    cyl("RubberStamp", 0.025, 0.06, (-0.42, -0.4, 0.03), mat("StampWood", (0.5, 0.3, 0.15), 0.5))
    sphere("StampKnob", 0.02, (-0.42, -0.4, 0.07), mat("StampRed", (0.7, 0.05, 0.05), 0.3))
    area("Overhead", (0.3, 0.2, 1.6), (0, 0, 0), 1.2, 120, (1.0, 0.85, 0.65))
    area("Bounce", (-0.8, -0.6, 0.5), (0, 0, 0), 1.0, 20, (0.8, 0.85, 1.0))
    camera((0, 0, 1.45), (0, 0.0001, 0), lens=30)


def P17_store():
    world((0.01, 0.012, 0.03), 1.0)
    wet = noisy("WetLot", (0.12, 0.12, 0.13), (0.05, 0.05, 0.06), 50, 0.12, 0.3)
    wet.node_tree.nodes["Principled BSDF"].inputs["Coat Weight"].default_value = 1.0
    plane("Lot", (100, 100), (0, 20, 0), wet)
    for i in range(10):
        box("Stripe", (0.12, 5, 0.005), (-13.5 + i * 3, 2, 0.003), mat("LotWhite", (0.85, 0.85, 0.8), 0.5), bevel=0)
    wall = noisy("StoreWall", (0.6, 0.57, 0.52), (0.5, 0.47, 0.42), 8, 0.7, 0.2)
    box("Store", (40, 10, 9), (0, 18, 4.5), wall, bevel=0.05)
    box("RedBand", (40.2, 10.2, 1.2), (0, 18, 7.6), mat("StoreRed", (0.75, 0.06, 0.05), 0.4, coat=0.4), bevel=0.05)
    box("Banner", (14, 0.2, 1.6), (0, 12.85, 5.6), mat("BannerYel", (0.95, 0.8, 0.1), 0.5), bevel=0.03)
    box("DoorGlow", (10, 0.2, 4.0), (0, 12.9, 2.0), emit("StoreInside", (1.0, 0.9, 0.72), 0.6), bevel=0)
    for x in (-4, -1.3, 1.3, 4):
        box("DoorFrame", (0.12, 0.25, 4.0), (x, 12.8, 2.0), mat("Steel2", (0.6, 0.62, 0.65), 0.3, metal=1.0), bevel=0)
    area("DoorSpill", (0, 12.5, 2.0), (0, 0, 0.5), 10, 350, (1.0, 0.92, 0.78), size_y=4)
    red = mat("CartRed", (0.75, 0.05, 0.05), 0.35, metal=0.3)
    for row in range(2):
        for i in range(6):
            x, y = 7 + i * 0.35, 9 - row * 1.2
            box("Cart", (0.6, 1.0, 0.55), (x, y, 0.8), red, bevel=0.03)
            for dy in (-0.4, 0.4):
                cyl("CWheel", 0.06, 0.04, (x, y + dy, 0.08), mat("Tire", (0.03, 0.03, 0.03), 0.8), rot=(0, R(90), 0))
            cyl("CLeg", 0.015, 0.5, (x, y, 0.3), chrome())
    for i in range(7):  # velvet rope stanchions in front of doors
        x = -6 + i * 2
        cyl("Stanchion", 0.04, 1.0, (x, 10.5, 0.5), mat("Gold2", (0.9, 0.7, 0.3), 0.15, metal=1.0))
        cyl("SBase", 0.18, 0.04, (x, 10.5, 0.02), mat("Gold2"))
        if i < 6:
            cyl("Rope", 0.03, 2.0, (x + 1, 10.5, 0.85), mat("Velvet", (0.6, 0.03, 0.08), 0.6), rot=(0, R(90), 0))
    for x in (-14, 14):
        cyl("Pole", 0.1, 9, (x, 4, 4.5), mat("Steel2"))
        box("PoleHead", (1.2, 0.5, 0.2), (x, 4, 9), mat("Steel2"), bevel=0.05)
        spot("Lot", (x, 4, 8.9), (x, 4, 0), 3000, (1.0, 0.85, 0.6), angle=80, blend=0.6, radius=0.3)
    sphere("Moon", 1.5, (25, 80, 40), emit("Moon2", (0.9, 0.95, 1.0), 8))
    world((0.02, 0.03, 0.07), 1.0)
    camera((2.5, -12, 1.6), (0.5, 12, 4.0), lens=20, dof=18, fstop=5)


SETS = ["P20_hero_street", "P06_kitchen", "P08_diner", "P11_exec_office", "P14_courtroom", "P18_school_bus", "P02_street_jet",
        "P04_school_jet", "P09_mailbox", "P12_porch", "P13_courthouse", "P10_hq_tower", "P15_gavel", "P16_countertop",
        "P17_store"]


def JET_TEST():
    _sky((0.15, 0.35, 0.8), (0.5, 0.7, 0.95), (1.0, 0.8, 0.6), 1.2)
    plane("G", (200, 200), (0, 0, -3), noisy("Grass2", (0.32, 0.58, 0.16), (0.16, 0.38, 0.08), 60, 0.9, 0.7))
    jet((0, 0, 1.5), rot=(R(5), 0, R(-35)), scale=1.0)
    sun("Sun", (50, 0, 215), 4.5, (1.0, 0.88, 0.7))
    camera((22, -30, 6), (0, 0, 1.0), lens=60)


def P20_hero_street():
    """Golden-hour street, Harrier hovering over the road, sun behind it (hook shot). Jet = foreground layer."""
    _sky((0.22, 0.28, 0.62), (0.95, 0.5, 0.42), (1.0, 0.58, 0.22), 1.6)
    _street(0.25)
    cols = [(0.86, 0.82, 0.72), (0.65, 0.78, 0.85), (0.92, 0.88, 0.7), (0.75, 0.62, 0.55)]
    for i in range(6):
        for s_ in (-1, 1):
            house((s_ * 15, 6 + i * 16, 0), wall=cols[(i + (s_ > 0)) % 4], rotz=R(90 if s_ < 0 else -90))
            tree((s_ * 8.8, 12 + i * 16, 0), 7.0, (0.28, 0.42, 0.12), seed=i * 2 + (s_ > 0))
    for i in range(10):  # power-line poles
        cyl("PowerPole", 0.12, 9, (6.8, -2 + i * 12, 4.5), wood("Pole", (0.35, 0.25, 0.16), (0.25, 0.17, 0.1), 0.8))
    car((-3.4, 4, 0), (0.6, 0.1, 0.08))
    car((3.4, 26, 0), (0.15, 0.3, 0.6), rotz=R(180))
    jet((0, 16, 4.2), rot=(R(3), R(-4), R(180)), scale=1.0)
    sun("Sun", (84, 0, 180), 5.0, (1.0, 0.62, 0.3), angle=1.5)
    sphere("SunDisc", 3.0, (0, 140, 14), emit("SunDisc", (1.0, 0.75, 0.4), 30))
    area("Bounce", (0, -6, 4), (0, 10, 2), 10, 400, (1.0, 0.7, 0.45))
    camera((0.3, -5.5, 1.0), (0, 14, 3.6), lens=24, dof=20, fstop=5.6)
    return {"fg": ["Jet"]}


def P21_flyby():
    """Animated: Harrier screams low over the street, camera tilts to follow (48 frames @30fps, motion blur)."""
    _sky((0.12, 0.35, 0.85), (0.5, 0.7, 0.95), (1.0, 0.72, 0.45), 1.2)
    _street()
    cols = [(0.86, 0.82, 0.72), (0.65, 0.78, 0.85), (0.92, 0.88, 0.7), (0.75, 0.62, 0.55)]
    for i in range(6):
        for s_ in (-1, 1):
            house((s_ * 15, 4 + i * 16, 0), wall=cols[(i + (s_ > 0)) % 4], rotz=R(90 if s_ < 0 else -90))
            tree((s_ * 8.5, 10 + i * 16, 0), 6.5, seed=i * 2 + (s_ > 0))
    car((-3.4, 6, 0), (0.6, 0.1, 0.08))
    j = jet((0, 95, 16), rot=(R(-4), 0, R(180)), scale=1.1)
    j.keyframe_insert("location", frame=0)
    j.keyframe_insert("rotation_euler", frame=0)
    j.location = (0.5, -2, 8.5)
    j.rotation_euler = (R(-8), R(14), R(180))
    j.keyframe_insert("location", frame=34)
    j.keyframe_insert("rotation_euler", frame=34)
    j.location = (1.0, -45, 7)
    j.rotation_euler = (R(-6), R(22), R(180))
    j.keyframe_insert("location", frame=47)
    j.keyframe_insert("rotation_euler", frame=47)
    sun("Sun", (82, 0, 180), 4.5, (1.0, 0.8, 0.55))
    cam = camera((0.6, -6, 0.4), (0, 40, 9), lens=18)
    cam.keyframe_insert("rotation_euler", frame=0)
    cam.rotation_euler = (R(150), 0, R(178))
    cam.keyframe_insert("rotation_euler", frame=47)
    return {"frames": 48, "spp": 14, "scale": 75}

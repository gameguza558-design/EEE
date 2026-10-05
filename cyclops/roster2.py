"""The cyclops roster on the real Roblox R15 body (v2).

Per character:
  * body: the Studio R15 mesh (reference/roblox_r15.obj) with clothing, skin, the
    mouthless fierce cyclops face and corruption cracks *painted* (style2.Painter
    template baked into Roblox's own R15 UV layout) -> pieces "<Part>_Body"
  * hair / hoods / pelts: clump geometry (hair.py) with its own painted texture
  * armour, horns, pouches, crystals: geometry from the outfit modules with the shared
    material atlas (clothing helpers are switched off: common.PAINTED = True)

Run:  python3 cyclops/roster2.py [--no-render]
Outputs: export/r15/<Name>.fbx (+ textures), export/weapons/*.fbx, roblox/CyclopsData.lua,
         renders/r15_*.png
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import build_all  # noqa: E402
import hair  # noqa: E402
import kit  # noqa: E402
import r15_real  # noqa: E402
import style2  # noqa: E402
import weapons  # noqa: E402
from kit import R15_SIZE, band, blob, circle, tube  # noqa: E402
from outfits import common  # noqa: E402
from style2 import FACES, Painter, cyclops_face  # noqa: E402

common.PAINTED = True
from outfits import elite, knights  # noqa: E402
from outfits.common import Outfit  # noqa: E402

OUT = os.path.join(HERE, "export", "r15")
RENDERS = os.path.join(HERE, "renders")
SIDES4 = ("front", "back", "left", "right")
ARMS = [s + p for s in ("Left", "Right") for p in ("UpperArm", "LowerArm", "Hand")]
LEGS = [s + p for s in ("Left", "Right") for p in ("UpperLeg", "LowerLeg", "Foot")]
PURPLE = (176, 70, 255)
PINK = (255, 70, 190)


def mul(c, k):
    return tuple(max(0, min(255, int(x * k))) for x in c)


# ---------------------------------------------------------------------------
# Painting helpers
def skin_all(p, skin):
    for part in style2.PARTS:
        p.fill(part, FACES, skin)


def paint_hair_cap(p, color, back=0.45, sides=0.25):
    p.fill("Head", ("top",), color)
    p.box("Head", "back", 0, 0, 1, back, color)
    for s in ("left", "right"):
        p.box("Head", s, 0, 0, 1, sides, color)


def shirt(p, color, sleeves="short", trim=None):
    p.fill("UpperTorso", FACES, color)
    for side in ("Left", "Right"):
        if sleeves in ("short", "long"):
            p.fill(side + "UpperArm", FACES, color)
            for f in SIDES4:
                p.folds(side + "UpperArm", f, mul(color, 0.85), 2, horizontal=True)
        if sleeves == "long":
            p.fill(side + "LowerArm", FACES, color)
            for f in SIDES4:
                p.box(side + "LowerArm", f, 0, 0.82, 1, 1, mul(color, 0.85))
    for f in ("front", "back"):
        p.folds("UpperTorso", f, mul(color, 0.86), 3)
    if trim:
        p.poly("UpperTorso", "front", [(0.36, 0), (0.64, 0), (0.5, 0.25)], trim)


def pants(p, color, belt=None, buckle=(190, 160, 90)):
    p.fill("LowerTorso", FACES, color)
    for part in LEGS:
        if not part.endswith("Foot"):
            p.fill(part, FACES, color)
            for f in SIDES4:
                p.folds(part, f, mul(color, 0.8), 3)
    if belt:
        for f in SIDES4:
            p.box("LowerTorso", f, 0, 0.15, 1, 0.7, belt)
            p.dashes("LowerTorso", f, [(0, 0.22), (1, 0.22)], mul(belt, 1.5), dash=8, gap=6)
            p.dashes("LowerTorso", f, [(0, 0.63), (1, 0.63)], mul(belt, 1.5), dash=8, gap=6)
        p.box("LowerTorso", "front", 0.42, 0.08, 0.58, 0.77, buckle, outline=mul(buckle, 0.5), width=4)
        p.box("LowerTorso", "front", 0.46, 0.25, 0.54, 0.6, mul(belt, 0.6))


def boots(p, color, height=0.6, cuff=None, sole=(30, 24, 20), plates=None):
    for side in ("Left", "Right"):
        p.fill(side + "Foot", FACES, color)
        p.box(side + "Foot", "front", 0, 0.7, 1, 1, sole)
        for f in SIDES4:
            p.box(side + "Foot", f, 0, 0.75, 1, 1, sole)
            p.box(side + "LowerLeg", f, 0, 1 - height, 1, 1, color)
            p.line(side + "LowerLeg", f, [(0, 1 - height), (1, 1 - height)], mul(color, 0.6), width=5)
            if cuff:
                p.box(side + "LowerLeg", f, 0, 1 - height - 0.08, 1, 1 - height + 0.06, cuff)
        if plates:
            p.box(side + "LowerLeg", "front", 0.2, 1 - height + 0.08, 0.8, 0.95, plates, outline=mul(plates, 0.5), width=4)
            for v in (1 - height + 0.15, 0.88):
                p.ellipse(side + "LowerLeg", "front", 0.28, v, 0.03, 0.03, mul(plates, 1.3))
                p.ellipse(side + "LowerLeg", "front", 0.72, v, 0.03, 0.03, mul(plates, 1.3))
        for v in (0.1, 0.25, 0.4):
            p.line(side + "Foot", "top", [(0.3, v), (0.7, v + 0.05)], mul(color, 1.6), width=3)


def gloves(p, color):
    for side in ("Left", "Right"):
        p.fill(side + "Hand", FACES, color)
        for f in SIDES4:
            p.box(side + "LowerArm", f, 0, 0.85, 1, 1, mul(color, 1.1))


def bracers(p, color, laces=(200, 180, 140)):
    for side in ("Left", "Right"):
        for f in SIDES4:
            p.box(side + "LowerArm", f, 0, 0.25, 1, 0.85, color, outline=mul(color, 0.6), width=3)
        for v in (0.35, 0.5, 0.65, 0.78):
            p.line(side + "LowerArm", "front", [(0.35, v), (0.65, v + 0.06)], laces, width=3)
            p.line(side + "LowerArm", "front", [(0.65, v), (0.35, v + 0.06)], laces, width=3)


def wraps(p, part, color, count=5):
    for f in SIDES4:
        for k in range(count):
            v = 0.15 + 0.75 * k / max(1, count - 1)
            p.box(part, f, 0, v - 0.05, 1, v + 0.04, color)
            p.line(part, f, [(0, v + 0.04), (1, v + 0.02)], mul(color, 0.7), width=3)


def strap(p, color, front=True, back=True, from_right=True):
    """Diagonal strap across the torso."""
    for face, on in (("front", front), ("back", back)):
        if not on:
            continue
        a, b = ((0.12, 0.0), (0.88, 1.0)) if (from_right == (face == "front")) else ((0.88, 0.0), (0.12, 1.0))
        p.line("UpperTorso", face, [a, b], color, width=26)
        p.dashes("UpperTorso", face, [a, b], mul(color, 1.6), dash=8, gap=8)


def muscles(p, skin, part="UpperTorso"):
    """Painted pecs, abs and back muscles for bare torsos."""
    line, hi = mul(skin, 0.68), mul(skin, 1.08)
    for s in (0, 1):
        x0, x1 = (0.06, 0.48) if s == 0 else (0.52, 0.94)
        p.poly(part, "front", [(x0, 0.12), (x1, 0.12), (x1, 0.4), ((x0 + x1) / 2, 0.47), (x0, 0.38)], hi)
        p.line(part, "front", [(x0, 0.38), ((x0 + x1) / 2, 0.47), (x1, 0.4)], line, width=6)
    p.line(part, "front", [(0.5, 0.12), (0.5, 1.0)], line, width=5)
    for v in (0.55, 0.7, 0.85):
        for u0 in (0.3, 0.52):
            p.box(part, "front", u0, v, u0 + 0.18, v + 0.12, hi, outline=line, width=4)
    for s in (0.12, 0.88):
        p.line(part, "front", [(s, 0.45), (0.25 if s < 0.5 else 0.75, 0.98)], line, width=5)
    p.line(part, "back", [(0.5, 0.05), (0.5, 0.95)], line, width=5)
    for s in (0, 1):
        x0, x1 = (0.08, 0.46) if s == 0 else (0.54, 0.92)
        p.poly(part, "back", [(x0, 0.15), (x1, 0.1), (x1, 0.5), (x0, 0.62)], hi)
    for side in ("Left", "Right"):
        for f in ("front", "back"):
            p.line(side + "UpperArm", f, [(0.15, 0.35), (0.5, 0.55), (0.85, 0.35)], line, width=5)
            p.line(side + "LowerArm", f, [(0.3, 0.1), (0.4, 0.7)], line, width=4)


def quilt(p, part, face, color):
    line = mul(color, 0.72)
    for k in range(-6, 7):
        p.line(part, face, [(k / 6, 0), (k / 6 + 1, 1)], line, width=3)
        p.line(part, face, [(k / 6, 1), (k / 6 + 1, 0)], line, width=3)


def chainmail(p, part, face, base=(48, 48, 54), ring=(150, 150, 160)):
    p.box(part, face, 0, 0, 1, 1, base)
    x0, y0, x1, y1 = style2.face_rect(part, face)
    step = 9
    for row, y in enumerate(range(int(y0), int(y1), step)):
        for x in range(int(x0) + (step // 2 if row % 2 else 0), int(x1), step):
            p.d.ellipse([x - 4, y - 4, x + 4, y + 4], outline=ring, width=2)


def corruption(p, parts, level, seed=0, glow=PURPLE):
    rnd = random.Random(seed)
    for part in parts:
        for f in SIDES4:
            if rnd.random() < 0.85:
                p.cracks(part, f, (45, 22, 55), glow, count=max(1, int(2 + 5 * level)), seed=rnd.randint(0, 999))


# ---------------------------------------------------------------------------
# Characters: painter + geometry + hair + weapon
class Character:
    def __init__(self, name, glow=PURPLE, weapon=None, shield=False):
        self.name, self.glow, self.weapon, self.shield = name, glow, weapon, shield
        self.painter = None
        self.outfit = Outfit(name, glow=glow)
        self.hairs = []  # (part, kind, bmesh, (base, tip, highlight))


def villager():
    ch = Character("Villager", weapon="Hoe")
    _, ch.painter, _, _ = style2.villager()
    ch.hairs.append(("Head", "Hair", hair.messy_short(1), ((80, 55, 36), (45, 30, 20), (160, 120, 85))))
    return ch


def hunter():
    ch = Character("Hunter", weapon="HunterBow")
    skin, green, leather, brown = (140, 150, 142), (58, 82, 52), (100, 66, 42), (82, 62, 44)
    p = Painter(seed=12)
    skin_all(p, skin)
    cyclops_face(p, skin, iris=(120, 200, 90))
    shirt(p, green, sleeves="long")
    p.box("UpperTorso", "front", 0.15, 0.2, 0.85, 1.0, leather, outline=mul(leather, 0.6), width=5)
    p.dashes("UpperTorso", "front", [(0.19, 0.25), (0.19, 0.95)], (200, 170, 120))
    p.dashes("UpperTorso", "front", [(0.81, 0.25), (0.81, 0.95)], (200, 170, 120))
    strap(p, (70, 45, 28))
    pants(p, brown, belt=(70, 45, 28))
    for part in ("LeftUpperLeg", "RightUpperLeg"):
        for f in SIDES4:  # tunic hem over the thighs
            p.poly(part, f, [(0, 0), (1, 0), (1, 0.3), (0.8, 0.38), (0.6, 0.3), (0.4, 0.4), (0.2, 0.3), (0, 0.38)], green)
    bracers(p, leather)
    gloves(p, (75, 50, 32))
    boots(p, leather, height=0.7, cuff=(150, 145, 140))
    corruption(p, ["RightUpperArm"], 0.2, seed=3)
    p.shade()
    ch.painter = p
    # Hood: a cloth "hair" cap with a point at the back.
    ch.hairs.append(("Head", "Hood", hood(), ((70, 98, 62), (45, 64, 40), (95, 125, 85))))
    o = ch.outfit
    t = o("UpperTorso")
    tube(t, -0.4, 0.75, 0.2, 0.24, "leather", sides=8, pos=(0.35, 0.62, 0.1), rot=(0, -25, 0))
    for i, x in enumerate((-0.08, 0.0, 0.08, 0.02)):
        t.box((0.04, 0.04, 0.6), "wood", pos=(0.6 + x, 0.62, 0.95 + 0.04 * i), rot=(0, -25, 0))
        t.box((0.12, 0.02, 0.18), "linen", pos=(0.72 + x, 0.62, 1.18 + 0.04 * i), rot=(0, -25, 0))
    common.pouch(o, 0.75, y=-0.56)
    o.crystals("RightUpperArm", 3, (-0.5, 0.2, 0.4), (0.1, 0.2, 0.15), (-1, 0.3, 0.6),
               length=(0.15, 0.3), radius=(0.04, 0.06))
    return ch


def hood():
    h = hair.HairBuilder(7)
    h.cap(radius=hair.HEAD_HALF + 0.1, front_cut=0.1, back_low=-0.75)
    rnd = h.rnd
    for d in hair.around(rnd, 18, (-20, 15), (70, 290)):  # drape over the shoulders
        h.clump(d, 0.45, 0.32, gravity=1.0, lift=-0.3, thickness=0.25)
    h.clump(Vector((0, 1, 0.5)), 0.7, 0.3, gravity=1.2, thickness=0.25)  # hood point
    return h.finish()


def woodcutter():
    ch = Character("Woodcutter", weapon="WoodcutterAxe")
    skin, leather, pants_c = (132, 140, 130), (110, 72, 44), (70, 40, 42)
    p = Painter(seed=13)
    skin_all(p, skin)
    cyclops_face(p, skin, iris=(220, 120, 60))
    muscles(p, skin)
    # Leather apron over the belly and thighs, suspenders over bare shoulders.
    p.poly("UpperTorso", "front", [(0.2, 0.5), (0.8, 0.5), (0.85, 1.0), (0.15, 1.0)], leather)
    p.dashes("UpperTorso", "front", [(0.22, 0.55), (0.78, 0.55)], (200, 160, 110))
    for u in (0.3, 0.7):
        p.line("UpperTorso", "front", [(u, 0.0), (u, 0.55)], (70, 45, 28), width=18)
        p.line("UpperTorso", "back", [(u, 0.0), (0.5, 1.0)], (70, 45, 28), width=18)
    pants(p, pants_c, belt=None)
    for f in SIDES4:
        p.box("LowerTorso", f, 0, 0.3, 1, 0.6, (170, 140, 90))  # rope belt
    p.box("LowerTorso", "front", 0.15, 0.0, 0.85, 1.0, leather)
    for part in ("LeftUpperLeg", "RightUpperLeg"):
        p.box(part, "front", 0.0 if part.startswith("Right") else 0.0, 0.0, 1.0, 0.75, leather)
    for side in ("Left", "Right"):
        wraps(p, side + "LowerArm", (75, 50, 32), count=3)
    boots(p, (65, 45, 30), height=0.55, cuff=(40, 36, 34))
    corruption(p, ["LeftUpperArm", "LeftLowerArm"], 0.35, seed=5)
    p.cracks("UpperTorso", "front", (45, 22, 55), PURPLE, count=3, seed=8)
    p.shade()
    ch.painter = p
    ch.hairs.append(("Head", "Hair", hair.top_knot(3), ((45, 36, 30), (28, 22, 18), (95, 80, 70))))
    ch.hairs.append(("Head", "Beard", hair.beard(4), ((45, 36, 30), (28, 22, 18), (95, 80, 70))))
    o = ch.outfit
    o.crystals("LeftUpperArm", 4, (0.5, 0.0, 0.3), (0.05, 0.3, 0.2), (1, 0, 0.6), length=(0.18, 0.35),
               radius=(0.04, 0.07))
    o.crystals("UpperTorso", 4, (0.0, 0.55, 0.3), (0.05, 0.02, 0.4), (0, 1, 0.4), length=(0.2, 0.4),
               radius=(0.05, 0.08))
    return ch


def wolf_rider():
    ch = Character("WolfRider", weapon="WolfRiderSpear")
    skin, leather, dark, fur = (135, 142, 136), (92, 60, 38), (48, 36, 40), (88, 84, 82)
    p = Painter(seed=14)
    skin_all(p, skin)
    cyclops_face(p, skin, iris=(240, 200, 60))
    shirt(p, dark, sleeves="short")
    for f in ("front", "back", "left", "right"):
        p.box("UpperTorso", f, 0.04, 0.12, 0.96, 1.0, leather, outline=mul(leather, 0.55), width=5)
    for v in (0.35, 0.55, 0.75):
        p.line("UpperTorso", "front", [(0.08, v), (0.92, v)], mul(leather, 0.6), width=6)
        p.poly("UpperTorso", "front", [(0.49, v - 0.04), (0.53, v), (0.49, v + 0.06)], (225, 215, 190))
    strap(p, (60, 40, 26), from_right=False)
    pants(p, dark, belt=(60, 40, 26))
    bracers(p, (70, 46, 30))
    gloves(p, leather)
    for side in ("Left", "Right"):
        wraps(p, side + "LowerLeg", fur, count=4)
    boots(p, (60, 40, 26), height=0.3)
    corruption(p, ["LeftLowerArm", "LeftUpperArm"], 0.4, seed=9)
    p.shade()
    ch.painter = p
    ch.hairs.append(("Head", "Pelt", pelt(), ((70, 66, 66), (40, 37, 38), (130, 125, 122))))
    o = ch.outfit
    for i in range(5):
        o("UpperTorso").spike((-0.35 + 0.17 * i, -0.6, 0.25 - 0.13 * i), (0, -0.3, -1), 0.18, 0.04, "bone", sides=4)
    o.crystals("LeftUpperArm", 5, (0.55, 0, 0.55), (0.15, 0.3, 0.15), (1, 0, 1), length=(0.2, 0.45),
               radius=(0.04, 0.08))
    return ch


def pelt():
    """Wolf-pelt hood: shaggy fur over the head and shoulders, with the wolf's ears."""
    h = hair.HairBuilder(9)
    h.cap(radius=hair.HEAD_HALF + 0.08, front_cut=0.25, back_low=-0.7)
    rnd = h.rnd
    for d in hair.around(rnd, 30, (-25, 40), (55, 305)):
        h.clump(d, rnd.uniform(0.5, 0.9), rnd.uniform(0.18, 0.25), gravity=1.0, lift=-0.2, twist=rnd.uniform(-0.5, 0.5))
    for s in (1, -1):  # ears
        h.clump(Vector((s * 0.45, 0.0, 1.0)), 0.45, 0.22, gravity=-0.3, lift=1.0, thickness=0.4)
    for d in hair.around(rnd, 6, (40, 60), (-40, 40)):  # fur over the brow
        h.clump(d, 0.3, 0.2, gravity=0.8, curl=1.0 if d.x > 0 else -1.0)
    return h.finish()


def knight(kind, corruption_level, name, weapon, seed):
    ch = Character(name, weapon=weapon, shield=True)
    skin = (128, 136, 130)
    p = Painter(seed=seed)
    skin_all(p, skin)
    cyclops_face(p, skin, iris=(210, 90, 255) if corruption_level > 0.5 else (230, 170, 60),
                 corruption=corruption_level > 0.5)
    gamb = (120, 98, 72) if kind == "apprentice" else (60, 50, 56)
    shirt(p, gamb, sleeves="long")
    for part in ("UpperTorso", "LeftUpperArm", "RightUpperArm", "LeftLowerArm", "RightLowerArm"):
        for f in SIDES4:
            quilt(p, part, f, gamb)
    if kind != "apprentice":
        for part in ("LowerTorso", "LeftUpperLeg", "RightUpperLeg"):
            for f in SIDES4:
                chainmail(p, part, f)
    else:
        pants(p, (90, 72, 52), belt=None)
        for part in ("LeftUpperLeg", "RightUpperLeg"):
            for f in SIDES4:
                quilt(p, part, f, (90, 72, 52))
    p.box("UpperTorso", "front", 0.25, 0.0, 0.75, 1.0, (130, 36, 48))  # tabard
    p.dashes("UpperTorso", "front", [(0.27, 0.02), (0.27, 0.98)], (210, 170, 90))
    p.dashes("UpperTorso", "front", [(0.73, 0.02), (0.73, 0.98)], (210, 170, 90))
    gloves(p, (70, 50, 36))
    boots(p, (60, 44, 32), height=0.8, plates=(95, 92, 100) if kind != "apprentice" else None)
    corruption(p, ["LeftUpperArm", "LeftLowerArm", "UpperTorso"], corruption_level, seed=seed)
    p.shade()
    ch.painter = p
    builder = {"apprentice": knights.apprentice, "mid": knights.mid, "high": knights.high}[kind]
    ch.outfit = builder(name=name, corruption=corruption_level, seed=seed)
    return ch


def elite_onehorn():
    ch = Character("EliteOneHorn", weapon="OneHornGreatsword")
    p = Painter(seed=31)
    dark = (40, 36, 44)
    skin_all(p, dark)
    for part in style2.PARTS:
        for f in SIDES4:
            quilt(p, part, f, dark)
    p.shade()
    ch.painter = p
    ch.outfit = elite.elite_onehorn()
    return ch


def cyclops_king():
    ch = Character("CyclopsKing", glow=PINK)
    skin = (214, 192, 204)
    p = Painter(seed=41)
    skin_all(p, skin)
    muscles(p, skin)
    for part in ("Head", "UpperTorso", "LeftUpperArm", "RightUpperArm", "LeftLowerArm", "RightLowerArm",
                 "LeftHand", "RightHand"):
        for f in FACES:
            if f == "front" and part == "Head":
                continue
            p.cracks(part, f, (60, 20, 50), PINK, count=6, seed=hash((part, f)) % 997)
    p.cracks("Head", "front", (60, 20, 50), PINK, count=2, seed=3)
    cyclops_face(p, skin, iris=(255, 70, 190), corruption=True)
    pants(p, (40, 34, 44), belt=(55, 38, 28), buckle=(220, 180, 70))
    for part in ("LeftLowerLeg", "RightLowerLeg"):
        for f in SIDES4:  # torn hem
            p.poly(part, f, [(0, 0.3), (0.2, 0.42), (0.35, 0.3), (0.55, 0.45), (0.75, 0.3), (1, 0.42), (1, 1), (0, 1)], skin)
    boots(p, (48, 36, 30), height=0.62, cuff=(40, 36, 40), plates=(110, 108, 118))
    for side in ("Left", "Right"):
        for f in SIDES4:
            p.box(side + "UpperArm", f, 0, 0.55, 1, 0.68, (220, 180, 70))  # gold arm bands
            p.box(side + "LowerArm", f, 0, 0.55, 1, 1.0, (50, 40, 54))  # dark wraps
            for v in (0.62, 0.78, 0.92):
                p.line(side + "LowerArm", f, [(0, v), (1, v + 0.03)], (30, 24, 34), width=4)
    p.shade()
    ch.painter = p
    ch.hairs.append(("Head", "Hair", hair.wild_mane(2), ((240, 230, 240), (180, 160, 190), (255, 255, 255))))
    o = ch.outfit
    h = o("Head")
    band(h, 0.32, 0.44, 0.66, 0.66, 0.24, "gold")
    h.spike((0, -0.42, 0.4), (0, 0.12, 1), 1.6, 0.2, "horn", sides=6)
    g = o("Head", "Glow")
    for i in range(7):
        ang = math.pi * (0.15 + 0.7 * i / 6)
        x, y = 0.68 * math.cos(ang), -0.68 * math.sin(ang)
        g.spike((x, y, 0.42), (x * 0.4, y * 0.4, 1), 0.3 + 0.15 * (i % 2), 0.06, "glow", sides=5)
    o.crystals("UpperTorso", 10, (0.0, 0.55, 0.35), (0.7, 0.03, 0.35), (0, 1, 0.8), length=(0.5, 1.3),
               radius=(0.08, 0.17))
    for s, pre in ((1, "Left"), (-1, "Right")):
        o.crystals(pre + "UpperArm", 8 if s > 0 else 4, (s * 0.45, 0, 0.5), (0.15, 0.3, 0.1), (s * 0.8, 0, 1),
                   length=(0.4, 1.2 if s > 0 else 0.7), radius=(0.07, 0.16))
        band(o(pre + "LowerLeg"), 0.42, 0.6, 0.6, 0.6, 0.16, "fur_dark")  # boot cuffs
    for i in range(4):
        o("LeftLowerArm", "Glow").spike((0.55, 0.1, 0.35 - 0.25 * i), (1, 0.6, 0.5 - 0.1 * i), 0.55 - 0.08 * i,
                                        0.08, "glow", sides=4)
    return ch


ROSTER = {
    "stage1": [villager, hunter, woodcutter, wolf_rider,
               lambda: knight("apprentice", 0.3, "KnightApprentice", "ApprenticeSword", 21), elite_onehorn],
    "stage2": [lambda: knight("apprentice", 0.55, "KnightApprenticeInfected", "ApprenticeAxe", 24),
               lambda: knight("mid", 0.65, "KnightMid", "MidSword", 22),
               lambda: knight("high", 0.9, "KnightHigh", "HighAxe", 23)],
    "boss": [cyclops_king],
}


# ---------------------------------------------------------------------------
def build_character(ch, atlas_mats):
    """Bake the body, build hair and geometry pieces. Returns all objects (origins at
    the real R15 part centres) for export."""
    template = ch.painter.save(os.path.join(OUT, f"{ch.name}_template.png"))
    parts = r15_real.load_reference()
    for part, o in parts.items():
        r15_real.add_paint_uv(o, part)
    img = r15_real.bake(parts, template, os.path.join(OUT, f"{ch.name}_texture.png"))
    body_mat = r15_real.final_material(img, ch.name + "Body")
    objs = []
    for part, o in parts.items():
        o.data.materials.clear()
        o.data.materials.append(body_mat)
        o.data.uv_layers.remove(o.data.uv_layers["Paint"])
        o.name = o.data.name = f"{part}_Body"
        objs.append(o)
    centres = {part: o.location.copy() for part, o in parts.items()}
    for part, kind, bm, (base, tip, hi) in ch.hairs:
        tex = hair.hair_texture(os.path.join(OUT, f"{ch.name}_{kind}.png"), base, tip, hi)
        mat = bpy.data.materials.new(f"{ch.name}{kind}")
        mat.use_nodes = True
        t = mat.node_tree.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(tex)
        mat.node_tree.links.new(t.outputs["Color"], mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
        mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.55
        me = bpy.data.meshes.new(f"{part}_{kind}")
        bm.to_mesh(me)
        bm.free()
        for poly in me.polygons:
            poly.use_smooth = True
        me.materials.append(mat)
        o = bpy.data.objects.new(f"{part}_{kind}", me)
        o.location = centres[part]
        bpy.context.collection.objects.link(o)
        objs.append(o)
    for part, kinds in ch.outfit.pieces.items():
        for kind, piece in kinds.items():
            if not len(piece.bm.faces):
                piece.bm.free()
                continue
            if kind.startswith("Shield") and not ch.shield:
                piece.bm.free()
                continue
            mat = atlas_mats[1] if kind.endswith("Glow") else atlas_mats[0]
            objs.append(piece.to_object(f"{part}_{kind}", mat, centres[part]))
    return objs


def main():
    no_render = "--no-render" in sys.argv
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version = 0
    os.makedirs(OUT, exist_ok=True)
    img = bpy.data.images.load(kit.build_atlas(os.path.join(HERE, "export", "cyclops_texture.png")))
    mats = build_all.make_materials(img)

    outfit_lua, weapon_lua, built = [], [], {}
    for group, makers in ROSTER.items():
        for make in makers:
            ch = make()
            objs = build_character(ch, mats)
            build_all.export_fbx(os.path.join(OUT, ch.name + ".fbx"), objs)
            outfit_lua.append(build_all.lua_outfit(ch.outfit, objs))
            build_all.release_names(objs, ch.name)
            built.setdefault(group, []).append((ch, objs))
            print(f"{ch.name}: {len(objs)} pieces")
    weapon_objs = {}
    for w in weapons.all_weapons():
        objs = build_all.build_weapon_objects(w, mats)
        build_all.export_fbx(os.path.join(HERE, "export", "weapons", w.name + ".fbx"), objs)
        weapon_lua.append(build_all.lua_weapon(w, objs))
        build_all.release_names(objs, w.name)
        weapon_objs[w.name] = objs
    build_all.write_data(outfit_lua, weapon_lua, [])
    if no_render:
        return
    render_lineups(built, weapon_objs, mats)


def render_lineups(built, weapon_objs, mats):
    scene, cam = build_all.setup_scene()
    scene.view_settings.view_transform = "Standard"
    scales = {"CyclopsKing": 1.6}
    for group, members in built.items():
        shown, x = [], 0.0
        for ch, objs in members:
            k = scales.get(ch.name, 1.0)
            offset = Vector((x + 2.3 * k, 0, 0))
            build_all.place(objs, offset, k)
            shown += objs
            if ch.weapon:
                hand = next(o for o in objs if o.name.endswith("RightHand_Body")).matrix_world.translation
                shown += build_all.held_weapon(weapons, ch.weapon, mats, hand + Vector((0, -0.1, 0)), k)
            x += 4.6 * k
        build_all.set_visible(bpy.data.objects, shown)
        top = 6.8 * max(scales.get(c.name, 1.0) for c, _ in members)
        center = (x / 2, 0, top / 2 - 0.2)
        if group == "boss":
            build_all.render(scene, cam, os.path.join(RENDERS, "r15_boss_hero.png"), (x / 2 - 9, -16, 10),
                             (x / 2, 0, 6.2), 10.5, (1000, 1000))
            res, size = (1000, 1200), top + 1.8
        else:
            res, size = (1800, int(1800 * (top + 1.0) / (x + 0.6))), x + 0.6
        for tag, y in (("front", -40), ("back", 40)):
            build_all.render(scene, cam, os.path.join(RENDERS, f"r15_{group}_{tag}.png"), (center[0], y, center[2]),
                             center, size, res)
        build_all.place(shown, Vector((0, 0, -100)))
    # Weapons sheet.
    shown, x = [], 0.0
    for name, objs in weapon_objs.items():
        build_all.place(objs, Vector((x, 0, 1.6)), 1.0, 90 if name in build_all.SIDEWAYS | {"Hoe", "Sickle", "Scythe"} else 0)
        shown += objs
        x += 1.6
    build_all.set_visible(bpy.data.objects, shown)
    build_all.render(scene, cam, os.path.join(RENDERS, "r15_weapons.png"), ((x - 1.6) / 2, -40, 2.4),
                     ((x - 1.6) / 2, 0, 2.4), x + 0.4, (1800, int(1800 * 6.0 / (x + 0.4))))


if __name__ == "__main__":
    main()

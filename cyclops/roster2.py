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
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402
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
from outfits import elite, knights, parade  # noqa: E402
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


def soft_shapes(p, shapes, color, strength, blur=6):
    """Blend soft-edged painted shapes (anime-style cel shading) onto the canvas.
    shapes: list of (part, face, kind, args) with kind "poly" (pts) or "ellipse" (cu, cv, ru, rv)."""
    mask = Image.new("L", p.img.size, 0)
    md = ImageDraw.Draw(mask)
    for part, face, kind, args in shapes:
        if kind == "poly":
            md.polygon([p.at(part, face, u, v) for u, v in args], fill=255)
        else:
            cu, cv, ru, rv = args
            x0, y0, x1, y1 = style2.face_rect(part, face)
            cx, cy = p.at(part, face, cu, cv)
            rx, ry = ru * (x1 - x0), rv * (y1 - y0)
            md.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(blur)).point(lambda x: int(x * strength))
    p.img = Image.composite(Image.new("RGB", p.img.size, color), p.img, mask)
    p.d = ImageDraw.Draw(p.img)


def muscles(p, skin, part="UpperTorso"):
    """Anime-style muscle shading: soft shadow shapes under the pecs, between the abs and
    along the obliques, with highlights on the pec tops, ab pads, delts and biceps."""
    shadow = (int(skin[0] * 0.62), int(skin[1] * 0.55), int(skin[2] * 0.68))
    light = mul(skin, 1.12)
    dark, hi = [], []
    for sgn in (1, -1):
        def m(u):  # mirror around the centre line
            return 0.5 + sgn * (u - 0.5)
        dark.append((part, "front", "poly", [(m(0.06), 0.34), (m(0.28), 0.47), (m(0.49), 0.44), (m(0.49), 0.5),
                                              (m(0.28), 0.54), (m(0.06), 0.42)]))  # under the pecs
        dark.append((part, "front", "poly", [(m(0.1), 0.52), (m(0.17), 0.52), (m(0.33), 0.99), (m(0.25), 0.99)]))  # obliques
        hi.append((part, "front", "ellipse", (m(0.28), 0.28, 0.17, 0.09)))  # pec tops
        for v in (0.6, 0.73, 0.86):
            hi.append((part, "front", "ellipse", (m(0.41), v, 0.065, 0.045)))  # ab pads
            dark.append((part, "front", "ellipse", (m(0.41), v + 0.065, 0.07, 0.012)))  # ab grooves
        dark.append((part, "back", "poly", [(m(0.08), 0.5), (m(0.45), 0.36), (m(0.45), 0.42), (m(0.12), 0.6)]))
        hi.append((part, "back", "ellipse", (m(0.27), 0.25, 0.17, 0.12)))
    dark.append((part, "front", "ellipse", (0.5, 0.75, 0.012, 0.24)))  # centre line
    dark.append((part, "front", "ellipse", (0.5, 0.3, 0.012, 0.12)))
    dark.append((part, "back", "ellipse", (0.5, 0.5, 0.015, 0.42)))  # spine
    for side in ("Left", "Right"):
        for f in ("front", "back", "left", "right"):
            hi.append((side + "UpperArm", f, "ellipse", (0.5, 0.25, 0.4, 0.16)))  # delts
            dark.append((side + "UpperArm", f, "ellipse", (0.5, 0.42, 0.42, 0.03)))  # delt line
            hi.append((side + "UpperArm", f, "ellipse", (0.5, 0.66, 0.28, 0.18)))  # biceps
            dark.append((side + "UpperArm", f, "ellipse", (0.5, 0.9, 0.35, 0.05)))
            hi.append((side + "LowerArm", f, "ellipse", (0.45, 0.3, 0.25, 0.2)))
    soft_shapes(p, dark, shadow, 0.75, blur=7)
    soft_shapes(p, hi, light, 0.6, blur=10)


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
        self.sculpt = None  # {part: [(face, cu, cv, ru, rv, height)]} real 3D muscle bulges
        # Fully helmed knights: the hidden head is shrunk so the helm can be slim (a small
        # head on broad armour reads as big and dangerous).
        self.head_scale = None


def villager():
    ch = Character("Villager", weapon="Hoe")
    _, ch.painter, _, _ = style2.villager()
    ch.hairs.append(("Head", "Hair", hair.swept_short(11, part=1), ((80, 55, 36), (45, 30, 20), (160, 120, 85))))
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
    ch.hairs.append(("Head", "Hair", hair.knot_v3(13), ((45, 36, 30), (28, 22, 18), (95, 80, 70))))
    ch.hairs.append(("Head", "Beard", hair.beard_v3(14), ((45, 36, 30), (28, 22, 18), (95, 80, 70))))
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


def pelt(over_helmet=False):
    """Wolf-pelt hood: shaggy fur over the head and shoulders, with the wolf's ears.
    over_helmet: bigger, to sit on top of a knight's helmet."""
    h = hair.HairBuilder(9)
    extra = 0.26 if over_helmet else 0.0
    h.pad = 0.02 + extra
    h.cap(radius=hair.HEAD_HALF + 0.08 + extra, front_cut=0.25 + (0.15 if over_helmet else 0), back_low=-0.7)
    rnd = h.rnd
    for d in hair.around(rnd, 30, (-25, 40), (55, 305)):
        h.clump(d, rnd.uniform(0.5, 0.9), rnd.uniform(0.18, 0.25), gravity=1.0, lift=-0.2, twist=rnd.uniform(-0.5, 0.5))
    for s in (1, -1):  # ears
        h.clump(Vector((s * 0.45, 0.0, 1.0)), 0.45, 0.22, gravity=-0.3, lift=1.0, thickness=0.4)
    for d in hair.around(rnd, 6, (40, 60), (-40, 40)):  # fur over the brow
        h.clump(d, 0.3, 0.2, gravity=0.8, curl=1.0 if d.x > 0 else -1.0)
    return h.finish()


KNIGHT_TIERS = {
    # One-Horn design language, escalating with rank.
    "apprentice": dict(remap={"plate_dark": "plate_rust", "plate_mid": "iron", "plate_trim": "plate_mid",
                              "plate_corrupt": "plate_rust"},
                       cfg=dict(horn=False, head_crystals=False, chest_v=False, crystals=0.2), shield="round",
                       gamb=(120, 98, 72)),
    "apprentice_infected": dict(remap={"plate_dark": "plate_rust", "plate_mid": "iron", "plate_trim": "plate_mid"},
                                cfg=dict(horn=False, head_crystals=False, chest_v=True, crystals=0.5), shield="round",
                                gamb=(100, 80, 64)),
    "mid": dict(remap={}, cfg=dict(horn=False, twin_horns=0.6, head_crystals=True, chest_v=True, crystals=0.8),
                shield="heater", gamb=(60, 50, 56), cape=("cloth_dark", 2.4)),
    "high": dict(remap={"plate_trim": "gold", "plate_mid": "plate_dark"},
                 cfg=dict(horn=False, twin_horns=1.1, crest=True, head_crystals=True, chest_v=True, crystals=1.4,
                          right_crystals=True), shield="kite", gamb=(40, 34, 44), cape=("cloth", 3.4)),
}


def remap_tiles(outfit, remap):
    idx = {kit.TILES.index(a): kit.TILES.index(b) for a, b in remap.items()}
    for kinds in outfit.pieces.values():
        for piece in kinds.values():
            for f in piece.bm.faces:
                f[piece.col] = idx.get(f[piece.col], f[piece.col])


def knight(kind, corruption_level, name, weapon, seed):
    tier = KNIGHT_TIERS[kind]
    ch = Character(name, weapon=weapon, shield=True)
    skin = (128, 136, 130)
    p = Painter(seed=seed)
    skin_all(p, skin)
    cyclops_face(p, skin, iris=(210, 90, 255), corruption=True)
    gamb = tier["gamb"]
    shirt(p, gamb, sleeves="long")
    for part in style2.PARTS:
        if part != "Head":
            for f in SIDES4:
                quilt(p, part, f, gamb)
    gloves(p, (50, 40, 34))
    p.shade()
    ch.painter = p
    o = elite.elite_onehorn(name, corruption_level, **tier["cfg"])
    remap_tiles(o, tier["remap"])
    {"round": knights.round_shield, "heater": knights.heater_shield, "kite": knights.kite_shield}[tier["shield"]](o)
    if "cape" in tier:
        color, length = tier["cape"]
        common.back_cloth(o, color, top=0.85, length=length, width=1.0, y=0.8)
    ch.outfit = o
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


KING_HAIR = ((246, 170, 225), (170, 90, 190), (255, 230, 250))  # pink-lilac blaze


def king_face(p, skin):
    """The King's face: no mouth, a deep black socket (the glowing eye is geometry),
    a heavy V brow and frown lines."""
    P = "Head"
    dark = (40, 14, 34)
    # Socket centred on the glowing eye geometry (z = +0.04 on the head -> v ~ 0.47).
    p.ellipse(P, "front", 0.5, 0.47, 0.34, 0.1, (90, 50, 80))
    p.ellipse(P, "front", 0.5, 0.47, 0.29, 0.065, dark)
    p.poly(P, "front", [(0.1, 0.26), (0.5, 0.41), (0.9, 0.26), (0.9, 0.34), (0.5, 0.47), (0.1, 0.34)],
           mul(skin, 0.5))
    p.line(P, "front", [(0.46, 0.41), (0.43, 0.3)], mul(skin, 0.45), width=5)
    p.line(P, "front", [(0.54, 0.41), (0.57, 0.3)], mul(skin, 0.45), width=5)


def cyclops_king(sculpted=False):
    ch = Character("CyclopsKing3D" if sculpted else "CyclopsKing", glow=PINK)
    if sculpted:
        ch.sculpt = king_bumps()
    ch.outfit.hair_tint = (246, 170, 225)  # accessories loaded by ID are recoloured to the mane's pink
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
    king_face(p, skin)
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
    ch.hairs.append(("Head", "Hair", hair.super_mane(21), KING_HAIR))
    o = ch.outfit
    h = o("Head")
    band(h, 0.32, 0.44, 0.66, 0.66, 0.24, "gold")
    h.spike((0, -0.42, 0.4), (0, 0.12, 1), 1.6, 0.2, "horn", sides=6)
    g = o("Head", "Glow")
    # Glowing eye like the knights': a bright slit with a diamond core, set in the dark socket.
    g.box((0.6, 0.04, 0.075), "glow", pos=(0, -0.625, 0.04))
    g.box((0.2, 0.05, 0.2), "glow", pos=(0, -0.63, 0.04), rot=(0, 45, 0))
    g.box((0.08, 0.06, 0.08), "glow", pos=(0, -0.645, 0.04), rot=(0, 45, 0))
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


# ---------------------------------------------------------------------------
# Nobles, soldiers and the wolf corps.
def embroidery(p, part, face, color, seed=0):
    """Gold scrollwork: mirrored swirls down a panel."""
    rnd = random.Random(seed)
    for k in range(4):
        v = 0.12 + 0.22 * k
        for sgn in (1, -1):
            pts = [(0.5 + sgn * (0.06 + 0.12 * math.cos(a / 3)), v + 0.07 * math.sin(a / 3)) for a in range(0, 19, 3)]
            p.line(part, face, pts, color, width=4)
        p.ellipse(part, face, 0.5, v, 0.025, 0.025, color)


def ruff(o, color="linen", n=18):
    t = o("UpperTorso")
    for k in range(n):
        a = 2 * math.pi * k / n
        d = (math.cos(a), math.sin(a) * 0.7, 0.15)
        t.spike((0.3 * math.cos(a), 0.22 * math.sin(a), 0.82), d, 0.42, 0.13, color, sides=4)


def fur_mantle(o, color="fur", n=16):
    t = o("UpperTorso")
    for k in range(n):
        a = math.pi * (-0.1 + 1.2 * k / (n - 1))
        x = math.cos(a) * 1.0
        y = 0.55 - math.sin(a) * 0.05
        t.spike((x, y * (1 if k % 2 else -1) * 0.9, 0.78), (x * 0.6, (1 if k % 2 else -1) * 0.4, -0.6), 0.45, 0.16,
                color, sides=4)


def kettle_helmet(o, color="plate_mid"):
    h = o("Head")
    h.shell([(0.2, 0.72, 0.72, 0.22), (0.5, 0.66, 0.66, 0.22), (0.72, 0.38, 0.38, 0.16)], color, tip=(0, 0, 0.8))
    band(h, 0.18, 0.28, 0.98, 0.98, 0.32, color)
    band(h, 0.27, 0.33, 0.73, 0.73, 0.22, "leather_strap")


def tower_shield(o):
    s = o("LeftLowerArm", "Shield")
    outline = [(-0.7, 1.3), (0.7, 1.3), (0.75, -1.2), (0.0, -1.45), (-0.75, -1.2)]
    prof = [(-up, across) for across, up in outline]
    s.loft([(0.62, prof), (0.74, prof)], "shield", rot=(0, 90, 0))
    big = [(x * 1.06, y * 1.04) for x, y in prof]
    s.loft([(0.6, big), (0.66, big)], "plate_mid", rot=(0, 90, 0))
    blob(s, (0.8, 0, 0.05), (0.1, 0.22, 0.22), "plate_trim")


def spline(pts, steps=8):
    """Catmull-Rom through the control points (smooth flowing lines)."""
    if len(pts) < 3:
        return pts
    ext = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        for s in range(steps):
            t = s / steps
            out.append(tuple(0.5 * (2 * p1[k] + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t * t
                                    + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t ** 3) for k in range(2)))
    out.append(pts[-1])
    return out


def glow_lines(p, strokes, color, core, halo=20):
    """Smooth glowing lines (a soft halo, a coloured line and a bright core).
    strokes: (part, face, points, width)."""
    mask = Image.new("L", p.img.size, 0)
    md = ImageDraw.Draw(mask)
    paths = [([p.at(part, face, u, v) for u, v in spline(pts)], width) for part, face, pts, width in strokes]
    for path, width in paths:
        md.line(path, fill=255, width=int(width + halo * width / 10), joint="curve")
    mask = mask.filter(ImageFilter.GaussianBlur(halo / 2)).point(lambda x: int(x * 0.75))
    p.img = Image.composite(Image.new("RGB", p.img.size, color), p.img, mask)
    p.d = ImageDraw.Draw(p.img)
    for path, width in paths:
        p.d.line(path, fill=color, width=int(width), joint="curve")
        p.d.line(path, fill=core, width=max(2, int(width / 3)), joint="curve")


def vein(rnd, strokes, part, face, start, end, width, depth):
    """A wandering glowing vein from start to end that forks into thinner branches."""
    (u0, v0), (u1, v1) = start, end
    du, dv = u1 - u0, v1 - v0
    length = math.hypot(du, dv) or 1e-6
    nu, nv = -dv / length, du / length  # perpendicular
    pts = [start]
    for k in range(1, 4):
        t = k / 4
        off = rnd.uniform(-0.04, 0.04) * min(1.0, length * 2)
        pts.append((u0 + du * t + nu * off, v0 + dv * t + nv * off))
    pts.append(end)
    strokes.append((part, face, pts, width))
    if depth <= 0 or width < 3:
        return
    for _ in range(rnd.choice((1, 2, 2, 3))):
        i = rnd.randint(1, 3)
        bu, bv = pts[i]
        ang = math.atan2(dv, du) + rnd.choice((1, -1)) * math.radians(rnd.uniform(25, 60))
        ln = length * rnd.uniform(0.25, 0.45)
        eu = min(1.0, max(0.0, bu + math.cos(ang) * ln))
        ev = min(1.0, max(0.0, bv + math.sin(ang) * ln))
        vein(rnd, strokes, part, face, (bu, bv), (eu, ev), width * 0.6, depth - 1)


def energy_veins(p, color, core, seed=3):
    """Glowing veins branching out from the chest eye to every part of the body, like
    lightning under the skin (not a muscle grid)."""
    rnd = random.Random(seed)
    S = []

    def trunk(part, face, a, b, width=11, depth=2):
        vein(rnd, S, part, face, a, b, width * 1.4, depth)

    T = "UpperTorso"
    eye = (0.5, 0.24)
    for end in ((0.02, 0.02), (0.98, 0.02), (0.0, 0.48), (1.0, 0.48), (0.5, 1.0), (0.18, 1.0), (0.82, 1.0)):
        trunk(T, "front", eye, end, 13)
    trunk(T, "back", (0.5, 0.0), (0.5, 1.0), 12)
    trunk(T, "back", (0.05, 0.05), (0.38, 0.95))
    trunk(T, "back", (0.95, 0.05), (0.62, 0.95))
    for f in ("left", "right"):
        trunk(T, f, (0.5, 0.0), (0.5, 1.0), 10, 1)
    for u in (0.2, 0.5, 0.8):
        trunk("LowerTorso", "front", (u, 0.0), (u + rnd.uniform(-0.08, 0.08), 1.0), 9, 0)
        trunk("LowerTorso", "back", (u, 0.0), (u, 1.0), 8, 0)
    for side in ("Left", "Right"):
        for f in SIDES4:
            trunk(side + "UpperArm", f, (0.5, 0.0), (rnd.uniform(0.35, 0.65), 1.0), 10 if f == "front" else 8)
            trunk(side + "LowerArm", f, (rnd.uniform(0.35, 0.65), 0.0), (0.5, 1.0), 9 if f == "front" else 7)
            trunk(side + "UpperLeg", f, (rnd.uniform(0.3, 0.7), 0.0), (0.5, 1.0), 10 if f == "front" else 8)
            trunk(side + "LowerLeg", f, (0.5, 0.0), (rnd.uniform(0.35, 0.65), 1.0), 9 if f == "front" else 7, 1)
        trunk(side + "UpperLeg", "front", (0.75, 0.0), (0.6, 1.0), 8, 1)
        trunk(side + "Hand", "front", (0.5, 0.0), (0.5, 0.7), 6, 1)
    trunk("Head", "back", (0.5, 1.0), (0.5, 0.1), 8, 1)
    for u in (0.3, 0.7):
        trunk("Head", "front", (u, 1.0), (0.5 + (u - 0.5) * 1.6, 0.65), 6, 1)
    glow_lines(p, S, color, core)


def cyclops_prince():
    """Sub-boss: the Cyclops Prince, the most corrupted of them all. The King's son - his
    pink mane, but swept back and long; black-violet skin traced with glowing violet lines
    that follow his muscles and joints, an eye on the chest, a crown with a young horn,
    crystal-overgrown half-armour, a royal cape and a pair of moon blades (or the moon
    spear)."""
    ch = Character("CyclopsPrince", glow=PRINCE_GLOW, weapon="MoonBlade")
    ch.sculpt = prince_bumps()
    skin = (40, 26, 52)
    p = Painter(seed=71)
    skin_all(p, skin)
    muscles(p, skin)
    king_face(p, skin)
    p.fill("LowerTorso", FACES, (20, 14, 28))
    boots(p, (18, 14, 24), height=0.25, cuff=(200, 160, 70))
    energy_veins(p, PRINCE_GLOW, (245, 215, 255))
    for side in ("Left", "Right"):
        for f in SIDES4:
            p.box(side + "UpperArm", f, 0, 0.6, 1, 0.7, (220, 180, 70))  # gold arm bands
    p.shade()
    ch.painter = p
    ch.hairs.append(("Head", "Hair", hair.prince_hair(22), PRINCE_HAIR))
    o = ch.outfit
    o.hair_tint = PRINCE_HAIR[0]
    h, hg = o("Head"), o("Head", "Glow")
    # Crown: an engraved circlet with points and gems, and a young horn.
    band(h, 0.34, 0.46, 0.67, 0.67, 0.24, "gold_engraved")
    for k in range(7):
        ang = math.pi * (0.1 + 0.8 * k / 6)
        x, y = 0.7 * math.cos(ang), -0.7 * math.sin(ang)
        h.spike((x, y, 0.45), (x * 0.3, y * 0.3, 1), 0.3 + 0.12 * (k % 2), 0.07, "gold", sides=4)
    weapons.gem(h, (0, -0.72, 0.4), 0.09)
    h.spike((0, -0.4, 0.45), (0, 0.15, 1), 1.0, 0.14, "horn", sides=6)
    # Glowing eye (as the King's) in the painted socket.
    hg.box((0.56, 0.04, 0.07), "glow", pos=(0, -0.625, 0.04))
    hg.box((0.19, 0.05, 0.19), "glow", pos=(0, -0.63, 0.04), rot=(0, 45, 0))
    # The chest eye.
    t, tg = o("UpperTorso"), o("UpperTorso", "Glow")
    for sgn in (1, -1):
        t.box((0.5, 0.06, 0.07), "gold", pos=(0, -0.53, 0.42 + sgn * 0.11), rot=(0, sgn * 12, 0))
    tg.box((0.42, 0.04, 0.12), "glow", pos=(0, -0.54, 0.42))
    tg.box((0.17, 0.05, 0.17), "glow", pos=(0, -0.55, 0.42), rot=(0, 45, 0))
    # Gold gorget and a single great pauldron on the left, the cape hanging from it.
    t.shell([(0.7, 0.62, 0.5, 0.16), (0.9, 0.55, 0.45, 0.14)], "gold_engraved")
    la = o("LeftUpperArm")
    la.shell([(0.2, 0.82, 0.76, 0.24, 0.12, 0), (0.6, 0.76, 0.7, 0.24, 0.06, 0), (0.88, 0.42, 0.44, 0.16, 0, 0)],
             "plate_black")
    band(la, 0.1, 0.24, 0.85, 0.79, 0.25, "gold_engraved", dx=0.12)
    for i in range(3):
        la.box((0.5, 1.4 - 0.1 * i, 0.3), "plate_black", pos=(0.64 + 0.05 * i, 0, 0.42 - 0.22 * i), rot=(0, 30, 0),
               bottom=(1, 0.9))
    for k in range(3):
        la.spike((0.5 + 0.12 * k, -0.25 + 0.25 * k, 0.85), (0.5, 0, 1), 0.5, 0.08, "gold", sides=4)
    # The heaviest infection of the roster: crystal clusters all over.
    o.crystals("LeftUpperArm", 10, (0.6, 0, 0.7), (0.25, 0.4, 0.15), (0.8, 0, 1), length=(0.5, 1.3),
               radius=(0.08, 0.16))
    o.crystals("RightUpperArm", 7, (-0.55, 0, 0.55), (0.15, 0.35, 0.1), (-0.8, 0, 1), length=(0.4, 1.0),
               radius=(0.07, 0.14))
    o.crystals("UpperTorso", 9, (0.0, 0.6, 0.4), (0.7, 0.05, 0.35), (0, 1, 0.8), length=(0.6, 1.5),
               radius=(0.09, 0.18))
    o.crystals("Head", 6, (0.0, 0.1, 0.65), (0.5, 0.4, 0.05), (0, 0.4, 1), length=(0.3, 0.7), radius=(0.05, 0.1))
    for side, sx in (("Left", 1), ("Right", -1)):
        o.crystals(side + "LowerArm", 4, (sx * 0.6, 0.0, 0.0), (0.05, 0.4, 0.3), (sx, 0, 0.5),
                   length=(0.3, 0.6), radius=(0.05, 0.1))
        o.crystals(side + "LowerLeg", 3, (sx * 0.6, 0.1, 0.0), (0.05, 0.3, 0.3), (sx, 0.3, 0.3),
                   length=(0.25, 0.5), radius=(0.05, 0.09))
    parade.cape(o, dict(cape="cloth_royal", lining="cloth_dark", trim="gold", trim2="gold_engraved", gem="gem"))
    # Navy-and-gold bracers and greaves, a gold belt with a gem.
    for side, sx in (("Left", 1), ("Right", -1)):
        la_ = o(side + "LowerArm")
        la_.shell([(-0.45, 0.58, 0.58, 0.15), (0.35, 0.62, 0.62, 0.16)], "plate_black")
        band(la_, 0.3, 0.42, 0.65, 0.65, 0.17, "gold")
        la_.spike((sx * 0.6, 0, 0.0), (sx, 0, 0.6), 0.35, 0.08, "gold", sides=4)
        ll = o(side + "LowerLeg")
        ll.shell([(-0.1, 0.58, 0.58, 0.15), (0.48, 0.61, 0.61, 0.16)], "plate_black")
        band(ll, 0.44, 0.58, 0.64, 0.64, 0.17, "gold_engraved")
        ll.spike((0, -0.62, 0.5), (0, -1, 0.15), 0.3, 0.16, "gold", sides=4)
    lt = o("LowerTorso")
    band(lt, -0.1, 0.18, 1.06, 0.6, 0.2, "gold_engraved")
    weapons.gem(lt, (0, -0.64, 0.04), 0.12)
    xs = [-0.5, -0.25, 0.0, 0.25, 0.5]
    lt.cloth(xs, -0.1, [-1.5 - 0.3 * (1 - abs(x) / 0.5) for x in xs], -0.66, "cloth_royal", sag=-0.05)
    ch.outfit = o
    return ch


PRINCE_HAIR = ((240, 186, 236), (160, 104, 200), (255, 240, 255))
PRINCE_GLOW = (200, 80, 255)


def prince_bumps():
    """Leaner than his father: real 3D pecs and abs, smaller arms."""
    bumps = king_bumps()
    return {part: [(f, cu, cv, ru, rv, hgt * 0.7) for f, cu, cv, ru, rv, hgt in b] for part, b in bumps.items()}


# ---------------------------------------------------------------------------
# The court: luxury knights in parade armour (One-Horn design language, regal finish).
GOLD_GLOW = (255, 200, 90)
HELMED_HEAD = (0.8, 0.82, 0.95)
CRIMSON = (255, 40, 60)
CYAN = (60, 230, 255)


def armored_painter(seed, skin, gamb, iris=(210, 90, 255)):
    p = Painter(seed=seed)
    skin_all(p, skin)
    cyclops_face(p, skin, iris=iris, corruption=True)
    shirt(p, gamb, sleeves="long")
    for part in style2.PARTS:
        if part != "Head":
            for f in SIDES4:
                quilt(p, part, f, gamb)
    gloves(p, mul(gamb, 0.6))
    p.shade()
    return p


def plume(seed, count=9, pad=0.3, length=1.0):
    pl = hair.HairBuilder(seed)
    pl.chunky = True
    pl.pad = pad
    for k in range(count):
        pl.clump(Vector((0, 0.2 + 0.1 * k, 1)), length + 0.1 * k, 0.2, gravity=0.7, lift=0.6, segments=7,
                 thickness=0.5, taper=1.2)
    return pl.finish()


def white_knight():
    """The White Knight: polished white plate piped in gold, a winged helm, a blue-gem
    sunburst on the chest, a crimson cape, a long holy greatsword and a great shield."""
    ch = Character("KnightWhite", glow=GOLD_GLOW, weapon="RadiantGreatsword", shield=True)
    ch.painter = armored_painter(61, (128, 136, 130), (225, 220, 210), iris=(255, 200, 90))
    ch.outfit = parade.parade_knight(ch.name, "white", glow=GOLD_GLOW, seed=61)
    parade.parade_shield(ch.outfit)
    ch.head_scale = HELMED_HEAD
    return ch


def black_knight():
    """The Black Knight (after Momon): sleek black muscle-cuirass plate traced with gold,
    gold knee cops, a bladed helm and pauldrons, a full crimson cape and two enormous
    greatswords, one in each hand."""
    ch = Character("KnightBlack", glow=CRIMSON, weapon="AbyssGreatsword")
    ch.painter = armored_painter(62, (120, 126, 124), (34, 30, 36), iris=(255, 60, 70))
    ch.outfit = parade.parade_knight(ch.name, "black", glow=CRIMSON, seed=62)
    ch.head_scale = HELMED_HEAD
    return ch


def royal_guard():
    """Royal Guard: polished steel and gold, a gold cross on the chest, a crimson tabard,
    cape and plume, and a towering halberd."""
    ch = Character("KnightRoyalGuard", weapon="RoyalHalberd")
    ch.painter = armored_painter(63, (132, 140, 134), (120, 26, 40))
    ch.outfit = parade.parade_knight(ch.name, "guard", seed=63)
    ch.hairs.append(("Head", "Plume", plume(64, pad=0.36, length=1.3),
                     ((190, 30, 45), (110, 14, 26), (245, 110, 110))))
    ch.head_scale = HELMED_HEAD
    return ch


def paladin():
    """Paladin of the Eye: white-and-gold plate with corrupted lames, a horn and a halo of
    crystal rays, a glowing eye on the chest and a colossal eye maul."""
    ch = Character("KnightPaladin", weapon="EyeWarhammer")
    ch.painter = armored_painter(65, (126, 132, 130), (230, 226, 220))
    ch.outfit = parade.parade_knight(ch.name, "paladin", seed=65)
    ch.head_scale = HELMED_HEAD
    return ch


def dragon_knight():
    """Miniboss: the Cyclops Dragon Knight. Black dragoon plate traced in silver, curved
    blades sweeping back from the helm, shoulders, elbows, knees and back like a dragon's
    wings, a crimson-violet aura and a long winged lance."""
    ch = Character("CyclopsDragonKnight", glow=DRAGON_GLOW, weapon="DragonLance")
    ch.painter = armored_painter(91, (110, 100, 118), (30, 26, 36), iris=(255, 60, 120))
    ch.outfit = parade.parade_knight(ch.name, "dragoon", glow=DRAGON_GLOW, seed=91)
    ch.head_scale = HELMED_HEAD
    return ch


DRAGON_GLOW = (255, 50, 110)


# ---------------------------------------------------------------------------
# Elites of the heavily infected: villagers and ordinary knights the corruption has
# almost consumed. Darker, cracked all over, crystals bursting out of them.
BLIGHT = (215, 90, 255)


def glow_eye(o):
    g = o("Head", "Glow")
    g.box((0.58, 0.04, 0.075), "glow", pos=(0, -0.625, 0.04))
    g.box((0.2, 0.05, 0.2), "glow", pos=(0, -0.63, 0.04), rot=(0, 45, 0))


def blighted_skin(p, skin, count=6, seed=0):
    rnd = random.Random(seed)
    for part in style2.PARTS:
        for f in FACES:
            if f == "front" and part == "Head":
                continue
            p.cracks(part, f, (30, 10, 40), BLIGHT, count=count, seed=rnd.randint(0, 999))
    p.cracks("Head", "front", (30, 10, 40), BLIGHT, count=2, seed=seed)


def villager_blighted():
    """Blighted farmer: grey-violet skin cracked everywhere, rags, crystals erupting from
    the back and shoulders, a crystal-edged reaper's scythe."""
    ch = Character("VillagerBlighted", glow=BLIGHT, weapon="BlightScythe")
    skin = (92, 80, 104)
    p = Painter(seed=81)
    skin_all(p, skin)
    muscles(p, skin)
    shirt(p, (110, 98, 80), sleeves="short")
    for f in SIDES4:  # torn shirt
        p.poly("UpperTorso", f, [(0, 0.55), (0.2, 0.75), (0.35, 0.6), (0.55, 0.85), (0.75, 0.62), (1, 0.8), (1, 1), (0, 1)],
               skin)
    pants(p, (70, 56, 46), belt=(50, 36, 26))
    for part in ("LeftLowerLeg", "RightLowerLeg"):
        for f in SIDES4:
            p.poly(part, f, [(0, 0.3), (0.25, 0.45), (0.5, 0.3), (0.75, 0.5), (1, 0.32), (1, 1), (0, 1)], skin)
    blighted_skin(p, skin, 6, 81)
    king_face(p, skin)
    boots(p, (44, 34, 30), height=0.3)
    p.shade()
    ch.painter = p
    ch.hairs.append(("Head", "Hair", hair.shaggy(31), ((40, 30, 44), (20, 14, 24), (110, 80, 130))))
    o = ch.outfit
    glow_eye(o)
    o.crystals("UpperTorso", 12, (0.0, 0.6, 0.3), (0.7, 0.05, 0.4), (0, 1, 0.6), length=(0.5, 1.4),
               radius=(0.08, 0.17))
    o.crystals("LeftUpperArm", 8, (0.55, 0, 0.5), (0.15, 0.35, 0.2), (1, 0, 0.9), length=(0.4, 1.1),
               radius=(0.07, 0.14))
    o.crystals("RightLowerArm", 5, (-0.55, 0, 0.1), (0.05, 0.35, 0.3), (-1, 0, 0.4), length=(0.3, 0.7),
               radius=(0.05, 0.1))
    o.crystals("Head", 4, (0.35, 0.2, 0.55), (0.2, 0.3, 0.05), (0.6, 0.3, 1), length=(0.3, 0.6),
               radius=(0.05, 0.09))
    return ch


def woodcutter_blighted():
    """Blighted brute: a bare-chested woodcutter whose left arm has become a fist of
    crystal, with a crystal-headed maul."""
    ch = Character("WoodcutterBlighted", glow=BLIGHT, weapon="CrystalMaul")
    ch.sculpt = prince_bumps()
    skin = (86, 76, 98)
    p = Painter(seed=82)
    skin_all(p, skin)
    muscles(p, skin)
    pants(p, (62, 36, 40), belt=(48, 34, 24))
    for u in (0.3, 0.7):
        p.line("UpperTorso", "front", [(u, 0.0), (u, 0.5)], (60, 40, 26), width=18)
    blighted_skin(p, skin, 7, 82)
    king_face(p, skin)
    boots(p, (50, 36, 26), height=0.55, cuff=(40, 36, 34))
    p.shade()
    ch.painter = p
    ch.hairs.append(("Head", "Hair", hair.knot_v3(32), ((34, 26, 30), (18, 12, 16), (100, 80, 110))))
    ch.hairs.append(("Head", "Beard", hair.beard_v3(33), ((34, 26, 30), (18, 12, 16), (100, 80, 110))))
    o = ch.outfit
    glow_eye(o)
    # The crystal fist: the left forearm and hand encased in a cluster.
    o.crystals("LeftLowerArm", 14, (0.2, 0.0, -0.1), (0.4, 0.4, 0.45), (1, 0, 0.2), length=(0.4, 1.0),
               radius=(0.1, 0.2))
    o.crystals("LeftHand", 10, (0.0, 0.0, -0.2), (0.35, 0.35, 0.1), (0, 0, -1), length=(0.3, 0.8),
               radius=(0.1, 0.18))
    o.crystals("LeftUpperArm", 8, (0.5, 0, 0.45), (0.15, 0.35, 0.2), (1, 0, 0.9), length=(0.5, 1.2),
               radius=(0.08, 0.16))
    o.crystals("UpperTorso", 12, (0.0, 0.6, 0.35), (0.75, 0.05, 0.35), (0, 1, 0.7), length=(0.6, 1.6),
               radius=(0.09, 0.19))
    return ch


def knight_blighted(axe=False):
    """Blighted knights: ordinary knights whose armour the crystal has split open."""
    name = "KnightBlightedAxe" if axe else "KnightBlighted"
    ch = Character(name, glow=BLIGHT, weapon="CrystalWarAxe" if axe else "BlightGreatsword")
    ch.painter = armored_painter(83 + axe, (96, 84, 108), (40, 30, 44))
    o = elite.elite_onehorn(name, 1.0, horn=axe, twin_horns=0.0 if axe else 0.7, head_crystals=True,
                            chest_v=True, crystals=2.4, right_crystals=True)
    remap_tiles(o, {"plate_dark": "plate_corrupt_heavy", "plate_mid": "plate_corrupt", "plate_trim": "plate_mid",
                    "cloth": "cloth_dark"} if axe else
                {"plate_dark": "plate_corrupt", "plate_mid": "plate_corrupt_heavy", "plate_trim": "iron"})
    o.glow = BLIGHT
    o.crystals("UpperTorso", 10, (0.0, 0.75, 0.3), (0.7, 0.05, 0.4), (0, 1, 0.7), length=(0.5, 1.4),
               radius=(0.08, 0.17))
    o.crystals("Head", 5, (0.0, 0.3, 0.8), (0.4, 0.3, 0.05), (0, 0.3, 1), length=(0.4, 0.9), radius=(0.06, 0.11))
    for side, sx in (("Left", 1), ("Right", -1)):
        o.crystals(side + "UpperLeg", 3, (sx * 0.62, 0, 0.1), (0.05, 0.4, 0.4), (sx, 0, 0.4), length=(0.25, 0.55),
                   radius=(0.05, 0.1))
        o.crystals(side + "LowerLeg", 2, (sx * 0.62, 0, 0.0), (0.05, 0.3, 0.3), (sx, 0, 0.3), length=(0.2, 0.45),
                   radius=(0.05, 0.08))
    common.back_cloth(o, "cloth_dark", top=0.85, length=2.4, width=1.0, y=0.85)
    ch.outfit = o
    return ch


def spearman(with_shield=False):
    ch = Character("SpearmanShield" if with_shield else "Spearman", weapon="Spear", shield=with_shield)
    skin, gamb, brig = (132, 140, 134), (122, 100, 74), (120, 34, 40)
    p = Painter(seed=54 + with_shield)
    skin_all(p, skin)
    cyclops_face(p, skin, iris=(230, 160, 70))
    shirt(p, gamb, sleeves="long")
    for part in ("LeftUpperArm", "RightUpperArm", "LeftLowerArm", "RightLowerArm"):
        for f in SIDES4:
            quilt(p, part, f, gamb)
    for f in SIDES4:  # brigandine: cloth over riveted plates
        p.box("UpperTorso", f, 0.05, 0.1, 0.95, 1.0, brig, outline=mul(brig, 0.5), width=4)
        for v in (0.25, 0.45, 0.65, 0.85):
            for u in (0.15, 0.32, 0.5, 0.68, 0.85):
                p.ellipse("UpperTorso", f, u, v, 0.018, 0.018, (200, 190, 160))
    pants(p, (82, 66, 50), belt=(60, 40, 26))
    gloves(p, (70, 50, 34))
    boots(p, (62, 44, 30), height=0.7)
    p.shade()
    ch.painter = p
    o = ch.outfit
    kettle_helmet(o)
    for side, sx in (("Left", 1), ("Right", -1)):
        o(side + "UpperArm").box((0.5, 1.15, 0.3), "plate_mid", pos=(sx * 0.5, 0, 0.5), rot=(0, sx * 25, 0))
    common.pouch(o, -0.78)
    if with_shield:
        tower_shield(o)
    return ch


def wolf_handler():
    ch = Character("WolfHandler", weapon="SerratedCleaver")
    skin, fur, leather = (134, 142, 136), (98, 92, 88), (92, 60, 38)
    p = Painter(seed=56)
    skin_all(p, skin)
    cyclops_face(p, skin, iris=(240, 190, 60))
    shirt(p, (70, 58, 52), sleeves="short")
    for f in SIDES4:
        p.box("UpperTorso", f, 0.0, 0.05, 1.0, 0.9, fur)  # fur vest
        for k in range(14):
            u = (k * 0.137) % 1
            p.line("UpperTorso", f, [(u, 0.1), (u + 0.03, 0.85)], mul(fur, 0.75), width=3)
    p.box("UpperTorso", "front", 0.42, 0.05, 0.58, 0.9, (70, 58, 52))
    p.box("LowerTorso", "front", 0.15, 0.0, 0.85, 1.0, leather)
    pants(p, (60, 48, 40), belt=(55, 36, 24))
    for side in ("Left", "Right"):
        wraps(p, side + "LowerArm", (210, 200, 180), count=4)  # bandages
    boots(p, (60, 42, 28), height=0.6, cuff=fur)
    corruption(p, ["RightLowerArm"], 0.35, seed=6)
    p.shade()
    ch.painter = p
    ch.hairs.append(("Head", "Hair", hair.shaggy(12), ((50, 40, 36), (30, 24, 22), (100, 85, 75))))
    o = ch.outfit
    fur_mantle(o)
    lt = o("LowerTorso")
    for k in range(7):  # coiled leash chain at the hip
        lt.box((0.1, 0.05, 0.16), "iron", pos=(0.85, -0.3 + 0.08 * k, -0.15 - 0.09 * k), rot=(0, 0, 90 * (k % 2)))
    lt.box((0.06, 0.06, 0.2), "bone", pos=(-0.7, -0.62, -0.1))  # whistle
    return ch


def wolf_knight():
    ch = Character("WolfKnight", weapon="SerratedSword", shield=False)
    skin = (128, 136, 130)
    p = Painter(seed=57)
    skin_all(p, skin)
    cyclops_face(p, skin, iris=(210, 90, 255), corruption=True)
    shirt(p, (44, 40, 48), sleeves="long")
    for part in style2.PARTS:
        if part != "Head":
            for f in SIDES4:
                quilt(p, part, f, (44, 40, 48))
    p.shade()
    ch.painter = p
    o = elite.elite_onehorn("WolfKnight", 0.6, horn=False, head_crystals=False, chest_v=True, crystals=0.6)
    remap_tiles(o, {"plate_mid": "plate_dark", "plate_trim": "iron"})
    common.back_cloth(o, "fur_dark", top=0.85, length=1.9, width=1.0, y=0.8)
    fur_mantle(o, "fur_dark", n=18)
    ch.outfit = o
    ch.hairs.append(("Head", "Pelt", pelt(over_helmet=True), ((70, 66, 70), (36, 34, 38), (130, 126, 132))))
    return ch


def general():
    ch = Character("General", weapon="DragonSlayer")
    skin = (124, 130, 128)
    p = Painter(seed=58)
    skin_all(p, skin)
    cyclops_face(p, skin, iris=(210, 90, 255), corruption=True)
    shirt(p, (30, 26, 32), sleeves="long")
    p.shade()
    ch.painter = p
    o = elite.elite_onehorn("General", 0.8, horn=False, twin_horns=1.4, head_crystals=True, chest_v=True,
                            crystals=1.1, right_crystals=True)
    remap_tiles(o, {"plate_trim": "gold", "plate_mid": "plate_dark"})
    common.back_cloth(o, "cloth_dark", top=0.88, length=3.8, width=1.15, y=0.82)
    for side, sx in (("Left", 1), ("Right", -1)):  # even bigger pauldrons
        o(side + "UpperArm").shell([(0.5, 0.95, 0.85, 0.26, sx * 0.18, 0), (0.95, 0.6, 0.6, 0.2, sx * 0.08, 0)],
                                   "plate_dark")
    ch.outfit = o
    ch.hairs.append(("Head", "Plume", plume(31), ((170, 30, 40), (90, 12, 20), (230, 90, 90))))
    return ch


ROSTER = {
    "stage1": [villager, hunter, woodcutter, wolf_rider,
               lambda: knight("apprentice", 0.3, "KnightApprentice", "ApprenticeSword", 21), elite_onehorn],
    "stage2": [lambda: knight("apprentice_infected", 0.55, "KnightApprenticeInfected", "ApprenticeAxe", 24),
               lambda: knight("mid", 0.65, "KnightMid", "MidSword", 22),
               lambda: knight("high", 0.9, "KnightHigh", "HighAxe", 23)],
    "court": [white_knight, black_knight, royal_guard, paladin, general],
    "army": [spearman, lambda: spearman(True), wolf_handler, wolf_knight],
    "elite": [villager_blighted, woodcutter_blighted, knight_blighted, lambda: knight_blighted(True)],
    "miniboss": [dragon_knight],
    "boss": [cyclops_prince, cyclops_king, lambda: cyclops_king(sculpted=True)],
}


# ---------------------------------------------------------------------------
# Anime ink outlines: an "inverted hull" per piece - a slightly inflated copy with its
# faces flipped. With back-face culling (Roblox's default) only the rim around the
# silhouette shows, as a black line.
OUTLINE_THICKNESS = {"Body": 0.035, "Hair": 0.03, "Hood": 0.03, "Pelt": 0.03, "Beard": 0.025}


def outline_material():
    mat = bpy.data.materials.get("InkOutline")
    if mat:
        return mat
    mat = bpy.data.materials.new("InkOutline")
    mat.use_nodes = True
    mat.use_backface_culling = True
    mat.diffuse_color = (0.02, 0.015, 0.025, 1)
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    mix = nt.nodes.new("ShaderNodeMixShader")
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    ink = nt.nodes.new("ShaderNodeEmission")
    ink.inputs["Color"].default_value = (0.02, 0.015, 0.025, 1)
    clear = nt.nodes.new("ShaderNodeBsdfTransparent")
    # Ink only for camera rays on front faces; invisible to lights and shadows (preview only -
    # in Roblox the hull is simply a black part with back-face culling).
    path = nt.nodes.new("ShaderNodeLightPath")
    not_cam = nt.nodes.new("ShaderNodeMath")
    not_cam.operation = "SUBTRACT"
    not_cam.inputs[0].default_value = 1.0
    nt.links.new(path.outputs["Is Camera Ray"], not_cam.inputs[1])
    hide = nt.nodes.new("ShaderNodeMath")
    hide.operation = "MAXIMUM"
    nt.links.new(geo.outputs["Backfacing"], hide.inputs[0])
    nt.links.new(not_cam.outputs["Value"], hide.inputs[1])
    nt.links.new(hide.outputs["Value"], mix.inputs["Fac"])
    nt.links.new(ink.outputs["Emission"], mix.inputs[1])
    nt.links.new(clear.outputs["BSDF"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return mat


def make_outline(obj, thickness):
    part, kind = obj.name.split("_", 1)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.002)
    bm.normal_update()
    for v in bm.verts:
        v.co += v.normal * thickness
    bmesh.ops.reverse_faces(bm, faces=bm.faces)
    for layer in list(bm.loops.layers.uv):
        bm.loops.layers.uv.remove(layer)
    me = bpy.data.meshes.new(f"{part}_{kind}Outline")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(outline_material())
    o = bpy.data.objects.new(f"{part}_{kind}Outline", me)
    o.location = obj.location
    bpy.context.collection.objects.link(o)
    return o


SIDE_AXIS = {  # face -> (outward normal, how (u, v) map onto the part's bbox)
    "front": (Vector((0, -1, 0)), lambda n: (n.x, 1 - n.z)),
    "back": (Vector((0, 1, 0)), lambda n: (1 - n.x, 1 - n.z)),
    "left": (Vector((1, 0, 0)), lambda n: (n.y, 1 - n.z)),
    "right": (Vector((-1, 0, 0)), lambda n: (1 - n.y, 1 - n.z)),
}


def sculpt_part(obj, bumps, cuts=4):
    """Subdivide a body part and push real muscle bulges out of it. Bumps use the same
    (face, u, v) coordinates as the painter, so the painted shading lines up with them."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=cuts, use_grid_fill=True)
    bm.normal_update()
    xs, ys, zs = ([getattr(v.co, a) for v in bm.verts] for a in "xyz")
    lo = Vector((min(xs), min(ys), min(zs)))
    span = Vector((max(xs), max(ys), max(zs))) - lo
    for v in bm.verts:
        n = Vector(((v.co.x - lo.x) / span.x, (v.co.y - lo.y) / span.y, (v.co.z - lo.z) / span.z))
        push = Vector()
        for face, cu, cv, ru, rv, height in bumps:
            axis, to_uv = SIDE_AXIS[face]
            if v.normal.dot(axis) < 0.35:
                continue
            u, w = to_uv(n)
            r2 = ((u - cu) / ru) ** 2 + ((w - cv) / rv) ** 2
            if r2 < 1:
                push += axis * height * (1 - r2) ** 2 * min(1.0, v.normal.dot(axis) * 1.6)
        v.co += push
    bm.normal_update()
    bm.to_mesh(obj.data)
    bm.free()
    for poly in obj.data.polygons:
        poly.use_smooth = True


def replace_head(head, template_path, name):
    """Swap the Studio head for a clean one with exactly the default Roblox head's shape.
    The stock head has a mouth slit, an inner mouth and face-feature meshes that show
    through as a smile; cyclopes have no mouth. A finely subdivided rounded block is
    shrink-wrapped onto the stock head's outer surface (rays cast inward from outside),
    dents where a ray fell into the mouth slit are smoothed out, and the result is UV'd
    straight onto the painted template."""
    from mathutils.bvhtree import BVHTree
    src = bmesh.new()
    src.from_mesh(head.data)
    tree = BVHTree.FromBMesh(src)
    xs, ys, zs = ([v.co[k] for v in src.verts] for k in range(3))
    size = (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
    centre = Vector(((max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2, (max(zs) + min(zs)) / 2))
    src.free()

    bm = style2.rounded_box(size, 0.27, centre)
    bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=3, use_grid_fill=True)
    radius = {}
    for v in bm.verts:
        d = (v.co - centre).normalized()
        hit, *_ = tree.ray_cast(centre + d * 3.0, -d, 3.0)
        radius[v] = (hit - centre).length if hit else (v.co - centre).length
    # Median-smooth the radii twice so the mouth slit and face-feature bumps vanish.
    for _ in range(2):
        new = {}
        for v in bm.verts:
            ring = sorted([radius[v]] + [radius[e.other_vert(v)] for e in v.link_edges])
            new[v] = ring[len(ring) // 2]
        radius = new
    for _ in range(2):  # then a light relax so the surface is perfectly smooth
        radius = {v: 0.5 * radius[v] + 0.5 * sum(radius[e.other_vert(v)] for e in v.link_edges) / len(v.link_edges)
                  for v in bm.verts}
    for v in bm.verts:
        v.co = centre + (v.co - centre).normalized() * radius[v]
    bm.normal_update()
    style2.project(bm, "Head")
    me = bpy.data.meshes.new("Head_Body")
    bm.to_mesh(me)
    bm.free()
    me.uv_layers[0].name = "UVMap"
    for poly in me.polygons:
        poly.use_smooth = True
    mat = bpy.data.materials.new(name + "Head")
    mat.use_nodes = True
    t = mat.node_tree.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(template_path)
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    mat.node_tree.links.new(t.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.8
    me.materials.append(mat)
    old = head.data
    head.data = me
    bpy.data.meshes.remove(old)


def king_bumps():
    """Pecs, a six-pack, obliques, back, delts and biceps for the 3D King."""
    t = []
    for c in (0.28, 0.72):
        t.append(("front", c, 0.29, 0.22, 0.17, 0.16))  # pecs
        t.append(("back", c, 0.3, 0.2, 0.24, 0.08))  # back / shoulder blades
    for c in (0.41, 0.59):
        for v in (0.6, 0.73, 0.86):
            t.append(("front", c, v, 0.075, 0.055, 0.07))  # six-pack
    for c in (0.14, 0.86):
        t.append(("front", c, 0.75, 0.08, 0.22, 0.04))  # obliques
    arm = []
    for f in ("front", "back", "left", "right"):
        arm.append((f, 0.5, 0.22, 0.45, 0.2, 0.09))  # deltoid
    arm.append(("front", 0.5, 0.65, 0.3, 0.22, 0.1))  # biceps
    arm.append(("back", 0.5, 0.6, 0.3, 0.25, 0.07))  # triceps
    fore = [("front", 0.45, 0.3, 0.3, 0.25, 0.06), ("back", 0.5, 0.3, 0.3, 0.25, 0.05)]
    bumps = {"UpperTorso": t}
    for side in ("Left", "Right"):
        bumps[side + "UpperArm"] = arm
        bumps[side + "LowerArm"] = fore
    return bumps


def tint_glow(objs, color):
    for o in objs:
        if o.name.split(".")[0].endswith("Glow"):
            o.data.materials.clear()
            o.data.materials.append(glow_material(color))
    return objs


def glow_material(color):
    """Preview material for glow pieces in the character's own colour (in Roblox they
    become Neon parts tinted with the outfit's glow colour)."""
    name = "Glow%02x%02x%02x" % tuple(color)
    mat = bpy.data.materials.get(name)
    if mat:
        return mat
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    c = tuple(x / 255 for x in color) + (1,)
    bsdf.inputs["Base Color"].default_value = c
    bsdf.inputs["Emission Color"].default_value = c
    bsdf.inputs["Emission Strength"].default_value = 3.0
    return mat


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
    replace_head(parts["Head"], template, ch.name)
    if ch.head_scale:
        parts["Head"].data.transform(Matrix.Diagonal(Vector(ch.head_scale)).to_4x4())
    if ch.sculpt:
        for part, bumps in ch.sculpt.items():
            sculpt_part(parts[part], bumps)
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
            mat = glow_material(ch.outfit.glow) if kind.endswith("Glow") else atlas_mats[0]
            objs.append(piece.to_object(f"{part}_{kind}", mat, centres[part]))
    outlines = []
    for o in objs:
        kind = o.name.split("_", 1)[1]
        if not kind.endswith("Glow"):
            outlines.append(make_outline(o, OUTLINE_THICKNESS.get(kind, 0.025)))
    return objs + outlines


def main():
    no_render = "--no-render" in sys.argv
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version = 0
    os.makedirs(OUT, exist_ok=True)
    img = bpy.data.images.load(kit.build_atlas(os.path.join(HERE, "export", "cyclops_texture.png")))
    mats = build_all.make_materials(img)

    # --only Name1,Name2 rebuilds just those characters and keeps everyone else's
    # entries from the existing CyclopsData.lua.
    only = next((a.split("=", 1)[1].split(",") for a in sys.argv if a.startswith("--only=")), None)
    previous = existing_outfit_entries() if only else {}
    outfit_lua, weapon_lua, built = [], [], {}
    for group, makers in ROSTER.items():
        for make in makers:
            ch = make()
            if only and ch.name not in only:
                if ch.name in previous:
                    outfit_lua.append(previous[ch.name])
                continue
            objs = build_character(ch, mats)
            build_all.export_fbx(os.path.join(OUT, ch.name + ".fbx"), objs)
            outfit_lua.append(build_all.lua_outfit(ch.outfit, objs))
            build_all.release_names(objs, ch.name)
            built.setdefault(group, []).append((ch, objs))
            print(f"{ch.name}: {len(objs)} pieces")
    weapon_objs = {}
    for w in weapons.all_weapons():
        objs = tint_glow(build_all.build_weapon_objects(w, mats), w.glow)
        build_all.export_fbx(os.path.join(HERE, "export", "weapons", w.name + ".fbx"), objs)
        weapon_lua.append(build_all.lua_weapon(w, objs))
        build_all.release_names(objs, w.name)
        weapon_objs[w.name] = objs
    build_all.write_data(outfit_lua, weapon_lua, [])
    if no_render:
        return
    render_lineups(built, weapon_objs, mats)


def existing_outfit_entries():
    """Outfit entries (name -> Lua text) from the current generated CyclopsData.lua."""
    path = os.path.join(HERE, "roblox", "CyclopsData.lua")
    if not os.path.exists(path):
        return {}
    text = open(path).read()
    body = text[text.index("\toutfits = {") + len("\toutfits = {"):text.index("\n\t},\n\tweapons")]
    entries, name, buf = {}, None, []
    for line in body.split("\n"):
        if line.startswith("\t\t") and not line.startswith("\t\t\t") and line.rstrip().endswith("= {"):
            name, buf = line.strip().split(" ")[0], [line]
        elif name:
            buf.append(line)
            if line == "\t\t},":
                entries[name] = "\n".join(buf)
                name = None
    return entries


SHOW_USER_HAIR = False  # the King now wears his own original hair (hair.super_mane)
USER_HAIR = "/tmp/claude-0/-home-user-EEE/501a4460-fa65-53b8-babc-75b878986ea1/scratchpad/hair_only.obj"
# Where the hair sits relative to the head centre, measured on the buyer's own avatar
# export (their rig faces +Y; this is already turned to face -Y).
USER_HAIR_OFFSET = Vector((0.006, 0.531, -0.294))


def preview_user_hair(head):
    """Preview only: the hair the user bought, placed on a King's head. It is never
    exported - in game it is loaded onto the King by asset ID."""
    if not os.path.exists(USER_HAIR):
        return None
    before = set(bpy.data.objects)
    bpy.ops.wm.obj_import(filepath=USER_HAIR, use_split_groups=True)
    new = [o for o in bpy.data.objects if o not in before]
    hair_obj = new[0]
    for extra in new[1:]:
        bpy.data.objects.remove(extra)
    vs = [hair_obj.matrix_world @ v.co for v in hair_obj.data.vertices]
    c = Vector([(min(getattr(v, a) for v in vs) + max(getattr(v, a) for v in vs)) / 2 for a in "xyz"])
    hair_obj.data.transform(Matrix.Translation(USER_HAIR_OFFSET) @ Matrix.Rotation(math.pi, 4, "Z")
                            @ Matrix.Translation(-c) @ hair_obj.matrix_world)
    hair_obj.matrix_world = head.matrix_world
    mat = bpy.data.materials.new("UserHairPreview")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.86, 0.8, 0.92, 1)
    hair_obj.data.materials.clear()
    hair_obj.data.materials.append(mat)
    for poly in hair_obj.data.polygons:
        poly.use_smooth = True
    return hair_obj


SPACING = {"court": 6.4, "elite": 6.0, "boss": 6.0, "miniboss": 7.0}


def pose_weapons(ch, objs, mats, k):
    """Weapons for the lineup renders. Long weapons are raised beside the body so their
    full length reads from the front; a dual wielder's second blade hangs low in the left
    hand, like the Black Knight's reference pose."""
    w = {x.name: x for x in weapons.all_weapons()}[ch.weapon]
    length = max(v.co.z for piece in w.pieces.values() for v in piece.bm.verts)
    for piece in w.pieces.values():
        piece.bm.free()
    raised = length > 4.5 or w.dual
    out = []
    for side, aim in (("Right", (-0.3, -0.15, 1) if raised else (-0.15, -0.8, -0.55)),
                      ("Left", (0.55, -0.25, -0.8))):
        if side == "Left" and not w.dual:
            break
        hand = next(o for o in objs if o.name.endswith(side + "Hand_Body")).matrix_world.translation
        copy = tint_glow(build_all.held_weapon(weapons, ch.weapon, mats, hand, k), w.glow)
        m = (Matrix.Translation(hand + Vector((0, -0.1, 0))) @ Matrix.Scale(k, 4)
             @ Vector(aim).to_track_quat("Z", "Y").to_matrix().to_4x4())
        for o in copy:
            o.matrix_world = m
        out += copy
    return out


def render_lineups(built, weapon_objs, mats):
    scene, cam = build_all.setup_scene()
    scene.view_settings.view_transform = "Standard"
    scales = {"CyclopsKing": 1.6, "CyclopsKing3D": 1.6, "CyclopsPrince": 1.3, "CyclopsDragonKnight": 1.2}
    for group, members in built.items():
        shown, x = [], 0.0
        for ch, objs in members:
            k = scales.get(ch.name, 1.0)
            offset = Vector((x + SPACING.get(group, 4.6) / 2 * k, 0, 0))
            build_all.place(objs, offset, k)
            shown += objs
            if ch.weapon:
                shown += pose_weapons(ch, objs, mats, k)
            x += SPACING.get(group, 4.6) * k
        build_all.set_visible(bpy.data.objects, shown)
        bpy.context.view_layer.update()
        top = max(6.8 * max(scales.get(c.name, 1.0) for c, _ in members),
                  max((o.matrix_world @ Vector(c)).z for o in shown for c in o.bound_box) + 0.4)
        center = (x / 2, 0, top / 2 - 0.2)
        if group in ("boss", "miniboss"):
            # One close-up per King; the buyer's own hair is shown here as a preview only.
            for ch, objs in members:
                head = next(o for o in objs if o.name.endswith("Head_Body"))
                user_hair = preview_user_hair(head) if SHOW_USER_HAIR else None
                own = [o for o in objs if "Head_Hair" in o.name]
                visible = [o for o in objs if o not in own] + ([user_hair] if user_hair else own)
                build_all.set_visible(bpy.data.objects, visible)
                cx = head.matrix_world.translation.x
                build_all.render(scene, cam, os.path.join(RENDERS, f"r15_{ch.name}_hero.png"),
                                 (cx - 9, -16, 10), (cx, 0, 6.2), 10.5, (1000, 1000))
                for tag, y in (("front", -40), ("side", None)):
                    loc = (cx, -40, 5.4) if y else (cx + 40, 0, 5.4)
                    build_all.render(scene, cam, os.path.join(RENDERS, f"r15_{ch.name}_{tag}.png"), loc,
                                     (cx, 0, 5.4), 12.5, (1000, 1100))
                if user_hair:
                    user_hair.hide_render = True
            build_all.set_visible(bpy.data.objects, shown)
            res, size = (1800, 1100), max(x + 0.6, (top + 1.8) * 1800 / 1100)
        else:
            res, size = (1800, int(1800 * (top + 1.0) / (x + 0.6))), x + 0.6
        for tag, y in (("front", -40), ("back", 40)):
            build_all.render(scene, cam, os.path.join(RENDERS, f"r15_{group}_{tag}.png"), (center[0], y, center[2]),
                             center, size, res)
        build_all.place(shown, Vector((0, 0, -100)))
    # Weapons sheet: two rows, big enough to read.
    names = list(weapon_objs)
    per_row = (len(names) + 1) // 2
    shown = []
    for i, name in enumerate(names):
        objs = weapon_objs[name]
        row, col = divmod(i, per_row)
        build_all.place(objs, Vector((col * 1.9, 0, 2.0 - row * 9.5)), 1.0,
                        90 if name in build_all.SIDEWAYS | {"Sickle", "Scythe", "Hoe"} else 0)
        shown += objs
    build_all.set_visible(bpy.data.objects, shown)
    width = per_row * 1.9 + 0.6
    cx = (per_row - 1) * 1.9 / 2
    build_all.render(scene, cam, os.path.join(RENDERS, "r15_weapons.png"), (cx, -40, 0.2), (cx, 0, 0.2), width,
                     (1800, int(1800 * 19.5 / width)))

if __name__ == "__main__":
    main()

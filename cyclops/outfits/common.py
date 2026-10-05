"""Garment and body building blocks shared by the cyclops outfits.

Every function adds geometry to Piece objects in R15 part-local space
(see kit.py: Blender units = studs, front = -Y, character left = +X).
"""
import math
import random

from kit import Piece, band, blob, circle, corruption_crystals, tube

# When True, body clothing (shirts, pants, shoes, bare skin, faces...) is painted on the
# real R15 body texture instead of built as geometry; only armor/accessories are built.
PAINTED = False


def _painted_skip(fn):
    def wrapper(*args, **kwargs):
        if PAINTED:
            return None
        return fn(*args, **kwargs)
    wrapper.__name__, wrapper.__doc__ = fn.__name__, fn.__doc__
    return wrapper


PARTS = ["Head", "UpperTorso", "LowerTorso",
         "LeftUpperArm", "LeftLowerArm", "LeftHand", "RightUpperArm", "RightLowerArm", "RightHand",
         "LeftUpperLeg", "LeftLowerLeg", "LeftFoot", "RightUpperLeg", "RightLowerLeg", "RightFoot"]


def side_of(part):
    """+1 for Left parts (+X), -1 for Right parts, 0 for the center line."""
    return 1 if part.startswith("Left") else -1 if part.startswith("Right") else 0


class Outfit:
    """Collects Pieces per R15 part and kind ("Armor", "Glow", "Shield", "ShieldGlow")."""

    def __init__(self, name, glow=(176, 70, 255), corruption=0.0, seed=0):
        self.name = name
        self.glow = glow
        self.corruption = corruption
        self.rnd = random.Random(seed)
        self.pieces = {p: {} for p in PARTS}

    def __call__(self, part, kind="Armor"):
        return self.pieces[part].setdefault(kind, Piece())

    def crystals(self, part, count, center, spread, direction, **kw):
        if count > 0:
            corruption_crystals(self(part, "Glow"), self.rnd, count, center, spread, direction, **kw)


# ---------------------------------------------------------------------------
# Heads
@_painted_skip
def cyclops_head(o, skin="skin", eye_w=0.3, brow=True, ears=True, mouth=True):
    """Bare cyclops head that covers the 1.2 stud block head, with one big eye."""
    a = o("Head")
    a.shell([(-0.62, 0.63, 0.64, 0.2), (0.25, 0.66, 0.67, 0.22), (0.6, 0.5, 0.52, 0.2)], skin,
            tip=(0, 0.04, 0.72))
    # Eye: a disk whose front face carries the whole "eye" tile, under heavy lids.
    a.loft([(0.62, circle(eye_w, 12, 1.25, 1.0)), (0.69, circle(eye_w * 0.97, 12, 1.25, 1.0))],
           "eye", pos=(0, 0, 0.12), rot=(90, 0, 0))
    a.box((eye_w * 2.8, 0.16, 0.13), skin, pos=(0, -0.7, 0.12 + eye_w * 0.95), rot=(-15, 0, 0))
    a.box((eye_w * 2.3, 0.12, 0.08), skin, pos=(0, -0.69, 0.12 - eye_w * 0.98))
    if brow:
        a.box((1.18, 0.2, 0.16), skin, pos=(0, -0.68, 0.12 + eye_w + 0.12), top=(0.9, 0.7))
    a.spike((0, -0.68, -0.14), (0, -0.4, -1), 0.2, 0.09, skin, sides=4)  # nose
    if mouth:
        a.box((0.46, 0.04, 0.045), "black", pos=(0, -0.66, -0.36))
    if ears:
        for s in (1, -1):
            a.spike((s * 0.62, 0.05, 0.08), (s, 0.4, 0.5), 0.32, 0.1, skin, sides=4)
    return a


@_painted_skip
def hair_tuft(o, count=6, length=(0.2, 0.4)):
    rnd = o.rnd
    for _ in range(count):
        o("Head").spike((rnd.uniform(-0.25, 0.25), rnd.uniform(-0.2, 0.3), 0.66),
                        (rnd.uniform(-0.6, 0.6), rnd.uniform(-0.2, 0.8), 1), rnd.uniform(*length),
                        0.06, "hair", sides=4)


@_painted_skip
def beard(o, color="fur_dark", length=0.55):
    a = o("Head")
    a.box((1.0, 0.24, length), color, pos=(0, -0.6, -0.42 - length / 2 + 0.2), bottom=(0.45, 0.8))
    for x in (-0.3, -0.1, 0.1, 0.3):
        a.spike((x, -0.62, -0.5 - length / 2), (x * 0.5, -0.2, -1), 0.25, 0.08, color, sides=4)


# ---------------------------------------------------------------------------
# Bodies and clothing
@_painted_skip
def skin_limbs(o, skin="skin", arms=True, legs=False, muscle=1.0, upper=True):
    """Bare arms (and optionally legs) with simple muscle bulges. upper=False leaves the
    upper arms to sleeves."""
    if arms:
        for s, pre in ((1, "Left"), (-1, "Right")):
            ua, la, h = o(pre + "UpperArm"), o(pre + "LowerArm"), o(pre + "Hand")
            if upper:
                band(ua, -0.6, 0.55, 0.57, 0.57, 0.1, skin, grow=0.03 * muscle)
                blob(ua, (s * 0.1, -0.1, 0.05), (0.42 * muscle, 0.45 * muscle, 0.5), skin)  # biceps
                blob(ua, (s * 0.2, 0, 0.42), (0.6 * muscle, 0.6 * muscle, 0.32), skin)  # deltoid
            band(la, -0.55, 0.52, 0.56, 0.56, 0.1, skin, grow=0.04 * muscle)
            blob(la, (s * 0.05, -0.12, 0.2), (0.48 * muscle, 0.5 * muscle, 0.38), skin)
            band(h, -0.2, 0.18, 0.56, 0.56, 0.1, skin)
            for x in (-0.28, -0.09, 0.1, 0.29):
                h.box((0.17, 0.12, 0.14), skin, pos=(x, -0.56, -0.08))
    if legs:
        for pre in ("Left", "Right"):
            band(o(pre + "UpperLeg"), -0.62, 0.62, 0.57, 0.57, 0.1, skin, grow=0.03)
            band(o(pre + "LowerLeg"), -0.6, 0.6, 0.56, 0.56, 0.1, skin, grow=0.02)


@_painted_skip
def shirt(o, color, sleeves="upper", collar="black"):
    """Simple shirt/tunic on the torso; sleeves: None, "upper" or "full"."""
    t = o("UpperTorso")
    t.shell([(-0.82, 1.06, 0.56, 0.2), (0.6, 1.08, 0.58, 0.22), (0.84, 0.92, 0.5, 0.2)], color)
    t.box((0.34, 0.05, 0.4), collar, pos=(0, -0.58, 0.62), bottom=(0.1, 1))
    for pre in ("Left", "Right"):
        if sleeves:
            band(o(pre + "UpperArm"), -0.45, 0.6, 0.56, 0.56, 0.16, color, grow=0.02)
        if sleeves == "full":
            band(o(pre + "LowerArm"), -0.3, 0.53, 0.55, 0.55, 0.16, color)


@_painted_skip
def tunic_skirt(o, color, length=0.9, ragged=True):
    """Skirt of a tunic, hanging from the waist."""
    lt = o("LowerTorso")
    lt.shell([(-0.2 - length, 1.16, 0.66, 0.24), (0.1, 1.08, 0.6, 0.2)], color)
    if ragged:
        xs = [-0.9, -0.6, -0.3, 0.0, 0.3, 0.6, 0.9]
        bottoms = [-0.2 - length - o.rnd.uniform(0.05, 0.25) for _ in xs]
        lt.cloth(xs, -0.2 - length + 0.05, bottoms, -0.66, color)


@_painted_skip
def belt(o, color="leather_strap", buckle="buckle", z=0.0, w=1.13, d=0.65, h=0.3):
    lt = o("LowerTorso")
    band(lt, z - h / 2, z + h / 2, w, d, 0.2, color)
    if buckle:
        lt.box((0.36, 0.08, h + 0.06), buckle, pos=(0, -d - 0.03, z))
        lt.box((0.2, 0.05, h * 0.5), "black", pos=(0, -d - 0.07, z))


def pouch(o, x, y=-0.55, z=-0.25, color="leather"):
    lt = o("LowerTorso")
    lt.box((0.32, 0.24, 0.36), color, pos=(x, y, z))
    lt.box((0.35, 0.27, 0.12), "leather_strap", pos=(x, y, z + 0.17))


@_painted_skip
def pants(o, color="cloth_brown", baggy=1.0, to_ankle=True):
    for pre in ("Left", "Right"):
        band(o(pre + "UpperLeg"), -0.62, 0.62, 0.56 * baggy, 0.56 * baggy, 0.16, color, grow=0.02)
        if to_ankle:
            band(o(pre + "LowerLeg"), -0.6, 0.6, 0.55 * baggy, 0.55 * baggy, 0.16, color)
    band(o("LowerTorso"), -0.22, 0.22, 1.08, 0.6, 0.2, color)


@_painted_skip
def wraps(o, part, zs, color="linen", w=0.6):
    for z in zs:
        band(o(part), z - 0.05, z + 0.05, w, w, 0.16, color)


@_painted_skip
def shoes(o, color="leather", tall=0.0, cuff=None, toe="leather_strap"):
    for pre in ("Left", "Right"):
        f = o(pre + "Foot")
        f.shell([(-0.2, 0.57, 0.66, 0.16, 0, -0.12), (0.22, 0.56, 0.6, 0.16, 0, -0.04)], color)
        f.box((1.14, 1.44, 0.08), "leather_strap", pos=(0, -0.13, -0.21))
        f.box((0.9, 0.3, 0.16), toe, pos=(0, -0.68, -0.08), top=(0.8, 0.7))
        if tall:
            ll = o(pre + "LowerLeg")
            band(ll, -0.6, -0.6 + tall, 0.58, 0.58, 0.16, color, grow=0.03)
            if cuff:
                band(ll, -0.62 + tall, -0.48 + tall, 0.64, 0.64, 0.2, cuff)


@_painted_skip
def gloves(o, color="leather", cuff=True):
    for pre in ("Left", "Right"):
        h = o(pre + "Hand")
        band(h, -0.2, 0.15, 0.55, 0.55, 0.15, color)
        if cuff:
            band(h, 0.06, 0.3, 0.6, 0.6, 0.16, color, grow=0.05)


@_painted_skip
def bracers(o, color="leather", sides=("Left", "Right")):
    for pre in sides:
        band(o(pre + "LowerArm"), -0.5, 0.15, 0.6, 0.6, 0.16, color, grow=0.03)
        wraps(o, pre + "LowerArm", (-0.35, -0.05), "leather_strap", 0.62)


def back_cloth(o, color, top=0.75, length=1.4, width=0.75, y=0.62, part="UpperTorso"):
    n = 7
    xs = [-width + 2 * width * i / (n - 1) for i in range(n)]
    bottoms = [top - length + o.rnd.uniform(-0.3, 0.15) for _ in xs]
    o(part).cloth(xs, top, bottoms, y, color, sag=0.04)


def strap_diagonal(o, color="leather_strap", side=1, front=True, back=True):
    t = o("UpperTorso")
    for y, on in ((-0.62, front), (0.62, back)):
        if on:
            t.box((0.2, 0.06, 1.85), color, pos=(0, y, 0.05), rot=(0, side * 38 * (1 if y < 0 else -1), 0))

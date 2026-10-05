"""Wolves for the cyclops roster: a pack wolf (minion) and a big alpha.

They are plain wolves on purpose - no crystals or glow - so the corruption can be
hinted at through behaviour instead. Each wolf is split into jointed parts with a
pivot per joint; the Roblox side builds Motor6Ds from these so the wolf can be
animated without an armature.

Built facing -Y, feet on z = 0, at pack-wolf scale; the alpha is scaled up.
"""
import random

from mathutils import Matrix

from kit import Piece, blob, tube


class Creature:
    def __init__(self, name, root="Torso"):
        self.name, self.root = name, root
        self.pieces = {}
        self.joints = {}  # part -> (parent, pivot in Blender space)
        self.k = 1.0  # geometry scale, applied when the parts are turned into objects

    def __call__(self, part, parent=None, pivot=None):
        if parent:
            self.joints[part] = (parent, pivot)
        return self.pieces.setdefault(part, Piece())

    def scale(self, k):
        self.joints = {p: (parent, tuple(v * k for v in pivot)) for p, (parent, pivot) in self.joints.items()}
        self.k = k


def wolf(name, coat="fur", dark="fur_dark", mane="fur", size=1.0, seed=1, ruff=14):
    c = Creature(name)
    rnd = random.Random(seed)
    t = c("Torso")
    blob(t, (0, -0.75, 1.95), (0.56, 0.8, 0.7), coat, sides=8)  # deep chest
    blob(t, (0, -0.05, 2.0), (0.48, 0.8, 0.52), coat, sides=8)  # ribs, joining chest and hips
    blob(t, (0, 0.65, 2.0), (0.46, 0.75, 0.5), coat, sides=8)  # hips
    for i in range(ruff):  # neck ruff / mane
        a = -1 + 2 * i / (ruff - 1)
        t.spike((a * 0.45, -1.05, 2.25 + rnd.uniform(-0.15, 0.25)), (a * 1.2, -0.3, rnd.uniform(-0.3, 0.6)),
                rnd.uniform(0.35, 0.6), 0.14, mane, sides=4, twist=rnd.uniform(0, 3))
    for i in range(9):  # darker fur along the back, lying flat toward the tail
        t.spike((rnd.uniform(-0.2, 0.2), -0.9 + 0.25 * i, 2.5 - 0.02 * i), (rnd.uniform(-0.3, 0.3), 1, 0.25),
                rnd.uniform(0.35, 0.5), 0.12, dark, sides=4, twist=rnd.uniform(0, 3))
    for i in range(6):  # shaggy belly
        t.spike((rnd.uniform(-0.25, 0.25), -0.9 + 0.3 * i, 1.6), (rnd.uniform(-0.3, 0.3), 0.3, -1),
                0.25, 0.1, coat, sides=4)

    h = c("Head", "Torso", (0, -1.3, 2.3))
    blob(h, (0, -1.45, 2.45), (0.38, 0.45, 0.42), coat)  # neck
    blob(h, (0, -1.85, 2.75), (0.38, 0.42, 0.35), coat)  # skull
    h.box((0.34, 0.66, 0.28), coat, pos=(0, -2.35, 2.64), top=(0.8, 1), bottom=(0.9, 1))  # snout
    h.box((0.17, 0.12, 0.12), "black", pos=(0, -2.68, 2.72))  # nose
    h.box((0.28, 0.52, 0.12), dark, pos=(0, -2.3, 2.45))  # jaw
    for s in (1, -1):
        h.spike((s * 0.2, -1.72, 3.0), (s * 0.3, 0.2, 1), 0.38, 0.12, dark, sides=4)  # ears
        h.box((0.09, 0.05, 0.07), "gold", pos=(s * 0.19, -2.14, 2.86), rot=(0, s * 15, 0))  # eyes
        h.spike((s * 0.12, -2.55, 2.5), (0, 0, 1), 0.1, 0.025, "bone", sides=3)  # fangs
        for z in (2.55, 2.75):
            h.spike((s * 0.35, -1.75, z), (s, 0.4, -0.2), 0.3, 0.1, mane, sides=4)  # cheek fur

    tail = c("Tail", "Torso", (0, 1.35, 2.15))
    tail.spike((0, 1.3, 2.15), (0, 0.8, -0.45), 1.5, 0.2, coat, sides=5)
    for i in range(4):
        tail.spike((0, 1.55 + 0.25 * i, 2.0 - 0.14 * i), (rnd.uniform(-0.5, 0.5), 0.6, rnd.uniform(-0.6, 0.4)),
                   0.4, 0.12, dark if i == 3 else coat, sides=4)

    for side, sx in (("Left", 1), ("Right", -1)):
        for end, y, thigh in (("Front", -0.85, False), ("Back", 0.75, True)):
            x = sx * 0.3
            up = c(f"{end}{side}UpperLeg", "Torso", (x, y, 1.85))
            if thigh:
                blob(up, (x, y + 0.05, 1.6), (0.27, 0.45, 0.5), coat)
            else:
                blob(up, (x, y + 0.05, 1.6), (0.24, 0.32, 0.42), coat)  # shoulder
            tube(up, 0.95, 1.7, 0.17, 0.24, coat, sides=6, pos=(x, y + (0.12 if thigh else 0), 0))
            blob(up, (x, y + (0.12 if thigh else 0), 1.0), (0.17, 0.19, 0.16), coat, sides=6, rings=3)
            low = c(f"{end}{side}LowerLeg", f"{end}{side}UpperLeg", (x, y, 1.0))
            # Hind legs angle back at the hock; forelegs are straight.
            tube(low, 0.15, 1.02, 0.12, 0.15, coat, sides=6, pos=(x, y, 0), rot=(-12 if thigh else 0, 0, 0))
            low.box((0.32, 0.46, 0.18), dark, pos=(x, y - 0.1, 0.09), top=(0.85, 0.8))
            for dx in (-0.09, 0.0, 0.09):
                low.spike((x + dx, y - 0.32, 0.06), (0, -1, -0.3), 0.08, 0.03, "bone", sides=3)
    c.scale(size)
    return c


def pack_wolf():
    return wolf("Wolf", coat="fur", dark="fur_dark", mane="fur", size=1.0, seed=3, ruff=12)


def alpha_wolf():
    """Bigger, darker, heavier mane and scarred muzzle - big enough to be ridden."""
    c = wolf("AlphaWolf", coat="fur_dark", dark="black", mane="fur", size=1.55, seed=5, ruff=22)
    return c


def all_creatures():
    return [pack_wolf(), alpha_wolf()]

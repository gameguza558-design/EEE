"""Elite cyclops: the One-Horn, a fallen knight with partial corruption (end of stage 1).
Ported from the original One-Horn build; every body part returns (armor, glow) Pieces.
"""
import random

from kit import Piece

from outfits.common import Outfit

# One function per body region. `side` is +1 for Left (+X), -1 for Right.
# The concept's corruption grows on the character's left side, so left pieces use
# the cracked "plate_corrupt" texture and carry the crystals.
def band(p, z0, z1, w, d, c, color, grow=0.0, dx=0.0, dy=0.0, rot=(0, 0, 0)):
    """A ring of armor between z0 and z1, flaring by `grow` toward the top."""
    p.shell([(z0, w, d, c, dx, dy), (z1, w + grow, d + grow, c, dx, dy)], color, rot=rot)


def crystals(g, rnd, count, base_fn, dir_fn, length, radius):
    for _ in range(count):
        g.spike(base_fn(), dir_fn(), rnd.uniform(*length), rnd.uniform(*radius), "glow",
                sides=5, twist=rnd.uniform(0, 3))


def head():
    a, g = Piece(), Piece()
    # Helmet bowl, brow band and crest.
    a.shell([(-0.5, 0.72, 0.72, 0.22), (0.15, 0.76, 0.76, 0.24), (0.52, 0.66, 0.68, 0.26),
             (0.74, 0.4, 0.42, 0.16)], "plate_dark", tip=(0, 0.02, 0.86))
    band(a, 0.1, 0.3, 0.79, 0.79, 0.25, "plate_trim")
    a.box((0.14, 1.42, 0.24), "plate_trim", pos=(0, 0, 0.66), top=(0.5, 0.9))
    # Face: visor, brow over the eye, nose ridge, breaths and pointed chin.
    a.box((1.22, 0.14, 0.52), "plate_mid", pos=(0, -0.76, -0.14), bottom=(0.78, 1))
    a.box((1.14, 0.18, 0.2), "plate_trim", pos=(0, -0.8, 0.22), rot=(-12, 0, 0), top=(0.92, 1))
    a.box((1.0, 0.06, 0.11), "black", pos=(0, -0.84, 0.07))
    a.box((0.13, 0.12, 0.58), "plate_trim", pos=(0, -0.85, -0.22), bottom=(0.45, 1))
    for x in (-0.36, -0.24, 0.24, 0.36):
        a.box((0.05, 0.05, 0.2), "black", pos=(x, -0.84, -0.2))
    a.box((0.62, 0.16, 0.3), "plate_mid", pos=(0, -0.74, -0.58), bottom=(0.15, 0.6))
    # Cheek guards and layered neck guard.
    for s in (1, -1):
        a.box((0.13, 0.78, 0.86), "plate_mid", pos=(s * 0.8, -0.1, -0.18), bottom=(1, 0.6))
        a.box((0.1, 0.3, 0.3), "plate_trim", pos=(s * 0.86, -0.15, 0.05), rot=(0, 0, 45))
    for i in range(3):
        a.box((1.36 - 0.1 * i, 0.14, 0.22), "plate_mid" if i % 2 else "plate_dark",
              pos=(0, 0.74 + 0.05 * i, -0.36 - 0.17 * i), rot=(22, 0, 0))
    # The horn: dark metal fading to purple, set in a trim collar.
    band(a, 0.66, 0.78, 0.22, 0.22, 0.07, "plate_trim", dy=-0.12)
    a.spike((0, -0.12, 0.72), (0, 0.18, 1), 1.4, 0.17, "horn", sides=6)
    # Cyclops eye and corruption creeping over the left side of the helmet.
    g.box((0.22, 0.05, 0.22), "glow", pos=(0, -0.875, 0.07), rot=(0, 45, 0))
    g.box((0.5, 0.03, 0.035), "glow", pos=(0, -0.873, 0.07))
    rnd = random.Random(1)
    crystals(g, rnd, 5, lambda: (rnd.uniform(0.6, 0.78), rnd.uniform(-0.3, 0.4), rnd.uniform(0.15, 0.6)),
             lambda: (1, rnd.uniform(-0.4, 0.4), rnd.uniform(0.3, 1.0)), (0.2, 0.45), (0.05, 0.09))
    for _ in range(3):
        g.spike((rnd.uniform(-0.12, 0.12), -0.12, 0.74), (rnd.uniform(-0.5, 0.5), rnd.uniform(-0.4, 0.4), 1),
                rnd.uniform(0.15, 0.3), 0.05, "glow", sides=5)
    return a, g


def upper_torso():
    a, g = Piece(), Piece()
    # Upper breastplate and three abdomen lames, each flaring over the one below.
    a.shell([(-0.02, 1.1, 0.64, 0.22), (0.45, 1.15, 0.69, 0.24), (0.84, 1.0, 0.6, 0.24)],
            "plate_dark")
    for i in range(3):
        z1 = -0.02 - 0.27 * i
        band(a, z1 - 0.3, z1, 1.06, 0.62, 0.2, "plate_mid" if i % 2 == 0 else "plate_dark",
             grow=0.04)
    # Pectoral plates (left one cracked), center ridge.
    for s in (1, -1):
        a.box((0.84, 0.1, 0.64), "plate_corrupt" if s > 0 else "plate_mid",
              pos=(s * 0.5, -0.71, 0.42), rot=(0, s * -8, 0), bottom=(0.9, 1))
    a.box((0.17, 0.13, 1.55), "plate_trim", pos=(0, -0.73, 0.0), top=(1, 0.6))
    # Gorget with flared collar plates.
    a.shell([(0.7, 0.68, 0.52, 0.16), (1.02, 0.6, 0.46, 0.14)], "plate_trim")
    for s in (1, -1):
        a.box((0.5, 0.95, 0.16), "plate_mid", pos=(s * 0.64, 0, 0.9), rot=(0, s * -22, 0))
    # Back: plate, spine ridge, torn cloth and crossed straps with a buckle.
    a.box((1.8, 0.1, 1.3), "plate_mid", pos=(0, 0.69, 0.12))
    a.box((0.15, 0.1, 1.45), "plate_trim", pos=(0, 0.75, 0.05))
    a.cloth([-0.75, -0.5, -0.25, 0.0, 0.25, 0.5, 0.75], 0.75,
            [-0.9, -1.35, -1.0, -1.5, -1.1, -1.4, -0.95], 0.78, "cloth_dark", sag=0.04)
    for s in (1, -1):
        a.box((0.22, 0.06, 2.0), "leather_strap", pos=(0, 0.86, 0.05), rot=(0, s * 38, 0))
    a.box((0.28, 0.06, 0.28), "buckle", pos=(0, 0.9, 0.05))
    # Glowing V with its stem, and cracks breaking out of the left chest.
    for s in (1, -1):
        g.box((0.09, 0.06, 0.74), "glow", pos=(s * 0.22, -0.8, 0.33), rot=(0, s * 38, 0))
    g.box((0.09, 0.06, 0.55), "glow", pos=(0, -0.8, -0.16))
    rnd = random.Random(4)
    crystals(g, rnd, 4, lambda: (rnd.uniform(0.75, 0.95), -0.72, rnd.uniform(0.1, 0.7)),
             lambda: (rnd.uniform(0.3, 1), -1, rnd.uniform(-0.2, 0.8)), (0.15, 0.3), (0.04, 0.07))
    return a, g


def lower_torso():
    a, g = Piece(), Piece()
    # Main belt with a big square buckle, and a second, slanted belt.
    band(a, -0.22, 0.2, 1.14, 0.66, 0.2, "leather_strap")
    a.box((0.52, 0.1, 0.44), "buckle", pos=(0, -0.7, 0))
    a.box((0.28, 0.05, 0.22), "black", pos=(0, -0.75, 0))
    a.box((0.05, 0.05, 0.22), "buckle", pos=(0.04, -0.77, 0))
    band(a, -0.36, -0.22, 1.17, 0.69, 0.21, "leather", rot=(0, 7, 0))
    a.box((0.24, 0.08, 0.2), "buckle", pos=(0.5, -0.72, -0.24), rot=(0, 7, 0))
    # Pouches.
    for s, y in ((1, -0.55), (-1, -0.55), (-1, 0.5)):
        a.box((0.34, 0.26, 0.4), "leather", pos=(s * 0.8, y, -0.22))
        a.box((0.37, 0.29, 0.13), "leather_strap", pos=(s * 0.8, y, -0.04))
    # Chainmail skirt under everything.
    a.shell([(-1.05, 1.18, 0.7, 0.22), (-0.15, 1.1, 0.64, 0.2)], "chainmail")
    # Hip tassets: two overlapping plates per side.
    for s in (1, -1):
        for i in range(2):
            a.box((0.17, 1.02 - 0.06 * i, 0.5), "plate_mid" if i == 0 else "plate_dark",
                  pos=(s * (1.16 + 0.03 * i), 0, -0.4 - 0.38 * i), rot=(0, s * 12, 0),
                  bottom=(1, 0.88))
    # Tattered tabard front and back, with ragged side strips.
    xs = [-0.58, -0.43, -0.29, -0.14, 0.0, 0.14, 0.29, 0.43, 0.58]
    a.cloth(xs, -0.15, [-1.55, -1.9, -1.62, -2.05, -1.72, -2.0, -1.6, -1.85, -1.5], -0.74,
            "cloth", sag=-0.06)
    a.cloth(xs, -0.15, [-1.75, -2.1, -1.85, -2.2, -1.9, -2.15, -1.8, -2.05, -1.7], 0.74,
            "cloth_dark", sag=0.06)
    for s in (1, -1):
        a.cloth([s * 0.66, s * 0.8, s * 0.95], -0.2, [-1.2, -1.55, -1.25], -0.72, "cloth_dark",
                sag=-0.03)
    return a, g


def upper_arm(side):
    a, g = Piece(), Piece()
    corrupt = "plate_corrupt" if side > 0 else "plate_dark"
    # Mail sleeve, rerebrace and a trim lame at the elbow.
    band(a, -0.6, 0.45, 0.55, 0.55, 0.14, "chainmail")
    band(a, -0.5, 0.3, 0.6, 0.6, 0.15, corrupt)
    band(a, -0.62, -0.46, 0.63, 0.63, 0.16, "plate_trim")
    # Big layered pauldron: dome plus four lames stepping down the outside.
    a.shell([(0.22, 0.84, 0.78, 0.24, side * 0.12, 0), (0.6, 0.78, 0.72, 0.24, side * 0.06, 0),
             (0.88, 0.44, 0.46, 0.16, 0, 0)], corrupt)
    band(a, 0.12, 0.26, 0.86, 0.8, 0.25, "plate_trim", dx=side * 0.12)
    for i in range(4):
        a.box((0.54, 1.5 - 0.1 * i, 0.32), "plate_mid" if i % 2 == 0 else "plate_dark",
              pos=(side * (0.64 + 0.05 * i), 0, 0.44 - 0.22 * i), rot=(0, side * 30, 0),
              bottom=(1, 0.9))
    # Front/back edge plates so the pauldron reads chunky from the side too.
    for y in (-1, 1):
        a.box((0.9, 0.12, 0.5), "plate_mid", pos=(side * 0.2, y * 0.82, 0.45), rot=(y * -12, 0, 0),
              bottom=(0.85, 1))
    rnd = random.Random(10 + side)
    if side > 0:
        # Left shoulder: the corruption bursts out as a large crystal cluster.
        crystals(g, rnd, 12, lambda: (rnd.uniform(0.15, 0.8), rnd.uniform(-0.45, 0.45), rnd.uniform(0.55, 0.9)),
                 lambda: (rnd.uniform(0.1, 1.0), rnd.uniform(-0.6, 0.6), rnd.uniform(0.5, 1.2)),
                 (0.45, 1.15), (0.07, 0.16))
        crystals(g, rnd, 5, lambda: (0.95, rnd.uniform(-0.5, 0.5), rnd.uniform(-0.1, 0.4)),
                 lambda: (1, rnd.uniform(-0.5, 0.5), rnd.uniform(-0.2, 0.6)), (0.25, 0.5), (0.05, 0.1))
    else:
        # Right shoulder: clean steel with a raised, pointed gardbrace.
        a.box((0.16, 1.25, 0.55), "plate_trim", pos=(side * 0.32, 0, 1.0), rot=(0, side * 15, 0),
              top=(1, 0.3))
        for y in (-0.38, 0.0, 0.38):
            a.spike((side * 0.55, y, 0.82), (side * 0.5, 0, 1), 0.4, 0.09, "plate_trim", sides=4)
    return a, g


def lower_arm(side):
    a, g = Piece(), Piece()
    corrupt = "plate_corrupt" if side > 0 else "plate_dark"
    a.shell([(-0.53, 0.56, 0.56, 0.14), (0.5, 0.61, 0.61, 0.15)], corrupt)
    a.box((0.64, 0.12, 0.82), "plate_mid", pos=(0, -0.62, 0.0), bottom=(0.7, 1))
    a.box((0.12, 0.74, 0.82), "plate_mid", pos=(side * 0.62, 0, 0.0), bottom=(1, 0.75))
    band(a, -0.56, -0.42, 0.65, 0.65, 0.16, "plate_trim")
    band(a, -0.02, 0.1, 0.63, 0.63, 0.16, "leather_strap")
    # Couter: elbow plate with a backward spike.
    a.box((0.72, 0.22, 0.46), "plate_trim", pos=(0, 0.63, 0.42), top=(0.8, 1))
    a.spike((0, 0.7, 0.42), (0, 1, 0.2), 0.4, 0.22, "plate_trim", sides=4)
    if side > 0:
        rnd = random.Random(21)
        crystals(g, rnd, 8, lambda: (rnd.uniform(0.55, 0.7), rnd.uniform(-0.45, 0.45), rnd.uniform(-0.45, 0.45)),
                 lambda: (1, rnd.uniform(-0.6, 0.6), rnd.uniform(-0.2, 0.9)), (0.25, 0.6), (0.05, 0.11))
        crystals(g, rnd, 3, lambda: (rnd.uniform(-0.2, 0.3), 0.62, rnd.uniform(-0.3, 0.3)),
                 lambda: (rnd.uniform(-0.2, 0.6), 1, rnd.uniform(0, 0.8)), (0.2, 0.4), (0.05, 0.08))
    return a, g


def hand(side):
    a, g = Piece(), Piece()
    band(a, -0.22, 0.06, 0.54, 0.54, 0.14, "plate_dark")
    a.shell([(0.04, 0.64, 0.64, 0.16), (0.3, 0.71, 0.71, 0.18)], "plate_trim")
    # Knuckle plates and a thumb plate.
    for x in (-0.3, -0.1, 0.1, 0.3):
        a.box((0.17, 0.1, 0.15), "plate_mid", pos=(x, -0.57, -0.1), top=(0.8, 1))
    a.box((0.12, 0.3, 0.26), "plate_mid", pos=(-side * 0.58, -0.25, -0.05))
    if side > 0:
        rnd = random.Random(31)
        crystals(g, rnd, 3, lambda: (0.56, rnd.uniform(-0.3, 0.3), rnd.uniform(-0.1, 0.2)),
                 lambda: (1, rnd.uniform(-0.4, 0.4), rnd.uniform(0, 0.8)), (0.2, 0.35), (0.05, 0.07))
    return a, g


def upper_leg(side):
    a, g = Piece(), Piece()
    a.shell([(-0.55, 0.57, 0.57, 0.15), (0.6, 0.6, 0.6, 0.15)], "plate_dark")
    for i in range(3):
        a.box((0.8, 0.11, 0.3), "plate_mid" if i % 2 == 0 else "plate_dark",
              pos=(0, -0.65, 0.42 - 0.33 * i), rot=(8, 0, 0), bottom=(0.94, 1))
    a.box((0.12, 0.8, 0.9), "plate_mid", pos=(side * 0.62, 0, 0.05), bottom=(1, 0.8))
    for z in (0.22, -0.32):
        band(a, z - 0.06, z + 0.06, 0.63, 0.63, 0.16, "leather_strap")
    return a, g


def lower_leg(side):
    a, g = Piece(), Piece()
    a.shell([(-0.6, 0.56, 0.56, 0.15), (0.48, 0.6, 0.6, 0.15)], "plate_dark")
    band(a, 0.44, 0.6, 0.62, 0.62, 0.16, "plate_trim")
    a.box((0.17, 0.12, 0.95), "plate_trim", pos=(0, -0.62, -0.14), bottom=(0.6, 1))
    band(a, 0.0, 0.1, 0.62, 0.62, 0.16, "leather_strap")
    # Poleyn: knee cop with side wings and a forward point.
    a.box((0.7, 0.22, 0.46), "plate_mid", pos=(0, -0.64, 0.52), top=(0.8, 1), bottom=(0.8, 1))
    for s in (1, -1):
        a.box((0.12, 0.42, 0.44), "plate_trim", pos=(s * 0.42, -0.5, 0.52), rot=(0, s * 20, 0))
    a.spike((0, -0.74, 0.52), (0, -1, 0.1), 0.36, 0.2, "plate_trim", sides=4)
    return a, g


def foot(side):
    a, g = Piece(), Piece()
    a.shell([(-0.2, 0.58, 0.68, 0.14, 0, -0.14), (0.2, 0.56, 0.6, 0.14, 0, -0.04)], "plate_dark")
    band(a, 0.12, 0.28, 0.62, 0.62, 0.16, "plate_trim")
    for i in range(3):
        a.box((1.12 - 0.08 * i, 0.3, 0.13), "plate_mid" if i % 2 == 0 else "plate_dark",
              pos=(0, -0.5 - 0.2 * i, 0.16 - 0.11 * i), rot=(16, 0, 0))
    a.spike((0, -0.88, -0.1), (0, -1, 0.15), 0.3, 0.2, "plate_mid", sides=4)
    a.box((1.12, 1.5, 0.08), "leather_strap", pos=(0, -0.16, -0.21))
    return a, g




def elite_onehorn():
    o = Outfit("EliteOneHorn", corruption=0.5, seed=31)
    builders = {"Head": head, "UpperTorso": upper_torso, "LowerTorso": lower_torso}
    for prefix, side in (("Left", 1), ("Right", -1)):
        builders[prefix + "UpperArm"] = lambda s=side: upper_arm(s)
        builders[prefix + "LowerArm"] = lambda s=side: lower_arm(s)
        builders[prefix + "Hand"] = lambda s=side: hand(s)
        builders[prefix + "UpperLeg"] = lambda s=side: upper_leg(s)
        builders[prefix + "LowerLeg"] = lambda s=side: lower_leg(s)
        builders[prefix + "Foot"] = lambda s=side: foot(s)
    for part, fn in builders.items():
        armor, glow = fn()
        o.pieces[part] = {"Armor": armor, "Glow": glow}
    return o

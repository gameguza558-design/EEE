"""Boss: the One-Horn Cyclops King. Fully corrupted, no armor: a bare, cracked,
muscular upper body, a wild spiky mane, one huge eye and one horn, a gold circlet
of crystals, torn pants and heavy boots. Glow is pink-magenta instead of purple.
"""
import math

from kit import band, blob, circle

from outfits.common import Outfit, skin_limbs

SKIN = "skin_king"
PINK = (255, 70, 190)


def head(o):
    a, rnd = o("Head"), o.rnd
    a.shell([(-0.64, 0.66, 0.66, 0.22), (0.2, 0.7, 0.7, 0.24), (0.58, 0.56, 0.58, 0.22)], SKIN,
            tip=(0, 0.05, 0.72))
    # A wide, slit-like eye under a heavy, angry brow.
    a.loft([(0.64, circle(0.27, 14, 1.8, 0.75)), (0.72, circle(0.26, 14, 1.8, 0.72))], "eye",
           pos=(0, 0, 0.12), rot=(90, 0, 0))
    for s in (1, -1):
        a.box((0.72, 0.24, 0.2), SKIN, pos=(s * 0.33, -0.72, 0.34), rot=(0, s * 14, 0), top=(1, 0.6))
        a.box((0.34, 0.18, 0.2), SKIN, pos=(s * 0.42, -0.68, -0.12))  # cheekbones
    a.box((0.9, 0.12, 0.08), SKIN, pos=(0, -0.72, -0.06))
    a.box((0.9, 0.26, 0.42), SKIN, pos=(0, -0.58, -0.5), bottom=(0.7, 0.8))  # jaw
    a.box((0.4, 0.04, 0.04), "black", pos=(0, -0.72, -0.42))
    # Gold circlet set with crystals, and the horn rising from the forehead.
    band(a, 0.38, 0.5, 0.73, 0.73, 0.24, "gold")
    a.spike((0, -0.4, 0.5), (0, 0.15, 1), 1.7, 0.22, "horn", sides=6)
    g = o("Head", "Glow")
    for i in range(7):
        ang = math.pi * (0.15 + 0.7 * i / 6)
        x, y = 0.74 * math.cos(ang), -0.74 * math.sin(ang)
        g.spike((x, y, 0.5), (x * 0.4, y * 0.4, 1), 0.3 + 0.15 * (i % 2), 0.06, "glow", sides=5)
    # Mane: long spikes sweeping up and back, with bangs falling over the brow.
    for i in range(46):
        u = rnd.random()
        ang = rnd.uniform(-math.pi * 0.95, math.pi * 0.95) + math.pi / 2  # mostly not the face
        r = rnd.uniform(0.35, 0.65)
        base = (r * math.cos(ang), r * math.sin(ang) * 0.9 + 0.1, rnd.uniform(0.25, 0.7))
        d = (base[0] * 1.6 + rnd.uniform(-0.3, 0.3), base[1] * 1.4 + 0.6, 0.7 + u)
        a.spike(base, d, rnd.uniform(0.9, 2.3), rnd.uniform(0.13, 0.24), "hair", sides=4,
                twist=rnd.uniform(0, 3))
    for i in range(9):
        x = -0.6 + 1.2 * i / 8
        a.spike((x, -0.45, 0.62), (x * 0.8, -0.9, -0.6), rnd.uniform(0.45, 0.9), 0.1, "hair", sides=4)


def torso(o):
    t, rnd = o("UpperTorso"), o.rnd
    t.shell([(-0.82, 1.06, 0.56, 0.22), (0.3, 1.18, 0.62, 0.24), (0.84, 1.05, 0.55, 0.24)], SKIN)
    for s in (1, -1):
        blob(t, (s * 0.5, -0.56, 0.36), (0.6, 0.34, 0.44), SKIN)  # pecs
        blob(t, (s * 0.48, 0.12, 0.84), (0.46, 0.42, 0.26), SKIN)  # traps
        blob(t, (s * 1.0, 0.1, 0.15), (0.24, 0.45, 0.6), SKIN)  # lats
        blob(t, (s * 0.46, 0.5, 0.3), (0.52, 0.22, 0.48), SKIN)  # back
        t.box((0.22, 0.12, 0.7), SKIN, pos=(s * 0.66, -0.52, -0.42), rot=(0, s * 12, 0))  # obliques
    for x in (-0.23, 0.23):
        for z in (-0.04, -0.32, -0.6):
            blob(t, (x * 1.05, -0.6, z), (0.25, 0.17, 0.15), SKIN, sides=6, rings=3)
    # Mane spilling down the back.
    for i in range(14):
        x = -0.7 + 1.4 * i / 13
        t.spike((x, 0.55, 0.85), (x * 0.4, 0.5, -1), rnd.uniform(0.9, 1.9), rnd.uniform(0.14, 0.22),
                "hair", sides=4, twist=rnd.uniform(0, 3))
    # Crystals tearing out of the shoulder blades, spine and left chest.
    o.crystals("UpperTorso", 10, (0.0, 0.62, 0.35), (0.7, 0.05, 0.35), (0, 1, 0.8),
               length=(0.5, 1.3), radius=(0.08, 0.17))
    o.crystals("UpperTorso", 5, (0.6, -0.68, 0.3), (0.25, 0.03, 0.3), (0.4, -1, 0.4),
               length=(0.15, 0.35), radius=(0.04, 0.07))


def arms(o):
    skin_limbs(o, SKIN, muscle=1.32)
    for s, pre in ((1, "Left"), (-1, "Right")):
        ua, la, h = o(pre + "UpperArm"), o(pre + "LowerArm"), o(pre + "Hand")
        band(ua, -0.25, -0.1, 0.66, 0.66, 0.12, "gold")
        band(la, -0.55, -0.15, 0.64, 0.64, 0.12, "cloth_dark", grow=0.02)
        for z in (-0.5, -0.32):
            band(la, z - 0.03, z + 0.03, 0.67, 0.67, 0.12, "leather_strap")
        o.crystals(pre + "UpperArm", 8 if s > 0 else 4, (s * 0.45, 0, 0.55), (0.2, 0.35, 0.15),
                   (s * 0.8, 0, 1), length=(0.4, 1.2 if s > 0 else 0.7), radius=(0.07, 0.16))
        if s > 0:
            # Crystal blades along the left forearm, and on the knuckles.
            for i in range(4):
                o("LeftLowerArm", "Glow").spike((0.62, 0.1, 0.35 - 0.25 * i), (1, 0.6, 0.5 - 0.1 * i),
                                                0.55 - 0.08 * i, 0.08, "glow", sides=4)
            o.crystals("LeftHand", 4, (0.0, -0.6, -0.05), (0.35, 0.02, 0.05), (0, -1, 0.2),
                       length=(0.15, 0.3), radius=(0.04, 0.06))
        else:
            band(la, 0.05, 0.4, 0.66, 0.66, 0.14, "gold")


def legs(o):
    lt, rnd = o("LowerTorso"), o.rnd
    band(lt, -0.22, 0.22, 1.1, 0.62, 0.2, "pants")
    band(lt, -0.05, 0.22, 1.15, 0.67, 0.2, "leather_strap")
    lt.box((0.6, 0.12, 0.42), "gold", pos=(0, -0.72, 0.08))
    lt.spike((0, -0.76, 0.08), (0, -1, 0), 0.22, 0.14, "gold", sides=4)
    # Torn sash on the left hip and a ragged front cloth.
    lt.cloth([0.45, 0.7, 0.95, 1.15], 0.0, [-1.4, -1.9, -1.6, -1.2], -0.7, "cloth_dark", sag=-0.04)
    lt.cloth([-0.45, -0.2, 0.05, 0.3], -0.15, [-1.1, -1.35, -1.15, -1.0], -0.72, "cloth_dark", sag=-0.04)
    for s, pre in ((1, "Left"), (-1, "Right")):
        ul, ll, f = o(pre + "UpperLeg"), o(pre + "LowerLeg"), o(pre + "Foot")
        ul.shell([(-0.62, 0.6, 0.6, 0.16), (0.0, 0.66, 0.66, 0.18), (0.62, 0.62, 0.62, 0.16)], "pants")
        ul.cloth([-0.5, -0.25, 0.0, 0.25, 0.5], -0.45, [-0.75, -0.95, -0.7, -1.0, -0.8], -0.67,
                 "pants", sag=-0.03)
        # Tall boots: leather with iron plates, straps and a fur cuff.
        ll.shell([(-0.6, 0.6, 0.6, 0.16), (0.3, 0.63, 0.63, 0.16), (0.62, 0.68, 0.68, 0.2)],
                 "leather_strap")
        band(ll, 0.5, 0.68, 0.74, 0.74, 0.24, "fur_dark")
        ll.box((0.6, 0.12, 0.85), "iron", pos=(0, -0.66, -0.05), top=(0.85, 1))
        ll.spike((0, -0.72, 0.38), (0, -1, 0.3), 0.3, 0.14, "iron", sides=4)
        for z in (-0.35, -0.05, 0.25):
            band(ll, z - 0.04, z + 0.04, 0.66, 0.66, 0.17, "leather")
        f.shell([(-0.2, 0.62, 0.72, 0.16, 0, -0.14), (0.24, 0.6, 0.64, 0.16, 0, -0.04)],
                "leather_strap")
        f.box((1.2, 1.55, 0.1), "black", pos=(0, -0.14, -0.21))
        f.box((1.0, 0.4, 0.3), "iron", pos=(0, -0.72, -0.02), top=(0.8, 0.7))
        for x in (-0.3, 0.0, 0.3):
            f.spike((x, -0.9, 0.0), (0, -1, 0.2), 0.22, 0.07, "iron", sides=4)
        if s < 0:
            o.crystals(pre + "UpperLeg", 3, (-0.62, 0, 0.1), (0.03, 0.3, 0.3), (-1, 0, 0.3),
                       length=(0.2, 0.4), radius=(0.04, 0.07))


def cyclops_king():
    o = Outfit("CyclopsKing", glow=PINK, corruption=1.0, seed=41)
    head(o)
    torso(o)
    arms(o)
    legs(o)
    return o

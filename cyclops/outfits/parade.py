"""Parade armour for the luxury knights (White, Black, Royal Guard, Paladin).

Unlike the One-Horn's chunky boxes, these suits are built from rounded, smooth-shaded
plates (superellipse sections) with gold edge piping, sculpted chest plates, big knee
cops, layered pauldrons and full flowing capes. One style dict per knight picks the
materials and the helm / chest / pauldron variants.
"""
import math
import random

from mathutils import Vector

from kit import blob
from outfits.common import Outfit

# ---------------------------------------------------------------------------
# Rounded geometry helpers (part-local coordinates; front = -Y, left = +X).


def ring(hw, hd, p=2.6, n=20, keel=0.0, dx=0.0, dy=0.0):
    """Superellipse section (p = 2 ellipse ... large p = box). keel pushes the front
    centre forward into a ridge."""
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        c, s = math.cos(a), math.sin(a)
        x = hw * math.copysign(abs(s) ** (2 / p), s)
        y = -hd * math.copysign(abs(c) ** (2 / p), c)
        if keel:
            y -= keel * max(0.0, c) ** 6
        pts.append((x + dx, y + dy))
    return pts


def rshell(piece, rings, color, tip=None, base=None, pos=(0, 0, 0), rot=(0, 0, 0), p=2.6, n=20):
    """Rounded shell. rings: (z, half_w, half_d[, {p, keel, dx, dy}])."""
    lofted = []
    for r in rings:
        z, hw, hd = r[:3]
        o = r[3] if len(r) > 3 else {}
        lofted.append((z, ring(hw, hd, o.get("p", p), n, o.get("keel", 0.0), o.get("dx", 0.0), o.get("dy", 0.0))))
    piece.loft(lofted, color, pos=pos, rot=rot, tip=tip, base=base, smooth=True)


def trim(piece, z, hw, hd, color, h=0.07, **o):
    """Thin edge band (gold piping round a plate)."""
    rshell(piece, [(z - h / 2, hw, hd, o), (z + h / 2, hw, hd, o)], color)


def _rot_to(direction, roll=0.0):
    d = Vector(direction).normalized()
    q = d.to_track_quat("Z", "Y")
    e = q.to_euler()
    m = q.to_matrix()
    if roll:
        from mathutils import Matrix
        m = m @ Matrix.Rotation(math.radians(roll), 3, "Z")
        e = m.to_euler()
    return tuple(math.degrees(a) for a in e)


def lens(piece, center, direction, rx, ry, depth, color, p=2.4, n=16):
    """A domed plate (pec, knee cop, boss) bulging out along `direction`."""
    rshell(piece, [(0.0, rx, ry), (depth * 0.55, rx * 0.86, ry * 0.86), (depth * 0.85, rx * 0.5, ry * 0.5)],
           color, tip=(0, 0, depth), pos=center, rot=_rot_to(direction), p=p, n=n)


def fin(piece, base, direction, length, width, thick, color, roll=0.0):
    """A flat, blade-like fin (helm crests, pauldron blades)."""
    prof = lambda w, t: [(w, 0), (0, t), (-w, 0), (0, -t)]  # noqa: E731
    piece.loft([(0.0, prof(width, thick)), (length * 0.55, prof(width * 0.75, thick * 0.8))], color,
               pos=base, rot=_rot_to(direction, roll), tip=(0, 0, length))


def pipe(piece, pts, color, w=0.05, t=0.035):
    """Gold piping along a polyline of 3D points."""
    for a, b in zip(pts, pts[1:]):
        a, b = Vector(a), Vector(b)
        d = b - a
        piece.box((w, t, d.length + w * 0.6), color, pos=tuple((a + b) / 2), rot=_rot_to(d))


def curved_plate(piece, center, radius, a0, a1, z0, z1, color, thick=0.05, flare=0.0, n=8):
    """A plate curved round a vertical axis (tassets, greave fronts). Angles in degrees,
    0 = front (-Y), 90 = +X."""
    cx, cy = center

    def arc(r):
        return [(cx + r * math.sin(math.radians(a0 + (a1 - a0) * i / (n - 1))),
                 cy - r * math.cos(math.radians(a0 + (a1 - a0) * i / (n - 1)))) for i in range(n)]
    top = arc(radius) + list(reversed(arc(radius - thick)))
    bot = arc(radius + flare) + list(reversed(arc(radius + flare - thick)))
    piece.loft([(z0, bot), (z1, top)], color, smooth=True)


# ---------------------------------------------------------------------------
STYLES = {
    # plate: main plate, plate2: secondary lames, trim: piping, knee: knee cops
    "white": dict(plate="plate_white", plate2="blade", trim="gold", trim2="gold_engraved", knee="plate_white",
                  cape="cloth_royal", lining="cloth_white", tabard="cloth_white", helm="winged",
                  chest="emblem", gem="gem_blue", pauldron="round", crystals=3, spikes=False),
    "black": dict(plate="plate_black", plate2="plate_black", trim="gold", trim2="gold", knee="gold",
                  cape="cloth_royal", lining="cloth_dark", tabard=None, helm="dark", chest="muscle",
                  gem="gem", pauldron="bladed", crystals=3, spikes=True),
    "guard": dict(plate="blade", plate2="plate_white", trim="gold", trim2="gold_engraved", knee="blade",
                  cape="cloth_royal", lining="cloth_white", tabard="cloth_royal", helm="plume", chest="cross",
                  gem="gem", pauldron="round", crystals=4, spikes=False),
    "paladin": dict(plate="plate_white", plate2="plate_corrupt_heavy", trim="gold_engraved", trim2="gold",
                    knee="plate_white", cape="cloth_white", lining="cloth_royal", tabard="cloth_white",
                    helm="halo", chest="eye", gem="gem", pauldron="round", crystals=8, spikes=False),
}


def parade_knight(name, style, glow=(176, 70, 255), seed=40):
    S = STYLES[style]
    o = Outfit(name, glow=glow, corruption=0.4, seed=seed)
    helm(o, S)
    torso(o, S)
    cape(o, S)
    hips(o, S)
    for part, side in (("Left", 1), ("Right", -1)):
        arm(o, part, side, S)
        leg(o, part, side, S)
    crystals(o, S, random.Random(seed))
    return o


# ---------------------------------------------------------------------------
def helm(o, S):
    h, g = o("Head"), o("Head", "Glow")
    P, T = S["plate"], S["trim"]
    rshell(h, [(-0.66, 0.7, 0.72, {"keel": 0.1}), (-0.2, 0.74, 0.76, {"keel": 0.14}), (0.25, 0.75, 0.76, {"keel": 0.1}),
               (0.58, 0.64, 0.66), (0.76, 0.4, 0.42)], P, tip=(0, 0, 0.86))
    trim(h, -0.64, 0.72, 0.75, T, keel=0.1)
    trim(h, 0.3, 0.765, 0.775, T, h=0.06, keel=0.1)
    # Visor: a pointed brow over a glowing eye slit, and a beaked faceplate below.
    h.box((1.2, 0.2, 0.17), P, pos=(0, -0.8, 0.24), rot=(-14, 0, 0), top=(0.9, 1))
    pipe(h, [(-0.6, -0.9, 0.18), (0, -0.95, 0.14), (0.6, -0.9, 0.18)], T)
    h.box((1.0, 0.06, 0.11), "black", pos=(0, -0.86, 0.06))
    g.box((0.82, 0.03, 0.04), "glow", pos=(0, -0.885, 0.06))
    g.box((0.18, 0.04, 0.18), "glow", pos=(0, -0.885, 0.06), rot=(0, 45, 0))
    rshell(h, [(-0.62, 0.5, 0.12, {"dy": -0.74}), (-0.05, 0.58, 0.14, {"dy": -0.76})], P, p=2.2)  # faceplate
    pipe(h, [(0, -0.92, -0.05), (0, -0.92, -0.6)], T)
    for x in (-0.3, -0.18, 0.18, 0.3):  # breaths
        h.box((0.04, 0.05, 0.22), "black", pos=(x, -0.88, -0.3))
    pipe(h, [(0, -0.82, 0.36), (0, -0.6, 0.68), (0, 0.0, 0.88), (0, 0.6, 0.66)], T, w=0.09, t=0.06)  # crest line
    kind = S["helm"]
    if kind == "winged":
        for s in (1, -1):
            for k in range(5):  # silver feathers with gold quills
                d = (s * (0.55 - 0.08 * k), 0.35 + 0.15 * k, 0.75 + 0.12 * k)
                fin(h, (s * 0.72, 0.05 + 0.1 * k, 0.32 + 0.05 * k), d, 1.25 - 0.13 * k, 0.15, 0.035, "plate_white",
                    roll=90)
                fin(h, (s * 0.74, 0.05 + 0.1 * k, 0.32 + 0.05 * k), d, 0.9 - 0.1 * k, 0.04, 0.05, T, roll=90)
        lens(h, (0, -0.86, 0.42), (0, -1, 0.2), 0.11, 0.11, 0.1, "gem")
    elif kind == "dark":
        for s in (1, -1):
            for k in range(3):  # blade fins swept back from the temples
                fin(h, (s * 0.62, -0.05 + 0.22 * k, 0.5 - 0.1 * k), (s * 0.35, 1, 0.5 - 0.12 * k),
                    1.6 - 0.3 * k, 0.17, 0.04, P, roll=90)
                fin(h, (s * 0.66, -0.05 + 0.22 * k, 0.52 - 0.1 * k), (s * 0.35, 1, 0.5 - 0.12 * k),
                    1.1 - 0.2 * k, 0.04, 0.05, T, roll=90)
        fin(h, (0, -0.3, 0.8), (0, 0.6, 1), 0.9, 0.05, 0.16, P)  # centre crest blade
    elif kind == "halo":
        h.spike((0, -0.15, 0.75), (0, 0.15, 1), 1.3, 0.16, "horn", sides=6)
        for k in range(20):  # gold halo
            a = 2 * math.pi * k / 20
            h.box((0.12, 0.08, 0.36), T, pos=(1.15 * math.cos(a), 1.0, 0.4 + 1.15 * math.sin(a)),
                  rot=(0, -math.degrees(a) + 90, 0))
        for k in range(10):
            a = 2 * math.pi * (k + 0.5) / 10
            g.spike((1.22 * math.cos(a), 1.0, 0.4 + 1.22 * math.sin(a)), (math.cos(a), 0, math.sin(a)),
                    0.5 if k % 2 else 0.32, 0.06, "glow", sides=4)
    # Neck guard.
    for i in range(3):
        rshell(h, [(-0.75 - 0.12 * i, 0.7 - 0.04 * i, 0.12, {"dy": 0.72 + 0.04 * i}),
                   (-0.6 - 0.12 * i, 0.74 - 0.04 * i, 0.12, {"dy": 0.7 + 0.04 * i})], S["plate2"] if i % 2 else P)


def torso(o, S):
    t, g = o("UpperTorso"), o("UpperTorso", "Glow")
    P, P2, T = S["plate"], S["plate2"], S["trim"]
    # Breastplate with a central keel.
    rshell(t, [(-0.8, 1.04, 0.6, {"keel": 0.04}), (-0.2, 1.08, 0.63, {"keel": 0.08}),
               (0.35, 1.14, 0.67, {"keel": 0.12}), (0.74, 1.02, 0.6, {"keel": 0.06}), (0.86, 0.7, 0.5)], P)
    trim(t, -0.78, 1.06, 0.62, T, keel=0.04)
    rshell(t, [(0.72, 0.66, 0.5), (0.98, 0.56, 0.44)], P2)  # gorget
    trim(t, 0.97, 0.58, 0.46, T)
    chest = S["chest"]
    if chest == "muscle":
        # Muscle cuirass: sculpted pecs and abs, each plate edged in gold.
        for s in (1, -1):
            lens(t, (s * 0.44, -0.66, 0.42), (s * 0.15, -1, 0.05), 0.48, 0.3, 0.06, T)
            lens(t, (s * 0.44, -0.68, 0.42), (s * 0.15, -1, 0.05), 0.44, 0.27, 0.1, P)
            for k in range(3):
                z = 0.0 - 0.27 * k
                lens(t, (s * 0.2, -0.64, z), (s * 0.05, -1, 0), 0.18, 0.11, 0.05, T)
                lens(t, (s * 0.2, -0.66, z), (s * 0.05, -1, 0), 0.16, 0.095, 0.08, P)
        # Sweeping gold lines from the shoulders down the sides.
        for s in (1, -1):
            pipe(t, [(s * 0.95, -0.55, 0.75), (s * 0.85, -0.66, 0.2), (s * 0.55, -0.66, -0.3), (s * 0.35, -0.64, -0.78)], T)
        g.box((0.16, 0.04, 0.16), "glow", pos=(0, -0.74, 0.62), rot=(0, 45, 0))
    else:
        # Smooth plackart with a big central emblem.
        lens(t, (0, -0.66, -0.3), (0, -1, 0.1), 0.7, 0.45, 0.06, T)
        lens(t, (0, -0.68, -0.3), (0, -1, 0.1), 0.66, 0.42, 0.1, P2 if P2 != "plate_corrupt_heavy" else P)
        for s in (1, -1):
            pipe(t, [(s * 0.98, -0.55, 0.7), (s * 0.55, -0.73, 0.55), (s * 0.15, -0.8, 0.5)], T)
        if chest == "emblem":
            lens(t, (0, -0.76, 0.42), (0, -1, 0), 0.3, 0.3, 0.06, S["trim2"], n=12)
            lens(t, (0, -0.8, 0.42), (0, -1, 0), 0.19, 0.19, 0.1, S["gem"], n=12)
            for k in range(8):
                a = 2 * math.pi * k / 8
                fin(t, (0.26 * math.cos(a), -0.78, 0.42 + 0.26 * math.sin(a)), (math.cos(a), -0.3, math.sin(a)),
                    0.25, 0.06, 0.02, T, roll=90)
        elif chest == "cross":
            t.box((0.16, 0.08, 1.0), S["trim2"], pos=(0, -0.8, 0.3))
            t.box((0.8, 0.08, 0.16), S["trim2"], pos=(0, -0.8, 0.45))
            lens(t, (0, -0.84, 0.45), (0, -1, 0), 0.12, 0.12, 0.08, "gem", n=8)
        elif chest == "eye":
            for k in range(14):
                a = 2 * math.pi * k / 14
                t.box((0.07, 0.06, 0.15), T, pos=(0.34 * math.cos(a), -0.8, 0.42 + 0.24 * math.sin(a)),
                      rot=(0, -math.degrees(a) + 90, 0))
            g.box((0.48, 0.05, 0.11), "glow", pos=(0, -0.82, 0.42))
            g.box((0.2, 0.06, 0.2), "glow", pos=(0, -0.83, 0.42), rot=(0, 45, 0))
    # Back plate ridge.
    pipe(t, [(0, 0.72, 0.75), (0, 0.7, -0.75)], T, w=0.08)


def cape(o, S):
    """A full cape: lofted from curved sections, hugging the shoulders and flaring wide
    behind the legs, with soft folds, a lining and a gold hem."""
    t = o("UpperTorso")
    rings = [(0.94, 1.1, 0.15, 0.55, 80), (0.3, 1.35, 0.4, 0.45, 80), (-0.4, 2.15, 0.6, 0.38, 78),
             (-2.0, 2.3, 0.72, 0.4, 74), (-3.72, 2.5, 0.88, 0.45, 70)]
    n = 22

    def arc(rx, y0, ry, span, z, inset):
        pts = []
        for i in range(n):
            a = math.radians(-span + 2 * span * i / (n - 1))
            fold = 0.0 if z > 0.5 else 0.1 * math.sin(a * 7) * min(1.0, (0.5 - z) / 2.5)
            pts.append((rx * math.sin(a) * (1 - inset * 0.3), y0 + (ry + fold) * math.cos(a) - inset))
        return pts

    def sheet(color, inset, thick):
        lofted = [(z, arc(rx, y0, ry, span, z, inset) + list(reversed(arc(rx, y0, ry, span, z, inset + thick))))
                  for z, rx, y0, ry, span in rings]
        t.loft(lofted, color, smooth=True)

    sheet(S["cape"], 0.0, 0.04)
    sheet(S["lining"], 0.05, 0.02)
    z, rx, y0, ry, span = rings[-1]
    hem = [(z, arc(rx, y0, ry, span, z, -0.01) + list(reversed(arc(rx, y0, ry, span, z, 0.07)))),
           (z + 0.14, arc(rx * 0.995, y0 - 0.005, ry, span, z + 0.14, -0.01)
            + list(reversed(arc(rx * 0.995, y0 - 0.005, ry, span, z + 0.14, 0.07))))]
    t.loft(hem, S["trim"])
    for s in (1, -1):  # shoulder clasps
        blob(t, (s * 0.82, 0.3, 0.88), (0.19, 0.16, 0.19), S["trim2"], sides=10, rings=5)
        lens(t, (s * 0.82, 0.12, 0.9), (0, -1, 0.4), 0.09, 0.09, 0.09, S["gem"], n=8)


def hips(o, S):
    lt = o("LowerTorso")
    P, P2, T = S["plate"], S["plate2"], S["trim"]
    rshell(lt, [(-0.12, 1.08, 0.64), (0.22, 1.06, 0.62)], S["trim2"])  # belt
    lens(lt, (0, -0.64, 0.05), (0, -1, 0), 0.2, 0.15, 0.08, S["gem"], n=10)
    rshell(lt, [(-0.42, 1.14, 0.69), (-0.12, 1.1, 0.66)], P2 if P2 != "plate_corrupt_heavy" else P)  # fauld
    trim(lt, -0.42, 1.15, 0.7, T)
    for s in (1, -1):
        # Front and side tassets over the thighs, gold-edged.
        for (a0, a1), col in (((-60, 40), P), ((50, 120), P2)):
            if s < 0:
                a0, a1 = -a1, -a0
            # Gold underlay just behind and slightly larger, so only a rim of it shows.
            curved_plate(lt, (s * 0.5, 0.0), 0.72, a0 - 4, a1 + 4, -1.47, -0.35, T, thick=0.04, flare=0.14)
            curved_plate(lt, (s * 0.5, 0.0), 0.76, a0, a1, -1.4, -0.35, col, thick=0.05, flare=0.14)
    if S["tabard"]:
        xs = [-0.42, -0.28, -0.14, 0.0, 0.14, 0.28, 0.42]
        bottoms = [-2.5 - 0.35 * (1 - abs(x) / 0.42) for x in xs]
        for y in (-0.82, 0.8):
            lt.cloth(xs, -0.2, bottoms, y, S["tabard"], sag=0.04 if y > 0 else -0.04)
            lt.cloth(xs, -0.2, [b - 0.1 for b in bottoms], y * 0.99, T, thick=0.03)  # gold hem peeking below


def arm(o, part, side, S):
    P, P2, T = S["plate"], S["plate2"], S["trim"]
    ua, la, hand = o(part + "UpperArm"), o(part + "LowerArm"), o(part + "Hand")
    # Pauldron: a big rounded dome over three flaring lames, every edge piped in gold.
    rshell(ua, [(0.18, 0.86, 0.8, {"dx": side * 0.14}), (0.6, 0.8, 0.74, {"dx": side * 0.08}),
                (0.92, 0.46, 0.48)], P, tip=(side * 0.02, 0, 1.02))
    trim(ua, 0.2, 0.88, 0.82, T, dx=side * 0.14)
    for i in range(3):
        z = 0.12 - 0.2 * i
        rshell(ua, [(z - 0.2, 0.9 + 0.05 * i, 0.82 + 0.03 * i, {"dx": side * (0.2 + 0.05 * i)}),
                    (z, 0.86 + 0.05 * i, 0.8 + 0.03 * i, {"dx": side * (0.16 + 0.05 * i)})], P2 if i % 2 else P)
        trim(ua, z - 0.2, 0.92 + 0.05 * i, 0.84 + 0.03 * i, T, h=0.05, dx=side * (0.2 + 0.05 * i))
    if S["pauldron"] == "bladed":
        for k in range(3):
            fin(ua, (side * (0.35 + 0.18 * k), -0.35 + 0.35 * k, 0.88 - 0.08 * k), (side * 0.55, 0.3, 1),
                0.9 - 0.15 * k, 0.16, 0.04, P, roll=90)
            fin(ua, (side * (0.37 + 0.18 * k), -0.35 + 0.35 * k, 0.9 - 0.08 * k), (side * 0.55, 0.3, 1),
                0.6 - 0.1 * k, 0.04, 0.05, T, roll=90)
    else:
        pipe(ua, [(side * 0.3, -0.75, 0.75), (side * 0.85, 0.0, 0.85), (side * 0.3, 0.75, 0.75)], S["trim2"], w=0.1)
    rshell(ua, [(-0.6, 0.55, 0.55), (0.1, 0.57, 0.57)], P2 if P2 != "plate_corrupt_heavy" or side > 0 else P)
    # Couter, vambrace and a flared gauntlet cuff.
    lens(la, (0, 0.55, 0.42), (0, 1, 0.1), 0.34, 0.3, 0.16, P)
    lens(la, (side * 0.56, 0.0, 0.42), (side, 0, 0), 0.3, 0.26, 0.12, T)
    rshell(la, [(-0.4, 0.58, 0.58), (0.38, 0.6, 0.6)], P)
    trim(la, 0.36, 0.62, 0.62, T)
    rshell(la, [(-0.53, 0.72, 0.72), (-0.3, 0.6, 0.6)], P2 if P2 != "plate_corrupt_heavy" else P)
    trim(la, -0.53, 0.73, 0.73, T)
    rshell(hand, [(-0.16, 0.55, 0.55), (0.12, 0.58, 0.58)], P)
    for x in (-0.3, -0.1, 0.1, 0.3):
        lens(hand, (x, -0.56, -0.06), (0, -1, 0), 0.08, 0.07, 0.06, T, n=8)


def leg(o, part, side, S):
    P, P2, T = S["plate"], S["plate2"], S["trim"]
    ul, ll, foot = o(part + "UpperLeg"), o(part + "LowerLeg"), o(part + "Foot")
    rshell(ul, [(-0.58, 0.57, 0.58), (0.55, 0.6, 0.6)], P)
    for s in (1, -1):  # gold lines down the thigh
        pipe(ul, [(s * 0.32, -0.6, 0.5), (s * 0.2, -0.62, -0.1), (s * 0.08, -0.6, -0.55)], T)
    # Knee cop with side wings, greave with a front ridge.
    lens(ll, (0, -0.6, 0.5), (0, -1, 0.1), 0.4, 0.34, 0.2, T if S["knee"] == "gold" else P)
    if S["knee"] != "gold":
        trim(ll, 0.5, 0.6, 0.6, T, h=0.05)
    for s in (1, -1):
        lens(ll, (s * 0.5, -0.4, 0.5), (s, -0.6, 0), 0.26, 0.24, 0.1, S["knee"] if S["knee"] != "plate_black" else T)
    rshell(ll, [(-0.6, 0.58, 0.6, {"keel": 0.08}), (0.38, 0.6, 0.62, {"keel": 0.1})], P)
    trim(ll, 0.36, 0.62, 0.64, T, keel=0.1)
    pipe(ll, [(0, -0.73, 0.3), (0, -0.7, -0.55)], T)
    # Pointed sabaton with layered lames.
    rshell(foot, [(-0.2, 0.56, 0.62, {"keel": 0.3, "dy": -0.08}), (0.12, 0.54, 0.56, {"keel": 0.18, "dy": -0.04}),
                  (0.22, 0.5, 0.5)], P)
    for i in range(3):
        trim(foot, 0.1 - 0.1 * i, 0.56 + 0.01 * i, 0.6 + 0.03 * i, T if i == 0 else P2, h=0.05,
             keel=0.2 + 0.05 * i, dy=-0.06)


def crystals(o, S, rnd):
    """The corruption still shows: a cluster breaking through the left pauldron."""
    n = S["crystals"]
    if n:
        o.crystals("LeftUpperArm", n, (0.6, 0.1, 0.75), (0.25, 0.4, 0.15), (0.7, 0.2, 1), length=(0.35, 0.8),
                   radius=(0.06, 0.12))
    if n > 5:
        o.crystals("LeftLowerArm", n // 2, (0.6, 0.0, 0.0), (0.05, 0.4, 0.3), (1, 0, 0.4), length=(0.25, 0.55),
                   radius=(0.05, 0.09))


# ---------------------------------------------------------------------------
def parade_shield(o, face="plate_white", rim="gold", gem="gem_blue"):
    """Large rounded heater shield with a gold rim, a sunburst emblem and a gem."""
    s = o("LeftLowerArm", "Shield")
    outline = []
    for k in range(24):
        t = k / 24
        a = 2 * math.pi * t
        x, y = math.sin(a), math.cos(a)
        up = y * 1.15 if y > 0 else y * 1.7  # pointed toward the bottom
        across = x * (1.0 - 0.35 * max(0.0, -y) ** 1.5)
        outline.append((across * 0.95, up))
    prof = [(-up, -across) for across, up in outline]
    s.loft([(0.62, prof), (0.74, prof)], face, rot=(0, 90, 0), smooth=True)
    big = [(x * 1.07, y * 1.06) for x, y in prof]
    s.loft([(0.6, big), (0.69, big)], rim, rot=(0, 90, 0))
    lens(s, (0.76, 0, 0.25), (1, 0, 0), 0.42, 0.42, 0.08, rim, n=16)
    lens(s, (0.8, 0, 0.25), (1, 0, 0), 0.25, 0.25, 0.14, gem, n=12)
    for k in range(12):
        a = 2 * math.pi * k / 12
        fin(s, (0.78, 0.42 * math.cos(a), 0.25 + 0.42 * math.sin(a)), (0.2, math.cos(a), math.sin(a)),
            0.45 if k % 2 == 0 else 0.28, 0.07, 0.025, rim, roll=0)
    pipe(s, [(0.77, 0, -0.25), (0.77, 0, -1.5)], rim, w=0.12, t=0.05)

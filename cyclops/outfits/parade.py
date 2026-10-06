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


def ring(hw, hd, p=2.6, n=20, keel=0.0, dx=0.0, dy=0.0, kp=6):
    """Superellipse section (p = 2 ellipse ... large p = box). keel pushes the front
    centre forward into a ridge."""
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        c, s = math.cos(a), math.sin(a)
        x = hw * math.copysign(abs(s) ** (2 / p), s)
        y = -hd * math.copysign(abs(c) ** (2 / p), c)
        if keel:
            y -= keel * max(0.0, c) ** kp
        pts.append((x + dx, y + dy))
    return pts


def rshell(piece, rings, color, tip=None, base=None, pos=(0, 0, 0), rot=(0, 0, 0), p=2.6, n=20):
    """Rounded shell. rings: (z, half_w, half_d[, {p, keel, dx, dy}])."""
    lofted = []
    for r in rings:
        z, hw, hd = r[:3]
        o = r[3] if len(r) > 3 else {}
        lofted.append((z, ring(hw, hd, o.get("p", p), n, o.get("keel", 0.0), o.get("dx", 0.0), o.get("dy", 0.0),
                               o.get("kp", 6))))
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


def curved_plate(piece, center, radius, a0, a1, z0, z1, color, thick=0.05, flare=0.0, n=8, rot=(0, 0, 0)):
    """A plate curved round a vertical axis (tassets, greave fronts). Angles in degrees,
    0 = front (-Y), 90 = +X."""
    cx, cy = center

    def arc(r):
        return [(cx + r * math.sin(math.radians(a0 + (a1 - a0) * i / (n - 1))),
                 cy - r * math.cos(math.radians(a0 + (a1 - a0) * i / (n - 1)))) for i in range(n)]
    top = arc(radius) + list(reversed(arc(radius - thick)))
    bot = arc(radius + flare) + list(reversed(arc(radius + flare - thick)))
    piece.loft([(z0, bot), (z1, top)], color, smooth=True, rot=rot)


# ---------------------------------------------------------------------------
STYLES = {
    # plate: main plate, plate2: secondary lames, trim: piping, knee: knee cops
    "white": dict(plate="plate_white", plate2="blade", trim="blade", trim2="blade", knee="plate_white",
                  cape="cloth_royal", lining="cloth_white", tabard="cloth_white", helm="winged",
                  chest="emblem", gem="gem_blue", pauldron="round", crystals=3, spikes=False,
                  # Draped over the left shoulder only, like the reference.
                  cape_rings=[(0.98, 1.15, 0.1, 0.62, (35, 120)), (0.55, 1.9, 0.3, 0.75, (60, 105)),
                              (-0.4, 2.2, 0.6, 0.42, (74, 84)), (-2.0, 2.35, 0.72, 0.42, 74),
                              (-3.72, 2.55, 0.88, 0.48, 70)]),
    "black": dict(plate="plate_black", plate2="plate_black", trim="gold", trim2="gold", knee="gold",
                  cape="cloth_royal", lining="cloth_dark", tabard=None, helm="dark", chest="muscle",
                  gem="gem", pauldron="great", pk=1.25, crystals=3, spikes=True, folds=0.18, scarf=True,
                  lines=True,
                  # A voluminous cape draped over the great pauldrons and round the neck.
                  cape_rings=[(1.5, 0.88, 0.0, 0.76, 125), (1.34, 2.95, 0.1, 1.24, (122, 100)), (0.6, 3.05, 0.3, 1.05, 100),
                              (-0.4, 2.55, 0.65, 0.48, 80), (-2.0, 2.65, 0.8, 0.48, 74),
                              (-3.72, 2.85, 0.95, 0.55, 70)]),
    "guard": dict(plate="blade", plate2="plate_white", trim="gold", trim2="gold_engraved", knee="blade",
                  cape="cloth_royal", lining="cloth_white", tabard="cloth_royal", helm="plume", chest="cross",
                  gem="gem", pauldron="round", crystals=4, spikes=False),
    "dragoon": dict(plate="plate_black", plate2="plate_dark", trim="blade", trim2="blade", knee="plate_black",
                    cape=None, lining=None, tabard=None, helm="dragon", chest="muscle", gem="gem",
                    pauldron="dragon", crystals=4, spikes=True),
    "paladin": dict(plate="plate_white", plate2="plate_corrupt_heavy", trim="gold_engraved", trim2="gold",
                    knee="plate_white", cape="cloth_white", lining="cloth_royal", tabard="cloth_white",
                    helm="halo", chest="eye", gem="gem", pauldron="round", crystals=8, spikes=False),
}


def parade_knight(name, style, glow=(176, 70, 255), seed=40):
    S = STYLES[style]
    o = Outfit(name, glow=glow, corruption=0.4, seed=seed)
    helm(o, S)
    torso(o, S)
    if S["cape"]:
        cape(o, S)
    hips(o, S)
    for part, side in (("Left", 1), ("Right", -1)):
        arm(o, part, side, S)
        leg(o, part, side, S)
    if style == "dragoon":
        dragoon_fins(o, S)
    crystals(o, S, random.Random(seed))
    return o


def sweep(piece, base, d0, length, width, bend, color, edge=None, up=(0, 0, 1), flip=False):
    """A curved blade fin growing from base along d0, bending in the plane of d0 and `up`."""
    import weapons
    n = Vector(d0).cross(Vector(up))
    if n.length < 1e-3:
        n = Vector((1, 0, 0))
    n.normalize()
    if flip:
        n = -n
    weapons.sickle_blade(piece, base, d0, n, length, width, bend, color, thick=0.06, edge=edge)


def dragoon_fins(o, S):
    """Dragoon silhouette: curved blades sweeping back from elbows, forearms, knees, hips,
    heels and a pair of wing-like blades from the shoulder blades."""
    P, T = S["plate"], S["trim"]
    t, g = o("UpperTorso"), o("UpperTorso", "Glow")
    for s in (1, -1):
        # Silver filigree swirling over the chest, and the dragon's glowing veins.
        pipe(t, [(s * 0.15, -0.8, 0.62), (s * 0.45, -0.82, 0.78), (s * 0.78, -0.7, 0.6), (s * 0.95, -0.55, 0.2),
                 (s * 0.8, -0.65, -0.2), (s * 0.95, -0.55, -0.6)], T, w=0.06)
        pipe(g, [(s * 0.68, -0.72, 0.05), (s * 0.55, -0.72, -0.35), (s * 0.4, -0.7, -0.78)], "glow", w=0.05, t=0.03)
        pipe(g, [(s * 0.3, -0.83, 0.68), (s * 0.12, -0.82, 0.55)], "glow", w=0.05, t=0.03)
    for part, side in (("Left", 1), ("Right", -1)):
        pipe(o(part + "UpperArm", "Glow"), [(side * 0.86, -0.4, 0.3), (side * 0.95, 0.0, 0.25), (side * 0.86, 0.4, 0.3)],
             "glow", w=0.05, t=0.03)
        pipe(o(part + "LowerLeg", "Glow"), [(0, -0.75, 0.25), (0, -0.72, -0.5)], "glow", w=0.05, t=0.03)
    for s in (1, -1):
        sweep(t, (s * 0.45, 0.7, 0.6), (s * 0.5, 1, 0.9), 2.2, 0.7, 60, P, edge=T, flip=s < 0)  # back wings
        sweep(t, (s * 0.55, 0.7, 0.2), (s * 0.7, 1, 0.3), 1.5, 0.5, 50, P, edge=T, flip=s < 0)
    for part, side in (("Left", 1), ("Right", -1)):
        la, ll, lt, ft = o(part + "LowerArm"), o(part + "LowerLeg"), o("LowerTorso"), o(part + "Foot")
        sweep(la, (0, 0.6, 0.45), (side * 0.2, 1, 0.3), 1.1, 0.4, -50, P, edge=T)  # elbow blade
        sweep(la, (side * 0.6, 0.1, -0.1), (side * 0.6, 0.6, -1), 1.0, 0.34, 40, P, edge=T, up=(0, 1, 0))  # forearm
        sweep(ll, (0, -0.7, 0.55), (0, -0.4, 1), 0.95, 0.36, 60, P, edge=T, up=(0, -1, 0))  # knee horn
        sweep(lt, (side * 1.15, 0.2, -0.3), (side * 0.6, 0.7, -1), 1.3, 0.45, -45, P, edge=T, up=(0, 1, 0))  # hip
        sweep(ft, (0, 0.55, 0.0), (0, 1, -0.2), 0.65, 0.26, 40, P, edge=T)  # heel spur


# ---------------------------------------------------------------------------
def helm(o, S):
    """Each knight has his own helm, after his reference (the hidden head is shrunk so the
    helms can be slim). No eye shows - vision slits glow instead."""
    h, g = o("Head"), o("Head", "Glow")
    P, T, P2 = S["plate"], S["trim"], S["plate2"]
    kind = S["helm"]
    {"winged": helm_armet, "dark": helm_egg, "plume": helm_wolf, "halo": helm_hood,
     "dragon": helm_dragon}[kind](h, g, P, P2, T, S)
    if kind != "halo":  # layered neck guard (the hood covers the Paladin's neck)
        for i in range(3):
            rshell(h, [(-0.75 - 0.12 * i, 0.58 - 0.03 * i, 0.12, {"dy": 0.6 + 0.04 * i}),
                       (-0.6 - 0.12 * i, 0.62 - 0.03 * i, 0.12, {"dy": 0.58 + 0.04 * i})], P2 if i % 2 else P)


def _skull(h, P, top=1.12, tip_y=-0.06, keel=0.12):
    rshell(h, [(-0.6, 0.55, 0.6, {"keel": keel * 0.5}), (-0.15, 0.58, 0.63, {"keel": keel * 0.8}),
               (0.3, 0.58, 0.62, {"keel": keel}), (0.64, 0.46, 0.52, {"keel": keel * 0.8}), (top - 0.2, 0.2, 0.28)],
           P, tip=(0, tip_y, top), p=3.0)


def _wedge_visor(h, P, jut, z_top=0.04):
    """Faceted visor wedged to a vertical point (flat shading keeps the creases)."""
    def vis(front, half, side, back):
        return [(0, -front), (half[0], -half[1]), (side[0], -side[1]), (back[0], -back[1]),
                (-back[0], -back[1]), (-side[0], -side[1]), (-half[0], -half[1])]
    h.loft([(-0.72, vis(0.9 + jut, (0.18, 0.76 + jut * 0.6), (0.26, 0.52), (0.22, 0.3))),
            (-0.32, vis(0.86 + jut * 0.8, (0.4, 0.74 + jut * 0.4), (0.57, 0.48), (0.5, 0.25))),
            (z_top, vis(0.8 + jut * 0.4, (0.48, 0.69), (0.6, 0.42), (0.52, 0.25)))], P)
    return 0.8 + jut * 0.4  # front depth at the top of the visor


def _angry_brow(h, g, P, tilt=17, z=0.19):
    for s in (1, -1):
        h.box((0.66, 0.3, 0.1), P, pos=(s * 0.3, -0.74, z), rot=(-14, -s * tilt, s * 12), top=(1, 0.7))
        h.box((0.42, 0.06, 0.12), "black", pos=(s * 0.27, -0.74, z - 0.12), rot=(0, -s * tilt, 0))
        g.box((0.36, 0.04, 0.05), "glow", pos=(s * 0.27, -0.775, z - 0.12), rot=(0, -s * tilt, 0))


def helm_armet(h, g, P, P2, T, S):
    """White Knight: a sleek armet. The visor runs up to the brow and wedges to a sharp
    point, cut by glowing horizontal slots; cheek guards sweep back; a crest ridge and a
    crown of spikes rise at the top."""
    _skull(h, P, top=1.05)
    jut = 0.2
    front = _wedge_visor(h, P, jut, z_top=0.36)
    ang = math.degrees(math.atan2(front + jut * 0.2 - 0.69, 0.48))
    for z, wd in ((0.2, 0.05), (0.08, 0.035)):  # vision slots following the wedge
        for s in (1, -1):
            cx, cy = s * 0.23, -(front + 0.69) / 2 - 0.035
            h.box((0.46, 0.05, wd + 0.05), "black", pos=(cx, cy + 0.01, z), rot=(0, 0, s * ang))
            g.box((0.42, 0.03, wd), "glow", pos=(cx, cy - 0.01, z), rot=(0, 0, s * ang))
    h.box((0.06, 0.1, 0.95), P2, pos=(0, -front - 0.04, -0.15), rot=(6, 0, 0), top=(0.5, 1))  # nose ridge
    for s in (1, -1):  # cheek guards sweeping back
        for k in range(2):
            fin(h, (s * 0.58, -0.4 + 0.15 * k, -0.25 - 0.18 * k), (s * 0.25, 1, 0.25), 0.85 - 0.15 * k, 0.2, 0.035, P,
                roll=90)
    for k in range(5):  # crest ridge from brow to crown
        t = k / 4
        fin(h, (0, -0.5 + 0.8 * t, 0.8 + 0.2 * t - 0.3 * t * t), (0, 0.4, 1), 0.35 - 0.1 * t, 0.03, 0.1, P)
    for k in range(5):  # crown of spikes at the back of the top
        a = math.radians(-60 + 30 * k)
        fin(h, (0.32 * math.sin(a), 0.1 + 0.25 * math.cos(a), 0.88), (math.sin(a) * 0.5, 0.6, 1),
            0.6 if k == 2 else 0.45, 0.09, 0.03, P, roll=90)


def helm_egg(h, g, P, P2, T, S):
    """Black Knight (Momon): a very tall, smooth, egg-shaped helm whose crown points
    forward. A black face panel framed in gold, one burning slit across it."""
    rshell(h, [(-0.62, 0.55, 0.6, {"keel": 0.06}), (-0.1, 0.58, 0.64, {"keel": 0.14}), (0.4, 0.56, 0.62, {"keel": 0.14}),
               (0.82, 0.42, 0.5, {"keel": 0.1}), (1.08, 0.18, 0.26)], P, tip=(0, -0.16, 1.3), p=2.6)
    panel = [(-0.42, 0.34), (0.42, 0.34), (0.46, 0.05), (0.3, -0.38), (0.0, -0.66), (-0.3, -0.38), (-0.46, 0.05)]
    h.loft([(-0.03, panel), (0.04, panel)], "black", rot=(90, 0, 0), pos=(0, -0.72, 0))
    pipe(h, [(x, -0.78, z) for x, z in panel + panel[:1]], T, w=0.05)
    pipe(h, [(0, -0.8, 0.34), (0, -0.82, 0.7), (0, -0.6, 1.05)], T, w=0.05)  # gold up the keel
    h.box((0.9, 0.06, 0.07), "black", pos=(0, -0.765, 0.12))
    g.box((0.84, 0.04, 0.045), "glow", pos=(0, -0.79, 0.12))


def helm_wolf(h, g, P, P2, T, S):
    """Royal Guard (Berserker-style beast helm): a long angular wolf snout lined with
    jagged teeth, steep scowling slits under a heavy brow, plates layered back over the
    skull and two short ears."""
    _skull(h, P, top=0.98, tip_y=0.1, keel=0.06)
    # Snout: angular sections tapering forward and down (local z -> forward).
    def sec(w, ht, zc):
        return [(w, zc), (w * 0.7, zc + ht), (-w * 0.7, zc + ht), (-w, zc), (-w * 0.6, zc - ht * 0.8), (w * 0.6, zc - ht * 0.8)]
    h.loft([(0.0, sec(0.5, 0.42, -0.2)), (0.35, sec(0.38, 0.32, -0.27)), (0.62, sec(0.22, 0.2, -0.34))], P,
           rot=(90, 0, 0), pos=(0, -0.55, 0), tip=(0, -0.38, 0.85))
    for s in (1, -1):
        for k in range(5):  # jagged teeth along the jaw line
            t = k / 4
            h.spike((s * (0.4 - 0.24 * t), -0.62 - 0.55 * t, -0.48 + 0.05 * t), (s * 0.15, -0.2, -1), 0.16 - 0.04 * t,
                    0.035, "plate_trim", sides=3)
        h.box((0.04, 0.6, 0.04), "black", pos=(s * 0.33, -0.85, -0.38), rot=(0, 0, s * -20))  # mouth line
    _angry_brow(h, g, P, tilt=28, z=0.2)
    for k in range(4):  # layered plates back over the skull
        t = k / 3
        h.box((0.9 - 0.15 * t, 0.42, 0.08), P2 if k % 2 else P, pos=(0, -0.2 + 0.32 * k, 0.95 - 0.12 * k - 0.15 * t * t),
              rot=(-25 - 15 * t, 0, 0), top=(0.8, 1))
    for s in (1, -1):  # ears
        fin(h, (s * 0.4, 0.15, 0.75), (s * 0.4, 0.5, 1), 0.5, 0.14, 0.04, P, roll=90)


def helm_hood(h, g, P, P2, T, S):
    """Paladin: a deep cloth hood with a pointed peak. The face is a black void with two
    glowing slits; a gold mask covers the jaw. The halo stands behind."""
    cloth, n = S["tabard"] or "cloth_white", 24

    def arc(rx, ry, y0, z, span, inset):
        pts = []
        for i in range(n):
            a = math.radians(-span + 2 * span * i / (n - 1))
            pts.append(((rx - inset) * math.sin(a), y0 + (ry - inset) * math.cos(a)))
        return pts
    rings = [(-1.0, 1.05, 0.9, 0.15, 125), (-0.6, 0.78, 0.74, 0.08, 130), (0.0, 0.74, 0.74, 0.04, 140),
             (0.6, 0.66, 0.7, 0.08, 145), (1.0, 0.4, 0.5, 0.2, 160)]
    lofted = [(z, arc(rx, ry, y0, z, sp, 0) + list(reversed(arc(rx, ry, y0, z, sp, 0.05)))) for z, rx, ry, y0, sp in rings]
    h.loft(lofted, cloth, smooth=True, tip=None)
    h.spike((0, 0.35, 1.0), (0, 0.6, 0.6), 0.6, 0.18, cloth, sides=6)  # pointed peak
    lens(h, (0, -0.5, 0.0), (0, -1, 0), 0.6, 0.7, 0.05, "black", n=16)  # the void
    for s in (1, -1):  # gold trim round the opening
        pipe(h, [(s * 0.5, -0.55, -0.6), (s * 0.62, -0.5, 0.0), (s * 0.45, -0.45, 0.6), (0.0, -0.4, 0.85)], T, w=0.05)
    mask = [(-0.42, -0.05), (0.42, -0.05), (0.36, -0.35), (0.0, -0.62), (-0.36, -0.35)]
    h.loft([(-0.04, mask), (0.04, mask)], T, rot=(90, 0, 0), pos=(0, -0.62, -0.1))  # gold jaw mask
    for s in (1, -1):
        g.box((0.22, 0.04, 0.05), "glow", pos=(s * 0.18, -0.6, 0.12), rot=(0, -s * 15, 0))
    for k in range(20):  # gold halo
        a = 2 * math.pi * k / 20
        h.box((0.12, 0.08, 0.36), T, pos=(1.15 * math.cos(a), 1.0, 0.4 + 1.15 * math.sin(a)),
              rot=(0, -math.degrees(a) + 90, 0))
    for k in range(10):
        a = 2 * math.pi * (k + 0.5) / 10
        g.spike((1.22 * math.cos(a), 1.0, 0.4 + 1.22 * math.sin(a)), (math.cos(a), 0, math.sin(a)),
                0.5 if k % 2 else 0.32, 0.06, "glow", sides=4)


def helm_dragon(h, g, P, P2, T, S):
    """Dragon Knight: a long downward dragon snout, a scowling brow, and a mane of curved
    blades sweeping back from the crown and temples, fangs at the jaw."""
    _skull(h, P)
    _wedge_visor(h, P, 0.38)
    _angry_brow(h, g, P)
    h.box((0.1, 0.12, 0.85), P2, pos=(0, -1.05, -0.28), rot=(8, 0, 0), top=(0.4, 1))
    for side in (1, -1):
        for k in range(3):  # curved horns sweeping back from the temples
            sweep(h, (side * 0.5, -0.1 + 0.25 * k, 0.5 - 0.1 * k), (side * 0.3, 1, 0.6 - 0.15 * k),
                  1.9 - 0.4 * k, 0.42 - 0.07 * k, 55, P, edge=T, flip=side < 0)
        for k in range(2):  # mane from the crown
            sweep(h, (side * (0.15 + 0.15 * k), 0.0 + 0.2 * k, 0.9 - 0.1 * k), (side * 0.25, 0.8, 1),
                  1.4 - 0.3 * k, 0.32, 60, P, edge=T, flip=side < 0)
        sweep(h, (side * 0.4, -0.75, -0.4), (side * 0.5, -0.6, -0.5), 0.6, 0.22, -60, P, edge=T)  # fangs
    sweep(h, (0, -0.5, 0.85), (0, 0.4, 1), 1.7, 0.45, -70, P, edge=T, up=(1, 0, 0))  # crest


def torso(o, S):
    t, g = o("UpperTorso"), o("UpperTorso", "Glow")
    P, P2, T = S["plate"], S["plate2"], S["trim"]
    # Breastplate with a central keel.
    rshell(t, [(-0.8, 1.04, 0.6, {"keel": 0.04}), (-0.2, 1.08, 0.63, {"keel": 0.08}),
               (0.35, 1.14, 0.67, {"keel": 0.12}), (0.74, 1.02, 0.6, {"keel": 0.06}), (0.86, 0.7, 0.5)], P)
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
        # Smooth breastplate: raised ridges sweeping from the shoulders into a V at the
        # waist (no bib).
        for s in (1, -1):
            pipe(t, [(s * 0.98, -0.5, 0.72), (s * 0.7, -0.7, 0.3), (s * 0.3, -0.78, -0.2), (0, -0.8, -0.72)], P2, w=0.07,
                 t=0.05)
        if chest == "emblem":
            # The blue gem set high on the left breast, in a small silver mount.
            lens(t, (0.4, -0.7, 0.45), (0.2, -1, 0.1), 0.22, 0.22, 0.06, P2, n=12)
            lens(t, (0.41, -0.74, 0.45), (0.2, -1, 0.1), 0.15, 0.15, 0.1, S["gem"], n=12)
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
    # (z, half width, centre y, half depth, half span in degrees from the back)
    rings = S.get("cape_rings") or [(0.94, 1.1, 0.15, 0.55, 80), (0.3, 1.35, 0.4, 0.45, 80),
                                    (-0.4, 2.15, 0.6, 0.38, 78), (-2.0, 2.3, 0.72, 0.4, 74),
                                    (-3.72, 2.5, 0.88, 0.45, 70)]
    folds = S.get("folds", 0.1)
    n = 26

    def arc(rx, y0, ry, span, z, inset):
        neg, pos = span if isinstance(span, tuple) else (span, span)
        pts = []
        for i in range(n):
            a = math.radians(-neg + (neg + pos) * i / (n - 1))
            fold = 0.0 if z > 0.5 else folds * math.sin(a * 7) * min(1.0, (0.5 - z) / 2.5)
            pts.append(((rx - inset) * math.sin(a), y0 + (ry - inset + fold) * math.cos(a)))
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
    if S.get("scarf"):
        # The cape bunched in a thick roll round the neck (Momon).
        for k, (z, w) in enumerate(((1.05, 0.86), (1.2, 0.8), (1.32, 0.7))):
            rshell(t, [(z - 0.1, w, w * 0.88, {"dy": 0.05}), (z + 0.08, w * 0.96, w * 0.84, {"dy": 0.05})],
                   S["cape"], p=2.0)
    for s in (1, -1):  # shoulder clasps
        blob(t, (s * 0.82, 0.3, 0.88), (0.19, 0.16, 0.19), S["trim2"], sides=10, rings=5)
        lens(t, (s * 0.82, 0.12, 0.9), (0, -1, 0.4), 0.09, 0.09, 0.09, S["gem"], n=8)


def hips(o, S):
    lt = o("LowerTorso")
    P, P2, T = S["plate"], S["plate2"], S["trim"]
    rshell(lt, [(-0.12, 1.08, 0.64), (0.22, 1.06, 0.62)], S["trim2"] if S.get("lines") else P2)  # belt
    lens(lt, (0, -0.64, 0.05), (0, -1, 0), 0.2, 0.15, 0.08, S["gem"], n=10)
    rshell(lt, [(-0.42, 1.14, 0.69), (-0.12, 1.1, 0.66)], P2 if P2 != "plate_corrupt_heavy" else P)  # fauld
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
    lines = S.get("lines", False)  # Momon-style gold piping
    ua, la, hand = o(part + "UpperArm"), o(part + "LowerArm"), o(part + "Hand")
    k = S.get("pk", 0.84 if S["pauldron"] == "dragon" else 1.0)
    out = side * (k - 1) * 0.8  # big pauldrons sit further out, clear of the helm
    # Pauldron: a dome peaking toward the neck over plates that overlap like scales,
    # sloping down and out, each with a point at its lower edge. Gold (or silver) only
    # peeks out under each plate's edge.
    rshell(ua, [(0.15, 0.82 * k, 0.78 * k, {"dx": side * 0.14 + out}), (0.55, 0.76 * k, 0.72 * k, {"dx": side * 0.08 + out}),
                (0.85, 0.44 * k, 0.48 * k, {"dx": out - side * 0.06})], P, p=2.3, tip=(out - side * 0.15, 0, 1.0 + 0.1 * k))
    fin(ua, (out - side * 0.3, -0.45 * k, 0.78), (0, 1, 0.12), 0.9 * k, 0.03, 0.16, P)  # raised ridge by the neck
    a0, a1 = (-15, 195) if side > 0 else (-195, 15)  # the outer side of the arm
    lames = 1 if S["pauldron"] == "dragon" else 3
    for i in range(lames):
        z1 = 0.32 - 0.24 * i * k
        z0 = z1 - 0.34 * k
        r = (0.78 + 0.05 * i) * k
        c = (out + side * (0.12 + 0.05 * i), 0.0)
        curved_plate(ua, c, r - 0.03, a0, a1, z0 - 0.05, z1 - 0.05, T, thick=0.04, flare=0.16, n=12)
        curved_plate(ua, c, r, a0 + 4, a1 - 4, z0, z1, P2 if i % 2 else P, thick=0.06, flare=0.16, n=12)
        ua.spike((c[0] + side * (r + 0.12), 0.0, z0 + 0.05), (side * 0.4, 0, -1), 0.3 * k, 0.09, P, sides=4)
    if S["pauldron"] == "dragon":
        for k2 in range(3):
            sweep(ua, (side * (0.35 + 0.2 * k2), -0.4 + 0.4 * k2, 0.85 - 0.1 * k2), (side * 0.6, 0.4, 1),
                  1.4 - 0.25 * k2, 0.45, 55, P, edge=T, flip=side < 0)
    if lines:
        pipe(ua, [(out + side * 0.1, -0.8 * k, 0.5), (out + side * 0.8 * k, 0.0, 0.62), (out + side * 0.1, 0.8 * k, 0.5)],
             T, w=0.05)
    rshell(ua, [(-0.6, 0.55, 0.55), (0.1, 0.57, 0.57)], P2 if P2 != "plate_corrupt_heavy" or side > 0 else P)
    # Couter with a fan, vambrace and a flared gauntlet cuff.
    lens(la, (0, 0.55, 0.42), (0, 1, 0.1), 0.34, 0.3, 0.16, P)
    lens(la, (side * 0.56, 0.0, 0.42), (side, 0, 0), 0.3, 0.26, 0.12, P2 if P2 != "plate_corrupt_heavy" else P)
    rshell(la, [(-0.4, 0.58, 0.58), (0.38, 0.6, 0.6)], P)
    rshell(la, [(-0.53, 0.72, 0.72), (-0.3, 0.6, 0.6)], P2 if P2 != "plate_corrupt_heavy" else P)
    if lines:
        trim(la, -0.53, 0.73, 0.73, T)
        pipe(la, [(side * 0.3, -0.62, 0.3), (side * 0.1, -0.63, -0.1), (side * 0.35, -0.62, -0.32)], T, w=0.045)
    rshell(hand, [(-0.16, 0.55, 0.55), (0.12, 0.58, 0.58)], P)
    for x in (-0.3, -0.1, 0.1, 0.3):
        lens(hand, (x, -0.56, -0.06), (0, -1, 0), 0.08, 0.07, 0.06, P2 if P2 != "plate_corrupt_heavy" else P, n=8)


def leg(o, part, side, S):
    P, P2, T = S["plate"], S["plate2"], S["trim"]
    lines = S.get("lines", False)
    ul, ll, foot = o(part + "UpperLeg"), o(part + "LowerLeg"), o(part + "Foot")
    rshell(ul, [(-0.58, 0.57, 0.58), (0.55, 0.6, 0.6)], P)
    if lines:  # gold lines down the thigh (Momon)
        for s in (1, -1):
            pipe(ul, [(s * 0.32, -0.6, 0.5), (s * 0.2, -0.62, -0.1), (s * 0.08, -0.6, -0.55)], T)
    # Knee cop with side wings, greave with a front ridge.
    lens(ll, (0, -0.6, 0.5), (0, -1, 0.1), 0.4, 0.34, 0.2, S["knee"])
    for s in (1, -1):
        lens(ll, (s * 0.5, -0.4, 0.5), (s, -0.6, 0), 0.26, 0.24, 0.1, S["knee"] if S["knee"] == "gold" else P2)
    rshell(ll, [(-0.6, 0.58, 0.6, {"keel": 0.08}), (0.38, 0.6, 0.62, {"keel": 0.1})], P)
    if lines:
        pipe(ll, [(0, -0.73, 0.3), (0, -0.7, -0.55)], T)
    # Pointed sabaton with layered lames.
    rshell(foot, [(-0.2, 0.56, 0.62, {"keel": 0.3, "dy": -0.08}), (0.12, 0.54, 0.56, {"keel": 0.18, "dy": -0.04}),
                  (0.22, 0.5, 0.5)], P)
    for i in range(3):
        trim(foot, 0.1 - 0.1 * i, 0.56 + 0.01 * i, 0.6 + 0.03 * i, P2 if i % 2 == 0 else P, h=0.05,
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

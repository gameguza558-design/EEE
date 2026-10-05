"""Weapons for the cyclops roster. Each weapon is a few named parts around a grip origin
(where the hand holds it), blade/head pointing along +Z (Roblox +Y).

Parts: "Handle" (always) plus Head/Blade/Guard/... and an optional "Glow" for
corruption crystals.
"""
import math
import random

from kit import Piece, band, blob, circle, tube


class Weapon:
    def __init__(self, name, damage=15, cooldown=0.8, two_handed=False, glow=(176, 70, 255),
                 grip=(0, 0, 0)):
        self.name, self.damage, self.cooldown = name, damage, cooldown
        self.two_handed, self.glow, self.grip = two_handed, glow, grip
        self.pieces = {}
        self.bleed = False  # saw-toothed weapons apply the Bleeding status in game
        self.dual = False  # wielded as a pair: CyclopsKit puts a second copy in the left hand

    def __call__(self, kind):
        return self.pieces.setdefault(kind, Piece())


def diamond(w, t):
    return [(w, 0), (0, t), (-w, 0), (0, -t)]


def haft(w, z0, z1, r=0.075, color="wood", rings=(), ring_color="iron"):
    tube(w("Handle"), z0, z1, r, r * 0.9, color, sides=6)
    for z in rings:
        tube(w("Handle"), z - 0.05, z + 0.05, r * 1.35, r * 1.35, ring_color, sides=6)


def axe_head(p, z, reach, height, thick, color, edge="blade", beard=0.0):
    """Single-bit axe head on the -Y side of the haft, centered at height z."""
    # Outline in (across=-y, up=z) and lofted through the thickness (x).
    outline = [(0.0, 0.22), (reach * 0.55, 0.18 + height * 0.15), (reach, height / 2),
               (reach, -height / 2 - beard), (reach * 0.55, -0.18 - beard * 0.6), (0.0, -0.22)]
    prof = [(-up, -across) for across, up in outline]
    p.loft([(-thick, prof), (thick, prof)], color, pos=(0, 0, z), rot=(0, 90, 0))
    e = [(-up, -across) for across, up in ((reach - 0.12, height / 2), (reach + 0.04, height / 2 + 0.05),
                                           (reach + 0.04, -height / 2 - beard - 0.05),
                                           (reach - 0.12, -height / 2 - beard))]
    p.loft([(-thick * 0.6, e), (thick * 0.6, e)], edge, pos=(0, 0, z), rot=(0, 90, 0))
    p.box((thick * 2.4, 0.3, 0.46), color, pos=(0, 0.05, z))  # socket


def sword(name, length, width, blade="blade", guard="plate_trim", grip="leather",
          pommel="plate_trim", damage=18, cooldown=0.7, glow_count=0, quillon=0.55):
    w = Weapon(name, damage=damage, cooldown=cooldown)
    band(w("Handle"), -0.32, 0.32, 0.09, 0.09, 0.03, grip)
    w("Blade").loft([(0.42, diamond(width, 0.05)), (0.42 + length * 0.75, diamond(width * 0.9, 0.045))],
                    blade, tip=(0, 0, 0.42 + length))
    w("Blade").box((0.05, 0.11, length * 0.6), "black", pos=(0, 0, 0.42 + length * 0.32), top=(0.4, 1))
    w("Guard").box((quillon * 2, 0.16, 0.12), guard, pos=(0, 0, 0.38))
    for s in (1, -1):
        w("Guard").spike((s * quillon, 0, 0.38), (s, 0, 0.3), 0.15, 0.06, guard, sides=4)
    blob(w("Pommel"), (0, 0, -0.42), (0.11, 0.11, 0.11), pommel, sides=6, rings=3)
    rnd = random.Random(hash(name) & 0xffff)
    for _ in range(glow_count):
        z = rnd.uniform(0.6, 0.42 + length * 0.5)
        w("Glow").spike((rnd.uniform(-width, width) * 0.6, rnd.choice((-1, 1)) * 0.04, z),
                        (rnd.uniform(-0.5, 0.5), rnd.choice((-1, 1)), rnd.uniform(0.2, 1)),
                        rnd.uniform(0.12, 0.25), 0.04, "glow", sides=5)
    return w


# ---------------------------------------------------------------------------
def cluster(w, center, count, seed, spread=0.12, length=(0.15, 0.32), radius=(0.03, 0.06), up=0.6):
    """A burst of corruption crystals growing out of a weapon."""
    rnd = random.Random(seed)
    cx, cy, cz = center
    for _ in range(count):
        d = (rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(0, 1) + up)
        w("Glow").spike((cx + rnd.uniform(-spread, spread), cy + rnd.uniform(-spread, spread) * 0.5,
                         cz + rnd.uniform(-spread, spread)), d, rnd.uniform(*length), rnd.uniform(*radius), "glow",
                        sides=5)


def wrap(w, z0, z1, r=0.085, color="leather_strap", step=0.09):
    z = z0
    while z < z1:
        band(w("Handle"), z, z + step * 0.6, r, r, r * 0.3, color)
        z += step


def pitchfork():
    """Corrupted pitchfork: three long barbed tines, a crossbar lashed with rope and bone."""
    w = Weapon("Pitchfork", damage=12, cooldown=0.9, two_handed=True)
    haft(w, -1.2, 2.4, 0.07, rings=(2.35,))
    wrap(w, -0.2, 0.5, color="rope")
    h = w("Head")
    h.box((0.78, 0.1, 0.12), "iron", pos=(0, 0, 2.45), top=(1.15, 1))
    for x in (-0.36, 0.0, 0.36):
        tube(h, 2.45, 3.25, 0.035, 0.03, "iron", sides=4, pos=(x, 0, 0))
        h.spike((x, 0, 3.25), (x * 0.3, 0, 1), 0.3, 0.04, "iron", sides=4)
        out = 1 if x >= 0 else -1
        h.spike((x, 0, 3.08), (out * 0.6, 0, -0.6), 0.14, 0.03, "iron", sides=3)  # barb
    for sgn in (1, -1):
        h.spike((sgn * 0.4, 0, 2.45), (sgn, 0, -0.4), 0.25, 0.05, "bone", sides=4)
    cluster(w, (0, 0, 2.5), 4, 11)
    return w


def hoe():
    """จอบ: a heavy war-hoe - broad blade with a jagged edge and a spike on the back."""
    w = Weapon("Hoe", damage=13, cooldown=0.9, two_handed=True)
    haft(w, -1.0, 2.5, 0.07, rings=(2.35, -0.9))
    wrap(w, 0.0, 0.6)
    h = w("Head")
    h.box((0.22, 0.26, 0.3), "iron", pos=(0, 0, 2.45))  # eye around the haft
    h.box((0.7, 0.66, 0.07), "iron", pos=(0, -0.4, 2.4), rot=(14, 0, 0), top=(1.18, 1))
    h.box((0.8, 0.07, 0.09), "blade", pos=(0, -0.74, 2.32), rot=(14, 0, 0))
    for k in range(5):  # jagged teeth on the edge
        h.spike((-0.32 + 0.16 * k, -0.76, 2.31), (0, -1, -0.25), 0.16, 0.05, "blade", sides=3)
    h.spike((0, 0.12, 2.45), (0, 1, 0.25), 0.45, 0.08, "iron", sides=4)  # back spike
    cluster(w, (0, -0.3, 2.5), 4, 12)
    return w


def spade():
    """เสียม: a digging spade sharpened into a weapon - serrated sides, a T grip."""
    w = Weapon("Spade", damage=12, cooldown=0.85)
    haft(w, -0.6, 1.9, 0.065)
    w("Handle").box((0.46, 0.1, 0.1), "wood", pos=(0, 0, -0.62))
    wrap(w, -0.5, -0.1, r=0.075)
    h = w("Head")
    h.box((0.16, 0.16, 0.3), "iron", pos=(0, 0, 1.95))  # socket
    h.loft([(2.05, [(0.22, 0.03), (-0.22, 0.03), (-0.22, -0.03), (0.22, -0.03)]),
            (2.65, [(0.18, 0.025), (-0.18, 0.025), (-0.18, -0.025), (0.18, -0.025)])], "iron", tip=(0, 0, 2.95))
    for sgn in (1, -1):
        for k in range(4):
            h.spike((sgn * 0.21, 0, 2.15 + 0.15 * k), (sgn, 0, 0.3), 0.1, 0.035, "blade", sides=3)
    h.box((0.4, 0.05, 0.06), "blade", pos=(0, 0, 2.65))
    cluster(w, (0.1, 0, 2.2), 3, 13)
    return w


def sickle():
    """เคียว: a large hooked sickle with a crystal growing along the inner edge."""
    w = Weapon("Sickle", damage=15, cooldown=0.55)
    band(w("Handle"), -0.4, 0.3, 0.075, 0.075, 0.025, "wood")
    wrap(w, -0.35, 0.2, r=0.08)
    tube(w("Handle"), 0.3, 0.4, 0.1, 0.1, "iron", sides=6)
    b = w("Blade")
    pts = [(0.0, 0.4)]
    for k in range(1, 11):
        a = math.radians(-10 + 175 * k / 10)
        pts.append((-0.55 + 0.55 * math.cos(a) * -1, 0.4 + 0.7 * math.sin(a) + 0.12))
    for i, ((y0, z0), (y1, z1)) in enumerate(zip(pts, pts[1:])):
        mid = ((y0 + y1) / 2, (z0 + z1) / 2)
        ang = math.degrees(math.atan2(z1 - z0, y1 - y0))
        length = math.hypot(z1 - z0, y1 - y0) + 0.03
        t = 1 - (i + 1) / len(pts)
        b.box((0.035, length, 0.13 * t + 0.03), "blade", pos=(0, mid[0], mid[1]), rot=(ang, 0, 0))
        if i % 3 == 1:
            w("Glow").spike((0, mid[0], mid[1]), (0, -(z1 - z0), (y1 - y0)), 0.18, 0.03, "glow", sides=4)
    return w


def scythe():
    """The reaper's scythe: a long curved blade with a bone collar and a corrupted vein."""
    w = Weapon("Scythe", damage=22, cooldown=1.2, two_handed=True)
    haft(w, -1.4, 3.2, 0.07, rings=(0.6, 3.0), ring_color="leather_strap")
    w("Handle").box((0.08, 0.35, 0.08), "wood", pos=(0, -0.2, 0.9))  # side grip
    for k in range(3):
        w("Handle").spike((0, 0.05, 3.05 - 0.1 * k), (0, 1, -0.6), 0.22, 0.05, "bone", sides=4)
    b, g = w("Blade"), w("Glow")
    prev = (0.0, 3.15)
    for k in range(1, 12):
        t = k / 11
        y, z = -2.3 * t, 3.15 + 0.45 * math.sin(t * math.pi * 0.9) - 0.25 * t
        ang = math.degrees(math.atan2(z - prev[1], y - prev[0]))
        mid = ((y + prev[0]) / 2, (z + prev[1]) / 2)
        b.box((0.035, math.hypot(y - prev[0], z - prev[1]) + 0.04, 0.26 * (1 - t) + 0.04), "blade",
              pos=(0, mid[0], mid[1] - 0.1), rot=(ang, 0, 0))
        if t < 0.75:
            g.box((0.045, math.hypot(y - prev[0], z - prev[1]) + 0.03, 0.03), "glow",
                  pos=(0, mid[0], mid[1] - 0.04), rot=(ang, 0, 0))
        prev = (y, z)
    cluster(w, (0, -0.1, 3.15), 4, 14)
    return w


def hunter_bow():
    # Limbs in the YZ plane, string on the +Y side; the grip is turned so the bow stands up.
    w = Weapon("HunterBow", damage=12, cooldown=1.2, grip=(90, 0, 0))
    band(w("Handle"), -0.25, 0.25, 0.08, 0.1, 0.03, "leather")
    limb = w("Limbs")
    pts = [(z, -0.28 * (z / 1.8) ** 1.6) for z in (0.22, 0.6, 1.0, 1.4, 1.8)]
    for sgn in (1, -1):
        for (z0, y0), (z1, y1) in zip(pts, pts[1:]):
            mid_z, mid_y = sgn * (z0 + z1) / 2, (y0 + y1) / 2
            ang = math.degrees(math.atan2(y1 - y0, z1 - z0)) * sgn
            limb.box((0.08, 0.1, abs(z1 - z0) + 0.05), "wood", pos=(0, mid_y, mid_z), rot=(-ang, 0, 0))
        limb.box((0.1, 0.1, 0.1), "bone", pos=(0, pts[-1][1], sgn * 1.85))
    w("String").box((0.015, 0.015, 3.5), "linen", pos=(0, pts[-1][1] + 0.03, 0))
    w("Glow").spike((0.0, -0.06, 1.0), (0.3, -1, 0.5), 0.18, 0.035, "glow", sides=5)
    return w


def woodcutter_axe():
    w = Weapon("WoodcutterAxe", damage=24, cooldown=1.2, two_handed=True)
    haft(w, -0.6, 3.1, 0.085, rings=(-0.5,), ring_color="leather_strap")
    axe_head(w("Head"), 2.65, 1.0, 1.0, 0.07, "iron", beard=0.2)
    w("Head").box((0.16, 0.34, 0.34), "iron", pos=(0, 0.3, 2.65))  # hammer poll
    w("Glow").spike((0.05, -0.4, 2.7), (1, -0.3, 0.5), 0.2, 0.04, "glow", sides=5)
    return w


def wolf_rider_spear():
    w = Weapon("WolfRiderSpear", damage=16, cooldown=0.8, two_handed=True)
    haft(w, -1.4, 3.0, 0.07, rings=(2.6, 2.95), ring_color="leather_strap")
    w("Head").loft([(3.0, diamond(0.08, 0.05)), (3.25, diamond(0.2, 0.05)), (3.7, diamond(0.12, 0.04))],
                   "blade", tip=(0, 0, 4.05))
    for a in range(4):
        ang = a * math.pi / 2
        w("Head").spike((0.1 * math.cos(ang), 0.1 * math.sin(ang), 2.8),
                        (math.cos(ang), math.sin(ang), -1.2), 0.25, 0.04, "bone", sides=4)
    for i in range(5):
        w("Head").spike((0.06 * (i - 2), 0.07, 2.75), (0.2 * (i - 2), 0.4, -1), 0.45, 0.05, "fur_dark", sides=4)
    w("Glow").spike((0.0, 0.05, 3.3), (0.4, 1, 0.6), 0.2, 0.04, "glow", sides=5)
    return w


def tier_axe(tier):
    spec = {
        "Apprentice": dict(head="iron", edge="iron", haft="wood", ring="iron", reach=0.7, h=0.75, dmg=16, glow=0),
        "Mid": dict(head="plate_mid", edge="blade", haft="wood", ring="leather_strap", reach=0.9, h=0.95, dmg=22, glow=2),
        "High": dict(head="plate_dark", edge="blade_corrupt", haft="plate_dark", ring="gold", reach=1.1, h=1.2, dmg=30, glow=7),
    }[tier]
    w = Weapon(f"{tier}Axe", damage=spec["dmg"], cooldown=1.0)
    haft(w, -0.45, 2.3, 0.075, color=spec["haft"], rings=(-0.4, 1.0), ring_color=spec["ring"])
    axe_head(w("Head"), 1.9, spec["reach"], spec["h"], 0.065, spec["head"], edge=spec["edge"],
             beard=0.25 if tier != "Apprentice" else 0.0)
    if tier == "High":
        w("Head").spike((0, 0, 2.3), (0, 0, 1), 0.45, 0.08, "gold", sides=4)
        w("Head").spike((0, 0.15, 1.9), (0, 1, 0.2), 0.4, 0.09, "gold", sides=4)
    rnd = random.Random(len(tier))
    for _ in range(spec["glow"]):
        w("Glow").spike((rnd.uniform(-0.06, 0.06), -rnd.uniform(0.2, spec["reach"] - 0.1), 1.9 + rnd.uniform(-0.3, 0.3)),
                        (rnd.choice((-1, 1)), rnd.uniform(-0.5, 0.2), rnd.uniform(0, 0.8)),
                        rnd.uniform(0.12, 0.3), 0.04, "glow", sides=5)
    return w


def tier_sword(tier):
    if tier == "Apprentice":
        return sword("ApprenticeSword", 2.6, 0.17, blade="iron", guard="iron", pommel="iron",
                     damage=15)
    if tier == "Mid":
        w = sword("MidSword", 3.0, 0.21, damage=20, glow_count=2, quillon=0.6)
        w("Glow").box((0.03, 0.12, 1.6), "glow", pos=(0, 0, 1.3), top=(0.3, 1))  # corruption in the fuller
        for s in (1, -1):
            w("Guard").spike((s * 0.45, 0, 0.42), (s * 0.5, 0, 1), 0.28, 0.05, "plate_trim", sides=4)
        gem(w("Glow"), (0, 0, -0.42), 0.07, axis="z", color="glow")
        return w
    w = sword("HighSword", 3.6, 0.25, blade="blade_corrupt", guard="gold", grip="leather_strap",
              pommel="gold", damage=27, glow_count=8, quillon=0.75)
    w("Glow").box((0.035, 0.12, 2.4), "glow", pos=(0, 0, 1.7), top=(0.3, 1))
    for s in (1, -1):
        w("Guard").spike((s * 0.55, 0, 0.42), (s * 0.4, 0, 1), 0.45, 0.06, "gold", sides=4)
        w("Guard").spike((s * 0.3, 0, 0.42), (s * 0.2, 0, 1), 0.3, 0.05, "gold", sides=4)
        for k in range(4):  # jagged, flame-like edge near the guard
            w("Blade").spike((s * 0.24, 0, 0.7 + 0.28 * k), (s, 0, 0.8), 0.18, 0.045, "blade_corrupt", sides=4)
    gem(w("Glow"), (0, -0.1, 0.38), 0.08, color="glow")
    gem(w("Glow"), (0, 0.1, 0.38), 0.08, color="glow")
    return w


def onehorn_greatsword():
    """The One-Horn's lightly corrupted greatsword."""
    wp = Weapon("OneHornGreatsword", damage=35, cooldown=1.0, two_handed=True)
    grip, blade, guard, pommel, glow = wp("Handle"), wp("Blade"), wp("Guard"), wp("Pommel"), wp("Glow")
    rnd = random.Random(7)
    # Grip with leather wraps.
    grip.shell([(-0.65, 0.11, 0.11, 0.04), (0.65, 0.11, 0.11, 0.04)], "leather")
    for z in (-0.4, 0.0, 0.4):
        grip.box((0.26, 0.26, 0.08), "leather_strap", pos=(0, 0, z))
    # Blade: diamond section, slightly leaf-shaped, with a long point.
    # The lower blade, nearest the guard, is cracked by the corruption.
    blade.loft([(0.72, diamond(0.3, 0.07)), (1.4, diamond(0.34, 0.075)),
                (2.4, diamond(0.33, 0.072))], "blade_corrupt")
    blade.loft([(2.4, diamond(0.33, 0.072)), (3.6, diamond(0.3, 0.065)),
                (5.0, diamond(0.2, 0.05))], "blade", tip=(0, 0, 5.9))
    # Fuller.
    blade.box((0.08, 0.16, 3.2), "black", pos=(0, 0, 2.6), top=(0.5, 1))
    # Jagged teeth along both edges.
    for s in (1, -1):
        z = 1.0
        while z < 4.8:
            w = 0.34 if z < 3.6 else 0.3 - (z - 3.6) * 0.07
            blade.spike((s * (w - 0.03), 0, z), (s, 0, rnd.uniform(0.6, 1.1)),
                        rnd.uniform(0.18, 0.3), 0.045, "plate_trim", sides=4)
            z += rnd.uniform(0.35, 0.6)
    # Corruption crystals creeping up from the guard.
    for _ in range(9):
        z = rnd.uniform(0.85, 2.4)
        s = rnd.choice((1, -1))
        glow.spike((rnd.uniform(-0.2, 0.2), s * 0.06, z), (rnd.uniform(-0.4, 0.4), s, rnd.uniform(0.3, 1)),
                   rnd.uniform(0.15, 0.32), rnd.uniform(0.04, 0.07), "glow", sides=5)
    glow.box((0.05, 0.17, 1.4), "glow", pos=(0, 0, 1.45), top=(0.3, 1))
    # Cross-guard with spiked, downturned quillons.
    guard.box((1.0, 0.24, 0.2), "plate_dark", pos=(0, 0, 0.7))
    for s in (1, -1):
        guard.box((0.55, 0.2, 0.16), "plate_dark", pos=(s * 0.72, 0, 0.64), rot=(0, s * 18, 0),
                  top=(1, 0.8))
        guard.spike((s * 0.95, 0, 0.55), (s, 0, -0.6), 0.35, 0.09, "plate_mid", sides=4)
        guard.spike((s * 0.35, 0, 0.8), (s * 0.5, 0, 1), 0.25, 0.06, "plate_mid", sides=4)
    guard.spike((0, -0.12, 0.7), (0, -1, 0.2), 0.2, 0.08, "plate_mid", sides=4)
    guard.spike((0, 0.12, 0.7), (0, 1, 0.2), 0.2, 0.08, "plate_mid", sides=4)
    # Spiked pommel.
    pommel.loft([(-0.82, diamond(0.12, 0.12)), (-0.95, diamond(0.22, 0.22)),
                 (-1.08, diamond(0.12, 0.12))], "plate_dark", base=(0, 0, -1.3))
    pommel.box((0.12, 0.12, 0.2), "plate_mid", pos=(0, 0, -0.74))
    for s in (1, -1):
        pommel.spike((s * 0.2, 0, -0.95), (s, 0, 0), 0.18, 0.05, "plate_mid", sides=4)
    return wp


# ---------------------------------------------------------------------------
# Nobles, soldiers and the wolf corps.
def serrate(p, z0, z1, x, sign, depth=0.12, step=0.14, thick=0.03, color="blade"):
    """Saw teeth along a blade edge at x (sign = which side), pointing back toward the grip,
    so a cut drags and tears (bleeding)."""
    z = z0
    while z < z1:
        p.spike((x, 0, z), (sign, 0, -0.55), depth, 0.045, color, sides=3)
        z += step


def spear():
    """Soldier's winged spear: a long leaf blade, lugs below it and a red tassel."""
    w = Weapon("Spear", damage=17, cooldown=0.8, two_handed=True)
    haft(w, -1.6, 3.3, 0.07, rings=(-1.5, 3.2), ring_color="iron")
    h = w("Head")
    tube(h, 3.15, 3.45, 0.1, 0.08, "plate_dark", sides=6)
    h.loft([(3.45, diamond(0.08, 0.05)), (3.75, diamond(0.24, 0.05)), (4.3, diamond(0.14, 0.035))],
           "blade", tip=(0, 0, 4.9))
    h.box((0.05, 0.08, 1.0), "plate_dark", pos=(0, 0, 4.0), top=(0.4, 1))  # midrib
    for sgn in (1, -1):  # wings
        h.spike((sgn * 0.08, 0, 3.35), (sgn, 0, 0.45), 0.35, 0.05, "blade", sides=4)
    for k in range(5):  # tassel
        a = 2 * math.pi * k / 5
        h.spike((0.09 * math.cos(a), 0.09 * math.sin(a), 3.15), (0.2 * math.cos(a), 0.2 * math.sin(a), -1), 0.5, 0.05,
                "cloth", sides=4)
    return w


def dragon_slayer():
    """The General's colossal sword: a crude slab of iron, far too big to be called a sword."""
    w = Weapon("DragonSlayer", damage=55, cooldown=1.9, two_handed=True)
    band(w("Handle"), -0.75, 0.75, 0.12, 0.12, 0.04, "leather_strap")
    for z in (-0.5, -0.1, 0.3):
        band(w("Handle"), z - 0.04, z + 0.04, 0.14, 0.14, 0.04, "leather")
    w("Guard").box((1.25, 0.34, 0.24), "iron", pos=(0, 0, 0.88))
    blade = w("Blade")
    # Thick slab: hexagonal section, barely tapering, with a blunt angled tip.
    def slab(hw, ht):
        return [(hw, 0), (hw * 0.82, ht), (-hw * 0.82, ht), (-hw, 0), (-hw * 0.82, -ht), (hw * 0.82, -ht)]
    blade.loft([(1.0, slab(0.48, 0.13)), (5.6, slab(0.46, 0.12)), (6.6, slab(0.4, 0.1))], "iron",
               tip=(-0.15, 0, 7.4))
    for z in (2.0, 3.6, 5.0):  # dents and scars
        blade.box((0.3, 0.27, 0.06), "plate_dark", pos=(0.1, 0, z), rot=(0, 25, 0))
    blob(w("Pommel"), (0, 0, -0.9), (0.18, 0.18, 0.16), "iron", sides=6, rings=3)
    rnd = random.Random(99)
    for _ in range(6):  # the corruption has started to crack the iron
        z = rnd.uniform(1.2, 4.5)
        w("Glow").spike((rnd.uniform(-0.35, 0.35), rnd.choice((-1, 1)) * 0.12, z),
                        (rnd.uniform(-0.3, 0.3), rnd.choice((-1, 1)), rnd.uniform(0.2, 0.8)), rnd.uniform(0.15, 0.3),
                        0.05, "glow", sides=5)
    return w


def serrated_spear():
    w = Weapon("SerratedSpear", damage=15, cooldown=0.8, two_handed=True)
    w.bleed = True
    haft(w, -1.6, 3.2, 0.07, color="wood", rings=(3.1,), ring_color="iron")
    w("Head").loft([(3.2, diamond(0.08, 0.05)), (3.5, diamond(0.22, 0.045)), (4.0, diamond(0.12, 0.035))],
                   "iron", tip=(0, 0, 4.4))
    for sgn in (1, -1):
        serrate(w("Head"), 3.35, 4.1, sgn * 0.19, sgn, depth=0.12, step=0.12, color="iron")
    return w


def serrated_sword():
    w = Weapon("SerratedSword", damage=17, cooldown=0.7)
    w.bleed = True
    band(w("Handle"), -0.32, 0.32, 0.09, 0.09, 0.03, "leather_strap")
    w("Blade").loft([(0.42, diamond(0.22, 0.05)), (2.6, diamond(0.19, 0.045))], "iron", tip=(0, 0, 3.1))
    serrate(w("Blade"), 0.6, 2.7, 0.2, 1, depth=0.16, step=0.15, color="iron")  # saw spine on one edge
    w("Guard").box((0.9, 0.16, 0.12), "plate_dark", pos=(0, 0, 0.38))
    blob(w("Pommel"), (0, 0, -0.42), (0.11, 0.11, 0.11), "plate_dark", sides=6, rings=3)
    return w


def serrated_cleaver():
    """The wolf handler's butcher cleaver with a saw back."""
    w = Weapon("SerratedCleaver", damage=14, cooldown=0.65)
    w.bleed = True
    band(w("Handle"), -0.35, 0.3, 0.08, 0.08, 0.025, "wood")
    w("Blade").box((0.06, 0.62, 1.5), "iron", pos=(0, -0.22, 1.1), top=(1, 1.15))
    w("Blade").box((0.07, 0.08, 1.5), "blade", pos=(0, -0.55, 1.1))
    for k in range(10):  # saw back
        w("Blade").spike((0, 0.1, 0.45 + 0.13 * k), (0, 1, -0.5), 0.13, 0.04, "iron", sides=3)
    return w


# ---------------------------------------------------------------------------
# Luxury knights and the Prince: parade weapons - gold, gems and glowing runes.
GOLD_LIGHT = (255, 214, 120)
EMBER = (255, 40, 60)
CYAN = (60, 230, 255)


def gem(p, center, r, axis="y", color="gem"):
    """A cut gem (octahedron) set into a weapon."""
    x, y, z = center
    d = {"y": (0, 1, 0), "x": (1, 0, 0), "z": (0, 0, 1)}[axis]
    p.spike(center, d, r, r, color, sides=4)
    p.spike(center, tuple(-c for c in d), r, r, color, sides=4)


def wing_guard(p, z, span, color="gold_engraved", feathers=4, up=0.8):
    """Cross-guard shaped like a pair of swept-up wings, feathers fanning outward."""
    for s in (1, -1):
        for k in range(feathers):
            t = k / max(1, feathers - 1)
            base = (s * (0.12 + 0.18 * t), 0, z + 0.02 * k)
            p.spike(base, (s * (1 - 0.35 * t), 0, up * (0.25 + 0.6 * t)), span * (1 - 0.25 * t), 0.09, color, sides=4)


PURPLE_HOT = (200, 80, 255)
DRAGON_GLOW = (255, 50, 110)


def arc_boxes(p, center, radius, a0, a1, n, size, color, axis="y"):
    """Boxes along an arc in the XZ plane (hooks, crescents, guards). Angles in degrees,
    0 = +X, 90 = +Z. size = (thickness across the arc, depth in Y)."""
    cx, cz = center
    pts = [(cx + radius * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
            cz + radius * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
        ang = math.degrees(math.atan2(x1 - x0, z1 - z0))
        p.box((size[0], size[1], math.hypot(x1 - x0, z1 - z0) + size[0] * 0.5), color,
              pos=((x0 + x1) / 2, 0, (z0 + z1) / 2), rot=(0, ang, 0))


def long_grip(w, z0, z1, wrap="leather_strap", ring="gold", r=0.1):
    band(w("Handle"), z0, z1, r, r, r * 0.3, wrap)
    z = z0 + 0.15
    while z < z1 - 0.1:
        band(w("Handle"), z - 0.035, z + 0.035, r * 1.2, r * 1.2, r * 0.35, ring)
        z += 0.38


def radiant_greatsword():
    """White Knight: a very long holy greatsword - silver blade with an engraved gold
    fuller and a glowing rune, gold curved quillons, a blue gem and a long grip."""
    w = Weapon("RadiantGreatsword", damage=42, cooldown=1.0, glow=GOLD_LIGHT)
    long_grip(w, -0.75, 0.7, wrap="cloth_royal")
    b = w("Blade")
    b.loft([(1.0, diamond(0.46, 0.08)), (1.6, diamond(0.5, 0.085)), (5.4, diamond(0.44, 0.075)),
            (6.5, diamond(0.32, 0.06))], "blade", tip=(0, 0, 7.7))
    b.box((0.2, 0.18, 3.6), "gold_engraved", pos=(0, 0, 3.0), top=(0.5, 1))
    g = w("Glow")
    g.box((0.05, 0.2, 3.2), "glow", pos=(0, 0, 3.1), top=(0.3, 1))
    for z in (1.8, 2.6, 3.4, 4.2):
        g.box((0.16, 0.21, 0.06), "glow", pos=(0, 0, z), rot=(0, 45, 0))
    gd = w("Guard")
    gd.box((0.62, 0.32, 0.34), "gold_engraved", pos=(0, 0, 0.85))
    for s in (1, -1):
        arc_boxes(gd, (s * 0.3, 1.3), 0.55, 270, 270 + s * 75, 5, (0.15, 0.2), "gold")
        gd.spike((s * 0.85, 0, 1.25), (s * 0.3, 0, 1), 0.35, 0.08, "gold", sides=4)
        b.box((0.09, 0.22, 0.6), "gold", pos=(s * 0.42, 0, 1.25), top=(0.4, 1))  # langets
    wing_guard(gd, 0.85, 0.7, feathers=3)
    gem(gd, (0, -0.17, 0.85), 0.14, color="gem_blue")
    gem(gd, (0, 0.17, 0.85), 0.14, color="gem_blue")
    pm = w("Pommel")
    pm.loft([(-0.78, diamond(0.12, 0.12)), (-0.95, diamond(0.24, 0.24)), (-1.12, diamond(0.12, 0.12))],
            "gold_engraved", base=(0, 0, -1.35))
    gem(pm, (0, 0, -0.95), 0.12, color="gem_blue")
    return w


def abyss_greatsword():
    """Black Knight: one of a pair of enormous straight greatswords (as long as he is
    tall) with an open slot down the blade, an axe-head tip and silver curved quillons.
    Wielded one in each hand."""
    w = Weapon("AbyssGreatsword", damage=36, cooldown=0.9, glow=EMBER)
    w.dual = True
    long_grip(w, -0.8, 0.7)
    b, g = w("Blade"), w("Glow")
    b.loft([(0.95, diamond(0.44, 0.085)), (1.7, diamond(0.46, 0.085))], "blade_dark")
    for s in (1, -1):  # the two rails either side of the open slot
        rail = [(s * 0.17, 0.07), (s * 0.17, -0.07), (s * 0.46, 0.0)]
        b.loft([(1.7, rail), (6.4, [(x * 0.96, y) for x, y in rail])], "blade_dark")
        b.box((0.03, 0.05, 4.7), "blade", pos=(s * 0.45, 0, 4.05))  # bright cutting edge
    b.loft([(6.4, diamond(0.44, 0.08)), (6.9, diamond(0.42, 0.075))], "blade_dark")
    # The tip ends in an axe head: a broad blade flaring to one side with a hooked beard.
    head = [(-0.42, 6.85), (0.42, 6.85), (0.6, 7.0), (0.98, 7.3), (0.92, 7.8), (0.4, 8.0), (-0.22, 7.82), (-0.42, 7.35)]
    b.loft([(-0.07, head), (0.07, head)], "blade_dark", rot=(90, 0, 0))
    edge = [(0.9, 7.25), (1.06, 7.32), (1.0, 7.86), (0.86, 7.82)]
    b.loft([(-0.035, edge), (0.035, edge)], "blade", rot=(90, 0, 0))  # bright cutting edge
    b.spike((0.92, 0, 7.3), (0.4, 0, -1), 0.4, 0.06, "blade_dark", sides=4)  # beard hook
    b.spike((-0.3, 0, 7.75), (-0.3, 0, 1), 0.35, 0.06, "blade_dark", sides=4)
    g.box((0.05, 0.05, 4.6), "glow", pos=(0, 0, 4.05))  # ember core glowing in the slot
    b.box((0.94, 0.2, 0.08), "gold", pos=(0, 0, 1.0))
    gd = w("Guard")
    gd.box((0.6, 0.3, 0.3), "blade", pos=(0, 0, 0.82))
    for s in (1, -1):  # silver quillons curving up toward the blade
        arc_boxes(gd, (s * 0.25, 1.4), 0.62, 270, 270 + s * 70, 5, (0.14, 0.22), "blade")
        gd.spike((s * 0.75, 0, 1.4), (s * 0.4, 0, 1), 0.4, 0.07, "blade", sides=4)
    gem(gd, (0, -0.16, 0.82), 0.11)
    gem(gd, (0, 0.16, 0.82), 0.11)
    pm = w("Pommel")
    pm.loft([(-0.82, diamond(0.13, 0.13)), (-0.98, diamond(0.2, 0.2))], "blade", tip=(0, 0, -1.4))
    return w


def royal_halberd():
    """Royal Guard: a towering gilded halberd - huge crescent axe, long spike and back hook."""
    w = Weapon("RoyalHalberd", damage=34, cooldown=1.2, two_handed=True, glow=GOLD_LIGHT)
    haft(w, -2.2, 5.0, 0.085, color="black", rings=(-2.1, -0.4, 1.4, 4.4), ring_color="gold")
    h = w("Head")
    tube(h, 4.6, 5.5, 0.13, 0.12, "gold_engraved", sides=8)
    pts = []
    for k in range(13):  # crescent axe on -Y
        a = math.radians(-75 + 150 * k / 12)
        pts.append((-0.35 - 1.25 * math.cos(a), 5.05 + 1.15 * math.sin(a)))
    for (y0, z0), (y1, z1) in zip(pts, pts[1:]):
        h.box((0.06, 0.45, math.hypot(y1 - y0, z1 - z0) + 0.05), "blade", pos=(0, (y0 + y1) / 2 + 0.2, (z0 + z1) / 2),
              rot=(-math.degrees(math.atan2(y1 - y0, z1 - z0)), 0, 0))
        h.box((0.08, 0.06, math.hypot(y1 - y0, z1 - z0) + 0.05), "gold", pos=(0, (y0 + y1) / 2 + 0.42, (z0 + z1) / 2),
              rot=(-math.degrees(math.atan2(y1 - y0, z1 - z0)), 0, 0))
    h.box((0.09, 0.7, 0.9), "gold_engraved", pos=(0, -0.4, 5.05), top=(1, 0.6))
    h.spike((0, 0.12, 5.05), (0, 1, 0.35), 1.1, 0.13, "blade", sides=4)  # back hook
    h.loft([(5.5, diamond(0.13, 0.07)), (5.9, diamond(0.24, 0.06))], "blade", tip=(0, 0, 7.2))
    gem(h, (0, -0.15, 5.1), 0.12)
    gem(h, (0, 0.15, 5.1), 0.12)
    for k in range(6):  # tassel
        a = 2 * math.pi * k / 6
        h.spike((0.12 * math.cos(a), 0.12 * math.sin(a), 4.55), (0.25 * math.cos(a), 0.25 * math.sin(a), -1), 0.85,
                0.06, "cloth_royal", sides=4)
    w("Glow").box((0.04, 0.08, 1.0), "glow", pos=(0, 0, 6.3), top=(0.3, 1))
    return w


def eye_warhammer():
    """Paladin of the Eye: a colossal two-handed maul. A white-and-gold head the size of
    a chest, a glowing eye on each face, spikes, on a long gilded haft."""
    w = Weapon("EyeWarhammer", damage=46, cooldown=1.6, two_handed=True)
    haft(w, -2.0, 4.3, 0.1, color="plate_white", rings=(-1.9, -0.6, 0.8, 2.4, 3.9), ring_color="gold")
    h = w("Head")
    h.box((1.15, 1.9, 1.15), "gold_engraved", pos=(0, 0, 4.8))
    for s in (1, -1):
        h.box((1.3, 0.22, 1.3), "plate_white", pos=(0, s * 1.0, 4.8))  # striking faces
        h.box((1.4, 0.1, 1.4), "gold", pos=(0, s * 0.88, 4.8))
        h.box((0.12, 1.6, 1.0), "plate_white", pos=(s * 0.62, 0, 4.8), top=(1, 0.7))  # flanges
        for x in (-0.5, 0.5):
            for z in (4.3, 5.3):
                h.spike((x, s * 1.1, z), (x, s * 0.6, z - 4.8), 0.3, 0.07, "gold", sides=4)
    h.spike((0, 0, 5.4), (0, 0, 1), 1.0, 0.2, "gold", sides=4)  # top spike
    tube(h, 4.1, 4.25, 0.25, 0.25, "gold", sides=8)
    g = w("Glow")
    for s in (1, -1):  # the eye on both faces, with rays
        g.box((0.75, 0.05, 0.2), "glow", pos=(0, s * 1.12, 4.8))
        g.box((0.34, 0.06, 0.34), "glow", pos=(0, s * 1.13, 4.8), rot=(0, 45, 0))
        for k in range(8):
            a = 2 * math.pi * k / 8
            g.box((0.06, 0.05, 0.2), "glow", pos=(0.5 * math.cos(a), s * 1.12, 4.8 + 0.5 * math.sin(a)),
                  rot=(0, -math.degrees(a) + 90, 0))
    return w


def moon_blade():
    """The Prince's moon blade: a long crescent saber of black steel with a violet glowing
    edge and a gold crescent guard. He wields a pair (one in each hand)."""
    w = Weapon("MoonBlade", damage=32, cooldown=0.55, glow=PURPLE_HOT)
    w.dual = True
    band(w("Handle"), -0.5, 0.5, 0.09, 0.09, 0.03, "cloth_royal")
    for z in (-0.3, 0.1, 0.4):
        band(w("Handle"), z - 0.035, z + 0.035, 0.11, 0.11, 0.03, "gold")
    b, g = w("Blade"), w("Glow")
    x, z, ang = 0.0, 0.72, 0.0
    n = 14
    for k in range(n):
        t = k / n
        seg = 0.4
        wd = 0.5 * (1 - t) ** 0.6 + 0.07
        ang += 3.0
        ca = math.radians(ang)
        cx, cz = x - math.sin(ca) * seg / 2, z + math.cos(ca) * seg / 2
        b.box((wd, 0.08, seg + 0.04), "blade_dark", pos=(cx, 0, cz), rot=(0, -ang, 0), top=(0.93, 0.9))
        g.box((0.06, 0.09, seg + 0.04), "glow", pos=(cx + math.cos(ca) * wd / 2, 0, cz + math.sin(ca) * wd / 2),
              rot=(0, -ang, 0))
        if k % 4 == 1:  # crystal thorns on the spine
            g.spike((cx - math.cos(ca) * wd / 2, 0, cz - math.sin(ca) * wd / 2), (-math.cos(ca), 0, -math.sin(ca) + 0.4),
                    0.28, 0.05, "glow", sides=4)
        x, z = x - math.sin(ca) * seg, z + math.cos(ca) * seg
    b.spike((x, 0, z), (-math.sin(math.radians(ang + 10)), 0, math.cos(math.radians(ang + 10))), 0.6, 0.07,
            "blade_dark", sides=4)
    gd = w("Guard")
    arc_boxes(gd, (0, 1.05), 0.6, 200, 340, 8, (0.14, 0.22), "gold_engraved")  # crescent moon guard
    for s in (1, -1):
        gd.spike((s * 0.58, 0, 0.88), (s, 0, 0.9), 0.35, 0.07, "gold", sides=4)
    gd.box((0.34, 0.24, 0.24), "gold", pos=(0, 0, 0.6))
    gem(gd, (0, -0.15, 0.6), 0.1, color="glow")
    pm = w("Pommel")
    pm.loft([(-0.55, diamond(0.1, 0.1)), (-0.7, diamond(0.17, 0.17))], "gold_engraved", tip=(0, 0, -1.0))
    return w


def moon_spear():
    """The Prince's spear: a long black-and-gold glaive whose head is a crescent moon
    around a long blade, edged in violet light."""
    w = Weapon("MoonSpear", damage=34, cooldown=0.9, two_handed=True, glow=PURPLE_HOT)
    haft(w, -2.0, 5.0, 0.08, color="black", rings=(-1.9, -0.2, 1.6, 4.5), ring_color="gold")
    h, g = w("Head"), w("Glow")
    tube(h, 4.6, 5.3, 0.12, 0.11, "gold_engraved", sides=8)
    arc_boxes(h, (0, 5.75), 0.75, 200, 340, 9, (0.14, 0.12), "blade_dark")  # crescent
    arc_boxes(g, (0, 5.75), 0.84, 205, 335, 9, (0.05, 0.13), "glow")
    for s in (1, -1):
        h.spike((s * 0.72, 0, 5.6), (s * 0.6, 0, 1), 0.7, 0.08, "blade_dark", sides=4)  # moon horns
    h.loft([(5.3, diamond(0.14, 0.07)), (5.9, diamond(0.26, 0.06)), (6.8, diamond(0.16, 0.045))], "blade_dark",
           tip=(0, 0, 7.6))
    g.box((0.04, 0.08, 1.6), "glow", pos=(0, 0, 6.4), top=(0.3, 1))
    gem(h, (0, -0.13, 5.0), 0.1, color="glow")
    for k in range(4):
        g.spike((0, 0.1, 4.7 - 0.25 * k), (0.4 * (-1) ** k, 1, 0.3), 0.3, 0.05, "glow", sides=4)
    return w


# ---------------------------------------------------------------------------
# Weapons of the heavily infected elites: crystal has overgrown the steel.
def crystal_burst(w, center, count, seed, length=(0.3, 0.8), spread=0.25, radius=(0.06, 0.13), up=0.3):
    cluster(w, center, count, seed, spread=spread, length=length, radius=radius, up=up)


def blight_scythe():
    """Blighted villager: a huge scythe whose blade is half crystal."""
    w = Weapon("BlightScythe", damage=30, cooldown=1.3, two_handed=True)
    haft(w, -1.8, 4.2, 0.08, rings=(0.8, 3.9), ring_color="leather_strap")
    w("Handle").box((0.09, 0.42, 0.09), "wood", pos=(0, -0.25, 1.2))
    b, g = w("Blade"), w("Glow")
    prev = (0.0, 4.15)
    for k in range(1, 14):
        t = k / 13
        y, z = -3.0 * t, 4.15 + 0.6 * math.sin(t * math.pi * 0.9) - 0.35 * t
        ang = math.degrees(math.atan2(z - prev[1], y - prev[0]))
        mid = ((y + prev[0]) / 2, (z + prev[1]) / 2)
        L = math.hypot(y - prev[0], z - prev[1]) + 0.05
        b.box((0.05, L, 0.36 * (1 - t) + 0.06), "blade_corrupt", pos=(0, mid[0], mid[1] - 0.14), rot=(ang, 0, 0))
        g.box((0.06, L, 0.05), "glow", pos=(0, mid[0], mid[1] - 0.3 * (1 - t) - 0.04), rot=(ang, 0, 0))
        if k % 2 == 0:  # crystal teeth along the edge
            g.spike((0, mid[0], mid[1] - 0.3 * (1 - t) - 0.06), (0, 0.3, -1), 0.3 * (1 - t) + 0.12, 0.05, "glow", sides=4)
        prev = (y, z)
    crystal_burst(w, (0, 0, 4.1), 7, 21)
    crystal_burst(w, (0, 0, 2.2), 4, 22, length=(0.2, 0.45), spread=0.1)
    return w


def crystal_maul():
    """Blighted woodcutter: a sledge whose head has erupted into a crystal cluster."""
    w = Weapon("CrystalMaul", damage=40, cooldown=1.6, two_handed=True)
    haft(w, -1.0, 3.6, 0.1, rings=(-0.9, 3.0), ring_color="iron")
    h = w("Head")
    h.box((0.9, 1.4, 0.9), "plate_corrupt_heavy", pos=(0, 0, 3.75))
    for s in (1, -1):
        h.box((1.0, 0.15, 1.0), "iron", pos=(0, s * 0.72, 3.75))
    crystal_burst(w, (0, 0, 4.1), 12, 23, length=(0.6, 1.4), spread=0.35, radius=(0.1, 0.2), up=0.5)
    crystal_burst(w, (0, -0.7, 3.75), 5, 24, length=(0.4, 0.8), spread=0.3, up=-0.3)
    crystal_burst(w, (0, 0, 2.6), 4, 25, length=(0.2, 0.5), spread=0.1)
    return w


def blight_greatsword():
    """Blighted knight: a greatsword the corruption has split open - crystal shards
    grow out of the cracked blade."""
    w = Weapon("BlightGreatsword", damage=40, cooldown=1.1, two_handed=True)
    long_grip(w, -0.7, 0.6, ring="plate_dark")
    b = w("Blade")
    b.loft([(0.9, diamond(0.42, 0.08)), (3.0, diamond(0.46, 0.08)), (5.6, diamond(0.36, 0.06))], "blade_corrupt",
           tip=(0.1, 0, 6.6))
    w("Guard").box((1.5, 0.3, 0.26), "plate_corrupt_heavy", pos=(0, 0, 0.8))
    for s in (1, -1):
        w("Guard").spike((s * 0.75, 0, 0.8), (s, 0, 0.5), 0.5, 0.1, "plate_corrupt_heavy", sides=4)
    w("Glow").box((0.06, 0.18, 4.4), "glow", pos=(0, 0, 3.2), top=(0.3, 1))
    rnd = random.Random(26)
    for _ in range(14):  # shards breaking out of both edges
        z = rnd.uniform(1.2, 5.4)
        s = rnd.choice((1, -1))
        w("Glow").spike((s * 0.38, 0, z), (s, rnd.uniform(-0.4, 0.4), rnd.uniform(0.2, 1.2)), rnd.uniform(0.3, 0.75),
                        rnd.uniform(0.06, 0.11), "glow", sides=5)
    crystal_burst(w, (0, 0, 1.0), 6, 27, length=(0.3, 0.7))
    blob(w("Pommel"), (0, 0, -0.85), (0.16, 0.16, 0.16), "plate_corrupt_heavy", sides=6, rings=3)
    return w


def crystal_war_axe():
    """Blighted knight: a double-bitted war axe with crystal blades."""
    w = Weapon("CrystalWarAxe", damage=42, cooldown=1.3, two_handed=True)
    haft(w, -1.2, 4.2, 0.09, color="plate_dark", rings=(-1.1, 1.0, 3.2), ring_color="plate_corrupt_heavy")
    h, g = w("Head"), w("Glow")
    for s in (1, -1):  # two bits, -Y and +Y
        outline = [(0.0, 0.35), (0.7, 0.55), (1.3, 1.0), (1.3, -1.0), (0.7, -0.55), (0.0, -0.35)]
        prof = [(-up, -s * across) for across, up in outline]
        h.loft([(-0.07, prof), (0.07, prof)], "plate_corrupt_heavy", pos=(0, 0, 3.6), rot=(0, 90, 0))
        for k in range(5):  # crystal edge
            zz = 3.6 - 0.9 + 0.45 * k
            g.spike((0, s * 1.3, zz), (0, s, 0.2 * (k - 2)), 0.35, 0.07, "glow", sides=4)
    h.spike((0, 0, 4.2), (0, 0, 1), 0.8, 0.12, "plate_corrupt_heavy", sides=4)
    crystal_burst(w, (0, 0, 3.6), 8, 28, length=(0.4, 0.9))
    return w


def sickle_blade(p, base, d0, n, length, width, bend, color, thick=0.05, segs=10, edge=None):
    """A curved, single-edged blade (dragoon fins, lance wings) built as one continuous
    surface: a spine bending by `bend` degrees around the axis n, the blade widening out
    to one side and tapering to a point. edge (a tile) adds a bright outer cutting edge."""
    from mathutils import Matrix, Vector
    d, n = Vector(d0).normalized(), Vector(n).normalized()
    pos = Vector(base)
    spine, perps, widths = [], [], []
    seg = length / segs
    for k in range(segs + 1):
        t = k / segs
        spine.append(pos.copy())
        perps.append(n.cross(d).normalized())
        widths.append(width * math.sin(math.pi * min(1.0, 0.15 + t * 0.95)) ** 0.7 * (1 - t) ** 0.35 + 0.0)
        pos = pos + d * seg
        d = Matrix.Rotation(math.radians(bend / segs), 3, n) @ d

    def strip(w0, w1, tile, th):
        verts, faces = [], []
        for c, pp, wd in zip(spine, perps, widths):
            for off in (w0(wd), w1(wd)):
                for s in (1, -1):
                    verts.append(tuple(c + pp * off + n * s * th / 2))
        m = len(spine)
        for i in range(m - 1):
            a, b = 4 * i, 4 * (i + 1)
            faces.append((a, a + 2, b + 2, b))  # front face (+n)
            faces.append((a + 1, b + 1, b + 3, a + 3))  # back face
            faces.append((a + 2, a + 3, b + 3, b + 2))  # outer edge
            faces.append((a, b, b + 1, a + 1))  # inner edge
        faces.append((0, 1, 3, 2))
        last = 4 * (m - 1)
        faces.append((last, last + 2, last + 3, last + 1))
        p._faces(verts, faces, tile)

    strip(lambda wd: 0.0, lambda wd: wd, color, thick)
    if edge:
        strip(lambda wd: wd - 0.005, lambda wd: wd + 0.05 * min(1.0, wd / max(widths) * 3), edge, thick * 0.7)


def dragon_lance():
    """The Dragon Knight's lance: a long dark lance with a great leaf blade swept by
    curved wings, a crescent blade at the butt and a red cord."""
    w = Weapon("DragonLance", damage=38, cooldown=0.85, two_handed=True, glow=DRAGON_GLOW)
    haft(w, -2.6, 5.4, 0.08, color="plate_black", rings=(-2.5, -0.6, 1.4, 5.2), ring_color="blade")
    h, g = w("Head"), w("Glow")
    tube(h, 5.3, 5.8, 0.13, 0.11, "plate_black", sides=8)
    h.loft([(5.8, diamond(0.14, 0.07)), (6.3, diamond(0.34, 0.07)), (7.4, diamond(0.18, 0.05))], "blade_dark",
           tip=(0, 0, 8.5))
    g.box((0.04, 0.08, 2.0), "glow", pos=(0, 0, 6.9), top=(0.3, 1))
    for s in (1, -1):  # swept wings at the base of the head
        sickle_blade(h, (s * 0.12, 0, 5.6), (s * 1, 0, 0.35), (0, -s, 0), 1.4, 0.5, 70, "plate_black", edge="blade")
        sickle_blade(h, (s * 0.12, 0, 6.0), (s * 1, 0, 0.9), (0, -s, 0), 0.9, 0.3, 50, "plate_black", edge="blade")
        g.box((0.03, 0.06, 0.6), "glow", pos=(s * 0.45, 0, 5.85), rot=(0, s * -60, 0))
    # Crescent blade at the butt, sweeping one way.
    sickle_blade(h, (0.05, 0, -2.4), (1, 0, -0.6), (0, -1, 0), 1.8, 0.6, -110, "plate_black", edge="blade")
    h.spike((0, 0, -2.6), (0, 0, -1), 0.6, 0.08, "blade_dark", sides=4)
    for k in range(4):  # red cord hanging below the head
        h.spike((0.08, 0, 5.2 - 0.5 * k), (0.3, 0.2, -1), 0.55, 0.035, "cloth_royal", sides=4)
    return w


def all_weapons():
    return ([pitchfork(), hoe(), spade(), sickle(), scythe(), hunter_bow(), woodcutter_axe(), wolf_rider_spear(), onehorn_greatsword()]
            + [tier_axe(t) for t in ("Apprentice", "Mid", "High")]
            + [tier_sword(t) for t in ("Apprentice", "Mid", "High")]
            + [spear(), dragon_slayer(), serrated_spear(), serrated_sword(), serrated_cleaver()]
            + [radiant_greatsword(), abyss_greatsword(), royal_halberd(), eye_warhammer(), moon_blade(),
               moon_spear()]
            + [blight_scythe(), crystal_maul(), blight_greatsword(), crystal_war_axe(), dragon_lance()])

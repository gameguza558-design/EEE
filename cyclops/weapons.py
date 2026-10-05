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


def radiant_greatsword():
    """White Knight: a great holy blade with winged gold guard, a red gem and a glowing rune."""
    w = Weapon("RadiantGreatsword", damage=38, cooldown=0.95, glow=GOLD_LIGHT)
    band(w("Handle"), -0.5, 0.5, 0.1, 0.1, 0.03, "cloth_royal")
    for z in (-0.35, 0.0, 0.35):
        band(w("Handle"), z - 0.04, z + 0.04, 0.12, 0.12, 0.03, "gold")
    b = w("Blade")
    b.loft([(0.75, diamond(0.36, 0.07)), (1.4, diamond(0.4, 0.075)), (3.8, diamond(0.36, 0.065)),
            (4.8, diamond(0.26, 0.05))], "blade", tip=(0, 0, 5.7))
    b.box((0.16, 0.16, 2.6), "gold_engraved", pos=(0, 0, 2.2), top=(0.6, 1))  # engraved fuller
    for s in (1, -1):  # ricasso langets
        b.box((0.08, 0.18, 0.5), "gold", pos=(s * 0.34, 0, 0.95), top=(0.5, 1))
    g = w("Glow")
    g.box((0.05, 0.19, 2.2), "glow", pos=(0, 0, 2.3), top=(0.3, 1))  # holy rune line
    for z in (1.4, 2.1, 2.8):
        g.box((0.14, 0.2, 0.05), "glow", pos=(0, 0, z), rot=(0, 45, 0))
    gd = w("Guard")
    gd.box((0.5, 0.26, 0.26), "gold_engraved", pos=(0, 0, 0.62))
    wing_guard(gd, 0.62, 0.85)
    gem(gd, (0, -0.14, 0.62), 0.12)
    gem(gd, (0, 0.14, 0.62), 0.12)
    pm = w("Pommel")
    pm.loft([(-0.55, diamond(0.1, 0.1)), (-0.7, diamond(0.2, 0.2)), (-0.85, diamond(0.1, 0.1))], "gold_engraved",
            base=(0, 0, -1.05))
    gem(pm, (0, 0, -0.7), 0.1)
    return w


def abyss_greatsword():
    """Black Knight: one of a pair of long black greatswords (wielded in both hands)."""
    w = Weapon("AbyssGreatsword", damage=30, cooldown=0.8, glow=EMBER)
    w.dual = True
    band(w("Handle"), -0.5, 0.45, 0.09, 0.09, 0.03, "leather_strap")
    for z in (-0.3, 0.05, 0.35):
        band(w("Handle"), z - 0.035, z + 0.035, 0.11, 0.11, 0.03, "gold")
    b = w("Blade")
    b.loft([(0.65, diamond(0.3, 0.07)), (1.3, diamond(0.34, 0.07)), (4.2, diamond(0.3, 0.06)),
            (5.0, diamond(0.2, 0.045))], "blade_dark", tip=(0, 0, 5.8))
    b.box((0.12, 0.15, 3.6), "gold_engraved", pos=(0, 0, 2.6), top=(0.5, 1))  # gold spine
    g = w("Glow")
    for s in (1, -1):  # ember edge lines
        g.box((0.035, 0.12, 3.4), "glow", pos=(s * 0.25, 0, 2.6), rot=(0, s * -0.7, 0), top=(0.5, 1))
    gd = w("Guard")
    gd.box((0.95, 0.24, 0.2), "plate_black", pos=(0, 0, 0.55))
    gd.box((1.0, 0.27, 0.06), "gold", pos=(0, 0, 0.66))
    for s in (1, -1):  # horned guard curving toward the blade
        gd.spike((s * 0.45, 0, 0.55), (s * 0.7, 0, 1), 0.55, 0.1, "gold", sides=4)
        gd.spike((s * 0.45, 0, 0.5), (s * 1, 0, -0.5), 0.35, 0.08, "plate_black", sides=4)
    gem(gd, (0, -0.13, 0.55), 0.1)
    gem(gd, (0, 0.13, 0.55), 0.1)
    pm = w("Pommel")
    pm.loft([(-0.52, diamond(0.12, 0.12)), (-0.66, diamond(0.18, 0.18))], "gold", tip=(0, 0, -1.0))
    return w


def royal_halberd():
    """Royal Guard: gilded halberd with a crescent axe, a long spike and a red tassel."""
    w = Weapon("RoyalHalberd", damage=26, cooldown=1.0, two_handed=True, glow=GOLD_LIGHT)
    haft(w, -1.6, 3.4, 0.07, color="black", rings=(-1.5, 0.5, 2.8), ring_color="gold")
    h = w("Head")
    tube(h, 3.2, 3.75, 0.11, 0.1, "gold_engraved", sides=8)
    # Crescent axe blade on -Y.
    pts = []
    for k in range(9):
        a = math.radians(-70 + 140 * k / 8)
        pts.append((-0.25 - 0.85 * math.cos(a) * 0.9, 3.45 + 0.75 * math.sin(a)))
    for (y0, z0), (y1, z1) in zip(pts, pts[1:]):
        h.box((0.05, 0.3, math.hypot(y1 - y0, z1 - z0) + 0.04), "blade", pos=(0, (y0 + y1) / 2 + 0.13, (z0 + z1) / 2),
              rot=(-math.degrees(math.atan2(y1 - y0, z1 - z0)), 0, 0))
    h.box((0.07, 0.5, 0.6), "gold_engraved", pos=(0, -0.3, 3.45), top=(1, 0.7))
    h.spike((0, 0.1, 3.45), (0, 1, 0.25), 0.75, 0.1, "blade", sides=4)  # back spike
    h.loft([(3.75, diamond(0.1, 0.06)), (4.05, diamond(0.17, 0.05))], "blade", tip=(0, 0, 4.9))
    gem(h, (0, -0.12, 3.5), 0.09)
    gem(h, (0, 0.12, 3.5), 0.09)
    for k in range(5):  # tassel
        a = 2 * math.pi * k / 5
        h.spike((0.1 * math.cos(a), 0.1 * math.sin(a), 3.15), (0.25 * math.cos(a), 0.25 * math.sin(a), -1), 0.6, 0.05,
                "cloth_royal", sides=4)
    w("Glow").spike((0, 0, 4.4), (0, 0, 1), 0.3, 0.03, "glow", sides=4)
    return w


def eye_warhammer():
    """Paladin of the Eye: a white-and-gold warhammer whose face is a glowing eye."""
    w = Weapon("EyeWarhammer", damage=30, cooldown=1.15, two_handed=True)
    haft(w, -1.3, 2.8, 0.075, color="plate_white", rings=(-1.2, 0.3, 2.3), ring_color="gold")
    h = w("Head")
    h.box((0.55, 0.95, 0.55), "gold_engraved", pos=(0, 0, 3.05))
    for s in (1, -1):  # flanges
        h.box((0.08, 0.7, 0.75), "plate_white", pos=(s * 0.3, 0, 3.05), top=(1, 0.6))
    h.box((0.62, 0.12, 0.62), "plate_white", pos=(0, -0.5, 3.05))  # striking face
    h.spike((0, 0.45, 3.05), (0, 1, 0.3), 0.7, 0.16, "gold", sides=4)  # back beak
    h.spike((0, 0, 3.32), (0, 0, 1), 0.6, 0.12, "gold", sides=4)  # top spike
    g = w("Glow")
    g.box((0.42, 0.04, 0.12), "glow", pos=(0, -0.57, 3.05))
    g.box((0.2, 0.05, 0.2), "glow", pos=(0, -0.58, 3.05), rot=(0, 45, 0))
    for k in range(6):  # rays around the eye
        a = 2 * math.pi * k / 6
        g.box((0.04, 0.03, 0.12), "glow", pos=(0.24 * math.cos(a), -0.57, 3.05 + 0.24 * math.sin(a)),
              rot=(0, -math.degrees(a) + 90, 0))
    return w


def eclipse_saber():
    """The Prince's curved saber: a navy crescent blade with a glowing cyan edge, a gold
    crescent-moon guard and a golden eye gem."""
    w = Weapon("EclipseSaber", damage=34, cooldown=0.6, glow=CYAN)
    band(w("Handle"), -0.4, 0.4, 0.085, 0.085, 0.03, "cloth_royal")
    for z in (-0.25, 0.15):
        band(w("Handle"), z - 0.035, z + 0.035, 0.1, 0.1, 0.03, "gold")
    b, g = w("Blade"), w("Glow")
    # Curved blade: short tapered segments bending toward -X.
    x, z, ang = 0.0, 0.62, 0.0
    n = 12
    for k in range(n):
        t = k / n
        seg = 0.37
        wd = 0.36 * (1 - t) ** 0.5 + 0.06
        ang += 2.6
        ca = math.radians(ang)
        cx, cz = x - math.sin(ca) * seg / 2, z + math.cos(ca) * seg / 2
        b.box((wd, 0.07, seg + 0.03), "plate_navy", pos=(cx, 0, cz), rot=(0, -ang, 0), top=(0.92, 0.9))
        g.box((0.05, 0.08, seg + 0.03), "glow", pos=(cx + math.cos(ca) * wd / 2, 0, cz + math.sin(ca) * wd / 2),
              rot=(0, -ang, 0))
        x, z = x - math.sin(ca) * seg, z + math.cos(ca) * seg
    b.spike((x, 0, z), (-math.sin(math.radians(ang + 10)), 0, math.cos(math.radians(ang + 10))), 0.5, 0.06,
            "plate_navy", sides=4)
    gd = w("Guard")
    # Crescent-moon guard.
    for k in range(9):
        a = math.radians(200 + 140 * k / 8)
        gd.box((0.14, 0.18, 0.1), "gold_engraved", pos=(0.5 * math.cos(a), 0, 0.85 + 0.35 * math.sin(a)),
               rot=(0, -math.degrees(a) - 90, 0))
    gd.box((0.3, 0.22, 0.2), "gold", pos=(0, 0, 0.55))
    gem(gd, (0, -0.13, 0.55), 0.09, color="gold")
    g.box((0.1, 0.05, 0.1), "glow", pos=(0, -0.2, 0.55), rot=(0, 45, 0))
    pm = w("Pommel")
    pm.loft([(-0.45, diamond(0.1, 0.1)), (-0.58, diamond(0.16, 0.16))], "gold_engraved", tip=(0, 0, -0.85))
    return w


def all_weapons():
    return ([pitchfork(), hoe(), spade(), sickle(), scythe(), hunter_bow(), woodcutter_axe(), wolf_rider_spear(), onehorn_greatsword()]
            + [tier_axe(t) for t in ("Apprentice", "Mid", "High")]
            + [tier_sword(t) for t in ("Apprentice", "Mid", "High")]
            + [spear(), dragon_slayer(), serrated_spear(), serrated_sword(), serrated_cleaver()]
            + [radiant_greatsword(), abyss_greatsword(), royal_halberd(), eye_warhammer(),
               eclipse_saber()])

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
def pitchfork():
    w = Weapon("Pitchfork", damage=10, cooldown=0.9, two_handed=True)
    haft(w, -1.2, 2.4, 0.07, rings=(2.35,))
    h = w("Head")
    h.box((0.62, 0.08, 0.1), "iron", pos=(0, 0, 2.45))
    for x in (-0.28, 0.0, 0.28):
        tube(h, 2.45, 3.1, 0.03, 0.025, "iron", sides=4, pos=(x, 0, 0))
        h.spike((x, 0, 3.1), (0, 0, 1), 0.18, 0.03, "iron", sides=4)
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
        return sword("MidSword", 3.0, 0.2, damage=20, glow_count=2)
    w = sword("HighSword", 3.4, 0.23, blade="blade_corrupt", guard="gold", grip="leather_strap",
              pommel="gold", damage=27, glow_count=8, quillon=0.7)
    for s in (1, -1):
        w("Guard").spike((s * 0.55, 0, 0.42), (s * 0.4, 0, 1), 0.3, 0.05, "gold", sides=4)
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


def all_weapons():
    return ([pitchfork(), hunter_bow(), woodcutter_axe(), wolf_rider_spear(), onehorn_greatsword()]
            + [tier_axe(t) for t in ("Apprentice", "Mid", "High")]
            + [tier_sword(t) for t in ("Apprentice", "Mid", "High")])

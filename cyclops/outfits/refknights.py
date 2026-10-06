"""The five helmed knights, each built after its own reference image - its own helm, its
own pauldrons, chest, waist and silhouette. Only the low-level shapes are shared.

    KnightWhite         <- silver knight: crested close helm, big rounded lamed pauldrons,
                           blue gem on the left breast, long cloth panels, cape on one shoulder
    KnightBlack         <- black knight in the forest: round-topped helm with a flat visor
                           and a white plume, many-lamed pauldrons edged in silver, a
                           baldric across the chest, long tassets (+ the red cape)
    KnightRoyalGuard    <- Artorias: narrow helm with a long plume, one huge right
                           pauldron, ribbed arms, chainmail skirt, tattered blue scarf
    KnightPaladin       <- hooded knight: deep hood over a black void, dark plate with
                           engraved gold, fringed pauldrons, chainmail sleeves, crossed strap
    CyclopsDragonKnight <- dragoon: beaked helm with a mane of blades, slim plate, blades
                           sweeping back from every joint

Plates get thickness and a rolled rim on their lower edge, and overlap, so they read in
depth instead of as flat shells. Every helm sits close to the head: seen from the side
the face is flush, nothing juts out like a snout.
"""
import math

from mathutils import Vector

from kit import blob
from outfits.common import Outfit
from outfits.parade import cape as lofted_cape
from outfits.parade import curved_plate, fin, lens, pipe, rshell, sweep, trim


def boxy(piece, rings, col, **kw):
    """Rounded shell squared enough to cover the R15 parts' box corners."""
    kw.setdefault("p", 4.2)
    rshell(piece, rings, col, **kw)

OUTER = {1: (-25, 205), -1: (-205, 25)}  # angles covering the outer side of an arm


# ---------------------------------------------------------------------------
# Shared low-level shapes
def rimmed(piece, c, r, a0, a1, z0, z1, col, rim, flare=0.1, thick=0.07, n=12, rot=(0, 0, 0)):
    """A curved plate with thickness and a rolled rim along its lower edge."""
    curved_plate(piece, c, r, a0, a1, z0, z1, col, thick=thick, flare=flare, n=n, rot=rot)
    curved_plate(piece, c, r + flare + 0.022, a0 - 1, a1 + 1, z0 - 0.015, z0 + 0.045, rim, thick=thick + 0.035, n=n,
                 rot=rot)


def band(piece, z0, z1, r0, r1, col, rim=None, keel=0.0):
    """A lame running all the way round a limb, flaring from r1 (top) to r0 (bottom)."""
    boxy(piece, [(z0, r0, r0, {"keel": keel}), (z1, r1, r1, {"keel": keel})], col)
    if rim:
        trim(piece, z0 + 0.02, r0 + 0.022, r0 + 0.022, rim, h=0.04, keel=keel, p=4.2)


def pauldron(ua, side, size, count, cols, rim, dome=True, peak=0.15, out=0.0, step=None, height=None, flare=0.08,
             tilt=16, fringe=None, reach=-0.45):
    """A pauldron that hugs the shoulder: a dome over lames that wrap the outside of the
    upper arm and overlap downward like shingles, each sloping down toward the outside
    and finished with a rolled rim. The last lame reaches `reach` (toward the elbow)."""
    if dome:
        rshell(ua, [(0.18, 0.7 * size, 0.66 * size, {"dx": out + side * 0.08}),
                    (0.5, 0.66 * size, 0.62 * size, {"dx": out + side * 0.05}),
                    (0.74, 0.46 * size, 0.46 * size, {"dx": out})], cols[0], p=2.0,
               tip=(out - side * peak, 0, 0.84 + 0.05 * size))
        trim(ua, 0.19, 0.72 * size, 0.68 * size, rim, h=0.05, dx=out + side * 0.08)
    a0, a1 = OUTER[side]
    top = 0.3
    height = height or (top - reach) / count * 1.45
    step = step or (top - reach - height) / max(1, count - 1)
    for i in range(count):
        z1 = top - step * i
        z0 = z1 - height
        r = (0.68 + 0.035 * i) * size
        c = (out + side * (0.08 + 0.03 * i), 0.0)
        rimmed(ua, c, r, a0, a1, z0, z1, cols[(i + 1) % len(cols)], rim, flare=flare, rot=(0, side * tilt, 0))
        if fringe and i == count - 1:
            for k in range(13):  # a fringe hanging under the last lame
                a = math.radians(a0 + (a1 - a0) * (k + 0.5) / 13)
                x, y = c[0] + (r + flare) * math.sin(a), -(r + flare) * math.cos(a)
                ua.spike((x, y, z0 - side * math.tan(math.radians(tilt)) * (x - c[0])), (0, 0, -1), 0.26, 0.035, fringe,
                         sides=3)


def arm_plate(o, part, side, P, P2, rim, lames=2, cuff=0.12, ribs=0, chain=False, knuckles=True):
    ua, la, hand = o(part + "UpperArm"), o(part + "LowerArm"), o(part + "Hand")
    if chain:
        band(ua, -0.6, 0.55, 0.56, 0.56, "chainmail")
        band(la, -0.2, 0.5, 0.56, 0.56, "chainmail")
    elif ribs:
        band(ua, 0.05, 0.55, 0.56, 0.57, P)
        for i in range(ribs):  # ribbed rerebrace
            z1 = 0.1 - 0.7 * i / ribs
            band(ua, z1 - 0.7 / ribs - 0.02, z1, 0.6, 0.57, P if i % 2 else P2, rim)
    else:
        band(ua, -0.6, 0.55, 0.56, 0.57, P)
    # Couter with a side fan.
    lens(la, (0, 0.55, 0.42), (0, 1, 0.1), 0.34, 0.3, 0.16, P)
    lens(la, (side * 0.56, 0.0, 0.42), (side, 0, 0), 0.3, 0.26, 0.12, P2)
    vz0 = -0.32 if not chain else -0.35
    if ribs:
        for i in range(ribs):
            z1 = 0.32 - 0.62 * i / ribs
            band(la, z1 - 0.62 / ribs - 0.02, z1, 0.62, 0.59, P if i % 2 else P2, rim)
    else:
        band(la, vz0, 0.32 if not chain else 0.0, 0.6, 0.58, P)
        for i in range(lames):  # lames at the top of the vambrace
            z1 = 0.36 - 0.1 * i
            band(la, z1 - 0.12, z1, 0.63, 0.6, P2, rim)
    band(la, -0.53, -0.28, 0.6 + cuff, 0.6, P2, rim)  # flared cuff
    boxy(hand, [(-0.16, 0.55, 0.55), (0.12, 0.58, 0.58)], P)
    if knuckles:
        for x in (-0.3, -0.1, 0.1, 0.3):
            lens(hand, (x, -0.56, -0.06), (0, -1, 0), 0.08, 0.07, 0.06, P2, n=8)


def leg_plate(o, part, side, P, P2, rim, knee=None, fan=True, point=0.3, lines=None, cuisse_lames=2):
    ul, ll, foot = o(part + "UpperLeg"), o(part + "LowerLeg"), o(part + "Foot")
    band(ul, -0.3, 0.55, 0.58, 0.6, P)
    for i in range(cuisse_lames):  # lames running down to the knee
        z1 = -0.3 - 0.13 * i
        band(ul, z1 - 0.16, z1 + 0.02, 0.61, 0.59, P2 if i % 2 == 0 else P, rim)
    if lines:
        for s in (1, -1):
            pipe(ul, [(s * 0.32, -0.6, 0.5), (s * 0.2, -0.62, -0.1), (s * 0.08, -0.6, -0.5)], lines)
    lens(ll, (0, -0.6, 0.5), (0, -1, 0.1), 0.4, 0.34, 0.2, knee or P)
    if fan:
        for s in (1, -1):
            lens(ll, (s * 0.5, -0.4, 0.5), (s, -0.6, 0), 0.27, 0.25, 0.1, P2)
    boxy(ll, [(-0.6, 0.58, 0.6, {"keel": 0.08}), (0.36, 0.6, 0.62, {"keel": 0.1})], P)
    trim(ll, 0.34, 0.62, 0.64, rim, h=0.05, keel=0.1, p=4.2)
    pipe(ll, [(0, -0.72, 0.28), (0, -0.69, -0.55)], P2, w=0.06)  # greave ridge
    boxy(foot, [(-0.2, 0.56, 0.62, {"keel": point, "dy": -0.08}), (0.12, 0.54, 0.56, {"keel": point * 0.6, "dy": -0.04}),
                  (0.22, 0.5, 0.5)], P)
    for i in range(3):
        trim(foot, 0.1 - 0.1 * i, 0.56 + 0.01 * i, 0.6 + 0.03 * i, rim if i == 0 else P2, h=0.05,
             keel=point * 0.7 + 0.05 * i, dy=-0.06)


def neck_lames(h, P, P2, rim):
    for i in range(3):
        rshell(h, [(-0.75 - 0.12 * i, 0.58 - 0.03 * i, 0.12, {"dy": 0.6 + 0.04 * i}),
                   (-0.6 - 0.12 * i, 0.62 - 0.03 * i, 0.12, {"dy": 0.58 + 0.04 * i})], P2 if i % 2 else P)


def gorget(t, P, P2, rim, high=0.0):
    for i in range(2):
        z = 0.72 + 0.14 * i
        rshell(t, [(z, 0.68 - 0.05 * i, 0.52 - 0.03 * i), (z + 0.18 + high, 0.6 - 0.05 * i, 0.46 - 0.03 * i)],
               P if i == 0 else P2)
        trim(t, z + 0.01, 0.69 - 0.05 * i, 0.53 - 0.03 * i, rim, h=0.04)


def slit(h, g, x0, x1, z, y, w=0.05, tilt=0.0, spin=0.0):
    cx, L = (x0 + x1) / 2, abs(x1 - x0)
    h.box((L + 0.06, 0.06, w + 0.05), "black", pos=(cx, y + 0.02, z), rot=(0, tilt, spin))
    g.box((L, 0.04, w), "glow", pos=(cx, y - 0.01, z), rot=(0, tilt, spin))


def breastplate(t, P, keel=0.1, waist=1.04):
    boxy(t, [(-0.8, waist, 0.6, {"keel": keel * 0.4}), (-0.2, waist + 0.04, 0.63, {"keel": keel * 0.7}),
               (0.35, 1.12, 0.67, {"keel": keel}), (0.74, 1.08, 0.62, {"keel": keel * 0.5}), (0.92, 0.86, 0.52)], P)


def faulds(lt, P, P2, rim, count=2):
    for i in range(count):
        z1 = 0.0 - 0.18 * i
        boxy(lt, [(z1 - 0.24, 1.12 + 0.03 * i, 0.68 + 0.02 * i), (z1, 1.09 + 0.03 * i, 0.66 + 0.02 * i)],
             P if i % 2 == 0 else P2)
        trim(lt, z1 - 0.23, 1.14 + 0.03 * i, 0.7 + 0.02 * i, rim, h=0.04, p=4.2)


def tassets(lt, P, P2, rim, z_top=-0.3, rows=2, length=0.45, arcs=((-55, 35), (50, 115)), r=0.74):
    for s in (1, -1):
        for a0, a1 in arcs:
            if s < 0:
                a0, a1 = -a1, -a0
            for i in range(rows):
                z1 = z_top - length * 0.8 * i
                rimmed(lt, (s * 0.5, 0.0), r + 0.03 * i, a0, a1, z1 - length, z1, P if i % 2 == 0 else P2, rim,
                       flare=0.1)


def plume(seed, colors_unused=None, count=8, root=(0, 0.25, 1), aim=(0, 1, 0.4), length=1.6, width=0.2,
          gravity=0.6, pad=0.42, spread=0.25):
    import hair
    pl = hair.HairBuilder(seed)
    pl.chunky = True
    pl.pad = pad
    rnd = pl.rnd
    for k in range(count):
        t = (k / max(1, count - 1)) - 0.5
        pl.clump(Vector((root[0] + t * spread, root[1], root[2])), length * rnd.uniform(0.85, 1.1), width,
                 gravity=gravity, aim=(aim[0] + t * spread * 1.5, aim[1], aim[2]), thickness=0.45, taper=1.2,
                 segments=9, twist=rnd.uniform(-0.3, 0.3))
    return pl.finish()


# ---------------------------------------------------------------------------
# 1. White Knight (silver knight)
def white(name, glow):
    o = Outfit(name, glow=glow, seed=61)
    P, P2, R = "plate_white", "blade", "blade"
    h, g = o("Head"), o("Head", "Glow")
    # Close helm: the visor is part of the shell, keeled to a gentle point - flush in profile.
    rshell(h, [(-0.62, 0.56, 0.6, {"keel": 0.1}), (-0.2, 0.58, 0.63, {"keel": 0.15}), (0.25, 0.58, 0.62, {"keel": 0.13}),
               (0.62, 0.47, 0.52, {"keel": 0.08}), (0.88, 0.22, 0.3)], P, tip=(0, -0.02, 1.02), p=3.0)
    trim(h, 0.33, 0.585, 0.625, P2, h=0.05, keel=0.13)  # visor pivot line
    for s in (1, -1):
        slit(h, g, s * 0.06, s * 0.46, 0.15, -0.69, w=0.045, spin=s * 18)
        for k in range(3):  # breaths
            h.box((0.035, 0.05, 0.16), "black", pos=(s * (0.2 + 0.08 * k), -0.66 + 0.03 * k, -0.3), rot=(0, 0, s * 18))
        blob(h, (s * 0.6, -0.05, 0.28), (0.07, 0.1, 0.1), P2, sides=8, rings=3)  # visor pivots
    pipe(h, [(0, -0.8, 0.35), (0, -0.8, -0.55)], P2, w=0.05)
    for k in range(5):  # crested crown: flame-like fins swept back over the top
        t = k / 4
        fin(h, (0, -0.35 + 0.6 * t, 0.98 - 0.1 * t), (0, 0.8, 1), 0.55 - 0.15 * abs(t - 0.4), 0.025, 0.11, P)
    for s in (1, -1):
        for k in range(2):
            fin(h, (s * 0.3, -0.15 + 0.2 * k, 0.88), (s * 0.35, 0.8, 0.7), 0.5 - 0.12 * k, 0.1, 0.025, P, roll=90)
    neck_lames(h, P, P2, R)
    # Chest: smooth plate, a raised V plackart line, the blue gem high on the left breast.
    t, tg = o("UpperTorso"), o("UpperTorso", "Glow")
    breastplate(t, P)
    gorget(t, P, P2, R, high=0.04)
    for s in (1, -1):
        pipe(t, [(s * 0.95, -0.52, 0.65), (s * 0.55, -0.72, 0.1), (0, -0.8, -0.45)], P2, w=0.06, t=0.05)
    lens(t, (0.42, -0.68, 0.42), (0.25, -1, 0.1), 0.22, 0.24, 0.06, P2, n=12)
    lens(t, (0.43, -0.72, 0.42), (0.25, -1, 0.1), 0.15, 0.17, 0.1, "gem_blue", n=12)
    pipe(t, [(0, 0.72, 0.75), (0, 0.7, -0.75)], P2, w=0.07)
    for part, side in (("Left", 1), ("Right", -1)):
        pauldron(o(part + "UpperArm"), side, 1.12, 4, (P, P2), R, peak=0.2)
        arm_plate(o, part, side, P, P2, R, lames=2, cuff=0.16)
        leg_plate(o, part, side, P, P2, R, point=0.32)
    lt = o("LowerTorso")
    boxy(lt, [(-0.12, 1.08, 0.64), (0.2, 1.06, 0.62)], P2)
    faulds(lt, P, P2, R, 2)
    tassets(lt, P, P2, R, z_top=-0.45, rows=1, arcs=((-50, 30),))
    # Long cloth panels flowing down the outside of each leg, edged in gold, flaring out.
    for s in (1, -1):
        a0, a1 = (30, 115) if s > 0 else (-115, -30)
        curved_plate(lt, (s * 0.45, 0.0), 0.84, a0, a1, -2.65, -0.15, "cloth_white", thick=0.04, flare=0.3, n=10)
        curved_plate(lt, (s * 0.45, 0.0), 0.86, a0 - 2, a1 + 2, -2.72, -2.55, "gold_engraved", thick=0.03, flare=0.33,
                     n=10)
    lofted_cape(o, dict(cape="cloth_royal", lining="cloth_white", trim="gold", trim2="blade", gem="gem_blue",
                        cape_rings=[(0.98, 1.15, 0.1, 0.62, (35, 120)), (0.55, 1.9, 0.3, 0.75, (60, 105)),
                                    (-0.4, 2.2, 0.6, 0.42, (74, 84)), (-2.0, 2.35, 0.72, 0.42, 74),
                                    (-3.72, 2.55, 0.88, 0.48, 70)]))
    o.crystals("LeftUpperArm", 3, (0.6, 0.1, 0.7), (0.2, 0.35, 0.12), (0.7, 0.2, 1), length=(0.3, 0.7),
               radius=(0.05, 0.1))
    return o


def white_shield(o):
    from outfits.parade import parade_shield
    parade_shield(o, face="plate_white", rim="blade", gem="gem_blue")


# ---------------------------------------------------------------------------
# 2. Black Knight (black knight in the forest, keeping his red cape)
def black(name, glow):
    o = Outfit(name, glow=glow, seed=62)
    P, P2, R = "plate_black", "plate_black", "blade"
    h, g = o("Head"), o("Head", "Glow")
    # Round-topped helm with a flat, upright visor plate and a white plume.
    rshell(h, [(-0.64, 0.56, 0.6), (-0.1, 0.58, 0.62), (0.45, 0.57, 0.61), (0.75, 0.5, 0.54), (0.92, 0.3, 0.34)],
           P, tip=(0, 0.04, 0.98), p=3.4)
    # Visor: a plate curving round the face, edged in silver, with one slit across it.
    rimmed(h, (0, -0.02), 0.64, -68, 68, -0.6, 0.34, P, R, flare=0.03, thick=0.06, n=14)
    curved_plate(h, (0, -0.02), 0.665, -48, 48, 0.1, 0.17, "black", thick=0.03, n=12)
    curved_plate(g, (0, -0.02), 0.672, -44, 44, 0.115, 0.155, "glow", thick=0.02, n=12)
    for k in range(4):  # breathing holes on the right cheek
        for j in range(2):
            a = math.radians(-25 - 9 * j)
            h.box((0.04, 0.04, 0.045), "black", pos=(0.67 * math.sin(a), -0.67 * math.cos(a) - 0.02, -0.12 - 0.08 * k))
    trim(h, 0.45, 0.585, 0.625, R, h=0.04, p=3.4)
    neck_lames(h, P, P2, R)
    # Slim breastplate, silver-edged plackart in a double V, a baldric across the chest.
    t = o("UpperTorso")
    breastplate(t, P, keel=0.08, waist=1.0)
    gorget(t, P, P2, R)
    for s in (1, -1):
        pipe(t, [(s * 0.98, -0.5, 0.7), (s * 0.6, -0.7, 0.1), (0, -0.8, -0.6)], R, w=0.05)
        pipe(t, [(s * 0.7, -0.62, 0.72), (s * 0.35, -0.75, 0.3), (0, -0.8, 0.05)], R, w=0.04)
    for y, sgn in ((-0.82, 1), (0.82, -1)):  # baldric from the right shoulder to the left hip
        t.box((0.2, 0.05, 2.0), "leather_strap", pos=(0.05, y, 0.0), rot=(0, sgn * -38, 0))
    t.box((0.24, 0.07, 0.2), "blade", pos=(0.33, -0.84, -0.35), rot=(0, -38, 0))
    pipe(t, [(0, 0.72, 0.75), (0, 0.7, -0.75)], R, w=0.06)
    for part, side in (("Left", 1), ("Right", -1)):
        pauldron(o(part + "UpperArm"), side, 1.15, 4, (P, P2), R, peak=0.18, out=side * 0.06, reach=-0.5)
        arm_plate(o, part, side, P, P2, R, lames=3, cuff=0.12)
        leg_plate(o, part, side, P, P2, R, point=0.25)
    lt = o("LowerTorso")
    boxy(lt, [(-0.12, 1.06, 0.64), (0.2, 1.04, 0.62)], "leather_strap")
    faulds(lt, P, P2, R, 1)
    # Long tassets hanging as separate vertical panels down to the knee.
    tassets(lt, P, P2, R, z_top=-0.22, rows=2, length=0.68, arcs=((-48, -6), (2, 44), (56, 112)))
    xs = [-0.6, -0.3, 0.0, 0.3, 0.6]
    lt.cloth(xs, -0.3, [-2.3, -2.45, -2.4, -2.45, -2.3], 0.8, "pants", sag=0.06)  # dark skirt behind
    lofted_cape(o, dict(cape="cloth_royal", lining="cloth_dark", trim="blade", trim2="blade", gem="gem", folds=0.16,
                        cape_rings=[(1.02, 1.2, 0.12, 0.62, 95), (0.45, 2.6, 0.4, 0.8, 95), (-0.4, 2.55, 0.68, 0.48, 80),
                                    (-2.0, 2.65, 0.8, 0.48, 74), (-3.72, 2.85, 0.95, 0.55, 70)]))
    o.crystals("LeftUpperArm", 3, (0.7, 0.1, 0.7), (0.2, 0.35, 0.12), (0.7, 0.2, 1), length=(0.3, 0.7),
               radius=(0.05, 0.1))
    return o


# ---------------------------------------------------------------------------
# 3. Royal Guard (Artorias)
def artorias(name, glow):
    o = Outfit(name, glow=glow, seed=63)
    P, P2, R = "plate_dark", "iron", "blade"
    h, g = o("Head"), o("Head", "Glow")
    # Narrow, rounded helm with a low crest; one flush slit; the plume streams from the crest.
    rshell(h, [(-0.62, 0.54, 0.6, {"keel": 0.08}), (-0.15, 0.56, 0.62, {"keel": 0.12}), (0.3, 0.56, 0.61, {"keel": 0.1}),
               (0.66, 0.44, 0.5, {"keel": 0.06}), (0.9, 0.2, 0.28)], P, tip=(0, 0.0, 1.02), p=2.8)
    slit(h, g, -0.4, 0.4, 0.1, -0.7, w=0.045)
    h.box((0.9, 0.06, 0.09), P2, pos=(0, -0.7, 0.2))  # brow band over the slit
    for k in range(5):  # vertical breaths
        h.box((0.035, 0.05, 0.22), "black", pos=(-0.3 + 0.15 * k, -0.7, -0.3))
    for k in range(4):  # low crest
        fin(h, (0, -0.4 + 0.3 * k, 0.95 - 0.04 * k * k), (0, 0.3, 1), 0.16, 0.03, 0.16, P2)
    neck_lames(h, P, P2, R)
    # Chest: plate over overlapping abdominal lames.
    t = o("UpperTorso")
    breastplate(t, P, keel=0.1)
    gorget(t, P, P2, R)
    for i in range(3):
        z1 = -0.25 - 0.2 * i
        boxy(t, [(z1 - 0.26, 1.07 + 0.02 * i, 0.66 + 0.02 * i), (z1, 1.06 + 0.02 * i, 0.65 + 0.02 * i)], P2 if i % 2 else P)
        trim(t, z1 - 0.25, 1.09 + 0.02 * i, 0.68 + 0.02 * i, R, h=0.04)
    pipe(t, [(0, 0.72, 0.75), (0, 0.7, -0.75)], R, w=0.06)
    # One huge pauldron on the right; a small one on the left under the scarf.
    pauldron(o("RightUpperArm"), -1, 1.35, 4, (P, P2), R, peak=0.25, out=-0.15, reach=-0.55)
    pauldron(o("LeftUpperArm"), 1, 0.95, 2, (P, P2), R, peak=0.1)
    for part, side in (("Left", 1), ("Right", -1)):
        arm_plate(o, part, side, P, P2, R, ribs=5, cuff=0.1)
        leg_plate(o, part, side, P, P2, R, point=0.22, fan=False)
    lt = o("LowerTorso")
    boxy(lt, [(-0.12, 1.06, 0.64), (0.2, 1.04, 0.62)], "leather_strap")
    boxy(lt, [(-1.3, 1.24, 0.82), (-0.1, 1.1, 0.66)], "chainmail")  # chainmail skirt
    faulds(lt, P, P2, R, 1)
    tassets(lt, P, P2, R, z_top=-0.35, rows=1, length=0.5, arcs=((-40, 30),))
    # Tattered blue scarf wrapping the neck and left shoulder, streaming down the back.
    lofted_cape(o, dict(cape="cloth_blue", lining="cloth_blue", trim="cloth_blue", trim2="iron", gem="gem_blue",
                        folds=0.14, cape_rings=[(1.05, 0.95, 0.05, 0.7, (130, 150)), (0.7, 1.7, 0.2, 0.85, (60, 120)),
                                                (-0.2, 2.0, 0.55, 0.5, (55, 95)), (-1.3, 2.1, 0.7, 0.45, (50, 85))]))
    tt = o("UpperTorso")
    xs = [-0.4, -0.15, 0.1, 0.35, 0.6, 0.85, 1.1, 1.35]
    tt.cloth(xs, -1.25, [-2.4, -1.9, -2.7, -2.1, -2.9, -2.2, -2.6, -1.8], 1.05, "cloth_blue", sag=0.1)  # tatters
    o.crystals("LeftUpperArm", 3, (0.6, 0.1, 0.7), (0.2, 0.3, 0.12), (0.7, 0.2, 1), length=(0.3, 0.6),
               radius=(0.05, 0.1))
    return o


def artorias_plume():
    """The long dark-blue plume streaming back and down from the crest."""
    return plume(64, count=9, root=(0, 0.35, 1), aim=(0, 1, 0.1), length=2.4, width=0.22, gravity=1.1, pad=0.44,
                 spread=0.2)


# ---------------------------------------------------------------------------
# 4. Paladin (hooded knight)
def hooded(name, glow):
    o = Outfit(name, glow=glow, seed=65)
    P, P2, R, C = "plate_dark", "plate_dark", "gold_engraved", "pants"
    h = o("Head")
    # A deep hood with its peak falling back; inside, nothing but darkness.
    n = 26

    def arc(rx, ry, y0, sp, inset):
        return [((rx - inset) * math.sin(math.radians(-sp + 2 * sp * i / (n - 1))),
                 y0 + (ry - inset) * math.cos(math.radians(-sp + 2 * sp * i / (n - 1)))) for i in range(n)]
    rings = [(-1.05, 1.35, 1.05, 0.15, 125), (-0.7, 0.98, 0.86, 0.08, 132), (-0.1, 0.8, 0.82, 0.04, 140),
             (0.45, 0.76, 0.8, 0.06, 148), (0.82, 0.58, 0.68, 0.12, 160), (1.0, 0.3, 0.42, 0.2, 175)]
    h.loft([(z, arc(rx, ry, y0, sp, 0) + list(reversed(arc(rx, ry, y0, sp, 0.07)))) for z, rx, ry, y0, sp in rings],
           C, smooth=True)
    # The void: a black dome filling the opening, in front of the head.
    rshell(h, [(-0.75, 0.62, 0.1, {"dy": -0.55}), (0.0, 0.66, 0.12, {"dy": -0.6}), (0.6, 0.5, 0.1, {"dy": -0.56})],
           "black", tip=(0, -0.55, 0.85))
    rshell(h, [(-0.95, 0.66, 0.62, {"dy": 0.05}), (-0.62, 0.62, 0.58, {"dy": 0.05})], C)  # cowl under the chin
    for s in (1, -1):  # gold edge round the opening
        pipe(h, [(s * 0.62, -0.72, -0.8), (s * 0.7, -0.74, -0.1), (s * 0.62, -0.7, 0.5), (s * 0.3, -0.64, 0.86),
                 (0, -0.62, 0.95)], R, w=0.05)
    # Chest: dark plate engraved with gold scrollwork, an emblem, a strap across.
    t = o("UpperTorso")
    breastplate(t, P, keel=0.08)
    gorget(t, P, P2, R, high=0.06)
    for s in (1, -1):
        pipe(t, [(s * 0.1, -0.78, 0.55), (s * 0.35, -0.75, 0.68), (s * 0.6, -0.7, 0.55), (s * 0.55, -0.73, 0.32),
                 (s * 0.3, -0.76, 0.35)], R, w=0.04)
        pipe(t, [(s * 0.15, -0.79, 0.0), (s * 0.45, -0.74, -0.15), (s * 0.7, -0.66, 0.05)], R, w=0.04)
    lens(t, (0, -0.76, 0.3), (0, -1, 0), 0.2, 0.16, 0.08, R, n=10)
    for y, sgn in ((-0.82, -1), (0.82, 1)):  # strap from the left shoulder to the right hip
        t.box((0.22, 0.05, 2.0), "leather_strap", pos=(-0.05, y, 0.0), rot=(0, sgn * -38, 0))
        for k in range(4):
            t.box((0.06, 0.06, 0.06), R, pos=(0.5 - 0.3 * k, y * 1.02, 0.6 - 0.38 * k))
    for part, side in (("Left", 1), ("Right", -1)):
        pauldron(o(part + "UpperArm"), side, 1.05, 3, (P, P2), R, peak=0.25, fringe="rope")
        arm_plate(o, part, side, P, P2, R, chain=True, cuff=0.14)
        leg_plate(o, part, side, P, P2, R, point=0.22, knee=P)
    lt = o("LowerTorso")
    boxy(lt, [(-0.14, 1.1, 0.66), (0.22, 1.08, 0.64)], "leather_strap")  # wide belt
    lens(lt, (0, -0.68, 0.04), (0, -1, 0), 0.24, 0.17, 0.08, R, n=10)  # buckle
    for s in (1, -1):  # gold wings on the buckle
        for k in range(3):
            fin(lt, (s * 0.2, -0.7, 0.04), (s, -0.2, 0.4 - 0.3 * k), 0.35 - 0.06 * k, 0.05, 0.02, R, roll=90)
    tassets(lt, P, P2, R, z_top=-0.25, rows=2, length=0.4, arcs=((-60, -5), (5, 55), (60, 120)), r=0.76)
    xs = [-0.9, -0.5, -0.1, 0.3, 0.7]
    lt.cloth(xs, -0.2, [-1.9, -2.0, -1.95, -2.05, -1.9], -0.74, C, sag=-0.05)
    lt.cloth(xs, -0.2, [-2.0, -2.1, -2.0, -2.1, -2.0], 0.74, C, sag=0.05)
    tt = o("UpperTorso")  # torn cape on the left of the back
    xs = [0.1, 0.35, 0.6, 0.85, 1.1]
    tt.cloth(xs, 0.85, [-2.6, -1.8, -2.9, -2.0, -2.4], 0.78, C, sag=0.08)
    o.crystals("LeftUpperArm", 4, (0.6, 0.1, 0.7), (0.2, 0.35, 0.12), (0.7, 0.2, 1), length=(0.3, 0.7),
               radius=(0.05, 0.1))
    return o


# ---------------------------------------------------------------------------
# 5. Dragon Knight (dragoon)
def dragoon(name, glow):
    o = Outfit(name, glow=glow, seed=91)
    P, P2, R = "plate_black", "plate_dark", "blade"
    h, g = o("Head"), o("Head", "Glow")
    # Helm: domed, its visor curving down to a beak over the face (flush, pointing down,
    # not out); a mane of curved blades sweeping back from crown and temples.
    rshell(h, [(-0.62, 0.55, 0.6, {"keel": 0.2}), (-0.25, 0.57, 0.63, {"keel": 0.16}), (0.2, 0.58, 0.63, {"keel": 0.1}),
               (0.6, 0.48, 0.54, {"keel": 0.06}), (0.88, 0.24, 0.3)], P, tip=(0, 0.05, 1.0), p=2.8)
    rshell(h, [(-0.9, 0.08, 0.06, {"dy": -0.72}), (-0.6, 0.2, 0.1, {"dy": -0.74})], P, tip=(0, -0.66, -1.05))  # beak
    for s in (1, -1):
        slit(h, g, s * 0.08, s * 0.44, 0.1, -0.7, w=0.045, spin=s * -22)
        pipe(h, [(s * 0.05, -0.8, 0.3), (s * 0.4, -0.66, 0.25), (s * 0.6, -0.4, 0.05)], R, w=0.04)  # silver brow line
        for k in range(3):
            sweep(h, (s * 0.5, -0.1 + 0.25 * k, 0.5 - 0.1 * k), (s * 0.3, 1, 0.6 - 0.15 * k),
                  1.8 - 0.4 * k, 0.4 - 0.07 * k, 55, P, edge=R, flip=s < 0)
        for k in range(2):
            sweep(h, (s * (0.15 + 0.15 * k), 0.0 + 0.2 * k, 0.88 - 0.1 * k), (s * 0.25, 0.8, 1),
                  1.3 - 0.3 * k, 0.3, 60, P, edge=R, flip=s < 0)
    sweep(h, (0, -0.4, 0.88), (0, 0.4, 1), 1.5, 0.4, -70, P, edge=R, up=(1, 0, 0))
    neck_lames(h, P, P2, R)
    t, tg = o("UpperTorso"), o("UpperTorso", "Glow")
    breastplate(t, P, keel=0.12, waist=0.98)
    gorget(t, P, P2, R)
    for s in (1, -1):  # silver scrollwork and glowing veins
        pipe(t, [(s * 0.15, -0.8, 0.62), (s * 0.45, -0.78, 0.74), (s * 0.78, -0.66, 0.55), (s * 0.9, -0.55, 0.15),
                 (s * 0.72, -0.66, -0.2), (s * 0.85, -0.58, -0.6)], R, w=0.05)
        pipe(tg, [(s * 0.6, -0.72, 0.05), (s * 0.45, -0.73, -0.35), (s * 0.3, -0.72, -0.75)], "glow", w=0.045, t=0.03)
    pipe(t, [(0, 0.72, 0.75), (0, 0.7, -0.75)], R, w=0.06)
    for part, side in (("Left", 1), ("Right", -1)):
        ua = o(part + "UpperArm")
        pauldron(ua, side, 0.9, 2, (P, P2), R, peak=0.3)
        for k in range(3):
            sweep(ua, (side * (0.3 + 0.18 * k), -0.35 + 0.35 * k, 0.85 - 0.1 * k), (side * 0.6, 0.4, 1),
                  1.3 - 0.25 * k, 0.42, 55, P, edge=R, flip=side < 0)
        arm_plate(o, part, side, P, P2, R, lames=2, cuff=0.1)
        leg_plate(o, part, side, P, P2, R, point=0.38)
        la, ll, ft = o(part + "LowerArm"), o(part + "LowerLeg"), o(part + "Foot")
        sweep(la, (0, 0.6, 0.45), (side * 0.2, 1, 0.3), 1.1, 0.4, -50, P, edge=R)
        sweep(la, (side * 0.6, 0.1, -0.1), (side * 0.6, 0.6, -1), 1.0, 0.34, 40, P, edge=R, up=(0, 1, 0))
        sweep(ll, (0, -0.7, 0.55), (0, -0.4, 1), 0.95, 0.36, 60, P, edge=R, up=(0, -1, 0))
        sweep(ft, (0, 0.55, 0.0), (0, 1, -0.2), 0.65, 0.26, 40, P, edge=R)
        pipe(o(part + "LowerLeg", "Glow"), [(0, -0.75, 0.25), (0, -0.72, -0.5)], "glow", w=0.045, t=0.03)
    for s in (1, -1):
        sweep(t, (s * 0.45, 0.7, 0.6), (s * 0.5, 1, 0.9), 2.2, 0.7, 60, P, edge=R, flip=s < 0)
        sweep(t, (s * 0.55, 0.7, 0.2), (s * 0.7, 1, 0.3), 1.5, 0.5, 50, P, edge=R, flip=s < 0)
    lt = o("LowerTorso")
    boxy(lt, [(-0.12, 1.04, 0.62), (0.2, 1.02, 0.6)], P2)
    lens(lt, (0, -0.64, 0.05), (0, -1, 0), 0.18, 0.14, 0.08, "gem", n=10)
    faulds(lt, P, P2, R, 2)
    tassets(lt, P, P2, R, z_top=-0.42, rows=2, length=0.4)
    for s in (1, -1):
        sweep(lt, (s * 1.15, 0.2, -0.3), (s * 0.6, 0.7, -1), 1.3, 0.45, -45, P, edge=R, up=(0, 1, 0))
    o.crystals("LeftUpperArm", 4, (0.6, 0.1, 0.75), (0.25, 0.4, 0.15), (0.7, 0.2, 1), length=(0.35, 0.8),
               radius=(0.06, 0.12))
    return o

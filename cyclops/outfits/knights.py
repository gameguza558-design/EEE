"""Cyclops knights: apprentice, mid and high rank, with a shield per rank.

`corruption` (0..1) decides how much of the armor is cracked and how many
crystals break through, so the same rank can be reused deeper into the game.
The shield is an optional extra on LeftLowerArm ("Shield"/"ShieldGlow" kinds).
"""
from kit import band, blob, circle

from outfits.common import (Outfit, back_cloth, belt, cyclops_head, gloves, pants, pouch, shirt,
                            shoes, tunic_skirt, wraps)


def plate_for(o, side, base):
    """Pick the plate texture for a side of the body given the corruption level."""
    c = o.corruption
    if c >= 0.85:
        return "plate_corrupt" if side > 0 else base
    if c >= 0.6:
        return "plate_corrupt" if side > 0 else base
    if c >= 0.45 and side > 0:
        return "plate_corrupt"
    return base


def spread_corruption(o):
    """Crystals scaled by corruption: always strongest on the left side."""
    c, n = o.corruption, lambda k: int(round(k * o.corruption))
    o.crystals("LeftUpperArm", n(14), (0.5, 0, 0.55), (0.25, 0.4, 0.2), (0.8, 0, 1),
               length=(0.25, 0.4 + 0.7 * c), radius=(0.05, 0.08 + 0.08 * c))
    o.crystals("LeftLowerArm", n(8), (0.62, 0, 0.0), (0.03, 0.4, 0.4), (1, 0, 0.4),
               length=(0.2, 0.3 + 0.3 * c), radius=(0.04, 0.09))
    o.crystals("UpperTorso", n(6), (0.8, -0.7, 0.4), (0.15, 0.03, 0.35), (0.5, -1, 0.3),
               length=(0.15, 0.35), radius=(0.04, 0.07))
    if c >= 0.6:
        o.crystals("UpperTorso", n(8), (0.0, 0.75, 0.3), (0.5, 0.03, 0.5), (0, 1, 0.5),
                   length=(0.25, 0.6), radius=(0.05, 0.1))
        o.crystals("LeftUpperLeg", n(5), (0.6, 0, 0.0), (0.03, 0.4, 0.4), (1, 0, 0.3),
                   length=(0.15, 0.35), radius=(0.04, 0.07))
    if c >= 0.85:
        o.crystals("RightUpperArm", n(6), (-0.5, 0, 0.6), (0.2, 0.3, 0.15), (-0.6, 0, 1),
                   length=(0.2, 0.5), radius=(0.04, 0.08))
        o.crystals("Head", n(5), (0.6, 0.0, 0.4), (0.1, 0.3, 0.2), (1, 0, 0.8),
                   length=(0.2, 0.5), radius=(0.05, 0.08))


# ---------------------------------------------------------------------------
# Shields: built facing +X (outward from the left forearm).
def round_shield(o, rim="iron", face="wood"):
    s = o("LeftLowerArm", "Shield")
    s.loft([(0.6, circle(0.95, 12)), (0.7, circle(0.95, 12))], face, rot=(0, 90, 0))
    s.loft([(0.68, circle(1.0, 12)), (0.74, circle(1.0, 12))], rim, rot=(0, 90, 0))
    blob(s, (0.82, 0, 0), (0.12, 0.26, 0.26), rim)  # boss
    for i in range(4):
        s.box((0.06, 0.12, 1.75), "plate_rust", pos=(0.74, -0.45 + 0.3 * i, 0))


def heater_shield(o, face="shield", rim="plate_trim"):
    s = o("LeftLowerArm", "Shield")
    # (across, up) outline; the loft is rotated so its profile is (-up, across).
    outline = [(0.0, 0.95), (0.62, 0.9), (0.72, 0.3), (0.45, -0.5), (0.0, -1.15),
               (-0.45, -0.5), (-0.72, 0.3), (-0.62, 0.9)]
    prof = [(-up, across) for across, up in outline]
    s.loft([(0.62, prof), (0.72, prof)], face, rot=(0, 90, 0), pos=(0, 0, 0))
    big = [(x * 1.08, y * 1.06) for x, y in prof]
    s.loft([(0.6, big), (0.67, big)], rim, rot=(0, 90, 0))
    s.box((0.08, 0.16, 1.7), rim, pos=(0.74, 0, -0.08))


def kite_shield(o):
    heater_shield(o, face="plate_corrupt", rim="gold")
    s = o("LeftLowerArm", "Shield")
    s.spike((0.78, 0, 0.1), (1, 0, 0), 0.35, 0.18, "gold", sides=4)
    for z in (0.6, -0.6):
        s.box((0.08, 1.0, 0.1), "gold", pos=(0.76, 0, z * 0.9), top=(1, 0.7))
    rnd, g = o.rnd, o("LeftLowerArm", "ShieldGlow")
    for _ in range(6):
        g.spike((0.75, rnd.uniform(-0.5, 0.5), rnd.uniform(-0.8, 0.6)),
                (1, rnd.uniform(-0.6, 0.6), rnd.uniform(-0.4, 0.8)), rnd.uniform(0.2, 0.45),
                rnd.uniform(0.04, 0.08), "glow", sides=5)


# ---------------------------------------------------------------------------
def apprentice(name="KnightApprentice", corruption=0.3, seed=21):
    """Gambeson, mail and rusty scraps of plate; an open kettle hat shows the eye."""
    o = Outfit(name, corruption=corruption, seed=seed)
    cyclops_head(o, ears=False)
    h = o("Head")
    h.shell([(0.18, 0.72, 0.72, 0.22), (0.5, 0.66, 0.66, 0.22), (0.7, 0.4, 0.4, 0.16)],
            "plate_rust", tip=(0, 0, 0.78))
    band(h, 0.18, 0.28, 0.95, 0.95, 0.3, "plate_rust")  # brim
    for s in (1, -1):
        h.box((0.12, 0.6, 0.7), "chainmail", pos=(s * 0.7, 0.1, -0.25))
    h.box((1.3, 0.14, 0.75), "chainmail", pos=(0, 0.7, -0.25))
    shirt(o, "quilt", sleeves="full")
    t = o("UpperTorso")
    t.shell([(-0.82, 1.1, 0.6, 0.2), (0.3, 1.12, 0.62, 0.22)], "chainmail")
    t.box((1.3, 0.1, 0.9), plate_for(o, 0, "plate_rust"), pos=(0, -0.66, 0.25), top=(0.9, 1))
    back_cloth(o, "cloth", top=0.7, length=1.0, width=0.6, y=0.64)
    for s, pre in ((1, "Left"), (-1, "Right")):
        ua = o(pre + "UpperArm")
        ua.shell([(0.25, 0.68, 0.66, 0.2, s * 0.06, 0), (0.62, 0.55, 0.55, 0.18)],
                 plate_for(o, s, "plate_rust"))
        band(o(pre + "LowerArm"), -0.45, 0.2, 0.6, 0.6, 0.16, "leather", grow=0.03)
    tunic_skirt(o, "cloth", length=0.8)
    belt(o, "leather_strap")
    pouch(o, -0.78)
    gloves(o, "leather")
    pants(o, "quilt")
    for pre in ("Left", "Right"):
        ll = o(pre + "LowerLeg")
        ll.box((0.66, 0.2, 0.42), "plate_rust", pos=(0, -0.6, 0.48), top=(0.8, 1), bottom=(0.8, 1))
        wraps(o, pre + "LowerLeg", (-0.3, 0.0, 0.25), "leather_strap", 0.6)
    shoes(o, "leather", tall=0.4)
    round_shield(o)
    spread_corruption(o)
    return o


def _plate_limbs(o, trim, base, pauldron_layers=2, gold=False):
    for s, pre in ((1, "Left"), (-1, "Right")):
        plate = plate_for(o, s, base)
        ua, la, h = o(pre + "UpperArm"), o(pre + "LowerArm"), o(pre + "Hand")
        band(ua, -0.6, 0.45, 0.55, 0.55, 0.14, "chainmail")
        band(ua, -0.45, 0.3, 0.6, 0.6, 0.15, plate)
        ua.shell([(0.22, 0.8, 0.74, 0.24, s * 0.1, 0), (0.6, 0.72, 0.68, 0.24, s * 0.05, 0),
                  (0.84, 0.42, 0.44, 0.16)], plate)
        for i in range(pauldron_layers):
            ua.box((0.52, 1.35 - 0.1 * i, 0.3), trim if i == 0 else plate,
                   pos=(s * (0.6 + 0.05 * i), 0, 0.4 - 0.22 * i), rot=(0, s * 28, 0), bottom=(1, 0.9))
        la.shell([(-0.52, 0.56, 0.56, 0.14), (0.5, 0.61, 0.61, 0.15)], plate)
        la.box((0.7, 0.2, 0.44), trim, pos=(0, 0.62, 0.42), top=(0.8, 1))
        band(la, -0.55, -0.42, 0.65, 0.65, 0.16, trim)
        band(h, -0.22, 0.06, 0.54, 0.54, 0.14, plate)
        h.shell([(0.04, 0.63, 0.63, 0.16), (0.3, 0.7, 0.7, 0.18)], trim)
        for x in (-0.3, -0.1, 0.1, 0.3):
            h.box((0.17, 0.1, 0.15), plate, pos=(x, -0.57, -0.1))
        ul, ll, f = o(pre + "UpperLeg"), o(pre + "LowerLeg"), o(pre + "Foot")
        ul.shell([(-0.55, 0.57, 0.57, 0.15), (0.6, 0.6, 0.6, 0.15)], plate)
        for i in range(2):
            ul.box((0.8, 0.1, 0.32), trim if i == 0 else plate, pos=(0, -0.64, 0.4 - 0.36 * i),
                   rot=(8, 0, 0))
        ll.shell([(-0.6, 0.56, 0.56, 0.15), (0.5, 0.6, 0.6, 0.15)], plate)
        ll.box((0.7, 0.22, 0.46), trim, pos=(0, -0.64, 0.52), top=(0.8, 1), bottom=(0.8, 1))
        ll.box((0.16, 0.12, 0.9), trim, pos=(0, -0.62, -0.15), bottom=(0.6, 1))
        f.shell([(-0.2, 0.58, 0.68, 0.14, 0, -0.14), (0.2, 0.56, 0.6, 0.14, 0, -0.04)], plate)
        for i in range(2):
            f.box((1.1 - 0.08 * i, 0.3, 0.13), trim if i == 0 else plate,
                  pos=(0, -0.5 - 0.2 * i, 0.16 - 0.11 * i), rot=(16, 0, 0))
        if gold:
            band(ua, 0.14, 0.24, 0.84, 0.78, 0.25, "gold", dx=s * 0.1)
            band(ll, 0.46, 0.58, 0.63, 0.63, 0.16, "gold")


def mid(name="KnightMid", corruption=0.65, seed=22):
    """Half plate over mail, bascinet with a visor slit and a long tabard."""
    o = Outfit(name, corruption=corruption, seed=seed)
    h = o("Head")
    h.shell([(-0.62, 0.7, 0.72, 0.22), (0.2, 0.74, 0.76, 0.24), (0.55, 0.6, 0.62, 0.24)],
            plate_for(o, 0, "plate_mid"), tip=(0, 0.1, 0.92))
    h.box((1.2, 0.3, 0.75), "plate_trim", pos=(0, -0.76, -0.12), top=(0.85, 1), bottom=(0.5, 0.6),
          shift=(0, 0.1))
    h.box((0.95, 0.05, 0.09), "black", pos=(0, -0.92, 0.12))
    o("Head", "Glow").box((0.35, 0.04, 0.07), "glow", pos=(0, -0.94, 0.12))
    for z in (-0.15, -0.3):
        for x in (-0.25, 0.25):
            h.box((0.08, 0.05, 0.08), "black", pos=(x, -0.92, z))
    h.box((1.45, 1.45, 0.3), "chainmail", pos=(0, 0.1, -0.55), bottom=(1.05, 1.05))
    shirt(o, "chainmail", sleeves=None)
    t = o("UpperTorso")
    t.shell([(-0.82, 1.1, 0.64, 0.22), (0.45, 1.15, 0.69, 0.24), (0.84, 1.0, 0.6, 0.24)],
            plate_for(o, 0, "plate_mid"))
    t.box((0.16, 0.12, 1.5), "plate_trim", pos=(0, -0.72, 0.0), top=(1, 0.6))
    t.shell([(0.7, 0.68, 0.52, 0.16), (1.0, 0.6, 0.46, 0.14)], "plate_trim")
    t.box((1.25, 0.06, 1.4), "cloth", pos=(0, -0.71, -0.15))
    back_cloth(o, "cloth_dark", top=0.8, length=2.2, width=0.8, y=0.72)
    _plate_limbs(o, "plate_trim", "plate_mid")
    belt(o, "leather_strap")
    lt = o("LowerTorso")
    lt.shell([(-1.05, 1.18, 0.7, 0.22), (-0.15, 1.1, 0.64, 0.2)], "chainmail")
    xs = [-0.6, -0.4, -0.2, 0.0, 0.2, 0.4, 0.6]
    lt.cloth(xs, -0.15, [-1.75, -2.0, -1.8, -2.1, -1.85, -2.0, -1.7], -0.74, "cloth", sag=-0.05)
    for s in (1, -1):
        lt.box((0.17, 1.0, 0.6), "plate_mid", pos=(s * 1.15, 0, -0.45), rot=(0, s * 12, 0))
    heater_shield(o)
    spread_corruption(o)
    return o


def high(name="KnightHigh", corruption=0.9, seed=23):
    """Ornate full plate with gold trim, a great helm with a crest, and a long cape."""
    o = Outfit(name, corruption=corruption, seed=seed)
    h = o("Head")
    h.shell([(-0.68, 0.74, 0.76, 0.16), (0.45, 0.78, 0.8, 0.18), (0.66, 0.66, 0.68, 0.18)],
            plate_for(o, 0, "plate_dark"))
    band(h, 0.5, 0.66, 0.8, 0.82, 0.2, "gold")
    h.box((0.08, 0.06, 0.95), "gold", pos=(0, -0.84, -0.12))  # cross slit frame
    h.box((1.0, 0.06, 0.09), "black", pos=(0, -0.84, 0.15))
    h.box((0.07, 0.06, 0.55), "black", pos=(0, -0.84, -0.12))
    g = o("Head", "Glow")
    g.box((0.4, 0.04, 0.07), "glow", pos=(0, -0.86, 0.15))
    h.box((0.16, 1.5, 0.4), "gold", pos=(0, 0, 0.82), top=(0.5, 0.85))  # crest
    for s in (1, -1):  # broken horn stubs: the corruption is turning them into the One-Horn
        h.spike((s * 0.45, -0.1, 0.62), (s * 0.5, 0.1, 1), 0.45, 0.12, "horn", sides=5)
    shirt(o, "chainmail", sleeves=None)
    t = o("UpperTorso")
    t.shell([(-0.02, 1.12, 0.66, 0.22), (0.45, 1.17, 0.71, 0.24), (0.86, 1.02, 0.62, 0.24)],
            plate_for(o, 0, "plate_dark"))
    for i in range(3):
        z1 = -0.02 - 0.27 * i
        band(t, z1 - 0.3, z1, 1.07, 0.63, 0.2, plate_for(o, 0, "plate_mid"), grow=0.04)
    for s in (1, -1):
        t.box((0.84, 0.1, 0.64), plate_for(o, s, "plate_mid"), pos=(s * 0.5, -0.72, 0.42),
              rot=(0, s * -8, 0), bottom=(0.9, 1))
    t.box((0.18, 0.13, 1.55), "gold", pos=(0, -0.74, 0.0), top=(1, 0.6))
    t.shell([(0.7, 0.7, 0.54, 0.16), (1.04, 0.62, 0.48, 0.14)], "gold")
    # Long cape from the shoulders to the calves.
    back_cloth(o, "cloth", top=0.85, length=3.4, width=1.05, y=0.76)
    _plate_limbs(o, "gold", "plate_dark", pauldron_layers=4, gold=True)
    lt = o("LowerTorso")
    band(lt, -0.22, 0.2, 1.14, 0.66, 0.2, "leather_strap")
    lt.box((0.52, 0.1, 0.44), "gold", pos=(0, -0.7, 0))
    lt.box((0.28, 0.05, 0.22), "black", pos=(0, -0.75, 0))
    lt.shell([(-1.05, 1.18, 0.7, 0.22), (-0.15, 1.1, 0.64, 0.2)], "chainmail")
    for s in (1, -1):
        for i in range(3):
            lt.box((0.18, 1.04 - 0.06 * i, 0.42), "gold" if i == 0 else "plate_dark",
                   pos=(s * (1.16 + 0.03 * i), 0, -0.35 - 0.33 * i), rot=(0, s * 12, 0))
    for i in range(3):  # faulds
        lt.box((1.5 - 0.1 * i, 0.12, 0.3), "plate_dark" if i % 2 else "plate_mid",
               pos=(0, -0.72, -0.4 - 0.26 * i), rot=(8, 0, 0))
    lt.cloth([-0.35, -0.2, 0.0, 0.2, 0.35], -1.05, [-1.9, -2.15, -1.95, -2.2, -1.85], -0.76, "cloth")
    kite_shield(o)
    spread_corruption(o)
    return o


def all_knights():
    return [
        apprentice("KnightApprentice", 0.3, 21),
        apprentice("KnightApprenticeInfected", 0.55, 24),
        mid(),
        high(),
    ]

"""Stage 1 cyclopes: villagers and wilderness folk with an early, partial corruption.

Corruption shows as a cracked skin patch and a few crystals, growing from the
villager to the wolf rider.
"""
from kit import band, blob, tube

from outfits.common import (Outfit, back_cloth, beard, belt, bracers, cyclops_head, gloves,
                            hair_tuft, pants, pouch, shirt, shoes, skin_limbs, strap_diagonal,
                            tunic_skirt, wraps)


def villager():
    o = Outfit("Villager", corruption=0.15, seed=11)
    cyclops_head(o)
    hair_tuft(o, 7)
    skin_limbs(o, "skin", upper=False)
    # The corruption has just reached the left forearm.
    band(o("LeftLowerArm"), -0.3, 0.3, 0.61, 0.61, 0.16, "skin_corrupt")
    shirt(o, "linen", sleeves="upper")
    # Open vest, rolled sleeves, rope belt and a short tunic skirt.
    t = o("UpperTorso")
    for s in (1, -1):
        t.box((0.62, 0.08, 1.5), "cloth_brown", pos=(s * 0.66, -0.6, 0.0), bottom=(1.05, 1))
        t.box((0.12, 1.2, 1.5), "cloth_brown", pos=(s * 1.1, 0, 0.0))
    t.box((1.9, 0.08, 1.5), "cloth_brown", pos=(0, 0.6, 0.0))
    for pre in ("Left", "Right"):
        band(o(pre + "UpperArm"), -0.62, -0.4, 0.62, 0.62, 0.18, "linen")
    tunic_skirt(o, "cloth_brown", length=0.7)
    belt(o, "rope", buckle=None, h=0.16)
    pouch(o, 0.75)
    pants(o, "cloth_brown")
    wraps(o, "LeftLowerLeg", (-0.4, -0.15, 0.1, 0.35))
    wraps(o, "RightLowerLeg", (-0.4, -0.15, 0.1, 0.35))
    shoes(o, "leather")
    o.crystals("LeftLowerArm", 2, (0.58, 0, 0.0), (0.02, 0.2, 0.2), (1, 0, 0.4),
               length=(0.12, 0.22), radius=(0.03, 0.05))
    return o


def hunter():
    o = Outfit("Hunter", corruption=0.2, seed=12)
    cyclops_head(o, ears=False)
    # Hood: open at the face, with a pointed back.
    h = o("Head")
    h.box((1.42, 1.1, 0.24), "cloth_green", pos=(0, 0.06, 0.72), top=(0.8, 0.8))
    h.box((1.42, 0.22, 1.35), "cloth_green", pos=(0, 0.66, 0.0))
    for s in (1, -1):
        h.box((0.2, 1.3, 1.35), "cloth_green", pos=(s * 0.71, 0.0, 0.0), bottom=(1, 0.8))
        h.box((0.12, 0.14, 1.3), "cloth_green", pos=(s * 0.64, -0.66, 0.05))
    h.spike((0, 0.7, 0.55), (0, 1, -0.5), 0.6, 0.25, "cloth_green", sides=4)
    # Body: shirt, leather vest, capelet and a quiver on the back.
    shirt(o, "cloth_green", sleeves="full")
    t = o("UpperTorso")
    t.shell([(-0.8, 1.1, 0.6, 0.2), (0.5, 1.12, 0.62, 0.22)], "leather")
    t.shell([(0.45, 1.25, 0.72, 0.26), (0.88, 0.8, 0.48, 0.2)], "cloth_green")
    back_cloth(o, "cloth_green", top=0.6, length=1.6, width=0.95, y=0.66)
    strap_diagonal(o, side=-1)
    tube(t, -0.4, 0.75, 0.2, 0.24, "leather", sides=8, pos=(0.35, 0.88, 0.1), rot=(0, -25, 0))
    for i, x in enumerate((-0.08, 0.0, 0.08, 0.02)):
        t.box((0.04, 0.04, 0.6), "wood", pos=(0.6 + x, 0.88, 0.95 + 0.04 * i), rot=(0, -25, 0))
        t.box((0.12, 0.02, 0.18), "linen", pos=(0.72 + x, 0.88, 1.18 + 0.04 * i), rot=(0, -25, 0))
    belt(o, "leather_strap")
    pouch(o, 0.75)
    pouch(o, -0.8, y=0.0)
    lt = o("LowerTorso")
    lt.box((0.14, 0.14, 0.7), "leather_strap", pos=(-0.62, -0.62, -0.42), rot=(0, 12, 0))  # knife
    lt.box((0.1, 0.08, 0.2), "wood", pos=(-0.66, -0.62, 0.0), rot=(0, 12, 0))
    tunic_skirt(o, "cloth_green", length=0.75)
    bracers(o, "leather")
    gloves(o, "leather_strap")
    pants(o, "cloth_brown")
    shoes(o, "leather", tall=0.95, cuff="fur")
    o.crystals("RightUpperArm", 3, (-0.5, 0.2, 0.4), (0.1, 0.2, 0.15), (-1, 0.3, 0.6),
               length=(0.15, 0.3), radius=(0.04, 0.06))
    o.crystals("UpperTorso", 2, (0.35, 0.9, 0.6), (0.1, 0.05, 0.1), (0.3, 1, 0.5),
               length=(0.12, 0.25), radius=(0.03, 0.05))
    return o


def woodcutter():
    o = Outfit("Woodcutter", corruption=0.3, seed=13)
    cyclops_head(o, skin="skin")
    beard(o, "fur_dark", 0.6)
    h = o("Head")
    for s in (1, -1):
        h.spike((s * 0.28, -0.66, -0.3), (s * 0.15, -0.3, 1), 0.3, 0.06, "bone", sides=4)  # tusks
    # Bare, muscular torso with the corruption cracking the left side.
    t = o("UpperTorso")
    t.shell([(-0.82, 1.06, 0.56, 0.2), (0.6, 1.1, 0.6, 0.22), (0.84, 0.95, 0.52, 0.2)], "skin")
    for s in (1, -1):
        blob(t, (s * 0.5, -0.5, 0.35), (0.48, 0.2, 0.32), "skin_corrupt" if s > 0 else "skin")
    for x in (-0.22, 0.22):
        for z in (-0.15, -0.42, -0.68):
            t.box((0.36, 0.1, 0.22), "skin", pos=(x, -0.58, z), top=(0.9, 1))
    skin_limbs(o, "skin", muscle=1.12)
    band(o("LeftUpperArm"), -0.3, 0.45, 0.66, 0.66, 0.18, "skin_corrupt")
    # Leather apron with suspenders, rope belt, axe loop.
    t.box((1.5, 0.1, 1.25), "leather", pos=(0, -0.66, -0.25), top=(0.8, 1))
    for s in (1, -1):
        t.box((0.16, 0.06, 1.7), "leather_strap", pos=(s * 0.45, -0.66, 0.05), rot=(0, s * -8, 0))
        t.box((0.16, 0.06, 1.7), "leather_strap", pos=(s * 0.45, 0.62, 0.05), rot=(0, s * 8, 0))
    lt = o("LowerTorso")
    lt.box((1.4, 0.1, 1.1), "leather", pos=(0, -0.68, -0.6), bottom=(0.85, 1))
    belt(o, "rope", buckle=None, h=0.18)
    pouch(o, -0.8)
    band(lt, -0.1, 0.1, 0.25, 0.25, 0.08, "iron", dx=0.8, dy=0.3)  # axe loop
    for pre in ("Left", "Right"):
        wraps(o, pre + "LowerArm", (-0.45, -0.3), "leather_strap", 0.62)
    pants(o, "cloth_dark", baggy=1.03)
    shoes(o, "leather_strap", tall=0.7, cuff="fur_dark")
    o.crystals("LeftUpperArm", 4, (0.45, 0.0, 0.3), (0.1, 0.3, 0.2), (1, 0, 0.6),
               length=(0.18, 0.35), radius=(0.04, 0.07))
    o.crystals("UpperTorso", 4, (0.0, 0.6, 0.3), (0.05, 0.02, 0.4), (0, 1, 0.4),
               length=(0.2, 0.4), radius=(0.05, 0.08))
    return o


def wolf_rider():
    o = Outfit("WolfRider", corruption=0.35, seed=14)
    cyclops_head(o, ears=False)
    # Wolf-pelt hood: fur over the head with ears and the wolf's brow over the eye.
    h = o("Head")
    h.shell([(0.25, 0.72, 0.72, 0.22, 0, 0.05), (0.62, 0.62, 0.64, 0.22, 0, 0.05)], "fur_dark",
            tip=(0, 0.1, 0.82))
    h.box((0.8, 0.5, 0.26), "fur_dark", pos=(0, -0.6, 0.62), top=(0.6, 0.8), rot=(-10, 0, 0))
    h.box((0.3, 0.3, 0.14), "black", pos=(0, -0.86, 0.56))
    for s in (1, -1):
        h.spike((s * 0.38, -0.05, 0.75), (s * 0.3, 0.1, 1), 0.45, 0.14, "fur_dark", sides=4)
        h.spike((s * 0.2, -0.85, 0.5), (s * 0.1, -0.5, -1), 0.14, 0.03, "bone", sides=4)
    h.box((1.5, 0.3, 1.25), "fur_dark", pos=(0, 0.66, -0.05), bottom=(1.1, 1))
    # Leather armor with a fur mantle and bone trinkets.
    skin_limbs(o, "skin", upper=False)
    shirt(o, "cloth_dark", sleeves="upper")
    t = o("UpperTorso")
    t.shell([(-0.82, 1.1, 0.6, 0.2), (0.62, 1.13, 0.63, 0.22)], "leather")
    for z in (-0.5, -0.1, 0.3):
        t.box((1.6, 0.06, 0.08), "leather_strap", pos=(0, -0.64, z))
    blob(t, (0, 0, 0.8), (1.3, 0.8, 0.35), "fur_dark", sides=10)
    for i in range(10):
        a = i / 9
        t.spike((-1.0 + 2 * a, 0.3, 0.75), (-1 + 2 * a, 0.6, 0.6), 0.4, 0.14, "fur_dark", sides=4)
    strap_diagonal(o, side=1)
    for i in range(5):
        t.spike((-0.35 + 0.17 * i, -0.66, 0.25 - 0.13 * i), (0, -0.3, -1), 0.18, 0.04, "bone", sides=4)
    for s, pre in ((1, "Left"), (-1, "Right")):
        ua = o(pre + "UpperArm")
        ua.shell([(0.15, 0.7, 0.7, 0.2, s * 0.08, 0), (0.6, 0.62, 0.62, 0.2, s * 0.05, 0)], "leather")
        blob(ua, (s * 0.15, 0, 0.62), (0.7, 0.68, 0.22), "fur_dark")
    belt(o, "leather_strap")
    lt = o("LowerTorso")
    for x in (-0.55, 0.55):
        lt.spike((x, -0.67, -0.12), (0, -0.2, -1), 0.3, 0.06, "bone", sides=4)
    tunic_skirt(o, "leather", length=0.85)
    lt.cloth([0.55, 0.75, 0.95, 1.12], -0.2, [-1.3, -1.55, -1.4, -1.2], -0.7, "fur", sag=-0.03)
    bracers(o, "leather_strap")
    gloves(o, "leather")
    pants(o, "cloth_dark")
    for pre in ("Left", "Right"):
        wraps(o, pre + "LowerLeg", (-0.35, -0.1, 0.15, 0.4), "fur", 0.62)
    shoes(o, "leather_strap")
    o.crystals("LeftUpperArm", 5, (0.55, 0, 0.55), (0.15, 0.3, 0.15), (1, 0, 1),
               length=(0.2, 0.45), radius=(0.04, 0.08))
    o.crystals("LeftLowerArm", 3, (0.6, 0, 0.0), (0.03, 0.3, 0.3), (1, 0, 0.3),
               length=(0.15, 0.3), radius=(0.03, 0.06))
    band(o("LeftLowerArm"), 0.2, 0.5, 0.6, 0.6, 0.16, "skin_corrupt")
    return o


def all_stage1():
    return [villager(), hunter(), woodcutter(), wolf_rider()]

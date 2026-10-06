"""Sculpted armour: every R15 part is ONE closed, smooth mesh - the part itself, padded out
and pushed into shape (a pauldron bulging from the shoulder, a pointed bevor, a knee cop, a
flared cuff) - with no separate floating pieces. All the detail (plate seams, rolled rims,
rivets, engraving, the glowing visor) is painted into the character's template
(armorpaint.py), which this mesh is UV-projected onto directly.

Coordinates are part-local (part centre at the origin, front = -Y, character's left = +X).
"""
import math

import bmesh
from mathutils import Vector

import style2

# R15 part sizes on the Studio mesh (x, y, z) - the body is a set of boxes.
SIZE = {"Head": (1.2, 1.2, 1.2), "UpperTorso": (2.0, 1.0, 1.6), "LowerTorso": (2.0, 1.0, 0.4),
        "UpperArm": (1.0, 1.0, 1.17), "LowerArm": (1.0, 1.0, 1.05), "Hand": (1.0, 1.0, 0.3),
        "UpperLeg": (1.0, 1.0, 1.22), "LowerLeg": (1.0, 1.0, 1.19), "Foot": (1.0, 1.0, 0.3)}


def kind_of(part):
    for k in ("UpperArm", "LowerArm", "Hand", "UpperLeg", "LowerLeg", "Foot"):
        if part.endswith(k):
            return k
    return part


def shell(part, pad=(0.07, 0.07, 0.04), bevel=0.22, cuts=5, center=(0, 0, 0), scale=(1, 1, 1)):
    """The part's box, padded and rounded, finely subdivided so it can be pushed around."""
    sx, sy, sz = SIZE[kind_of(part)]
    dims = Vector(((sx + 2 * pad[0]) * scale[0], (sy + 2 * pad[1]) * scale[1], (sz + 2 * pad[2]) * scale[2]))
    bm = style2.rounded_box(dims, min(bevel, min(dims) * 0.45), center)
    bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=cuts, use_grid_fill=True)
    bm.normal_update()
    return bm


def deform(bm, fn):
    """fn(co, normal) -> displacement vector. Normals are refreshed afterwards."""
    bm.normal_update()
    moves = [(v, fn(v.co.copy(), v.normal.copy())) for v in bm.verts]
    for v, d in moves:
        v.co += d
    bm.normal_update()


def gauss(d2, r):
    return math.exp(-d2 / (r * r))


def bulge(bm, center, radius, height, axis=None):
    """A smooth dome pushed out of the surface (pauldron, knee cop, elbow, pec)."""
    c = Vector(center)

    def fn(co, n):
        w = gauss((co - c).length_squared, radius)
        return (Vector(axis).normalized() if axis else n) * height * w
    deform(bm, fn)


def keel(bm, amount, width, peak_z, half, sharp=2.0):
    """Push the front centre line forward: a ridge whose depth peaks at peak_z.
    sharp=2 gives a soft ')' profile; a bigger half-width with a narrow 'width' a '>'."""
    def fn(co, n):
        if co.y > 0:
            return Vector()
        bell = max(0.0, 1 - abs((co.z - peak_z) / half) ** sharp)
        front = min(1.0, -co.y / 0.3)
        return Vector((0, -amount * gauss(co.x * co.x, width) * bell * front, 0))
    deform(bm, fn)


def ridge(bm, height, width, axis="x", zmin=0.0, ylim=(-9, 9)):
    """Raise a crest along a centre line on the top (crest of a helm, spine of a plate)."""
    def fn(co, n):
        if co.z < zmin or not ylim[0] < co.y < ylim[1]:
            return Vector()
        d = co.x if axis == "x" else co.y
        return Vector((0, 0, height * gauss(d * d, width) * min(1.0, (co.z - zmin) / 0.15)))
    deform(bm, fn)


def flare(bm, z0, z1, k):
    """Widen x/y progressively from z0 (no change) to z1 (scale 1 + k): cuffs, skirts."""
    def fn(co, n):
        t = (co.z - z0) / (z1 - z0)
        if t <= 0:
            return Vector()
        t = min(1.0, t)
        return Vector((co.x * k * t, co.y * k * t, 0))
    deform(bm, fn)


def taper_top(bm, z0, z1, k):
    """Narrow toward the top (a pointed dome / a tall egg helm)."""
    def fn(co, n):
        t = (co.z - z0) / (z1 - z0)
        if t <= 0:
            return Vector()
        t = min(1.0, t)
        return Vector((-co.x * k * t, -co.y * k * t, 0))
    deform(bm, fn)


def terrace(bm, z_top, step, lip, weight=lambda co: 1.0, drop=0.0):
    """Stepped lames carved into the surface: each band of height `step` below z_top swells
    outward toward its lower edge and then steps back in - overlapping plates in one mesh.
    `drop` bends the bands down toward the outside (x) so they curve like shingles."""
    def fn(co, n):
        if co.z > z_top:
            return Vector()
        w = weight(co)
        if w <= 0:
            return Vector()
        zz = z_top - co.z - drop * abs(co.x)
        frac = (zz / step) % 1.0
        out = Vector((n.x, n.y, 0))
        if out.length < 1e-4:
            return Vector()
        return out.normalized() * lip * (frac ** 1.5) * w
    deform(bm, fn)


def move(bm, fn):
    deform(bm, lambda co, n: fn(co))


def to_mesh(bm, part, name):
    """UV-project onto the painted template (style2 layout) and make a smooth mesh."""
    import bpy
    style2.project(bm, part)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.uv_layers[0].name = "UVMap"
    for poly in me.polygons:
        poly.use_smooth = True
    return me


# ---------------------------------------------------------------------------
# White Knight (silver knight reference)
def white(part):
    k = kind_of(part)
    side = 1 if part.startswith("Left") else -1
    if part == "Head":
        # Close helm: a tall dome, a '>' bevor peaking at mid-face, a crest along the top.
        bm = shell(part, pad=(0.0, 0.03, 0.06), bevel=0.5, cuts=6, center=(0, 0, 0.05), scale=(0.94, 1.0, 1.05))
        taper_top(bm, 0.25, 0.75, 0.18)
        keel(bm, 0.2, 0.2, -0.12, 0.62, sharp=1.4)
        ridge(bm, 0.14, 0.07, zmin=0.38, ylim=(-0.5, 0.55))
        return bm
    if part == "UpperTorso":
        # Breastplate: a full rounded 'pigeon' chest and a slight central keel; a high collar.
        bm = shell(part, pad=(0.08, 0.1, 0.05), bevel=0.32, cuts=6)
        bulge(bm, (0, -0.6, 0.2), 0.62, 0.12, axis=(0, -1, 0))
        keel(bm, 0.05, 0.1, 0.0, 0.8)
        bulge(bm, (0, 0, 0.82), 0.45, 0.1, axis=(0, 0, 1))
        return bm
    if part == "LowerTorso":
        bm = shell(part, pad=(0.1, 0.11, 0.06), bevel=0.18, cuts=8)
        flare(bm, 0.0, -0.26, 0.06)
        terrace(bm, 0.16, 0.14, 0.04)  # faulds
        return bm
    if k == "UpperArm":
        # Great rounded pauldron swelling from the top and outside of the shoulder.
        bm = shell(part, pad=(0.06, 0.06, 0.03), bevel=0.3, cuts=12)
        bulge(bm, (side * 0.3, 0, 0.45), 0.55, 0.3)
        bulge(bm, (side * 0.45, 0, 0.05), 0.5, 0.16)
        # Four lames stepping down the outside of the shoulder.
        terrace(bm, 0.42, 0.2, 0.07, weight=lambda co: max(0.0, min(1.0, (co.x * side + 0.15) / 0.3)), drop=0.12)
        return bm
    if k == "LowerArm":
        bm = shell(part, pad=(0.06, 0.06, 0.02), bevel=0.3, cuts=5)
        bulge(bm, (0, 0.5, 0.4), 0.32, 0.14)  # couter
        flare(bm, -0.2, -0.56, 0.22)  # big flared gauntlet cuff
        return bm
    if k == "Hand":
        bm = shell(part, pad=(0.06, 0.06, 0.04), bevel=0.14, cuts=4)
        return bm
    if k == "UpperLeg":
        bm = shell(part, pad=(0.08, 0.08, 0.03), bevel=0.3, cuts=10)
        flare(bm, 0.25, 0.62, 0.08)  # tassets flaring at the hip
        terrace(bm, 0.62, 0.17, 0.05, weight=lambda co: max(0.0, min(1.0, (co.z - 0.05) / 0.15)))
        terrace(bm, -0.38, 0.11, 0.035, weight=lambda co: max(0.0, min(1.0, (-0.08 - co.z) / 0.1)))  # knee lames
        return bm
    if k == "LowerLeg":
        bm = shell(part, pad=(0.06, 0.07, 0.03), bevel=0.3, cuts=5)
        bulge(bm, (0, -0.55, 0.45), 0.3, 0.16)  # round knee cop
        bulge(bm, (side * 0.45, -0.3, 0.45), 0.22, 0.08)  # knee wing
        flare(bm, -0.25, -0.62, 0.08)
        return bm
    if k == "Foot":
        bm = shell(part, pad=(0.06, 0.08, 0.04), bevel=0.12, cuts=4)
        keel(bm, 0.22, 0.18, -0.05, 0.3, sharp=2)  # pointed sabaton
        return bm
    raise KeyError(part)


BUILDERS = {"white": white}

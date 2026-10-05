"""One-Horn Cyclops - low-poly armor for a Roblox R15 (Block) character.

Run:  python3 onehorn/build_onehorn.py     (needs `pip install bpy==4.2.0 pillow`)

No armature. Every armor piece is modelled around one R15 body part at the
real R15 Block-rig size, and named after it:

    <R15PartName>_Armor   textured plates / leather / cloth
    <R15PartName>_Glow    purple corruption (eye, chest V, horn, crystals)

In Studio, roblox/OneHornArmor.server.lua welds each piece onto the body part
with the same name, using the size/offset table this script generates.

Blender units = studs. Character faces -Y, its left side is +X.
Outputs: export/onehorn_armor.fbx, export/onehorn_greatsword.fbx, .blend,
export/onehorn_texture.png, renders/*.png, roblox/OneHornArmor.server.lua
"""
import math
import os
import random
import sys

import bpy  # must come first: it makes bmesh/mathutils importable
import bmesh
from mathutils import Euler, Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
EXPORT_DIR = os.path.join(HERE, "export")
RENDER_DIR = os.path.join(HERE, "renders")
ROBLOX_DIR = os.path.join(HERE, "roblox")

# ---------------------------------------------------------------------------
# R15 Block rig: part sizes in studs (Roblox X, Y, Z) and preview positions.
# Head is the visible 1.2 stud block head.
R15_SIZE = {
    "Head": (1.2, 1.2, 1.2),
    "UpperTorso": (2.0, 1.6, 1.0),
    "LowerTorso": (2.0, 0.4, 1.0),
    "LeftUpperArm": (1.0, 1.169, 1.0),
    "LeftLowerArm": (1.0, 1.052, 1.0),
    "LeftHand": (1.0, 0.3, 1.0),
    "RightUpperArm": (1.0, 1.169, 1.0),
    "RightLowerArm": (1.0, 1.052, 1.0),
    "RightHand": (1.0, 0.3, 1.0),
    "LeftUpperLeg": (1.0, 1.217, 1.0),
    "LeftLowerLeg": (1.0, 1.193, 1.0),
    "LeftFoot": (1.0, 0.4, 1.0),
    "RightUpperLeg": (1.0, 1.217, 1.0),
    "RightLowerLeg": (1.0, 1.193, 1.0),
    "RightFoot": (1.0, 0.4, 1.0),
}
FOOT_Z = 0.2
LOWER_LEG_Z = 0.4 + 1.193 / 2
UPPER_LEG_Z = 0.4 + 1.193 + 1.217 / 2
LOWER_TORSO_Z = 2.81 + 0.2
UPPER_TORSO_Z = 3.21 + 0.8
HEAD_Z = 4.81 + 0.6
UPPER_ARM_Z = 4.81 - 1.169 / 2
LOWER_ARM_Z = 4.81 - 1.169 - 1.052 / 2
HAND_Z = 4.81 - 1.169 - 1.052 - 0.15
R15_POS = {
    "Head": (0, 0, HEAD_Z),
    "UpperTorso": (0, 0, UPPER_TORSO_Z),
    "LowerTorso": (0, 0, LOWER_TORSO_Z),
    "LeftUpperArm": (1.5, 0, UPPER_ARM_Z),
    "LeftLowerArm": (1.5, 0, LOWER_ARM_Z),
    "LeftHand": (1.5, 0, HAND_Z),
    "RightUpperArm": (-1.5, 0, UPPER_ARM_Z),
    "RightLowerArm": (-1.5, 0, LOWER_ARM_Z),
    "RightHand": (-1.5, 0, HAND_Z),
    "LeftUpperLeg": (0.5, 0, UPPER_LEG_Z),
    "LeftLowerLeg": (0.5, 0, LOWER_LEG_Z),
    "LeftFoot": (0.5, 0, FOOT_Z),
    "RightUpperLeg": (-0.5, 0, UPPER_LEG_Z),
    "RightLowerLeg": (-0.5, 0, LOWER_LEG_Z),
    "RightFoot": (-0.5, 0, FOOT_Z),
}

# ---------------------------------------------------------------------------
# Texture: a painted 4x4 atlas of materials (see texture_gen.py). Every face is
# projected onto the whole tile of its material, so each face reads as a plate
# with beveled edges, rivets, scratches and grime.
sys.path.insert(0, HERE)
from texture_gen import TILES, build_atlas, tile_rect  # noqa: E402


def face_uvs(face, tile):
    """Planar-project a face (tile 'up' = world up where possible) onto its tile."""
    n = face.normal
    t = Vector((1, 0, 0)) if abs(n.z) > 0.9 else Vector((0, 0, 1)).cross(n).normalized()
    b = n.cross(t)
    us = [l.vert.co.dot(t) for l in face.loops]
    vs = [l.vert.co.dot(b) for l in face.loops]
    u0, v0, size = tile_rect(tile)
    m = 3 / 1024  # keep clear of neighbouring tiles
    def norm(x, lo, hi):
        return (x - lo) / (hi - lo) if hi - lo > 1e-6 else 0.5
    return [(u0 + m + norm(u, min(us), max(us)) * (size - 2 * m),
             v0 + m + norm(v, min(vs), max(vs)) * (size - 2 * m)) for u, v in zip(us, vs)]


# ---------------------------------------------------------------------------
# Geometry helpers. Everything is built into a bmesh in part-local space.
class Piece:
    def __init__(self):
        self.bm = bmesh.new()
        self.col = self.bm.faces.layers.int.new("col")

    def _faces(self, verts, faces, color):
        vs = [self.bm.verts.new(v) for v in verts]
        for f in faces:
            face = self.bm.faces.new([vs[i] for i in f])
            face[self.col] = TILES.index(color)

    def loft(self, rings, color, pos=(0, 0, 0), rot=(0, 0, 0), tip=None, base=None):
        """rings: list of (z, profile) where profile is a list of (x, y) points.
        tip/base: optional (x, y, z) apex to close the top/bottom with a point."""
        m = Euler([math.radians(a) for a in rot]).to_matrix()
        p = Vector(pos)
        verts, faces = [], []
        n = len(rings[0][1])
        for z, prof in rings:
            verts += [tuple(m @ Vector((x, y, z)) + p) for x, y in prof]
        for r in range(len(rings) - 1):
            a, b = r * n, (r + 1) * n
            for i in range(n):
                j = (i + 1) % n
                faces.append((a + i, a + j, b + j, b + i))
        last = (len(rings) - 1) * n
        if tip is not None:
            verts.append(tuple(m @ Vector(tip) + p))
            t = len(verts) - 1
            faces += [(last + i, last + (i + 1) % n, t) for i in range(n)]
        else:
            faces.append(tuple(last + i for i in range(n)))
        if base is not None:
            verts.append(tuple(m @ Vector(base) + p))
            t = len(verts) - 1
            faces += [((i + 1) % n, i, t) for i in range(n)]
        else:
            faces.append(tuple(reversed(range(n))))
        self._faces(verts, faces, color)

    def box(self, size, color, pos=(0, 0, 0), rot=(0, 0, 0), top=(1, 1), bottom=(1, 1),
            shift=(0, 0)):
        """Box with optional tapered top/bottom and top shifted by (dx, dy)."""
        w, d, h = (s / 2 for s in size)
        rings = [
            (-h, rect(w * bottom[0], d * bottom[1])),
            (h, [(x + shift[0], y + shift[1]) for x, y in rect(w * top[0], d * top[1])]),
        ]
        self.loft(rings, color, pos, rot)

    def shell(self, rings, color, pos=(0, 0, 0), rot=(0, 0, 0), tip=None):
        """Chamfered-box armor shell. rings: (z, half_w, half_d, chamfer[, dx, dy])."""
        lofted = []
        for r in rings:
            z, w, d, c = r[:4]
            dx, dy = (r[4], r[5]) if len(r) > 4 else (0, 0)
            lofted.append((z, [(x + dx, y + dy) for x, y in chamfer_rect(w, d, c)]))
        self.loft(lofted, color, pos, rot, tip=tip)

    def spike(self, base, direction, length, radius, color, sides=5, twist=0.0):
        """Crystal / spike: a bipyramid pointing along direction."""
        d = Vector(direction).normalized()
        m = d.to_track_quat("Z", "Y").to_matrix() @ Matrix.Rotation(twist, 3, "Z")
        prof = [(radius * math.cos(2 * math.pi * i / sides),
                 radius * math.sin(2 * math.pi * i / sides)) for i in range(sides)]
        verts, faces = [], []
        mid = length * 0.28
        verts += [tuple(m @ Vector((x, y, mid)) + Vector(base)) for x, y in prof]
        verts.append(tuple(m @ Vector((0, 0, length)) + Vector(base)))
        verts.append(tuple(m @ Vector((0, 0, -length * 0.12)) + Vector(base)))
        t, b = sides, sides + 1
        for i in range(sides):
            j = (i + 1) % sides
            faces.append((i, j, t))
            faces.append((j, i, b))
        self._faces(verts, faces, color)

    def cloth(self, xs, top_z, bottoms, y, color, thick=0.05, sag=0.0, pos=(0, 0, 0),
              rot=(0, 0, 0)):
        """Tattered cloth flap: a strip of columns with a jagged bottom edge.
        sag bows the flap outward (y) in the middle."""
        m = Euler([math.radians(a) for a in rot]).to_matrix()
        p = Vector(pos)
        n = len(xs)
        span = (xs[-1] - xs[0]) or 1
        verts = []
        for side in (0, 1):  # 0 = outer, 1 = inner
            for i, x in enumerate(xs):
                u = (x - xs[0]) / span
                # The inner layer sits `thick` closer to the body.
                yy = y + sag * math.sin(math.pi * u) - (math.copysign(thick, y) if side else 0)
                verts.append(tuple(m @ Vector((x, yy, top_z)) + p))
                verts.append(tuple(m @ Vector((x, yy, bottoms[i])) + p))
        faces = []
        o = 2 * n  # offset of inner layer
        for i in range(n - 1):
            t0, b0, t1, b1 = 2 * i, 2 * i + 1, 2 * i + 2, 2 * i + 3
            faces.append((t0, t1, b1, b0))  # outer
            faces.append((o + t0, o + b0, o + b1, o + t1))  # inner
            faces.append((b0, b1, o + b1, o + b0))  # bottom edge
            faces.append((t0, o + t0, o + t1, t1))  # top edge
        faces.append((0, 1, o + 1, o + 0))  # side ends
        last = 2 * (n - 1)
        faces.append((last, o + last, o + last + 1, last + 1))
        self._faces(verts, faces, color)

    def to_object(self, name, material, location):
        bm = self.bm
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.normal_update()
        uv = bm.loops.layers.uv.new("UVMap")
        for f in bm.faces:
            for loop, coords in zip(f.loops, face_uvs(f, TILES[f[self.col]])):
                loop[uv].uv = coords
        mesh = bpy.data.meshes.new(name)
        bm.to_mesh(mesh)
        bm.free()
        for poly in mesh.polygons:
            poly.use_smooth = False
        mesh.materials.append(material)
        obj = bpy.data.objects.new(name, mesh)
        obj.location = location
        bpy.context.collection.objects.link(obj)
        return obj


def rect(w, d):
    return [(w, -d), (w, d), (-w, d), (-w, -d)]


def chamfer_rect(w, d, c):
    return [(w, -d + c), (w, d - c), (w - c, d), (-w + c, d),
            (-w, d - c), (-w, -d + c), (-w + c, -d), (w - c, -d)]


# ---------------------------------------------------------------------------
# Armor, one function per body region. `side` is +1 for Left (+X), -1 for Right.
# The concept's corruption grows on the character's left side, so left pieces use
# the cracked "plate_corrupt" texture and carry the crystals.
def band(p, z0, z1, w, d, c, color, grow=0.0, dx=0.0, dy=0.0, rot=(0, 0, 0)):
    """A ring of armor between z0 and z1, flaring by `grow` toward the top."""
    p.shell([(z0, w, d, c, dx, dy), (z1, w + grow, d + grow, c, dx, dy)], color, rot=rot)


def crystals(g, rnd, count, base_fn, dir_fn, length, radius):
    for _ in range(count):
        g.spike(base_fn(), dir_fn(), rnd.uniform(*length), rnd.uniform(*radius), "glow",
                sides=5, twist=rnd.uniform(0, 3))


def head():
    a, g = Piece(), Piece()
    # Helmet bowl, brow band and crest.
    a.shell([(-0.5, 0.72, 0.72, 0.22), (0.15, 0.76, 0.76, 0.24), (0.52, 0.66, 0.68, 0.26),
             (0.74, 0.4, 0.42, 0.16)], "plate_dark", tip=(0, 0.02, 0.86))
    band(a, 0.1, 0.3, 0.79, 0.79, 0.25, "plate_trim")
    a.box((0.14, 1.42, 0.24), "plate_trim", pos=(0, 0, 0.66), top=(0.5, 0.9))
    # Face: visor, brow over the eye, nose ridge, breaths and pointed chin.
    a.box((1.22, 0.14, 0.52), "plate_mid", pos=(0, -0.76, -0.14), bottom=(0.78, 1))
    a.box((1.14, 0.18, 0.2), "plate_trim", pos=(0, -0.8, 0.22), rot=(-12, 0, 0), top=(0.92, 1))
    a.box((1.0, 0.06, 0.11), "black", pos=(0, -0.84, 0.07))
    a.box((0.13, 0.12, 0.58), "plate_trim", pos=(0, -0.85, -0.22), bottom=(0.45, 1))
    for x in (-0.36, -0.24, 0.24, 0.36):
        a.box((0.05, 0.05, 0.2), "black", pos=(x, -0.84, -0.2))
    a.box((0.62, 0.16, 0.3), "plate_mid", pos=(0, -0.74, -0.58), bottom=(0.15, 0.6))
    # Cheek guards and layered neck guard.
    for s in (1, -1):
        a.box((0.13, 0.78, 0.86), "plate_mid", pos=(s * 0.8, -0.1, -0.18), bottom=(1, 0.6))
        a.box((0.1, 0.3, 0.3), "plate_trim", pos=(s * 0.86, -0.15, 0.05), rot=(0, 0, 45))
    for i in range(3):
        a.box((1.36 - 0.1 * i, 0.14, 0.22), "plate_mid" if i % 2 else "plate_dark",
              pos=(0, 0.74 + 0.05 * i, -0.36 - 0.17 * i), rot=(22, 0, 0))
    # The horn: dark metal fading to purple, set in a trim collar.
    band(a, 0.66, 0.78, 0.22, 0.22, 0.07, "plate_trim", dy=-0.12)
    a.spike((0, -0.12, 0.72), (0, 0.18, 1), 1.4, 0.17, "horn", sides=6)
    # Cyclops eye and corruption creeping over the left side of the helmet.
    g.box((0.22, 0.05, 0.22), "glow", pos=(0, -0.875, 0.07), rot=(0, 45, 0))
    g.box((0.5, 0.03, 0.035), "glow", pos=(0, -0.873, 0.07))
    rnd = random.Random(1)
    crystals(g, rnd, 5, lambda: (rnd.uniform(0.6, 0.78), rnd.uniform(-0.3, 0.4), rnd.uniform(0.15, 0.6)),
             lambda: (1, rnd.uniform(-0.4, 0.4), rnd.uniform(0.3, 1.0)), (0.2, 0.45), (0.05, 0.09))
    for _ in range(3):
        g.spike((rnd.uniform(-0.12, 0.12), -0.12, 0.74), (rnd.uniform(-0.5, 0.5), rnd.uniform(-0.4, 0.4), 1),
                rnd.uniform(0.15, 0.3), 0.05, "glow", sides=5)
    return a, g


def upper_torso():
    a, g = Piece(), Piece()
    # Upper breastplate and three abdomen lames, each flaring over the one below.
    a.shell([(-0.02, 1.1, 0.64, 0.22), (0.45, 1.15, 0.69, 0.24), (0.84, 1.0, 0.6, 0.24)],
            "plate_dark")
    for i in range(3):
        z1 = -0.02 - 0.27 * i
        band(a, z1 - 0.3, z1, 1.06, 0.62, 0.2, "plate_mid" if i % 2 == 0 else "plate_dark",
             grow=0.04)
    # Pectoral plates (left one cracked), center ridge.
    for s in (1, -1):
        a.box((0.84, 0.1, 0.64), "plate_corrupt" if s > 0 else "plate_mid",
              pos=(s * 0.5, -0.71, 0.42), rot=(0, s * -8, 0), bottom=(0.9, 1))
    a.box((0.17, 0.13, 1.55), "plate_trim", pos=(0, -0.73, 0.0), top=(1, 0.6))
    # Gorget with flared collar plates.
    a.shell([(0.7, 0.68, 0.52, 0.16), (1.02, 0.6, 0.46, 0.14)], "plate_trim")
    for s in (1, -1):
        a.box((0.5, 0.95, 0.16), "plate_mid", pos=(s * 0.64, 0, 0.9), rot=(0, s * -22, 0))
    # Back: plate, spine ridge, torn cloth and crossed straps with a buckle.
    a.box((1.8, 0.1, 1.3), "plate_mid", pos=(0, 0.69, 0.12))
    a.box((0.15, 0.1, 1.45), "plate_trim", pos=(0, 0.75, 0.05))
    a.cloth([-0.75, -0.5, -0.25, 0.0, 0.25, 0.5, 0.75], 0.75,
            [-0.9, -1.35, -1.0, -1.5, -1.1, -1.4, -0.95], 0.78, "cloth_dark", sag=0.04)
    for s in (1, -1):
        a.box((0.22, 0.06, 2.0), "leather_strap", pos=(0, 0.86, 0.05), rot=(0, s * 38, 0))
    a.box((0.28, 0.06, 0.28), "buckle", pos=(0, 0.9, 0.05))
    # Glowing V with its stem, and cracks breaking out of the left chest.
    for s in (1, -1):
        g.box((0.09, 0.06, 0.74), "glow", pos=(s * 0.22, -0.8, 0.33), rot=(0, s * 38, 0))
    g.box((0.09, 0.06, 0.55), "glow", pos=(0, -0.8, -0.16))
    rnd = random.Random(4)
    crystals(g, rnd, 4, lambda: (rnd.uniform(0.75, 0.95), -0.72, rnd.uniform(0.1, 0.7)),
             lambda: (rnd.uniform(0.3, 1), -1, rnd.uniform(-0.2, 0.8)), (0.15, 0.3), (0.04, 0.07))
    return a, g


def lower_torso():
    a, g = Piece(), Piece()
    # Main belt with a big square buckle, and a second, slanted belt.
    band(a, -0.22, 0.2, 1.14, 0.66, 0.2, "leather_strap")
    a.box((0.52, 0.1, 0.44), "buckle", pos=(0, -0.7, 0))
    a.box((0.28, 0.05, 0.22), "black", pos=(0, -0.75, 0))
    a.box((0.05, 0.05, 0.22), "buckle", pos=(0.04, -0.77, 0))
    band(a, -0.36, -0.22, 1.17, 0.69, 0.21, "leather", rot=(0, 7, 0))
    a.box((0.24, 0.08, 0.2), "buckle", pos=(0.5, -0.72, -0.24), rot=(0, 7, 0))
    # Pouches.
    for s, y in ((1, -0.55), (-1, -0.55), (-1, 0.5)):
        a.box((0.34, 0.26, 0.4), "leather", pos=(s * 0.8, y, -0.22))
        a.box((0.37, 0.29, 0.13), "leather_strap", pos=(s * 0.8, y, -0.04))
    # Chainmail skirt under everything.
    a.shell([(-1.05, 1.18, 0.7, 0.22), (-0.15, 1.1, 0.64, 0.2)], "chainmail")
    # Hip tassets: two overlapping plates per side.
    for s in (1, -1):
        for i in range(2):
            a.box((0.17, 1.02 - 0.06 * i, 0.5), "plate_mid" if i == 0 else "plate_dark",
                  pos=(s * (1.16 + 0.03 * i), 0, -0.4 - 0.38 * i), rot=(0, s * 12, 0),
                  bottom=(1, 0.88))
    # Tattered tabard front and back, with ragged side strips.
    xs = [-0.58, -0.43, -0.29, -0.14, 0.0, 0.14, 0.29, 0.43, 0.58]
    a.cloth(xs, -0.15, [-1.55, -1.9, -1.62, -2.05, -1.72, -2.0, -1.6, -1.85, -1.5], -0.74,
            "cloth", sag=-0.06)
    a.cloth(xs, -0.15, [-1.75, -2.1, -1.85, -2.2, -1.9, -2.15, -1.8, -2.05, -1.7], 0.74,
            "cloth_dark", sag=0.06)
    for s in (1, -1):
        a.cloth([s * 0.66, s * 0.8, s * 0.95], -0.2, [-1.2, -1.55, -1.25], -0.72, "cloth_dark",
                sag=-0.03)
    return a, g


def upper_arm(side):
    a, g = Piece(), Piece()
    corrupt = "plate_corrupt" if side > 0 else "plate_dark"
    # Mail sleeve, rerebrace and a trim lame at the elbow.
    band(a, -0.6, 0.45, 0.55, 0.55, 0.14, "chainmail")
    band(a, -0.5, 0.3, 0.6, 0.6, 0.15, corrupt)
    band(a, -0.62, -0.46, 0.63, 0.63, 0.16, "plate_trim")
    # Big layered pauldron: dome plus four lames stepping down the outside.
    a.shell([(0.22, 0.84, 0.78, 0.24, side * 0.12, 0), (0.6, 0.78, 0.72, 0.24, side * 0.06, 0),
             (0.88, 0.44, 0.46, 0.16, 0, 0)], corrupt)
    band(a, 0.12, 0.26, 0.86, 0.8, 0.25, "plate_trim", dx=side * 0.12)
    for i in range(4):
        a.box((0.54, 1.5 - 0.1 * i, 0.32), "plate_mid" if i % 2 == 0 else "plate_dark",
              pos=(side * (0.64 + 0.05 * i), 0, 0.44 - 0.22 * i), rot=(0, side * 30, 0),
              bottom=(1, 0.9))
    # Front/back edge plates so the pauldron reads chunky from the side too.
    for y in (-1, 1):
        a.box((0.9, 0.12, 0.5), "plate_mid", pos=(side * 0.2, y * 0.82, 0.45), rot=(y * -12, 0, 0),
              bottom=(0.85, 1))
    rnd = random.Random(10 + side)
    if side > 0:
        # Left shoulder: the corruption bursts out as a large crystal cluster.
        crystals(g, rnd, 12, lambda: (rnd.uniform(0.15, 0.8), rnd.uniform(-0.45, 0.45), rnd.uniform(0.55, 0.9)),
                 lambda: (rnd.uniform(0.1, 1.0), rnd.uniform(-0.6, 0.6), rnd.uniform(0.5, 1.2)),
                 (0.45, 1.15), (0.07, 0.16))
        crystals(g, rnd, 5, lambda: (0.95, rnd.uniform(-0.5, 0.5), rnd.uniform(-0.1, 0.4)),
                 lambda: (1, rnd.uniform(-0.5, 0.5), rnd.uniform(-0.2, 0.6)), (0.25, 0.5), (0.05, 0.1))
    else:
        # Right shoulder: clean steel with a raised, pointed gardbrace.
        a.box((0.16, 1.25, 0.55), "plate_trim", pos=(side * 0.32, 0, 1.0), rot=(0, side * 15, 0),
              top=(1, 0.3))
        for y in (-0.38, 0.0, 0.38):
            a.spike((side * 0.55, y, 0.82), (side * 0.5, 0, 1), 0.4, 0.09, "plate_trim", sides=4)
    return a, g


def lower_arm(side):
    a, g = Piece(), Piece()
    corrupt = "plate_corrupt" if side > 0 else "plate_dark"
    a.shell([(-0.53, 0.56, 0.56, 0.14), (0.5, 0.61, 0.61, 0.15)], corrupt)
    a.box((0.64, 0.12, 0.82), "plate_mid", pos=(0, -0.62, 0.0), bottom=(0.7, 1))
    a.box((0.12, 0.74, 0.82), "plate_mid", pos=(side * 0.62, 0, 0.0), bottom=(1, 0.75))
    band(a, -0.56, -0.42, 0.65, 0.65, 0.16, "plate_trim")
    band(a, -0.02, 0.1, 0.63, 0.63, 0.16, "leather_strap")
    # Couter: elbow plate with a backward spike.
    a.box((0.72, 0.22, 0.46), "plate_trim", pos=(0, 0.63, 0.42), top=(0.8, 1))
    a.spike((0, 0.7, 0.42), (0, 1, 0.2), 0.4, 0.22, "plate_trim", sides=4)
    if side > 0:
        rnd = random.Random(21)
        crystals(g, rnd, 8, lambda: (rnd.uniform(0.55, 0.7), rnd.uniform(-0.45, 0.45), rnd.uniform(-0.45, 0.45)),
                 lambda: (1, rnd.uniform(-0.6, 0.6), rnd.uniform(-0.2, 0.9)), (0.25, 0.6), (0.05, 0.11))
        crystals(g, rnd, 3, lambda: (rnd.uniform(-0.2, 0.3), 0.62, rnd.uniform(-0.3, 0.3)),
                 lambda: (rnd.uniform(-0.2, 0.6), 1, rnd.uniform(0, 0.8)), (0.2, 0.4), (0.05, 0.08))
    return a, g


def hand(side):
    a, g = Piece(), Piece()
    band(a, -0.22, 0.06, 0.54, 0.54, 0.14, "plate_dark")
    a.shell([(0.04, 0.64, 0.64, 0.16), (0.3, 0.71, 0.71, 0.18)], "plate_trim")
    # Knuckle plates and a thumb plate.
    for x in (-0.3, -0.1, 0.1, 0.3):
        a.box((0.17, 0.1, 0.15), "plate_mid", pos=(x, -0.57, -0.1), top=(0.8, 1))
    a.box((0.12, 0.3, 0.26), "plate_mid", pos=(-side * 0.58, -0.25, -0.05))
    if side > 0:
        rnd = random.Random(31)
        crystals(g, rnd, 3, lambda: (0.56, rnd.uniform(-0.3, 0.3), rnd.uniform(-0.1, 0.2)),
                 lambda: (1, rnd.uniform(-0.4, 0.4), rnd.uniform(0, 0.8)), (0.2, 0.35), (0.05, 0.07))
    return a, g


def upper_leg(side):
    a, g = Piece(), Piece()
    a.shell([(-0.55, 0.57, 0.57, 0.15), (0.6, 0.6, 0.6, 0.15)], "plate_dark")
    for i in range(3):
        a.box((0.8, 0.11, 0.3), "plate_mid" if i % 2 == 0 else "plate_dark",
              pos=(0, -0.65, 0.42 - 0.33 * i), rot=(8, 0, 0), bottom=(0.94, 1))
    a.box((0.12, 0.8, 0.9), "plate_mid", pos=(side * 0.62, 0, 0.05), bottom=(1, 0.8))
    for z in (0.22, -0.32):
        band(a, z - 0.06, z + 0.06, 0.63, 0.63, 0.16, "leather_strap")
    return a, g


def lower_leg(side):
    a, g = Piece(), Piece()
    a.shell([(-0.6, 0.56, 0.56, 0.15), (0.48, 0.6, 0.6, 0.15)], "plate_dark")
    band(a, 0.44, 0.6, 0.62, 0.62, 0.16, "plate_trim")
    a.box((0.17, 0.12, 0.95), "plate_trim", pos=(0, -0.62, -0.14), bottom=(0.6, 1))
    band(a, 0.0, 0.1, 0.62, 0.62, 0.16, "leather_strap")
    # Poleyn: knee cop with side wings and a forward point.
    a.box((0.7, 0.22, 0.46), "plate_mid", pos=(0, -0.64, 0.52), top=(0.8, 1), bottom=(0.8, 1))
    for s in (1, -1):
        a.box((0.12, 0.42, 0.44), "plate_trim", pos=(s * 0.42, -0.5, 0.52), rot=(0, s * 20, 0))
    a.spike((0, -0.74, 0.52), (0, -1, 0.1), 0.36, 0.2, "plate_trim", sides=4)
    return a, g


def foot(side):
    a, g = Piece(), Piece()
    a.shell([(-0.2, 0.58, 0.68, 0.14, 0, -0.14), (0.2, 0.56, 0.6, 0.14, 0, -0.04)], "plate_dark")
    band(a, 0.12, 0.28, 0.62, 0.62, 0.16, "plate_trim")
    for i in range(3):
        a.box((1.12 - 0.08 * i, 0.3, 0.13), "plate_mid" if i % 2 == 0 else "plate_dark",
              pos=(0, -0.5 - 0.2 * i, 0.16 - 0.11 * i), rot=(16, 0, 0))
    a.spike((0, -0.88, -0.1), (0, -1, 0.15), 0.3, 0.2, "plate_mid", sides=4)
    a.box((1.12, 1.5, 0.08), "leather_strap", pos=(0, -0.16, -0.21))
    return a, g


def build_armor(armor_mat, glow_mat):
    builders = {
        "Head": head, "UpperTorso": upper_torso, "LowerTorso": lower_torso,
    }
    for prefix, side in (("Left", 1), ("Right", -1)):
        builders[prefix + "UpperArm"] = lambda s=side: upper_arm(s)
        builders[prefix + "LowerArm"] = lambda s=side: lower_arm(s)
        builders[prefix + "Hand"] = lambda s=side: hand(s)
        builders[prefix + "UpperLeg"] = lambda s=side: upper_leg(s)
        builders[prefix + "LowerLeg"] = lambda s=side: lower_leg(s)
        builders[prefix + "Foot"] = lambda s=side: foot(s)
    objects = []
    for part, fn in builders.items():
        armor, glow = fn()
        objects.append(armor.to_object(f"{part}_Armor", armor_mat, R15_POS[part]))
        if len(glow.bm.faces):
            objects.append(glow.to_object(f"{part}_Glow", glow_mat, R15_POS[part]))
        else:
            glow.bm.free()
    return objects


# ---------------------------------------------------------------------------
def build_greatsword(armor_mat, glow_mat):
    """Lightly corrupted greatsword. Grip centered on the origin, blade along +Z."""
    grip, blade, guard, pommel, glow = Piece(), Piece(), Piece(), Piece(), Piece()
    # Grip with leather wraps.
    grip.shell([(-0.65, 0.11, 0.11, 0.04), (0.65, 0.11, 0.11, 0.04)], "leather")
    for z in (-0.4, 0.0, 0.4):
        grip.box((0.26, 0.26, 0.08), "leather_strap", pos=(0, 0, z))
    # Blade: diamond section, slightly leaf-shaped, with a long point.
    def diamond(w, t):
        return [(w, 0), (0, t), (-w, 0), (0, -t)]
    # The lower blade, nearest the guard, is cracked by the corruption.
    blade.loft([(0.72, diamond(0.3, 0.07)), (1.4, diamond(0.34, 0.075)),
                (2.4, diamond(0.33, 0.072))], "blade_corrupt")
    blade.loft([(2.4, diamond(0.33, 0.072)), (3.6, diamond(0.3, 0.065)),
                (5.0, diamond(0.2, 0.05))], "blade", tip=(0, 0, 5.9))
    # Fuller.
    blade.box((0.08, 0.16, 3.2), "black", pos=(0, 0, 2.6), top=(0.5, 1))
    # Jagged teeth along both edges.
    rnd = random.Random(7)
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
    return [
        grip.to_object("Handle", armor_mat, (0, 0, 0)),
        blade.to_object("Blade", armor_mat, (0, 0, 0)),
        guard.to_object("Guard", armor_mat, (0, 0, 0)),
        pommel.to_object("Pommel", armor_mat, (0, 0, 0)),
        glow.to_object("Blade_Glow", glow_mat, (0, 0, 0)),
    ]


# ---------------------------------------------------------------------------
def make_materials(img):
    def mat(name, emission):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        nodes = m.node_tree.nodes
        bsdf = nodes["Principled BSDF"]
        tex = nodes.new("ShaderNodeTexImage")
        tex.image = img
        tex.interpolation = "Linear"
        m.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Metallic"].default_value = 0.0 if emission else 0.35
        bsdf.inputs["Roughness"].default_value = 0.55
        if emission:
            m.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
            bsdf.inputs["Emission Strength"].default_value = 4.0
        return m
    return mat("Armor", False), mat("Glow", True)


def export_fbx(path, objects):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objects:
        o.select_set(True)
    bpy.ops.export_scene.fbx(
        filepath=path,
        use_selection=True,
        object_types={"MESH"},
        mesh_smooth_type="FACE",
        path_mode="COPY",
        embed_textures=True,
        # Blender -Y (character front) -> -Z, Roblox's forward.
        axis_forward="Z",
        axis_up="Y",
    )


def roblox_table(objects):
    """Size and offset (relative to the R15 part center) of each piece in Roblox axes.
    Blender (x, y, z) maps to Roblox (-x, z, y) with the export axes above."""
    lines = []
    for o in sorted(objects, key=lambda o: o.name):
        xs = [v.co.x for v in o.data.vertices]
        ys = [v.co.y for v in o.data.vertices]
        zs = [v.co.z for v in o.data.vertices]
        size = (max(xs) - min(xs), max(zs) - min(zs), max(ys) - min(ys))
        c = ((max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2, (max(zs) + min(zs)) / 2)
        offset = (-c[0], c[2], c[1])
        f = lambda v: ", ".join(f"{x:.4f}" for x in v)
        lines.append(f'\t["{o.name}"] = {{ size = Vector3.new({f(size)}), '
                     f'offset = Vector3.new({f(offset)}) }},')
    return "\n".join(lines)


def write_armor_script(objects):
    template = open(os.path.join(ROBLOX_DIR, "OneHornArmor.template.lua")).read()
    sizes = "\n".join(f'\t{name} = Vector3.new({", ".join(f"{v:g}" for v in s)}),'
                      for name, s in R15_SIZE.items())
    out = template.replace("--@@PIECES@@", roblox_table(objects)).replace("--@@R15SIZES@@", sizes)
    with open(os.path.join(ROBLOX_DIR, "OneHornArmor.server.lua"), "w") as fh:
        fh.write(out)


# ---------------------------------------------------------------------------
def build_body(mat):
    """Plain R15 block body, only for the preview renders (not exported)."""
    objs = []
    for part, (sx, sy, sz) in R15_SIZE.items():
        p = Piece()
        p.box((sx, sz, sy), "body")
        objs.append(p.to_object("Body_" + part, mat, R15_POS[part]))
    return objs


def setup_render():
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 48
    scene.cycles.use_denoising = True
    world = bpy.data.worlds.new("World")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.11, 0.11, 0.12, 1)
    bg.inputs["Strength"].default_value = 1.0
    scene.world = world
    for name, loc, energy, size in (("Key", (-4, -6, 8), 950, 4), ("Fill", (6, -4, 4), 260, 4),
                                    ("Rim", (0, 7, 6), 900, 3)):
        light = bpy.data.lights.new(name, "AREA")
        light.energy, light.size = energy, size
        obj = bpy.data.objects.new(name, light)
        obj.location = loc
        obj.rotation_euler = (Vector((0, 0, 3)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        scene.collection.objects.link(obj)
    floor = Piece()
    floor.box((30, 30, 0.1), "black", pos=(0, 0, -0.05))
    cam = bpy.data.cameras.new("Camera")
    cam.type = "ORTHO"
    cam_obj = bpy.data.objects.new("Camera", cam)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj
    return scene, cam_obj, floor


def render_views(scene, cam, sword_objs):
    views = {
        "front": ((0, -20, 3.0), (0, 0, 3.0), 7.4),
        "side": ((20, 0, 3.0), (0, 0, 3.0), 7.4),
        "back": ((0, 20, 3.0), (0, 0, 3.0), 7.4),
        "hero": ((-9, -14, 6.0), (0, 0, 2.9), 7.6),
    }
    paths = []
    for name, (loc, target, scale) in views.items():
        for o in sword_objs:
            o.hide_render = name != "hero"
        cam.location = loc
        cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        cam.data.ortho_scale = scale
        scene.render.resolution_x, scene.render.resolution_y = 900, 1200
        path = os.path.join(RENDER_DIR, f"onehorn_{name}.png")
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        paths.append(path)
    return paths


def render_sword(scene, cam, sword_objs, hide):
    for o in hide:
        o.hide_render = True
    for o in sword_objs:
        o.hide_render = False
        o.matrix_world = Matrix.Translation((0, 0, 1.5)) @ Matrix.Rotation(math.radians(90), 4, "Y")
    cam.location = (2.3, -20, 1.5)
    cam.rotation_euler = (Vector((2.3, 0, 1.5)) - Vector(cam.location)).to_track_quat("-Z", "Y").to_euler()
    cam.data.ortho_scale = 7.6
    scene.render.resolution_x, scene.render.resolution_y = 1600, 600
    path = os.path.join(RENDER_DIR, "onehorn_greatsword.png")
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path


def contact_sheet(paths, out):
    from PIL import Image
    imgs = [Image.open(p) for p in paths]
    w = sum(i.width for i in imgs)
    h = max(i.height for i in imgs)
    sheet = Image.new("RGB", (w, h))
    x = 0
    for i in imgs:
        sheet.paste(i, (x, 0))
        x += i.width
    sheet.save(out)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version = 0
    for d in (EXPORT_DIR, RENDER_DIR, ROBLOX_DIR):
        os.makedirs(d, exist_ok=True)

    tex_path = build_atlas(os.path.join(EXPORT_DIR, "onehorn_texture.png"))
    img = bpy.data.images.load(tex_path)
    armor_mat, glow_mat = make_materials(img)
    armor = build_armor(armor_mat, glow_mat)
    sword = build_greatsword(armor_mat, glow_mat)
    print("armor pieces:", len(armor), "faces:", sum(len(o.data.polygons) for o in armor))
    print("sword faces:", sum(len(o.data.polygons) for o in sword))

    export_fbx(os.path.join(EXPORT_DIR, "onehorn_armor.fbx"), armor)
    export_fbx(os.path.join(EXPORT_DIR, "onehorn_greatsword.fbx"), sword)
    write_armor_script(armor)

    # Preview scene: R15 block body under the armor, sword in the right hand.
    body = build_body(armor_mat)
    for o in sword:
        # Point the blade down, forward and outward, like the concept pose.
        aim = Vector((-0.3, -0.85, -0.45)).to_track_quat("Z", "Y").to_matrix().to_4x4()
        o.matrix_world = Matrix.Translation(Vector(R15_POS["RightHand"]) + Vector((0, -0.1, 0))) @ aim
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(EXPORT_DIR, "onehorn.blend"))

    scene, cam, floor = setup_render()
    floor_obj = floor.to_object("Floor", armor_mat, (0, 0, 0))
    views = render_views(scene, cam, sword)
    contact_sheet(views, os.path.join(RENDER_DIR, "onehorn_sheet.png"))
    render_sword(scene, cam, sword, armor + body + [floor_obj])


if __name__ == "__main__":
    main()

"""Shared kit for the corrupted cyclops roster: R15 rig constants, low-poly geometry
helpers, texture-atlas UVs, materials, export and Roblox data generation.

Blender units = studs. Characters face -Y; their left side is +X.
Blender (x, y, z) maps to Roblox (-x, z, y) with the FBX export axes below.
"""
import math
import os
import random
import sys

import bpy  # must come first: it makes bmesh/mathutils importable
import bmesh
from mathutils import Euler, Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from texture_gen import TILES, build_atlas, tile_rect  # noqa: E402

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

# Materials painted as one plate per face (bevel, rivets, stitching) map each face onto
# the whole tile. Organic/fabric materials keep a constant texel density instead, so
# small faces show a small patch of the tile rather than a squashed copy of it.
DENSITY_TILES = {"plate_white", "plate_black", "cloth_royal", "cloth_white",
                 "skin", "skin_corrupt", "skin_king", "hair", "fur", "fur_dark", "cloth",
                 "cloth_dark", "cloth_brown", "cloth_green", "linen", "pants", "quilt",
                 "chainmail", "wood", "rope", "horn", "body"}
STUDS_PER_TILE = 1.3


def face_uvs(face, tile):
    """Planar-project a face (tile 'up' = world up where possible) onto its tile."""
    n = face.normal
    t = Vector((1, 0, 0)) if abs(n.z) > 0.9 else Vector((0, 0, 1)).cross(n).normalized()
    b = n.cross(t)
    us = [l.vert.co.dot(t) for l in face.loops]
    vs = [l.vert.co.dot(b) for l in face.loops]
    u0, v0, size = tile_rect(tile)
    m = 3 / 1024  # keep clear of neighbouring tiles
    span = size - 2 * m
    du, dv = max(us) - min(us), max(vs) - min(vs)
    if tile in DENSITY_TILES:
        su, sv = min(1.0, du / STUDS_PER_TILE), min(1.0, dv / STUDS_PER_TILE)
        rnd = random.Random(face.index * 7919 + len(face.loops))
        ou, ov = rnd.uniform(0, 1 - su), rnd.uniform(0, 1 - sv)
    else:
        su = sv = 1.0
        ou = ov = 0.0

    def norm(x, lo, d):
        return (x - lo) / d if d > 1e-6 else 0.5
    return [(u0 + m + (ou + norm(u, min(us), du) * su) * span,
             v0 + m + (ov + norm(v, min(vs), dv) * sv) * span) for u, v in zip(us, vs)]


# ---------------------------------------------------------------------------
# Geometry helpers. Everything is built into a bmesh in part-local space.
class Piece:
    def __init__(self):
        self.bm = bmesh.new()
        self.col = self.bm.faces.layers.int.new("col")
        self.smooth = self.bm.faces.layers.int.new("smooth")

    def _faces(self, verts, faces, color, smooth=0):
        """smooth: number of leading faces to shade smooth (the sides of a loft)."""
        vs = [self.bm.verts.new(v) for v in verts]
        for k, f in enumerate(faces):
            face = self.bm.faces.new([vs[i] for i in f])
            face[self.col] = TILES.index(color)
            face[self.smooth] = 1 if k < smooth else 0

    def loft(self, rings, color, pos=(0, 0, 0), rot=(0, 0, 0), tip=None, base=None, smooth=False):
        """rings: list of (z, profile) where profile is a list of (x, y) points.
        tip/base: optional (x, y, z) apex to close the top/bottom with a point.
        smooth: shade the sides smooth (rounded plates, capes); caps stay flat."""
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
        sides = len(faces) if smooth else 0
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
        self._faces(verts, faces, color, smooth=sides)

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
        bm.faces.index_update()
        uv = bm.loops.layers.uv.new("UVMap")
        for f in bm.faces:
            for loop, coords in zip(f.loops, face_uvs(f, TILES[f[self.col]])):
                loop[uv].uv = coords
        flags = [f[self.smooth] for f in bm.faces]
        mesh = bpy.data.meshes.new(name)
        bm.to_mesh(mesh)
        bm.free()
        for poly, flag in zip(mesh.polygons, flags):
            poly.use_smooth = bool(flag)
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
# Small shared building blocks.
def band(p, z0, z1, w, d, c, color, grow=0.0, dx=0.0, dy=0.0, rot=(0, 0, 0)):
    """A ring of armor between z0 and z1, flaring by `grow` toward the top."""
    p.shell([(z0, w, d, c, dx, dy), (z1, w + grow, d + grow, c, dx, dy)], color, rot=rot)


def crystals(g, rnd, count, base_fn, dir_fn, length, radius):
    for _ in range(count):
        g.spike(base_fn(), dir_fn(), rnd.uniform(*length), rnd.uniform(*radius), "glow",
                sides=5, twist=rnd.uniform(0, 3))



def circle(r, n=8, sx=1.0, sy=1.0, phase=0.0):
    return [(r * sx * math.cos(2 * math.pi * i / n + phase), r * sy * math.sin(2 * math.pi * i / n + phase))
            for i in range(n)]


def blob(p, center, radii, color, sides=8, rings=4, rot=(0, 0, 0)):
    """Low-poly ellipsoid (muscles, heads, bodies)."""
    rx, ry, rz = radii
    lofted = []
    for k in range(1, rings):
        a = math.pi * k / rings
        z = -math.cos(a) * rz
        s = math.sin(a)
        lofted.append((z, circle(1, sides, rx * s, ry * s, math.pi / sides)))
    p.loft(lofted, color, pos=center, rot=rot, tip=(0, 0, rz), base=(0, 0, -rz))


def tube(p, z0, z1, r0, r1, color, sides=8, sx=1.0, sy=1.0, pos=(0, 0, 0), rot=(0, 0, 0)):
    p.loft([(z0, circle(r0, sides, sx, sy, math.pi / sides)),
            (z1, circle(r1, sides, sx, sy, math.pi / sides))], color, pos=pos, rot=rot)


def corruption_crystals(g, rnd, count, center, spread, direction, length=(0.2, 0.5),
                        radius=(0.04, 0.09)):
    """Scatter `count` crystals around center (+/- spread) pointing roughly along direction."""
    for _ in range(count):
        base = tuple(c + rnd.uniform(-s, s) for c, s in zip(center, spread))
        d = tuple(v + rnd.uniform(-0.5, 0.5) for v in direction)
        g.spike(base, d, rnd.uniform(*length), rnd.uniform(*radius), "glow", sides=5,
                twist=rnd.uniform(0, 3))


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
    os.makedirs(os.path.dirname(path), exist_ok=True)
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


def piece_bounds(obj):
    """Size and center offset (from the object origin) in Roblox axes."""
    xs = [v.co.x for v in obj.data.vertices]
    ys = [v.co.y for v in obj.data.vertices]
    zs = [v.co.z for v in obj.data.vertices]
    size = (max(xs) - min(xs), max(zs) - min(zs), max(ys) - min(ys))
    c = ((max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2, (max(zs) + min(zs)) / 2)
    return size, (-c[0], c[2], c[1])


def lua_vec(v):
    return "Vector3.new(" + ", ".join(f"{x:.4f}" for x in v) + ")"


def lua_piece_table(objects, indent="\t\t\t"):
    lines = []
    for o in sorted(objects, key=lambda o: o.name):
        size, offset = piece_bounds(o)
        lines.append(f'{indent}["{o.name}"] = {{ size = {lua_vec(size)}, offset = {lua_vec(offset)} }},')
    return "\n".join(lines)


def link_piece_objects(pieces, armor_mat, glow_mat, positions=None):
    """pieces: {part_name: {kind: Piece}} -> objects named <part>_<kind>, placed at R15 spots.
    Kinds ending in "Glow" get the glow material."""
    objs = []
    for part, kinds in pieces.items():
        for kind, piece in kinds.items():
            if not len(piece.bm.faces):
                piece.bm.free()
                continue
            mat = glow_mat if kind.endswith("Glow") else armor_mat
            loc = (positions or R15_POS)[part]
            objs.append(piece.to_object(f"{part}_{kind}", mat, loc))
    return objs

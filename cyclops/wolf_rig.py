"""Stylized low-poly wolf with a real skinned rig (bones) for Roblox.

Look (from the reference): charcoal-black back, head and mask; silver-white chest,
throat, cheeks and legs; a shaggy mane; ice-blue eyes; black nose.

Pipeline (all code, no armature-less tricks):
  skeleton graph -> Skin modifier -> Subdivision -> sculpt-like deforms (deep chest,
  narrow body, shaggy mane) + fur tufts, ears, eyes -> vertex-colour coat pattern ->
  baked into a painted 1024px texture -> armature + distance-based skin weights ->
  idle / walk actions -> FBX for Roblox (rig and one file per animation).

Run:  python3 cyclops/wolf_rig.py [--alpha] [--no-render]
Blender units = studs. The wolf faces -Y, feet on z = 0.
"""
import math
import os
import random
import sys

import bpy  # must come first: it makes bmesh/mathutils importable
import bmesh
from mathutils import Matrix, Vector
from mathutils.geometry import intersect_point_line

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "export", "creatures")
RENDERS = os.path.join(HERE, "renders")

# ---------------------------------------------------------------------------
# Skeleton: name -> (position, skin radius). Mirrored legs get L/R from +X/-X.
SPINE = {
    "pelvis": ((0, 0.95, 2.15), 0.46),
    "back": ((0, 0.15, 2.22), 0.5),
    "chest": ((0, -0.62, 2.15), 0.6),
    "neck": ((0, -1.1, 2.6), 0.44),
    "head": ((0, -1.52, 2.98), 0.4),
    "muzzle": ((0, -1.95, 2.84), 0.24),
    "nose": ((0, -2.27, 2.8), 0.14),
}
TAIL = {
    "tail1": ((0, 1.35, 2.2), 0.17),
    "tail2": ((0, 1.8, 1.9), 0.25),
    "tail3": ((0, 2.15, 1.45), 0.24),
    "tail4": ((0, 2.4, 1.0), 0.11),
}
LEG = {  # x is mirrored
    "fshoulder": ((0.32, -0.68, 1.85), 0.31),
    "felbow": ((0.32, -0.62, 1.12), 0.19),
    "fwrist": ((0.31, -0.7, 0.4), 0.125),
    "fpaw": ((0.31, -0.9, 0.13), 0.15),
    "hhip": ((0.32, 0.9, 1.95), 0.36),
    "hknee": ((0.33, 0.6, 1.3), 0.22),
    "hhock": ((0.32, 1.06, 0.66), 0.13),
    "hpaw": ((0.32, 0.94, 0.13), 0.15),
}
CHAINS = [
    ["pelvis", "back", "chest", "neck", "head", "muzzle", "nose"],
    ["pelvis", "tail1", "tail2", "tail3", "tail4"],
]
LEG_CHAINS = [["chest", "fshoulder", "felbow", "fwrist", "fpaw"], ["pelvis", "hhip", "hknee", "hhock", "hpaw"]]


def skeleton_points():
    pts = {k: (Vector(p), r) for k, (p, r) in {**SPINE, **TAIL}.items()}
    for side, sx in (("L", 1), ("R", -1)):
        for k, (p, r) in LEG.items():
            pts[k + side] = (Vector((p[0] * sx, p[1], p[2])), r)
    return pts


def skeleton_edges():
    edges = []
    for chain in CHAINS:
        edges += list(zip(chain, chain[1:]))
    for side in ("L", "R"):
        for chain in LEG_CHAINS:
            names = [chain[0]] + [n + side for n in chain[1:]]
            edges += list(zip(names, names[1:]))
    return edges


def EYE_OFFSET(s):
    return Vector((s * 0.175, -0.29, 0.08))


# ---------------------------------------------------------------------------
def build_body(pts):
    names = list(pts)
    mesh = bpy.data.meshes.new("WolfSkeleton")
    mesh.from_pydata([pts[n][0] for n in names], [(names.index(a), names.index(b)) for a, b in skeleton_edges()], [])
    obj = bpy.data.objects.new("WolfSkeleton", mesh)
    bpy.context.collection.objects.link(obj)
    skin = obj.modifiers.new("Skin", "SKIN")
    skin.branch_smoothing = 0.6
    skin.use_smooth_shade = True
    for i, n in enumerate(names):
        r = pts[n][1]
        mesh.skin_vertices[0].data[i].radius = (r, r)
        mesh.skin_vertices[0].data[i].use_root = n == "chest"
    sub = obj.modifiers.new("Subsurf", "SUBSURF")
    sub.levels = 1
    deps = bpy.context.evaluated_depsgraph_get()
    body = bpy.data.meshes.new_from_object(obj.evaluated_get(deps))
    bpy.data.objects.remove(obj)
    return body


def seg_dist(p, a, b):
    t = max(0.0, min(1.0, intersect_point_line(p, a, b)[1]))
    return (p - a.lerp(b, t)).length, t


def sculpt(mesh, pts, alpha):
    """Shape the skinned tube into a wolf: deep chest, tucked belly, narrow body,
    long flat skull, broad cheeks and a shaggy mane."""
    rnd = random.Random(2)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.normal_update()
    P = {k: v[0] for k, v in pts.items()}
    for v in bm.verts:
        p = v.co
        # Torso region (between pelvis and chest, above the legs).
        d_torso, t = seg_dist(p, P["pelvis"], P["chest"])
        if d_torso < 0.7 and p.z > 1.55:
            p.x *= 0.82  # wolves are narrow
            if p.z < P["chest"].z - 0.1:
                # Deep chest at the front, tucked belly toward the hips.
                deep = (1 - t) * 0.75 + t * 0.08
                p.z -= deep * (P["chest"].z - p.z) / 0.5
            elif t < 0.45:
                p.z += 0.12 * (1 - t / 0.45) * smoothstep(P["chest"].z, P["chest"].z + 0.4, p.z)  # withers
        # Skull: longer and flatter, with broad cheeks.
        d_head, _ = seg_dist(p, P["head"], P["muzzle"])
        if d_head < 0.4:
            p.z = P["head"].z + (p.z - P["head"].z) * 0.82
            if p.z < P["head"].z + 0.05 and p.y > P["head"].y - 0.2:
                p.x *= 1.25  # cheek ruff
    bm.to_mesh(mesh)
    bm.free()


def star_shell(bm, centers, radii, points=12, jag=0.3, rnd=None, open_back=True):
    """A fluffy fur shell: rings with a star-shaped cross-section lofted along a path.
    The last ring is pulled into jagged points that trail backward, like clumps of fur."""
    rings = []
    for k, (c, r) in enumerate(zip(centers, radii)):
        nxt = centers[min(k + 1, len(centers) - 1)]
        prv = centers[max(k - 1, 0)]
        axis = (nxt - prv).normalized()
        m = axis.to_track_quat("Z", "Y").to_matrix()
        ring = []
        for i in range(points):
            a = 2 * math.pi * i / points
            rr = r * (1 + (jag if i % 2 else 0) * (0.7 + 0.6 * rnd.random()))
            ring.append(bm.verts.new(c + m @ Vector((math.cos(a) * rr, math.sin(a) * rr, 0))))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for i in range(points):
            j = (i + 1) % points
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.faces.new(list(reversed(rings[0])))
    # Trailing jagged tips from the last ring.
    last, c_last = rings[-1], centers[-1]
    back = (centers[-1] - centers[-2]).normalized()
    tips = []
    for i in range(0, points, 2):
        v = last[i].co
        tip = v + back * (0.25 + 0.2 * rnd.random()) + (v - c_last) * 0.15
        tips.append(bm.verts.new(tip))
    for k, i in enumerate(range(0, points, 2)):
        a, b, c = last[i - 1], last[i], last[(i + 1) % points]
        bm.faces.new((a, b, tips[k]))
        bm.faces.new((b, c, tips[k]))
    if not open_back:
        bm.faces.new(last)


def add_tufts(bm, pts, alpha, rnd):
    """Fur: a fluffy mane shell around neck and shoulders, cheek ruffs and a bushy tail tip."""
    P = {k: v[0] for k, v in pts.items()}
    k = 1.25 if alpha else 1.0
    # Mane from behind the ears down over the shoulders.
    path = [P["head"] + Vector((0, 0.3, -0.08)), P["neck"] + Vector((0, 0.02, 0.0)),
            P["neck"].lerp(P["chest"], 0.5) + Vector((0, 0, 0.06)), P["chest"] + Vector((0, 0.3, 0.12))]
    star_shell(bm, path, [0.4 * k, 0.48 * k, 0.56 * k, 0.56 * k], points=22, jag=0.16, rnd=rnd)
    # Cheek ruff around the back of the jaw.
    path = [P["head"] + Vector((0, -0.05, -0.12)), P["head"] + Vector((0, 0.15, -0.1))]
    star_shell(bm, path, [0.36, 0.4], points=18, jag=0.14, rnd=rnd)
    # Bushy tail.
    path = [P["tail2"], P["tail3"], P["tail4"] + (P["tail4"] - P["tail3"]) * 0.25]
    star_shell(bm, path, [0.27, 0.29, 0.15], points=16, jag=0.18, rnd=rnd)


def add_head_parts(bm, pts):
    """Ears (with a slight cup), eyes and nose pad."""
    P = {k: v[0] for k, v in pts.items()}
    for s in (1, -1):
        base = P["head"] + Vector((s * 0.18, 0.08, 0.2))
        tip = base + Vector((s * 0.08, 0.1, 0.5))
        ring = [base + Vector((s * dx, dy, 0)) for dx, dy in ((0.15, 0.0), (0.0, -0.05), (-0.15, 0.0), (0.0, 0.12))]
        vs = [bm.verts.new(p) for p in ring]
        t = bm.verts.new(tip)
        for i in range(4):
            bm.faces.new((vs[i], vs[(i + 1) % 4], t))
        bm.faces.new(list(reversed(vs)))
    for s in (1, -1):
        # Almond-shaped, half sunk into the head.
        m = Matrix.Translation(P["head"] + EYE_OFFSET(s)) @ Matrix.Diagonal((1.0, 0.8, 0.65, 1.0))
        bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=6, radius=0.05, matrix=m)


# ---------------------------------------------------------------------------
# Coat colours (linear). Charcoal top, silver-white underside, mask, blue eyes.
def srgb(c):
    return tuple(x ** 2.2 for x in c)


def coat_palette(alpha):
    if alpha:
        return dict(top=srgb((0.09, 0.09, 0.1)), mid=srgb((0.24, 0.24, 0.26)), light=srgb((0.66, 0.67, 0.7)),
                    mask=srgb((0.06, 0.06, 0.07)), eye=srgb((0.35, 0.75, 1.0)))
    return dict(top=srgb((0.15, 0.15, 0.16)), mid=srgb((0.38, 0.38, 0.4)), light=srgb((0.82, 0.82, 0.84)),
                mask=srgb((0.1, 0.1, 0.11)), eye=srgb((0.4, 0.78, 1.0)))


def smoothstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def mix(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def paint(mesh, pts, alpha):
    """Vertex colours for the coat pattern, later baked into the texture."""
    pal = coat_palette(alpha)
    P = {k: v[0] for k, v in pts.items()}
    col = mesh.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
    mesh.calc_normals_split() if hasattr(mesh, "calc_normals_split") else None
    eye_centers = [P["head"] + EYE_OFFSET(s) for s in (1, -1)]
    segs = [(pts[a][0], pts[b][0]) for a, b in skeleton_edges()]
    for v in mesh.vertices:
        p = v.co
        # Colour by the direction away from the nearest bone, not the surface normal,
        # so fur clumps get the same colour as the coat around them.
        a, b = min(segs, key=lambda ab: seg_dist(p, *ab)[0])
        _, t = seg_dist(p, a, b)
        n = (p - a.lerp(b, t))
        n = n.normalized() if n.length > 1e-6 else Vector((0, 0, 1))
        # Base: dark on top, mid on the flanks, light underneath.
        up = smoothstep(-0.55, 0.35, n.z)
        c = mix(pal["mid"], pal["top"], up)
        under = smoothstep(-0.35, -0.75, n.z)
        c = mix(c, pal["light"], under * 0.85)
        # Legs fade to silver-white from the elbows/knees down.
        if p.z < 1.3 and abs(p.x) > 0.12:
            c = mix(c, pal["light"], smoothstep(1.3, 0.8, p.z) * 0.9)
        # Throat, chest and bib.
        d_throat, _ = seg_dist(p, P["chest"] + Vector((0, -0.3, -0.25)), P["neck"] + Vector((0, -0.2, -0.15)))
        if n.y < 0.2:
            c = mix(c, pal["light"], smoothstep(0.42, 0.18, d_throat))
        # Head: dark mask over the brow and around the eyes, light cheeks and muzzle sides.
        d_head, _ = seg_dist(p, P["head"], P["nose"])
        if d_head < 0.5:
            cheek = smoothstep(0.05, -0.12, p.z - P["head"].z) * smoothstep(0.15, 0.3, abs(p.x))
            muzzle = smoothstep(P["head"].y - 0.25, P["muzzle"].y, p.y) * smoothstep(0.1, -0.3, n.z)
            c = mix(c, pal["light"], max(cheek, muzzle))
            brow = smoothstep(-0.05, 0.12, p.z - P["head"].z) * smoothstep(0.25, 0.05, abs(p.x))
            c = mix(c, pal["mask"], brow * 0.8)
            for e in eye_centers:
                ring = smoothstep(0.13, 0.07, (p - e).length)
                c = mix(c, pal["mask"], ring)
        if (p - P["nose"]).length < 0.16 and n.y < 0:
            c = pal["mask"]
        # Ear tips and tail tip darker.
        if p.z > P["head"].z + 0.35 or (p - P["tail4"]).length < 0.35:
            c = mix(c, pal["mask"], 0.8)
        # Eyes: ice-blue iris with a black pupil, facing forward-out.
        for e in eye_centers:
            if (p - e).length < 0.062:
                local = (p - e).normalized()
                c = pal["eye"]
                if local.y < -0.7:
                    c = srgb((0.01, 0.01, 0.02))
        col.data[v.index].color = (*c, 1.0)


# ---------------------------------------------------------------------------
def make_wolf_mesh(alpha=False):
    pts = skeleton_points()
    body = build_body(pts)
    sculpt(body, pts, alpha)
    rnd = random.Random(7 if alpha else 3)
    fur = bmesh.new()
    add_tufts(fur, pts, alpha, rnd)
    fur_mesh = bpy.data.meshes.new("Fur")
    fur.to_mesh(fur_mesh)
    fur.free()
    fur_obj = bpy.data.objects.new("Fur", fur_mesh)
    bpy.context.collection.objects.link(fur_obj)
    fur_obj.modifiers.new("Subsurf", "SUBSURF").levels = 1
    fur_eval = bpy.data.meshes.new_from_object(fur_obj.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(fur_obj)
    bm = bmesh.new()
    bm.from_mesh(body)
    bm.from_mesh(fur_eval)
    add_head_parts(bm, pts)
    mesh = bpy.data.meshes.new("Wolf")
    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()
    bpy.data.meshes.remove(body)
    for poly in mesh.polygons:
        poly.use_smooth = True
    paint(mesh, pts, alpha)
    obj = bpy.data.objects.new("AlphaWolf" if alpha else "Wolf", mesh)
    bpy.context.collection.objects.link(obj)
    return obj, pts


def unwrap(obj):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.01)
    bpy.ops.object.mode_set(mode="OBJECT")


def bake_texture(obj, path, size=1024):
    """Bake vertex colours x fur-streak noise into a painted texture, then switch
    the material to use that texture."""
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 4
    img = bpy.data.images.new(obj.name + "Texture", size, size)
    mat = bpy.data.materials.new(obj.name + "Bake")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    emit = nt.nodes.new("ShaderNodeEmission")
    attr = nt.nodes.new("ShaderNodeAttribute")
    attr.attribute_name = "Col"
    # Long fur streaks: noise stretched along the body (y) and up (z).
    coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (14, 3, 5)
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 6
    noise.inputs["Detail"].default_value = 8
    ramp = nt.nodes.new("ShaderNodeMapRange")
    ramp.inputs["To Min"].default_value = 0.72
    ramp.inputs["To Max"].default_value = 1.3
    mul = nt.nodes.new("ShaderNodeVectorMath")
    mul.operation = "MULTIPLY"
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    nt.links.new(coord.outputs["Object"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Value"])
    nt.links.new(attr.outputs["Color"], mul.inputs[0])
    nt.links.new(ramp.outputs["Result"], mul.inputs[1])
    nt.links.new(mul.outputs["Vector"], emit.inputs["Color"])
    nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])
    nt.nodes.active = tex
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    scene.render.bake.margin = 8
    bpy.ops.object.bake(type="EMIT")
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()

    final = bpy.data.materials.new(obj.name + "Fur")
    final.use_nodes = True
    bsdf = final.node_tree.nodes["Principled BSDF"]
    t = final.node_tree.nodes.new("ShaderNodeTexImage")
    t.image = img
    final.node_tree.links.new(t.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.85
    obj.data.materials.clear()
    obj.data.materials.append(final)
    return img


# ---------------------------------------------------------------------------
# Rig: one bone per skeleton edge, named for Roblox animators.
BONE_NAMES = {
    "back": "Spine", "chest": "Chest", "neck": "Neck", "head": "Head", "muzzle": "Snout", "nose": "Nose",
    "tail1": "Tail1", "tail2": "Tail2", "tail3": "Tail3", "tail4": "Tail4",
    "fshoulder": "Shoulder", "felbow": "UpperArm", "fwrist": "Forearm", "fpaw": "FrontPaw",
    "hhip": "Hip", "hknee": "Thigh", "hhock": "Shin", "hpaw": "HindPaw",
}


def bone_name(point):
    for side in ("L", "R"):
        if point.endswith(side) and point[:-1] in BONE_NAMES:
            return BONE_NAMES[point[:-1]] + side
    return BONE_NAMES[point]


def build_rig(mesh_obj, pts):
    arm = bpy.data.armatures.new(mesh_obj.name + "Rig")
    rig = bpy.data.objects.new(mesh_obj.name + "Rig", arm)
    bpy.context.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    root = arm.edit_bones.new("Root")
    root.head, root.tail = (0, 0.15, 0), (0, 0.15, 0.6)
    bones = {}
    edges = skeleton_edges()
    for a, b in edges:  # edges are listed parent-first along every chain
        eb = arm.edit_bones.new(bone_name(b))
        eb.head, eb.tail = pts[a][0], pts[b][0]
        parent = bones.get(a)  # the bone that ends where this one starts
        eb.parent = parent or root
        eb.use_connect = parent is not None
        bones[b] = eb
    bpy.ops.object.mode_set(mode="OBJECT")

    # Skin weights: smooth falloff from each bone segment, kept to the same side
    # for legs so left and right never pull on each other.
    groups = {}
    for a, b in edges:
        groups[b] = mesh_obj.vertex_groups.new(name=bone_name(b))
    segs = [(b, pts[a][0], pts[b][0]) for a, b in edges]
    for v in mesh_obj.data.vertices:
        p = v.co
        cands = []
        for b, ha, hb in segs:
            if b[-1] in "LR" and b[:-1] in LEG:
                if (b[-1] == "L") != (p.x > 0) and abs(p.x) > 0.08:
                    continue
            d, _ = seg_dist(p, ha, hb)
            cands.append((d, b))
        cands.sort()
        best = cands[:3]
        ws = [(1.0 / max(d, 0.02) ** 6, b) for d, b in best]
        total = sum(w for w, _ in ws)
        for w, b in ws:
            if w / total > 0.02:
                groups[b].add([v.index], w / total, "REPLACE")
    mesh_obj.parent = rig
    mod = mesh_obj.modifiers.new("Armature", "ARMATURE")
    mod.object = rig
    return rig


def key(rig, bone, frame, rot=(0, 0, 0), loc=None):
    pb = rig.pose.bones[bone]
    pb.rotation_mode = "XYZ"
    pb.rotation_euler = [math.radians(a) for a in rot]
    pb.keyframe_insert("rotation_euler", frame=frame)
    if loc is not None:
        pb.location = loc
        pb.keyframe_insert("location", frame=frame)


def make_actions(rig):
    """Looping idle and walk cycles keyed on the bones (30 fps)."""
    rig.animation_data_create()
    actions = {}

    idle = bpy.data.actions.new("Idle")
    rig.animation_data.action = idle
    for f in range(0, 61, 6):
        ph = 2 * math.pi * f / 60
        key(rig, "Chest", f, (1.5 * math.sin(ph), 0, 0))
        key(rig, "Neck", f, (-2 * math.sin(ph), 0, 0))
        key(rig, "Head", f, (2 * math.sin(ph + 1), 0, 3 * math.sin(ph * 0.5)))
        for i, t in enumerate(("Tail1", "Tail2", "Tail3", "Tail4")):
            key(rig, t, f, (0, 0, 7 * math.sin(ph - i * 0.6)))
    actions["Idle"] = idle

    walk = bpy.data.actions.new("Walk")
    rig.animation_data.action = walk
    n = 32
    for f in range(0, n + 1, 2):
        ph = 2 * math.pi * f / n
        for side, off in (("L", 0.0), ("R", math.pi)):
            front, hind = ph + off, ph + off + math.pi  # diagonal pairs move together
            key(rig, "UpperArm" + side, f, (24 * math.sin(front), 0, 0))
            key(rig, "Forearm" + side, f, (-30 * max(0.0, math.sin(front + 1.2)), 0, 0))
            key(rig, "FrontPaw" + side, f, (20 * max(0.0, math.sin(front + 1.6)), 0, 0))
            key(rig, "Thigh" + side, f, (22 * math.sin(hind), 0, 0))
            key(rig, "Shin" + side, f, (25 * max(0.0, math.sin(hind + 1.2)), 0, 0))
            key(rig, "HindPaw" + side, f, (-20 * max(0.0, math.sin(hind + 1.6)), 0, 0))
        key(rig, "Root", f, (0, 0, 0), loc=(0, 0.06 * abs(math.sin(ph)), 0))
        key(rig, "Chest", f, (0, 0, 2 * math.sin(ph)))
        key(rig, "Head", f, (3 * math.sin(2 * ph), 0, 0))
        for i, t in enumerate(("Tail1", "Tail2", "Tail3", "Tail4")):
            key(rig, t, f, (0, 0, 6 * math.sin(ph - i * 0.7)))
    actions["Walk"] = walk
    for act in actions.values():
        for fc in act.fcurves:
            fc.modifiers.new("CYCLES")
    rig.animation_data.action = None
    return actions


def export(rig, mesh_obj, path, action=None):
    bpy.ops.object.select_all(action="DESELECT")
    rig.select_set(True)
    mesh_obj.select_set(True)
    bpy.context.view_layer.objects.active = rig
    rig.animation_data.action = action
    if action:
        start, end = (int(x) for x in action.frame_range)
        bpy.context.scene.frame_start, bpy.context.scene.frame_end = start, end
    bpy.ops.export_scene.fbx(
        filepath=path, use_selection=True, object_types={"ARMATURE", "MESH"},
        add_leaf_bones=False, bake_anim=action is not None, bake_anim_use_all_actions=False,
        bake_anim_use_nla_strips=False, bake_anim_force_startend_keying=True,
        path_mode="COPY", embed_textures=True, axis_forward="Z", axis_up="Y",
        mesh_smooth_type="FACE",
    )
    rig.animation_data.action = None


# ---------------------------------------------------------------------------
def setup_preview():
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.view_settings.view_transform = "Standard"
    scene.cycles.samples = 48
    scene.cycles.use_denoising = True
    world = bpy.data.worlds.new("World")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.03, 0.035, 0.05, 1)
    scene.world = world
    for name, loc, energy, color in (("Key", (-6, -8, 9), 1300, (0.9, 0.93, 1.0)),
                                     ("Rim", (5, 7, 6), 1800, (0.6, 0.75, 1.0)),
                                     ("Fill", (8, -5, 3), 300, (1, 1, 1))):
        light = bpy.data.lights.new(name, "AREA")
        light.energy, light.size, light.color = energy, 6, color
        o = bpy.data.objects.new(name, light)
        o.location = loc
        o.rotation_euler = (Vector((0, 0, 2)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        scene.collection.objects.link(o)
    cam = bpy.data.cameras.new("Cam")
    cam.lens = 60
    co = bpy.data.objects.new("Cam", cam)
    scene.collection.objects.link(co)
    scene.camera = co
    return scene, co


def shoot(scene, cam, path, loc, target, res=(1200, 1000)):
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


ALPHA_SCALE = 1.45


def main():
    alpha = "--alpha" in sys.argv
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.context.scene.render.fps = 30
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(RENDERS, exist_ok=True)
    obj, pts = make_wolf_mesh(alpha)
    print("faces:", len(obj.data.polygons))
    unwrap(obj)
    name = obj.name
    bake_texture(obj, os.path.join(OUT, name + "_texture.png"))
    k = ALPHA_SCALE if alpha else 1.0
    if k != 1.0:  # the alpha is the same wolf, bigger (feet stay on the ground)
        obj.data.transform(Matrix.Scale(k, 4))
        pts = {n: (p * k, r * k) for n, (p, r) in pts.items()}
    rig = build_rig(obj, pts)
    actions = make_actions(rig)
    export(rig, obj, os.path.join(OUT, name + ".fbx"))
    for act_name, act in actions.items():
        export(rig, obj, os.path.join(OUT, f"{name}_{act_name}.fbx"), act)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, name + ".blend"))
    if "--no-render" in sys.argv:
        return
    scene, cam = setup_preview()
    s = k
    shoot(scene, cam, os.path.join(RENDERS, f"{name}_hero.png"), (-6.2 * s, -8.0 * s, 3.9 * s), (0, 0.25, 1.6 * s))
    shoot(scene, cam, os.path.join(RENDERS, f"{name}_side.png"), (11 * s, -0.2, 2.2 * s), (0, 0.1, 1.8 * s), (1400, 900))
    # A walk-cycle pose to check the joints bend the right way.
    rig.animation_data.action = actions["Walk"]
    scene.frame_set(8)
    shoot(scene, cam, os.path.join(RENDERS, f"{name}_walk.png"), (11 * s, -0.2, 2.2 * s), (0, 0.1, 1.8 * s), (1400, 900))


if __name__ == "__main__":
    main()

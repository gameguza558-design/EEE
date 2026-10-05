"""Roblox-style R15 characters: smooth rounded shells + a hand-painted texture.

Instead of stacking boxes and bumps, every R15 body part gets one smooth, beveled
shell slightly larger than the part (like Roblox layered clothing), and all the
detail - face, folds, seams, buttons, belts, cracks - is painted into a per-character
texture, laid out like a Roblox clothing template:

    2048 px canvas (saved at 1024), 4x4 cells of 512 px, one cell per R15 part.
    Inside a cell: front | back on the top half, left | right | top | bottom below.

Run:  python3 cyclops/style2.py      -> export/style2/<Name>.fbx, renders/style2_<Name>.png
"""
import math
import os
import random
import sys

import bpy  # must come first: it makes bmesh/mathutils importable
import bmesh
from mathutils import Matrix, Vector
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from kit import R15_POS, R15_SIZE  # noqa: E402

OUT = os.path.join(HERE, "export", "style2")
RENDERS = os.path.join(HERE, "renders")
CANVAS = 2048
CELL = 512
PARTS = list(R15_SIZE)
FACES = ("front", "back", "left", "right", "top", "bottom")
SUB = {  # sub-rectangles of a cell (x0, y0, x1, y1) as fractions, y down
    "front": (0.0, 0.0, 0.5, 0.5), "back": (0.5, 0.0, 1.0, 0.5),
    "left": (0.0, 0.5, 0.25, 1.0), "right": (0.25, 0.5, 0.5, 1.0),
    "top": (0.5, 0.5, 0.75, 1.0), "bottom": (0.75, 0.5, 1.0, 1.0),
}


def face_rect(part, face):
    """Pixel rectangle of a part's face on the canvas."""
    i = PARTS.index(part)
    cx, cy = (i % 4) * CELL, (i // 4) * CELL
    x0, y0, x1, y1 = SUB[face]
    pad = 6
    return (cx + x0 * CELL + pad, cy + y0 * CELL + pad, cx + x1 * CELL - pad, cy + y1 * CELL - pad)


# ---------------------------------------------------------------------------
# Geometry: one rounded shell per part.
def rounded_box(size, bevel, center=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bevel, segments=3, profile=0.5, affect="EDGES")
    bmesh.ops.translate(bm, vec=Vector(center), verts=bm.verts)
    return bm


def dominant_face(n):
    ax = max(range(3), key=lambda i: abs(n[i]))
    if ax == 0:
        return "left" if n.x > 0 else "right"  # character's left is +X
    if ax == 1:
        return "front" if n.y < 0 else "back"
    return "top" if n.z > 0 else "bottom"


def project(bm, part):
    """UV every face into its side's rectangle, as seen looking at that side."""
    uv = bm.loops.layers.uv.verify()
    xs = [v.co.x for v in bm.verts]
    ys = [v.co.y for v in bm.verts]
    zs = [v.co.z for v in bm.verts]
    lo, hi = Vector((min(xs), min(ys), min(zs))), Vector((max(xs), max(ys), max(zs)))
    span = hi - lo
    bm.normal_update()
    for f in bm.faces:
        side = dominant_face(f.normal)
        x0, y0, x1, y1 = face_rect(part, side)
        for loop in f.loops:
            p = (loop.vert.co - lo)
            nx, ny, nz = p.x / span.x, p.y / span.y, p.z / span.z
            # (u, v) across the side as a viewer facing it sees it; v=0 at the top.
            u, v = {
                "front": (nx, 1 - nz), "back": (1 - nx, 1 - nz),
                "left": (ny, 1 - nz), "right": (1 - ny, 1 - nz),
                "top": (nx, ny), "bottom": (nx, 1 - ny),
            }[side]
            px, py = x0 + u * (x1 - x0), y0 + v * (y1 - y0)
            loop[uv].uv = (px / CANVAS, 1 - py / CANVAS)


SHELL_MARGIN = {"Head": 0.04}


def build_shells(spec, material):
    """spec: {part: dict(size=(w, d, h) override, bevel=r, center=(x, y, z))}."""
    objs = []
    for part in PARTS:
        sx, sy, sz = R15_SIZE[part]
        m = SHELL_MARGIN.get(part, 0.05)
        cfg = spec.get(part, {})
        size = cfg.get("size", (sx + 2 * m, sz + 2 * m, sy + 2 * m))
        bm = rounded_box(size, cfg.get("bevel", 0.12), cfg.get("center", (0, 0, 0)))
        for extra in cfg.get("extras", []):
            extra(bm)
        project(bm, part)
        mesh = bpy.data.meshes.new(part + "_Armor")
        bm.to_mesh(mesh)
        bm.free()
        for poly in mesh.polygons:
            poly.use_smooth = True
        mesh.materials.append(material)
        obj = bpy.data.objects.new(part + "_Armor", mesh)
        obj.location = R15_POS[part]
        bpy.context.collection.objects.link(obj)
        objs.append(obj)
    return objs


# ---------------------------------------------------------------------------
# Painting helpers (PIL, on the 2048 canvas).
class Painter:
    def __init__(self, seed=0):
        self.img = Image.new("RGB", (CANVAS, CANVAS), (40, 40, 44))
        self.d = ImageDraw.Draw(self.img)
        self.rnd = random.Random(seed)

    def rect(self, part, face):
        return face_rect(part, face)

    def at(self, part, face, u, v):
        x0, y0, x1, y1 = face_rect(part, face)
        return x0 + u * (x1 - x0), y0 + v * (y1 - y0)

    def box(self, part, face, u0, v0, u1, v1, color, outline=None, width=0):
        a, b = self.at(part, face, u0, v0), self.at(part, face, u1, v1)
        self.d.rectangle([a, b], fill=color, outline=outline, width=width)

    def poly(self, part, face, pts, color, outline=None, width=0):
        self.d.polygon([self.at(part, face, u, v) for u, v in pts], fill=color, outline=outline)
        if outline and width:
            q = [self.at(part, face, u, v) for u, v in pts]
            self.d.line(q + [q[0]], fill=outline, width=width, joint="curve")

    def line(self, part, face, pts, color, width=3):
        self.d.line([self.at(part, face, u, v) for u, v in pts], fill=color, width=width, joint="curve")

    def ellipse(self, part, face, cu, cv, ru, rv, color, outline=None, width=0):
        x0, y0, x1, y1 = face_rect(part, face)
        rx, ry = ru * (x1 - x0), rv * (y1 - y0)
        cx, cy = self.at(part, face, cu, cv)
        self.d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=color, outline=outline, width=width)

    def fill(self, part, faces, color):
        for f in faces:
            self.d.rectangle(face_rect(part, f), fill=color)

    def dashes(self, part, face, pts, color, dash=10, gap=8, width=3):
        q = [self.at(part, face, u, v) for u, v in pts]
        for (ax, ay), (bx, by) in zip(q, q[1:]):
            length = math.hypot(bx - ax, by - ay)
            t = 0.0
            while t < length:
                t1 = min(length, t + dash)
                self.d.line([(ax + (bx - ax) * t / length, ay + (by - ay) * t / length),
                             (ax + (bx - ax) * t1 / length, ay + (by - ay) * t1 / length)], fill=color, width=width)
                t += dash + gap

    def folds(self, part, face, color, count=4, horizontal=False, seed=None):
        """Soft cloth folds: curved darker strokes."""
        rnd = random.Random(seed if seed is not None else self.rnd.random())
        for _ in range(count):
            if horizontal:
                v = rnd.uniform(0.15, 0.9)
                pts = [(0.05, v), (0.35, v + rnd.uniform(-0.05, 0.05)), (0.7, v + rnd.uniform(-0.06, 0.06)),
                       (0.95, v + rnd.uniform(-0.04, 0.04))]
            else:
                u = rnd.uniform(0.15, 0.85)
                pts = [(u, rnd.uniform(0.0, 0.3)), (u + rnd.uniform(-0.06, 0.06), 0.5),
                       (u + rnd.uniform(-0.08, 0.08), rnd.uniform(0.7, 1.0))]
            self.line(part, face, pts, color, width=rnd.randint(3, 6))

    def cracks(self, part, face, color, glow, count=4, seed=1):
        """Corruption veins: dark cracks with a glowing core."""
        rnd = random.Random(seed)
        layer = Image.new("L", self.img.size, 0)
        ld = ImageDraw.Draw(layer)
        for _ in range(count):
            u, v = rnd.uniform(0.1, 0.9), rnd.uniform(0.1, 0.9)
            a = rnd.uniform(0, 2 * math.pi)
            pts = [(u, v)]
            for _ in range(rnd.randint(4, 8)):
                a += rnd.uniform(-0.8, 0.8)
                u, v = u + math.cos(a) * 0.08, v + math.sin(a) * 0.08
                pts.append((min(max(u, 0), 1), min(max(v, 0), 1)))
            q = [self.at(part, face, uu, vv) for uu, vv in pts]
            self.d.line(q, fill=color, width=7, joint="curve")
            ld.line(q, fill=255, width=3, joint="curve")
        halo = layer.filter(ImageFilter.GaussianBlur(6))
        glow_img = Image.new("RGB", self.img.size, glow)
        self.img = Image.composite(glow_img, self.img, halo.point(lambda x: min(255, x * 2)))
        self.img.paste(Image.new("RGB", self.img.size, (235, 200, 255)), mask=layer)
        self.d = ImageDraw.Draw(self.img)

    def shade(self):
        """Ambient-occlusion style darkening toward every face edge, plus soft noise."""
        import numpy as np
        a = np.asarray(self.img, np.float32) / 255
        yy, xx = np.mgrid[0:CANVAS, 0:CANVAS].astype(np.float32)
        ao = np.ones((CANVAS, CANVAS), np.float32)
        for part in PARTS:
            for face in FACES:
                x0, y0, x1, y1 = (int(c) for c in face_rect(part, face))
                sub = (slice(y0, y1), slice(x0, x1))
                ex = np.minimum(xx[sub] - x0, x1 - xx[sub]) / max(1, (x1 - x0))
                ey = np.minimum(yy[sub] - y0, y1 - yy[sub]) / max(1, (y1 - y0))
                e = np.minimum(ex, ey)
                ao[sub] = 0.72 + 0.28 * np.clip(e / 0.18, 0, 1)
                ao[sub] *= 1.0 - 0.12 * ((yy[sub] - y0) / max(1, (y1 - y0)))  # darker toward the bottom
        noise = np.asarray(Image.effect_noise((CANVAS // 8, CANVAS // 8), 40).resize((CANVAS, CANVAS), Image.BICUBIC),
                           np.float32) / 255 - 0.5
        a = a * ao[..., None] * (1 + noise[..., None] * 0.1)
        self.img = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
        self.d = ImageDraw.Draw(self.img)

    def save(self, path):
        self.img.resize((1024, 1024), Image.LANCZOS).save(path)
        return path


# ---------------------------------------------------------------------------
# Shared painted pieces.
def cyclops_face(p, skin, iris=(230, 170, 60), corruption=0.0):
    """Fierce painted cyclops face: no mouth, one narrowed eye under a heavy V brow,
    a shadowed socket and a slit pupil."""
    P = "Head"
    dark = tuple(int(c * 0.5) for c in skin)
    socket = tuple(int(c * 0.72) for c in skin)
    # Shadowed socket around the eye.
    p.ellipse(P, "front", 0.5, 0.530, 0.3, 0.2, socket)
    # Eye: almond white, glowing iris, slit pupil, glint.
    p.ellipse(P, "front", 0.5, 0.540, 0.24, 0.13, (240, 232, 220), outline=(25, 18, 20), width=7)
    p.ellipse(P, "front", 0.5, 0.550, 0.11, 0.11, iris, outline=(70, 30, 15), width=4)
    p.ellipse(P, "front", 0.5, 0.550, 0.06, 0.06, tuple(min(255, int(c * 1.25)) for c in iris))
    p.ellipse(P, "front", 0.5, 0.550, 0.022, 0.085, (12, 6, 12))
    p.ellipse(P, "front", 0.455, 0.510, 0.02, 0.02, (255, 255, 255))
    if corruption:
        p.ellipse(P, "front", 0.5, 0.550, 0.135, 0.135, None, outline=(190, 80, 255), width=4)
    # Upper lid slanting down to the middle: it cuts the top of the eye for an angry glare.
    p.poly(P, "front", [(0.2, 0.380), (0.5, 0.500), (0.8, 0.380), (0.8, 0.440), (0.5, 0.550), (0.2, 0.440)], socket)
    p.line(P, "front", [(0.24, 0.435), (0.5, 0.545), (0.76, 0.435)], (25, 18, 20), width=7)
    # Heavy V brow.
    p.poly(P, "front", [(0.12, 0.280), (0.5, 0.440), (0.88, 0.280), (0.88, 0.360), (0.5, 0.500), (0.12, 0.360)], dark)
    # Lower lid crease and frown lines; no mouth.
    p.line(P, "front", [(0.32, 0.680), (0.5, 0.710), (0.68, 0.680)], socket, width=5)
    p.line(P, "front", [(0.47, 0.500), (0.45, 0.410)], dark, width=4)
    p.line(P, "front", [(0.53, 0.500), (0.55, 0.410)], dark, width=4)


def skin_part(p, part, skin, faces=FACES):
    p.fill(part, faces, skin)


# ---------------------------------------------------------------------------
def villager():
    """Stage-1 villager: linen shirt, brown vest, rope belt, patched trousers,
    leg wraps, worn shoes; the corruption has only cracked the left forearm."""
    skin = (150, 158, 150)
    linen, vest, pants = (214, 200, 168), (110, 74, 46), (92, 70, 50)
    rope, leather = (170, 140, 90), (78, 52, 34)
    p = Painter(seed=5)
    # Head: skin all round, short brown hair on top and back, painted face.
    p.fill("Head", FACES, skin)
    hair = (88, 62, 42)
    p.fill("Head", ("top",), hair)
    p.box("Head", "back", 0, 0, 1, 0.45, hair)
    for side in ("left", "right"):
        p.box("Head", side, 0, 0, 1, 0.22, hair)
    p.poly("Head", "front", [(0, 0), (1, 0), (1, 0.1), (0.7, 0.16), (0.55, 0.08), (0.35, 0.15), (0, 0.1)], hair)
    cyclops_face(p, skin)
    # Upper torso: shirt with an open vest, buttons and a V-neck.
    p.fill("UpperTorso", FACES, linen)
    p.poly("UpperTorso", "front", [(0.38, 0), (0.62, 0), (0.5, 0.3)], skin)
    p.line("UpperTorso", "front", [(0.38, 0), (0.5, 0.3), (0.62, 0)], (150, 120, 90), width=5)
    for s in (0, 1):
        u0, u1 = (0.0, 0.33) if s == 0 else (0.67, 1.0)
        p.box("UpperTorso", "front", u0, 0, u1, 1, vest)
        edge = 0.33 if s == 0 else 0.67
        p.dashes("UpperTorso", "front", [(edge - (0.03 if s == 0 else -0.03), 0.02), (edge - (0.03 if s == 0 else -0.03), 0.98)],
                 (190, 150, 110))
    for v in (0.42, 0.62, 0.82):
        p.ellipse("UpperTorso", "front", 0.36, v, 0.025, 0.025, (60, 40, 25))
    p.fill("UpperTorso", ("back",), vest)
    p.dashes("UpperTorso", "back", [(0.5, 0.05), (0.5, 0.95)], (150, 110, 80))
    for side in ("left", "right"):
        p.box("UpperTorso", side, 0, 0, 1, 1, vest)
    p.folds("UpperTorso", "front", (180, 165, 135), 2, seed=1)
    # Lower torso: tunic hem with a rope belt.
    p.fill("LowerTorso", FACES, linen)
    for face in ("front", "back", "left", "right"):
        p.box("LowerTorso", face, 0, 0.2, 1, 0.75, rope)
        p.line("LowerTorso", face, [(0, 0.47), (1, 0.47)], (120, 95, 60), width=4)
    p.ellipse("LowerTorso", "front", 0.7, 0.5, 0.06, 0.3, rope, outline=(120, 95, 60), width=3)
    # Arms: rolled linen sleeves, bare forearms (left one cracking), skin hands.
    for side in ("Left", "Right"):
        p.fill(side + "UpperArm", FACES, linen)
        for face in ("front", "back", "left", "right"):
            p.box(side + "UpperArm", face, 0, 0.78, 1, 1, (196, 182, 150))
            p.line(side + "UpperArm", face, [(0, 0.8), (1, 0.82)], (160, 140, 110), width=4)
            p.folds(side + "UpperArm", face, (185, 170, 140), 2, horizontal=True)
        p.fill(side + "LowerArm", FACES, skin)
        p.fill(side + "Hand", FACES, skin)
        for face in ("front", "back"):
            for u in (0.25, 0.5, 0.75):
                p.line(side + "Hand", face, [(u, 0.2), (u, 0.8)], tuple(int(c * 0.75) for c in skin), width=3)
    for face in ("front", "left", "back"):
        p.cracks("LeftLowerArm", face, (50, 30, 60), (170, 70, 255), count=3, seed=hash(face) % 100)
    # Legs: patched trousers, linen wraps on the shins, leather shoes.
    for side in ("Left", "Right"):
        p.fill(side + "UpperLeg", FACES, pants)
        for face in ("front", "back", "left", "right"):
            p.folds(side + "UpperLeg", face, (70, 52, 36), 3)
        p.fill(side + "LowerLeg", FACES, pants)
        for face in ("front", "back", "left", "right"):
            for v in (0.3, 0.45, 0.6, 0.75, 0.9):
                p.box(side + "LowerLeg", face, 0, v - 0.05, 1, v + 0.04, linen)
                p.line(side + "LowerLeg", face, [(0, v + 0.04), (1, v + 0.03)], (150, 135, 105), width=3)
        p.fill(side + "Foot", FACES, leather)
        p.box(side + "Foot", "top", 0.2, 0.0, 0.8, 0.6, (95, 64, 42))
        for v in (0.15, 0.3, 0.45):
            p.line(side + "Foot", "top", [(0.3, v), (0.7, v + 0.05)], (200, 180, 140), width=3)
    # A knee patch with stitches.
    p.box("RightUpperLeg", "front", 0.3, 0.55, 0.75, 0.9, (130, 100, 70))
    p.dashes("RightUpperLeg", "front", [(0.3, 0.55), (0.75, 0.55), (0.75, 0.9), (0.3, 0.9), (0.3, 0.55)],
             (200, 180, 140), dash=8, gap=6)
    p.shade()

    spec = {
        "Head": dict(bevel=0.26),
        "UpperTorso": dict(bevel=0.16),
        "LeftFoot": dict(size=(1.12, 1.3, 0.5), center=(0, -0.12, 0.02), bevel=0.14),
        "RightFoot": dict(size=(1.12, 1.3, 0.5), center=(0, -0.12, 0.02), bevel=0.14),
    }
    return "Villager", p, spec, villager_extras


def villager_extras(material):
    """Smooth geometry where the silhouette needs it: hair tuft and ears."""
    bm = bmesh.new()
    for i, (x, z) in enumerate(((-0.1, 0.0), (0.1, 0.05), (0.0, 0.08))):
        cone = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.16, radius2=0.0, depth=0.42,
                                     matrix=Matrix.Translation((x, 0.05 * i, 0.72 + z)) @ Matrix.Rotation(0.3 * (i - 1), 4, "Y"))
    return bm


# ---------------------------------------------------------------------------
def render(objs, name):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 48
    scene.cycles.use_denoising = True
    scene.view_settings.view_transform = "Standard"
    world = bpy.data.worlds.new("W")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.35, 0.38, 0.45, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6
    scene.world = world
    sun = bpy.data.lights.new("Sun", "SUN")
    sun.energy = 3.0
    so = bpy.data.objects.new("Sun", sun)
    so.rotation_euler = (math.radians(50), math.radians(-20), math.radians(-35))
    scene.collection.objects.link(so)
    cam = bpy.data.cameras.new("Cam")
    cam.lens = 50
    co = bpy.data.objects.new("Cam", cam)
    scene.collection.objects.link(co)
    scene.camera = co
    paths = []
    for tag, loc in (("front", (-4.5, -11, 4.2)), ("back", (5, 11, 4.2))):
        co.location = loc
        co.rotation_euler = (Vector((0, 0, 2.8)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        scene.render.resolution_x, scene.render.resolution_y = 900, 1100
        path = os.path.join(RENDERS, f"style2_{name}_{tag}.png")
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        paths.append(path)
    imgs = [Image.open(x) for x in paths]
    sheet = Image.new("RGB", (sum(i.width for i in imgs), imgs[0].height))
    x = 0
    for i in imgs:
        sheet.paste(i, (x, 0))
        x += i.width
    sheet.save(os.path.join(RENDERS, f"style2_{name}.png"))


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(RENDERS, exist_ok=True)
    name, painter, spec, extras = villager()
    tex_path = painter.save(os.path.join(OUT, f"{name}_texture.png"))
    img = bpy.data.images.load(tex_path)
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    t = mat.node_tree.nodes.new("ShaderNodeTexImage")
    t.image = img
    mat.node_tree.links.new(t.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.8
    objs = build_shells(spec, mat)
    render(objs, name)


if __name__ == "__main__":
    main()

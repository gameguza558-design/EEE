"""Stylized clump hair for Roblox-style heads (original geometry, made in code).

Hair is built like the catalog anime hairs: a scalp cap plus many curved, tapered,
flattened clumps that sweep from the scalp outward and down, layered for volume.
Each style returns a bmesh in Head-local space (Blender units = studs, front = -Y)
with UVs running root -> tip down a small painted hair texture.
"""
import math
import random

import bmesh
from mathutils import Vector
from PIL import Image, ImageDraw, ImageFilter

HEAD_CENTER = Vector((0, 0.0, 0.02))
SCALP_R = 0.66
HEAD_HALF = 0.6  # the R15 head is a rounded 1.2 stud block, not a sphere


def scalp(d, pad=0.04):
    """Point on a rounded-box scalp (superellipse, p = 4) in direction d."""
    d = Vector(d).normalized()
    k = (abs(d.x) ** 4 + abs(d.y) ** 4 + abs(d.z) ** 4) ** 0.25
    return HEAD_CENTER + d / k * (HEAD_HALF + pad)


def hair_texture(path, base, tip, highlight, size=256, seed=0):
    """Vertical strip: roots (top) -> tips (bottom) with strand lines and a shine band."""
    rnd = random.Random(seed)
    img = Image.new("RGB", (size, size))
    d = ImageDraw.Draw(img)
    for y in range(size):
        t = y / (size - 1)
        c = tuple(int(base[i] + (tip[i] - base[i]) * t) for i in range(3))
        d.line([(0, y), (size, y)], fill=c)
    for _ in range(90):  # strands
        x = rnd.uniform(0, size)
        shade = rnd.uniform(-35, 25)
        col = tuple(max(0, min(255, int(base[i] + shade))) for i in range(3))
        d.line([(x, 0), (x + rnd.uniform(-6, 6), size)], fill=col, width=rnd.choice((1, 1, 2)))
    shine = Image.new("L", (size, size), 0)
    sd = ImageDraw.Draw(shine)
    sd.rectangle([0, int(size * 0.18), size, int(size * 0.3)], fill=150)
    shine = shine.filter(ImageFilter.GaussianBlur(10))
    img = Image.composite(Image.new("RGB", (size, size), highlight), img, shine)
    img.save(path)
    return path


class HairBuilder:
    def __init__(self, seed=0):
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new("UVMap")
        self.rnd = random.Random(seed)
        self.pad = 0.02  # how far above the head surface clumps start (bigger over helmets)
        self.chunky = False  # six-sided ridged clumps (thicker anime look)

    def _face(self, verts, uvs):
        f = self.bm.faces.new(verts)
        for loop, uv in zip(f.loops, uvs):
            loop[self.uv].uv = uv
        return f

    def cap(self, radius=SCALP_R + 0.02, front_cut=0.15, back_low=-0.45, sides=16, rings=7):
        """Scalp cap: a dome over the top and back of the head, open at the face."""
        rows = []
        for r in range(rings + 1):
            lat = math.pi / 2 * (1 - r / rings)  # 90deg (top) -> 0 (equator)
            row = []
            for s in range(sides):
                lon = 2 * math.pi * s / sides
                d = Vector((math.cos(lat) * math.sin(lon), -math.cos(lat) * math.cos(lon), math.sin(lat)))
                # Pull the rim down at the back, up at the face.
                if r == rings:
                    back = (1 - math.cos(lon)) / 2  # 0 at the front, 1 at the back
                    d.z = front_cut + (back_low - front_cut) * back
                row.append(self.bm.verts.new(scalp(d, radius - HEAD_HALF) if r < rings
                                             else scalp(Vector((d.x, d.y, 0)), radius - HEAD_HALF) + Vector((0, 0, d.z * HEAD_HALF))))
            rows.append(row)
        for r in range(rings):
            for s in range(sides):
                t = (s + 1) % sides
                q = [rows[r][s], rows[r][t], rows[r + 1][t], rows[r + 1][s]]
                self._face(q, [(s / sides, 1 - r / rings * 0.4), ((s + 1) / sides, 1 - r / rings * 0.4),
                               ((s + 1) / sides, 1 - (r + 1) / rings * 0.4), (s / sides, 1 - (r + 1) / rings * 0.4)])

    def clump(self, root_dir, length, width, gravity=0.6, curl=0.0, lift=0.0, thickness=0.35, segments=6,
              twist=0.0):
        """One tapered, flattened clump of hair growing from the scalp along root_dir."""
        n = Vector(root_dir).normalized()
        p = scalp(n, self.pad)
        direction = (n + Vector((0, 0, lift))).normalized()
        side = n.cross(Vector((0, 0, 1)))
        if side.length < 1e-3:
            side = Vector((1, 0, 0))
        side.normalize()
        pts = [p]
        step = length / segments
        for i in range(segments):
            # Bend toward the ground (gravity) and around (curl) as the clump grows.
            direction = (direction + Vector((0, 0, -gravity * 0.35)) + side * curl * 0.25).normalized()
            p = p + direction * step
            # Keep strands from cutting back into the head.
            surface = scalp(p - HEAD_CENTER, 0.05)
            if (p - HEAD_CENTER).length < (surface - HEAD_CENTER).length:
                p = surface
            pts.append(p)
        rings = []
        for i, c in enumerate(pts[:-1]):
            t = i / segments
            w = width * (1 - t) ** 0.7
            fwd = (pts[i + 1] - c).normalized()
            out = (c - HEAD_CENTER).normalized()
            flat = fwd.cross(out).normalized()  # across the clump
            out = flat.cross(fwd).normalized()  # facing away from the head
            a = twist * t
            flat, out = flat * math.cos(a) + out * math.sin(a), out * math.cos(a) - flat * math.sin(a)
            th = w * thickness
            if self.chunky:
                # Six-sided, ridged section: a thick anime clump rather than a flat ribbon.
                ring = [c + flat * w, c + flat * w * 0.45 + out * th, c - flat * w * 0.45 + out * th * 0.8,
                        c - flat * w, c - flat * w * 0.4 - out * th * 0.55, c + flat * w * 0.4 - out * th * 0.55]
            else:
                ring = [c + flat * w, c + out * th, c - flat * w, c - out * th * 0.6]
            rings.append([self.bm.verts.new(v) for v in ring])
        tip = self.bm.verts.new(pts[-1])
        n = len(rings[0])
        for i in range(len(rings) - 1):
            a, b = rings[i], rings[i + 1]
            v0, v1 = 1 - i / segments, 1 - (i + 1) / segments
            for k in range(n):
                j = (k + 1) % n
                self._face([a[k], a[j], b[j], b[k]], [(k / n, v0), ((k + 1) / n, v0), ((k + 1) / n, v1), (k / n, v1)])
        last = rings[-1]
        for k in range(n):
            self._face([last[k], last[(k + 1) % n], tip], [(k / n, 0.1), ((k + 1) / n, 0.1), ((k + 0.5) / n, 0.0)])
        self._face(list(reversed(rings[0])), [((k + 0.5) / n, 1.0) for k in range(n)])  # close the root

    def finish(self):
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        return self.bm


def around(rnd, count, lat_range, lon_range):
    """Directions on the scalp: latitude 0 = equator, 90 = crown; longitude 0 = front."""
    for i in range(count):
        lat = math.radians(rnd.uniform(*lat_range))
        lon = math.radians(lon_range[0] + (lon_range[1] - lon_range[0]) * (i + rnd.random()) / count)
        yield Vector((math.cos(lat) * math.sin(lon), -math.cos(lat) * math.cos(lon), math.sin(lat)))


# ---------------------------------------------------------------------------
# Styles
def messy_short(seed=1):
    """Short, layered, slightly spiky hair (villager)."""
    h = HairBuilder(seed)
    h.cap(front_cut=0.32, back_low=-0.3)
    rnd = h.rnd
    for d in around(rnd, 26, (5, 35), (40, 320)):  # sides and back, hanging down
        h.clump(d, rnd.uniform(0.38, 0.55), rnd.uniform(0.15, 0.2), gravity=0.9, lift=-0.2, twist=rnd.uniform(-0.4, 0.4))
    for d in around(rnd, 16, (40, 75), (0, 360)):  # crown, sticking out a little
        h.clump(d, rnd.uniform(0.3, 0.45), rnd.uniform(0.15, 0.19), gravity=0.35, lift=0.3, curl=rnd.uniform(-0.4, 0.4))
    for d in around(rnd, 6, (35, 50), (-50, 50)):  # fringe swept to the sides, clear of the eye
        h.clump(d, rnd.uniform(0.3, 0.4), 0.16, gravity=0.7, curl=1.0 if d.x > 0 else -1.0, lift=0.1)
    return h.finish()


def wild_mane(seed=2):
    """Big, wild, spiky mane sweeping up and back (the Cyclops King)."""
    h = HairBuilder(seed)
    h.cap(front_cut=0.3, back_low=-0.55)
    rnd = h.rnd
    for d in around(rnd, 30, (30, 85), (25, 335)):  # long spikes up and back
        h.clump(d + Vector((0, 0.7, 0)), rnd.uniform(1.1, 2.1), rnd.uniform(0.2, 0.28), gravity=-0.1, lift=0.45,
                curl=rnd.uniform(-0.3, 0.3), twist=rnd.uniform(-0.6, 0.6))
    for d in around(rnd, 26, (-10, 30), (60, 300)):  # mane falling down the back
        h.clump(d, rnd.uniform(1.0, 1.7), rnd.uniform(0.2, 0.26), gravity=0.8, lift=-0.1, twist=rnd.uniform(-0.5, 0.5))
    for s in (1, -1):  # spiky bangs at the temples framing the eye
        for k in range(3):
            d = Vector((s * (0.75 - 0.1 * k), -0.6, 0.35 + 0.1 * k))
            h.clump(d, 0.7 - 0.1 * k, 0.17, gravity=0.6, curl=s * 0.8, lift=0.2)
    return h.finish()


def top_knot(seed=3):
    """Shaved sides with a short tied knot (woodcutter)."""
    h = HairBuilder(seed)
    h.cap(front_cut=0.45, back_low=0.0)
    rnd = h.rnd
    for d in around(rnd, 10, (60, 85), (0, 360)):
        h.clump(d, 0.35, 0.16, gravity=-0.2, lift=0.8, curl=rnd.uniform(-0.6, 0.6))
    for d in around(rnd, 5, (80, 89), (0, 360)):
        h.clump(d, 0.5, 0.14, gravity=0.6, lift=0.5, curl=1.2)
    return h.finish()


def beard(seed=4, length=0.55):
    """Full beard under the eye (clumps growing down from cheeks and chin)."""
    h = HairBuilder(seed)
    rnd = h.rnd
    for i in range(16):
        a = math.radians(-70 + 140 * i / 15)
        d = Vector((math.sin(a) * 0.9, -math.cos(a) * 0.9, -0.55))
        h.clump(d, length + rnd.uniform(-0.1, 0.15), 0.17, gravity=1.0, lift=-0.4, thickness=0.5)
    return h.finish()


def king_mane(seed=5):
    """Boros-style mane: a huge mass of long hair swept back from a spiky crown and
    pouring down the back to the waist, with long locks framing the face."""
    h = HairBuilder(seed)
    h.cap(front_cut=0.28, back_low=-0.6)
    rnd = h.rnd
    # Spiky crown, flaring up and back.
    for d in around(rnd, 22, (45, 88), (0, 360)):
        h.clump(d + Vector((0, 0.5, 0.2)), rnd.uniform(0.8, 1.5), rnd.uniform(0.18, 0.26), gravity=0.1, lift=0.7,
                curl=rnd.uniform(-0.4, 0.4), twist=rnd.uniform(-0.6, 0.6))
    # The big mass: long locks sweeping back, then falling down the back (to the waist).
    for lat, length, width in ((35, (2.6, 3.4), (0.3, 0.4)), (15, (2.2, 3.0), (0.28, 0.36)),
                               (-5, (1.8, 2.6), (0.26, 0.34))):
        for d in around(rnd, 22, (lat - 10, lat + 10), (40, 320)):
            out = Vector((d.x * 1.6, d.y, d.z))  # flare outward for volume
            h.clump(out + Vector((0, 0.9, 0.35)), rnd.uniform(*length), rnd.uniform(*width), gravity=0.75, lift=0.35,
                    curl=rnd.uniform(-0.25, 0.25), twist=rnd.uniform(-0.5, 0.5), segments=9)
    # Long locks over the temples, falling in front of the shoulders.
    for s in (1, -1):
        for k in range(4):
            d = Vector((s * (0.85 - 0.08 * k), -0.45 + 0.1 * k, 0.3 + 0.08 * k))
            h.clump(d, rnd.uniform(1.4, 2.0), 0.2, gravity=0.9, curl=s * 0.35, lift=0.25, segments=8)
    # A few spiky bangs, kept off the eye.
    for s in (1, -1):
        h.clump(Vector((s * 0.55, -0.7, 0.5)), 0.55, 0.15, gravity=0.6, curl=s * 0.9, lift=0.3)
    return h.finish()


def king_crown(seed=8):
    """Original hair for the King, inspired by a big spiky catalog mane: a dense crown of
    thick spikes swept up and back, layered locks falling to the shoulders, and loose,
    uneven bangs above the eye."""
    h = HairBuilder(seed)
    h.chunky = True
    h.cap(front_cut=0.38, back_low=-0.5)
    rnd = h.rnd
    # Crown: dense spikes swept up and strongly back.
    for d in around(rnd, 30, (40, 88), (0, 360)):
        h.clump(d + Vector((0, 0.85, 0.55)), rnd.uniform(0.85, 1.6), rnd.uniform(0.26, 0.34), gravity=-0.1,
                lift=0.35, curl=rnd.uniform(-0.45, 0.45), twist=rnd.uniform(-0.7, 0.7), thickness=0.55, segments=7)
    # Mid layer: spikes pointing out and back all round, slightly drooping.
    for d in around(rnd, 28, (8, 40), (20, 340)):
        h.clump(Vector((d.x * 1.15, d.y + 0.55, d.z + 0.15)), rnd.uniform(0.75, 1.25), rnd.uniform(0.24, 0.31),
                gravity=0.3, lift=0.1, curl=rnd.uniform(-0.5, 0.5), twist=rnd.uniform(-0.7, 0.7), thickness=0.5)
    # Back: heavy locks falling to the shoulders.
    for d in around(rnd, 24, (-20, 18), (90, 270)):
        h.clump(d + Vector((0, 0.35, 0)), rnd.uniform(1.1, 1.75), rnd.uniform(0.25, 0.32), gravity=0.95, lift=-0.1,
                curl=rnd.uniform(-0.3, 0.3), twist=rnd.uniform(-0.6, 0.6), thickness=0.5, segments=8)
    # Bangs: uneven clumps from the hairline, hanging over the forehead, clear of the eye.
    for k in range(7):
        x = -0.45 + 0.15 * k + rnd.uniform(-0.04, 0.04)
        root = Vector((x, -0.75, 0.8))
        h.clump(root, rnd.uniform(0.6, 0.85), rnd.uniform(0.2, 0.26), gravity=1.3, lift=0.2,
                curl=(1 if x > 0 else -1) * rnd.uniform(0.2, 0.6), twist=rnd.uniform(-0.4, 0.4), thickness=0.5)
    # Side locks framing the face down to the jaw.
    for s in (1, -1):
        for k in range(3):
            h.clump(Vector((s * 0.95, -0.4 + 0.18 * k, 0.3)), 0.9 - 0.12 * k, 0.19, gravity=1.0,
                    curl=s * 0.25, twist=rnd.uniform(-0.4, 0.4), thickness=0.5, segments=7)
    return h.finish()


STYLES = {"king_crown": king_crown, "king_mane": king_mane, "messy_short": messy_short, "wild_mane": wild_mane, "top_knot": top_knot, "beard": beard}

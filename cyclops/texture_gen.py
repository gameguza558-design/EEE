"""Hand-painted-style texture atlas shared by every corrupted cyclops, generated with
numpy + Pillow.

The atlas is a 6x6 grid of 170 px tiles (1024 px image). Every face of the model is mapped onto the
whole tile of its material, so each tile is painted like a single armor plate: a
beveled edge, a dark seam, corner rivets, scratches and grime toward the bottom.
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

GRID = 6
ATLAS = 1024
TS = ATLAS // GRID  # tile size in px
K = TS / 256  # scale for sizes tuned at 256 px

TILES = [
    "plate_dark", "plate_mid", "plate_trim", "plate_corrupt", "plate_rust", "gold",
    "leather", "leather_strap", "buckle", "cloth", "cloth_dark", "chainmail",
    "black", "blade", "blade_corrupt", "horn", "glow", "body",
    "skin", "skin_corrupt", "skin_king", "hair", "eye", "fur",
    "cloth_brown", "cloth_green", "linen", "quilt", "wood", "iron",
    "pants", "shield", "fur_dark", "rope", "plate_corrupt_heavy", "bone",
]

PURPLE = np.array([0.72, 0.30, 1.0])
PURPLE_CORE = np.array([0.93, 0.80, 1.0])

YY, XX = np.mgrid[0:TS, 0:TS].astype(np.float32)


def tile_rect(name):
    """(u0, v0, size) of a tile in UV space (v up)."""
    i = TILES.index(name)
    col, row = i % GRID, i // GRID
    size = TS / ATLAS
    return col * size, 1 - (row + 1) * size, size


# ---------------------------------------------------------------------------
def fbm(rng, octaves=((4, 0.5), (8, 0.25), (16, 0.15), (32, 0.1)), aspect=(1, 1)):
    """Smooth value noise in [-0.5, 0.5]-ish. aspect stretches cells (rows, cols)."""
    acc = np.zeros((TS, TS), np.float32)
    for cells, amp in octaves:
        small = rng.random((max(2, cells * aspect[0]), max(2, cells * aspect[1])))
        img = Image.fromarray((small * 255).astype(np.uint8)).resize((TS, TS), Image.BICUBIC)
        acc += (np.asarray(img, np.float32) / 255 - 0.5) * amp
    return acc


def solid(color):
    return np.ones((TS, TS, 3), np.float32) * np.array(color, np.float32)


def shade(tile, amount):
    """Brighten (+) or darken (-) by a per-pixel amount."""
    return tile + amount[..., None]


def bevel(tile, width=14, hi=0.16, lo=0.16, seam=3):
    width, seam = width * K, max(2, seam * K)
    top = np.clip(1 - YY / width, 0, 1)
    left = np.clip(1 - XX / width, 0, 1)
    bottom = np.clip(1 - (TS - 1 - YY) / width, 0, 1)
    right = np.clip(1 - (TS - 1 - XX) / width, 0, 1)
    tile = shade(tile, hi * top + hi * 0.7 * left - lo * bottom - lo * 0.7 * right)
    edge = np.minimum(np.minimum(YY, XX), np.minimum(TS - 1 - YY, TS - 1 - XX))
    tile[edge < seam] *= 0.45
    return tile


def grime(tile, rng, strength=0.35):
    """Darker toward the bottom, broken up by noise."""
    n = fbm(rng) + 0.5
    amount = strength * (YY / TS) ** 2 * n
    return tile * (1 - amount[..., None])


def scratches(tile, rng, count=40, light=0.14, horizontal=True):
    mask = Image.new("L", (TS, TS), 0)
    d = ImageDraw.Draw(mask)
    for _ in range(count):
        x, y = rng.uniform(0, TS), rng.uniform(0, TS)
        base = 0 if horizontal else math.pi / 2
        a = base + rng.uniform(-0.35, 0.35)
        length = rng.uniform(15, 80)
        d.line([(x, y), (x + math.cos(a) * length, y + math.sin(a) * length)],
               fill=int(rng.uniform(120, 255)), width=1)
    m = np.asarray(mask, np.float32) / 255
    return shade(tile, m * light)


def rivets(tile, inset=22, r=7, mids=False, color=(0.55, 0.54, 0.6)):
    inset, r = inset * K, r * K
    spots = [(inset, inset), (TS - inset, inset), (inset, TS - inset), (TS - inset, TS - inset)]
    if mids:
        spots += [(TS // 2, inset), (TS // 2, TS - inset)]
    for cx, cy in spots:
        dx, dy = XX - cx, YY - cy
        dist = np.sqrt(dx * dx + dy * dy)
        head = dist < r
        ring = (dist >= r) & (dist < r + 2.2)
        light = 0.62 + 0.3 * np.clip(-(dx + dy) / (r * 1.5), -1, 1)
        tile[head] = (np.array(color) * light[head][:, None])
        tile[ring] *= 0.35
    return tile


def veins(tile, rng, count=5, width=2, glow_radius=6, strength=1.0, color=None, core_color=None,
          dark=False):
    """Glowing corruption cracks: branching random walks."""
    mask = Image.new("L", (TS, TS), 0)
    d = ImageDraw.Draw(mask)

    def walk(x, y, a, steps, w):
        for _ in range(steps):
            a += rng.uniform(-0.6, 0.6)
            nx, ny = x + math.cos(a) * rng.uniform(6, 14), y + math.sin(a) * rng.uniform(6, 14)
            d.line([(x, y), (nx, ny)], fill=255, width=w)
            if rng.random() < 0.18 and w > 1:
                walk(nx, ny, a + rng.choice((-1, 1)) * rng.uniform(0.6, 1.2), steps // 2, w - 1)
            x, y = nx, ny

    for _ in range(count):
        walk(rng.uniform(0, TS), rng.uniform(0, TS), rng.uniform(0, 2 * math.pi),
             rng.integers(8, 18), width)
    color = PURPLE if color is None else np.array(color)
    core_color = PURPLE_CORE if core_color is None else np.array(core_color)
    core = np.asarray(mask, np.float32) / 255
    glow = np.asarray(mask.filter(ImageFilter.GaussianBlur(glow_radius * K)), np.float32) / 255
    glow = np.clip(glow * 2.2, 0, 1) * strength
    if dark:
        # Dark cracks with a thin glowing rim (skin): darken the core, tint around it.
        tile = tile * (1 - glow[..., None] * 0.35) + color * glow[..., None] * 0.35
        return tile * (1 - core[..., None] * 0.85) + np.array([0.08, 0.02, 0.08]) * core[..., None]
    tile = tile * (1 - glow[..., None] * 0.6) + color * glow[..., None] * 0.85
    return tile * (1 - core[..., None]) + core_color * core[..., None]


# ---------------------------------------------------------------------------
def plate(rng, color, corrupt=False, rivet=True):
    t = solid(color)
    t = shade(t, fbm(rng) * 0.16)
    t = shade(t, fbm(rng, ((24, 0.5), (48, 0.5))) * 0.05)
    t = scratches(t, rng)
    t = grime(t, rng)
    t = bevel(t)
    if rivet:
        t = rivets(t)
    if corrupt:
        t = veins(t, rng)
    return t


def leather(rng, color, stitch=True):
    t = solid(color)
    t = shade(t, fbm(rng) * 0.18)
    t = shade(t, fbm(rng, ((64, 0.6), (128, 0.4))) * 0.08)
    t = grime(t, rng, 0.25)
    t = bevel(t, width=8, hi=0.08, lo=0.12, seam=2)
    if stitch:
        img = Image.fromarray((np.clip(t, 0, 1) * 255).astype(np.uint8))
        d = ImageDraw.Draw(img)
        c = (178, 142, 104)
        i = 10
        for k in range(i, TS - i, 10):
            d.line([(k, i), (k + 5, i)], fill=c, width=2)
            d.line([(k, TS - i), (k + 5, TS - i)], fill=c, width=2)
            d.line([(i, k), (i, k + 5)], fill=c, width=2)
            d.line([(TS - i, k), (TS - i, k + 5)], fill=c, width=2)
        t = np.asarray(img, np.float32) / 255
    return t


def buckle(rng):
    t = solid((0.5, 0.44, 0.33))
    t = shade(t, fbm(rng) * 0.18)
    t = scratches(t, rng, 30, 0.2)
    t = bevel(t, width=26, hi=0.25, lo=0.25, seam=4)
    return t


def cloth(rng, color):
    t = solid(color)
    weave = 0.05 * np.sin(XX * 1.7) * np.sin(YY * 1.7)
    t = shade(t, weave)
    t = shade(t, fbm(rng, ((8, 0.5), (64, 0.5)), aspect=(1, 6)) * 0.14)  # vertical streaks
    t = shade(t, fbm(rng) * 0.14)
    t = grime(t, rng, 0.55)
    # Worn, lighter frayed edge along the top.
    t = shade(t, np.clip(1 - YY / 10, 0, 1) * 0.08)
    return t


def chainmail(rng):
    img = Image.new("RGB", (TS, TS), (18, 17, 20))
    d = ImageDraw.Draw(img)
    step = 8
    for row in range(-1, TS // step + 2):
        off = (step // 2) if row % 2 else 0
        for col in range(-1, TS // step + 2):
            x, y = col * step + off, row * step
            d.ellipse([x - 4.5, y - 4.5, x + 4.5, y + 4.5], outline=(102, 100, 110), width=2)
            d.arc([x - 4.5, y - 4.5, x + 4.5, y + 4.5], 200, 290, fill=(160, 158, 170), width=1)
    t = np.asarray(img, np.float32) / 255
    t = shade(t, fbm(rng) * 0.1)
    return grime(t, rng, 0.45)


def blade(rng, corrupt=False):
    t = solid((0.66, 0.66, 0.71))
    t = shade(t, fbm(rng, ((2, 0.5), (64, 0.5)), aspect=(1, 32)) * 0.12)  # brushed lengthwise
    t = shade(t, fbm(rng) * 0.08)
    t = scratches(t, rng, 50, 0.12, horizontal=False)
    edge = np.clip(1 - np.minimum(XX, TS - 1 - XX) / 24, 0, 1)
    t = shade(t, edge * 0.18)
    t = grime(t, rng, 0.2)
    if corrupt:
        t = veins(t, rng, count=7, strength=0.9)
    return t


def horn(rng):
    v = YY / TS
    t = solid((0.0, 0.0, 0.0))
    t[:] = (np.array([0.33, 0.2, 0.47]) * (1 - v)[..., None] + np.array([0.1, 0.07, 0.13]) * v[..., None])
    t = shade(t, fbm(rng, ((4, 0.5), (48, 0.5)), aspect=(1, 8)) * 0.12)
    return veins(t, rng, count=3, width=1, glow_radius=4, strength=0.6)


def glow(rng):
    cx = np.abs(XX - TS / 2) / (TS / 2)
    cy = np.abs(YY - TS / 2) / (TS / 2)
    r = np.clip(np.maximum(cx, cy), 0, 1)
    t = PURPLE_CORE * (1 - r)[..., None] + np.array([0.55, 0.2, 0.92]) * r[..., None]
    return shade(t.astype(np.float32), fbm(rng) * 0.1)


def skin(rng, color, level=0.0, king=False):
    """Grey cyclops skin: mottled, with muscle shading toward the edges of each face.
    level adds dark corruption cracks with a glowing rim."""
    t = solid(color)
    t = shade(t, fbm(rng) * 0.12)
    t = shade(t, fbm(rng, ((48, 0.6), (96, 0.4))) * 0.04)
    edge = np.minimum(np.minimum(XX, TS - 1 - XX), np.minimum(YY, TS - 1 - YY)) / (TS / 2)
    t = shade(t, -(1 - np.clip(edge * 2.2, 0, 1)) * 0.12)  # soft form shadow
    if level:
        glow_color = (1.0, 0.35, 0.8) if king else (0.72, 0.3, 1.0)
        t = veins(t, rng, count=int(4 + 10 * level), width=3 if king else 2,
                  glow_radius=7, strength=level, color=glow_color, dark=True)
    return t


def hair(rng):
    """Pale, spiky mane: long strands running up the tile, darker at the roots."""
    v = YY / TS
    t = solid((0.0, 0.0, 0.0))
    t[:] = np.array([0.9, 0.84, 0.88]) * (1 - v)[..., None] + np.array([0.5, 0.42, 0.5]) * v[..., None]
    t = shade(t, fbm(rng, ((3, 0.4), (90, 0.6)), aspect=(1, 10)) * 0.25)
    return veins(t, rng, count=4, width=1, glow_radius=3, strength=0.6, color=(1.0, 0.35, 0.8),
                 dark=True)


def eye(rng, iris=(1.0, 0.25, 0.75)):
    """Big cyclops eye: pale sclera, glowing iris and a slit pupil, filling the tile."""
    cx, cy = XX - TS / 2, YY - TS / 2
    r = np.sqrt(cx * cx + cy * cy) / (TS / 2)
    t = solid((0.93, 0.9, 0.9))
    t = shade(t, -np.clip(r - 0.6, 0, 1) * 0.6)  # shadow toward the lids
    iris_mask = r < 0.42
    ring = np.clip(1 - r / 0.42, 0, 1)
    t[iris_mask] = (np.array(iris) * (0.55 + 0.6 * ring[iris_mask])[:, None])
    pupil = (np.abs(cx) < TS * 0.035) & (np.abs(cy) < TS * 0.17)
    t[pupil] = (0.05, 0.0, 0.05)
    glint = (cx + TS * 0.1) ** 2 + (cy + TS * 0.1) ** 2 < (TS * 0.05) ** 2
    t[glint] = (1, 1, 1)
    return t


def fur(rng, color):
    t = solid(color)
    t = shade(t, fbm(rng, ((6, 0.4), (80, 0.6)), aspect=(1, 5)) * 0.3)
    t = scratches(t, rng, 120, 0.1, horizontal=False)
    return grime(t, rng, 0.3)


def wood(rng):
    t = solid((0.4, 0.27, 0.16))
    rings = 0.06 * np.sin(XX * 0.25 + fbm(rng, ((4, 1),)) * 12)
    t = shade(t, rings + fbm(rng, ((3, 0.3), (80, 0.7)), aspect=(10, 1)) * 0.15)
    return grime(t, rng, 0.25)


def quilt(rng, color):
    """Gambeson: padded cloth with diagonal quilting seams."""
    t = cloth(rng, color)
    step = 28 * K
    seam = (np.abs(((XX + YY) % step) - step / 2) < 1.2) | (np.abs(((XX - YY) % step) - step / 2) < 1.2)
    t[seam] *= 0.6
    puff = 0.05 * np.cos((XX + YY) / step * 2 * np.pi) * np.cos((XX - YY) / step * 2 * np.pi)
    return shade(t, puff)


def rope(rng):
    t = solid((0.52, 0.43, 0.3))
    twist = 0.12 * np.sin((XX + YY * 0.6) * 0.35)
    return grime(shade(t, twist + fbm(rng) * 0.1), rng, 0.3)


def shield(rng):
    """Painted wooden shield face: dark red field with a pale cyclops-eye emblem."""
    t = plate(rng, (0.33, 0.1, 0.12), rivet=False)
    cx, cy = XX - TS / 2, YY - TS / 2
    r = np.sqrt((cx / 1.6) ** 2 + cy ** 2) / (TS / 2)
    t[(r < 0.42) & (r > 0.34)] = (0.7, 0.66, 0.6)
    t[r < 0.18] = (0.7, 0.66, 0.6)
    t = scratches(t, rng, 30, 0.12)
    t = veins(t, rng, count=3, strength=0.8)
    return rivets(t, mids=True)


def build_atlas(path, seed=3):
    rng = np.random.default_rng(seed)
    tiles = {
        "plate_dark": plate(rng, (0.16, 0.15, 0.19)),
        "plate_mid": plate(rng, (0.23, 0.22, 0.27)),
        "plate_trim": plate(rng, (0.36, 0.35, 0.41), rivet=False),
        "plate_corrupt": plate(rng, (0.16, 0.14, 0.2), corrupt=True),
        "plate_corrupt_heavy": veins(plate(rng, (0.14, 0.12, 0.18), corrupt=True), rng, 6, 3),
        "plate_rust": grime(shade(plate(rng, (0.3, 0.24, 0.2)), fbm(rng) * 0.2), rng, 0.4),
        "gold": bevel(scratches(shade(solid((0.62, 0.48, 0.2)), fbm(rng) * 0.2), rng), hi=0.25, lo=0.25),
        "leather": leather(rng, (0.38, 0.24, 0.15)),
        "leather_strap": leather(rng, (0.27, 0.17, 0.11)),
        "buckle": buckle(rng),
        "cloth": cloth(rng, (0.44, 0.13, 0.19)),
        "cloth_dark": cloth(rng, (0.28, 0.09, 0.13)),
        "cloth_brown": cloth(rng, (0.36, 0.27, 0.18)),
        "cloth_green": cloth(rng, (0.2, 0.26, 0.17)),
        "linen": cloth(rng, (0.6, 0.55, 0.45)),
        "pants": cloth(rng, (0.2, 0.18, 0.24)),
        "quilt": quilt(rng, (0.42, 0.36, 0.28)),
        "chainmail": chainmail(rng),
        "black": shade(solid((0.05, 0.045, 0.06)), fbm(rng) * 0.04),
        "blade": blade(rng),
        "blade_corrupt": blade(rng, corrupt=True),
        "iron": grime(scratches(shade(solid((0.3, 0.29, 0.31)), fbm(rng) * 0.2), rng), rng, 0.4),
        "horn": horn(rng),
        "glow": glow(rng),
        "body": shade(solid((0.1, 0.1, 0.11)), fbm(rng) * 0.05),
        "skin": skin(rng, (0.5, 0.48, 0.47)),
        "skin_corrupt": skin(rng, (0.47, 0.44, 0.46), level=0.6),
        "skin_king": skin(rng, (0.8, 0.7, 0.74), level=0.55, king=True),
        "hair": hair(rng),
        "eye": eye(rng),
        "fur": fur(rng, (0.4, 0.37, 0.36)),
        "fur_dark": fur(rng, (0.17, 0.15, 0.17)),
        "wood": wood(rng),
        "rope": rope(rng),
        "shield": shield(rng),
        "bone": grime(shade(solid((0.78, 0.74, 0.64)), fbm(rng) * 0.15), rng, 0.4),
    }
    assert set(tiles) == set(TILES), set(TILES) ^ set(tiles)
    atlas = np.zeros((ATLAS, ATLAS, 3), np.float32)
    for name, tile in tiles.items():
        i = TILES.index(name)
        col, row = i % GRID, i // GRID
        atlas[row * TS:(row + 1) * TS, col * TS:(col + 1) * TS] = tile
    Image.fromarray((np.clip(atlas, 0, 1) * 255).astype(np.uint8)).save(path)
    return path


if __name__ == "__main__":
    build_atlas("atlas_preview.png")

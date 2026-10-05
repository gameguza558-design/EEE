"""Hand-painted-style texture atlas for the One-Horn Cyclops, generated with numpy + Pillow.

The atlas is a 4x4 grid of 256 px tiles. Every face of the model is mapped onto the
whole tile of its material, so each tile is painted like a single armor plate: a
beveled edge, a dark seam, corner rivets, scratches and grime toward the bottom.
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

TS = 256  # tile size in px
GRID = 4
ATLAS = TS * GRID

TILES = [
    "plate_dark", "plate_mid", "plate_trim", "plate_corrupt",
    "leather", "leather_strap", "buckle", "cloth",
    "cloth_dark", "chainmail", "black", "blade",
    "blade_corrupt", "horn", "glow", "body",
]

PURPLE = np.array([0.72, 0.30, 1.0])
PURPLE_CORE = np.array([0.93, 0.80, 1.0])

YY, XX = np.mgrid[0:TS, 0:TS].astype(np.float32)


def tile_rect(name):
    """(u0, v0, size) of a tile in UV space (v up)."""
    i = TILES.index(name)
    col, row = i % GRID, i // GRID
    size = 1 / GRID
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


def rivets(tile, inset=22, r=7, mids=False):
    spots = [(inset, inset), (TS - inset, inset), (inset, TS - inset), (TS - inset, TS - inset)]
    if mids:
        spots += [(TS // 2, inset), (TS // 2, TS - inset)]
    for cx, cy in spots:
        dx, dy = XX - cx, YY - cy
        dist = np.sqrt(dx * dx + dy * dy)
        head = dist < r
        ring = (dist >= r) & (dist < r + 2.2)
        light = 0.62 + 0.3 * np.clip(-(dx + dy) / (r * 1.5), -1, 1)
        tile[head] = (np.array([0.55, 0.54, 0.6]) * light[head][:, None])
        tile[ring] *= 0.35
    return tile


def veins(tile, rng, count=5, width=2, glow_radius=6, strength=1.0):
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
    core = np.asarray(mask, np.float32) / 255
    glow = np.asarray(mask.filter(ImageFilter.GaussianBlur(glow_radius)), np.float32) / 255
    glow = np.clip(glow * 2.2, 0, 1) * strength
    tile = tile * (1 - glow[..., None] * 0.6) + PURPLE * glow[..., None] * 0.85
    tile = tile * (1 - core[..., None]) + PURPLE_CORE * core[..., None]
    return tile


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
        i = 14
        for k in range(i, TS - i, 14):
            d.line([(k, i), (k + 7, i)], fill=c, width=2)
            d.line([(k, TS - i), (k + 7, TS - i)], fill=c, width=2)
            d.line([(i, k), (i, k + 7)], fill=c, width=2)
            d.line([(TS - i, k), (TS - i, k + 7)], fill=c, width=2)
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
    step = 11
    for row in range(-1, TS // step + 2):
        off = (step // 2) if row % 2 else 0
        for col in range(-1, TS // step + 2):
            x, y = col * step + off, row * step
            d.ellipse([x - 6, y - 6, x + 6, y + 6], outline=(102, 100, 110), width=2)
            d.arc([x - 6, y - 6, x + 6, y + 6], 200, 290, fill=(160, 158, 170), width=2)
    t = np.asarray(img, np.float32) / 255
    t = shade(t, fbm(rng) * 0.1)
    return grime(t, rng, 0.45)


def blade(rng, corrupt=False):
    t = solid((0.66, 0.66, 0.71))
    t = shade(t, fbm(rng, ((2, 0.5), (64, 0.5)), aspect=(1, 32)) * 0.12)  # brushed lengthwise
    t = shade(t, fbm(rng) * 0.08)
    t = scratches(t, rng, 50, 0.12, horizontal=False)
    edge = np.clip(1 - np.minimum(XX, TS - 1 - XX) / 34, 0, 1)
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


def build_atlas(path, seed=3):
    rng = np.random.default_rng(seed)
    tiles = {
        "plate_dark": plate(rng, (0.16, 0.15, 0.19)),
        "plate_mid": plate(rng, (0.23, 0.22, 0.27)),
        "plate_trim": plate(rng, (0.36, 0.35, 0.41), rivet=False),
        "plate_corrupt": plate(rng, (0.16, 0.14, 0.2), corrupt=True),
        "leather": leather(rng, (0.38, 0.24, 0.15)),
        "leather_strap": leather(rng, (0.27, 0.17, 0.11)),
        "buckle": buckle(rng),
        "cloth": cloth(rng, (0.44, 0.13, 0.19)),
        "cloth_dark": cloth(rng, (0.28, 0.09, 0.13)),
        "chainmail": chainmail(rng),
        "black": shade(solid((0.05, 0.045, 0.06)), fbm(rng) * 0.04),
        "blade": blade(rng),
        "blade_corrupt": blade(rng, corrupt=True),
        "horn": horn(rng),
        "glow": glow(rng),
        "body": shade(solid((0.1, 0.1, 0.11)), fbm(rng) * 0.05),
    }
    atlas = np.zeros((ATLAS, ATLAS, 3), np.float32)
    for name, tile in tiles.items():
        i = TILES.index(name)
        col, row = i % GRID, i // GRID
        atlas[row * TS:(row + 1) * TS, col * TS:(col + 1) * TS] = tile
    Image.fromarray((np.clip(atlas, 0, 1) * 255).astype(np.uint8)).save(path)
    return path


if __name__ == "__main__":
    build_atlas("atlas_preview.png")

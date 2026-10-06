"""Painted armour detail for the sculpted knights (sculpt.py). The meshes are simple and
whole; this paints what makes them read as armour: polished metal gradients, plate seams
with a lit edge, rolled rims, rivets, engraving, gems and the glowing visor opening.

All coordinates are (u, v) on a part's face of the style2 template, v = 0 at the top.
"""
import math
import random

from PIL import Image, ImageDraw, ImageFilter

import style2
from style2 import FACES, Painter, face_rect

SIDES4 = ("front", "back", "left", "right")
LIMBS = [s + p for s in ("Left", "Right") for p in ("UpperArm", "LowerArm", "Hand", "UpperLeg", "LowerLeg", "Foot")]


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def px(p, part, face, u, v):
    return p.at(part, face, u, v)


def metal(p, part, face, base, light, dark, streak=0.35):
    """Polished plate: lit from above, darker toward the bottom, with a soft vertical
    highlight streak."""
    x0, y0, x1, y1 = face_rect(part, face)
    h = int(y1 - y0)
    for i in range(h + 1):
        t = i / max(1, h)
        c = mix(light, base, min(1.0, t * 2.2)) if t < 0.45 else mix(base, dark, (t - 0.45) / 0.55)
        p.d.line([(x0, y0 + i), (x1, y0 + i)], fill=c)
    if streak and face in SIDES4:
        soft(p, [(part, face, "ellipse", (streak, 0.45, 0.07, 0.5))], light, 0.5, blur=10)


def soft(p, shapes, color, strength, blur=6):
    mask = Image.new("L", p.img.size, 0)
    md = ImageDraw.Draw(mask)
    for part, face, kind, args in shapes:
        if kind == "poly":
            md.polygon([p.at(part, face, u, v) for u, v in args], fill=255)
        elif kind == "line":
            pts, w = args
            md.line([p.at(part, face, u, v) for u, v in pts], fill=255, width=w, joint="curve")
        else:
            cu, cv, ru, rv = args
            x0, y0, x1, y1 = face_rect(part, face)
            cx, cy = p.at(part, face, cu, cv)
            rx, ry = ru * (x1 - x0), rv * (y1 - y0)
            md.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(blur)).point(lambda x: int(x * strength))
    p.img = Image.composite(Image.new("RGB", p.img.size, color), p.img, mask)
    p.d = ImageDraw.Draw(p.img)


def seam(p, part, face, pts, dark, light, w=4):
    """A plate edge: a dark groove with a lit lip just below it (reads as an overlap)."""
    q = [px(p, part, face, u, v) for u, v in pts]
    p.d.line([(x, y + w * 0.8) for x, y in q], fill=light, width=max(2, w // 2 + 1), joint="curve")
    p.d.line(q, fill=dark, width=w, joint="curve")


def rim(p, part, face, pts, light, dark, w=7):
    """A rolled rim: a bright rounded band with a shadow line under it."""
    q = [px(p, part, face, u, v) for u, v in pts]
    p.d.line([(x, y + w * 0.75) for x, y in q], fill=dark, width=max(2, w // 2), joint="curve")
    p.d.line(q, fill=light, width=w, joint="curve")
    p.d.line([(x, y - w * 0.25) for x, y in q], fill=mix(light, (255, 255, 255), 0.5), width=max(1, w // 3),
             joint="curve")


def arc(u0, u1, v_edge, v_mid, n=10):
    return [(u0 + (u1 - u0) * i / (n - 1), v_edge + (v_mid - v_edge) * math.sin(math.pi * i / (n - 1))) for i in range(n)]


def rivet(p, part, face, u, v, r, dark, light):
    x, y = px(p, part, face, u, v)
    p.d.ellipse([x - r, y - r, x + r, y + r], fill=dark)
    p.d.ellipse([x - r * 0.7, y - r * 0.8, x + r * 0.3, y + r * 0.2], fill=light)


def gem(p, part, face, u, v, r, color, mount):
    x, y = px(p, part, face, u, v)
    p.d.ellipse([x - r * 1.45, y - r * 1.45, x + r * 1.45, y + r * 1.45], fill=mount, outline=mix(mount, (0, 0, 0), 0.5),
                width=3)
    p.d.ellipse([x - r, y - r, x + r, y + r], fill=mix(color, (0, 0, 0), 0.35))
    p.d.ellipse([x - r * 0.8, y - r * 0.85, x + r * 0.7, y + r * 0.6], fill=color)
    p.d.ellipse([x - r * 0.55, y - r * 0.65, x - r * 0.1, y - r * 0.2], fill=(240, 248, 255))


def filigree(p, part, face, cu, cv, s, color, w=3, mirror=True):
    """Engraved scrollwork: mirrored curls."""
    for sg in ((1, -1) if mirror else (1,)):
        pts = []
        for i in range(24):
            a = i / 23 * math.pi * 1.6
            r = s * (1 - i / 30)
            pts.append((cu + sg * (s * 0.4 + r * math.cos(a) * 0.6), cv + r * math.sin(a) * 0.5))
        p.line(part, face, pts, color, width=w)


def glow_line(p, part, face, pts, color, core, width=8, halo=16):
    q = [px(p, part, face, u, v) for u, v in pts]
    mask = Image.new("L", p.img.size, 0)
    ImageDraw.Draw(mask).line(q, fill=255, width=width + halo, joint="curve")
    mask = mask.filter(ImageFilter.GaussianBlur(halo / 2)).point(lambda x: int(x * 0.8))
    p.img = Image.composite(Image.new("RGB", p.img.size, color), p.img, mask)
    p.d = ImageDraw.Draw(p.img)
    p.d.line(q, fill=color, width=width, joint="curve")
    p.d.line(q, fill=core, width=max(2, width // 3), joint="curve")


def chainmail(p, part, face, v0, v1, base, ring):
    x0, y0, x1, y1 = face_rect(part, face)
    ya, yb = y0 + (y1 - y0) * v0, y0 + (y1 - y0) * v1
    p.d.rectangle([x0, ya, x1, yb], fill=base)
    step = 9
    for row, y in enumerate(range(int(ya), int(yb), step)):
        for x in range(int(x0) + (step // 2 if row % 2 else 0), int(x1), step):
            p.d.arc([x - 4, y - 4, x + 4, y + 4], 180, 360, fill=ring, width=2)


def outer_face(part):
    return "left" if part.startswith("Left") else "right"


def inner_face(part):
    return "right" if part.startswith("Left") else "left"


def outer_u(part, face):
    """u of the outer edge (away from the body) on the front/back faces of a limb."""
    left = part.startswith("Left")
    if face == "front":
        return 1.0 if left else 0.0
    return 0.0 if left else 1.0


# ---------------------------------------------------------------------------
def white_knight():
    """Silver knight: polished silver, rolled rims, a V visor glowing gold, the blue gem."""
    p = Painter(seed=61)
    S, L, D, G = (196, 201, 212), (246, 248, 252), (104, 110, 126), (60, 64, 78)
    gold, blue, black = (214, 174, 84), (40, 96, 225), (14, 14, 20)
    glow, core = (255, 206, 110), (255, 248, 225)
    for part in style2.PARTS:
        for f in FACES:
            metal(p, part, f, S, L, D, streak=0.32 if f in ("front", "back") else 0.5)

    H = "Head"
    # Visor: a V-shaped opening, its inside black with a gold glow along it.
    p.poly(H, "front", [(0.03, 0.31), (0.5, 0.5), (0.97, 0.31), (0.97, 0.41), (0.5, 0.61), (0.03, 0.41)], black)
    glow_line(p, H, "front", [(0.07, 0.36), (0.5, 0.555), (0.93, 0.36)], glow, core, width=9)
    seam(p, H, "front", [(0.0, 0.25), (0.5, 0.43), (1.0, 0.25)], G, L, w=5)  # brow of the visor
    rim(p, H, "front", [(0.03, 0.43), (0.5, 0.625), (0.97, 0.43)], L, D, w=6)
    seam(p, H, "front", [(0.5, 0.0), (0.5, 0.42)], G, L, w=4)
    seam(p, H, "front", [(0.5, 0.64), (0.5, 1.0)], G, L, w=4)
    for s in (1, -1):  # breathing slots raked along the V
        for k in range(4):
            v = 0.66 + 0.06 * k
            a = (0.5 + s * 0.12, v + 0.06)
            b = (0.5 + s * 0.36, v - 0.04)
            p.line(H, "front", [a, b], black, width=5)
    for k in range(3):
        rim(p, H, "front", [(0.0, 0.84 + 0.06 * k), (1.0, 0.84 + 0.06 * k)], L, D, w=5)
    for f in ("left", "right"):
        u = 0.32 if f == "left" else 0.68
        rivet(p, H, f, u, 0.36, 13, G, L)
        seam(p, H, f, [(u, 0.36), (0.0 if f == "left" else 1.0, 0.3)], G, L, w=4)
        seam(p, H, f, [(u, 0.36), (0.0 if f == "left" else 1.0, 0.48)], G, L, w=4)
        for k in range(3):
            rim(p, H, f, [(0.0, 0.84 + 0.06 * k), (1.0, 0.84 + 0.06 * k)], L, D, w=5)
    for k in range(3):
        rim(p, H, "back", [(0.0, 0.8 + 0.07 * k), (1.0, 0.8 + 0.07 * k)], L, D, w=5)
    seam(p, H, "back", [(0.5, 0.0), (0.5, 0.78)], G, L, w=4)
    seam(p, H, "top", [(0.5, 0.0), (0.5, 1.0)], G, L, w=5)
    filigree(p, H, "top", 0.5, 0.3, 0.18, gold, w=3)

    T = "UpperTorso"
    soft(p, [(T, "front", "ellipse", (0.32, 0.38, 0.16, 0.2)), (T, "front", "ellipse", (0.68, 0.38, 0.16, 0.2))], L, 0.6,
         blur=14)  # the full chest catching light
    rim(p, T, "front", [(0.22, 0.05), (0.5, 0.12), (0.78, 0.05)], L, D, w=7)  # collar
    rim(p, T, "front", [(0.12, 0.0), (0.5, 0.2), (0.88, 0.0)], L, D, w=6)
    for d in (0.0, 0.1):  # V plackart
        seam(p, T, "front", [(0.04 + d, 0.48 + d * 0.6), (0.5, 0.94), (0.96 - d, 0.48 + d * 0.6)], G, L, w=5)
    seam(p, T, "front", [(0.5, 0.2), (0.5, 0.94)], mix(S, D, 0.6), L, w=3)
    gem(p, T, "front", 0.7, 0.3, 17, blue, (210, 214, 222))
    filigree(p, T, "front", 0.7, 0.42, 0.08, mix(S, G, 0.6), w=2)
    for u in (0.08, 0.92):
        for k in range(4):
            rivet(p, T, "front", u, 0.12 + 0.11 * k, 6, G, L)
    rim(p, T, "front", [(0.0, 0.98), (1.0, 0.98)], L, D, w=7)
    seam(p, T, "back", [(0.5, 0.0), (0.5, 1.0)], G, L, w=5)
    for v in (0.68, 0.8, 0.92):
        rim(p, T, "back", [(0.0, v), (1.0, v)], L, D, w=6)
    rim(p, T, "back", [(0.15, 0.06), (0.85, 0.06)], L, D, w=7)
    for f in ("left", "right"):
        seam(p, T, f, [(0.5, 0.1), (0.5, 0.95)], G, L, w=4)
        rim(p, T, f, [(0.0, 0.98), (1.0, 0.98)], L, D, w=6)
    for f in ("top",):
        rim(p, T, f, [(0.3, 0.2), (0.7, 0.2)], L, D, w=6)

    LT = "LowerTorso"
    for f in SIDES4:
        for v in (0.15, 0.5, 0.85):
            rim(p, LT, f, [(0.0, v), (1.0, v)], L, D, w=7)
    p.box(LT, "front", 0.42, 0.25, 0.58, 0.75, (206, 210, 220), outline=G, width=3)
    rivet(p, LT, "front", 0.5, 0.5, 9, G, L)

    for part in LIMBS:
        k = part.replace("Left", "").replace("Right", "")
        of, inf = outer_face(part), inner_face(part)
        if k == "UpperArm":
            # Pauldron lames: arcs that bow down over the outside of the shoulder.
            for v in (0.33, 0.5, 0.66, 0.82):
                rim(p, part, of, arc(0.0, 1.0, v - 0.04, v + 0.03), L, D, w=8)
                for f in ("front", "back"):
                    ou = outer_u(part, f)
                    rim(p, part, f, [(1 - ou, v - 0.1), (ou, v - 0.02)], L, D, w=7)
            p.ellipse(part, "top", 0.5 + (0.12 if part.startswith("Left") else -0.12), 0.5, 0.3, 0.3, None, outline=G,
                      width=4)
            soft(p, [(part, "top", "ellipse", (0.5, 0.42, 0.22, 0.2))], L, 0.7, blur=10)
            chainmail(p, part, inf, 0.55, 1.0, (52, 54, 62), (150, 154, 166))
        elif k == "LowerArm":
            p.ellipse(part, "back", 0.5, 0.18, 0.28, 0.16, None, outline=G, width=4)  # couter
            rivet(p, part, "back", 0.5, 0.18, 8, G, L)
            for f in SIDES4:
                rim(p, part, f, [(0.0, 0.62), (1.0, 0.62)], L, D, w=6)  # cuff edge
                rim(p, part, f, [(0.0, 0.94), (1.0, 0.94)], L, D, w=7)
                seam(p, part, f, [(0.5, 0.05), (0.5, 0.58)], G, L, w=3)
        elif k == "Hand":
            for f in ("front", "back", "bottom"):
                for u in (0.25, 0.42, 0.58, 0.75):
                    seam(p, part, f, [(u, 0.1), (u, 0.95)], G, L, w=3)
            for u in (0.25, 0.42, 0.58, 0.75):
                rivet(p, part, "front", u, 0.3, 5, G, L)
        elif k == "UpperLeg":
            for f in SIDES4:  # tassets over the hip, cuisse, knee lames
                for v in (0.1, 0.26, 0.42):
                    rim(p, part, f, arc(0.0, 1.0, v, v + 0.03), L, D, w=6)
                for v in (0.82, 0.92):
                    rim(p, part, f, [(0.0, v), (1.0, v)], L, D, w=6)
            seam(p, part, "front", [(0.5, 0.45), (0.5, 0.8)], mix(S, D, 0.5), L, w=3)
        elif k == "LowerLeg":
            # Knee cop: a pointed shell with a rolled rim and a central ridge.
            seam(p, part, "front", [(0.18, 0.06), (0.5, 0.02), (0.82, 0.06), (0.7, 0.26), (0.5, 0.34), (0.3, 0.26),
                                    (0.18, 0.06)], G, L, w=5)
            seam(p, part, "front", [(0.5, 0.04), (0.5, 0.32)], mix(S, D, 0.5), L, w=3)
            soft(p, [(part, "front", "ellipse", (0.42, 0.14, 0.1, 0.06))], L, 0.8, blur=6)
            p.ellipse(part, of, 0.5, 0.2, 0.28, 0.13, None, outline=G, width=4)  # wing
            seam(p, part, "front", [(0.5, 0.34), (0.5, 0.95)], mix(S, D, 0.6), L, w=3)
            for f in SIDES4:
                rim(p, part, f, [(0.0, 0.34), (1.0, 0.34)], L, D, w=5)
                rim(p, part, f, [(0.0, 0.95), (1.0, 0.95)], L, D, w=6)
        elif k == "Foot":
            for v in (0.2, 0.4, 0.6, 0.8):
                rim(p, part, "top", arc(0.0, 1.0, v, v + 0.06), L, D, w=5)
            for f in SIDES4:
                rim(p, part, f, [(0.0, 0.25), (1.0, 0.25)], L, D, w=5)
                p.box(part, f, 0.0, 0.85, 1.0, 1.0, (60, 60, 66))
            seam(p, part, "front", [(0.5, 0.0), (0.5, 0.8)], G, L, w=3)
    p.shade(ink=False)
    return p


PAINTERS = {"white": white_knight}

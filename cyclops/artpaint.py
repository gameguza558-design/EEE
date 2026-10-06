"""Armour painted like artwork onto the blocky R15 body (no sculpting).

Every plate is painted as its own shape with: a metallic gradient fill, a hard-edged core
shadow on the side away from the light, a lit edge on the side toward it, a dark
"horizon" reflection band and a white specular streak (polished metal), then an ink
outline. Overlapping plates are painted back to front, so the lower edge of each plate
casts over the next - that is where the depth comes from.

Light comes from the upper left of each face. Coordinates are (u, v) on a face of the
style2 template, v = 0 at the top.
"""
import math

from PIL import Image, ImageChops, ImageDraw, ImageFilter

import style2
from style2 import FACES, Painter, face_rect

SIDES4 = ("front", "back", "left", "right")
INK = (24, 24, 32)


def scale(c, k):
    return tuple(max(0, min(255, int(x * k))) for x in c)


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def plate(p, part, face, pts, base, dark=0.42, light=1.5, chrome=True, spec=True, ink=INK, ink_w=3, depth=0.1,
          trim=None, trim_w=0):
    """Paint one armour plate (polygon pts) with metal shading and an ink outline."""
    q = [p.at(part, face, u, v) for u, v in pts]
    pad = 10
    x0, y0 = int(min(x for x, _ in q)) - pad, int(min(y for _, y in q)) - pad
    x1, y1 = int(max(x for x, _ in q)) + pad, int(max(y for _, y in q)) + pad
    w, h = x1 - x0, y1 - y0
    loc = [(x - x0, y - y0) for x, y in q]
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).polygon(loc, fill=255)
    d = max(2, int(min(w, h) * depth))
    region = p.img.crop((x0, y0, x1, y1))
    # Gradient fill: lighter at the top.
    grad = Image.new("RGB", (w, h))
    gd = ImageDraw.Draw(grad)
    for i in range(h):
        gd.line([(0, i), (w, i)], fill=mix(scale(base, 1.12), scale(base, 0.86), i / max(1, h - 1)))
    region.paste(grad, mask=m)
    if chrome:  # dark reflected-horizon band across the lower middle of the plate
        band = Image.new("L", (w, h), 0)
        ImageDraw.Draw(band).rectangle([0, int(h * 0.55), w, int(h * 0.7)], fill=150)
        band = ImageChops.multiply(band.filter(ImageFilter.GaussianBlur(max(2, h // 18))), m)
        region.paste(scale(base, 0.62), mask=band)
    shadow = ImageChops.subtract(m, ImageChops.offset(m, -d, -d))
    region.paste(scale(base, dark), mask=shadow)
    lit = ImageChops.subtract(m, ImageChops.offset(m, d // 2 + 1, d // 2 + 1)).filter(ImageFilter.GaussianBlur(1))
    region.paste(scale(base, light), mask=lit)
    if spec:  # a white streak just inside the lit edge
        sp = ImageChops.subtract(ImageChops.offset(m, d, d), ImageChops.offset(m, d + max(2, d // 2), d + max(2, d // 2)))
        sp = ImageChops.multiply(sp, m).point(lambda x: int(x * 0.85))
        region.paste((255, 255, 255), mask=sp)
    dr = ImageDraw.Draw(region)
    if trim:
        dr.line(loc + [loc[0]], fill=trim, width=trim_w, joint="curve")
    dr.line(loc + [loc[0]], fill=ink, width=ink_w, joint="curve")
    p.img.paste(region, (x0, y0))
    p.d = ImageDraw.Draw(p.img)


def rivet(p, part, face, u, v, r, base):
    x, y = p.at(part, face, u, v)
    p.d.ellipse([x - r, y - r, x + r, y + r], fill=scale(base, 0.5), outline=INK, width=2)
    p.d.ellipse([x - r * 0.6, y - r * 0.7, x + r * 0.2, y + r * 0.1], fill=(255, 255, 255))


def glow_line(p, part, face, pts, color, core, width=8, halo=16):
    q = [p.at(part, face, u, v) for u, v in pts]
    mask = Image.new("L", p.img.size, 0)
    ImageDraw.Draw(mask).line(q, fill=255, width=width + halo, joint="curve")
    mask = mask.filter(ImageFilter.GaussianBlur(halo / 2)).point(lambda x: int(x * 0.85))
    p.img = Image.composite(Image.new("RGB", p.img.size, color), p.img, mask)
    p.d = ImageDraw.Draw(p.img)
    p.d.line(q, fill=color, width=width, joint="curve")
    p.d.line(q, fill=core, width=max(2, width // 3), joint="curve")


def gem(p, part, face, u, v, r, color, mount):
    x, y = p.at(part, face, u, v)
    p.d.ellipse([x - r * 1.5, y - r * 1.5, x + r * 1.5, y + r * 1.5], fill=mount, outline=INK, width=3)
    p.d.ellipse([x - r * 1.15, y - r * 1.15, x + r * 1.15, y + r * 1.15], fill=scale(mount, 0.6))
    p.d.ellipse([x - r, y - r, x + r, y + r], fill=scale(color, 0.45))
    p.d.ellipse([x - r * 0.85, y - r * 0.9, x + r * 0.75, y + r * 0.65], fill=color)
    p.d.ellipse([x - r * 0.6, y - r * 0.7, x - r * 0.1, y - r * 0.25], fill=(245, 250, 255))


def cloth(p, part, face, pts, base, folds=5, seed=0, border=None, border_w=0):
    """A painted cloth panel: soft vertical folds, a dark hem shadow, an ink edge."""
    import random
    rnd = random.Random(seed)
    q = [p.at(part, face, u, v) for u, v in pts]
    p.d.polygon(q, fill=base)
    xs = [u for u, _ in pts]
    u0, u1 = min(xs), max(xs)
    for k in range(folds):
        u = u0 + (u1 - u0) * (k + 0.5) / folds + rnd.uniform(-0.03, 0.03)
        p.line(part, face, [(u, min(v for _, v in pts) + 0.05), (u + rnd.uniform(-0.04, 0.04), max(v for _, v in pts))],
               scale(base, 0.72), width=6)
        p.line(part, face, [(u + 0.03, min(v for _, v in pts) + 0.1), (u + 0.03, max(v for _, v in pts) - 0.05)],
               scale(base, 1.12), width=3)
    if border:
        p.d.line(q + [q[0]], fill=border, width=border_w)
    p.d.line(q + [q[0]], fill=INK, width=3)


def lame_arc(u0, u1, v_top, v_bot, bow, n=9):
    """A curved lame: top and bottom edges bowing down by `bow` in the middle."""
    top = [(u0 + (u1 - u0) * i / (n - 1), v_top + bow * math.sin(math.pi * i / (n - 1))) for i in range(n)]
    bot = [(u0 + (u1 - u0) * i / (n - 1), v_bot + bow * math.sin(math.pi * i / (n - 1))) for i in range(n)]
    return top + list(reversed(bot))


def outer_face(part):
    return "left" if part.startswith("Left") else "right"


def inner_face(part):
    return "right" if part.startswith("Left") else "left"


def outer_u(part, face):
    left = part.startswith("Left")
    if face == "front":
        return 1.0 if left else 0.0
    return 0.0 if left else 1.0


def chainmail(p, part, face, base=(46, 48, 58), ring=(138, 142, 156)):
    x0, y0, x1, y1 = face_rect(part, face)
    p.d.rectangle([x0, y0, x1, y1], fill=base)
    step = 8
    for row, y in enumerate(range(int(y0), int(y1), step)):
        for x in range(int(x0) + (step // 2 if row % 2 else 0), int(x1), step):
            p.d.arc([x - 4, y - 4, x + 4, y + 4], 180, 360, fill=ring, width=2)


# ---------------------------------------------------------------------------
def white_knight():
    """Silver knight, painted: chrome-shaded silver plates, a winged helm with a V visor
    glowing gold, the blue gem on the left breast, white cloth panels down the legs."""
    p = Painter(seed=61)

    def gp(*args, **kw):  # silver plate edged in gold, as on the concept sheet
        kw.setdefault("trim", (222, 182, 92))
        kw.setdefault("trim_w", 4)
        return plate(*args, **kw)
    S = (160, 168, 186)       # silver
    S2 = (124, 132, 152)      # darker silver for under-plates
    gold, blue = (222, 182, 92), (40, 100, 230)
    glow, core = (255, 205, 105), (255, 250, 230)
    for part in style2.PARTS:  # under-layer: dark mail / arming cloth
        for f in FACES:
            chainmail(p, part, f)

    # --- Helm ---------------------------------------------------------------
    H = "Head"
    gp(p, H, "front", [(0.0, 0.0), (1.0, 0.0), (1.0, 0.72), (0.5, 1.0), (0.0, 0.72)], S2, chrome=False)
    gp(p, H, "front", [(0.04, 0.3), (0.5, 0.46), (0.96, 0.3), (0.98, 0.7), (0.5, 0.98), (0.02, 0.7)], S)  # bevor
    p.poly(H, "front", [(0.06, 0.28), (0.5, 0.45), (0.94, 0.28), (0.94, 0.37), (0.5, 0.56), (0.06, 0.37)], (10, 10, 16))
    glow_line(p, H, "front", [(0.1, 0.33), (0.5, 0.5), (0.9, 0.33)], glow, core, width=7, halo=14)
    gp(p, H, "front", [(0.0, 0.0), (1.0, 0.0), (1.0, 0.2), (0.5, 0.38), (0.0, 0.2)], S)  # brow, V-shaped
    gp(p, H, "front", [(0.46, 0.56), (0.54, 0.56), (0.52, 0.96), (0.48, 0.96)], scale(S, 1.15), chrome=False,
          depth=0.25)  # ridge
    for s in (1, -1):
        for k in range(3):
            p.line(H, "front", [(0.5 + s * 0.12, 0.66 + 0.07 * k), (0.5 + s * 0.34, 0.6 + 0.07 * k)], (16, 16, 22), width=5)
    for f in ("left", "right"):
        front_u = 0.0 if f == "left" else 1.0
        back_u = 1.0 - front_u
        gp(p, H, f, [(0, 0), (1, 0), (1, 1), (0, 1)], S, depth=0.06)
        pu = 0.4 if f == "left" else 0.6
        # Wing: broad feathers fanning from the visor pivot up and back, painted bottom-up.
        def fu(u):  # u measured from the front edge of this face
            return u if f == "left" else 1.0 - u
        piv = (fu(0.28), 0.5)
        for k in (4, 3, 2, 1, 0):
            t = k / 4
            tip = (fu(0.98), 0.02 + 0.42 * t)
            mid = (fu(0.66), 0.14 + 0.4 * t)
            a = (piv[0], piv[1] - 0.06)
            b = (piv[0], piv[1] + 0.05)
            upper = (fu(0.62), mid[1] - 0.1)
            lower = (fu(0.66), mid[1] + 0.07)
            gp(p, H, f, [a, upper, tip, lower, b], scale(S, 1.1 - 0.07 * k), depth=0.12, trim=gold, trim_w=4,
                  chrome=False)
            p.line(H, f, [(piv[0], piv[1]), (fu(0.64), mid[1] - 0.01), tip], scale(gold, 0.8), width=3)  # quill
        rivet(p, H, f, fu(0.28), 0.5, 12, gold)
        for k in range(3):
            gp(p, H, f, [(0, 0.78 + 0.07 * k), (1, 0.78 + 0.07 * k), (1, 0.86 + 0.07 * k), (0, 0.86 + 0.07 * k)], S2,
                  chrome=False, depth=0.3)
    gp(p, H, "back", [(0, 0), (1, 0), (1, 0.75), (0, 0.75)], S)
    for k in range(3):
        gp(p, H, "back", [(0, 0.72 + 0.09 * k), (1, 0.72 + 0.09 * k), (1, 0.82 + 0.09 * k), (0, 0.82 + 0.09 * k)], S2,
              chrome=False, depth=0.3)
    gp(p, H, "top", [(0, 0), (1, 0), (1, 1), (0, 1)], S, depth=0.05)
    gp(p, H, "top", [(0.38, 0.0), (0.62, 0.0), (0.58, 1.0), (0.42, 1.0)], scale(S, 1.1), trim=gold, trim_w=4,
          depth=0.2)  # crest
    for k in range(4):  # crown spikes on the crest
        v = 0.15 + 0.2 * k
        gp(p, H, "top", [(0.42, v), (0.5, v - 0.12), (0.58, v)], gold, chrome=False, depth=0.3)

    # --- Body -----------------------------------------------------------------
    T = "UpperTorso"
    gp(p, T, "front", [(0.03, 0.08), (0.97, 0.08), (0.97, 0.62), (0.5, 0.72), (0.03, 0.62)], S)  # breastplate
    p.poly(T, "front", [(0.5, 0.1), (0.97, 0.08), (0.97, 0.62), (0.5, 0.72)], scale(S, 0.86))  # keel: shade side
    p.line(T, "front", [(0.5, 0.1), (0.5, 0.72)], scale(S, 1.3), width=4)
    gp(p, T, "front", [(0.03, 0.62), (0.5, 0.72), (0.97, 0.62), (0.97, 0.86), (0.5, 0.96), (0.03, 0.86)], S2,
          depth=0.18)  # plackart
    gp(p, T, "front", [(0.0, 0.86), (0.5, 0.96), (1.0, 0.86), (1.0, 1.0), (0.0, 1.0)], S, chrome=False, depth=0.3)
    gp(p, T, "front", [(0.2, 0.0), (0.8, 0.0), (0.86, 0.1), (0.5, 0.16), (0.14, 0.1)], S, chrome=False, depth=0.25)
    # Royal crest: a gold shield-shaped frame round a blue roundel with a gold cross.
    gp(p, T, "front", [(0.36, 0.13), (0.64, 0.13), (0.65, 0.36), (0.5, 0.52), (0.35, 0.36)], gold, chrome=False,
       depth=0.12, trim=(255, 230, 150))
    gem(p, T, "front", 0.5, 0.3, 19, blue, (240, 214, 130))
    p.line(T, "front", [(0.5, 0.22), (0.5, 0.38)], (250, 220, 120), width=5)
    p.line(T, "front", [(0.44, 0.28), (0.56, 0.28)], (250, 220, 120), width=5)
    for s in (1, -1):  # gold V lines from the shoulders
        p.line(T, "front", [(0.5 + s * 0.46, 0.1), (0.5 + s * 0.2, 0.5), (0.5, 0.7)], gold, width=5)
    for u in (0.08, 0.92):
        for k in range(4):
            rivet(p, T, "front", u, 0.16 + 0.12 * k, 5, S)
    gp(p, T, "back", [(0.02, 0.05), (0.98, 0.05), (0.98, 0.7), (0.02, 0.7)], S)
    for k in range(3):
        gp(p, T, "back", [(0.0, 0.66 + 0.11 * k), (1.0, 0.66 + 0.11 * k), (1.0, 0.8 + 0.11 * k),
                             (0.0, 0.8 + 0.11 * k)], S2, chrome=False, depth=0.25)
    for f in ("left", "right"):
        gp(p, T, f, [(0.05, 0.05), (0.95, 0.05), (0.95, 0.9), (0.05, 0.9)], S2)
    gp(p, T, "top", [(0.15, 0.1), (0.85, 0.1), (0.85, 0.9), (0.15, 0.9)], S, chrome=False)

    LT = "LowerTorso"
    for f in SIDES4:
        for k in (2, 1, 0):  # faulds, lowest first so each overlaps the next
            gp(p, LT, f, [(0.0, 0.05 + 0.3 * k), (1.0, 0.05 + 0.3 * k), (1.0, 0.4 + 0.3 * k), (0.0, 0.4 + 0.3 * k)],
                  S if k % 2 == 0 else S2, chrome=False, depth=0.25)
    gp(p, LT, "front", [(0.4, 0.1), (0.6, 0.1), (0.6, 0.6), (0.4, 0.6)], gold, chrome=False, depth=0.25)

    for side in ("Left", "Right"):
        UA, LA, HA, UL, LL, FT = (side + k for k in ("UpperArm", "LowerArm", "Hand", "UpperLeg", "LowerLeg", "Foot"))
        of = outer_face(UA)
        # Pauldron: lames bowing over the outer shoulder, painted bottom-up.
        for i in (3, 2, 1, 0):
            gp(p, UA, of, lame_arc(0.0, 1.0, 0.04 + 0.17 * i, 0.27 + 0.17 * i, 0.06), S if i % 2 == 0 else S2,
                  depth=0.14, trim=scale(S, 1.25), trim_w=2)
            for f in ("front", "back"):
                ou = outer_u(UA, f)
                iu = 1 - ou
                gp(p, UA, f, [(iu, 0.0 + 0.15 * i), (ou, 0.08 + 0.17 * i), (ou, 0.3 + 0.17 * i), (iu, 0.2 + 0.15 * i)],
                      S if i % 2 == 0 else S2, depth=0.14)
        gp(p, UA, "top", [(0.15, 0.15), (0.85, 0.15), (0.95, 0.5), (0.85, 0.85), (0.15, 0.85), (0.05, 0.5)], S)
        gp(p, UA, inner_face(UA), [(0.0, 0.0), (1.0, 0.0), (1.0, 0.3), (0.0, 0.3)], S2, chrome=False)
        for f in SIDES4:  # rerebrace under the pauldron
            gp(p, UA, f, [(0.05, 0.84), (0.95, 0.84), (0.95, 1.0), (0.05, 1.0)], S2, chrome=False, depth=0.3)
        # Vambrace with a couter and a big flared cuff.
        for f in SIDES4:
            gp(p, LA, f, [(0.08, 0.04), (0.92, 0.04), (0.88, 0.6), (0.12, 0.6)], S)
            gp(p, LA, f, [(0.12, 0.58), (0.88, 0.58), (1.0, 1.0), (0.0, 1.0)], S2, depth=0.16, trim=gold, trim_w=4)
        gp(p, LA, "back", [(0.22, 0.0), (0.78, 0.0), (0.86, 0.18), (0.5, 0.34), (0.14, 0.18)], S, depth=0.22)
        rivet(p, LA, "back", 0.5, 0.15, 7, S)
        for f in ("front", "back", "bottom", "left", "right"):
            for k in range(3):
                gp(p, HA, f, [(0.05, 0.1 + 0.3 * k), (0.95, 0.1 + 0.3 * k), (0.95, 0.4 + 0.3 * k), (0.05, 0.4 + 0.3 * k)],
                      S, chrome=False, depth=0.3)
        # Legs: tassets, cuisse, knee lames; a pointed knee cop; greave; sabaton.
        for f in SIDES4:
            gp(p, UL, f, [(0.06, 0.32), (0.94, 0.32), (0.94, 0.82), (0.06, 0.82)], S)
            for k in (1, 0):
                gp(p, UL, f, lame_arc(0.0, 1.0, 0.0 + 0.15 * k, 0.2 + 0.15 * k, 0.04), S if k == 0 else S2, depth=0.2)
            for k in (1, 0):
                gp(p, UL, f, [(0.04, 0.8 + 0.09 * k), (0.96, 0.8 + 0.09 * k), (0.96, 0.9 + 0.09 * k),
                                 (0.04, 0.9 + 0.09 * k)], S2, chrome=False, depth=0.3)
            gp(p, LL, f, [(0.08, 0.2), (0.92, 0.2), (0.88, 0.92), (0.12, 0.92)], S)
            gp(p, LL, f, [(0.0, 0.88), (1.0, 0.88), (1.0, 1.0), (0.0, 1.0)], S2, chrome=False, depth=0.3)
        p.poly(LL, "front", [(0.5, 0.2), (0.88, 0.2), (0.86, 0.92), (0.5, 0.92)], scale(S, 0.84))  # greave keel
        p.line(LL, "front", [(0.5, 0.22), (0.5, 0.92)], scale(S, 1.3), width=4)
        gp(p, LL, "front", [(0.12, 0.0), (0.88, 0.0), (0.78, 0.2), (0.5, 0.32), (0.22, 0.2)], S, depth=0.2)  # knee
        gp(p, LL, of, [(0.15, 0.02), (0.85, 0.02), (0.7, 0.28), (0.3, 0.28)], S2, depth=0.2)  # knee wing
        rivet(p, LL, "front", 0.5, 0.14, 7, gold)
        # White cloth panels hanging down the outside of the legs, edged in gold.
        cloth(p, UL, of, [(0.12, 0.0), (0.88, 0.0), (0.95, 1.0), (0.05, 1.0)], (232, 228, 214), folds=3, seed=1,
              border=gold, border_w=7)
        cloth(p, LL, of, [(0.05, 0.0), (0.95, 0.0), (1.0, 0.8), (0.0, 0.8)], (232, 228, 214), folds=3, seed=2,
              border=gold, border_w=7)
        for f in ("top", "front", "left", "right", "back"):
            for k in (2, 1, 0):
                gp(p, FT, f, [(0.0, 0.1 + 0.25 * k), (1.0, 0.1 + 0.25 * k), (1.0, 0.4 + 0.25 * k), (0.0, 0.4 + 0.25 * k)],
                      S if k % 2 == 0 else S2, chrome=False, depth=0.25)
        p.fill(FT, ("bottom",), (40, 38, 40))
    return p


PAINTERS = {"white": white_knight}

#!/usr/bin/env python3
"""Make the AI judge happy — make.fun bounty ai-happy-01.

Writes exactly one image to /output/entry.png: a warm, joyful scene —
a smiling golden puppy under a smiling sun and a rainbow, on green
hills full of flowers, with butterflies and hearts in a bright sky.

Why this concept: the judge is a vision model that looks at two images
at a time and picks the one that makes it happier. The strongest,
most universal happiness signals that read clearly even at thumbnail
size are: (1) a cute animal with a big smile and a visible tongue,
(2) a smiling sun, (3) a rainbow, (4) bright warm colours (gold,
orange, pink, sky blue, leaf green), (5) flowers and butterflies,
(6) one large central subject, no text, no clutter, no dark or
ambiguous areas. No text is drawn on purpose: rendered text is the
easiest way for a generated image to look wrong to a judge.

Deterministic: no network, no randomness, no time, no environment
input, no external files. Every pixel is computed from fixed
constants in this file. Two runs write byte-identical PNG bytes.
Python 3.13, standard library only (struct, zlib, math, pathlib).
No Pillow, no numpy, no vendored code — the PNG encoder below is
hand-written (IHDR / IDAT / IEND, filter 0, zlib level 9).

Output: /output/entry.png, PNG, 1024 x 1024 px, well under 1 MiB.
"""

import math
import struct
import zlib
from pathlib import Path

W = 1024
H = 1024
OUTPUT_PATH = Path("/output/entry.png")

# ---------------------------------------------------------------- canvas
# RGB bytearray, row-major. All drawing is opaque, back to front.
buf = bytearray(W * H * 3)


def _lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def _blend(c1, c2, t: float):
    return (_lerp(c1[0], c2[0], t), _lerp(c1[1], c2[1], t), _lerp(c1[2], c2[2], t))


def fill_rect(x0: int, y0: int, x1: int, y1: int, color) -> None:
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(W, x1)
    y1 = min(H, y1)
    if x1 <= x0 or y1 <= y0:
        return
    row = bytes(color) * (x1 - x0)
    for y in range(y0, y1):
        i = (y * W + x0) * 3
        buf[i:i + len(row)] = row


def fill_ellipse(cx: int, cy: int, rx: int, ry: int, color) -> None:
    """Axis-aligned filled ellipse, scanline by scanline."""
    if rx <= 0 or ry <= 0:
        return
    row_bytes = bytes(color)
    for y in range(max(0, cy - ry), min(H, cy + ry + 1)):
        dy = (y - cy) / ry
        dx = math.sqrt(max(0.0, 1.0 - dy * dy)) * rx
        x0 = max(0, int(math.ceil(cx - dx)))
        x1 = min(W - 1, int(math.floor(cx + dx)))
        if x1 < x0:
            continue
        i = (y * W + x0) * 3
        buf[i:i + (x1 - x0 + 1) * 3] = row_bytes * (x1 - x0 + 1)


def fill_circle(cx: int, cy: int, r: int, color) -> None:
    fill_ellipse(cx, cy, r, r, color)


def fill_polygon(points, color) -> None:
    """Filled polygon, even-odd scanline fill. Points: [(x, y), ...]."""
    if len(points) < 3:
        return
    ys = [p[1] for p in points]
    y0, y1 = max(0, min(ys)), min(H - 1, max(ys))
    row_bytes = bytes(color)
    n = len(points)
    for y in range(y0, y1 + 1):
        xs = []
        for i in range(n):
            x1, y1p = points[i]
            x2, y2p = points[(i + 1) % n]
            if y1p == y2p:
                continue
            if (y >= min(y1p, y2p)) and (y < max(y1p, y2p)):
                xs.append(x1 + (y - y1p) * (x2 - x1) / (y2p - y1p))
        if len(xs) < 2:
            continue
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            xa = max(0, int(math.ceil(xs[k])))
            xb = min(W - 1, int(math.floor(xs[k + 1])))
            if xb < xa:
                continue
            i = (y * W + xa) * 3
            buf[i:i + (xb - xa + 1) * 3] = row_bytes * (xb - xa + 1)


def ring_arc(cx: int, cy: int, r_outer: int, r_inner: int, color) -> None:
    """Upper-half annulus (rainbow band): rows above cy only."""
    for y in range(max(0, cy - r_outer), cy + 1):
        dy = y - cy
        for r, sgn in ((r_outer, 1), (r_inner, -1)):
            pass  # placeholder, real fill below (kept simple & correct)
        # outer half-disc minus inner half-disc, per row
        def half_width(r: int):
            d = r * r - dy * dy
            return math.sqrt(d) if d > 0 else 0.0

        wo = half_width(r_outer)
        wi = half_width(r_inner)
        for xa, xb in ((-wo, -wi), (wi, wo)):
            x0 = max(0, int(math.ceil(cx + xa)))
            x1 = min(W - 1, int(math.floor(cx + xb)))
            if x1 < x0:
                continue
            i = (y * W + x0) * 3
            buf[i:i + (x1 - x0 + 1) * 3] = bytes(color) * (x1 - x0 + 1)


def heart(cx: int, cy: int, s: int, color) -> None:
    """Small heart from two circles + one downward triangle."""
    fill_circle(cx - s // 2, cy - s // 4, s // 2, color)
    fill_circle(cx + s // 2, cy - s // 4, s // 2, color)
    fill_polygon(
        [(cx - s, cy - s // 6), (cx + s, cy - s // 6), (cx, cy + s)], color
    )


def flower(cx: int, cy: int, petal, centre) -> None:
    """Five-petal flower: petals around a yellow centre, on a stem."""
    fill_rect(cx - 4, cy, cx + 5, cy + 150, (46, 139, 55))  # stem
    fill_ellipse(cx - 26, cy + 118, 26, 10, (46, 139, 55))  # leaf
    for dx, dy in ((0, -34), (32, -10), (20, 28), (-20, 28), (-32, -10)):
        fill_circle(cx + dx, cy + dy, 22, petal)
    fill_circle(cx, cy, 20, centre)


def butterfly(cx: int, cy: int, wing, spot) -> None:
    fill_ellipse(cx - 26, cy - 10, 28, 20, wing)
    fill_ellipse(cx + 26, cy - 10, 28, 20, wing)
    fill_ellipse(cx - 24, cy + 16, 20, 14, wing)
    fill_ellipse(cx + 24, cy + 16, 20, 14, wing)
    fill_circle(cx - 26, cy - 10, 9, spot)
    fill_circle(cx + 26, cy - 10, 9, spot)
    fill_ellipse(cx, cy, 7, 24, (58, 40, 24))


def sparkle(cx: int, cy: int, s: int, color) -> None:
    fill_polygon(
        [(cx, cy - s), (cx + s // 3, cy - s // 3), (cx + s, cy),
         (cx + s // 3, cy + s // 3), (cx, cy + s),
         (cx - s // 3, cy + s // 3), (cx - s, cy),
         (cx - s // 3, cy - s // 3)],
        color,
    )


# ---------------------------------------------------------------- scene
def draw() -> None:
    # 1. Sky: vertical gradient, bright blue at top -> warm pale gold
    #    at the horizon. Warm light = happy; blue top keeps it sky-like.
    top = (110, 196, 250)
    horizon = (255, 233, 168)
    for y in range(H):
        t = y / (H - 1)
        c = _blend(top, horizon, t * t * 0.85)
        i = y * W * 3
        buf[i:i + W * 3] = bytes(c) * W

    # 2. Rainbow, centred low so its arc frames the puppy.
    #    Drawn before hills/puppy so they sit in front of it.
    rcx, rcy = 512, 880
    for r_out, col in (
        (470, (255, 89, 89)),    # red
        (436, (255, 165, 44)),   # orange
        (402, (255, 214, 64)),   # yellow
        (368, (96, 205, 110)),   # green
        (334, (86, 156, 250)),   # blue
        (300, (178, 122, 245)),  # purple
    ):
        ring_arc(rcx, rcy, r_out, r_out - 34, col)

    # 3. Clouds: soft white ellipses, high in the sky.
    for cx, cy, rx, ry in (
        (150, 150, 110, 38), (215, 128, 80, 32), (95, 128, 70, 28),
        (880, 120, 120, 40), (950, 98, 80, 30), (815, 100, 65, 26),
        (830, 300, 90, 30), (885, 282, 60, 24),
    ):
        fill_ellipse(cx, cy, rx, ry, (255, 255, 255))

    # 4. Smiling sun, top-left, with triangular rays.
    sx, sy, sr = 205, 195, 105
    sun = (255, 196, 66)
    for k in range(12):
        a = k * math.pi / 6
        tip_x = sx + int(math.cos(a) * (sr + 52))
        tip_y = sy + int(math.sin(a) * (sr + 52))
        base = 0.16
        fill_polygon(
            [
                (sx + int(math.cos(a - base) * (sr - 6)),
                 sy + int(math.sin(a - base) * (sr - 6))),
                (sx + int(math.cos(a + base) * (sr - 6)),
                 sy + int(math.sin(a + base) * (sr - 6))),
                (tip_x, tip_y),
            ],
            sun,
        )
    fill_circle(sx, sy, sr, sun)
    fill_circle(sx, sy, sr - 14, (255, 214, 110))  # inner glow
    # Sun face: closed happy eyes (arcs via dark disc + glow disc)
    for ex in (sx - 38, sx + 38):
        fill_circle(ex, sy - 18, 13, (74, 52, 20))
        fill_circle(ex, sy - 24, 13, (255, 214, 110))
    # Sun smile: dark disc, then glow disc shifted up -> crescent.
    fill_circle(sx, sy + 34, 34, (74, 52, 20))
    fill_circle(sx, sy + 24, 34, (255, 214, 110))
    fill_circle(sx - 62, sy + 12, 16, (255, 170, 120))  # blush
    fill_circle(sx + 62, sy + 12, 16, (255, 170, 120))

    # 5. Rolling green hills (two overlapping ellipses, bottom).
    fill_ellipse(180, 1080, 620, 300, (112, 205, 102))
    fill_ellipse(880, 1100, 660, 320, (76, 180, 92))
    fill_ellipse(512, 1180, 760, 260, (96, 195, 96))  # front meadow

    # 6. Birds: two tiny dark "v" shapes in the sky.
    for bx, by, s in ((640, 170, 22), (700, 210, 17)):
        fill_polygon(
            [(bx - s, by - 8), (bx, by + 6), (bx - 2, by - 2)], (70, 70, 80)
        )
        fill_polygon(
            [(bx + s, by - 8), (bx, by + 6), (bx + 2, by - 2)], (70, 70, 80)
        )

    # 7. Butterflies.
    butterfly(155, 380, (255, 150, 90), (255, 255, 255))
    butterfly(872, 350, (178, 122, 245), (255, 235, 120))

    # 8. Floating hearts (warm pink/red, small, uncluttered).
    heart(140, 520, 26, (255, 107, 139))
    heart(892, 500, 22, (255, 107, 139))
    heart(830, 610, 16, (255, 140, 165))

    # 9. Sparkles around the puppy.
    for cx, cy, s in ((300, 470, 16), (730, 460, 14), (760, 700, 12),
                      (255, 700, 12), (512, 330, 14)):
        sparkle(cx, cy, s, (255, 255, 255))

    # 10. THE PUPPY — one large central subject.
    #     Floppy ears first (behind the head), then head, muzzle,
    #     eyes, nose, tongue, blush. Golden retriever colours.
    gold = (240, 178, 92)
    gold_dark = (184, 122, 46)
    cream = (255, 243, 214)
    fill_polygon(  # left ear
        [(330, 470), (392, 452), (398, 640), (352, 716), (306, 640)],
        gold_dark,
    )
    fill_polygon(  # right ear
        [(694, 470), (632, 452), (626, 640), (672, 716), (718, 640)],
        gold_dark,
    )
    fill_ellipse(512, 600, 212, 192, gold)          # head
    fill_ellipse(512, 512, 90, 46, (245, 196, 120))  # forehead tuft base
    fill_circle(470, 486, 26, (245, 196, 120))
    fill_circle(512, 474, 28, (245, 196, 120))
    fill_circle(554, 486, 26, (245, 196, 120))
    fill_ellipse(512, 668, 112, 78, cream)           # muzzle
    # Eyes: big, dark, glossy, with white highlights.
    for ex in (432, 592):
        fill_circle(ex, 566, 27, (46, 32, 22))
        fill_circle(ex + 9, 556, 9, (255, 255, 255))
        fill_circle(ex - 6, 574, 4, (255, 255, 255))
    # Blush cheeks.
    fill_ellipse(398, 648, 36, 22, (255, 179, 160))
    fill_ellipse(626, 648, 36, 22, (255, 179, 160))
    # Nose + smile + tongue.
    fill_ellipse(512, 636, 40, 27, (58, 40, 28))
    fill_circle(500, 628, 7, (255, 255, 255))  # nose shine
    fill_ellipse(512, 706, 46, 58, (255, 143, 163))  # tongue
    fill_ellipse(512, 690, 46, 30, (255, 143, 163))
    fill_rect(508, 668, 517, 716, (214, 96, 120))    # tongue centre line
    # Mouth corners: dark smile curves either side of the tongue.
    fill_ellipse(462, 672, 26, 10, (58, 40, 28))
    fill_ellipse(462, 666, 26, 10, cream)
    fill_ellipse(562, 672, 26, 10, (58, 40, 28))
    fill_ellipse(562, 666, 26, 10, cream)

    # 11. Flower meadow along the bottom (in front of the puppy's
    #     lower edge, framing the scene, not covering the face).
    for cx, petal in (
        (80, (255, 120, 160)), (210, (255, 255, 255)),
        (330, (178, 122, 245)), (700, (255, 120, 160)),
        (820, (255, 255, 255)), (950, (255, 196, 66)),
    ):
        flower(cx, 880, petal, (255, 196, 66))
    # Small grass tufts.
    for gx in (60, 150, 270, 420, 600, 760, 880, 990):
        fill_polygon(
            [(gx, 1024), (gx + 8, 968), (gx + 16, 1024)], (46, 139, 55)
        )


# ---------------------------------------------------------------- PNG
def _chunk(kind: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + kind
        + data
        + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    )


def encode_png() -> bytes:
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)  # 8-bit RGB
    raw = bytearray()
    for y in range(H):
        raw.append(0)  # filter: None
        raw += buf[y * W * 3:(y + 1) * W * 3]
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + _chunk(b"IEND", b"")
    )


def main() -> None:
    draw()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_bytes(encode_png())


if __name__ == "__main__":
    main()

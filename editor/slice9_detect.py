#!/usr/bin/env python3
# slice9_detect.py - normalise + auto-slice a generated 9-slice frame.
# ============================================================================
# The IMAGE-GEN path for slice9 atlases. A model generates an ornate frame
# (gold filigree, carved stone) to the geometry contract: a centered hollow
# frame on a transparent middle, identical corners, tileable straight edges.
# rembg cuts the background; THIS tool then:
#   1. squares the canvas (transparent pad) so corners stay symmetric,
#   2. trims rembg's soft alpha fringe,
#   3. DETECTS the four slice insets from where the transparent center begins
#      (that inset IS the border-image-slice - the point past which the edge is
#      a stretchable band), with a filled-frame fallback.
#
# Used two ways:
#   python3 slice9_detect.py detect    <png>   -> prints {"slice":[t,r,b,l],...} (JSON, stdout)
#   python3 slice9_detect.py normalize <png>   -> PNG bytes on stdout, JSON meta on stderr
#
# The daemon's _local_slice9 (serve.py) calls `normalize`; an orchestrating
# agent calls `detect` to assemble atlas.json. PIL-only, Python 3.9 safe.
# ============================================================================
from __future__ import annotations

import json
import sys

try:
    from PIL import Image
except Exception as e:  # pragma: no cover - surfaced to the daemon as a clean error
    sys.stderr.write("Pillow (PIL) is required: pip install --user Pillow\n")
    raise

ALPHA_SOLID = 40        # alpha above this counts as "opaque content"
CENTER_LO = 0.40        # central span used to test "is this row/col hollow?"
CENTER_HI = 0.60


def _load_rgba(path: str) -> "Image.Image":
    return Image.open(path).convert("RGBA")


def _alpha_at(px, x: int, y: int) -> int:
    return px[x, y][3]


def detect_slices(img: "Image.Image"):
    """Return [top, right, bottom, left] insets (source px) where the
    stretchable edge begins - i.e. where the hollow center starts on each side.
    Falls back to ~1/4 of the short side for a FILLED frame (no transparency)."""
    w, h = img.size
    px = img.load()
    cx0, cx1 = int(w * CENTER_LO), int(w * CENTER_HI)
    cy0, cy1 = int(h * CENTER_LO), int(h * CENTER_HI)

    def row_hollow(y: int) -> bool:
        # a frame row over the center is transparent; a solid border band is not
        return all(_alpha_at(px, x, y) < ALPHA_SOLID for x in range(cx0, cx1))

    def col_hollow(x: int) -> bool:
        return all(_alpha_at(px, x, y) < ALPHA_SOLID for y in range(cy0, cy1))

    # each inset = distance from that edge to the first hollow row/col
    top = next((k for k in range(h) if row_hollow(k)), -1)
    bottom = next((k for k in range(h) if row_hollow(h - 1 - k)), -1)
    left = next((k for k in range(w) if col_hollow(k)), -1)
    right = next((k for k in range(w) if col_hollow(w - 1 - k)), -1)

    if min(top, bottom, left, right) < 1:
        # filled frame (no hollow center) - cannot detect; use a sane default
        fb = max(2, round(min(w, h) * 0.25))
        return [fb, fb, fb, fb], False
    return [top, right, bottom, left], True


def _square_pad(img: "Image.Image") -> "Image.Image":
    w, h = img.size
    if w == h:
        return img
    s = max(w, h)
    canvas = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    canvas.paste(img, ((s - w) // 2, (s - h) // 2))
    return canvas


def _trim_fringe(img: "Image.Image") -> "Image.Image":
    """Harden rembg's soft matte: drop near-zero alpha to fully transparent so
    the detected hollow is clean and edges don't ghost when stretched."""
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a < 12:
                px[x, y] = (r, g, b, 0)
    return img


def normalize(path: str):
    img = _trim_fringe(_square_pad(_load_rgba(path)))
    slice_, detected = detect_slices(img)
    w, h = img.size
    corner = slice_[0]
    meta = {
        "slice": slice_,
        "w": w, "h": h,
        "corner": corner,
        "detected": detected,            # False = fallback used (filled frame)
        # a reasonable rendered border thickness; the theme can override
        "width": max(12, min(48, round(corner * 0.6))),
        "repeat": "stretch",
        "fill": True,
    }
    out = sys.stdout.buffer
    img.save(out, format="PNG")
    out.flush()
    sys.stderr.write(json.dumps(meta))
    sys.stderr.flush()


def detect(path: str):
    img = _load_rgba(path)
    slice_, detected = detect_slices(img)
    print(json.dumps({"slice": slice_, "detected": detected,
                      "w": img.size[0], "h": img.size[1]}))


def main(argv):
    if len(argv) < 3:
        sys.stderr.write("usage: slice9_detect.py {detect|normalize} <png>\n")
        return 2
    op, path = argv[1], argv[2]
    if op == "detect":
        detect(path)
    elif op == "normalize":
        normalize(path)
    else:
        sys.stderr.write("unknown op: %s\n" % op)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

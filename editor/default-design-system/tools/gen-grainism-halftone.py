#!/usr/bin/env python3
"""Generate the grainism halftone mask and embed it into themes/grainism.css.

Bakes a REAL amplitude-modulated halftone screen: dot RADIUS encodes tone, so the
dots ramp from pinpricks (light) to merged near-solid blobs (dark) along a diagonal
- the classic newsprint corner-shadow / vignette ramp - screened at a 15 degree
angle. Output is a white-on-transparent RGBA PNG used as a CSS mask-image; the
theme paints the dots with background-color:var(--halftone-color), so it stays
themeable and dark-mode-safe. Re-run after tweaking the knobs below.
"""
from __future__ import annotations

import base64
import io
import math
import pathlib
import re

import numpy as np
from PIL import Image

# ---- knobs ----------------------------------------------------------------
W, H = 1200, 760           # mask resolution (scaled with background-size:cover)
CELL = 8.0                 # screen pitch in px (dot-to-dot spacing)
ANGLE = math.radians(15)   # screen angle (15 deg = classic K channel)
R_MAX = 0.72               # max dot radius as a fraction of CELL (0.5 = dots touch on the grid; >0.5 merges)
GAMMA = 1.15               # tone ramp shaping (>1 keeps the light end airy longer)
SS = 3                     # supersampling: positions dot edges accurately, then we threshold to 1-bit
# directional tone: weight of x vs y in the diagonal ramp (light at top-left -> dark at bottom-right)
WX, WY = 0.55, 0.55

CSS = pathlib.Path(__file__).resolve().parent.parent / "themes" / "grainism.css"


def build() -> Image.Image:
    w, h = W * SS, H * SS
    cell = CELL * SS
    rmax = R_MAX * cell

    ys, xs = np.meshgrid(np.arange(h), np.arange(w), indexing="ij")
    xs = xs.astype(np.float32)
    ys = ys.astype(np.float32)

    ca, sa = math.cos(ANGLE), math.sin(ANGLE)
    # rotate into screen space
    u = xs * ca + ys * sa
    v = -xs * sa + ys * ca

    # nearest cell centre in screen space, then rotate back to sample the tone there
    cu = (np.floor(u / cell) + 0.5) * cell
    cv = (np.floor(v / cell) + 0.5) * cell
    cx = cu * ca - cv * sa
    cy = cu * sa + cv * ca

    t = WX * (cx / w) + WY * (cy / h)
    t = np.clip(t, 0.0, 1.0) ** GAMMA
    radius = rmax * np.sqrt(t)            # area proportional to tone

    # distance from this pixel to its cell centre, in screen space
    du = u - cu
    dv = v - cv
    dist = np.sqrt(du * du + dv * dv)

    aa = 1.0 * SS
    # coverage = 1 inside the dot, smooth across a 1px (pre-SS) edge
    cov = np.clip((radius - dist) / aa + 0.5, 0.0, 1.0)

    # downsample the smooth coverage to place edges well, then threshold to 1-bit
    # alpha so the PNG stays tiny (runs of 0/255 compress far better than gradients).
    cov_img = Image.fromarray((cov * 255.0).astype(np.uint8), "L")
    if SS != 1:
        cov_img = cov_img.resize((W, H), Image.LANCZOS)
    alpha = (np.asarray(cov_img) > 128).astype(np.uint8) * 255

    lum = np.full((H, W), 255, dtype=np.uint8)   # L channel ignored by mask-image (alpha is what masks)
    return Image.fromarray(np.dstack([lum, alpha]), "LA")


def main() -> None:
    img = build()
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    data_uri = "data:image/png;base64," + b64

    css = CSS.read_text()
    # replace either the placeholder (first run) or a previously-baked data-uri
    css, n = re.subn(
        r"(--halftone-mask:url\(\")[^\"]*(\"\);)",
        lambda m: m.group(1) + data_uri + m.group(2),
        css,
    )
    if n == 0:
        raise SystemExit(f"could not find --halftone-mask url() target in {CSS}")
    CSS.write_text(css)
    print(f"baked {len(b64)/1024:.1f} KB base64 into --halftone-mask in {CSS.name}")


if __name__ == "__main__":
    main()

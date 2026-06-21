#!/usr/bin/env python3
"""
recolor_palette.py - perceptual, palette-based image recoloring.

Detects an image's color palette (k color groups), then recolors the image by
editing one or more of those palette colors. Edits are specified in OKLCH
(lightness / chroma / hue), and ALL color math happens in the OKLab perceptual
color space, so:

  * Changing a color's HUE does not change its perceived LIGHTNESS (no "glow").
  * Editing one palette color leaves the others alone (smooth, localized weights).
  * Transitions stay smooth -- no pixel breakup on textured/compressed images.

Method: palette = k-means in OKLab; per-pixel weights = interpolating radial
basis functions (Chang et al., "Palette-based Photo Recoloring", SIGGRAPH 2015);
recoloring = displacement composition  out = x + sum_i w_i(x) * (palette'_i - palette_i),
evaluated in OKLab. The RBF width is derived automatically from palette spacing,
so there is no width/sigma knob to tune.

Requires: numpy, pillow         (no GPU, no scipy, no sklearn)

CLI
---
  # 1) inspect the palette (prints JSON: index, rgb, oklch, coverage)
  python recolor_palette.py palette INPUT --k 6 [--swatches pal.png]

  # 2) apply edits (edits.json maps palette index -> edit; see GUIDE)
  python recolor_palette.py apply INPUT OUTPUT --k 6 --edits edits.json

`--k` and `--seed` MUST match between the two calls so indices line up.
"""
from __future__ import annotations
import argparse, json, math, sys
import numpy as np
from PIL import Image

# --------------------------------------------------------------------------- #
# OKLab / OKLCH  (Bjorn Ottosson, 2020)
# --------------------------------------------------------------------------- #
def srgb_to_linear(c):
    c = np.asarray(c, np.float64)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)

def linear_to_srgb(c):
    c = np.clip(np.asarray(c, np.float64), 0, 1)
    return np.where(c <= 0.0031308, 12.92 * c, 1.055 * c ** (1 / 2.4) - 0.055)

_M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929],
                [0.2119034982, 0.6806995451, 0.1073969566],
                [0.0883024619, 0.2817188376, 0.6299787005]])
_M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468],
                [1.9779984951, -2.4285922050, 0.4505937099],
                [0.0259040371, 0.7827717662, -0.8086757660]])
_M1i, _M2i = np.linalg.inv(_M1), np.linalg.inv(_M2)

def srgb_to_oklab(rgb01):
    return np.cbrt(srgb_to_linear(rgb01) @ _M1.T) @ _M2.T

def oklab_to_srgb(lab):
    lin = (lab @ _M2i.T) ** 3 @ _M1i.T
    return np.clip(linear_to_srgb(lin), 0, 1)

def oklab_to_lch(lab):
    L = lab[..., 0]
    C = np.hypot(lab[..., 1], lab[..., 2])
    H = np.degrees(np.arctan2(lab[..., 2], lab[..., 1])) % 360
    return L, C, H

def lch_to_oklab(L, C, Hdeg):
    h = math.radians(Hdeg)
    return np.array([L, math.cos(h) * C, math.sin(h) * C])

# --------------------------------------------------------------------------- #
# Palette extraction (k-means in OKLab)
# --------------------------------------------------------------------------- #
def extract_palette(img, k=6, samples=40000, seed=0):
    """Returns (centers_oklab [k,3], info [list of dicts])."""
    px = (np.asarray(img.convert("RGB")) / 255.0).reshape(-1, 3)
    rng = np.random.default_rng(seed)
    sub = px[rng.choice(len(px), min(samples, len(px)), replace=False)]
    lab = srgb_to_oklab(sub)
    c = [lab[rng.integers(len(lab))]]                          # k-means++
    for _ in range(1, k):
        d = np.min(((lab[:, None] - np.array(c)[None]) ** 2).sum(-1), 1)
        c.append(lab[rng.choice(len(lab), p=d / d.sum())])
    C = np.array(c)
    a = np.zeros(len(lab), int)
    for _ in range(50):
        a = ((lab[:, None] - C[None]) ** 2).sum(-1).argmin(1)
        newC = np.array([lab[a == i].mean(0) if np.any(a == i) else C[i] for i in range(k)])
        if np.allclose(newC, C, atol=1e-5):
            C = newC; break
        C = newC
    cov = np.bincount(a, minlength=k) / len(a)
    order = np.argsort(-cov)                                   # most common first
    C = C[order]; cov = cov[order]
    rgb = (oklab_to_srgb(C) * 255 + 0.5).astype(int)
    L, Ch, H = oklab_to_lch(C)
    info = [{"index": i, "rgb": tuple(int(v) for v in rgb[i]),
             "oklch": {"L": round(float(L[i]), 3), "C": round(float(Ch[i]), 3),
                       "H": round(float(H[i]), 1)},
             "coverage": round(float(cov[i]), 3)} for i in range(k)]
    return C, info

# --------------------------------------------------------------------------- #
# Recoloring
# --------------------------------------------------------------------------- #
def _rbf_weights(lab_pixels, palette):
    dPP = np.sqrt(((palette[:, None] - palette[None]) ** 2).sum(-1))
    sigma = np.where(dPP > 0, dPP, np.inf).min(1).mean()       # auto width
    phi = lambda d2: np.exp(-d2 / (2.0 * sigma * sigma))
    Phi_inv = np.linalg.pinv(phi(dPP ** 2))
    Psi = phi(((lab_pixels[:, None] - palette[None]) ** 2).sum(-1))
    W = np.clip(Psi @ Phi_inv, 0, None)                        # interpolating, smooth
    s = W.sum(1, keepdims=True)
    return np.divide(W, s, out=np.zeros_like(W), where=s > 1e-12)

def _edit_to_oklab(center, oklch, edit):
    """Compute the new palette color (OKLab) for an edit dict."""
    if "target_rgb" in edit:
        return srgb_to_oklab(np.array(edit["target_rgb"]) / 255.0)
    L = oklch["L"] + edit.get("lightness_shift", 0.0)
    C = oklch["C"] * edit.get("chroma_scale", 1.0)
    H = edit["hue_set"] if "hue_set" in edit else oklch["H"] + edit.get("hue_rotate", 0.0)
    return lch_to_oklab(L, C, H)

def recolor(img, palette, info, edits):
    """edits: {int index -> edit dict}. Returns a recolored PIL image."""
    arr = np.asarray(img.convert("RGB"), np.uint8); h, w = arr.shape[:2]
    lab = srgb_to_oklab((arr / 255.0).reshape(-1, 3))
    W = _rbf_weights(lab, palette)
    D = np.zeros_like(palette)
    for i, e in edits.items():
        if e:
            D[i] = _edit_to_oklab(palette[i], info[i]["oklch"], e) - palette[i]
    out = oklab_to_srgb(lab + W @ D)
    return Image.fromarray((out.reshape(h, w, 3) * 255 + 0.5).astype(np.uint8), "RGB")

def save_swatches(info, path, sw=110):
    from PIL import ImageDraw, ImageFont
    k = len(info); im = Image.new("RGB", (k * sw, sw + 40), (245, 245, 247))
    d = ImageDraw.Draw(im)
    try: f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    except Exception: f = ImageFont.load_default()
    for g in info:
        i = g["index"]; d.rectangle([i * sw, 0, (i + 1) * sw - 2, sw], fill=g["rgb"])
        d.text((i * sw + 3, sw + 2), f"#{i}  {int(g['coverage']*100)}%", fill=(20, 20, 20), font=f)
        o = g["oklch"]; d.text((i * sw + 3, sw + 20), f"L{o['L']:.2f} H{int(o['H'])}", fill=(90, 90, 90), font=f)
    im.save(path)

# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main(argv=None):
    ap = argparse.ArgumentParser(description="Perceptual palette-based recoloring (OKLab/OKLCH).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("palette", help="detect and print the palette as JSON")
    p.add_argument("input"); p.add_argument("--k", type=int, default=6)
    p.add_argument("--seed", type=int, default=0); p.add_argument("--swatches")
    a = sub.add_parser("apply", help="apply edits and save")
    a.add_argument("input"); a.add_argument("output")
    a.add_argument("--k", type=int, default=6); a.add_argument("--seed", type=int, default=0)
    a.add_argument("--edits", required=True, help="JSON file: {index: edit, ...}")
    args = ap.parse_args(argv)

    img = Image.open(args.input)
    if args.cmd == "palette":
        _, info = extract_palette(img, k=args.k, seed=args.seed)
        if args.swatches: save_swatches(info, args.swatches)
        print(json.dumps({"k": args.k, "seed": args.seed, "palette": info}, indent=2))
    else:
        spec = json.load(open(args.edits))
        edits_raw = spec.get("edits", spec)                    # allow bare dict or {"edits":...}
        edits = {int(k): v for k, v in edits_raw.items()}
        C, info = extract_palette(img, k=args.k, seed=args.seed)
        recolor(img, C, info, edits).save(args.output)
        print(f"wrote {args.output}")

if __name__ == "__main__":
    main()

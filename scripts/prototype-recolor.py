#!/usr/bin/env python3
"""
prototype-recolor.py - recolor a prototype-library reference image into ONE
direction-option's committed palette, so the Step -1 stop-and-ask UI can show
each option's library preview already wearing that option's colours.

Wrapper around scripts/recolor_palette.py. Handles the role-mapping the agent
would otherwise have to do by hand (which palette index becomes which token).

Usage
-----
  python scripts/prototype-recolor.py \
      <source-image> <output-image> \
      --tokens "#fafafa,#ffffff,#1a1a1a,#888888,#e5e5e5,#5566ee"

The --tokens list is the option's committed palette in any order - the script
identifies the accent (highest chroma) and the neutrals (the rest) on its own.

Mapping heuristic
-----------------
1. Extract source palette with k = len(target_tokens) (k=6 by default).
2. In the SOURCE palette, the most-chromatic entry becomes the accent slot;
   the remaining entries are the neutral slots.
3. In the TARGET tokens, identify the accent the same way (highest chroma in
   OKLCH); the remaining tokens are the target neutrals.
4. Match source-accent → target-accent (`target_rgb` edit).
5. Sort source neutrals by perceived L ascending; sort target neutrals by L
   ascending; match 1:1 (`target_rgb` edits).

The recolor is smooth (RBF weights from recolor_palette.recolor) so the output
preserves the source image's tonal structure - light areas stay light, dark
areas stay dark, only hue/chroma snap to the new palette.

Requires: numpy, pillow.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Make sibling recolor_palette.py importable regardless of cwd.
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import numpy as np
from PIL import Image

import recolor_palette as rp


def hex_to_rgb(token: str) -> tuple[int, int, int]:
    s = token.strip().lstrip("#")
    if len(s) == 3:
        s = "".join(c + c for c in s)
    if len(s) != 6:
        raise ValueError(f"bad hex token: {token!r}")
    return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)


def rgb_to_oklch(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
    """Single-pixel sRGB → OKLCH."""
    arr = np.array(rgb, dtype=np.float64) / 255.0
    lab = rp.srgb_to_oklab(arr.reshape(1, 3))
    L, C, H = rp.oklab_to_lch(lab)
    return float(L[0]), float(C[0]), float(H[0])


def build_edits(target_tokens: list[str], source_info: list[dict]) -> dict[int, dict]:
    """Map each source palette index to a target_rgb edit."""
    targets = [(t, hex_to_rgb(t), rgb_to_oklch(hex_to_rgb(t))) for t in target_tokens]
    # Highest-chroma target = accent.
    accent_target_idx = max(range(len(targets)), key=lambda i: targets[i][2][1])

    # Highest-chroma source = accent slot.
    accent_src_idx = max(range(len(source_info)),
                         key=lambda i: source_info[i]["oklch"]["C"])

    neutral_target_indices = [i for i in range(len(targets)) if i != accent_target_idx]
    neutral_src_indices = [i for i in range(len(source_info)) if i != accent_src_idx]

    # Sort by perceived L ascending - dark to light.
    neutral_target_indices.sort(key=lambda i: targets[i][2][0])
    neutral_src_indices.sort(key=lambda i: source_info[i]["oklch"]["L"])

    edits: dict[int, dict] = {
        accent_src_idx: {"target_rgb": list(targets[accent_target_idx][1])},
    }
    for src_i, tgt_i in zip(neutral_src_indices, neutral_target_indices):
        edits[src_i] = {"target_rgb": list(targets[tgt_i][1])}
    return edits


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("source", help="reference image (e.g. design-library/shell-mobile-app-ui.png)")
    ap.add_argument("output", help="recoloured output PNG path")
    ap.add_argument("--tokens", required=True,
                    help="comma-separated hex tokens for the target palette, "
                         "e.g. '#fafafa,#ffffff,#1a1a1a,#888888,#e5e5e5,#5566ee'")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)

    target_tokens = [t.strip() for t in args.tokens.split(",") if t.strip()]
    if len(target_tokens) < 4:
        ap.error("need at least 4 target tokens (bg, surface/border, fg, accent)")

    img = Image.open(args.source)
    centers, info = rp.extract_palette(img, k=len(target_tokens), seed=args.seed)
    edits = build_edits(target_tokens, info)
    out = rp.recolor(img, centers, info, edits)

    os.makedirs(os.path.dirname(os.path.abspath(args.output)) or ".", exist_ok=True)
    out.save(args.output)
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

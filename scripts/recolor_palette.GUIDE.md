# recolor_palette — Agent Guide

Perceptual, palette-based image recoloring. Detect an image's color palette (a
small set of color *groups*), then recolor by editing one or more of those
colors. All math is in the **OKLab/OKLCH** perceptual color space.

This guide is written for an LLM agent driving the tool. Read the **Agent
recipe** and **Edit specification** sections first.

---

## What it does

- Extracts a palette of `k` color groups from any image (k-means in OKLab).
- Recolors by editing chosen palette colors; **unedited colors are left alone**.
- Edits are perceptual: change **hue / chroma / lightness** independently, or map
  a color to a specific target RGB.
- Smooth, localized result — no hard edges, no pixel "breakup," even on
  textured/JPEG/WebP images.

## What it cannot do

- **It cannot separate two regions that are the same color.** If a dress and the
  skin share the same hue+lightness, editing one edits both. That requires
  spatial/semantic segmentation, which this tool does not do.
- It is global per color group. There is no "only the top-left" — selection is by
  color, not location.
- A tiny amount of an edit can bleed into nearby colors (smooth weights have soft
  tails). Usually imperceptible.

---

## Requirements

```
pip install numpy pillow
```
No GPU, no scipy/sklearn. Pure CPU. Works on PNG/JPG/WebP.

---

## Mental model

1. The palette is `k` colors, each with an **index** (0..k-1), an **rgb** swatch,
   its **OKLCH** = `{L, C, H}`, and **coverage** (fraction of the image).
   - `L` = perceived lightness, 0 (black) .. 1 (white)
   - `C` = chroma (colorfulness), ~0 (gray) .. ~0.4
   - `H` = hue angle in degrees, 0..360 (0/360≈red, ~120≈green, ~150-200≈teal,
     ~250-290≈blue/violet, ~330≈magenta) — **OKLab hue, not HSV hue**.
2. You edit some indices. Each edit moves that palette color; every pixel shifts
   in proportion to how much it belongs to that color.
3. Because the work is in OKLab, **changing H or C does not change L** — a color
   keeps its brightness unless you explicitly set `lightness_shift`.

---

## Two-step workflow (important)

**Step 1 — inspect the palette**, then **Step 2 — apply edits**.
`k` and `seed` MUST be identical across the two steps, or the indices won't match.

### CLI

```bash
# Step 1: print palette as JSON (and optionally save a labeled swatch strip)
python recolor_palette.py palette INPUT.png --k 6 --seed 0 --swatches pal.png

# Step 2: apply edits from a JSON file
python recolor_palette.py apply INPUT.png OUTPUT.png --k 6 --seed 0 --edits edits.json
```

`palette` prints:
```json
{ "k": 6, "seed": 0, "palette": [
  { "index": 0, "rgb": [144,197,189], "oklch": {"L":0.79,"C":0.06,"H":184.2}, "coverage": 0.42 },
  ...
] }
```

`edits.json` (either form is accepted):
```json
{ "edits": { "0": {"hue_set": 45}, "5": {"hue_rotate": -30, "chroma_scale": 1.2} } }
```

### Python API

```python
from PIL import Image
import recolor_palette as rp

img = Image.open("INPUT.png")
centers, info = rp.extract_palette(img, k=6, seed=0)   # info = list of dicts (as JSON above)

edits = {0: {"hue_set": 45}, 5: {"hue_rotate": -30, "chroma_scale": 1.2}}
out = rp.recolor(img, centers, info, edits)
out.save("OUTPUT.png")

rp.save_swatches(info, "pal.png")                       # optional palette preview
```

---

## Edit specification

`edits` maps a palette **index** (int) to an **edit dict**. Omitted indices are
unchanged. Within one edit, combine keys freely (e.g. set hue *and* boost chroma).

| Key | Type / range | Meaning |
|---|---|---|
| `hue_set` | degrees `0..360` | Set hue to an absolute OKLab hue angle. |
| `hue_rotate` | degrees, e.g. `-180..180` | Rotate hue relative to current. Ignored if `hue_set` present. |
| `chroma_scale` | float, `0..~3` (1 = unchanged) | Multiply colorfulness. `0` = grayscale, `<1` = muted, `>1` = punchier. |
| `lightness_shift` | float, `-1..1` (0 = unchanged) | Add to perceived lightness. `+` lighter, `−` darker. |
| `target_rgb` | `[r,g,b]` 0..255 | Map this palette color directly to a target color. Overrides the keys above. |

**Defaults (identity):** `hue_rotate 0`, `chroma_scale 1`, `lightness_shift 0`.
An empty edit `{}` does nothing.

---

## OKLCH behavior (the rules)

- **Hue-only or chroma-only edits preserve perceived lightness exactly.** Editing
  `hue_set`/`hue_rotate`/`chroma_scale` leaves every pixel's `L` unchanged.
- **Lightness changes only via `lightness_shift`.** Nothing else moves brightness.
- `target_rgb` moves all three (L, C, H) to match the target. If you want to
  recolor hue but keep the original brightness/feel, prefer `hue_set` +
  `chroma_scale` over `target_rgb`.

---

## Agent recipe: natural-language request → edits

1. **Run `palette`** on the image with a chosen `k` (start at 6).
2. **Identify the target group(s)** from the JSON by matching the user's words to
   each entry's `rgb` and `oklch.H`:
   - "the sky / the blue" → highest-coverage entry with `H` ≈ 250–290.
   - "the greenery / leaves" → `H` ≈ 120–160.
   - "teal/cyan" → `H` ≈ 160–200. "red" → `H` ≈ 20–40. "magenta/pink" → `H` ≈ 0 or 330–360.
   - Use `coverage` to disambiguate (the background is usually the biggest group).
   - A single perceived color may span 2–3 entries (e.g. light/dark shades). Edit
     all of them the same way to move the whole thing.
3. **Translate the desired change** into edit keys:
   - "make it orange" → `{"hue_set": 40}`. "make it blue" → `{"hue_set": 260}`.
   - "shift it warmer/cooler" → `{"hue_rotate": -20}` / `{"hue_rotate": +20}`.
   - "more vivid / muted / grayscale" → `chroma_scale` 1.3 / 0.6 / 0.
   - "lighter / darker" → `lightness_shift` +0.1 / −0.1.
   - "make it exactly this color" → `{"target_rgb": [r,g,b]}`.
4. **Run `apply`** with the same `k`/`seed`. Inspect output; adjust and repeat.

> If a hue-only edit looks washed out, the source color was low-chroma — add
> `chroma_scale` (e.g. 1.4) so the new hue reads clearly.

---

## Worked examples

**Change one color (background sky → sunset).** Palette shows `#1` is the blue sky.
```json
{ "edits": { "1": {"hue_set": 35, "chroma_scale": 1.2} } }
```

**Change several colors, keep the rest.** `#0` background, `#6` accents; leave the
subject's colors untouched.
```json
{ "edits": { "0": {"hue_set": 45}, "6": {"hue_set": 255} } }
```

**Whole new theme.** Edit most/all palette entries (e.g. rotate everything warm).
```json
{ "edits": { "0": {"hue_rotate": 120}, "1": {"hue_rotate": 120}, "2": {"hue_rotate": 120} } }
```

**Map to a brand color exactly.**
```json
{ "edits": { "2": {"target_rgb": [33, 122, 240]} } }
```

**Desaturate one color / darken another.**
```json
{ "edits": { "3": {"chroma_scale": 0.2}, "0": {"lightness_shift": -0.12} } }
```

---

## Tunable parameters (besides edits)

| Param | Where | Effect |
|---|---|---|
| `k` | `palette` & `apply` | Number of color groups. Raise it (e.g. 8–10) when a distinct feature is being lumped with another so it gets its own index. Lower it for broad strokes. |
| `seed` | `palette` & `apply` | Random seed for k-means. Keep identical across both calls. Change only if a palette split looks unstable. |

There is intentionally **no width/sigma knob** — the weight smoothness is derived
automatically from palette spacing.

---

## Limitations & remedies

- **Same-color regions move together** (dress vs. skin of the same pink). No color
  method can split them; needs segmentation. Remedy: none within this tool.
- **Hue-only edit looks washed out** → source was low-chroma; add `chroma_scale`.
- **A feature is lumped into the wrong group** → increase `k` so it separates,
  then re-read the palette (indices change when `k` changes).
- **Slight bleed into a neighboring color** → expected (smooth tails); usually
  invisible. If it matters, raise `k` so the two colors are more distinct.
- **Out-of-gamut targets** are clipped to displayable sRGB after conversion.

---
# Sample-image references for the System-tab design library. Images sit
# next to this file in prototype/ and were generated via image_gen.
images:
  - src: shell-scrapbook-substrate-ui.png
    reason: Generated UI mockup showing this shell's structural grammar — grid, density, regions, and characteristic component placement.
---
# Scrapbook substrate shell

**Tag:** `[any-aesthetic · raster-cutouts · layered z-order]`

## Structure

Full-bleed substrate texture hosts raster cutouts with overlap and rotation.

- Substrate: full-viewport background (PNG of paper / cork / fabric / journal)
- Cutouts: PNG/WebP-with-alpha positioned absolutely or freeform grid
  - `box-shadow: 2px 4px 6px rgba(0,0,0,0.18)` (paper-edge shadow)
  - `transform: rotate(-4deg)` to `rotate(4deg)` (hand-pasted feel)
  - z-index stacking for overlap
- Decorations: washi tape SVGs, push-pin PNGs, stapled corners, margin notes

Freeform composition.

## Mandatory interactions

Hover lift on cutouts. Optional drag-to-rearrange. Tap-to-flip/reveal.

## Forbidden

Lucide icons. Geometric SVG shapes. border-radius on cutouts. Pure white substrate.

## Best for

Aesthetic blogs, mood boards, fashion lookbooks, journal apps, fan catalogs.

## Pairs well with

Style: raster-cutout (mandatory). Aesthetic: cottagecore, dark-academia, y2k-myspace, goblincore, coastal-grandmother, fairycore, dreamcore, cottagegoth, angelcore, cluttercore — pick ONE.

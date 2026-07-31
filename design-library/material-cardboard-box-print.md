---
materialId: cardboard-box-print
name: Cardboard Box Print (one-ink screenprint on box board)
family: analog
category: packaging
surfaceFinish: matte (paper tooth, screen-ink grain)
scope: both
transparency: opaque
pairsPrototypes: [aesthetic-industrial-catalog, aesthetic-monochrome-pop-poster, aesthetic-craft-sketchbook, style-bold-display, shell-scrapbook-substrate, recipe-brutalist-web]
images:
  - src: material-cardboard-box-print.png
    reason: Material fidelity sample.
---

# Cardboard Box Print (one-ink screenprint on box board)

Printed corrugated packaging as a design system: the box-board color IS the field, everything on it is a single utility ink, and the layout follows die-line and shipping-label logic.

## Physical behavior

**Surface finish**: matte board with visible paper tooth; ink sits flat with slight screen grain

**Transparency**: opaque

**Reacts to light**: no

**Deforms**: creases at fold lines; corrugated flutes show at cut edges

**Age / wear**: scuffed corners, ink rub-off, sun fade

## Implementation strategies

```yaml
css: |
  /* the substrate is a saturated board color, not white - ink is ONE color on top */
  --board: #d26933; /* any box-board dye: kraft, orange, indigo, sage */
  --ink: #0e0e0e;
  body { background: var(--board); color: var(--ink); }
  /* everything is the ink: hairline die-line rules, 1-2px solid borders, filled bars */
  .rule { border-top: 1.5px solid var(--ink); }
  .btn-primary { background: var(--ink); color: var(--board); }
  .btn-secondary { border: 2px solid var(--ink); background: transparent; }
  /* corrugated edge reveal at panel cuts */
  .cut-edge { background: repeating-linear-gradient(90deg,
    #b98a5e 0 6px, #8a6644 6px 8px, #d9c4a8 8px 14px); height: 10px; }
svg: |
  product imagery as outline-only line art in the ink color (no fills, no photos);
  screen-ink grain via a coarse noise pattern multiplied into filled areas
raster: kraft/board paper scan at low opacity multiply for tooth
```

## Reactive behaviors

**Light**: no

**Highlight**: state changes swap fill polarity (ink-on-board becomes board-on-ink), like a second print pass

**Depth**: none - print is flat; hierarchy comes from type scale and die-line divisions

**Parallax**: none

## Common implementation mistakes (avoid these)

- multi-color gradients (the palette is one ink plus the board dye; extra colors arrive only as tiny swatch chips or spot labels)
- photographic imagery (box print is line art and type; a photo breaks the screenprint register)
- soft shadows and rounded glass (packaging is flat print with die-cut hard edges)
- white page background (the board color must be the field, edge to edge)
- perfect ink coverage (screen ink wants slight grain and rub; flat vector fill reads as digital)
- decorating with the corrugation everywhere (flutes appear only at cut edges and reveals, not as wallpaper)

## Examples in the wild

- sneaker-box and shipping-carton print systems
- fruit-crate and industrial-supply box labels
- kraft mailer packaging with single-ink branding

## Pairs with (prototype slugs)

- `aesthetic-industrial-catalog`
- `aesthetic-monochrome-pop-poster`
- `aesthetic-craft-sketchbook`
- `style-bold-display`
- `shell-scrapbook-substrate`
- `recipe-brutalist-web`

## Differentiation

- vs `material-paper-construction`: that is layered cut colored paper with physical depth; box print is a single flat board surface where all interest is printed
- vs `material-silkscreen`: silkscreen is an art print - layered inks on white stock; box print is industrial packaging - one utility ink on dyed board, governed by die-lines and label grids

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

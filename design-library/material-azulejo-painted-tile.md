---
materialId: azulejo-painted-tile
name: Azulejo Painted Tile (hand-brushed cobalt on glazed tile grid)
family: analog
category: ceramic
surfaceFinish: glossy (soft tin-glaze sheen)
transparency: opaque
scope: both
pairsPrototypes: [aesthetic-neoclassical-remix, recipe-brand-story-journey, style-serif-warm-paper, shell-centered-column]
images:
  - src: material-azulejo-painted-tile.png
    reason: Material fidelity sample.
---

# Azulejo Painted Tile (hand-brushed cobalt on glazed tile grid)

A wall of glazed tiles painted by hand in cobalt on milk white: everything - scrolling rocaille borders, cartouche frames, architectural scenes, even letterforms - is BRUSHWORK sitting under a soft tin-glaze sheen, and the whole surface is divided by a faint grout-seam grid that runs straight through the painting.

**Distinct from** `material-ceramic-glaze`, one continuous glossy surface with no imagery or grid - azulejo is a PAINTED, TILED plane where the grout lattice crosses the artwork; and from `material-watercolor-wash`, whose pigment blooms into paper fiber - azulejo brushwork pools and streaks on non-absorbent glaze, banded and stroke-visible, then fires permanent.

## Physical behavior

**Surface finish**: softly glossy - tin-glaze sheen, gentler than porcelain gloss

**Transparency**: opaque

**Reacts to light**: mildly - a broad low sheen across groups of tiles; slight per-tile variation as each sits at its own micro-angle

**Deforms**: no

**Age / wear**: graceful - occasional edge chips, one slightly mismatched replacement tile, crazing hairlines welcome

## Implementation strategies

```yaml
css: |
  /* the tile grid, laid OVER everything */
  .wall::after {
    content: ""; position: absolute; inset: 0; pointer-events: none;
    background:
      repeating-linear-gradient(0deg,  rgba(13,59,142,0.08) 0 1px, transparent 1px 120px),
      repeating-linear-gradient(90deg, rgba(13,59,142,0.08) 0 1px, transparent 1px 120px);
  }
  /* brush-paint blue */
  .painted { color: #0D3B8E; }
  .painted-wash { background: linear-gradient(120deg, #3F6FB7, #A8C3E6); } /* dilute strokes */
svg: |
  rocaille borders and cartouches as brush-weight paths (thick-thin stroke modulation);
  fills as layered dilute washes (cobalt mist under cobalt mid under cobalt deep) so
  every shape shows 2-3 brush-density steps; sparse mustard-gold accents only inside
  ornament frames
raster: scanned azulejo panels for hero scenes; ensure the grout grid crosses them
usage: |
  object scope: buttons and inputs as single painted border-tiles, cards as cartouche
  frames with scene fills
  medium scope: the whole page as one tiled wall - ornate painted border band around a
  calmer central field, grout grid uniting chrome and content
```

## Reactive behaviors

**Light**: mild - a slow broad sheen may traverse the wall; never a sharp specular dot

**Highlight**: per-tile - the hovered tile lifts its sheen a step, as if angled toward you

**Depth**: grout seams sit 1px low (faint dark line + hairline light lip below)

**Parallax**: none (a wall is a wall)

## Common implementation mistakes (avoid these)

- imagery that dodges the grid (the grout MUST cross the painting - artwork interrupted by seams is the entire azulejo signature)
- flat single-blue vectors (hand painting shows 2-3 dilution bands and stroke direction inside every shape)
- rainbow palettes (canonical azulejo is cobalt on white; at most one mustard-gold ornament accent)
- perfectly uniform tiles (vary each tile's white a fraction and rotate the sheen slightly; hand-set tiles are never identical)
- heavy drop shadows (a tiled wall is flat; depth lives in the 1px grout relief only)

## Examples in the wild

- Portuguese azulejo station halls (Sao Bento, Porto)
- Lisbon facade tiling and church cloisters
- Museu Nacional do Azulejo panels; heritage-brand identities quoting them

## Pairs with (prototype slugs)

- `aesthetic-neoclassical-remix`
- `recipe-brand-story-journey`
- `style-serif-warm-paper`
- `shell-centered-column`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

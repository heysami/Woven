---
materialId: washi-kozo-fiber
name: Washi Kozo Fiber (long-fibered craft paper with fold scoring)
family: analog
category: paper
surfaceFinish: matte
transparency: opaque
scope: both
pairsPrototypes: [aesthetic-japanese-poster-layout, recipe-warm-restraint, style-serif-warm-paper, shell-centered-column]
images:
  - src: material-washi-kozo-fiber.png
    reason: Material fidelity sample.
---

# Washi Kozo Fiber (long-fibered craft paper with fold scoring)

Handmade kozo-fiber paper whose long embedded strands stay visible in the sheet - fine pale filaments wandering through both the vermilion-dyed and natural-white grounds - scored by crisp fold creases that catch light as thin ridge lines, in a craft palette of vermilion, gold leaf dots, sumi black and warm paper grey.

**Distinct from** `material-parchment`, whose animal-skin mottle and aged yellowing carry no fiber strands - washi is plant fiber, fresh and matte with visible filaments; and from `material-paper-construction`, which is cut-and-layered card stock - washi's character lives IN the sheet (fiber, dye, crease), not in stacked cutouts.

## Physical behavior

**Surface finish**: matte, softly toothy; gold-leaf accents are the only shine

**Transparency**: opaque (heavier sheet; fibers read as surface marks, not backlit lace)

**Reacts to light**: only at creases - fold ridges catch a hairline highlight and cast a hairline shade

**Deforms**: yes - by folding only; washi takes and HOLDS a crease permanently

**Age / wear**: ageless (archival; creases are memory, not damage)

## Implementation strategies

```yaml
css: |
  /* fibered sheet */
  background:
    url(fiber-strands.png),                 /* sparse long filaments, 3-5% opacity */
    radial-gradient(140% 100% at 30% 0%, #E07A6E 0%, #D83C2E 60%);  /* dye unevenness */
  /* fold crease */
  .crease {
    background: linear-gradient(to bottom, rgba(255,255,255,0.5), rgba(0,0,0,0.12));
    height: 2px; transform: rotate(var(--fold-angle));
  }
svg: |
  fibers as long low-opacity bezier strokes with occasional crossings; creases as paired
  light/dark 1px lines meeting at fold vertices - diagonals must connect corner-to-corner
  like real origami scoring, never float
raster: scanned kozo sheet (white and vermilion-dyed) as ground truth for large fields
usage: |
  object scope: cards as creased squares (an X of diagonal scores), gold dots as markers,
  sumi-brush marks as accents
  medium scope: full washi ground, white content panels as uncreased calm sheet regions
```

## Reactive behaviors

**Light**: crease-only - flip the light/dark pair when a fold direction inverts (valley vs mountain)

**Highlight**: none on the flat sheet

**Depth**: fold logic - creased regions may lift a few px of soft shadow at their ridge

**Parallax**: none

## Common implementation mistakes (avoid these)

- uniform flat color (washi dye pools and fades; give every field a slow radial unevenness)
- fiber noise as gaussian grain (kozo strands are LONG distinct filaments, not speckle)
- creases as plain gray lines (a crease is a light/dark PAIR - lit side and shaded side)
- decorative fold lines that ignore geometry (scores connect vertices like a real fold net; arbitrary diagonals break the craft)
- glossy accents beyond gold leaf (only the leaf shines; the sheet itself never does)

## Examples in the wild

- origami instruction books and orizuru fold diagrams
- washi stationery and shuin stamp books
- Japanese craft-brand packaging with vermilion + sumi + gold

## Pairs with (prototype slugs)

- `aesthetic-japanese-poster-layout`
- `recipe-warm-restraint`
- `style-serif-warm-paper`
- `shell-centered-column`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

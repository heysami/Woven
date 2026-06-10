---
materialId: charcoal-drawing
name: Charcoal Drawing (smudged, expressive)
family: analog
category: ink
surfaceFinish: matte
transparency: translucent
pairsPrototypes: [aesthetic-dark-academia, aesthetic-cottagegoth, aesthetic-anti-design]
images:
  - src: material-charcoal-drawing.png
    reason: Material fidelity sample.
---

# Charcoal Drawing (smudged, expressive)

A matte surface (translucent).

## Physical behavior

**Surface finish**: matte

**Transparency**: translucent

**Reacts to light**: no

**Deforms**: no

**Age / wear**: shows wear (smudge)

## Implementation strategies

```yaml
css: |
  filter: contrast(1.3) brightness(0.85);
  mix-blend-mode: multiply;
svg: |
  <feTurbulence baseFrequency="0.05" numOctaves="3"/>
  <feDisplacementMap scale="2"/>
  <!-- coarser than pencil — charcoal pieces are bigger -->
raster: scanned charcoal artwork
```

## Reactive behaviors

**Light**: no

**Highlight**: no

**Depth**: smudge intensifies on press

**Parallax**: no

## Common implementation mistakes (avoid these)

- clean uniform fill (charcoal smudges)
- high-saturation accents alongside (charcoal is monochrome)

## Pairs with (prototype slugs)

- `aesthetic-dark-academia`
- `aesthetic-cottagegoth`
- `aesthetic-anti-design`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

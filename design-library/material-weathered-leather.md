---
materialId: weathered-leather
name: Weathered Leather (vintage, distressed)
family: analog
category: leather
surfaceFinish: matte
transparency: opaque
pairsPrototypes: [aesthetic-dark-academia, aesthetic-steampunk, aesthetic-dieselpunk, aesthetic-cottagegoth, aesthetic-corporate-grunge]
---

# Weathered Leather (vintage, distressed)

A matte surface that reacts to light: minor specular at non-worn areas and deforms: yes — creases at handle points.

## Physical behavior

**Surface finish**: matte

**Transparency**: opaque

**Reacts to light**: minor specular at non-worn areas

**Deforms**: yes — creases at handle points

**Age / wear**: acquired patina (cracks, discoloration)

## Implementation strategies

```yaml
css: |
  background:
    radial-gradient(ellipse at 25% 75%, rgba(0,0,0,0.3), transparent 35%),
    radial-gradient(ellipse at 75% 25%, rgba(255,255,255,0.06), transparent 35%),
    oklch(30% 0.06 35);
svg: |
  crack pattern via <feTurbulence baseFrequency="0.08"/> threshold-passed
raster: photograph of real weathered leather is essential
```

## Reactive behaviors

**Light**: minor specular at un-worn patches

**Highlight**: low intensity, asymmetric

**Depth**: subtle crease deepening on hover

**Parallax**: minimal

## Common implementation mistakes (avoid these)

- uniform wear (real wear lives at touch-points)
- no creases at all
- bright fresh leather colour

## Pairs with (prototype slugs)

- `aesthetic-dark-academia`
- `aesthetic-steampunk`
- `aesthetic-dieselpunk`
- `aesthetic-cottagegoth`
- `aesthetic-corporate-grunge`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

---
materialId: silk
name: Silk (lustrous fabric)
family: analog
category: fabric
surfaceFinish: semi-gloss
transparency: opaque
pairsPrototypes: [aesthetic-y2k-futurism, aesthetic-vaporwave, aesthetic-coastal-grandmother, aesthetic-defi-cosmic]
---

# Silk (lustrous fabric)

A semi-gloss surface that reacts to light: yes — anisotropic lustre and deforms: yes — flowing drape.

## Physical behavior

**Surface finish**: semi-gloss

**Transparency**: opaque

**Reacts to light**: yes — anisotropic lustre

**Deforms**: yes — flowing drape

**Age / wear**: shows wear (fray, water spots)

## Implementation strategies

```yaml
css: |
  background:
    linear-gradient(135deg,
      rgba(255,255,255,0.3) 0%,
      transparent 30%,
      rgba(255,255,255,0.2) 60%,
      transparent 100%
    ),
    oklch(75% 0.12 350);
raster: silk photograph
```

## Reactive behaviors

**Light**: lustre band shifts with pointer angle

**Highlight**: yes — narrow band perpendicular to fibre direction

**Depth**: drape via scroll-driven skewY

**Parallax**: yes — gentle

## Common implementation mistakes (avoid these)

- flat fabric (silk is always shifting in light)
- no drape (silk hangs)

## Pairs with (prototype slugs)

- `aesthetic-y2k-futurism`
- `aesthetic-vaporwave`
- `aesthetic-coastal-grandmother`
- `aesthetic-defi-cosmic`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

---
materialId: gold-leaf
name: Gold Leaf (rich warm metal)
family: digital
category: metal
surfaceFinish: metallic
transparency: opaque
pairsPrototypes: [aesthetic-dark-academia, aesthetic-defi-cosmic, aesthetic-urbling, style-holographic]
images:
  - src: material-gold-leaf.png
    reason: Material fidelity sample.
---

# Gold Leaf (rich warm metal)

A metallic surface that reacts to light: yes - warm specular, slight wrinkle.

## Physical behavior

**Surface finish**: metallic

**Transparency**: opaque

**Reacts to light**: yes - warm specular, slight wrinkle

**Deforms**: no

**Age / wear**: acquired patina

## Implementation strategies

```yaml
css: |
  background:
    linear-gradient(180deg,
      oklch(95% 0.10 90) 0%,
      oklch(70% 0.14 75) 50%,
      oklch(50% 0.12 60) 100%
    );
  box-shadow:
    inset 0 1px 0 rgba(255,250,210,0.9),
    inset 0 -1px 0 rgba(80,40,0,0.5),
    0 2px 6px rgba(80,40,0,0.3);
svg: |
  crinkle texture via <feTurbulence> baseFrequency="0.04" numOctaves="3"
  blended at mix-blend-mode: overlay, opacity 0.25
raster: scanned gold-leaf texture at 1024px tile, multiplied
```

## Reactive behaviors

**Light**: warm highlight tracks pointer; on tilt, deep amber shadows emerge

**Highlight**: yes via pointer

**Depth**: no

**Parallax**: minimal

## Common implementation mistakes (avoid these)

- cool-white gold (gold is warm - pull hue toward 80-90 in OKLCH)
- smooth perfect surface (real gold leaf wrinkles)

## Examples in the wild

- religious iconography
- Nike Mag chrome
- DeFi-cosmic certificate cards

## Pairs with (prototype slugs)

- `aesthetic-dark-academia`
- `aesthetic-defi-cosmic`
- `aesthetic-urbling`
- `style-holographic`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

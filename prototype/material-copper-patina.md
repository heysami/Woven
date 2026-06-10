---
materialId: copper-patina
name: Copper with Verdigris Patina
family: digital
category: metal
surfaceFinish: matte
transparency: opaque
pairsPrototypes: [aesthetic-steampunk, aesthetic-dieselpunk, aesthetic-solarpunk, aesthetic-dark-academia]
---

# Copper with Verdigris Patina

A matte surface that reacts to light: yes — but the patina kills most specular.

## Physical behavior

**Surface finish**: matte

**Transparency**: opaque

**Reacts to light**: yes — but the patina kills most specular

**Deforms**: no

**Age / wear**: acquired patina

## Implementation strategies

```yaml
css: |
  background:
    radial-gradient(ellipse at 30% 20%, oklch(60% 0.14 35) 0%, transparent 35%),
    radial-gradient(ellipse at 70% 80%, oklch(70% 0.08 165) 0%, transparent 45%),
    oklch(40% 0.10 35);  /* copper base */
svg: |
  patina spots — <feTurbulence baseFrequency="0.02"/> + <feColorMatrix> tinted toward verdigris green
raster: real-world copper-patina photograph as the truth
```

## Reactive behaviors

**Light**: highlight only on un-patinated areas (use mask)

**Highlight**: minimal — patina absorbs light

**Depth**: none

**Parallax**: none

## Common implementation mistakes (avoid these)

- uniform green (real patina is ASYMMETRIC, lives in crevices)
- bright orange copper (it tarnishes within weeks)

## Examples in the wild

- Statue of Liberty
- vintage scientific instruments

## Pairs with (prototype slugs)

- `aesthetic-steampunk`
- `aesthetic-dieselpunk`
- `aesthetic-solarpunk`
- `aesthetic-dark-academia`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

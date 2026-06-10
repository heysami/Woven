---
materialId: film-grain-cinestill-800t
name: Film Grain — CineStill 800T (tungsten, halation, neon glow)
family: analog
category: film
surfaceFinish: matte
transparency: opaque
pairsPrototypes: [aesthetic-cyberpunk, aesthetic-vaporwave, aesthetic-cassette-futurism, recipe-editorial-magazine]
---

# Film Grain — CineStill 800T (tungsten, halation, neon glow)

A matte surface that reacts to light: yes — bright lights bloom with red halation.

## Physical behavior

**Surface finish**: matte

**Transparency**: opaque

**Reacts to light**: yes — bright lights bloom with red halation

**Deforms**: no

**Age / wear**: ageless

## Implementation strategies

```yaml
css: |
  filter: contrast(1.05) saturate(0.95);
svg: |
  <feGaussianBlur stdDeviation="2"/>
  <feColorMatrix values="1.2 0 0 0 0  0 0.9 0 0 0  0 0 0.85 0 0  0 0 0 1 0"/>
  <!-- red boom at highlights — the CineStill signature -->
webgl: |
  threshold luminance, dilate red channel, additive composite — gives
  authentic halation around lamp posts and signs
raster: CineStill scan loop
```

## Reactive behaviors

**Light**: red halation tracks high-luminance regions

**Highlight**: no separate

**Depth**: no

**Parallax**: no

## Common implementation mistakes (avoid these)

- halation everywhere (must be tied to bright spots)
- flat blue tungsten (CineStill has WARM-red halation against the cool base)

## Pairs with (prototype slugs)

- `aesthetic-cyberpunk`
- `aesthetic-vaporwave`
- `aesthetic-cassette-futurism`
- `recipe-editorial-magazine`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

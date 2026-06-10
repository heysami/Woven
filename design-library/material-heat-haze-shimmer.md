---
materialId: heat-haze-shimmer
name: Heat Haze Shimmer (mirage / hot tarmac warp)
family: digital
category: digital-effect
surfaceFinish: glossy
transparency: transparent
pairsPrototypes: [aesthetic-vaporwave, aesthetic-dreamcore, aesthetic-frutiger-aero, aesthetic-coastal-grandmother, recipe-aurora-marketing]
---

# Heat Haze Shimmer (mirage / hot tarmac warp)

A glossy surface (transparent) that reacts to light: yes and deforms: yes — low-amplitude noise displacement.

## Physical behavior

**Surface finish**: glossy

**Transparency**: transparent

**Reacts to light**: yes

**Deforms**: yes — low-amplitude noise displacement

**Age / wear**: ageless

## Implementation strategies

```yaml
css: |
  filter: blur(0.4px);
  animation: shimmer 3s ease-in-out infinite alternate;
  @keyframes shimmer { from { transform: translateY(0) } to { transform: translateY(-1px) } }
svg: |
  <feTurbulence baseFrequency="0.01 0.02" type="fractalNoise"> →
  <feDisplacementMap scale="3"> with seed animated for live shimmer.
webgl: |
  tiny UV displacement driven by Perlin noise sampled with time;
  magnitude < 0.003 of viewport.
```

## Reactive behaviors

**Light**: shimmer intensifies at bright regions

**Highlight**: pointer creates a heat source (radial shimmer amp)

**Depth**: minor — shimmer reads as atmospheric warmth

**Parallax**: continuous, slow

## Common implementation mistakes (avoid these)

- too-fast shimmer (real heat is slow)
- shimmer that crosses sharp UI edges (always damp at edges)
- over text (illegibility)

## Examples in the wild

- mirage in cinema (Mad Max Fury Road)
- desert documentary
- synthwave intro shimmer

## References

- https://en.wikipedia.org/wiki/Mirage

## Pairs with (prototype slugs)

- `aesthetic-vaporwave`
- `aesthetic-dreamcore`
- `aesthetic-frutiger-aero`
- `aesthetic-coastal-grandmother`
- `recipe-aurora-marketing`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

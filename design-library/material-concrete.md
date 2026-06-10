---
materialId: concrete
name: Concrete (raw industrial)
family: analog
category: stone
surfaceFinish: matte
transparency: opaque
pairsPrototypes: [aesthetic-web-brutalism, aesthetic-corporate-grunge, aesthetic-cassette-futurism, recipe-brutalist-web]
images:
  - src: material-concrete.png
    reason: Material fidelity sample.
---

# Concrete (raw industrial)

A matte surface.

## Physical behavior

**Surface finish**: matte

**Transparency**: opaque

**Reacts to light**: no specular

**Deforms**: no

**Age / wear**: shows wear (cracks, stains)

## Implementation strategies

```yaml
css: |
  background: oklch(70% 0.005 250);
  filter: url(#concrete);
svg: |
  <filter id="concrete">
    <feTurbulence baseFrequency="0.6" numOctaves="3"/>
    <feColorMatrix values="0 0 0 0 0.4  0 0 0 0 0.4  0 0 0 0 0.4  0 0 0 0.2 0"/>
  </filter>
raster: concrete photograph is direct
```

## Reactive behaviors

**Light**: no

**Highlight**: no

**Depth**: no

**Parallax**: no

## Common implementation mistakes (avoid these)

- too clean (concrete is messy)
- no cracks or stains
- flat colour with no aggregate visible

## Examples in the wild

- Bauhaus poster substrates
- architectural photo overlays

## Pairs with (prototype slugs)

- `aesthetic-web-brutalism`
- `aesthetic-corporate-grunge`
- `aesthetic-cassette-futurism`
- `recipe-brutalist-web`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

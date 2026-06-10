---
materialId: film-grain-portra-400
name: Film Grain — Portra 400 (colour, fine grain, warm)
family: analog
category: film
surfaceFinish: matte
transparency: opaque
pairsPrototypes: [aesthetic-coastal-grandmother, aesthetic-cottagecore, recipe-editorial-magazine, aesthetic-cottagegoth]
---

# Film Grain — Portra 400 (colour, fine grain, warm)

A matte surface that reacts to light: yes — heavier in shadow.

## Physical behavior

**Surface finish**: matte

**Transparency**: opaque

**Reacts to light**: yes — heavier in shadow

**Deforms**: no

**Age / wear**: ageless

## Implementation strategies

```yaml
css: |
  mix-blend-mode: overlay;
  opacity: 0.4;
  filter: saturate(0.92) hue-rotate(2deg);
svg: |
  finer noise — baseFrequency="1.4"
raster: scanned Portra grain looping
```

## Reactive behaviors

**Light**: luminance-aware

**Highlight**: none

**Depth**: none

**Parallax**: none

## Common implementation mistakes (avoid these)

- too coarse grain (Portra is fine)
- cold colour grade (Portra is warm)

## Examples in the wild

- Magnum portraits
- lifestyle editorial

## Pairs with (prototype slugs)

- `aesthetic-coastal-grandmother`
- `aesthetic-cottagecore`
- `recipe-editorial-magazine`
- `aesthetic-cottagegoth`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

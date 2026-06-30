---
materialId: silkscreen
name: Silkscreen / Serigraphy (textile + poster print)
family: analog
category: print
surfaceFinish: matte
scope: both
fxStack: [halftone, posterize]
transparency: opaque (ink layer)
pairsPrototypes: [aesthetic-acid-design, aesthetic-bauhaus, aesthetic-constructivism, aesthetic-corporate-grunge]
images:
  - src: material-silkscreen.png
    reason: Material fidelity sample.
---

# Silkscreen / Serigraphy (textile + poster print)

A matte surface (opaque (ink layer)).

## Physical behavior

**Surface finish**: matte

**Transparency**: opaque (ink layer)

**Reacts to light**: no

**Deforms**: no

**Age / wear**: shows wear (ink crackle on textile)

## Implementation strategies

```yaml
css: |
  /* per-color layer with slight registration shift and ink-trap edges */
  .ink-layer { mix-blend-mode: multiply; transform: translate(1px, 1px); }
svg: |
  <feMorphology operator="dilate" radius="0.5"/> for ink trap;
  <feTurbulence baseFrequency="2"/> for ink texture mask
raster: scanned silkscreen print as substrate
```

## Reactive behaviors

**Light**: no

**Highlight**: no

**Depth**: no (flat sheet)

**Parallax**: minimal

## Common implementation mistakes (avoid these)

- too-clean ink edges (real silkscreen has slight bleed)
- perfect registration
- high gloss inks

## Examples in the wild

- Andy Warhol Marilyn series
- vintage concert posters
- merch tees with cracked ink

## Pairs with (prototype slugs)

- `aesthetic-acid-design`
- `aesthetic-bauhaus`
- `aesthetic-constructivism`
- `aesthetic-corporate-grunge`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

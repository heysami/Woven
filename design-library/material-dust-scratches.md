---
materialId: dust-scratches
name: Dust + Scratches (archival distress)
family: analog
category: digital-effect
surfaceFinish: matte
transparency: translucent
pairsPrototypes: [aesthetic-vaporwave, aesthetic-cottagegoth, aesthetic-dark-academia, aesthetic-corporate-grunge, recipe-editorial-magazine]
images:
  - src: material-dust-scratches.png
    reason: Material fidelity sample.
---

# Dust + Scratches (archival distress)

A matte surface (translucent).

## Physical behavior

**Surface finish**: matte

**Transparency**: translucent

**Reacts to light**: no

**Deforms**: no

**Age / wear**: acquired patina

## Implementation strategies

```yaml
css: |
  .distress::after {
    content: '';
    position: absolute; inset: 0;
    background-image: url('dust-scratches-overlay.png');
    mix-blend-mode: screen;
    opacity: 0.4;
    pointer-events: none;
  }
svg: |
  sparse Voronoi spots + <feTurbulence> at low baseFrequency for sub-pixel scratch lines
raster: dust + scratches overlay at 2048×2048
```

## Reactive behaviors

**Light**: no

**Highlight**: no

**Depth**: no

**Parallax**: yes - dust at FIXED layer (not parallaxed) gives "screen dust

## Common implementation mistakes (avoid these)

- regular spacing of "scratches
- same overlay tiled visibly
- high opacity dust (must be subtle)

## Pairs with (prototype slugs)

- `aesthetic-vaporwave`
- `aesthetic-cottagegoth`
- `aesthetic-dark-academia`
- `aesthetic-corporate-grunge`
- `recipe-editorial-magazine`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

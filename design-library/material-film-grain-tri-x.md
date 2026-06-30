---
materialId: film-grain-tri-x
name: Film Grain - Tri-X 400 (B&W, coarse grain)
family: analog
category: film
surfaceFinish: matte
scope: medium
fxStack: [fractal-noise]
transparency: opaque
pairsPrototypes: [recipe-editorial-magazine, aesthetic-dark-academia, aesthetic-corporate-grunge, aesthetic-vaporwave, aesthetic-cottagegoth]
images:
  - src: material-film-grain-tri-x.png
    reason: Material fidelity sample.
---

# Film Grain - Tri-X 400 (B&W, coarse grain)

A matte surface that reacts to light: yes - grain heavier in shadows.

## Physical behavior

**Surface finish**: matte

**Transparency**: opaque

**Reacts to light**: yes - grain heavier in shadows

**Deforms**: no

**Age / wear**: ageless

## Implementation strategies

```yaml
css: |
  .grain { mix-blend-mode: overlay; opacity: 0.7; }
svg: |
  <feTurbulence baseFrequency="0.9" numOctaves="2" stitchTiles="stitch"/>
  <feColorMatrix values="0 0 0 0 0.7  0 0 0 0 0.7  0 0 0 0 0.7  0 0 0 1.2 -0.6"/>
webgl: |
  For LUMINANCE-AWARE grain: sample base image luminance per fragment,
  modulate noise amplitude inversely. Heavier grain in shadow regions
  mimics real silver-halide.
raster: scanned 35mm Tri-X grain at 4K, looping
video: 30fps grain video underlay (mix-blend-mode: overlay)
```

## Reactive behaviors

**Light**: grain density is luminance-driven, not pointer-driven

**Highlight**: none

**Depth**: none

**Parallax**: grain doesn't parallax (it's per-frame noise)

## Common implementation mistakes (avoid these)

- flat-opacity grain over everything (grain follows luminance)
- too-fine grain (Tri-X is COARSE)
- colour grain (Tri-X is B&W)
- static grain not animating per frame (real film moves)

## Examples in the wild

- Filmbox film emulation
- Caleb Salvadori Lightroom presets
- editorial photography

## References

- https://videovillage.com/filmbox/

## Pairs with (prototype slugs)

- `recipe-editorial-magazine`
- `aesthetic-dark-academia`
- `aesthetic-corporate-grunge`
- `aesthetic-vaporwave`
- `aesthetic-cottagegoth`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

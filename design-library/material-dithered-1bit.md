---
materialId: dithered-1bit
name: 1-bit Dither (Obra Dinn / Game Boy threshold)
family: digital
category: digital-effect
surfaceFinish: matte
transparency: opaque
pairsPrototypes: [style-pixel-bitmap, aesthetic-pixel-game-boy-mono, aesthetic-web-brutalism, aesthetic-corporate-grunge]
images:
  - src: material-dithered-1bit.png
    reason: Material fidelity sample.
---

# 1-bit Dither (Obra Dinn / Game Boy threshold)

A matte surface.

## Physical behavior

**Surface finish**: matte

**Transparency**: opaque

**Reacts to light**: no

**Deforms**: no

**Age / wear**: ageless

## Implementation strategies

```yaml
css: |
  image-rendering: pixelated;
  filter: contrast(2) saturate(0);
svg: |
  Bayer ordered dither via <feComponentTransfer> with a threshold table —
  shader-friendly because it's parallelizable.
webgl: |
  Floyd-Steinberg error-diffusion gives the highest fidelity; difficult in
  shaders (serial), so use canvas-2d for FS, WebGL for Bayer.
raster: pre-rendered 1-bit assets at native resolution
```

## Reactive behaviors

**Light**: none — threshold is fixed

**Highlight**: none

**Depth**: none

**Parallax**: stepped only

## Common implementation mistakes (avoid these)

- Bayer + Floyd-Steinberg in the same scene (pick one)
- dither over already-low-contrast content (clamps to single shade)

## Examples in the wild

- Return of the Obra Dinn
- Macintosh System 1 graphics
- 1-bit Tumblr

## References

- https://www.alanzucconi.com/2018/10/24/shader-showcase-saturday-11/

## Pairs with (prototype slugs)

- `style-pixel-bitmap`
- `aesthetic-pixel-game-boy-mono`
- `aesthetic-web-brutalism`
- `aesthetic-corporate-grunge`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

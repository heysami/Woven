---
materialId: jpeg-block-corruption
name: JPEG Block Corruption (8×8 macroblock aesthetic)
family: digital
category: digital-effect
surfaceFinish: matte
transparency: opaque
pairsPrototypes: [aesthetic-vaporwave, aesthetic-y2k-myspace, aesthetic-internetcore, aesthetic-cyberpunk, aesthetic-weirdcore, aesthetic-dreamcore]
images:
  - src: material-jpeg-block-corruption.png
    reason: Material fidelity sample.
---

# JPEG Block Corruption (8×8 macroblock aesthetic)

A matte surface.

## Physical behavior

**Surface finish**: matte

**Transparency**: opaque

**Reacts to light**: no

**Deforms**: no (the blocks SHIFT, the underlying content stays)

**Age / wear**: ageless (or feels 2003-MySpace era)

## Implementation strategies

```yaml
css: |
  /* approximation via clip-path mosaic */
  filter: contrast(1.4) saturate(1.6);
  image-rendering: pixelated;
svg: |
  <feFlood> + <feComposite> with 8×8 tile <pattern> to introduce blocky
  color shifts; combine with <feColorMatrix> for chroma subsampling.
webgl: |
  quantize uvs to 8-pixel grid: vec2 q = floor(uv * resolution / 8.) * 8. / resolution;
  sample at q for the color, sample at uv for the luminance; combine.
  This is the "true" JPEG aesthetic (block color + finer luminance).
raster: re-save the source PNG as JPEG at quality 12-18 for the authentic look
```

## Reactive behaviors

**Light**: none

**Highlight**: blocks can desaturate locally under pointer (hint of decay)

**Depth**: none — JPEG corruption is structural

**Parallax**: stepped — block-grid feels stuck

## Common implementation mistakes (avoid these)

- blocks that don't align to an 8×8 grid (real JPEG is rigid)
- smooth gradients between blocks (real JPEG has hard block edges)
- applying to text (illegibility)

## Examples in the wild

- early MySpace profile photos
- art of Petra Cortright early-era
- aesthetic Tumblr 2012

## References

- https://en.wikipedia.org/wiki/Compression_artifact

## Pairs with (prototype slugs)

- `aesthetic-vaporwave`
- `aesthetic-y2k-myspace`
- `aesthetic-internetcore`
- `aesthetic-cyberpunk`
- `aesthetic-weirdcore`
- `aesthetic-dreamcore`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

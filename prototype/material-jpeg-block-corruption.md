# JPEG Block Corruption (8×8 macroblock aesthetic) (material)

**Tag:** material-jpeg-block-corruption  ·  **Family:** digital  ·  **Category:** digital-effect · matte

A matte digital surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: jpeg-block-corruption
  name: JPEG Block Corruption (8×8 macroblock aesthetic)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: no
    deforms: no (the blocks SHIFT, the underlying content stays)
    age: ageless (or feels 2003-MySpace era)
  implementationStrategies:
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
  reactiveBehaviors:
    light: none
    highlight: blocks can desaturate locally under pointer (hint of decay)
    depth: none — JPEG corruption is structural
    parallax: stepped — block-grid feels stuck
  pairsWith:
    prototypeStyles: [aesthetic-vaporwave, aesthetic-y2k-myspace, aesthetic-internetcore, aesthetic-cyberpunk, aesthetic-weirdcore, aesthetic-dreamcore]
  killsTheIllusion:
    - blocks that don't align to an 8×8 grid (real JPEG is rigid)
    - smooth gradients between blocks (real JPEG has hard block edges)
    - applying to text (illegibility)
  examples:
    - early MySpace profile photos
    - art of Petra Cortright early-era
    - aesthetic Tumblr 2012
  references:
    - https://en.wikipedia.org/wiki/Compression_artifact
```

## Common implementation mistakes (avoid these)

- blocks that don't align to an 8×8 grid (real JPEG is rigid)
- smooth gradients between blocks (real JPEG has hard block edges)
- applying to text (illegibility)

## Pairs with (prototype slugs)

- `aesthetic-vaporwave`
- `aesthetic-y2k-myspace`
- `aesthetic-internetcore`
- `aesthetic-cyberpunk`
- `aesthetic-weirdcore`
- `aesthetic-dreamcore`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 1054–1094 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

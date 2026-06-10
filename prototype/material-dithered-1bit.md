# 1-bit Dither (Obra Dinn / Game Boy threshold) (material)

**Tag:** material-dithered-1bit  ·  **Family:** digital  ·  **Category:** digital-effect · matte

A matte digital surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: dithered-1bit
  name: 1-bit Dither (Obra Dinn / Game Boy threshold)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: no
    deforms: no
    age: ageless
  implementationStrategies:
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
  reactiveBehaviors:
    light: none — threshold is fixed
    highlight: none
    depth: none
    parallax: stepped only
  pairsWith:
    prototypeStyles: [style-pixel-bitmap, aesthetic-pixel-game-boy-mono, aesthetic-web-brutalism, aesthetic-corporate-grunge]
  killsTheIllusion:
    - Bayer + Floyd-Steinberg in the same scene (pick one)
    - dither over already-low-contrast content (clamps to single shade)
  examples:
    - Return of the Obra Dinn
    - Macintosh System 1 graphics
    - 1-bit Tumblr
  references:
    - https://www.alanzucconi.com/2018/10/24/shader-showcase-saturday-11/
```

## Common implementation mistakes (avoid these)

- Bayer + Floyd-Steinberg in the same scene (pick one)
- dither over already-low-contrast content (clamps to single shade)

## Pairs with (prototype slugs)

- `style-pixel-bitmap`
- `aesthetic-pixel-game-boy-mono`
- `aesthetic-web-brutalism`
- `aesthetic-corporate-grunge`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 885–922 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

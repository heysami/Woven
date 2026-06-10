# Film Grain — Tri-X 400 (B&W, coarse grain) (material)

**Tag:** material-film-grain-tri-x  ·  **Family:** analog  ·  **Category:** film · matte

A matte analog surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: film-grain-tri-x
  name: Film Grain — Tri-X 400 (B&W, coarse grain)
  family: analog
  category: film
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: yes — grain heavier in shadows
    deforms: no
    age: ageless
  implementationStrategies:
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
  reactiveBehaviors:
    light: grain density is luminance-driven, not pointer-driven
    highlight: none
    depth: none
    parallax: grain doesn't parallax (it's per-frame noise)
  pairsWith:
    prototypeStyles: [recipe-editorial-magazine, aesthetic-dark-academia, aesthetic-corporate-grunge, aesthetic-vaporwave, aesthetic-cottagegoth]
  killsTheIllusion:
    - flat-opacity grain over everything (grain follows luminance)
    - too-fine grain (Tri-X is COARSE)
    - colour grain (Tri-X is B&W)
    - static grain not animating per frame (real film moves)
  examples:
    - Filmbox film emulation
    - Caleb Salvadori Lightroom presets
    - editorial photography
  references:
    - https://videovillage.com/filmbox/
```

## Common implementation mistakes (avoid these)

- flat-opacity grain over everything (grain follows luminance)
- too-fine grain (Tri-X is COARSE)
- colour grain (Tri-X is B&W)

## Pairs with (prototype slugs)

- `recipe-editorial-magazine`
- `aesthetic-dark-academia`
- `aesthetic-corporate-grunge`
- `aesthetic-vaporwave`
- `aesthetic-cottagegoth`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 2585–2625 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

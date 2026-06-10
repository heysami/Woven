# Photocopy / Xerox (toner crush) (material)

**Tag:** material-photocopy-xerox  ·  **Family:** analog  ·  **Category:** print · matte

A matte analog surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: photocopy-xerox
  name: Photocopy / Xerox (toner crush)
  family: analog
  category: print
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: no
    deforms: no
    age: shows wear (streaks, dirt)
  implementationStrategies:
    css: |
      filter: grayscale(1) contrast(1.8);
      mix-blend-mode: multiply;
    svg: |
      <feComponentTransfer> with steep sigmoid for toner crush;
      <feGaussianBlur stdDeviation="0.4"/> + <feColorMatrix> threshold for toner spread
    webgl: |
      sigmoid contrast → grayscale → noise overlay → soft blur → threshold —
      matches CopyCat / Vayce algorithms
    raster: photocopy texture overlays (Indieground packs) at multiply
  reactiveBehaviors:
    light: no
    highlight: no
    depth: no
    parallax: stepped
  pairsWith:
    prototypeStyles: [aesthetic-corporate-grunge, aesthetic-cottagegoth, aesthetic-web-brutalism, aesthetic-acid-graphics, aesthetic-curly-girly]
  killsTheIllusion:
    - clean colour photocopy (the look is mono-thresholded)
    - no streaks or dirt (real Xerox is messy)
    - smooth midtones (toner crushes midtones to black/white)
  examples:
    - punk flyers
    - underground zines
    - photocopy-noise stock packs (Indieground)
  references:
    - https://vayce.app/tools/photocopy-scan-lines-effect/
    - https://effect.app/effects/xerox
```

## Common implementation mistakes (avoid these)

- clean colour photocopy (the look is mono-thresholded)
- no streaks or dirt (real Xerox is messy)
- smooth midtones (toner crushes midtones to black/white)

## Pairs with (prototype slugs)

- `aesthetic-corporate-grunge`
- `aesthetic-cottagegoth`
- `aesthetic-web-brutalism`
- `aesthetic-acid-graphics`
- `aesthetic-curly-girly`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 2040–2079 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

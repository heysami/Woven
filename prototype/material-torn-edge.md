# Torn Edge (paper / fabric / film) (material)

**Tag:** material-torn-edge  ·  **Family:** analog  ·  **Category:** digital-effect · matte

A matte analog surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: torn-edge
  name: Torn Edge (paper / fabric / film)
  family: analog
  category: digital-effect
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: no
    deforms: yes
    age: ageless (or shows wear)
  implementationStrategies:
    css: |
      mask-image: url(torn-edge.svg);
      mask-size: cover;
      filter: drop-shadow(0 2px 1px rgba(0,0,0,0.18));
    svg: |
      irregular fractal-noise mask along one edge:
      <feTurbulence baseFrequency="0.06"/> + <feComponentTransfer> threshold
    raster: torn-paper PNG with alpha
  reactiveBehaviors:
    light: small shadow on hover
    highlight: no
    depth: hover lift 2px
    parallax: optional
  pairsWith:
    prototypeStyles: [style-raster-cutout, aesthetic-cottagecore, aesthetic-y2k-myspace, aesthetic-corporate-grunge]
  killsTheIllusion:
    - rounded "torn" edges (real tear is irregular and SHARP at peaks)
    - same tear pattern repeated
  examples:
    - Hack Club Scrapbook
    - SSENSE editorial torn type
```

### 4.8 Wood, stone, organic family

```yaml
```

## Common implementation mistakes (avoid these)

- rounded "torn" edges (real tear is irregular and SHARP at peaks)
- same tear pattern repeated

## Pairs with (prototype slugs)

- `style-raster-cutout`
- `aesthetic-cottagecore`
- `aesthetic-y2k-myspace`
- `aesthetic-corporate-grunge`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 2834–2870 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

# Ink Bleed (fountain pen / felt-tip on uncoated) (material)

**Tag:** material-ink-bleed-on-paper  ·  **Family:** analog  ·  **Category:** ink · matte

A matte analog surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: ink-bleed-on-paper
  name: Ink Bleed (fountain pen / felt-tip on uncoated)
  family: analog
  category: ink
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: no
    deforms: no
    age: ageless
  implementationStrategies:
    css: |
      filter: url(#inkBleed);
    svg: |
      <filter id="inkBleed">
        <feMorphology operator="dilate" radius="0.4"/>
        <feGaussianBlur stdDeviation="0.6"/>
        <feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 12 -4"/>
      </filter>
    raster: scanned ink for the highest fidelity
  reactiveBehaviors:
    light: no
    highlight: no
    depth: no
    parallax: no
  pairsWith:
    prototypeStyles: [style-raster-cutout, style-doodle, aesthetic-cottagecore, aesthetic-cottagegoth, aesthetic-dark-academia]
  killsTheIllusion:
    - perfect type (ink bleeds organically)
    - uniform stroke width (ink width varies with paper absorbency)
```

## Common implementation mistakes (avoid these)

- perfect type (ink bleeds organically)
- uniform stroke width (ink width varies with paper absorbency)

## Pairs with (prototype slugs)

- `style-raster-cutout`
- `style-doodle`
- `aesthetic-cottagecore`
- `aesthetic-cottagegoth`
- `aesthetic-dark-academia`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 2202–2232 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

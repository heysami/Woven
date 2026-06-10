# Linen Weave (Apple-linen / textbook substrate) (material)

**Tag:** material-linen-weave  ·  **Family:** analog  ·  **Category:** fabric · matte

A matte analog surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: linen-weave
  name: Linen Weave (Apple-linen / textbook substrate)
  family: analog
  category: fabric
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: no specular
    deforms: yes — fabric drapes
    age: ageless
  implementationStrategies:
    css: |
      background:
        repeating-linear-gradient(0deg,
          transparent 0px,
          rgba(0,0,0,0.04) 1px,
          transparent 2px
        ),
        repeating-linear-gradient(90deg,
          transparent 0px,
          rgba(0,0,0,0.04) 1px,
          transparent 2px
        ),
        oklch(80% 0.02 80);  /* warm beige */
    svg: <feTurbulence baseFrequency="2"/> noise atop the weave
    raster: scanned linen as ground truth
  reactiveBehaviors:
    light: no
    highlight: no
    depth: very subtle skew on scroll (drape)
    parallax: no
  pairsWith:
    prototypeStyles: [style-skeuomorphism (iOS Game Center linen), aesthetic-cottagecore, aesthetic-coastal-grandmother, aesthetic-dark-academia]
  killsTheIllusion:
    - the weave at huge scale (you can't see it)
    - the weave at sub-pixel scale (Moiré)
    - no warmth in the colour (linen is naturally warm-cream)
  examples:
    - iOS Game Center
    - Apple Notification Center pre-iOS-7
    - book endpapers
```

## Common implementation mistakes (avoid these)

- the weave at huge scale (you can't see it)
- the weave at sub-pixel scale (Moiré)
- no warmth in the colour (linen is naturally warm-cream)

## Pairs with (prototype slugs)

- `style-skeuomorphism (iOS Game Center linen)`
- `aesthetic-cottagecore`
- `aesthetic-coastal-grandmother`
- `aesthetic-dark-academia`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 2302–2343 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

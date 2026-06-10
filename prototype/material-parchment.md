# Parchment / Vellum (animal hide, premium document) (material)

**Tag:** material-parchment  ·  **Family:** analog  ·  **Category:** paper · matte

A matte analog surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: parchment
  name: Parchment / Vellum (animal hide, premium document)
  family: analog
  category: paper
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: no specular but visible thickness
    deforms: yes — curls dramatically at corners
    age: acquired patina (yellowing, blotches)
  implementationStrategies:
    css: |
      background:
        radial-gradient(ellipse at 30% 20%, oklch(94% 0.04 70) 0%, transparent 50%),
        radial-gradient(ellipse at 80% 80%, oklch(86% 0.06 50) 0%, transparent 50%),
        oklch(91% 0.05 60);
      filter: contrast(1.05);
    svg: |
      blotch turbulence pattern at low opacity
    raster: real parchment scan ideal
  reactiveBehaviors:
    light: edge highlight only
    highlight: no
    depth: corner curl prominent
    parallax: no
  pairsWith:
    prototypeStyles: [aesthetic-dark-academia, aesthetic-steampunk, aesthetic-defi-cosmic (achievement certificates)]
  killsTheIllusion:
    - uniform colour (parchment is naturally splotchy)
    - perfect rectangle (parchment has irregular hand-cut edges)
```

## Common implementation mistakes (avoid these)

- uniform colour (parchment is naturally splotchy)
- perfect rectangle (parchment has irregular hand-cut edges)

## Pairs with (prototype slugs)

- `aesthetic-dark-academia`
- `aesthetic-steampunk`
- `aesthetic-defi-cosmic (achievement certificates)`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 1847–1877 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

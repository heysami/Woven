# Paper with Watercolor (botanical illustration substrate) (material)

**Tag:** material-paper-with-watercolor  ·  **Family:** hybrid  ·  **Category:** paper · matte

A matte hybrid surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: paper-with-watercolor
  name: Paper with Watercolor (botanical illustration substrate)
  family: hybrid
  category: paper
  physicalBehavior:
    surfaceFinish: matte
    transparency: translucent (washes)
    reactsToLight: no
    deforms: yes
    age: shows wear
  implementationStrategies:
    css: |
      background: var(--paper);
    svg: |
      paper grain layer + watercolor wash filter layer; multiply blend
    raster: scanned watercolor on watercolor paper
  reactiveBehaviors:
    light: no
    highlight: no
    depth: no
    parallax: paper static; wash subtle scroll-bind
  pairsWith:
    prototypeStyles: [aesthetic-cottagecore, aesthetic-coastal-grandmother, aesthetic-fairycore]
  killsTheIllusion:
    - watercolor without paper texture (looks plastic)
    - watercolor with hard edges
  examples:
    - Beatrix Potter
    - children's book illustration
```

## Common implementation mistakes (avoid these)

- watercolor without paper texture (looks plastic)
- watercolor with hard edges

## Pairs with (prototype slugs)

- `aesthetic-cottagecore`
- `aesthetic-coastal-grandmother`
- `aesthetic-fairycore`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 3105–3134 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

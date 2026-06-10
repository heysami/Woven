# Holographic-Paper (iridescent foil on textured paper) (material)

**Tag:** material-holographic-paper  ·  **Family:** hybrid  ·  **Category:** iridescent · glossy

A glossy hybrid surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: holographic-paper
  name: Holographic-Paper (iridescent foil on textured paper)
  family: hybrid
  category: iridescent
  physicalBehavior:
    surfaceFinish: glossy
    transparency: opaque
    reactsToLight: yes — strong on foil, none on paper
    deforms: yes — paper underneath
    age: ageless
  implementationStrategies:
    css: |
      /* foil regions get the holographic recipe; rest is paper */
      background:
        url('paper-grain.jpg'),
        conic-gradient(in oklch from 45deg, /* full iridescence */) ;
    raster: paper texture as ground; holographic mask
  reactiveBehaviors:
    light: foil reacts to pointer/gyro; paper doesn't
    highlight: yes — masked to foil region only
    depth: paper deformation possible
    parallax: paper static; foil rotates with gyro
  pairsWith:
    prototypeStyles: [style-holographic, aesthetic-y2k-futurism, recipe-editorial-magazine]
  killsTheIllusion:
    - iridescence over the whole card (must be foil REGIONS, like a Pokemon card)
  examples:
    - foil-stamped business cards
    - Pokemon card (the canonical reference)
```

## Common implementation mistakes (avoid these)

- iridescence over the whole card (must be foil REGIONS, like a Pokemon card)

## Pairs with (prototype slugs)

- `style-holographic`
- `aesthetic-y2k-futurism`
- `recipe-editorial-magazine`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 3075–3104 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

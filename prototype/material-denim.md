# Denim (twill weave, indigo fade) (material)

**Tag:** material-denim  ·  **Family:** analog  ·  **Category:** fabric · matte

A matte analog surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: denim
  name: Denim (twill weave, indigo fade)
  family: analog
  category: fabric
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: no specular
    deforms: yes — soft drape
    age: acquired patina (whiskers, fade at stress points)
  implementationStrategies:
    css: |
      background:
        repeating-linear-gradient(45deg,
          oklch(35% 0.10 250) 0px,
          oklch(40% 0.10 250) 2px,
          oklch(33% 0.10 250) 4px
        );
    svg: noise + slight horizontal-fade gradient at wear points (whiskers)
    raster: scanned denim is the truth
  reactiveBehaviors:
    light: no
    highlight: no
    depth: yes — drape
    parallax: minimal
  pairsWith:
    prototypeStyles: [aesthetic-y2k-myspace, aesthetic-cottagecore, aesthetic-corporate-grunge]
  killsTheIllusion:
    - perfect uniform indigo (denim is uneven)
    - no twill direction visible
    - no fade at stress points
  examples:
    - Levi's tab stitching
    - fashion editorial denim closeups
```

## Common implementation mistakes (avoid these)

- perfect uniform indigo (denim is uneven)
- no twill direction visible
- no fade at stress points

## Pairs with (prototype slugs)

- `aesthetic-y2k-myspace`
- `aesthetic-cottagecore`
- `aesthetic-corporate-grunge`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 2344–2378 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

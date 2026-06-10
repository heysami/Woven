# Coated Glossy Paper (magazine cover stock) (material)

**Tag:** material-coated-glossy-paper  ·  **Family:** analog  ·  **Category:** paper · glossy

A glossy analog surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: coated-glossy-paper
  name: Coated Glossy Paper (magazine cover stock)
  family: analog
  category: paper
  physicalBehavior:
    surfaceFinish: glossy
    transparency: opaque
    reactsToLight: yes — specular sheen
    deforms: minimal
    age: ageless (or shows fingerprints)
  implementationStrategies:
    css: |
      background:
        linear-gradient(115deg, rgba(255,255,255,0.18) 0%, transparent 35%),
        url('coated-paper-1024.jpg') center/512px,
        oklch(98% 0.005 80);
      background-blend-mode: overlay, multiply, normal;
    raster: scanned coated stock; finer grain than uncoated
  reactiveBehaviors:
    light: glossy sheen tracks pointer at low intensity
    highlight: yes (linear sweep on hover, 0.2 opacity)
    depth: minimal
    parallax: minimal
  pairsWith:
    prototypeStyles: [recipe-editorial-magazine, aesthetic-y2k-memphis-loud, aesthetic-coastal-grandmother]
  killsTheIllusion:
    - the same fibers as uncoated (coated is much smoother)
    - missing the sheen on hover
  examples:
    - Vogue covers
    - National Geographic
    - airline in-flight magazines
```

## Common implementation mistakes (avoid these)

- the same fibers as uncoated (coated is much smoother)
- missing the sheen on hover

## Pairs with (prototype slugs)

- `recipe-editorial-magazine`
- `aesthetic-y2k-memphis-loud`
- `aesthetic-coastal-grandmother`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 1782–1814 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

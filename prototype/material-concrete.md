# Concrete (raw industrial) (material)

**Tag:** material-concrete  ·  **Family:** analog  ·  **Category:** stone · matte

A matte analog surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: concrete
  name: Concrete (raw industrial)
  family: analog
  category: stone
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: no specular
    deforms: no
    age: shows wear (cracks, stains)
  implementationStrategies:
    css: |
      background: oklch(70% 0.005 250);
      filter: url(#concrete);
    svg: |
      <filter id="concrete">
        <feTurbulence baseFrequency="0.6" numOctaves="3"/>
        <feColorMatrix values="0 0 0 0 0.4  0 0 0 0 0.4  0 0 0 0 0.4  0 0 0 0.2 0"/>
      </filter>
    raster: concrete photograph is direct
  reactiveBehaviors:
    light: no
    highlight: no
    depth: no
    parallax: no
  pairsWith:
    prototypeStyles: [aesthetic-web-brutalism, aesthetic-corporate-grunge, aesthetic-cassette-futurism, recipe-brutalist-web]
  killsTheIllusion:
    - too clean (concrete is messy)
    - no cracks or stains
    - flat colour with no aggregate visible
  examples:
    - Bauhaus poster substrates
    - architectural photo overlays
```

---

## 5. Hybrid / cross-over materials

Materials that combine digital + analog grammar — each one is a stack of two or more materials from §3 or §4, applied as a single committed surface.

```yaml
```

## Common implementation mistakes (avoid these)

- too clean (concrete is messy)
- no cracks or stains
- flat colour with no aggregate visible

## Pairs with (prototype slugs)

- `aesthetic-web-brutalism`
- `aesthetic-corporate-grunge`
- `aesthetic-cassette-futurism`
- `recipe-brutalist-web`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 2943–2985 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

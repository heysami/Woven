# Copper with Verdigris Patina (material)

**Tag:** material-copper-patina  ·  **Family:** digital  ·  **Category:** metal · matte

A matte digital surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: copper-patina
  name: Copper with Verdigris Patina
  family: digital
  category: metal
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: yes — but the patina kills most specular
    deforms: no
    age: acquired patina
  implementationStrategies:
    css: |
      background:
        radial-gradient(ellipse at 30% 20%, oklch(60% 0.14 35) 0%, transparent 35%),
        radial-gradient(ellipse at 70% 80%, oklch(70% 0.08 165) 0%, transparent 45%),
        oklch(40% 0.10 35);  /* copper base */
    svg: |
      patina spots — <feTurbulence baseFrequency="0.02"/> + <feColorMatrix> tinted toward verdigris green
    raster: real-world copper-patina photograph as the truth
  reactiveBehaviors:
    light: highlight only on un-patinated areas (use mask)
    highlight: minimal — patina absorbs light
    depth: none
    parallax: none
  pairsWith:
    prototypeStyles: [aesthetic-steampunk, aesthetic-dieselpunk, aesthetic-solarpunk, aesthetic-dark-academia]
  killsTheIllusion:
    - uniform green (real patina is ASYMMETRIC, lives in crevices)
    - bright orange copper (it tarnishes within weeks)
  examples:
    - Statue of Liberty
    - vintage scientific instruments
```

### 3.4 Iridescent and dichroic family

```yaml
```

## Common implementation mistakes (avoid these)

- uniform green (real patina is ASYMMETRIC, lives in crevices)
- bright orange copper (it tarnishes within weeks)

## Pairs with (prototype slugs)

- `aesthetic-steampunk`
- `aesthetic-dieselpunk`
- `aesthetic-solarpunk`
- `aesthetic-dark-academia`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 567–603 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

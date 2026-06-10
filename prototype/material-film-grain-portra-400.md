# Film Grain — Portra 400 (colour, fine grain, warm) (material)

**Tag:** material-film-grain-portra-400  ·  **Family:** analog  ·  **Category:** film · matte

A matte analog surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: film-grain-portra-400
  name: Film Grain — Portra 400 (colour, fine grain, warm)
  family: analog
  category: film
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: yes — heavier in shadow
    deforms: no
    age: ageless
  implementationStrategies:
    css: |
      mix-blend-mode: overlay;
      opacity: 0.4;
      filter: saturate(0.92) hue-rotate(2deg);
    svg: |
      finer noise — baseFrequency="1.4"
    raster: scanned Portra grain looping
  reactiveBehaviors:
    light: luminance-aware
    highlight: none
    depth: none
    parallax: none
  pairsWith:
    prototypeStyles: [aesthetic-coastal-grandmother, aesthetic-cottagecore, recipe-editorial-magazine, aesthetic-cottagegoth]
  killsTheIllusion:
    - too coarse grain (Portra is fine)
    - cold colour grade (Portra is warm)
  examples:
    - Magnum portraits
    - lifestyle editorial
```

## Common implementation mistakes (avoid these)

- too coarse grain (Portra is fine)
- cold colour grade (Portra is warm)

## Pairs with (prototype slugs)

- `aesthetic-coastal-grandmother`
- `aesthetic-cottagecore`
- `recipe-editorial-magazine`
- `aesthetic-cottagegoth`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 2626–2657 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

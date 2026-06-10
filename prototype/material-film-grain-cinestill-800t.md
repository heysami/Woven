# Film Grain — CineStill 800T (tungsten, halation, neon glow) (material)

**Tag:** material-film-grain-cinestill-800t  ·  **Family:** analog  ·  **Category:** film · matte

A matte analog surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: film-grain-cinestill-800t
  name: Film Grain — CineStill 800T (tungsten, halation, neon glow)
  family: analog
  category: film
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: yes — bright lights bloom with red halation
    deforms: no
    age: ageless
  implementationStrategies:
    css: |
      filter: contrast(1.05) saturate(0.95);
    svg: |
      <feGaussianBlur stdDeviation="2"/>
      <feColorMatrix values="1.2 0 0 0 0  0 0.9 0 0 0  0 0 0.85 0 0  0 0 0 1 0"/>
      <!-- red boom at highlights — the CineStill signature -->
    webgl: |
      threshold luminance, dilate red channel, additive composite — gives
      authentic halation around lamp posts and signs
    raster: CineStill scan loop
  reactiveBehaviors:
    light: red halation tracks high-luminance regions
    highlight: no separate
    depth: no
    parallax: no
  pairsWith:
    prototypeStyles: [aesthetic-cyberpunk, aesthetic-vaporwave, aesthetic-cassette-futurism, recipe-editorial-magazine]
  killsTheIllusion:
    - halation everywhere (must be tied to bright spots)
    - flat blue tungsten (CineStill has WARM-red halation against the cool base)
```

## Common implementation mistakes (avoid these)

- halation everywhere (must be tied to bright spots)
- flat blue tungsten (CineStill has WARM-red halation against the cool base)

## Pairs with (prototype slugs)

- `aesthetic-cyberpunk`
- `aesthetic-vaporwave`
- `aesthetic-cassette-futurism`
- `recipe-editorial-magazine`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 2658–2689 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

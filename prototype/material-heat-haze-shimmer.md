# Heat Haze Shimmer (mirage / hot tarmac warp) (material)

**Tag:** material-heat-haze-shimmer  ·  **Family:** digital  ·  **Category:** digital-effect · glossy

A glossy digital surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: heat-haze-shimmer
  name: Heat Haze Shimmer (mirage / hot tarmac warp)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: glossy
    transparency: transparent
    reactsToLight: yes
    deforms: yes — low-amplitude noise displacement
    age: ageless
  implementationStrategies:
    css: |
      filter: blur(0.4px);
      animation: shimmer 3s ease-in-out infinite alternate;
      @keyframes shimmer { from { transform: translateY(0) } to { transform: translateY(-1px) } }
    svg: |
      <feTurbulence baseFrequency="0.01 0.02" type="fractalNoise"> →
      <feDisplacementMap scale="3"> with seed animated for live shimmer.
    webgl: |
      tiny UV displacement driven by Perlin noise sampled with time;
      magnitude < 0.003 of viewport.
  reactiveBehaviors:
    light: shimmer intensifies at bright regions
    highlight: pointer creates a heat source (radial shimmer amp)
    depth: minor — shimmer reads as atmospheric warmth
    parallax: continuous, slow
  pairsWith:
    prototypeStyles: [aesthetic-vaporwave, aesthetic-dreamcore, aesthetic-frutiger-aero, aesthetic-coastal-grandmother, recipe-aurora-marketing]
  killsTheIllusion:
    - too-fast shimmer (real heat is slow)
    - shimmer that crosses sharp UI edges (always damp at edges)
    - over text (illegibility)
  examples:
    - mirage in cinema (Mad Max Fury Road)
    - desert documentary
    - synthwave intro shimmer
  references:
    - https://en.wikipedia.org/wiki/Mirage
```

## Common implementation mistakes (avoid these)

- too-fast shimmer (real heat is slow)
- shimmer that crosses sharp UI edges (always damp at edges)
- over text (illegibility)

## Pairs with (prototype slugs)

- `aesthetic-vaporwave`
- `aesthetic-dreamcore`
- `aesthetic-frutiger-aero`
- `aesthetic-coastal-grandmother`
- `recipe-aurora-marketing`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 1312–1350 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

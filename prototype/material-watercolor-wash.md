# Watercolor Wash (wet-on-wet, granulation) (material)

**Tag:** material-watercolor-wash  ·  **Family:** analog  ·  **Category:** wash · matte

A matte analog surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: watercolor-wash
  name: Watercolor Wash (wet-on-wet, granulation)
  family: analog
  category: wash
  physicalBehavior:
    surfaceFinish: matte
    transparency: translucent (multiple washes)
    reactsToLight: no
    deforms: no
    age: ageless
  implementationStrategies:
    css: |
      mix-blend-mode: multiply;
      filter: url(#watercolor);
    svg: |
      <filter id="watercolor">
        <feTurbulence type="turbulence" baseFrequency="0.01 0.05" numOctaves="2"/>
        <feDisplacementMap in="SourceGraphic" scale="8"/>
        <feGaussianBlur stdDeviation="0.4"/>
      </filter>
      <!-- Higher numOctaves for granulation; scale ≥10 starts shifting too much -->
    raster: scanned real watercolor wash as substrate
  reactiveBehaviors:
    light: no
    highlight: no
    depth: no (paper underneath has depth)
    parallax: yes — washes layer at different scroll rates
  pairsWith:
    prototypeStyles: [aesthetic-cottagecore, aesthetic-coastal-grandmother, aesthetic-fairycore, style-doodle]
  killsTheIllusion:
    - hard edges (watercolor bleeds — edges must be soft)
    - perfectly even wash (real watercolor pools at edges)
    - no paper substrate visible through the wash
  examples:
    - Beatrix Potter botanical plates
    - children's book illustration
    - botanical print apothecary brands
  references:
    - https://codepen.io/origan/pen/YOGpjp
    - https://andyjakubowski.com/tutorial/ink-bleed-effect-with-svg-filters
```

## Common implementation mistakes (avoid these)

- hard edges (watercolor bleeds — edges must be soft)
- perfectly even wash (real watercolor pools at edges)
- no paper substrate visible through the wash

## Pairs with (prototype slugs)

- `aesthetic-cottagecore`
- `aesthetic-coastal-grandmother`
- `aesthetic-fairycore`
- `style-doodle`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 2128–2168 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

# Vellum / Tracing Paper Translucency (material)

**Tag:** material-vellum-translucency  ·  **Family:** digital  ·  **Category:** glass · matte

A matte digital surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: vellum-translucency
  name: Vellum / Tracing Paper Translucency
  family: digital
  category: glass
  physicalBehavior:
    surfaceFinish: matte
    transparency: translucent
    reactsToLight: no specular — light scatters
    deforms: no
    age: ageless
  implementationStrategies:
    css: |
      background: rgba(252,250,245,0.62);
      backdrop-filter: blur(8px) saturate(80%);  /* desaturate, not boost */
      box-shadow: 0 2px 8px rgba(60,40,20,0.08);
      /* WARM tone, not cool — vellum is yellowish */
    svg: |
      <filter id="vellumGrain">
        <feTurbulence baseFrequency="0.9" numOctaves="2"/>
        <feColorMatrix values="0 0 0 0 0.95  0 0 0 0 0.93  0 0 0 0 0.88  0 0 0 0.08 0"/>
      </filter>
      /* paper-fibre noise at 8% opacity over the panel */
    raster: optional 2048px vellum scan multiplied at low opacity
  reactiveBehaviors:
    light: minimal; vellum doesn't glint
    highlight: none
    depth: 1px lift on hover only
    parallax: minimal
  pairsWith:
    prototypeStyles: [style-serif-warm-paper, aesthetic-cottagecore, aesthetic-cottagegoth, aesthetic-dark-academia]
  killsTheIllusion:
    - cool/blue blur (vellum is warm)
    - high saturate boost (vellum desaturates, doesn't intensify)
    - sharp specular highlight (matte material can't glint)
  examples:
    - architectural drawing overlays
    - wedding invitation overlays
    - Apple visionOS "Plate" material (when configured matte)
```

### 3.2 Plastic and ceramic family

```yaml
```

## Common implementation mistakes (avoid these)

- cool/blue blur (vellum is warm)
- high saturate boost (vellum desaturates, doesn't intensify)
- sharp specular highlight (matte material can't glint)

## Pairs with (prototype slugs)

- `style-serif-warm-paper`
- `aesthetic-cottagecore`
- `aesthetic-cottagegoth`
- `aesthetic-dark-academia`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 218–260 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

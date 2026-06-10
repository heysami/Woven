# Silkscreen / Serigraphy (textile + poster print) (material)

**Tag:** material-silkscreen  ·  **Family:** analog  ·  **Category:** print · matte

A matte analog surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: silkscreen
  name: Silkscreen / Serigraphy (textile + poster print)
  family: analog
  category: print
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque (ink layer)
    reactsToLight: no
    deforms: no
    age: shows wear (ink crackle on textile)
  implementationStrategies:
    css: |
      /* per-color layer with slight registration shift and ink-trap edges */
      .ink-layer { mix-blend-mode: multiply; transform: translate(1px, 1px); }
    svg: |
      <feMorphology operator="dilate" radius="0.5"/> for ink trap;
      <feTurbulence baseFrequency="2"/> for ink texture mask
    raster: scanned silkscreen print as substrate
  reactiveBehaviors:
    light: no
    highlight: no
    depth: no (flat sheet)
    parallax: minimal
  pairsWith:
    prototypeStyles: [aesthetic-acid-design, aesthetic-bauhaus, aesthetic-constructivism, aesthetic-corporate-grunge]
  killsTheIllusion:
    - too-clean ink edges (real silkscreen has slight bleed)
    - perfect registration
    - high gloss inks
  examples:
    - Andy Warhol Marilyn series
    - vintage concert posters
    - merch tees with cracked ink
```

## Common implementation mistakes (avoid these)

- too-clean ink edges (real silkscreen has slight bleed)
- perfect registration
- high gloss inks

## Pairs with (prototype slugs)

- `aesthetic-acid-design`
- `aesthetic-bauhaus`
- `aesthetic-constructivism`
- `aesthetic-corporate-grunge`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 1967–2000 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

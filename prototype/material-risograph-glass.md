# Risograph-Glass (frosted glass under riso grain) (material)

**Tag:** material-risograph-glass  ·  **Family:** hybrid  ·  **Category:** glass · matte

A matte hybrid surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: risograph-glass
  name: Risograph-Glass (frosted glass under riso grain)
  family: hybrid
  category: glass
  physicalBehavior:
    surfaceFinish: matte
    transparency: translucent
    reactsToLight: minimal
    deforms: no
    age: ageless
  implementationStrategies:
    css: |
      backdrop-filter: blur(20px) saturate(160%);
      mix-blend-mode: multiply;
    svg: |
      stack riso ink halftone over glass panel, slight offset
    raster: riso grain overlay + photographic substrate
  reactiveBehaviors:
    light: no — riso kills the gloss
    highlight: no
    depth: hover lift only
    parallax: substrate parallaxes
  pairsWith:
    prototypeStyles: [aesthetic-acid-design, aesthetic-corporate-grunge, aesthetic-y2k-myspace]
  killsTheIllusion:
    - glass sheen visible through the riso (riso must dominate top)
```

## Common implementation mistakes (avoid these)

- glass sheen visible through the riso (riso must dominate top)

## Pairs with (prototype slugs)

- `aesthetic-acid-design`
- `aesthetic-corporate-grunge`
- `aesthetic-y2k-myspace`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 3019–3045 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

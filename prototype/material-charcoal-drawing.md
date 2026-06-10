# Charcoal Drawing (smudged, expressive) (material)

**Tag:** material-charcoal-drawing  ·  **Family:** analog  ·  **Category:** ink · matte

A matte analog surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: charcoal-drawing
  name: Charcoal Drawing (smudged, expressive)
  family: analog
  category: ink
  physicalBehavior:
    surfaceFinish: matte
    transparency: translucent
    reactsToLight: no
    deforms: no
    age: shows wear (smudge)
  implementationStrategies:
    css: |
      filter: contrast(1.3) brightness(0.85);
      mix-blend-mode: multiply;
    svg: |
      <feTurbulence baseFrequency="0.05" numOctaves="3"/>
      <feDisplacementMap scale="2"/>
      <!-- coarser than pencil — charcoal pieces are bigger -->
    raster: scanned charcoal artwork
  reactiveBehaviors:
    light: no
    highlight: no
    depth: smudge intensifies on press
    parallax: no
  pairsWith:
    prototypeStyles: [aesthetic-dark-academia, aesthetic-cottagegoth, aesthetic-anti-design]
  killsTheIllusion:
    - clean uniform fill (charcoal smudges)
    - high-saturation accents alongside (charcoal is monochrome)
```

### 4.4 Fabric and textile family

```yaml
```

## Common implementation mistakes (avoid these)

- clean uniform fill (charcoal smudges)
- high-saturation accents alongside (charcoal is monochrome)

## Pairs with (prototype slugs)

- `aesthetic-dark-academia`
- `aesthetic-cottagegoth`
- `aesthetic-anti-design`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 2268–2301 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

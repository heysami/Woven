# Dust + Scratches (archival distress) (material)

**Tag:** material-dust-scratches  ·  **Family:** analog  ·  **Category:** digital-effect · matte

A matte analog surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: dust-scratches
  name: Dust + Scratches (archival distress)
  family: analog
  category: digital-effect
  physicalBehavior:
    surfaceFinish: matte
    transparency: translucent
    reactsToLight: no
    deforms: no
    age: acquired patina
  implementationStrategies:
    css: |
      .distress::after {
        content: '';
        position: absolute; inset: 0;
        background-image: url('dust-scratches-overlay.png');
        mix-blend-mode: screen;
        opacity: 0.4;
        pointer-events: none;
      }
    svg: |
      sparse Voronoi spots + <feTurbulence> at low baseFrequency for sub-pixel scratch lines
    raster: dust + scratches overlay at 2048×2048
  reactiveBehaviors:
    light: no
    highlight: no
    depth: no
    parallax: yes — dust at FIXED layer (not parallaxed) gives "screen dust"
  pairsWith:
    prototypeStyles: [aesthetic-vaporwave, aesthetic-cottagegoth, aesthetic-dark-academia, aesthetic-corporate-grunge, recipe-editorial-magazine]
  killsTheIllusion:
    - regular spacing of "scratches"
    - same overlay tiled visibly
    - high opacity dust (must be subtle)
```

## Common implementation mistakes (avoid these)

- regular spacing of "scratches
- same overlay tiled visibly
- high opacity dust (must be subtle)

## Pairs with (prototype slugs)

- `aesthetic-vaporwave`
- `aesthetic-cottagegoth`
- `aesthetic-dark-academia`
- `aesthetic-corporate-grunge`
- `recipe-editorial-magazine`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 2770–2804 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

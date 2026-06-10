# CAD Blueprint (white-on-blue technical drawing) (material)

**Tag:** material-cad-blueprint  ·  **Family:** digital  ·  **Category:** digital-effect · matte

A matte digital surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: cad-blueprint
  name: CAD Blueprint (white-on-blue technical drawing)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: no
    deforms: no
    age: feels 1900-1980 architectural era
  implementationStrategies:
    css: |
      background: #1e3a5f;  /* deep blueprint blue */
      color: #ffffff;
      font-family: 'Courier Prime', 'Architects Daughter', monospace;
      .blueprint-line { stroke: #c8d8e8; stroke-width: 0.6; fill: none; }
      .blueprint-grid {
        background-image:
          linear-gradient(rgba(255,255,255,0.06) 1px, transparent 1px),
          linear-gradient(90deg, rgba(255,255,255,0.06) 1px, transparent 1px);
        background-size: 20px 20px;
      }
    svg: |
      grid as <pattern>, vectors with stroke="#c8d8e8" fill="none".
      Dimension lines with <marker> arrows and <text> labels per technical convention.
    webgl: not typically needed
    raster: scanned grid paper PNG as substrate; vectors atop
  reactiveBehaviors:
    light: none — it's a print
    highlight: pointer-hover reveals dimension annotations
    depth: minor — pseudo-3D iso projection often present
    parallax: scroll between detail views
  pairsWith:
    prototypeStyles: [aesthetic-bauhaus, aesthetic-swiss-modernist, recipe-scientific-infra-marketing, aesthetic-atompunk, aesthetic-steampunk, style-restrained-hairline]
  killsTheIllusion:
    - blueprint blue too saturated (real blueprints fade toward cyan-grey)
    - antialiased grid lines (real blueprints have crisp 1px ferrocyanide trace)
    - sans-serif body type (blueprint convention is mono / technical letterer)
  examples:
    - Frank Gehry sketches
    - vintage car schematics
    - Le Corbusier's published drawings
  references:
    - https://en.wikipedia.org/wiki/Blueprint
```

## Common implementation mistakes (avoid these)

- blueprint blue too saturated (real blueprints fade toward cyan-grey)
- antialiased grid lines (real blueprints have crisp 1px ferrocyanide trace)
- sans-serif body type (blueprint convention is mono / technical letterer)

## Pairs with (prototype slugs)

- `aesthetic-bauhaus`
- `aesthetic-swiss-modernist`
- `recipe-scientific-infra-marketing`
- `aesthetic-atompunk`
- `aesthetic-steampunk`
- `style-restrained-hairline`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 1434–1478 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

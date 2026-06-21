---
materialId: cad-blueprint
name: CAD Blueprint (white-on-blue technical drawing)
family: digital
category: digital-effect
surfaceFinish: matte
transparency: opaque
pairsPrototypes: [aesthetic-bauhaus, aesthetic-swiss-modernist, recipe-scientific-infra-marketing, aesthetic-atompunk, aesthetic-steampunk, style-restrained-hairline]
images:
  - src: material-cad-blueprint.png
    reason: Material fidelity sample.
---

# CAD Blueprint (white-on-blue technical drawing)

A matte surface.

## Physical behavior

**Surface finish**: matte

**Transparency**: opaque

**Reacts to light**: no

**Deforms**: no

**Age / wear**: feels 1900-1980 architectural era

## Implementation strategies

```yaml
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
```

## Reactive behaviors

**Light**: none - it's a print

**Highlight**: pointer-hover reveals dimension annotations

**Depth**: minor - pseudo-3D iso projection often present

**Parallax**: scroll between detail views

## Common implementation mistakes (avoid these)

- blueprint blue too saturated (real blueprints fade toward cyan-grey)
- antialiased grid lines (real blueprints have crisp 1px ferrocyanide trace)
- sans-serif body type (blueprint convention is mono / technical letterer)

## Examples in the wild

- Frank Gehry sketches
- vintage car schematics
- Le Corbusier's published drawings

## References

- https://en.wikipedia.org/wiki/Blueprint

## Pairs with (prototype slugs)

- `aesthetic-bauhaus`
- `aesthetic-swiss-modernist`
- `recipe-scientific-infra-marketing`
- `aesthetic-atompunk`
- `aesthetic-steampunk`
- `style-restrained-hairline`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

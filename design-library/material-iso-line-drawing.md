---
materialId: iso-line-drawing
name: Isometric Line Drawing (axonometric vector, no fill)
family: digital
category: digital-effect
surfaceFinish: matte
transparency: opaque
pairsPrototypes: [aesthetic-bauhaus, aesthetic-swiss-modernist, recipe-scientific-infra-marketing, aesthetic-atompunk, aesthetic-cassette-futurism]
images:
  - src: material-iso-line-drawing.png
    reason: Material fidelity sample.
---

# Isometric Line Drawing (axonometric vector, no fill)

A matte surface.

## Physical behavior

**Surface finish**: matte

**Transparency**: opaque

**Reacts to light**: no

**Deforms**: no

**Age / wear**: ageless

## Implementation strategies

```yaml
css: |
  /* css can fake simple iso boxes */
  transform: matrix(0.866, 0.5, -0.866, 0.5, 0, 0);  /* 30°/30° iso */
  border: 1px solid var(--ink);
  background: transparent;
svg: |
  pre-project geometry to iso coords:
    sx = (x - y) * cos(30°)
    sy = (x + y) * sin(30°) - z
  stroke only; no fill. Use stroke-dasharray for hidden edges convention.
webgl: three.js OrthographicCamera + axes aligned for isometric; LineSegments material
raster: not appropriate
```

## Reactive behaviors

**Light**: none - vector

**Highlight**: pointer-hover on a face fills it with a tint

**Depth**: line-weight encodes z-depth (further = thinner)

**Parallax**: rotate around iso angle on scroll

## Common implementation mistakes (avoid these)

- perspective convergence (iso is by definition parallel)
- filled regions inconsistent with the line-only register
- stroke joins not crisp at vertices

## Examples in the wild

- SimCity 2000 building diagrams
- vintage technical isometric instruction manuals
- Monument Valley navigation prompts

## References

- https://en.wikipedia.org/wiki/Axonometric_projection

## Pairs with (prototype slugs)

- `aesthetic-bauhaus`
- `aesthetic-swiss-modernist`
- `recipe-scientific-infra-marketing`
- `aesthetic-atompunk`
- `aesthetic-cassette-futurism`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

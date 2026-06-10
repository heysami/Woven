# Isometric Line Drawing (axonometric vector, no fill) (material)

**Tag:** material-iso-line-drawing  ·  **Family:** digital  ·  **Category:** digital-effect · matte

A matte digital surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: iso-line-drawing
  name: Isometric Line Drawing (axonometric vector, no fill)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: no
    deforms: no
    age: ageless
  implementationStrategies:
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
  reactiveBehaviors:
    light: none — vector
    highlight: pointer-hover on a face fills it with a tint
    depth: line-weight encodes z-depth (further = thinner)
    parallax: rotate around iso angle on scroll
  pairsWith:
    prototypeStyles: [aesthetic-bauhaus, aesthetic-swiss-modernist, recipe-scientific-infra-marketing, style-outline-wireframe, aesthetic-atompunk, aesthetic-cassette-futurism]
  killsTheIllusion:
    - perspective convergence (iso is by definition parallel)
    - filled regions inconsistent with the line-only register
    - stroke joins not crisp at vertices
  examples:
    - SimCity 2000 building diagrams
    - vintage technical isometric instruction manuals
    - Monument Valley navigation prompts
  references:
    - https://en.wikipedia.org/wiki/Axonometric_projection
```

## Common implementation mistakes (avoid these)

- perspective convergence (iso is by definition parallel)
- filled regions inconsistent with the line-only register
- stroke joins not crisp at vertices

## Pairs with (prototype slugs)

- `aesthetic-bauhaus`
- `aesthetic-swiss-modernist`
- `recipe-scientific-infra-marketing`
- `style-outline-wireframe`
- `aesthetic-atompunk`
- `aesthetic-cassette-futurism`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 1561–1601 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

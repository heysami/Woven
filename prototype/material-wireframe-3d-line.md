# Wireframe 3D (Tron-style line-only volumetric) (material)

**Tag:** material-wireframe-3d-line  ·  **Family:** digital  ·  **Category:** digital-effect · matte (or glowing)

A matte (or glowing) digital surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: wireframe-3d-line
  name: Wireframe 3D (Tron-style line-only volumetric)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: matte (or glowing)
    transparency: transparent
    reactsToLight: yes — lines can glow with bloom
    deforms: no
    age: feels 1982 (Tron) / 1990s CGI titles
  implementationStrategies:
    css: |
      /* css can't render true 3D — use CSS transforms for simple wireframes */
      transform: perspective(800px) rotateY(20deg) rotateX(15deg);
      border: 1px solid #00ff88;
    svg: |
      pre-projected vector silhouette of geometry; stroke="<accent>" fill="none";
      stroke-width: 1px. For rotation, swap among pre-rendered SVG keyframes.
    webgl: |
      three.js LineSegments material with edges geometry helper. Real wireframe
      means rendering the EdgesGeometry — never just MeshBasicMaterial with
      wireframe:true (that gives triangulated wireframe, not edges-only).
      Add bloom for the Tron register.
    raster: not appropriate
  reactiveBehaviors:
    light: lines glow under bloom
    highlight: pointer-near lines intensify
    depth: depth-fade (far lines fainter)
    parallax: free rotation on pointer drag
  pairsWith:
    prototypeStyles: [aesthetic-cyberpunk, aesthetic-vaporwave, aesthetic-atompunk, aesthetic-cassette-futurism, recipe-terminal-on-web, style-terminal-mono, recipe-scientific-infra-marketing]
  killsTheIllusion:
    - triangulated wireframe (use edges-geometry instead)
    - line thickness variation per face (real wireframe has uniform stroke)
    - antialiasing without bloom for the Tron variant
  examples:
    - Tron (1982)
    - Atari Star Wars arcade (1983)
    - early 3D motion graphics
  references:
    - https://threejs.org/docs/#api/en/objects/LineSegments
```

## Common implementation mistakes (avoid these)

- triangulated wireframe (use edges-geometry instead)
- line thickness variation per face (real wireframe has uniform stroke)
- antialiasing without bloom for the Tron variant

## Pairs with (prototype slugs)

- `aesthetic-cyberpunk`
- `aesthetic-vaporwave`
- `aesthetic-atompunk`
- `aesthetic-cassette-futurism`
- `recipe-terminal-on-web`
- `style-terminal-mono`
- `recipe-scientific-infra-marketing`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 1479–1520 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

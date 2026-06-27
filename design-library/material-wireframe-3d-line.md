---
materialId: wireframe-3d-line
name: Wireframe 3D (Tron-style line-only volumetric)
family: digital
category: digital-effect
surfaceFinish: matte (or glowing)
transparency: transparent
pairsPrototypes: [aesthetic-cyberpunk, aesthetic-vaporwave, aesthetic-atompunk, aesthetic-cassette-futurism, recipe-terminal-on-web, recipe-scientific-infra-marketing]
images:
  - src: material-wireframe-3d-line.png
    reason: Material fidelity sample.
---

# Wireframe 3D (Tron-style line-only volumetric)

A matte (or glowing) surface (transparent) that reacts to light: yes - lines can glow with bloom.

## Physical behavior

**Surface finish**: matte (or glowing)

**Transparency**: transparent

**Reacts to light**: yes - lines can glow with bloom

**Deforms**: no

**Age / wear**: feels 1982 (Tron) / 1990s CGI titles

## Implementation strategies

```yaml
css: |
  /* css can't render true 3D - use CSS transforms for simple wireframes */
  transform: perspective(800px) rotateY(20deg) rotateX(15deg);
  border: 1px solid #00ff88;
svg: |
  pre-projected vector silhouette of geometry; stroke="<accent>" fill="none";
  stroke-width: 1px. For rotation, swap among pre-rendered SVG keyframes.
webgl: |
  three.js LineSegments material with edges geometry helper. Real wireframe
  means rendering the EdgesGeometry - never just MeshBasicMaterial with
  wireframe:true (that gives triangulated wireframe, not edges-only).
  Add bloom for the Tron register.
raster: not appropriate
```

## Reactive behaviors

**Light**: lines glow under bloom

**Highlight**: pointer-near lines intensify

**Depth**: depth-fade (far lines fainter)

**Parallax**: free rotation on pointer drag

## Common implementation mistakes (avoid these)

- triangulated wireframe (use edges-geometry instead)
- line thickness variation per face (real wireframe has uniform stroke)
- antialiasing without bloom for the Tron variant

## Examples in the wild

- Tron (1982)
- Atari Star Wars arcade (1983)
- early 3D motion graphics

## References

- https://threejs.org/docs/#api/en/objects/LineSegments

## Pairs with (prototype slugs)

- `aesthetic-cyberpunk`
- `aesthetic-vaporwave`
- `aesthetic-atompunk`
- `aesthetic-cassette-futurism`
- `recipe-terminal-on-web`
- `recipe-scientific-infra-marketing`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

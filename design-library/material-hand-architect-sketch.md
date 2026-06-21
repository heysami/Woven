---
materialId: hand-architect-sketch
name: Hand Architect Sketch (Le Corbusier / Frank Lloyd Wright register)
family: digital
category: digital-effect
surfaceFinish: matte
transparency: opaque
pairsPrototypes: [recipe-warm-restraint, recipe-editorial-magazine, aesthetic-dark-academia, style-cream-humanist, style-serif-warm-paper, aesthetic-cottagecore]
images:
  - src: material-hand-architect-sketch.png
    reason: Material fidelity sample.
---

# Hand Architect Sketch (Le Corbusier / Frank Lloyd Wright register)

A matte surface that reacts to light: subtle - paper grain breathes under raking light.

## Physical behavior

**Surface finish**: matte

**Transparency**: opaque

**Reacts to light**: subtle - paper grain breathes under raking light

**Deforms**: no

**Age / wear**: feels 1920-1960 master-architect era

## Implementation strategies

```yaml
css: |
  font-family: 'Architects Daughter', 'Caveat', sans-serif;
  color: #1a1a1a;
  .sketch-line { stroke: #1a1a1a; stroke-width: 0.8; fill: none; }
svg: |
  <filter id="hand-tremor">
    <feTurbulence baseFrequency="0.8" numOctaves="2" />
    <feDisplacementMap scale="1.5" />
  </filter>
  Apply to all paths. Use varying stroke widths (0.5-1.4) for "pressure" effect.
  Don't close every shape - leave a 5-10% gap (real hand sketches "breathe").
webgl: not typically needed
raster: scanned hand-drawn sketches OK as substrate (combine with vector overlay)
```

## Reactive behaviors

**Light**: paper texture subtly catches light

**Highlight**: pointer can advance an unfinished sketch

**Depth**: stroke weight implies depth (heavier = closer)

**Parallax**: stack of trace-paper overlays on scroll

## Common implementation mistakes (avoid these)

- uniform stroke width (real hand has pressure variation)
- perfectly closed shapes (real sketches breathe)
- antialiased curves with no tremor

## Examples in the wild

- Frank Lloyd Wright Falling Water sketches
- Le Corbusier's published sketches
- Steven Holl watercolor architectural ideation

## References

- https://en.wikipedia.org/wiki/Architectural_drawing

## Pairs with (prototype slugs)

- `recipe-warm-restraint`
- `recipe-editorial-magazine`
- `aesthetic-dark-academia`
- `style-cream-humanist`
- `style-serif-warm-paper`
- `aesthetic-cottagecore`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

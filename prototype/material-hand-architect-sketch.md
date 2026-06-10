# Hand Architect Sketch (Le Corbusier / Frank Lloyd Wright register) (material)

**Tag:** material-hand-architect-sketch  ·  **Family:** digital  ·  **Category:** digital-effect · matte

A matte digital surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: hand-architect-sketch
  name: Hand Architect Sketch (Le Corbusier / Frank Lloyd Wright register)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: subtle — paper grain breathes under raking light
    deforms: no
    age: feels 1920-1960 master-architect era
  implementationStrategies:
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
      Don't close every shape — leave a 5-10% gap (real hand sketches "breathe").
    webgl: not typically needed
    raster: scanned hand-drawn sketches OK as substrate (combine with vector overlay)
  reactiveBehaviors:
    light: paper texture subtly catches light
    highlight: pointer can advance an unfinished sketch
    depth: stroke weight implies depth (heavier = closer)
    parallax: stack of trace-paper overlays on scroll
  pairsWith:
    prototypeStyles: [recipe-warm-restraint, recipe-editorial-magazine, aesthetic-dark-academia, style-cream-humanist, style-serif-warm-paper, aesthetic-cottagecore]
  killsTheIllusion:
    - uniform stroke width (real hand has pressure variation)
    - perfectly closed shapes (real sketches breathe)
    - antialiased curves with no tremor
  examples:
    - Frank Lloyd Wright Falling Water sketches
    - Le Corbusier's published sketches
    - Steven Holl watercolor architectural ideation
  references:
    - https://en.wikipedia.org/wiki/Architectural_drawing
```

## Common implementation mistakes (avoid these)

- uniform stroke width (real hand has pressure variation)
- perfectly closed shapes (real sketches breathe)
- antialiased curves with no tremor

## Pairs with (prototype slugs)

- `recipe-warm-restraint`
- `recipe-editorial-magazine`
- `aesthetic-dark-academia`
- `style-cream-humanist`
- `style-serif-warm-paper`
- `aesthetic-cottagecore`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 1602–1643 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

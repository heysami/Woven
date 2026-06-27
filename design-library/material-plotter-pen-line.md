---
materialId: plotter-pen-line
name: Plotter Pen Line (HP 7475 single-weight ink-on-paper)
family: digital
category: digital-effect
surfaceFinish: matte
transparency: opaque
pairsPrototypes: [aesthetic-swiss-modernist, aesthetic-bauhaus, recipe-scientific-infra-marketing, recipe-newspaper-of-record, style-restrained-hairline]
images:
  - src: material-plotter-pen-line.png
    reason: Material fidelity sample.
---

# Plotter Pen Line (HP 7475 single-weight ink-on-paper)

A matte surface.

## Physical behavior

**Surface finish**: matte

**Transparency**: opaque

**Reacts to light**: no

**Deforms**: no

**Age / wear**: feels 1985-CAD-lab era

## Implementation strategies

```yaml
css: |
  stroke: #1a1a1a;
  stroke-width: 0.5;
  stroke-linecap: round;
  fill: none;
  filter: url(#pen-jitter);  /* subtle hand-tremor displacement */
svg: |
  <filter id="pen-jitter">
    <feTurbulence baseFrequency="0.5" numOctaves="2" />
    <feDisplacementMap scale="0.4" />
  </filter>
  Apply to all stroked paths. Use vector geometry only; no fills.
webgl: |
  line shader with subtle width noise + ink-blot simulation at line ends
raster: avoid - plotter is inherently vector
```

## Reactive behaviors

**Light**: paper grain shows under raking light

**Highlight**: pointer can advance a stroke (drawing-in-progress register)

**Depth**: none - flat ink on paper

**Parallax**: none

## Common implementation mistakes (avoid these)

- variable stroke width (a plotter uses one pen at a time)
- filled regions (plotters don't fill - they hatch)
- antialiased curves without ink-jitter

## Examples in the wild

- early CAD output (AutoCAD 1.0 era)
- vintage Tufte information graphics
- Casey Reas / processing.org early sketches

## References

- https://en.wikipedia.org/wiki/HP_7475

## Pairs with (prototype slugs)

- `aesthetic-swiss-modernist`
- `aesthetic-bauhaus`
- `recipe-scientific-infra-marketing`
- `recipe-newspaper-of-record`
- `style-restrained-hairline`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

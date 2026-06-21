---
materialId: schematic-pcb-trace
name: Schematic / PCB Trace (circuit-board aesthetic)
family: digital
category: digital-effect
surfaceFinish: matte
transparency: opaque
pairsPrototypes: [aesthetic-cyberpunk, aesthetic-cassette-futurism, aesthetic-atompunk, recipe-terminal-on-web, recipe-scientific-infra-marketing, recipe-devtools-marketing]
images:
  - src: material-schematic-pcb-trace.png
    reason: Material fidelity sample.
---

# Schematic / PCB Trace (circuit-board aesthetic)

A matte surface that reacts to light: minor - gold pads catch raking light.

## Physical behavior

**Surface finish**: matte

**Transparency**: opaque

**Reacts to light**: minor - gold pads catch raking light

**Deforms**: no

**Age / wear**: ageless

## Implementation strategies

```yaml
css: |
  background: #00553a;  /* solder mask green */
  color: #e2c376;       /* silkscreen yellow */
  font-family: 'IBM Plex Mono', monospace;
  .trace { stroke: #b58b3a; stroke-width: 1.6; }   /* copper trace */
  .pad { fill: #f5d480; stroke: #b58b3a; }          /* solder pad */
svg: |
  orthogonal-routed paths only (45° / 90° angles), <pattern> dot grid for
  vias, <circle> for component pins, <text> for silkscreen labels in mono.
webgl: not typically needed
raster: PCB texture PNG as substrate
```

## Reactive behaviors

**Light**: minor - pads glint subtly

**Highlight**: pointer can activate trace-flow animation (electron path)

**Depth**: layered traces (top + bottom copper) at different opacities

**Parallax**: scroll reveals additional copper layers

## Common implementation mistakes (avoid these)

- diagonal trace routing at non-45° angles (PCB design has strict angles)
- antialiased traces without copper-fill texture
- solder-mask color too bright (real green is muted)

## Examples in the wild

- Raspberry Pi board photography
- KiCAD render output
- vintage electronic component diagrams

## References

- https://en.wikipedia.org/wiki/Printed_circuit_board

## Pairs with (prototype slugs)

- `aesthetic-cyberpunk`
- `aesthetic-cassette-futurism`
- `aesthetic-atompunk`
- `recipe-terminal-on-web`
- `recipe-scientific-infra-marketing`
- `recipe-devtools-marketing`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

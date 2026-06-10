# Schematic / PCB Trace (circuit-board aesthetic) (material)

**Tag:** material-schematic-pcb-trace  ·  **Family:** digital  ·  **Category:** digital-effect · matte

A matte digital surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: schematic-pcb-trace
  name: Schematic / PCB Trace (circuit-board aesthetic)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: minor — gold pads catch raking light
    deforms: no
    age: ageless
  implementationStrategies:
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
  reactiveBehaviors:
    light: minor — pads glint subtly
    highlight: pointer can activate trace-flow animation (electron path)
    depth: layered traces (top + bottom copper) at different opacities
    parallax: scroll reveals additional copper layers
  pairsWith:
    prototypeStyles: [aesthetic-cyberpunk, aesthetic-cassette-futurism, aesthetic-atompunk, recipe-terminal-on-web, recipe-scientific-infra-marketing, recipe-devtools-marketing]
  killsTheIllusion:
    - diagonal trace routing at non-45° angles (PCB design has strict angles)
    - antialiased traces without copper-fill texture
    - solder-mask color too bright (real green is muted)
  examples:
    - Raspberry Pi board photography
    - KiCAD render output
    - vintage electronic component diagrams
  references:
    - https://en.wikipedia.org/wiki/Printed_circuit_board
```

## Common implementation mistakes (avoid these)

- diagonal trace routing at non-45° angles (PCB design has strict angles)
- antialiased traces without copper-fill texture
- solder-mask color too bright (real green is muted)

## Pairs with (prototype slugs)

- `aesthetic-cyberpunk`
- `aesthetic-cassette-futurism`
- `aesthetic-atompunk`
- `recipe-terminal-on-web`
- `recipe-scientific-infra-marketing`
- `recipe-devtools-marketing`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 1521–1560 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

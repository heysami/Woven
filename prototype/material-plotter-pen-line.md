# Plotter Pen Line (HP 7475 single-weight ink-on-paper) (material)

**Tag:** material-plotter-pen-line  ·  **Family:** digital  ·  **Category:** digital-effect · matte

A matte digital surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: plotter-pen-line
  name: Plotter Pen Line (HP 7475 single-weight ink-on-paper)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: no
    deforms: no
    age: feels 1985-CAD-lab era
  implementationStrategies:
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
    raster: avoid — plotter is inherently vector
  reactiveBehaviors:
    light: paper grain shows under raking light
    highlight: pointer can advance a stroke (drawing-in-progress register)
    depth: none — flat ink on paper
    parallax: none
  pairsWith:
    prototypeStyles: [aesthetic-swiss-modernist, aesthetic-bauhaus, recipe-scientific-infra-marketing, style-outline-wireframe, recipe-newspaper-of-record, style-restrained-hairline]
  killsTheIllusion:
    - variable stroke width (a plotter uses one pen at a time)
    - filled regions (plotters don't fill — they hatch)
    - antialiased curves without ink-jitter
  examples:
    - early CAD output (AutoCAD 1.0 era)
    - vintage Tufte information graphics
    - Casey Reas / processing.org early sketches
  references:
    - https://en.wikipedia.org/wiki/HP_7475
```

## Common implementation mistakes (avoid these)

- variable stroke width (a plotter uses one pen at a time)
- filled regions (plotters don't fill — they hatch)
- antialiased curves without ink-jitter

## Pairs with (prototype slugs)

- `aesthetic-swiss-modernist`
- `aesthetic-bauhaus`
- `recipe-scientific-infra-marketing`
- `style-outline-wireframe`
- `recipe-newspaper-of-record`
- `style-restrained-hairline`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 1390–1433 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

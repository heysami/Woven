# Risograph (limited-palette spot-color print) (material)

**Tag:** material-risograph  ·  **Family:** analog  ·  **Category:** print · matte

A matte analog surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: risograph
  name: Risograph (limited-palette spot-color print)
  family: analog
  category: print
  physicalBehavior:
    surfaceFinish: matte
    transparency: translucent (per ink layer)
    reactsToLight: no
    deforms: no
    age: ageless
  implementationStrategies:
    css: |
      /* Each "ink" is a colour layer with mix-blend-mode: multiply */
      .layer-fluo-pink { background: color-mix(in srgb, #ff48b0 60%, transparent); mix-blend-mode: multiply; }
      .layer-teal { background: color-mix(in srgb, #00a89c 60%, transparent); mix-blend-mode: multiply; }
      .registration-shift { transform: translate(1.5px, -1px); }  /* trapping miss */
    svg: |
      halftone via <pattern> of dots at varying spacing per ink layer
    webgl: |
      shader: posterise to N inks, apply per-ink halftone screen, slight per-ink
      offset to fake registration shift. Spectrolite-style.
    raster: scanned risograph print as ground truth
  reactiveBehaviors:
    light: no
    highlight: no
    depth: no
    parallax: subtle — each ink layer at slightly different scroll rate
  pairsWith:
    prototypeStyles: [aesthetic-acid-design, aesthetic-acid-graphics, aesthetic-corporate-grunge, aesthetic-y2k-myspace, aesthetic-corporate-memphis]
  killsTheIllusion:
    - perfect registration (riso is famously misregistered — 1–3px offset is the look)
    - smooth gradients (riso halftones, never blends)
    - full opacity inks (riso ink is semi-transparent)
    - warm paper substrate missing (riso usually prints on cream paper)
  examples:
    - RISOTTO Studio prints
    - Spectrolite Riso-ify tool
    - small-press zines
    - Are.na editorial banners
  references:
    - https://risottostudio.com/pages/printing-faq
    - https://spectrolite.app/how-to/overview/riso-ify
```

## Common implementation mistakes (avoid these)

- perfect registration (riso is famously misregistered — 1–3px offset is the look)
- smooth gradients (riso halftones, never blends)
- full opacity inks (riso ink is semi-transparent)

## Pairs with (prototype slugs)

- `aesthetic-acid-design`
- `aesthetic-acid-graphics`
- `aesthetic-corporate-grunge`
- `aesthetic-y2k-myspace`
- `aesthetic-corporate-memphis`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 1924–1966 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

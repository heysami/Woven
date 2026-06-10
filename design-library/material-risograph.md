---
materialId: risograph
name: Risograph (limited-palette spot-color print)
family: analog
category: print
surfaceFinish: matte
transparency: translucent (per ink layer)
pairsPrototypes: [aesthetic-acid-design, aesthetic-acid-graphics, aesthetic-corporate-grunge, aesthetic-y2k-myspace, aesthetic-corporate-memphis]
images:
  - src: material-risograph.png
    reason: Material fidelity sample.
---

# Risograph (limited-palette spot-color print)

A matte surface (translucent (per ink layer)).

## Physical behavior

**Surface finish**: matte

**Transparency**: translucent (per ink layer)

**Reacts to light**: no

**Deforms**: no

**Age / wear**: ageless

## Implementation strategies

```yaml
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
```

## Reactive behaviors

**Light**: no

**Highlight**: no

**Depth**: no

**Parallax**: subtle — each ink layer at slightly different scroll rate

## Common implementation mistakes (avoid these)

- perfect registration (riso is famously misregistered — 1–3px offset is the look)
- smooth gradients (riso halftones, never blends)
- full opacity inks (riso ink is semi-transparent)
- warm paper substrate missing (riso usually prints on cream paper)

## Examples in the wild

- RISOTTO Studio prints
- Spectrolite Riso-ify tool
- small-press zines
- Are.na editorial banners

## References

- https://risottostudio.com/pages/printing-faq
- https://spectrolite.app/how-to/overview/riso-ify

## Pairs with (prototype slugs)

- `aesthetic-acid-design`
- `aesthetic-acid-graphics`
- `aesthetic-corporate-grunge`
- `aesthetic-y2k-myspace`
- `aesthetic-corporate-memphis`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

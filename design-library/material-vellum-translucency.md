---
materialId: vellum-translucency
name: Vellum / Tracing Paper Translucency
family: digital
category: glass
surfaceFinish: matte
transparency: translucent
pairsPrototypes: [style-serif-warm-paper, aesthetic-cottagecore, aesthetic-cottagegoth, aesthetic-dark-academia]
images:
  - src: material-vellum-translucency.png
    reason: Material fidelity sample.
---

# Vellum / Tracing Paper Translucency

A matte surface (translucent).

## Physical behavior

**Surface finish**: matte

**Transparency**: translucent

**Reacts to light**: no specular - light scatters

**Deforms**: no

**Age / wear**: ageless

## Implementation strategies

```yaml
css: |
  background: rgba(252,250,245,0.62);
  backdrop-filter: blur(8px) saturate(80%);  /* desaturate, not boost */
  box-shadow: 0 2px 8px rgba(60,40,20,0.08);
  /* WARM tone, not cool - vellum is yellowish */
svg: |
  <filter id="vellumGrain">
    <feTurbulence baseFrequency="0.9" numOctaves="2"/>
    <feColorMatrix values="0 0 0 0 0.95  0 0 0 0 0.93  0 0 0 0 0.88  0 0 0 0.08 0"/>
  </filter>
  /* paper-fibre noise at 8% opacity over the panel */
raster: optional 2048px vellum scan multiplied at low opacity
```

## Reactive behaviors

**Light**: minimal; vellum doesn't glint

**Highlight**: none

**Depth**: 1px lift on hover only

**Parallax**: minimal

## Common implementation mistakes (avoid these)

- cool/blue blur (vellum is warm)
- high saturate boost (vellum desaturates, doesn't intensify)
- sharp specular highlight (matte material can't glint)

## Examples in the wild

- architectural drawing overlays
- wedding invitation overlays
- Apple visionOS "Plate" material (when configured matte)

## Pairs with (prototype slugs)

- `style-serif-warm-paper`
- `aesthetic-cottagecore`
- `aesthetic-cottagegoth`
- `aesthetic-dark-academia`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

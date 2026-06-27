---
materialId: filament-strand-ribbon
name: Filament strand ribbon (fiber-optic hairlines in flow)
family: digital
category: emissive-fiber
surfaceFinish: glossy
transparency: additive
pairsPrototypes: [style-silk-chrome-flow, aesthetic-cosmic-horizon, aesthetic-defi-cosmic, recipe-ai-foundry-dark]
images:
  - src: material-filament-strand-ribbon.png
    reason: Material fidelity sample.
---

# Filament strand ribbon (fiber-optic hairlines in flow)

Hundreds-to-thousands of 1px luminous strands traveling together as one silk
ribbon across a black field - a fiber-optic bundle mid-wave. Iridescent
micro-hues (amber, cyan, violet) live INSIDE the bundle where strands cross
and compress; the overall read stays achromatic until you look close. Distinct
from `material-liquid-chrome-silk` (a continuous mirrored SURFACE) and from
`material-aurora-mesh` (soft blobs): this material is DISCRETE strands with
additive blending - the gaps between hairs are part of the material.

## Physical behavior

**Surface finish**: each strand is a glossy emissive hairline; the bundle reads
as silk at distance, as fiber optics up close

**Transparency**: additive - strands brighten where they overlap; the black
substrate is mandatory (additive on white = invisible)

**Reacts to light**: self-luminous; hue shifts subtly along each strand's
length (a 30-50° hue travel end to end)

**Deforms**: yes - the whole point; the bundle undulates as one slow wave,
strands keeping loose formation like hair in water

**Age / wear**: ageless

## Implementation strategies

```yaml
css: |
  /* Static approximation only - layered repeating gradients on a curve
     can't hold the read; use SVG or canvas for anything visible. */
svg: |
  60-200 <path> strands: same base bezier, each with small per-strand
  offset + phase jitter, stroke-width 1, stroke a per-strand stop from
  an iridescent ramp, opacity 0.25-0.5, mix-blend-mode: screen.
  Animate with a slow dashoffset drift or SMIL path morph for ambient flow.
canvas2d: |
  The sweet spot for most pages: per frame, redraw N beziers whose control
  points ride layered sine fields (x phase-shifted per strand index);
  globalCompositeOperation = 'lighter'; alpha 0.2-0.4. 200 strands at 60fps
  is comfortable; cap DPR at 1.5.
webgl: |
  Hero grade: instanced line segments or a ribbon mesh with a strand-index
  varying driving hue + brightness; additive blending; noise-field
  displacement in the vertex shader. THE smoothest option for 1000+ strands.
raster: pre-rendered ribbon PNG for static slots (bake mid-wave)
video: 12-20s seamless undulation loop
```

## Reactive behaviors

**Proximity**: the wave's crest drifts toward the cursor (bias the sine field
centroid), falloff 1/d² over 500px - the ribbon leans, never chases

**Hover** (over a CTA near the ribbon): local strand brightness rises 20%
within a 200px radius - the fiber bundle lights up near the action

**Click**: a brightness pulse travels down the bundle from the click point at
~800px/s, one way, once

**Scroll**: wave phase advances with scroll at 0.3× - slow parallax, the
ribbon breathes through the page

## Common implementation mistakes (avoid these)

- Too few strands too thick (12 fat lines is a wireframe, not silk - the read
  needs ≥60 hairlines with sub-pixel feel)
- Uniform opacity (depth comes from per-strand alpha jitter; flat alpha
  flattens the bundle to a texture)
- Full-rainbow saturation (iridescence lives INSIDE a mostly-monochrome
  bundle; a rainbow ribbon is a different, louder material)
- White or light substrate (additive strands need black; on light fields use
  liquid-chrome-silk instead)
- Fast motion (the canon is SLOW - one full undulation per 10-20s; fast
  wiggle reads as a loading animation)

## Examples in the wild

- Spline "Clarity Stream" (hairline ribbon wave under "Clarity. Focus.
  Impact.")
- Stripe/Linear-era dark heroes with flowing line fields
- Audio-visualizer-grade WebGL ribbons on AI-product landings

## Pairs with (prototype slugs)

- `style-silk-chrome-flow`
- `aesthetic-cosmic-horizon`
- `aesthetic-defi-cosmic`
- `recipe-ai-foundry-dark`

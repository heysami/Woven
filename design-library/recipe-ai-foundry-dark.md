---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: recipe-ai-foundry-dark-ui.png
    reason: Full recipe UI mockup.
---
# AI-foundry dark

A `(shell + style + voice)` bundle for **AI-compute / model-training / chip-architecture marketing** that runs on dark surfaces with oversized neo-grotesque headlines.

## Picks

- **Shell:** `hero-stack` - read `shell-hero-stack.md`
- **Style:** `oversized-neo-grotesque` on near-black canvas - read `style-oversized-neo-grotesque.md` (override background to `oklch(8% 0.005 250)` or `#0A0B0E`)
- **Aesthetic:** *(none - the dark canvas + 3D hero render IS the identity)*
- **Voice:** confident, technical, restrained. Numeric superlatives are permitted ("100,000 cores", "20 PB/s"). No exclamation marks. Hardware specs as poetry.

## Pattern

- Full-bleed dark background (`#0A0B0E` / `oklch(8% 0.005 250)`); never pure black
- Oversized neo-grotesque headline at hero (96-160px on desktop), tracked slightly negative
- 3D-rendered hero object (chip, crystal, lattice, abstract architecture) often produced in Cinema 4D / Blender / Spline
- Optional restrained aurora bloom behind the hero object - kept subtle (15-25% opacity)
- Body sections in 8-col or 12-col grid, hairline dividers in `rgba(255,255,255,0.06)`
- Architectural product photography (chip macros, server racks, lattice close-ups) in feature sections
- Performance metric strip with agate-numeric readouts

## Best for

AI compute / chip / model-training marketing, foundation-model lab landing pages, high-performance-computing marketing, advanced-hardware brand sites - anywhere "industrial-scale infrastructure" needs a dark-mode confident voice.

## What distinguishes this from existing recipes

- `bento-marketing` is bright, consumer-marketing flavor - this is dark, enterprise-engineering flavor.
- `swiss-grid` uses editorial-broken-grid + monochrome - this uses hero-stack + dark canvas.
- `aurora-marketing` leads with the gradient - this leads with the 3D hero object.

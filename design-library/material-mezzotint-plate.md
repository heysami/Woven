---
materialId: mezzotint-plate
name: Mezzotint Plate (burnished highlights out of velvet black)
family: analog
category: print
surfaceFinish: matte (velvet ink, burnished-metal accents)
scope: both
transparency: opaque
pairsPrototypes: [aesthetic-dark-academia, aesthetic-luxury-cinematic-dark, aesthetic-neoclassical-remix, style-serif-warm-paper, recipe-editorial-magazine]
images:
  - src: material-mezzotint-plate.png
    reason: Material fidelity sample.
---

# Mezzotint Plate (burnished highlights out of velvet black)

A darkness-first printmaking surface: the plate is rocked entirely to black, and every form is polished back toward light.

## Physical behavior

**Surface finish**: matte velvet black ground; highlights read as burnished, faintly metallic passages

**Transparency**: opaque

**Reacts to light**: only where burnished - highlights carry a soft plate-metal sheen; the black absorbs everything

**Deforms**: no

**Age / wear**: plate tone drifts warm (silver toward sepia brown) as the plate wears

## Implementation strategies

```yaml
css: |
  /* the ground is total: near-black with rocked-plate grain, never a gray "dark theme" */
  --velvet-black: #0b0b0b; --burnished-silver: #e7e4dd; --soft-silver: #a79f95;
  --plate-brown: #5a4634; --deep-brown: #2d2219;
  body { background: var(--velvet-black); color: var(--soft-silver); }
  /* forms EMERGE: soft radial tone wells, darkest at the frame edges */
  .figure { background: radial-gradient(ellipse at 45% 35%,
    rgba(231,228,221,0.55), rgba(90,70,52,0.25) 45%, transparent 75%); }
  /* burnished accents (buttons, plates) as warm silver gradients with grain */
  .burnished { background: linear-gradient(160deg, #e7e4dd, #a79f95 55%, #7a6f60); }
svg: |
  rocked-plate grain: feTurbulence (fine, high-frequency) composited into BOTH
  the black field and the highlight wells so tone is granular, never smooth
webgl: |
  shader: invert the usual pipeline - start from black, add luminance only where
  the "burnisher" passed; clamp highlights to warm silver, never pure white
raster: scanned mezzotint plate tone at low opacity screen over the black field
```

## Reactive behaviors

**Light**: highlight wells breathe slightly brighter on hover, as if burnished further

**Highlight**: emergence, not specular - tone blooms outward from the subject

**Depth**: tonal only; no hard edges, form dissolves into the ground

**Parallax**: none - a plate is a single surface

## Common implementation mistakes (avoid these)

- treating it as a dark theme with flat gray text (mezzotint is tone carved OUT of black - every light passage needs a gradient of emergence)
- pure #fff highlights (burnished passages are warm silver #e7e4dd at their very brightest)
- adding hatching or contour lines (mezzotint has NO line - tone only; line work belongs to etching)
- smooth noiseless gradients (the rocker leaves grain in every tone, dark and light alike)
- high-contrast hard silhouettes (edges dissolve; the darkest dark and the subject share the same granular field)

## Examples in the wild

- 17th-19th century mezzotint portrait prints
- modern printmakers working dark-manner plates
- title sequences that fade figures up from true black

## Pairs with (prototype slugs)

- `aesthetic-dark-academia`
- `aesthetic-luxury-cinematic-dark`
- `aesthetic-neoclassical-remix`
- `style-serif-warm-paper`
- `recipe-editorial-magazine`

## Differentiation

- vs `material-charcoal-drawing`: charcoal is additive dark marks on a light paper ground with visible stroke direction; mezzotint is subtractive light polished out of a total black ground, grain but no stroke
- vs `material-pencil-graphite`: graphite is linear, light-ground, with sheen following stroke direction; mezzotint is toneless-of-line and darkness-first

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

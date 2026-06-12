---
materialId: reeded-fluted-glass
name: Reeded / fluted glass (vertical-slat refraction)
family: digital
category: glass
surfaceFinish: glossy
transparency: transparent-refractive
pairsPrototypes: [style-liquid-glass, style-glassmorphism, recipe-restrained-ai-marketing, aesthetic-pastel-pop-fmcg, aesthetic-monochrome-pop-poster]
images:
  - src: material-reeded-fluted-glass.png
    reason: Material fidelity sample.
---

# Reeded / fluted glass (vertical-slat refraction)

A glossy transparent panel of vertical half-cylinder ribs — each rib acts as a
cylindrical lens that SLICES whatever sits behind it into displaced vertical
strips. The privacy-glass read: you can tell something is there, the ribs
decide how much. Distinct from frosted glass (uniform scatter) and from
dispersion-prism glass (spectral split): reeded glass is about per-slat
DISPLACEMENT, not blur, not rainbow.

## Physical behavior

**Surface finish**: glossy; each rib carries its own 1px vertical specular line

**Transparency**: transparent with strong per-rib refraction; the subject behind
stays recognizable but striped — edges shear horizontally at every rib boundary

**Reacts to light**: yes — specular lines brighten/shift as the light or view
angle moves; a subject drifting behind the panel re-slices continuously (the
signature motion)

**Deforms**: no — rigid architectural panel

**Age / wear**: ageless

## Implementation strategies

```yaml
css: |
  /* Rib highlights + cheap displacement-free read for chips/panels: */
  backdrop-filter: blur(1.5px) saturate(115%);
  background: repeating-linear-gradient(90deg,
    rgba(255,255,255,0.16) 0px, rgba(255,255,255,0.02) 6px,
    rgba(0,0,0,0.05) 12px, rgba(255,255,255,0.16) 24px);
  border: 1px solid rgba(255,255,255,0.25);
  /* the repeating gradient fakes rib speculars; real slicing needs SVG/WebGL */
svg: |
  <feDisplacementMap scale="28"> driven by a displacement map that is a
  repeating horizontal sawtooth gradient (one tooth per rib) — displaces
  backdrop strips left/right per rib. Apply to an <image> or <foreignObject>
  copy of the content behind; never to live text.
webgl: |
  The real thing for hero scenes: plane with a normal map of vertical
  half-cylinders (or actual rib geometry), three.js MeshPhysicalMaterial
  { transmission: 1, roughness: 0.05–0.15, ior: 1.5, thickness: 0.6 }.
  Put a saturated hero object 0.5–1 unit BEHIND the panel and drift it
  slowly — the re-slicing is the whole show.
raster: pre-rendered panel-over-subject PNG for static slots (bake the slicing)
video: subject drifting behind the panel, fixed camera, 8–12s loop
```

## Reactive behaviors

**Proximity**: rib speculars lean toward the cursor (shift the repeating
gradient's phase by ±4px), falloff 1/d² over 400px

**Hover**: refraction depth ticks up (displacement scale 28 → 36; or thickness
0.6 → 0.8 in WebGL); speculars brighten 15%

**Click**: none — architectural glass absorbs; at most a 150ms specular flash

**Scroll/tilt**: the subject behind translates at 0.85× scroll speed (the panel
is fixed, the world moves behind it) — re-slicing reads as depth

## Common implementation mistakes (avoid these)

- Uniform blur with stripe overlay (that's frosted glass wearing a costume —
  the strips must DISPLACE, edges must shear at rib boundaries)
- Ribs on both axes (reeded glass is one direction; a grid reads as privacy
  film, a different material)
- Refracting body text through the ribs (unreadable; the panel goes over
  imagery and objects only)
- Rainbow fringe on the ribs (that's dispersion-prism-glass; reeded glass
  keeps the subject's own hue — monochrome scene discipline is the canon)
- Flat-white substrate behind the panel (nothing to slice = fogged plastic;
  the subject behind must be saturated and high-contrast)

## Examples in the wild

- Spline "Reeded liquid glass — Prism hero section concept" (green sphere
  sliced by a fluted panel, mint monochrome field)
- Apple Liquid Glass-era marketing details; interior-architecture reeded
  partitions (the physical referent)
- Fintech hero cards with fluted-glass strips over brand objects

## Pairs with (prototype slugs)

- `style-liquid-glass`
- `style-glassmorphism`
- `recipe-restrained-ai-marketing`
- `aesthetic-pastel-pop-fmcg`
- `aesthetic-monochrome-pop-poster`

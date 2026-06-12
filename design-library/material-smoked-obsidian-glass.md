---
materialId: smoked-obsidian-glass
name: Smoked obsidian glass (dark refractor over typography)
family: digital
category: glass
surfaceFinish: glossy
transparency: translucent-dark
pairsPrototypes: [aesthetic-monochrome-pop-poster, style-oversized-neo-grotesque, aesthetic-luxury-cinematic-dark, recipe-neo-grotesque-portfolio]
images:
  - src: material-smoked-obsidian-glass.png
    reason: Material fidelity sample.
---

# Smoked obsidian glass (dark refractor over typography)

A dark, smoky, glossy glass solid — cube, shard, blob — whose whole job is to
float OVER oversized typography and smear it: the letterforms behind bend,
blur, and dim through the body. Where dispersion-prism glass is optically pure
and splits spectra, smoked glass is tinted toward black, scatters softly, and
keeps the scene monochrome. The canonical use is a B/W poster page where the
type is the landscape and the glass object is the weather.

## Physical behavior

**Surface finish**: glossy with faint internal smoke (roughness gradient across
the volume — denser toward the core)

**Transparency**: translucent-dark; content behind survives at 30–60% legibility,
darkened and warped; thick sections go almost opaque

**Reacts to light**: yes — a single soft specular streak crawls across the face
as the object rotates; internal smoke catches a faint glow at grazing angles

**Deforms**: no — rigid solid; motion is slow tumble/orbit, never squish

**Age / wear**: ageless

## Implementation strategies

```yaml
css: |
  /* DOM approximation — a dark glass chip floating over display type: */
  backdrop-filter: blur(6px) brightness(0.55) contrast(1.15) saturate(0.8);
  background: linear-gradient(135deg, rgba(20,20,24,0.35), rgba(0,0,0,0.55));
  border: 1px solid rgba(255,255,255,0.08);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.10),
              0 30px 80px -30px rgba(0,0,0,0.8);
svg: |
  feDisplacementMap (scale 12–20, turbulence baseFrequency 0.012) over a
  duplicated <text> raster + feGaussianBlur 4px + feComponentTransfer
  darkening — the smear without a 3D engine.
webgl: |
  Hero canon: three.js MeshPhysicalMaterial { transmission: 1,
  thickness: 1.2, roughness: 0.25, attenuationColor: #0a0a0c,
  attenuationDistance: 0.9, ior: 1.45 } on a beveled cube/shard, the
  TYPE rendered to a plane 1 unit behind. Slow tumble (0.05 rad/s) +
  pointer-damped orbit. Film grain over everything ties it together.
raster: baked render (object over type) for static slots
video: 10–14s tumble loop, fixed camera, fixed type
```

## Reactive behaviors

**Proximity**: specular streak leans toward the cursor, falloff 1/d² over 400px

**Hover**: rotation rate eases up 1.5×; refraction thickness ticks up — the
object "notices" without snapping

**Click**: 150ms internal glow pulse (attenuationDistance briefly rises) — the
smoke lights up once

**Scroll**: object yaws ±20° across the section scroll; the type behind stays
fixed — the parallax between fixed type and turning glass is the read

## Common implementation mistakes (avoid these)

- Rainbow/spectral fringe (that's dispersion-prism; smoked glass is achromatic
  — the monochrome discipline IS the genre)
- Blurring the REAL text node (always smear a duplicated/rastered copy; the
  accessible text stays clean in the DOM)
- Tint so dark the type behind dies completely (30–60% survival is the zone;
  full occlusion reads as a black box, not glass)
- Multiple glass objects (one object over one headline; a fleet of cubes is
  the drag-physics-cluster pattern, a different register)
- Forgetting the grain pass (clean gradients + dark glass = render-y; 3–5%
  monochrome grain makes it filmic)

## Examples in the wild

- Spline "Tick Tock — Interactive Landing" (smoked cube smearing oversized
  TICK TOCK echo type, grain, mono micro-labels)
- Off-Black / fashion-editorial WebGL heroes with obsidian blobs over masthead
  type
- Watch/jewelry dark product stages (smoked glass plinth covers)

## Pairs with (prototype slugs)

- `aesthetic-monochrome-pop-poster`
- `style-oversized-neo-grotesque`
- `aesthetic-luxury-cinematic-dark`
- `recipe-neo-grotesque-portfolio`

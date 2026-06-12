---
materialId: volumetric-cloud
name: Volumetric cloud / cotton
family: digital
category: organic-volume
surfaceFinish: matte
transparency: translucent
pairsPrototypes: [aesthetic-surreal-dream-stage, aesthetic-pastoral-serene, aesthetic-angelcore, aesthetic-dreamcore, shell-scroll-journey-scene]
---

# Volumetric cloud / cotton

A matte volumetric mass (translucent at wisps) that reacts to light: yes — silver-lining rim where lit, soft self-shadowed underbelly; and deforms: yes — billows and drifts continuously, edges never hold a fixed silhouette.

## Physical behavior

**Surface finish**: matte, micro-scattering — no specular point highlights ever; brightness comes from scattering depth

**Transparency**: translucent at edges/wisps; dense core is opaque

**Reacts to light**: yes — strong rim ("silver lining") on the sun side, warm-to-cool gradient through the mass, underbelly self-shadow

**Deforms**: yes — slow billow (30s+ cycles), wisp shear, drift; cloud-as-upholstery variants compress softly under objects

**Age / wear**: none — perpetually re-forming

## Implementation strategies

```yaml
css: |
  /* Soft cloud chip / background puff (approximation): */
  background: radial-gradient(60% 50% at 50% 60%, #fff 30%, #eef3f9 60%, transparent 75%);
  filter: blur(6px) drop-shadow(0 18px 30px rgba(120,140,170,0.25));
  /* stack 3-5 offset puffs per cloud; animate translate ±8px over 30s */
svg: |
  feTurbulence (fractalNoise, low baseFrequency) + feComposite into soft
  blob masks — good for animated wisp edges on section dividers.
webgl: |
  Hero-grade: raymarched density field (fbm noise) with single-scatter
  approximation, sun-direction uniform for the silver lining. Expensive —
  budget half-res render target + upscale. Alternative: layered sprite
  billboards (8-12 baked puff textures) with depth-sorted parallax, 0.5ms.
raster: rendered/photographed cloud cutout PNGs — the standard path for
  dream-stage composites (cloud-couch); rembg-cleaned edges must stay wispy
video: time-lapse drift loop for sky grounds; reads at 15-30s loops
```

## Reactive behaviors

**Pointer**: parallax only — cloud layers shift 4-12px against each other; the mass itself never follows the cursor (clouds don't care about you).

**Scroll**: vertical journeys ascend/descend through layers — density thickens then breaks open; pairs with `scroll-journey-scene` stations.

## Common implementation mistakes (avoid these)

- Specular highlight on a cloud (scattering ≠ gloss; one shiny pixel kills it)
- Hard cutout edges after rembg (re-feather; wisp alpha is the material)
- Uniform white — a cloud with no underbelly shadow reads as fog blob
- Fast billow (<15s) — turns weather into smoke
- Using it as wallpaper texture everywhere (one cloud event per viewport; it's a subject, not a pattern)

## Examples in the wild

- RIVR "Fluid Asset Streams" cloud-couch in a misty lake
- Dola watercolor-cloud + chrome-type hero
- Buzzentic dawn-cloud agency hero; Space Voyage pastel skies
- Apple "Shot on iPhone" sky composites

## Pairs with (prototype slugs)

- `aesthetic-surreal-dream-stage`
- `aesthetic-pastoral-serene`
- `aesthetic-angelcore`
- `shell-scroll-journey-scene`

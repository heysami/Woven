---
materialId: dispersion-prism-glass
name: Dispersion prism glass
family: digital
category: glass
surfaceFinish: glossy
transparency: transparent
pairsPrototypes: [style-holographic, style-liquid-glass, aesthetic-cosmic-horizon, aesthetic-defi-cosmic, style-glassmorphism]
---

# Dispersion prism glass

A glossy transparent surface that reacts to light: yes — refraction SPLITS into spectral rainbow at edges and thick sections (chromatic dispersion), casting small caustic rainbows onto surfaces behind.

## Physical behavior

**Surface finish**: glossy, optically pure (no frost, no texture — the optics ARE the texture)

**Transparency**: transparent with high refraction (IOR ~1.5-2.4 diamond-end); content behind bends visibly

**Reacts to light**: yes — spectral fringing intensifies at grazing angles and thick edges; a slow light orbit makes rainbow caustics crawl

**Deforms**: no — rigid solid (cube, prism, blob, shard); motion is rotation, not deformation

**Age / wear**: ageless

## Implementation strategies

```yaml
css: |
  /* Edge-dispersion approximation for cards/chips: */
  background: rgba(255,255,255,0.06);
  backdrop-filter: blur(2px);
  border: 1px solid transparent;
  border-image: conic-gradient(from var(--ang,0deg),
    #ff5e5e, #ffd75e, #6eff8a, #5ec8ff, #b95eff, #ff5e5e) 1;
  /* drive --ang from pointer position for the angle-shift read */
svg: |
  Three offset copies of the edge path (R/G/B) with 1-2px displacement +
  screen blend — cheap chromatic fringe for logos and hairline frames.
webgl: |
  The real thing for hero objects: refraction with per-channel IOR offset
  (sample env/backbuffer 3× with slightly different ratios), plus a fake
  caustic sprite projected behind the mesh. three.js MeshPhysicalMaterial
  (transmission:1, dispersion — r178+) covers it out of the box.
raster: pre-rendered prism-object PNG with baked dispersion for static slots
video: turntable loop of the object; dispersion shifts read even at 12s loops
```

## Reactive behaviors

**Light**: spectral fringe angle tracks pointer (rotate the conic border-image / env map); intensity peaks near edges at grazing view.

**Scroll/tilt**: hero object slowly rotates on scroll or idles on a turntable; caustic patch drifts opposite to rotation.

## Common implementation mistakes (avoid these)

- Rainbow gradient FILL (dispersion lives at edges and thick sections, not as a wash — a filled rainbow is holographic-foil)
- Fringe on body text (1px RGB split on type is the rgb-channel-split material, and an accessibility hazard at size)
- Dispersion + frost together (frost scatters; dispersion needs optical purity)
- Static fringe that ignores pointer/view angle — the angle-dependence IS the material

## Examples in the wild

- EVR Ventures glass cube ("navigating the route to impactful regeneration")
- Guardnet iridescent blob heroes
- Apple Vision Pro press renders (lens dispersion edges)
- Diamond/jewelry product configurators

## Pairs with (prototype slugs)

- `style-holographic`
- `style-liquid-glass`
- `aesthetic-cosmic-horizon`
- `aesthetic-defi-cosmic`

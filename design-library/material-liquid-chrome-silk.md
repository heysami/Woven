---
materialId: liquid-chrome-silk
name: Liquid chrome silk
family: hybrid
category: metal-fabric
surfaceFinish: glossy
transparency: opaque
pairsPrototypes: [style-silk-chrome-flow, aesthetic-luxury-cinematic-dark, aesthetic-cosmic-horizon, recipe-ai-foundry-dark, style-aurorism]
images:
  - src: material-liquid-chrome-silk.png
    reason: Material fidelity sample.
---

# Liquid chrome silk

A metallic-anisotropic surface that reacts to light: yes - specular streaks travel along fabric folds; hue drifts across an iridescent 2-3 stop family; and deforms: yes - slow continuous undulation like silk underwater.

## Physical behavior

**Surface finish**: glossy-anisotropic (silk lustre stretched along the fold direction, chrome-sharp at crests)

**Transparency**: opaque (edges may fade via depth-of-field, not via alpha)

**Reacts to light**: yes - highlight bands MIGRATE along folds as light/pointer moves; iridescent hue shift (blue→violet→magenta family) follows view angle

**Deforms**: yes - continuous slow ripple (20-40s loop); folds form and release; never static

**Age / wear**: ageless - this is an idealized rendered material, no scratches or patina

## Implementation strategies

```yaml
css: |
  /* Static fallback only - CSS cannot do true anisotropy. Use a pre-rendered
     frame as background-image + a traveling sheen overlay: */
  background: url(ribbon-frame.webp) center/cover no-repeat #07070c;
  &::after {
    background: linear-gradient(115deg, transparent 40%,
      rgba(160,140,255,0.35) 50%, transparent 60%);
    background-size: 300% 100%;
    animation: sheen 9s ease-in-out infinite;
    mix-blend-mode: screen;
  }
svg: |
  /* Not viable for the material itself; SVG only for masking the ribbon
     shape so HTML text can sit in the reserved quiet zone. */
webgl: |
  The real thing. Vertex-displaced ribbon mesh (sine stack or curl noise),
  anisotropic GGX highlight stretched along tangent, iridescence via
  thin-film approximation (hue = f(NdotV)), 2-3 stop gradient ramp texture.
  Pointer tilt rotates the light vector ±15°. ~2ms/frame at 1080p.
raster: pre-rendered loop frame(s) from the 3d/motion drawer - the standard path
video: 20-40s seamless loop, H.265, dark-crushed so blacks merge with the page
```

## Reactive behaviors

**Light**: highlight bands track pointer-x as a proxy light direction; on touch devices, devicetilt (gyro, gated) drives the same uniform. Subtle: ±10-15% band travel, never a full re-light.

**Scroll**: ribbon undulation speed may ease 0.5×→1.5× with scroll velocity; never scroll-position-locked (it's ambient, not scrubbed).

## Common implementation mistakes (avoid these)

- Blurred mesh gradient labeled "silk" - no visible folds = aurorism, a different material
- Rainbow full-spectrum hue sweep (pick one 2-3 stop family; full rainbow = holographic-foil's job)
- Headline sitting on the brightest fold (reserve a dark quiet zone)
- Ribbon repeated per section - ONE per page, hero only
- 60fps full-page shader on mobile without a static-frame fallback

## Examples in the wild

- 2025-26 dark AI-SaaS hero wave (motionsites.ai: Grow, Luminex, Power AI, ClearInvoice, Taskora, Wealth)
- Stripe Sessions keynote openers
- High-end agency reel backgrounds

## Pairs with (prototype slugs)

- `style-silk-chrome-flow`
- `aesthetic-luxury-cinematic-dark`
- `aesthetic-cosmic-horizon`
- `recipe-ai-foundry-dark`

---
shaderId: organic-distortion
name: Organic Distortion (ripple / swirl / twist / bulge domain-warp)
family: filter
category: image-effect
subCategory: distortion
role: overlay
defaultBlend: normal
animated: yes
needsSource: yes
stackable: yes
pairsPrototypes: [aesthetic-surreal-dream-stage, aesthetic-vaporwave, aesthetic-acid-design, aesthetic-dreamcore]
notForUseWhen: precise data viz, technical diagrams
---

# Organic Distortion (ripple / swirl / twist / bulge domain-warp)

Domain-warp the layer with flowing noise so it ripples, swirls, twists and bulges like a reflection on water or heat-haze on asphalt. The Figma `Warp` effect - a liquid that deforms anything beneath it without melting legibility (at low strength).

## Stack contract

- **Role:** FILTER - displaces a SOURCE beneath. (Self-sourcing if you feed it a gradient.)
- **Layer:** mid/top - sits above the layer it liquifies.
- **Default blend when stacked:** `normal` (re-samples beneath).
- **Animated:** yes - the warp noise scrolls on `u_time`; can also be pointer-driven (ripple from cursor).
- **Applies to:** the layer directly below (or the flattened stack).

## Implementation strategies

```yaml
webgl: |
  vec2 q = vec2(fbm(uv+u_time*0.1), fbm(uv+vec2(5.2,1.3)-u_time*0.1));
  vec2 warp = uv + (q-0.5) * u_strength;          // domain warp
  // modes: ripple = sin rings; swirl = rotate by r; bulge = scale by r
  vec3 col = texture(u_src, warp).rgb;
engine: |
  Figma effect: `Warp` (ripple/swirl/twist/bulge presets). mm-composer: `wave` + displacement.
  paper-design/shaders: `warp`, `swirl`, `water`.
svg: feTurbulence + feDisplacementMap (the canonical DOM liquid).
css: not on its own - needs a displacement map.
```

## Parameters (knobs)

- `mode` (ripple / swirl / twist / bulge / flow), `strength`, `frequency`, `speed`, `center` (for swirl/bulge), `pointerRipple`.

## Stacking recipes

- Organic Distortion (low strength) over `fluid-halftone` = the dots themselves ripple - double-liquid.
- Pointer-ripple mode over a hero image = water-surface interaction on hover.

## Common mistakes (avoid these)

- Strength so high the content liquifies past recognition (unless that IS the dreamcore brief).
- Warping text every frame (nausea + illegibility) - exclude type or keep amplitude < 2px.
- Plain sin-warp with no noise (reads as a cheap flag-wave) - layer fbm for organic motion.

## Pairs with (prototype slugs)

- `aesthetic-surreal-dream-stage`
- `aesthetic-vaporwave`
- `aesthetic-acid-design`
- `aesthetic-dreamcore`

---
materialId: atmosphere-rim-glow
name: Atmosphere rim glow
family: digital
category: emissive-edge
surfaceFinish: matte
transparency: opaque
pairsPrototypes: [aesthetic-cosmic-horizon, recipe-ai-foundry-dark, aesthetic-defi-cosmic]
images:
  - src: material-atmosphere-rim-glow.png
    reason: Material fidelity sample.
---

# Atmosphere rim glow

A matte near-black body whose EDGE carries a thin scattering glow — the planet-limb optic applied to surfaces: dark mass, luminous rim, void beyond.

## Physical behavior

**Surface finish**: matte dark body (the "night side"); the event is the 1-8px luminous rim tracing one edge

**Transparency**: opaque body; rim glow is additive light, brightest at the contact line, exponential falloff both inward and outward

**Reacts to light**: yes — the rim IS directional light made visible; rim position/intensity shifts with the implied light source (pointer, scroll, time-theme)

**Deforms**: no — applies to rigid arcs, cards, section boundaries

**Age / wear**: ageless

## Implementation strategies

```yaml
css: |
  /* Card / arc with one lit limb: */
  background: #060910;
  border-radius: 16px;
  box-shadow:
    inset 0 1px 0 rgba(141,208,255,0.55),     /* contact line */
    inset 0 6px 18px -8px rgba(77,166,255,0.35),  /* inward scatter */
    0 -10px 30px -12px rgba(77,166,255,0.30);     /* outward halo */
  /* hero planet-limb: an oversized border-radius arc cropped by overflow,
     same three-layer glow on its top edge */
svg: |
  Arc path stroked 3× (1px bright core, 4px mid, 12px blurred halo via
  feGaussianBlur), additive over a near-black ellipse — the hero limb.
webgl: |
  Only for true planet heroes: sphere with fresnel-powered atmosphere shell
  (additive, exp falloff), city-light texture on the night side. The card-
  level material never needs WebGL.
raster: planet-limb photography/render (photo orbital-space) for hero slots;
  the CSS treatment then echoes the same optic on cards below
video: slow terminator drift loop on hero limbs
```

## Reactive behaviors

**Pointer**: rim brightness/position eases toward the pointer-facing edge (proxy sun direction) — ±20% intensity, 300ms ease; one shared light direction for ALL elements on the page.

**Scroll**: optional dawn effect — rim warms (blue → blue-white → gold tinge) as a section fully enters view.

## Common implementation mistakes (avoid these)

- Rim on all four edges (it's directional scattering, not an outline — one edge, matching the page's single light direction)
- Thick neon border (the optic is thin: core ≤2px; the rest is falloff)
- Different rim directions on sibling cards (breaks the shared-sun physics)
- Saturated rim on a light background (the material requires void darkness around it)
- Pairing with drop shadows (the halo replaces shadow as the depth cue)

## Examples in the wild

- Planet-horizon SaaS heroes (Apex, Planet Orbit, Bloom AI, WISA Space)
- SpaceX webcast UI edges
- Linear 2024+ feature-card top-edge glows (the UI-scale echo)

## Pairs with (prototype slugs)

- `aesthetic-cosmic-horizon`
- `recipe-ai-foundry-dark`
- `aesthetic-defi-cosmic`

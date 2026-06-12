---
materialId: volumetric-light-shaft
name: Volumetric light shaft (god rays raking a dark stage)
family: digital
category: light-volume
surfaceFinish: n/a (light, not surface)
transparency: additive
pairsPrototypes: [aesthetic-sculptural-minimal, aesthetic-luxury-cinematic-dark, aesthetic-dark-academia, recipe-ai-foundry-dark, aesthetic-cosmic-horizon]
images:
  - src: material-volumetric-light-shaft.png
    reason: Material fidelity sample.
---

# Volumetric light shaft (god rays raking a dark stage)

Light treated as a MATERIAL occupying air: soft parallel shafts entering a
near-black scene from one high corner, raking across a single sculptural
object, dissolving into darkness before they reach the floor. The museum-
skylight read. Distinct from `material-volumetric-cloud` (matter shaped as
volume) and `material-atmosphere-rim-glow` (emission at an edge): shafts are
about light SCATTERING IN AIR — they exist only because the room is dark and
slightly dusty, and they belong to the scene, never to a UI element.

## Physical behavior

**Surface finish**: none — the material is a luminance gradient in air with
soft, feathered boundaries

**Transparency**: additive; whatever passes behind a shaft brightens, nothing
is occluded

**Reacts to light**: it IS the light story; the object it rakes catches a
matching specular on its upper surfaces (the agreement is mandatory)

**Deforms**: drifts — shafts breathe in width and intensity over 10–30s;
optional dust motes ride them

**Age / wear**: n/a

## Implementation strategies

```yaml
css: |
  /* 2–4 layered wedges, blurred, screen-blended, slow drift: */
  .shaft {
    position: absolute; inset: -10% -20%;
    background: linear-gradient(115deg,
      transparent 38%, rgba(235,240,255,0.085) 47%,
      rgba(235,240,255,0.03) 53%, transparent 62%);
    filter: blur(18px);
    mix-blend-mode: screen;
    animation: shaft-drift 24s ease-in-out infinite alternate;
  }
  /* duplicate at different widths/opacities/delays; never more than 4 */
  @keyframes shaft-drift { to { transform: translateX(4%) ; opacity: 0.8; } }
svg: |
  <polygon> wedges from a common origin point + feGaussianBlur 12–24 +
  screen blend — better than CSS when the shafts must originate at a
  visible source (a logo, a slit, a doorway).
webgl: |
  Hero grade: billboard planes with a soft gradient texture, additive
  blending, slight rotation jitter per plane; or a radial-blur post pass
  (sample toward the light's screen position, 32–48 taps) for true
  occlusion-aware rays around the hero object. Add 30–80 dust-mote
  particles drifting INSIDE the shaft bounds only.
raster: baked shafts in a hero render for static slots
video: included in scene loops — shafts breathe, never sweep fast
```

## Reactive behaviors

**Proximity/pointer**: shafts do NOT chase the cursor (they are architecture,
not UI). Permitted: a ±1.5° parallax tilt of the whole shaft layer on
pointer-x, damped 0.04 — the visitor shifting their head, not the light moving

**Hover**: none on the shafts; the OBJECT under them may brighten its specular

**Scroll**: shaft layer translates at 0.9× scroll (slight depth separation
from the object at 1.0×); intensity may rise as the hero section centers

**Reduced motion**: freeze the drift; keep the shafts (they are composition,
not decoration)

## Common implementation mistakes (avoid these)

- Shafts from nowhere (commit an origin — upper-left or upper-right, ONE
  corner, and every other shadow/specular in the scene must agree with it)
- Hard wedge edges (real scatter feathers; any visible straight boundary
  kills the read — blur is not optional)
- Light-on-light (shafts need a near-black field; over grey they read as
  smudges)
- Rainbow or saturated-hue shafts (the canon is achromatic with at most a
  2–4% warm or cool tint; colored rays drift into club-poster territory)
- Fast motion or pointer-chasing (museum light is still; the 10–30s breathe
  is the maximum energy budget)
- More than 4 shafts (one stage, one skylight; a comb of rays is a different,
  louder genre)

## Examples in the wild

- Spline "The Eternal ARC" (black torus raked by skylight shafts)
- Museum/exhibition microsites; Leica/Hasselblad product noir
- Game-title screens (the dust-mote-in-shaft idle)

## Pairs with (prototype slugs)

- `aesthetic-sculptural-minimal`
- `aesthetic-luxury-cinematic-dark`
- `aesthetic-dark-academia`
- `recipe-ai-foundry-dark`
- `aesthetic-cosmic-horizon`

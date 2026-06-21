---
materialId: paper-construction
name: Paper construction (die-cut strata / pop-up volume)
family: hybrid
category: paper
surfaceFinish: matte
transparency: opaque
pairsPrototypes: [aesthetic-sculptural-minimal, aesthetic-positivity-kawaii, recipe-brand-story-journey, shell-scroll-journey-scene, aesthetic-pastel-pop-fmcg]
images:
  - src: material-paper-construction.png
    reason: Material fidelity sample.
---

# Paper construction (die-cut strata / pop-up volume)

Paper as BUILT VOLUME, not surface texture: stacked sheets of colored stock
with die-cut apertures revealing 2-3 layers beneath, crisp cut edges catching
light, soft contact shadows in the gaps between strata - and, in the pop-up
variant, hinged constructions that fold open like a children's book. The
library's other paper entries (kraft, uncoated, torn-edge, vellum) are 2D
finishes; this one is paper with a Z-axis. Canon references: Daimaru
Matsuzakaya's generative-identity site (GLSL die-cut strata you scroll
*through the holes of*) and KOKUYO's "Curiosity is Life" (WebGL pop-up book
whose page-flip is the scene transition).

## Physical behavior

**Surface finish**: matte cardstock with visible tooth; cut edges are the
material's specular moment - a hairline of lighter fiber where the die sliced

**Transparency**: opaque per sheet; DEPTH comes from apertures, never from
translucency (that's vellum)

**Reacts to light**: yes - each stratum casts a soft contact shadow (2-10px,
~20% opacity) onto the one below; shadow offset shifts with light/pointer
direction, which is what sells the stack

**Deforms**: pop-up variant only - sheets rotate on crease hinges (single
axis, 0-180°); sheets never bend mid-panel, paper folds at creases

**Age / wear**: ageless (fresh-cut stock; aging it turns it into a different
entry - foxing-stain / parchment)

## Implementation strategies

```yaml
css: |
  /* DOM strata - each layer a stacked element with cut-out shapes: */
  .stratum {
    background: var(--stock);            /* flat saturated cardstock color */
    clip-path: <aperture polygon/circle>; /* the die cut */
    filter: drop-shadow(0 4px 6px rgb(0 0 0 / .18));  /* contact shadow */
  }
  /* stack 3-4 strata with increasing z and 8-16px translate offsets;
     drop-shadow (not box-shadow) follows the clip-path silhouette */
svg: |
  <feDropShadow> per layer group; apertures as <mask> so one SVG holds the
  whole stack; add a 1px lighter stroke on cut edges (the sliced-fiber line).
webgl: |
  Hero register: each sheet a thin extruded plane (2-4mm), MeshStandardMaterial
  { roughness: 0.9, metalness: 0 } with paper-grain normal map; apertures via
  alpha-tested cutout textures or real geometry holes; one directional light
  raking ~30° so strata shadows fall naturally; camera can travel THROUGH an
  aperture into the next layer (the daimaru move). Pop-up: hinge groups
  rotating on shared crease axes, driven 0→1 by scroll or page-flip events.
raster: pre-rendered stack for static slots - bake 3 visible strata + shadows
```

## Reactive behaviors

**Proximity**: shadow offsets lean away from the cursor (light follows
pointer), ±3px over 400px falloff - the stack tilts perceptibly without moving

**Hover**: the top stratum lifts 2-4px (shadow grows + softens); apertures
do NOT resize (the die is cut)

**Click/tap**: pop-up variant - a hinged element folds open one step;
strata variant - at most a 1px press-down on the touched sheet

**Scroll**: strata translate at different rates (0.9× / 1.0× / 1.1×) for
intra-stack parallax; or the camera dives through an aperture as the scene
transition (pairs with motion-scene-zoom-through)

## Common implementation mistakes (avoid these)

- box-shadow on a clipped element (the shadow ignores the cut shape - use
  filter: drop-shadow, which follows the silhouette)
- Gradient-shaded "depth" without an actual lower layer visible through the
  aperture (a hole must show SOMETHING - the next stock color, at minimum)
- Translucent sheets (paper construction is opaque; translucency collapses the
  stack into vellum)
- Bending a sheet mid-panel in the pop-up variant (paper folds at creases
  only; mid-panel curve reads as cloth)
- Equal shadow on all strata (lower layers sit in MORE shadow - deepen
  opacity 4-6% per level down)
- Photoreal paper grain at full strength on every layer (grain whispers;
  the construction - cuts, shadows, stock colors - does the talking)

## Examples in the wild

- daimaru-matsuzakaya.com/vi - GLSL die-cut strata; narration typeset inside
  the apertures; scroll dives through the holes
- kokuyo.com "Curiosity is Life" - WebGL pop-up book, page-flip foley,
  pastel cardstock objects
- Physical referents: construction-paper collage, pop-up books, laser-cut
  paper art (Yulia Brodskaya territory adjacent)

## Pairs with (prototype slugs)

- `aesthetic-sculptural-minimal`
- `aesthetic-positivity-kawaii`
- `aesthetic-pastel-pop-fmcg`
- `recipe-brand-story-journey`
- `shell-scroll-journey-scene`

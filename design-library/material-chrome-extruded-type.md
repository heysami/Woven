---
materialId: chrome-extruded-type
name: Chrome extruded type (typography as mirrored object)
family: digital
category: metal-typography
surfaceFinish: metallic
transparency: opaque
pairsPrototypes: [aesthetic-luxury-cinematic-dark, aesthetic-urbling, style-bold-display, aesthetic-y2k-futurism, aesthetic-frutiger-chromecore]
images:
  - src: material-chrome-extruded-type.png
    reason: Material fidelity sample.
---

# Chrome extruded type (typography as mirrored object)

Display typography built as a 3D object: extruded letterforms with mirror-chrome
faces that reflect an environment, specular sweeps crawling across the glyphs
as the view or light moves. The type is no longer set ON the page - it is
STAGED in it, like a sign in a showroom. Sibling of `material-chrome-mirror`
(chrome as UI surface) and `material-liquid-chrome-silk` (chrome as cloth);
this one is chrome as LETTERFORM, and the env-map rule is absolute: a silver
gradient without an environment lookup reads as plastic, not chrome.

## Physical behavior

**Surface finish**: mirror-metallic; bevel edges catch the brightest speculars;
faces carry a recognizable (if abstract) environment reflection

**Transparency**: opaque

**Reacts to light**: yes - the defining behavior; a specular band SWEEPS across
the glyph faces as light/view angle changes; static chrome type is dead chrome
type

**Deforms**: no - rigid; motion is light/camera, not letterform

**Age / wear**: ageless (a scratched variant shifts it toward grunge registers)

## Implementation strategies

```yaml
css: |
  /* 2.5D approximation for headlines - env gradient + animated sweep: */
  background: linear-gradient(105deg,
    #2a2e38 0%, #e8ebf0 18%, #6a7180 32%, #f5f7fa 47%,
    #474d5c 62%, #d8dce4 80%, #30343e 100%);
  background-size: 220% 100%;
  -webkit-background-clip: text; background-clip: text; color: transparent;
  /* drive background-position-x from --px (pointer) or a 9s ease loop; */
  /* add 2-4 layered text-shadows below for the extrusion read */
  text-shadow: 0 1px 0 #1a1d24, 0 2px 0 #14161c, 0 3px 0 #0e1014,
               0 10px 24px rgba(0,0,0,0.5);
svg: |
  <text> duplicated: back copy offset for extrusion depth, front copy filled
  with a <linearGradient> whose stops animate via <animate> - sharable,
  crisp at any size.
webgl: |
  The real thing: three.js TextGeometry (or pre-modeled glyphs) +
  MeshPhysicalMaterial { metalness: 1, roughness: 0.08-0.18,
  envMap: studio HDRI }. Slow yaw ±6° on pointer (damped 0.06 lerp);
  the env reflection sliding across the faces is the spectacle.
  Bevel ON (bevelSize ~2% of cap height) - unbeveled chrome has no
  edge speculars and reads as flat grey.
raster: baked render for static heroes (bake the sweep mid-travel)
video: 8-12s light-orbit loop over fixed type
```

## Reactive behaviors

**Proximity**: specular band position leans toward cursor, falloff 1/d² over
500px (viewport-level --mx)

**Hover**: sweep speed eases up; reflection contrast rises 10% - the sign
catches the light for you

**Click**: brief specular flare at the click point (the §1.7 metal canon)

**Tilt (mobile)**: gamma drives the sweep position - the hold-it-in-your-hand
foil-card read

## Common implementation mistakes (avoid these)

- Gradient-only "chrome" with no environment structure (needs recognizable
  light/dark BANDS - a smooth silver ramp is plastic)
- Chrome on body text or UI labels (display sizes only, one headline per
  view; chrome paragraphs are unreadable and melt the luxury read)
- Static sweep (the angle-dependence IS the material - commit pointer, tilt,
  or a slow loop, never none)
- Rainbow hue in the reflection (that drifts into holographic-foil; chrome
  is achromatic with at most a cool/warm tint commitment)
- Skipping the extrusion shadow stack (a chrome FACE with no depth reads as
  background-clip gradient text, the most common AI-tell)

## Examples in the wild

- Spline "Elegant Beauty of Dark Aesthetics" (chrome caps over volcanic-rock
  field)
- Y2K rap/metal album lettering; UrBling-era logos (the cultural referent)
- Apple TV+ chrome wordmark treatments; fashion-drop microsites with
  mirrored mastheads

## Pairs with (prototype slugs)

- `aesthetic-luxury-cinematic-dark`
- `aesthetic-urbling`
- `style-bold-display`
- `aesthetic-y2k-futurism`
- `aesthetic-frutiger-chromecore`

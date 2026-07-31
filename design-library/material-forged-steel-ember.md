---
materialId: forged-steel-ember
name: Forged Steel Ember (incandescent heat-gradient metal)
family: analog
category: metal
surfaceFinish: matte (mill scale) with emissive incandescent passages
scope: object
transparency: opaque
pairsPrototypes: [aesthetic-arknights-endfield-industrial, aesthetic-industrial-catalog, aesthetic-zenless-zone-zero-retrofuture, style-bold-display, style-brutalist-raw]
images:
  - src: material-forged-steel-ember.png
    reason: Material fidelity sample.
---

# Forged Steel Ember (incandescent heat-gradient metal)

Iron under the hammer: matte scale-black steel that glows from within along a strict heat ramp - black through dull red, cherry, orange, to white heat - with spark showers and flaking mill scale.

## Physical behavior

**Surface finish**: matte; forge-black ground flecked with mill scale, anvil-gray satin on worked faces

**Transparency**: opaque; incandescence is emission, not translucency

**Reacts to light**: barely - hot passages EMIT instead; cold steel swallows light

**Deforms**: yes - drawn, upset, flattened; edges chip and scale shatters off

**Age / wear**: scale flake, hammer marks, quench mottling

## Implementation strategies

```yaml
css: |
  /* the heat ramp is canonical - never a flat orange */
  --forge-black: #0a0a0c; --anvil-gray: #3b3f45; --dull-red: #7a1e12;
  --cherry: #ff4b00; --white-heat: #ffb400; --white-hot: #fff7f0;
  .hot-bar { background: linear-gradient(90deg,
    var(--forge-black), var(--dull-red) 20%, var(--cherry) 45%,
    var(--white-heat) 70%, var(--white-hot) 88%); 
    box-shadow: 0 0 24px 4px rgba(255,75,0,0.55), 0 0 64px 12px rgba(255,75,0,0.25); }
  /* cold chrome: matte black with scale-fleck texture, chalky stencil type */
  .cold { background: var(--forge-black); color: #e8e6e2; }
canvas: |
  spark shower: particle burst from the strike point - fast, gravity-arced streaks
  in cherry/white-heat, 300-600ms lifetime, emitted ON ACTION only
svg: |
  mill scale: coarse dark flecks via feTurbulence threshold, denser near edges
webgl: |
  shader: blackbody ramp keyed to a "heat" uniform; bloom radius scales with heat
raster: forge-floor and anvil-steel photos for the cold texture plates
```

## Reactive behaviors

**Light**: hot elements are the light source - they cast orange bloom onto neighboring cold steel

**Highlight**: activation = heating; the element climbs the ramp toward white heat and its bloom widens

**Depth**: minimal; weight comes from mass and glow, not elevation

**Parallax**: none; sparks are the only motion layer

## Common implementation mistakes (avoid these)

- uniform orange glow (incandescence has anatomy: white-hot core, cherry mid, dull-red falloff into black - always a gradient)
- glow on cold elements (only active/hot things emit; idle steel is matte black)
- polished or mirrored steel (forged bar is matte with scale - reflectivity belongs to other metals)
- sparks as a constant ambient particle field (sparks are consequences of a strike; they burst and die)
- missing texture (scale flecks and hammer marks separate forge steel from generic dark UI)

## Examples in the wild

- blacksmithing and power-hammer forging footage
- foundry and rolling-mill photography
- industrial game UIs built on heat-and-strike feedback

## Pairs with (prototype slugs)

- `aesthetic-arknights-endfield-industrial`
- `aesthetic-industrial-catalog`
- `aesthetic-zenless-zone-zero-retrofuture`
- `style-bold-display`
- `style-brutalist-raw`

## Differentiation

- vs `material-brushed-aluminum`: aluminum is cold, satin, anisotropic - it reflects along the grain and never emits; ember steel is matte black and glows from within
- vs `material-chrome-mirror`: chrome is pure specular environment reflection; forged steel has almost none - its light is blackbody emission on a heat ramp

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

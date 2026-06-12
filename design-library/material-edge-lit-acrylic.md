---
materialId: edge-lit-acrylic
name: Edge-lit acrylic (frosted slab glowing from within)
family: digital
category: glass-emissive
surfaceFinish: satin-frosted
transparency: translucent-emissive
pairsPrototypes: [aesthetic-depin-hardware, aesthetic-cassette-futurism, recipe-ai-foundry-dark, style-dense-mono-dark, aesthetic-frutiger-dark-aero]
images:
  - src: material-edge-lit-acrylic.png
    reason: Material fidelity sample.
---

# Edge-lit acrylic (frosted slab glowing from within)

A frosted acrylic card or slab that carries light INSIDE its volume — edges
glow brightest, the interior holds a soft suspended luminance, and the glow
SPILLS volumetrically onto nearby matte surfaces. The physical referent is an
edge-lit LED sign or a backlit boarding pass. Distinct from
`material-atmosphere-rim-glow` (an emissive EDGE on a dark shape) and from
`material-frosted-glass` (passive scatter): this slab is a light SOURCE, and
the air gap between it and its neighbors is part of the material — warm bloom
filling the space between two objects is the signature connection cue.

## Physical behavior

**Surface finish**: satin-frosted faces; polished edges that pipe light (edges
read 2–3× brighter than faces)

**Transparency**: translucent; internal content (barcode, chip, type) floats
as soft silhouettes inside the volume

**Reacts to light**: it IS the light; nearby matte surfaces within ~1 slab
height catch a tinted gradient falloff

**Deforms**: no — rigid slab

**Age / wear**: ageless

## Implementation strategies

```yaml
css: |
  /* A convincing DOM card — the three-layer glow stack: */
  background: linear-gradient(160deg,
    rgba(255,140,80,0.10), rgba(255,140,80,0.04) 55%, rgba(255,140,80,0.12));
  backdrop-filter: blur(10px) brightness(1.1);
  border: 1px solid rgba(255,190,150,0.35);          /* the lit edge */
  border-radius: 14px;
  box-shadow:
    inset 0 0 24px rgba(255,150,90,0.18),            /* interior luminance */
    0 0 18px rgba(255,140,80,0.22),                  /* near spill */
    0 24px 80px -20px rgba(255,120,60,0.30);         /* volumetric pool */
  /* internal content (QR, mono labels) at opacity 0.55, blur(0.4px) —
     suspended-in-acrylic read */
svg: |
  feGaussianBlur stacks for the spill; <rect> edge strokes with wide soft
  duplicates beneath — good for diagram-grade cards.
webgl: |
  Hero grade: MeshPhysicalMaterial { transmission: 1, roughness: 0.55,
  thickness: 0.8, emissive: accent, emissiveIntensity: 0.25 } + a
  RectAreaLight inside/behind the slab + bloom pass (threshold ~0.7).
  For the between-objects bloom: a billboard sprite with radial gradient
  in the air gap, additive — cheaper and steadier than real volumetrics.
raster: baked render for static slots (bake the spill onto the substrate)
video: slow 8–12s breathe loop (emissive ±15%)
```

## Reactive behaviors

**Proximity**: interior luminance leans toward the cursor (shift the inset
glow's origin), falloff 1/d² over 400px

**Hover**: emissive rises 25%, the spill pool widens ~10% — the card wakes

**Click**: 200ms bright pulse that travels edge → interior → spill (one frame
of "data accepted")

**Connection moment** (the signature): when two cards/objects align or pair,
the air-gap bloom blooms in over 400ms ease-out — light announces the
handshake before any UI copy does

## Common implementation mistakes (avoid these)

- Uniform glow (edges MUST outshine faces — flat glow reads as a tinted
  panel, not edge-lit acrylic)
- Glow without spill (a luminous object that doesn't light its neighbors
  floats in a different scene; the substrate gradient sells the physics)
- Saturated neon at full field (this is restrained hardware light — one warm
  or one cool accent, dark matte world around it)
- Crisp internal content (anything inside the slab gets slight blur + reduced
  opacity; sharp content reads as printed ON the surface instead)
- Multiple competing light hues per scene (ONE accent; a second hue is
  allowed only as the pairing object's reply)

## Examples in the wild

- Spline "Connecting Card" (frosted boarding pass + chip card, orange bloom
  in the gap)
- Nothing Phone / Teenage Engineering hardware glow language
- visionOS window edge luminance; DePIN device marketing renders

## Pairs with (prototype slugs)

- `aesthetic-depin-hardware`
- `aesthetic-cassette-futurism`
- `recipe-ai-foundry-dark`
- `style-dense-mono-dark`
- `aesthetic-frutiger-dark-aero`

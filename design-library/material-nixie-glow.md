---
materialId: nixie-glow
name: Nixie Glow (gas-discharge digits in glass envelopes)
family: hybrid
category: display
surfaceFinish: glossy glass envelope over matte blackened-steel chassis
scope: object
transparency: transparent envelope; digits are solid wire silhouettes
pairsPrototypes: [aesthetic-atompunk, aesthetic-cassette-futurism, aesthetic-industrial-catalog, style-skeuomorphism, aesthetic-dark-academia]
images:
  - src: material-nixie-glow.png
    reason: Material fidelity sample.
---

# Nixie Glow (gas-discharge digits in glass envelopes)

Laboratory-counter digits: each glass envelope holds a physical stack of shaped wire cathodes - one digit lit in incandescent orange, the others visible as layered dark silhouettes behind and in front of it - fronted by a fine anode mesh, mounted on blackened steel with engraved label plates.

## Physical behavior

**Surface finish**: glossy borosilicate envelope (vertical highlight streaks) over matte blackened steel; hexagonal anode mesh visible in front of the digit stack

**Transparency**: envelope transparent; the digit stack gives true physical DEPTH - unlit digits occlude and layer

**Reacts to light**: the glow is self-emitted; glass picks up slim environment highlights

**Deforms**: no

**Age / wear**: cathode poisoning (uneven glow along the wire), slight flicker

## Implementation strategies

```yaml
css: |
  --nixie-glow: #ff6a00; --chassis: #0e0f11; --mesh-gray: #3a3f46;
  --glass-hl: #a6abb2; --engrave: #5b6168;
  /* each digit = stacked layers: unlit cathodes + one lit */
  .tube { position: relative; }
  .unlit { color: transparent; -webkit-text-stroke: 1px #23262b; }
  .lit { position: absolute; inset: 0; color: var(--nixie-glow);
    -webkit-text-stroke: 1px #ffd9b0;
    text-shadow: 0 0 4px #ff8c33, 0 0 14px rgba(255,106,0,0.8),
                 0 0 34px rgba(255,106,0,0.35); }
svg: |
  envelope: rounded-top capsule with 1px rim, two vertical highlight streaks,
  a top nipple; anode mesh as a hex <pattern> at 25-35% over the digit stack
detail: |
  unlit digits BOTH behind and in front of the lit one (front layers at lower
  opacity) - that occlusion sells the physical stack;
  label plates: dark metal chip, inset engraved caps, two screw dots
animation: |
  digit change = old cathode dims (80ms) while new one ignites with a brief
  over-bright flash; idle glow breathes +-3% at ~2Hz
```

## Reactive behaviors

**Light**: lit digits cast warm orange onto the mesh, envelope rim, and neighboring chassis

**Highlight**: active elements ignite (outline-only becomes glowing); focus adds the over-bright ignition flash

**Depth**: real - the cathode stack layers inside the glass; front unlit digits partially occlude the lit one

**Parallax**: a few px of internal shift between stack layers on pointer move sells the tube depth

## Common implementation mistakes (avoid these)

- the lit digit floating alone (the dark cathode stack around it is the identity of the material - never omit it)
- neon-tube outline lettering (nixie digits are solid shaped-wire silhouettes with volumetric glow, not hollow tube strokes)
- cool or cyan glow (neon gas discharge is warm orange, always - #ff6a00 territory)
- no glass envelope (without the capsule, rim highlights, and mesh, it is just glowing text)
- crisp glow edges (discharge glow is soft and layered: white-hot wire core, orange corona, wide falloff)
- using nixies for body text (tubes display digits and short codes; prose belongs to the chassis labels)

## Examples in the wild

- Soviet IN-series and Burroughs nixie tubes
- laboratory frequency counters and event counters
- boutique nixie clocks and watches

## Pairs with (prototype slugs)

- `aesthetic-atompunk`
- `aesthetic-cassette-futurism`
- `aesthetic-industrial-catalog`
- `style-skeuomorphism`
- `aesthetic-dark-academia`

## Differentiation

- vs `material-crt-phosphor`: CRT is a scanned raster surface; nixie is a physical stack of shaped wire digits inside a glass envelope - depth, occlusion, and a single warm hue
- vs `material-led-segment-display`: LED segments are flat emissive shapes with ghost cells; nixie digits are full continuous numerals with the OTHER numerals dark around them, behind glass with an anode mesh

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

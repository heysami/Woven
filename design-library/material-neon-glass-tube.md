---
materialId: neon-glass-tube
name: Neon Glass Tube (hand-bent gas-discharge craft object)
family: analog
category: glass
surfaceFinish: glossy glass tube, self-emissive discharge core
scope: object
transparency: transparent tube; the gas column emits
pairsPrototypes: [aesthetic-vaporwave, aesthetic-luxury-cinematic-dark, aesthetic-cyberpunk, aesthetic-y2k-futurism, style-skeuomorphism]
images:
  - src: material-neon-glass-tube.png
    reason: Material fidelity sample.
---

# Neon Glass Tube (hand-bent gas-discharge craft object)

Real bent-glass neon: letterforms are one continuous tube of constant gauge, script drawn in a single stroke with round glass-radius bends, terminated by red electrode caps, powered by visible transformer hardware - the halation glow belongs to a physical object, not a filter.

## Physical behavior

**Surface finish**: glossy borosilicate tube; the discharge core is white-hot, wrapped in the gas color, wrapped in wide halation

**Transparency**: tube transparent; unlit sections (bridges, blocked-out returns) read as dark glass

**Reacts to light**: it IS the light - it throws afterglow onto the wall and nearby hardware

**Deforms**: no, but every bend obeys a minimum glass radius; no sharp corners exist

**Age / wear**: flicker on strike-up, a weak electrode dimming one end, gas hum

## Implementation strategies

```yaml
css: |
  --room: #0b0f16; --discharge: #2a6bff; --afterglow: #0d1a33; --electrode: #ff5a3c;
  body { background: radial-gradient(120% 100% at 50% 40%, #101726, var(--room)); }
svg: |
  the ONLY honest construction: a single <path> per tube run,
  fill=none, stroke-linecap=round, stroke-linejoin=round, CONSTANT stroke-width;
  layered strokes on the same path:
    1. halo: stroke-width 14-20, blur 12px, gas color at 30%
    2. tube: stroke-width 6, blur 2px, gas color
    3. core: stroke-width 2.5, no blur, near-white (#eaf2ff)
  bridges (unlit jumps between letters): separate path segments in dark glass
  (#1a2230, no glow) - do NOT glow the whole word contour
hardware: |
  electrode caps: small metal-and-red-glass capsules at each path START and END;
  glass supports / wall standoffs as tiny gray ticks along long runs;
  transformer: matte powder-coat box with entry wires, placed at the sign base
typography: |
  script faces with monoline construction bend best; letterforms must be
  traceable as one line a bender could actually bend - dead-end strokes get
  a visible return or a blocked-out (painted) section
animation: |
  strike-up: 2-3 rapid flickers then steady; idle: +-2% intensity shimmer;
  hover: brighten core and widen halo 10-15%
```

## Reactive behaviors

**Light**: casts colored afterglow on the surface behind it (soft wide radial matching the gas color)

**Highlight**: active = brighter discharge and wider halation; never a color swap mid-tube (one tube = one gas)

**Depth**: the tube sits proud of the wall - faint offset shadow of the dark glass under the glow

**Parallax**: none

## Common implementation mistakes (avoid these)

- glow filter on ordinary type (the letterform must be a single continuous constant-width stroke with round bends - if a glass bender could not bend it, it is not neon)
- sharp corners (glass bends have a minimum radius; every join is a curve)
- variable stroke width (tube gauge is constant along the entire run; calligraphic modulation breaks the material)
- missing electrodes and hardware (the red-tipped caps, supports, and transformer are what make it an object instead of an effect)
- halo without the white-hot core (discharge is layered: near-white center line, gas color, wide halation)
- glowing the bridges (the jumps between letters are unlit dark glass; lighting them turns craft into contour)

## Examples in the wild

- hand-bent neon sign shops and bender demos
- motel, diner, and cocktail-bar script signage
- gallery neon (Tracey Emin, Bruce Nauman)

## Pairs with (prototype slugs)

- `aesthetic-vaporwave`
- `aesthetic-luxury-cinematic-dark`
- `aesthetic-cyberpunk`
- `aesthetic-y2k-futurism`
- `style-skeuomorphism`

## Differentiation

- vs cyberpunk neon glow filters: those apply screen-space glow to arbitrary shapes; this is a craft object - continuous single-tube paths, glass radii, electrodes, bridges, and hardware, with halation as a physical consequence
- vs `material-crt-phosphor`: CRT glow is a scanned raster surface; neon is one bent luminous line in real space that lights its surroundings

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

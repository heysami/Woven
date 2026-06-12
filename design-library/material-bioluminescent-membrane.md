---
materialId: bioluminescent-membrane
name: Bioluminescent membrane
family: digital
category: organic-emissive
surfaceFinish: glossy
transparency: translucent
pairsPrototypes: [aesthetic-bioluminescent-deep, aesthetic-fairycore, aesthetic-defi-cosmic, shell-scroll-journey-scene]
images:
  - src: material-bioluminescent-membrane.png
    reason: Material fidelity sample.
---

# Bioluminescent membrane

A translucent organic tissue that reacts to light: inverted — it IS the light source; subsurface glow pulses slowly from within, falling off into true black with no ambient fill.

## Physical behavior

**Surface finish**: wet-glossy outer film over soft subsurface interior (jellyfish bell, lantern-flora petal)

**Transparency**: translucent — inner structures (veins, gills, cores) silhouette through the tissue

**Reacts to light**: self-emissive — external light is nearly irrelevant; the membrane glows from inside, brightest at the core/veins, dimming toward edges

**Deforms**: yes — slow pulse (4-8s breathing cycle), tendril drift, medusa-bell contraction

**Age / wear**: living — variation between individuals, never two identical

## Implementation strategies

```yaml
css: |
  /* Glow-pulse for UI elements adopting the register (badges, orbs): */
  background: radial-gradient(closest-side,
    rgba(62,232,255,0.9), rgba(46,124,255,0.35) 55%, transparent 75%);
  filter: blur(0.5px) drop-shadow(0 0 24px rgba(62,232,255,0.45));
  animation: biopulse 6s ease-in-out infinite;  /* scale 1→1.04 + brightness 1→1.25 */
svg: |
  Layered ellipses with feGaussianBlur (core sharp → halo soft) + animated
  opacity for the pulse; veins as thin glowing strokes (stroke + blur dup).
webgl: |
  The real thing for hero organisms: translucent mesh with emissive interior
  texture, fake-subsurface (rim falloff inverted: brightest at thin parts),
  additive halo billboard, vertex-animated bell/tendrils. Particles
  (marine snow) as a separate slow drift system.
raster: rendered organism PNG with baked glow + transparent bg for static slots
video: dark-water loop; organism pulse reads even in 10s loops
```

## Reactive behaviors

**Pointer**: organism shies or leans — tendrils ease 2-4° toward/away from cursor with heavy lag (1-2s); glow brightens +15% on approach. Never snaps.

**Scroll** (journey formats): depth increases — glow hue cools, particle density rises, organism count thins.

## Common implementation mistakes (avoid these)

- Ambient fill light in the scene (kills the abyss — the organism must be the ONLY light)
- Neon `text-shadow` on every label "to match" (the glow belongs to the organism, not the chrome)
- Fast pulse (<3s reads as alarm, not breathing)
- Radial-gradient blob with no internal structure (lava lamp, not life — veins/cores required)
- Electric-blue everywhere: keep UI ink matte and dark; one glow family

## Examples in the wild

- Hashgraph Ventures (glowing jellyfish — "the next wave of venture capital")
- Totem crypto ecosystem totems
- *Blue Planet II* "The Deep" sequences; *Avatar* night flora

## Pairs with (prototype slugs)

- `aesthetic-bioluminescent-deep`
- `aesthetic-fairycore`
- `shell-scroll-journey-scene`

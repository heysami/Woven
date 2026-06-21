---
materialId: glossy-plastic-aqua
name: Glossy Plastic (Frutiger Aero / Apple Aqua / Windows Vista wet button)
family: digital
category: plastic
surfaceFinish: glossy
transparency: opaque
pairsPrototypes: [aesthetic-frutiger-aero, aesthetic-y2k-futurism, aesthetic-frutiger-chromecore, style-skeuomorphism]
images:
  - src: material-glossy-plastic-aqua.png
    reason: Material fidelity sample.
---

# Glossy Plastic (Frutiger Aero / Apple Aqua / Windows Vista wet button)

A glossy surface that reacts to light: yes - single top-half specular gloss and deforms: minor on press (inner shadow grows).

## Physical behavior

**Surface finish**: glossy

**Transparency**: opaque

**Reacts to light**: yes - single top-half specular gloss

**Deforms**: minor on press (inner shadow grows)

**Age / wear**: ageless

## Implementation strategies

```yaml
css: |
  background:
    linear-gradient(180deg,
      rgba(255,255,255,0.55) 0%,
      rgba(255,255,255,0.10) 45%,
      rgba(0,0,0,0.0) 46%,
      rgba(0,0,0,0.08) 100%
    ),
    linear-gradient(180deg, oklch(60% 0.18 240) 0%, oklch(45% 0.20 240) 100%);
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,0.7),
    inset 0 -1px 0 rgba(0,0,0,0.15),
    0 1px 3px rgba(0,0,0,0.25),
    0 4px 12px rgba(0,0,0,0.12);
  border-radius: 14px;
raster: optional photographic plate beneath the button group (sky / water)
```

## Reactive behaviors

**Light**: highlight is fixed (button has one canonical light); subtle background shift on scroll

**Highlight**: hover increases the top-half gloss opacity 0.05

**Depth**: press inverts the inner shadow (raised → inset)

**Parallax**: substrate parallaxes if photographic plate is present

## Common implementation mistakes (avoid these)

- gloss covers full height (collapses to generic gradient)
- flat solid colour with no gradient
- cool greyscale instead of saturated colour
- sharp drop shadow with no inset highlight
- >40% lightness step (reads plastic-toy)

## Examples in the wild

- iOS 1-6 lozenge icons
- Windows Vista Start button
- Apple Aqua buttons

## References

- https://en.wikipedia.org/wiki/Aqua_(user_interface)

## Pairs with (prototype slugs)

- `aesthetic-frutiger-aero`
- `aesthetic-y2k-futurism`
- `aesthetic-frutiger-chromecore`
- `style-skeuomorphism`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

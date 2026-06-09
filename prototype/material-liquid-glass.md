# Liquid Glass (Apple WWDC25) (material)


**Tag:** material-liquid-glass
  ·  **Family:** digital  ·  **Category:** glass  ·  **Surface:** glossy  ·  **Transparency:** transparent

A glossy surface (transparent) that reacts to light: yes — specular highlight tracks tilt/pointer; chromatic edge and deforms: minor on press.

**Examples in the wild**

- iOS 26 system
- Apple Music 2025
- visionOS Glass Materials
- Halide camera app

**Common implementation mistakes (avoid these)**

- displacement map applied to text (illegible)
- displacement scale > 30 (text swims even on chrome)
- glass nested inside glass (HIG explicitly forbids it)

**Pairs with** (prototype slugs)

- `style-liquid-glass`
- `style-glassmorphism`
- `aesthetic-frutiger-aero`
- `aesthetic-frutiger-dark-aero`
- `aesthetic-holographic`
- `aesthetic-y2k-futurism`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of the material -->

---

_Full entry in [docs/research/material-library.md](../docs/research/material-library.md)._

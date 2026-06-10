# Glossy Plastic (Frutiger Aero / Apple Aqua / Windows Vista wet button) (material)

**Tag:** material-glossy-plastic-aqua  ·  **Family:** digital  ·  **Category:** plastic · glossy

A glossy digital surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: glossy-plastic-aqua
  name: Glossy Plastic (Frutiger Aero / Apple Aqua / Windows Vista wet button)
  family: digital
  category: plastic
  physicalBehavior:
    surfaceFinish: glossy
    transparency: opaque
    reactsToLight: yes — single top-half specular gloss
    deforms: minor on press (inner shadow grows)
    age: ageless
  implementationStrategies:
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
  reactiveBehaviors:
    light: highlight is fixed (button has one canonical light); subtle background shift on scroll
    highlight: hover increases the top-half gloss opacity 0.05
    depth: press inverts the inner shadow (raised → inset)
    parallax: substrate parallaxes if photographic plate is present
  pairsWith:
    prototypeStyles: [aesthetic-frutiger-aero, aesthetic-y2k-futurism, aesthetic-frutiger-chromecore, style-skeuomorphism]
  killsTheIllusion:
    - gloss covers full height (collapses to generic gradient)
    - flat solid colour with no gradient
    - cool greyscale instead of saturated colour
    - sharp drop shadow with no inset highlight
    - >40% lightness step (reads plastic-toy)
  examples:
    - iOS 1–6 lozenge icons
    - Windows Vista Start button
    - Apple Aqua buttons
  references:
    - https://en.wikipedia.org/wiki/Aqua_(user_interface)
```

## Common implementation mistakes (avoid these)

- gloss covers full height (collapses to generic gradient)
- flat solid colour with no gradient
- cool greyscale instead of saturated colour

## Pairs with (prototype slugs)

- `aesthetic-frutiger-aero`
- `aesthetic-y2k-futurism`
- `aesthetic-frutiger-chromecore`
- `style-skeuomorphism`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 261–307 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

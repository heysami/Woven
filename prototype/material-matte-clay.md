# Matte Clay (claymorphism) (material)

**Tag:** material-matte-clay  ·  **Family:** digital  ·  **Category:** clay · matte

A matte digital surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: matte-clay
  name: Matte Clay (claymorphism)
  family: digital
  category: clay
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: yes — inset highlight + dark inset shadow
    deforms: minor on press (squash)
    age: ageless
  implementationStrategies:
    css: |
      background: oklch(85% 0.08 50);   /* peach pastel */
      border-radius: 32px;
      box-shadow:
        8px 8px 16px 0 oklch(50% 0.04 50 / 0.18),
        inset -6px -6px 12px 0 oklch(45% 0.06 50 / 0.22),
        inset 8px 8px 12px 0 oklch(100% 0 0 / 0.45);
      /* RULE: outer offset = inner offset, blur = 2× offset; outer shadow tinted with surface hue, NEVER black */
    svg: none
    raster: none
  reactiveBehaviors:
    light: shadow remains static (light source committed)
    highlight: hover scales 1.03 + translateY(-2px) with cubic-bezier(0.34, 1.56, 0.64, 1) overshoot
    depth: press scales 0.97 + inverts the inner highlight
    parallax: none — clay is grounded
  pairsWith:
    prototypeStyles: [style-claymorphism, aesthetic-positivity-kawaii, aesthetic-frutiger-eco, aesthetic-corporate-memphis]
  killsTheIllusion:
    - every container puffed (clay must be ONE moment per screen)
    - saturated 0.20+ chroma instead of 0.04–0.08 pastels
    - dark bottom-right inset shadow missing (reads flat pill with glow)
    - black drop shadow instead of surface-hue-tinted
    - clay extended to dark mode (inset highlight stops reading)
  examples:
    - Coursera 2022 rebrand
    - Pitch key visuals
    - Matter app
    - clay.css by Adrian Bece
  references:
    - https://hype4.academy/articles/coding/how-to-create-claymorphism-using-css
    - https://blog.openreplay.com/implementing-claymorphism-with-css/
```

## Common implementation mistakes (avoid these)

- every container puffed (clay must be ONE moment per screen)
- saturated 0.20+ chroma instead of 0.04–0.08 pastels
- dark bottom-right inset shadow missing (reads flat pill with glow)

## Pairs with (prototype slugs)

- `style-claymorphism`
- `aesthetic-positivity-kawaii`
- `aesthetic-frutiger-eco`
- `aesthetic-corporate-memphis`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 308–350 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

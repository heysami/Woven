---
materialId: matte-clay
name: Matte Clay (claymorphism)
family: digital
category: clay
surfaceFinish: matte
transparency: opaque
pairsPrototypes: [style-claymorphism, aesthetic-positivity-kawaii, aesthetic-frutiger-eco, aesthetic-corporate-memphis]
images:
  - src: material-matte-clay.png
    reason: Material fidelity sample.
---

# Matte Clay (claymorphism)

A matte surface that reacts to light: yes - inset highlight + dark inset shadow and deforms: minor on press (squash).

## Physical behavior

**Surface finish**: matte

**Transparency**: opaque

**Reacts to light**: yes - inset highlight + dark inset shadow

**Deforms**: minor on press (squash)

**Age / wear**: ageless

## Implementation strategies

```yaml
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
```

## Reactive behaviors

**Light**: shadow remains static (light source committed)

**Highlight**: hover scales 1.03 + translateY(-2px) with cubic-bezier(0.34, 1.56, 0.64, 1) overshoot

**Depth**: press scales 0.97 + inverts the inner highlight

**Parallax**: none - clay is grounded

## Common implementation mistakes (avoid these)

- every container puffed (clay must be ONE moment per screen)
- saturated 0.20+ chroma instead of 0.04-0.08 pastels
- dark bottom-right inset shadow missing (reads flat pill with glow)
- black drop shadow instead of surface-hue-tinted
- clay extended to dark mode (inset highlight stops reading)

## Examples in the wild

- Coursera 2022 rebrand
- Pitch key visuals
- Matter app
- clay.css by Adrian Bece

## References

- https://hype4.academy/articles/coding/how-to-create-claymorphism-using-css
- https://blog.openreplay.com/implementing-claymorphism-with-css/

## Pairs with (prototype slugs)

- `style-claymorphism`
- `aesthetic-positivity-kawaii`
- `aesthetic-frutiger-eco`
- `aesthetic-corporate-memphis`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

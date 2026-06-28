---
shaderId: concentric-patterns
name: Concentric Patterns (bold nested ring shapes)
family: source
category: generative-fill
subCategory: screen-pattern
role: background
defaultBlend: normal
animated: yes
needsSource: no
stackable: yes
pairsPrototypes: [aesthetic-op-art, aesthetic-y2k-memphis-loud, aesthetic-acid-design]
notForUseWhen: minimal restrained SaaS, photoreal hero
images:
  - src: shader-concentric-patterns.png
    reason: Concentric Patterns (bold nested ring shapes) - shader fill preview.
---

# Concentric Patterns (bold nested ring shapes)

Bold concentric rings / nested shapes radiating from a center, customizable shape and spacing - the Figma `Concentric patterns` fill. Op-art targets, retro sunbursts, hypnotic rings that can pulse outward.

## Stack contract

- **Role:** SOURCE (radial pattern fill).
- **Layer:** background, or accent overlay.
- **Default blend when stacked:** `normal`, or `multiply`/`screen` to interact with a layer below.
- **Animated:** yes - rings can travel outward (radar) or breathe; static is also valid.
- **Stacks under:** `organic-distortion` (warped target), `gradient-map`; **with:** `moire-interference`.

## Implementation strategies

```yaml
webgl: |
  float r = length(uv - u_center);
  float ring = step(0.5, fract(r*u_freq - u_time*u_speed));   // concentric bands
  // shape variants: replace length() with a square/hex distance for nested polygons
  vec3 col = mix(u_c1, u_c2, ring);
engine: |
  Figma fill: `Concentric patterns`. mm-composer: custom radial pattern effect.
svg: nested <circle>/<polygon> or a radial repeating-gradient (static).
css: repeating-radial-gradient (cheap static rings).
```

## Parameters (knobs)

- `shape` (circle / square / hex / star), `frequency` (ring spacing), `center`, `travelSpeed`, `c1`, `c2`, `thickness`.

## Stacking recipes

- Concentric Patterns + `organic-distortion` = a warped op-art target.
- Travel mode + a brand duotone = a radar / pulse hero.

## Common mistakes (avoid these)

- Even ring thickness at all radii on a square distance (aliasing at corners) - clamp / AA the band edge.
- Animating frequency instead of phase (rings pop in/out) - travel the phase.
- Over a busy photo (chaos) - concentric wants a plain ground.

## Pairs with (prototype slugs)

- `aesthetic-op-art`
- `aesthetic-y2k-memphis-loud`
- `aesthetic-acid-design`

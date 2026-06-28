---
shaderId: pattern-refraction
name: Pattern Refraction (light refracted through a ribbed pattern)
family: filter
category: image-effect
subCategory: distortion
role: overlay
defaultBlend: normal
animated: yes
needsSource: yes
stackable: yes
pairsPrototypes: [style-liquid-glass, style-glassmorphism, aesthetic-frutiger-aero, aesthetic-surreal-dream-stage]
notForUseWhen: flat editorial, accessibility-critical text
images:
  - src: shader-pattern-refraction.png
    reason: Pattern Refraction (light refracted through a ribbed pattern) - shader fill preview.
---

# Pattern Refraction (light refracted through a ribbed pattern)

Refract the layer beneath through a repeating pattern - ribs, lenses, ripples - so it slices and bends into wave distortions, like looking through reeded glass or a lenticular sheet. The Figma `Pattern refraction` effect.

## Stack contract

- **Role:** FILTER - displaces a SOURCE beneath through a pattern's normal field.
- **Layer:** top - it is the textured glass you view the rest through.
- **Default blend when stacked:** `normal` (re-samples beneath).
- **Animated:** yes - the pattern can drift / the ripple can travel; pointer can drag the lens.
- **Applies to:** the flattened layers below (render to texture first).

## Implementation strategies

```yaml
webgl: |
  // pattern normal -> refraction offset (Snell-ish: bend by the local slope)
  float pat = ribs(uv, u_freq, u_angle);            // sawtooth/sine rib field
  vec2 grad = patternGradient(uv, u_freq, u_angle);
  vec2 off = grad * u_strength;                      // refraction displacement
  vec3 col = texture(u_src, uv + off).rgb;
engine: |
  Figma effect: `Pattern refraction`. DOM material twins: material `reeded-fluted-glass`, `liquid-glass`.
svg: feDisplacementMap driven by a periodic feTurbulence/feImage rib map (the canonical DOM reeded glass).
```

## Parameters (knobs)

- `pattern` (ribs / lenses / ripple / hex), `frequency`, `angle`, `strength` (refraction amount), `driftSpeed`, `chromatic` (per-channel offset).

## Stacking recipes

- Pattern Refraction (vertical ribs) over a hero = reeded-glass privacy panel (liquid-glass register).
- Pointer-dragged lens pattern = a magnifier the user moves over the content.

## Common mistakes (avoid these)

- Refracting live text to illegibility - rasterize / duplicate text first, or keep strength tiny.
- Strength so high it shatters the image (becomes a glitch, not glass) - subtle for the premium read.
- No chromatic offset on thick glass (real glass fringes the rib edges) - add a small per-channel split.

## Pairs with (prototype slugs)

- `style-liquid-glass`
- `style-glassmorphism`
- `aesthetic-frutiger-aero`
- `aesthetic-surreal-dream-stage`

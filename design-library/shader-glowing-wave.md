---
shaderId: glowing-wave
name: Glowing Wave (luminous wave fill, on-canvas glow)
family: source
category: generative-fill
subCategory: light
role: background
defaultBlend: screen
animated: yes
needsSource: no
stackable: yes
pairsPrototypes: [aesthetic-cyberpunk, recipe-ai-foundry-dark, aesthetic-cassette-futurism, aesthetic-cosmic-horizon]
notForUseWhen: flat corporate, dense data tables
---

# Glowing Wave (luminous wave fill, on-canvas glow)

Smooth bands of emitted light undulating across the frame with on-canvas controls for color, glow and motion - the Figma `Glowing wave` fill. The clean luminous source BEFORE any dither; feed it into `dither` for the retro-CRT variant.

## Stack contract

- **Role:** SOURCE (self-generating light field).
- **Layer:** background, or overlay on a dark base.
- **Default blend when stacked:** `screen` / `add` (it emits light).
- **Animated:** yes - bands phase-scroll + glow breathes on `u_time`.
- **Stacks under:** `dither` (-> dither-waves register), `lens-distortion`, `color-outline`.

## Implementation strategies

```yaml
webgl: |
  float w = 0.5 + 0.5*sin(uv.y*u_freq + uv.x*1.5 + u_time*u_speed);
  float glow = pow(w, u_glow);
  vec3 col = u_lightColor * glow;
engine: |
  Figma fill: `Glowing wave`. mm-composer: `wave` effect with an emissive color ramp.
css/svg: repeating-linear-gradient + blur fakes a static wave; no glow breathing.
```

## Parameters (knobs)

- `lightColor`, `bandFrequency`, `waveSpeed`, `glow` (sharpness of the emissive falloff), `tilt`.

## Stacking recipes

- Glowing Wave + `dither` on top = `dither-waves`. Glowing Wave + `godrays` = lit aurora ribbon.

## Common mistakes (avoid these)

- `normal` blend (light must add, never composite over).
- Bright base (no contrast - waves need a dark field).
- Too many bands (reads as a barcode) - keep frequency low and the glow generous.

## Pairs with (prototype slugs)

- `aesthetic-cyberpunk`
- `recipe-ai-foundry-dark`
- `aesthetic-cassette-futurism`
- `aesthetic-cosmic-horizon`

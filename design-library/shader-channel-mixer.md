---
shaderId: channel-mixer
name: Channel Mixer (false-color / duotone channel remap)
family: filter
category: image-effect
subCategory: color
role: overlay
defaultBlend: normal
animated: no
needsSource: yes
stackable: yes
pairsPrototypes: [aesthetic-monochrome-pop-poster, aesthetic-cyberpunk, recipe-editorial-magazine, aesthetic-acid-graphics]
notForUseWhen: brand photos needing true color
---

# Channel Mixer (false-color / duotone channel remap)

Rebuild each output channel as a weighted mix of the source's R/G/B - the Figma `Channel mixer` effect. Custom color treatments, false-color infrared looks, surgical duotones, thermal palettes. A 3x3 (or 3x4) matrix on the pixels beneath.

## Stack contract

- **Role:** FILTER - recolors a SOURCE beneath.
- **Layer:** top color-grade pass.
- **Default blend when stacked:** `normal` (replaces color), or `color` to keep underlying detail.
- **Animated:** optional - the matrix can interpolate between two grades.
- **Applies to:** imagery layers (scope away from UI text that must stay brand-true).

## Implementation strategies

```yaml
webgl: |
  vec3 s = texture(u_src, uv).rgb;
  vec3 col = clamp(u_mat * s + u_bias, 0.0, 1.0);   // 3x3 mix + per-channel bias
engine: |
  Figma effect: `Channel mixer`. Sibling luminance-only recolor: `gradient-map`.
svg: feColorMatrix (the EXACT DOM equivalent - a 4x5 matrix).
css: not on its own (use an SVG filter url()).
```

## Parameters (knobs)

- `matrix` (3x3 channel weights), `bias` (per channel), `preset` (infrared / thermal / duotone / sepia), `blend`.

## Stacking recipes

- Channel Mixer (thermal preset) over `luminance-particles` = a heat-map readout.
- Channel Mixer to swap R<->B over a sky photo = instant false-color alien world.

## Common mistakes (avoid these)

- Rows that don't sum near 1.0 (the image blows out or goes black) - normalize unless intentional.
- Using it where `gradient-map` (luminance->ramp) is the cleaner duotone tool.
- Applying to UI/icons that must stay legible/brand - scope to imagery.

## Pairs with (prototype slugs)

- `aesthetic-monochrome-pop-poster`
- `aesthetic-cyberpunk`
- `recipe-editorial-magazine`
- `aesthetic-acid-graphics`

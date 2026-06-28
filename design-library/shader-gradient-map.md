---
shaderId: gradient-map
name: Gradient Map (luminance remapped to a custom color ramp)
family: filter
category: image-effect
subCategory: color
role: overlay
defaultBlend: normal
animated: no
needsSource: yes
stackable: yes
pairsPrototypes: [aesthetic-monochrome-pop-poster, aesthetic-luxury-cinematic-dark, recipe-editorial-magazine, aesthetic-acid-graphics]
notForUseWhen: brand photos that must keep true color
images:
  - src: shader-gradient-map.png
    reason: Gradient Map (luminance remapped to a custom color ramp) - shader fill preview.
---

# Gradient Map (luminance remapped to a custom color ramp)

Throw away the layer's hue and remap its LUMINANCE to a custom gradient - shadows take one color, highlights another, midtones the stops between. The Figma `Gradient map` effect: the single most powerful one-move way to force any image onto a brand palette (duotone / tritone).

## Stack contract

- **Role:** FILTER - recolors a SOURCE beneath by luminance.
- **Layer:** top color-grade pass.
- **Default blend when stacked:** `normal` (it replaces color), or `color` to keep underlying detail.
- **Animated:** optional - the ramp can slide / hue-cycle for a living gradient.
- **Applies to:** any image / illustration / the flattened stack - the universal palette-unifier.

## Implementation strategies

```yaml
webgl: |
  float l = dot(texture(u_src, uv).rgb, vec3(0.299,0.587,0.114));
  vec3 col = sampleRamp(u_ramp, l);              // 2-5 stop gradient lookup
engine: |
  Figma effect: `Gradient map`. mm-composer: a LUT/duotone color pass.
svg: |
  feColorMatrix to luminance (saturate 0) + feComponentTransfer tableValues per channel = DOM duotone.
css: |
  filter: grayscale(1) then a mix-blend-mode duotone overlay (cheap 2-stop only).
```

## Parameters (knobs)

- `ramp` (2-5 color stops + positions), `contrast` (pre-curve), `blend` (normal vs color), `rampSlide` (animate).

## Stacking recipes

- Gradient Map is the GLUE pass: drop it on TOP of any stack to force every layer onto one duotone - instant cohesion.
- Over `metaball-merge` / `luminance-particles` to recolor a sim without touching its math.

## Common mistakes (avoid these)

- Ramp with muddy midtone (gray sludge) - keep the mid stop chromatic.
- Mapping an already-low-contrast source (flat result) - boost contrast BEFORE the map.
- Using it on UI text/icons that need to stay legible/brand-true - scope it to imagery layers.

## Pairs with (prototype slugs)

- `aesthetic-monochrome-pop-poster`
- `aesthetic-luxury-cinematic-dark`
- `recipe-editorial-magazine`
- `aesthetic-acid-graphics`

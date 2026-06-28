---
shaderId: hatching
name: Hatching (cross-hatch line shading from luminance)
family: filter
category: image-effect
subCategory: edge
role: overlay
defaultBlend: multiply
animated: no
needsSource: yes
stackable: yes
pairsPrototypes: [recipe-editorial-magazine, aesthetic-dark-academia, style-doodle, recipe-newspaper-of-record]
notForUseWhen: glossy modern SaaS, vibrant pop
images:
  - src: shader-hatching.png
    reason: Hatching (cross-hatch line shading from luminance) - shader fill preview.
---

# Hatching (cross-hatch line shading from luminance)

Shade the layer beneath with engraving-style cross-hatching - darker tones get denser, more-crossed line layers, exactly like pen-and-ink or a banknote engraving. The Figma `Hatching` effect for text, shapes and images.

## Stack contract

- **Role:** FILTER - re-renders a SOURCE beneath as hatched line-art.
- **Layer:** top ink pass.
- **Default blend when stacked:** `multiply` (ink on paper), or `normal` on a paper base.
- **Animated:** usually NO (engraving is still); optional very-slow line jitter for a hand-drawn feel.
- **Applies to:** the luminance of the layer below.

## Implementation strategies

```yaml
webgl: |
  float l = luma(texture(u_src, uv).rgb);
  float h = 0.0;
  // add a hatch layer per luminance threshold, each at a different angle
  if (l < 0.8) h = max(h, lines(uv, 0.0,  u_freq));
  if (l < 0.6) h = max(h, lines(uv, 45.0, u_freq));
  if (l < 0.4) h = max(h, lines(uv, 90.0, u_freq));
  if (l < 0.2) h = max(h, lines(uv,135.0, u_freq));
  vec3 col = mix(u_paper, u_ink, h);
engine: |
  Figma effect: `Hatching`. DOM material twins: material `charcoal-drawing`, `iso-line-drawing`.
svg: <pattern> hatch fills masked by luminance bands; crisp + cheap.
```

## Parameters (knobs)

- `lineFrequency`, `thresholds` (how many hatch layers), `angles`, `inkColor`, `paperColor`, `lineWeight`.

## Stacking recipes

- Hatching over a portrait = an etched-engraving editorial illustration.
- Hatching over `gradient-map` (sepia) = a vintage banknote / dark-academia plate.

## Common mistakes (avoid these)

- One hatch angle at all tones (reads as a screen, not engraving) - cross-hatch denser in shadows.
- Line frequency too high (gray mush - the lines must stay resolvable) - scale to DPR.
- Smooth midtones (engraving is discrete tone steps) - threshold the luminance.

## Pairs with (prototype slugs)

- `recipe-editorial-magazine`
- `aesthetic-dark-academia`
- `style-doodle`
- `recipe-newspaper-of-record`

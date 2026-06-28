---
shaderId: chromatic-metal
name: Chromatic Metal (inflated glossy metal + RGB separation)
family: filter
category: image-effect
subCategory: metal
role: overlay
defaultBlend: normal
animated: yes
needsSource: yes
stackable: yes
pairsPrototypes: [aesthetic-y2k-futurism, aesthetic-urbling, aesthetic-cyberpunk, style-holographic]
notForUseWhen: matte editorial, flat utilitarian UI
images:
  - src: shader-chromatic-metal.png
    reason: Chromatic Metal (inflated glossy metal + RGB separation) - shader fill preview.
---

# Chromatic Metal (inflated glossy metal + RGB separation)

Give shapes and type a glossy, inflated liquid-metal finish with RGB channel separation at the highlights - the Figma `Chromatic metal` effect. Y2K chrome, bubble-text, iridescent fluid foil. Inflates the layer's alpha into a rounded body, then lights it like chrome.

## Stack contract

- **Role:** FILTER - inflates + chromes a SOURCE beneath (best on solid shapes / type / logos with alpha).
- **Layer:** replaces the content with its metal version.
- **Default blend when stacked:** `normal`.
- **Animated:** yes - the environment reflection / hue sweep drifts; pointer can move the highlight.
- **Applies to:** alpha shapes (type, marks). Poor on full photos (no clean silhouette to inflate).

## Implementation strategies

```yaml
webgl: |
  // 1. distance-field from the source alpha -> a rounded inflated normal
  float d = sdfFromAlpha(u_src, uv);
  vec3 n = normalFromSDF(d);
  // 2. env-map / matcap lookup for chrome; split RGB along the view-tangent
  vec3 env = matcap(reflect(viewDir, n));
  vec3 col = vec3(matcap(refl+caOffset).r, env.g, matcap(refl-caOffset).b);
engine: |
  Figma effect: `Chromatic metal`. DOM material twins: material `chrome-mirror`, `chrome-extruded-type`, `liquid-chrome-silk`.
css/svg: SVG feSpecularLighting + feDisplacement fakes inflated gloss on type (no true env reflection).
```

## Parameters (knobs)

- `inflate` (bevel depth), `gloss`, `envMap` (chrome / holographic / sunset), `caStrength` (RGB split), `highlightAngle` (pointer-bindable).

## Stacking recipes

- Chromatic Metal on a wordmark + `godrays` behind = Y2K hero lockup.
- holographic envMap = oil-slick iridescent chrome (urbling / bling register).

## Common mistakes (avoid these)

- Applying to a full photo (nothing to inflate - reads as a smear) - use on clean alpha shapes.
- No environment map (flat gray - reads as plastic, not chrome) - chrome needs something to reflect.
- CA on the whole body (only the highlights split in real chromatic metal).

## Pairs with (prototype slugs)

- `aesthetic-y2k-futurism`
- `aesthetic-urbling`
- `aesthetic-cyberpunk`
- `style-holographic`

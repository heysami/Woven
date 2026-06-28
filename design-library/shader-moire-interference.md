---
shaderId: moire-interference
name: Moire Interference (beating line/dot fields + RGB separation)
family: source
category: generative-fill
subCategory: screen-pattern
role: overlay
defaultBlend: screen
animated: yes
needsSource: no
stackable: yes
pairsPrototypes: [aesthetic-op-art, aesthetic-acid-design, aesthetic-monochrome-tech-editorial, recipe-swiss-grid]
notForUseWhen: calm wellness brands, accessibility-first UI
images:
  - src: shader-moire-interference.png
    reason: Moire Interference (beating line/dot fields + RGB separation) - shader fill preview.
---

# Moire Interference (beating line/dot fields + RGB separation)

Two or more fine line/dot fields overlaid at a slight angle so they beat into large moire interference patterns that swim as the angle drifts - the Figma `Moire` fill, with optional RGB channel separation for an optical, almost-3D shimmer.

## Stack contract

- **Role:** SOURCE (procedural interference). Works as an OVERLAY (screen) or a standalone op-art base.
- **Layer:** overlay over a flat base, or background.
- **Default blend when stacked:** `screen` / `difference` (the beat patterns interact with what's below).
- **Animated:** yes - one field's angle/phase drifts, so the moire bloom slowly swims.
- **Stacks over:** flat color or `gradient-map`; keep AWAY from busy imagery (clashes).

## Implementation strategies

```yaml
webgl: |
  float a = stripes(uv, u_freqA, u_angleA);
  float b = stripes(uv, u_freqB, u_angleB + u_time*0.02);
  float m = a * b;                                // multiply -> interference beat
  // optional RGB separation: sample b at angle +/- delta per channel
  vec3 col = vec3(stripes(uv,u_freqB,u_angleB+0.01)*a,
                  m, stripes(uv,u_freqB,u_angleB-0.01)*a);
engine: |
  Figma fill: `Moire`. Sibling DOM material: material `op-art` / moire entries.
svg: two <pattern> line fills at a few degrees apart (static moire).
css: repeating-linear-gradient x2 rotated a few degrees fakes a static beat.
```

## Parameters (knobs)

- `frequencyA/B`, `angleA/B`, `driftSpeed`, `rgbSeparation`, `mode` (lines / dots / concentric), `baseColor`.

## Stacking recipes

- Moire Interference (screen) over a flat brand color = a hypnotic op-art hero that never sits still.
- Add `rgbSeparation` for a chromatic, near-stereoscopic shimmer (Bridget Riley meets RGB-split).

## Common mistakes (avoid these)

- Angle difference too large (just a cross-hatch, no moire) - the beat needs a SMALL angle delta (1-5 deg).
- Over a detailed photo (visual chaos + accessibility nightmare) - moire wants a plain ground.
- Fast drift (induces real eye strain / can trigger discomfort) - keep the swim very slow; honour prefers-reduced-motion.

## Pairs with (prototype slugs)

- `aesthetic-op-art`
- `aesthetic-acid-design`
- `aesthetic-monochrome-tech-editorial`
- `recipe-swiss-grid`

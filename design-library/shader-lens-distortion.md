---
shaderId: lens-distortion
name: Lens Distortion (barrel/pincushion + radial chromatic aberration)
family: filter
category: image-effect
subCategory: distortion
role: overlay
defaultBlend: normal
animated: no
needsSource: yes
stackable: yes
pairsPrototypes: [aesthetic-cyberpunk, recipe-bento-marketing, aesthetic-frutiger-aero]
notForUseWhen: flat editorial type, accessibility-critical text
images:
  - src: shader-lens-distortion.png
    reason: Lens Distortion (barrel/pincushion + radial chromatic aberration) - shader fill preview.
---

# Lens Distortion (barrel/pincushion + radial chromatic aberration)

Optical lens warp - barrel (bulge) or pincushion (pinch) - with the RGB channels split radially toward the corners, exactly like a real wide-angle or anamorphic lens. The frame gains glassy depth and a cinematic fringe at the edges.

## Stack contract

- **Role:** FILTER - warps + fringes a SOURCE beneath (image, or a whole composed stack).
- **Layer:** TOP of the stack (it is the lens you view the rest through).
- **Default blend when stacked:** `normal` (replaces - it re-samples everything below).
- **Animated:** optional - distortion can breathe subtly, or be static; pointer can set the zero-CA focal point.
- **Applies to:** the flattened layers beneath it (render them to a texture, then distort).

## Implementation strategies

```yaml
webgl: |
  vec2 d = uv - 0.5;
  float r2 = dot(d,d);
  vec2 warp = uv + d * (u_barrel * r2);          // +barrel / -pincushion
  float ca = u_caStrength * r2;                   // CA grows toward corners
  vec3 col = vec3(
    texture(u_src, warp + d*ca).r,
    texture(u_src, warp).g,
    texture(u_src, warp - d*ca).b);
engine: |
  Figma effect: `Lens distortion`. mm-composer: `chromatic-aberration` (radial mode).
  Sibling card (static, DOM-register): material `chromatic-aberration-lens`.
svg: |
  feDisplacementMap (radial map) + per-channel feOffset for a cheap DOM approximation.
css: filter: drop-shadow tricks only fake edge CA, no warp.
```

## Parameters (knobs)

- `distortion` (-1 pincushion .. +1 barrel), `caStrength`, `focalPoint` (zero-CA center, pointer-bindable),
  `vignette`, `edgeFalloff`.

## Stacking recipes

- Lens Distortion (top) over the ENTIRE composed shader stack = ties disparate layers into one "shot through glass".
- Pair a gentle barrel with a vignette for a CCTV / fisheye register.

## Common mistakes (avoid these)

- Uniform CA across the frame (real lens CA is radial - zero at center, max at corners).
- Distorting live text to illegibility - rasterize text first or exclude it from the lensed texture.
- Over-strong warp (becomes a funhouse mirror) - subtle barrel reads as premium glass, not gimmick.

## Pairs with (prototype slugs)

- `aesthetic-cyberpunk`
- `recipe-bento-marketing`
- `aesthetic-frutiger-aero`

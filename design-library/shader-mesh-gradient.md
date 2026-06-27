---
shaderId: mesh-gradient
name: Mesh Gradient (animated 16-point color mesh)
family: source
category: generative-fill
subCategory: gradient
role: background
defaultBlend: normal
animated: yes
needsSource: no
stackable: yes
pairsPrototypes: [style-aurorism, recipe-aurora-marketing, aesthetic-frutiger-aero, recipe-restrained-ai-marketing]
notForUseWhen: high-density data UI, brutalist flat
---

# Mesh Gradient (animated 16-point color mesh)

Smooth multi-point color mesh - up to 16 editable color stops bleeding into each other - gently drifting and warping. The Figma `Mesh gradient` fill and the animated WebGL sibling of the CSS-first `material-aurora-mesh`. The default premium SaaS backdrop.

## Stack contract

- **Role:** SOURCE (color field).
- **Layer:** background base.
- **Default blend when stacked:** `normal` (it is the ground).
- **Animated:** yes - control points drift on slow counter-rotating orbits + a subtle swirl warp.
- **Stacks under:** `fractal-noise` (anti-band grain), `godrays`, `lens-distortion`. **DOM twin:** `material-aurora-mesh`.

## Implementation strategies

```yaml
webgl: |
  // bilinear/bicubic blend of N corner colors whose positions drift on u_time,
  // plus a low-freq swirl warp of uv for organic motion
  vec2 p = uv + 0.05*vec2(sin(u_time*0.2+uv.y*3.0), cos(u_time*0.17+uv.x*3.0));
  vec3 col = meshBlend(p, u_points, u_colors);
engine: |
  Figma fill: `Mesh gradient` (16 points). paper-design/shaders: `meshGradient`.
  Prefer the DOM `material-aurora-mesh` (radial-gradient stack + blur) when motion is optional.
css: layered radial-gradients in OKLCH + blur(80px) (the cheap static version).
```

## Parameters (knobs)

- `colors` (3-16 stops), `pointDrift`, `swirl`, `speed`, `grain` (anti-band), `blurSoftness`.

## Stacking recipes

- Mesh Gradient + `fractal-noise` (overlay 5%) = banding-free animated brand backdrop.
- Mesh Gradient + `metaball-merge` (screen) = drifting color with floating glass lozenges.

## Common mistakes (avoid these)

- No grain (8-bit banding across the soft blend) - always a noise overlay.
- Full-saturation rainbow (no falloff) - 3-4 brand-adjacent hues read premium.
- Fast drift (cheap screensaver) - barely-perceptible motion.

## Pairs with (prototype slugs)

- `style-aurorism`
- `recipe-aurora-marketing`
- `aesthetic-frutiger-aero`
- `recipe-restrained-ai-marketing`

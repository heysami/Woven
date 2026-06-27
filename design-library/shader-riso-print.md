---
shaderId: riso-print
name: Riso Print (2-color screen re-print with grain + registration shift)
family: filter
category: image-effect
subCategory: halftone
role: overlay
defaultBlend: multiply
animated: no
needsSource: yes
stackable: yes
pairsPrototypes: [recipe-editorial-magazine, recipe-readcv, aesthetic-anti-design, style-raster-cutout]
notForUseWhen: glossy enterprise polish, photoreal hero
---

# Riso Print (2-color screen re-print with grain + registration shift)

Re-screen the layer as a Risograph print: split it into 2-3 spot inks, screen each through a grain or halftone, then offset the channels a few pixels so the registration is charmingly wrong - colored fringes at every edge. The Figma gallery `Riso print` effect.

## Stack contract

- **Role:** FILTER - re-prints a SOURCE beneath (image / illustration / the whole stack).
- **Layer:** top finishing pass.
- **Default blend when stacked:** `multiply` (translucent ink layers build hue where they overlap).
- **Animated:** usually NO (print is static) - optional micro-jitter on the registration for a living-zine feel.
- **Applies to:** the flattened layers below.

## Implementation strategies

```yaml
webgl: |
  float lum = luma(texture(u_src, uv).rgb);
  // posterize to ink coverage per channel, screen each through grain dither
  float pink = dither(lum, uv + u_regShift);     // channel 1 offset +regShift
  float teal = dither(lum, uv - u_regShift);     // channel 2 offset -regShift
  vec3 col = u_paper * (1.0 - pink*u_inkA - teal*u_inkB); // multiply build-up
engine: |
  Figma gallery: `Riso print`. paper-design/shaders: `dithering` + channel offset.
  Sibling raster style: illust `risograph-illustration`. Material analog twin: material `risograph`.
svg: feColorMatrix duotone + feTurbulence grain + feOffset per channel (DOM riso).
css: mix-blend-mode: multiply on two tinted copies fakes the overlap, not the grain.
```

## Parameters (knobs)

- `inks` (2-3 spot colors - riso pink/teal/yellow), `grain` (diffusion-dither density), `registrationShift`, `paperTint`, `posterizeLevels`.

## Stacking recipes

- Riso Print (multiply) over `fluid-halftone` = an animated field that resolves into a printed zine page.
- Stack three single-ink riso passes (pink / teal / yellow) for a true 3-color overprint.

## Common mistakes (avoid these)

- Opaque inks (kills the overprint hue-mixing that DEFINES riso) - each ink must be translucent, multiply.
- Perfect registration (then it's just a duotone) - the small misalignment IS the effect.
- Smooth gradients (riso cannot hold them) - posterize + grain, always.

## Pairs with (prototype slugs)

- `recipe-editorial-magazine`
- `recipe-readcv`
- `aesthetic-anti-design`
- `style-raster-cutout`

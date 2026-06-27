---
shaderId: bokeh-blur
name: Bokeh Blur (depth-of-field highlight bloom)
family: filter
category: image-effect
subCategory: light
role: overlay
defaultBlend: normal
animated: yes
needsSource: yes
stackable: yes
pairsPrototypes: [aesthetic-luxury-cinematic-dark, recipe-bento-marketing, aesthetic-frutiger-aero, recipe-aurora-marketing]
notForUseWhen: crisp technical diagrams, dense tables
---

# Bokeh Blur (depth-of-field highlight bloom)

Soft lens blur where the bright spots bloom into rounded bokeh discs - the Figma `Bokeh blur` effect, with controls for highlight density. Dreamy depth-of-field, festive light backdrops, premium product haze.

## Stack contract

- **Role:** FILTER - blurs a SOURCE beneath, blooming its highlights into discs.
- **Layer:** mid/top - often a blurred copy behind a sharp foreground.
- **Default blend when stacked:** `normal`, or `screen` for the highlight-disc layer only (additive bokeh).
- **Animated:** optional - discs can drift / twinkle; focal plane can rack on scroll.
- **Applies to:** the layer below (a photo, a gradient, a light field).

## Implementation strategies

```yaml
webgl: |
  // disc-kernel (hexagonal/circular) gather; boost samples above a highlight threshold
  vec3 acc=vec3(0); float w=0.0;
  for (k in disc(u_radius)) { vec3 s=texture(u_src, uv+k).rgb;
     float b = step(u_thresh, luma(s)) * u_bloom + 1.0; acc+=s*b; w+=b; }
  vec3 col = acc/w;
engine: |
  Figma effect: `Bokeh blur`. paper-design/shaders: blur + threshold bloom.
css: filter: blur() is GAUSSIAN (no disc bokeh / no highlight bloom) - only a rough stand-in.
```

## Parameters (knobs)

- `radius`, `highlightThreshold`, `bloom` (disc intensity), `discShape` (round / hex / cat-eye), `focalPlane` (what stays sharp).

## Stacking recipes

- Bokeh Blur over `nebula` or `clouds` = soft glowing depth behind a sharp hero.
- Screen-blend just the highlight discs over a product shot = festive light bokeh.

## Common mistakes (avoid these)

- Gaussian blur called bokeh (no disc shape, no bloom) - real bokeh needs a disc kernel + highlight boost.
- Blurring everything (no focal subject) - keep a sharp plane to read against.
- Huge radius on the CPU/canvas (dead perf) - downsample, blur small, upsample.

## Pairs with (prototype slugs)

- `aesthetic-luxury-cinematic-dark`
- `recipe-bento-marketing`
- `aesthetic-frutiger-aero`
- `recipe-aurora-marketing`

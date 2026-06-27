---
shaderId: particle-stretch
name: Particle Stretch (directional pixel-smear motion trails)
family: filter
category: image-effect
subCategory: distortion
role: overlay
defaultBlend: normal
animated: yes
needsSource: yes
stackable: yes
pairsPrototypes: [aesthetic-cyberpunk, aesthetic-y2k-futurism, style-bold-display, style-oversized-neo-grotesque]
notForUseWhen: calm restrained brands, dense tables
---

# Particle Stretch (directional pixel-smear motion trails)

Stretch and smear the layer's pixels along a direction - like a long-exposure of something moving fast, or paint dragged with a squeegee. The Figma `Pixel stretch` effect: motion without motion blur's softness, a hard directional pull.

## Stack contract

- **Role:** FILTER - smears a SOURCE beneath.
- **Layer:** top/mid over the layer it streaks.
- **Default blend when stacked:** `normal`, or `screen` for a glowing light-streak version.
- **Animated:** yes - stretch amount/length can pulse; direction can follow scroll velocity or pointer.
- **Applies to:** the layer below; great on text and bright shapes.

## Implementation strategies

```yaml
webgl: |
  // accumulate samples backward along the stretch direction
  vec3 acc = vec3(0.0); float w = 0.0;
  for (int i=0;i<STEPS;i++){
    float t = float(i)/float(STEPS);
    acc += texture(u_src, uv - u_dir * t * u_len).rgb * (1.0-t);
    w += (1.0-t);
  }
  vec3 col = acc / w;
engine: |
  Figma effect: `Pixel stretch`. mm-composer: `squash-stretch` + directional blur.
  Sibling motion register: material `motion-blur-streak`.
canvas2d: drawImage the layer N times offset along dir with decreasing alpha.
css/svg: feGaussianBlur is omnidirectional - cannot do a clean directional stretch.
```

## Parameters (knobs)

- `direction` (deg, or `auto` from scroll/pointer velocity), `length`, `falloff`, `threshold` (only stretch bright pixels), `steps`.

## Stacking recipes

- Particle Stretch (threshold=bright, screen) on a headline = neon light-trails on the type only.
- Drive `direction` + `length` from scroll velocity = the page smears when you fling it, settles when still.

## Common mistakes (avoid these)

- Stretching the whole frame uniformly (reads as a render glitch) - threshold to bright areas or shapes.
- Too few steps (banded ghosts) - 12-24 samples for a smooth trail.
- Omnidirectional blur masquerading as stretch - it MUST be along one vector.

## Pairs with (prototype slugs)

- `aesthetic-cyberpunk`
- `aesthetic-y2k-futurism`
- `style-bold-display`
- `style-oversized-neo-grotesque`

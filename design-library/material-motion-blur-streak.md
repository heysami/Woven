---
materialId: motion-blur-streak
name: Motion Blur Streak (directional motion artifact)
family: digital
category: digital-effect
surfaceFinish: glossy
transparency: translucent
pairsPrototypes: [aesthetic-cyberpunk, aesthetic-cassette-futurism, aesthetic-cinematic, recipe-bento-marketing, recipe-aurora-marketing, aesthetic-frutiger-aero]
images:
  - src: material-motion-blur-streak.png
    reason: Material fidelity sample.
---

# Motion Blur Streak (directional motion artifact)

A glossy surface (translucent) that reacts to light: yes and deforms: yes — directional smear along motion vector.

## Physical behavior

**Surface finish**: glossy

**Transparency**: translucent

**Reacts to light**: yes

**Deforms**: yes — directional smear along motion vector

**Age / wear**: ageless

## Implementation strategies

```yaml
css: |
  transition: transform 0.15s ease-out;
  will-change: transform;
  filter: blur(0); /* clean rest state */
  /* runtime sets filter: blur(2px) during fast pointer drag */
svg: |
  <feGaussianBlur stdDeviation="<dx> <dy>"> with anisotropic blur along
  motion direction. Drive dx/dy from pointer velocity.
webgl: |
  multi-tap blur in the motion-vector direction; 4-8 samples is enough for UI.
```

## Reactive behaviors

**Light**: streaks extend specular highlights

**Highlight**: pointer velocity drives blur amount + direction

**Depth**: faster motion = more apparent speed = more depth perception

**Parallax**: scroll velocity drives vertical streak

## Common implementation mistakes (avoid these)

- persistent blur at rest (real motion blur clears in 1 frame)
- omnidirectional blur (real motion blur is directional)
- applied to text mid-action (illegibility)

## Examples in the wild

- Apple iOS scrolling speed-blur (subtle)
- racing games
- WebGL "fluid" demos

## References

- https://en.wikipedia.org/wiki/Motion_blur

## Pairs with (prototype slugs)

- `aesthetic-cyberpunk`
- `aesthetic-cassette-futurism`
- `aesthetic-cinematic`
- `recipe-bento-marketing`
- `recipe-aurora-marketing`
- `aesthetic-frutiger-aero`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

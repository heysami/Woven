# Motion Blur Streak (directional motion artifact) (material)

**Tag:** material-motion-blur-streak  ·  **Family:** digital  ·  **Category:** digital-effect · glossy

A glossy digital surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: motion-blur-streak
  name: Motion Blur Streak (directional motion artifact)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: glossy
    transparency: translucent
    reactsToLight: yes
    deforms: yes — directional smear along motion vector
    age: ageless
  implementationStrategies:
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
  reactiveBehaviors:
    light: streaks extend specular highlights
    highlight: pointer velocity drives blur amount + direction
    depth: faster motion = more apparent speed = more depth perception
    parallax: scroll velocity drives vertical streak
  pairsWith:
    prototypeStyles: [aesthetic-cyberpunk, aesthetic-cassette-futurism, aesthetic-cinematic, recipe-bento-marketing, recipe-aurora-marketing, aesthetic-frutiger-aero]
  killsTheIllusion:
    - persistent blur at rest (real motion blur clears in 1 frame)
    - omnidirectional blur (real motion blur is directional)
    - applied to text mid-action (illegibility)
  examples:
    - Apple iOS scrolling speed-blur (subtle)
    - racing games
    - WebGL "fluid" demos
  references:
    - https://en.wikipedia.org/wiki/Motion_blur
```

## Common implementation mistakes (avoid these)

- persistent blur at rest (real motion blur clears in 1 frame)
- omnidirectional blur (real motion blur is directional)
- applied to text mid-action (illegibility)

## Pairs with (prototype slugs)

- `aesthetic-cyberpunk`
- `aesthetic-cassette-futurism`
- `aesthetic-cinematic`
- `recipe-bento-marketing`
- `recipe-aurora-marketing`
- `aesthetic-frutiger-aero`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 1351–1389 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

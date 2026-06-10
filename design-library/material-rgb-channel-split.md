---
materialId: rgb-channel-split
name: RGB Channel Split (intentional large-displacement chromatic split)
family: digital
category: digital-effect
surfaceFinish: matte
transparency: opaque
pairsPrototypes: [aesthetic-cyberpunk, aesthetic-acid-graphics, aesthetic-vaporwave, aesthetic-y2k-futurism, aesthetic-acid-design, recipe-terminal-on-web]
images:
  - src: material-rgb-channel-split.png
    reason: Material fidelity sample.
---

# RGB Channel Split (intentional large-displacement chromatic split)

A matte surface that reacts to light: yes — displacement amount can react to pointer / tilt.

## Physical behavior

**Surface finish**: matte

**Transparency**: opaque

**Reacts to light**: yes — displacement amount can react to pointer / tilt

**Deforms**: no (the channels shift, the structure stays)

**Age / wear**: ageless

## Implementation strategies

```yaml
css: |
  .rgb-split {
    position: relative;
    color: transparent;
  }
  .rgb-split::before,
  .rgb-split::after {
    content: attr(data-text);
    position: absolute; inset: 0;
    mix-blend-mode: screen;
  }
  .rgb-split::before { color: #ff0040; transform: translate(-2px, 0); }
  .rgb-split::after  { color: #00ffff; transform: translate( 2px, 0); }
svg: |
  <feOffset> + <feColorMatrix> to isolate the R, G, B channels, then
  <feMerge> them with horizontal offsets. Drives reactive splits via
  animated <feOffset dx>.
webgl: |
  sample input three times at (uv - offset, uv, uv + offset), output
  (sampleA.r, sampleB.g, sampleC.b). Trivial fragment shader.
raster: not appropriate — RGB split needs the live composition
```

## Reactive behaviors

**Light**: split amount can grow with pointer velocity

**Highlight**: pointer-distance modulates the displacement

**Depth**: hover spreads the channels (treat as "depth on attention")

**Parallax**: scroll-velocity drives split amount

## Common implementation mistakes (avoid these)

- applying to body text at any displacement that breaks legibility
- symmetric offsets (real chromatic aberration is radial, biased toward edges)
- flat across the whole frame (real lens CA gets worse toward corners)

## Examples in the wild

- Blade Runner 2049 type treatment
- 1980s VHS title cards
- Kraftwerk "Computer World" sleeve

## References

- https://en.wikipedia.org/wiki/Chromatic_aberration

## Pairs with (prototype slugs)

- `aesthetic-cyberpunk`
- `aesthetic-acid-graphics`
- `aesthetic-vaporwave`
- `aesthetic-y2k-futurism`
- `aesthetic-acid-design`
- `recipe-terminal-on-web`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

---
materialId: signal-interference
name: Signal Interference (hum bars, sync errors, vertical hold drift)
family: digital
category: digital-effect
surfaceFinish: glossy
transparency: opaque
pairsPrototypes: [aesthetic-vaporwave, aesthetic-cassette-futurism, aesthetic-atompunk, aesthetic-cyberpunk, recipe-terminal-on-web, style-dense-mono-dark]
---

# Signal Interference (hum bars, sync errors, vertical hold drift)

A glossy surface that reacts to light: yes — interference modulates with content luminance and deforms: yes (frame skew, scroll, sync loss).

## Physical behavior

**Surface finish**: glossy

**Transparency**: opaque

**Reacts to light**: yes — interference modulates with content luminance

**Deforms**: yes (frame skew, scroll, sync loss)

**Age / wear**: feels analog-CRT era despite digital implementation

## Implementation strategies

```yaml
css: |
  .interference::after {
    content: '';
    position: absolute; inset: 0;
    background: linear-gradient(180deg,
      transparent 0%,
      rgba(255,255,255,0.08) 47%,
      rgba(0,0,0,0.15) 50%,
      transparent 53%
    );
    background-size: 100% 4px;
    animation: hum 0.8s linear infinite;
  }
  @keyframes hum { 0% { background-position: 0 0 } 100% { background-position: 0 100vh } }
svg: |
  <feTurbulence type="turbulence" baseFrequency="0 4" numOctaves="2"> for
  horizontal noise band; modulate with <feComposite in2="SourceAlpha"> for
  the hum bar drift.
webgl: |
  fragment shader: sin(uv.y * 200. + time * 8.) modulates a horizontal band
  offset that displaces UVs. Combine with sync-loss frame-skew (uv.x += step * uv.y).
raster: looping mp4 of CRT hum bars as overlay layer
```

## Reactive behaviors

**Light**: interference intensity scales with content luminance

**Highlight**: pointer can seed sync-loss spikes

**Depth**: frame-skew creates apparent depth via the slip-line

**Parallax**: scroll triggers transient sync loss

## Common implementation mistakes (avoid these)

- regular sine-wave (real interference is stochastic)
- hum bars at the same position every frame (real ones drift)
- applying with linear blend (use mix-blend-mode: screen or color-dodge)

## Examples in the wild

- 1980s broadcast TV
- VHS recorded off-air
- synthwave music video establishing shots

## References

- https://en.wikipedia.org/wiki/Image_quality_television

## Pairs with (prototype slugs)

- `aesthetic-vaporwave`
- `aesthetic-cassette-futurism`
- `aesthetic-atompunk`
- `aesthetic-cyberpunk`
- `recipe-terminal-on-web`
- `style-dense-mono-dark`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

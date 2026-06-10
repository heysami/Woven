# Signal Interference (hum bars, sync errors, vertical hold drift) (material)

**Tag:** material-signal-interference  ·  **Family:** digital  ·  **Category:** digital-effect · glossy

A glossy digital surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: signal-interference
  name: Signal Interference (hum bars, sync errors, vertical hold drift)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: glossy
    transparency: opaque
    reactsToLight: yes — interference modulates with content luminance
    deforms: yes (frame skew, scroll, sync loss)
    age: feels analog-CRT era despite digital implementation
  implementationStrategies:
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
  reactiveBehaviors:
    light: interference intensity scales with content luminance
    highlight: pointer can seed sync-loss spikes
    depth: frame-skew creates apparent depth via the slip-line
    parallax: scroll triggers transient sync loss
  pairsWith:
    prototypeStyles: [aesthetic-vaporwave, aesthetic-cassette-futurism, aesthetic-atompunk, aesthetic-cyberpunk, recipe-terminal-on-web, style-dense-mono-dark]
  killsTheIllusion:
    - regular sine-wave (real interference is stochastic)
    - hum bars at the same position every frame (real ones drift)
    - applying with linear blend (use mix-blend-mode: screen or color-dodge)
  examples:
    - 1980s broadcast TV
    - VHS recorded off-air
    - synthwave music video establishing shots
  references:
    - https://en.wikipedia.org/wiki/Image_quality_television
```

## Common implementation mistakes (avoid these)

- regular sine-wave (real interference is stochastic)
- hum bars at the same position every frame (real ones drift)
- applying with linear blend (use mix-blend-mode: screen or color-dodge)

## Pairs with (prototype slugs)

- `aesthetic-vaporwave`
- `aesthetic-cassette-futurism`
- `aesthetic-atompunk`
- `aesthetic-cyberpunk`
- `recipe-terminal-on-web`
- `style-dense-mono-dark`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 1095–1145 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

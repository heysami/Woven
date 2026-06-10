# VHS Distortion (chromatic aberration + scanlines + bleed) (material)

**Tag:** material-vhs-distortion  ·  **Family:** analog  ·  **Category:** film · glossy

A glossy analog surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: vhs-distortion
  name: VHS Distortion (chromatic aberration + scanlines + bleed)
  family: analog
  category: film
  physicalBehavior:
    surfaceFinish: glossy
    transparency: opaque
    reactsToLight: no
    deforms: yes — tape head distortion bands
    age: shows wear (drop-outs)
  implementationStrategies:
    css: |
      filter: contrast(1.05) saturate(1.1);
    svg: |
      <feOffset in="SourceGraphic" dx="2" dy="0" result="R"/>
      <feOffset in="SourceGraphic" dx="-2" dy="0" result="B"/>
      <feColorMatrix in="R" values="1 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0"/>
      <feColorMatrix in="B" values="0 0 0 0 0  0 0 0 0 0  0 0 1 0 0  0 0 0 1 0"/>
      <feBlend mode="screen"/>
    webgl: |
      RGB-shift in fragment shader; horizontal scanline darken; periodic
      vertical roll bar at 6s interval (the tape-tracking jitter)
    raster: real VHS rip overlay at multiply
    video: looping VHS distortion source at overlay
  reactiveBehaviors:
    light: no
    highlight: no
    depth: no
    parallax: no
  pairsWith:
    prototypeStyles: [aesthetic-vaporwave, aesthetic-cassette-futurism, aesthetic-cyberpunk, aesthetic-y2k-myspace, aesthetic-acid-graphics]
  killsTheIllusion:
    - static RGB shift (real VHS varies)
    - no scanlines (VHS interlace is signature)
    - no horizontal bleed
  examples:
    - 90s home video aesthetic
    - vaporwave music videos
  references:
    - https://halisavakis.com/write-up-vhs-image-effect/
```

## Common implementation mistakes (avoid these)

- static RGB shift (real VHS varies)
- no scanlines (VHS interlace is signature)
- no horizontal bleed

## Pairs with (prototype slugs)

- `aesthetic-vaporwave`
- `aesthetic-cassette-futurism`
- `aesthetic-cyberpunk`
- `aesthetic-y2k-myspace`
- `aesthetic-acid-graphics`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 2690–2730 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

# Halftone CMYK (newspaper / comic process) (material)

**Tag:** material-halftone-cmyk  ·  **Family:** analog  ·  **Category:** print · matte

A matte analog surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: halftone-cmyk
  name: Halftone CMYK (newspaper / comic process)
  family: analog
  category: print
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: no
    deforms: no
    age: shows wear
  implementationStrategies:
    css: |
      background:
        radial-gradient(circle at center, #000 0.5px, transparent 1.5px) 0 0/4px 4px;
      transform: rotate(45deg);  /* black at 45° */
    svg: |
      Per-channel halftone: C @ 15°, M @ 75°, Y @ 0°, K @ 45° — the rosette
      pattern that hides moiré. Use <pattern> with rotated transforms.
    webgl: |
      Sample image luminance, per-channel threshold against rotated dot grid.
    raster: stack of 4 PNG halftone screens at correct angles
  reactiveBehaviors:
    light: no
    highlight: no
    depth: no
    parallax: stepped only
  pairsWith:
    prototypeStyles: [aesthetic-corporate-grunge, style-raster-cutout, aesthetic-acid-design, aesthetic-y2k-memphis-loud, recipe-newspaper-of-record]
  killsTheIllusion:
    - grid-aligned dots for all channels (must rotate per channel)
    - dot size too uniform (real halftone is luminance-driven)
    - moiré-pattern alarms (caused by wrong screen angles)
  examples:
    - Lichtenstein paintings
    - Marvel comics 1960s
    - daily newspaper photos
  references:
    - http://the-print-guide.blogspot.com/2009/05/halftone-screen-angles.html
```

## Common implementation mistakes (avoid these)

- grid-aligned dots for all channels (must rotate per channel)
- dot size too uniform (real halftone is luminance-driven)
- moiré-pattern alarms (caused by wrong screen angles)

## Pairs with (prototype slugs)

- `aesthetic-corporate-grunge`
- `style-raster-cutout`
- `aesthetic-acid-design`
- `aesthetic-y2k-memphis-loud`
- `recipe-newspaper-of-record`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 2001–2039 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

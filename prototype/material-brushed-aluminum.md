# Brushed Aluminum (anisotropic metal) (material)

**Tag:** material-brushed-aluminum  ·  **Family:** digital  ·  **Category:** metal · semi-gloss

A semi-gloss digital surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: brushed-aluminum
  name: Brushed Aluminum (anisotropic metal)
  family: digital
  category: metal
  physicalBehavior:
    surfaceFinish: semi-gloss
    transparency: opaque
    reactsToLight: yes — anisotropic highlight perpendicular to brush direction
    deforms: no
    age: shows wear (scratches deepen)
  implementationStrategies:
    css: |
      background:
        repeating-linear-gradient(90deg,
          rgba(255,255,255,0.06) 0px,
          rgba(0,0,0,0.06) 1px,
          rgba(255,255,255,0.06) 2px
        ),
        linear-gradient(180deg, #d6d8db 0%, #a8abb1 100%);
      box-shadow:
        inset 0 1px 0 rgba(255,255,255,0.4),
        inset 0 -1px 0 rgba(0,0,0,0.3),
        0 1px 2px rgba(0,0,0,0.2);
    svg: |
      <filter id="brushed">
        <feTurbulence type="turbulence" baseFrequency="0.8 0.01" numOctaves="2"/>
        <feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 0.18 0"/>
      </filter>
      /* baseFrequency x ≫ y → directional grain */
    raster: 2048px scan of real brushed metal at 0.18 opacity multiply
  reactiveBehaviors:
    light: highlight stretches ALONG the grain direction on tilt (90deg), never across
    highlight: pointer tracks but highlight is elongated
    depth: hairline scratch overlay reveals at hover
    parallax: minimal
  pairsWith:
    prototypeStyles: [aesthetic-cassette-futurism, aesthetic-dieselpunk, aesthetic-steampunk, style-skeuomorphism (recorder-as-tape-deck)]
  killsTheIllusion:
    - isotropic noise instead of directional grain
    - brushed pattern at huge scale (the grain has to be sub-mm)
    - circular highlight instead of elongated one
  examples:
    - iPod nano body
    - MacBook Pro casing
    - Sony WALKMAN front face
```

## Common implementation mistakes (avoid these)

- isotropic noise instead of directional grain
- brushed pattern at huge scale (the grain has to be sub-mm)
- circular highlight instead of elongated one

## Pairs with (prototype slugs)

- `aesthetic-cassette-futurism`
- `aesthetic-dieselpunk`
- `aesthetic-steampunk`
- `style-skeuomorphism (recorder-as-tape-deck)`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 480–525 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

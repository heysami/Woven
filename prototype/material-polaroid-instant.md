# Polaroid / Instant Photo (square frame, faded chemistry) (material)

**Tag:** material-polaroid-instant  ·  **Family:** analog  ·  **Category:** film · glossy

A glossy analog surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: polaroid-instant
  name: Polaroid / Instant Photo (square frame, faded chemistry)
  family: analog
  category: film
  physicalBehavior:
    surfaceFinish: glossy
    transparency: opaque
    reactsToLight: yes — reflective sheen
    deforms: minimal
    age: acquired patina (yellowing, fade)
  implementationStrategies:
    css: |
      .polaroid {
        background: #f4ede1;
        padding: 12px 12px 56px;
        box-shadow:
          0 1px 2px rgba(0,0,0,0.2),
          0 14px 28px -8px rgba(0,0,0,0.4);
        transform: rotate(-2deg);
        font-family: 'Caveat', cursive;
      }
      .polaroid img { filter: saturate(0.85) contrast(0.95); }
    raster: polaroid frame PNG
  reactiveBehaviors:
    light: subtle gloss on hover
    highlight: minimal
    depth: hover lifts the frame
    parallax: in scrapbook layouts, yes
  pairsWith:
    prototypeStyles: [style-raster-cutout, aesthetic-cottagecore, aesthetic-y2k-myspace, aesthetic-coastal-grandmother, recipe-readcv]
  killsTheIllusion:
    - all polaroids at the same angle (real ones scatter)
    - no chemistry fade
    - caption in a digital font (must be handwritten)
```

### 4.7 Distress / age family

```yaml
```

## Common implementation mistakes (avoid these)

- all polaroids at the same angle (real ones scatter)
- no chemistry fade
- caption in a digital font (must be handwritten)

## Pairs with (prototype slugs)

- `style-raster-cutout`
- `aesthetic-cottagecore`
- `aesthetic-y2k-myspace`
- `aesthetic-coastal-grandmother`
- `recipe-readcv`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 2731–2769 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

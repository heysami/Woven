# Foxing / Tea Stain (paper aging) (material)

**Tag:** material-foxing-stain  ·  **Family:** analog  ·  **Category:** digital-effect · matte

A matte analog surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: foxing-stain
  name: Foxing / Tea Stain (paper aging)
  family: analog
  category: digital-effect
  physicalBehavior:
    surfaceFinish: matte
    transparency: translucent
    reactsToLight: no
    deforms: no
    age: acquired patina
  implementationStrategies:
    css: |
      background:
        radial-gradient(ellipse at 18% 24%, oklch(70% 0.12 60 / 0.4) 0%, transparent 18%),
        radial-gradient(ellipse at 85% 65%, oklch(60% 0.10 50 / 0.3) 0%, transparent 22%),
        var(--paper);
      mix-blend-mode: multiply;
    raster: scanned aged-paper for ground truth
  reactiveBehaviors:
    light: no
    highlight: no
    depth: no
    parallax: tied to paper layer
  pairsWith:
    prototypeStyles: [style-serif-warm-paper, aesthetic-dark-academia, aesthetic-cottagecore, aesthetic-cottagegoth]
  killsTheIllusion:
    - symmetric stains (real foxing is asymmetric, lives where moisture pooled)
    - stains over photos (paper-edge-only)
```

## Common implementation mistakes (avoid these)

- symmetric stains (real foxing is asymmetric, lives where moisture pooled)
- stains over photos (paper-edge-only)

## Pairs with (prototype slugs)

- `style-serif-warm-paper`
- `aesthetic-dark-academia`
- `aesthetic-cottagecore`
- `aesthetic-cottagegoth`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 2805–2833 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

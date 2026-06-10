# Legal Pad (ruled yellow paper) (material)

**Tag:** material-legal-pad  ·  **Family:** analog  ·  **Category:** paper · matte

A matte analog surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: legal-pad
  name: Legal Pad (ruled yellow paper)
  family: analog
  category: paper
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: no
    deforms: yes — pages tear from spiral
    age: shows wear
  implementationStrategies:
    css: |
      background:
        repeating-linear-gradient(180deg,
          transparent 0px,
          transparent 21px,
          #D9C46B 22px
        ),
        linear-gradient(90deg,
          transparent 0px,
          transparent 47px,
          #C44 48px,
          #C44 49.5px,
          transparent 50px
        ),
        #F8E9A4;
    raster: optional yellow-pad scan
  reactiveBehaviors:
    light: no
    highlight: no
    depth: corner curl on hover
    parallax: minimal
  pairsWith:
    prototypeStyles: [style-skeuomorphism (notes-as-legal-pad), aesthetic-dark-academia, recipe-newspaper-of-record]
  killsTheIllusion:
    - lines that don't go full-bleed
    - missing red margin line
    - perfect type instead of handwriting
  examples:
    - iOS 6 Notes app
    - office-supply photography
```

### 4.2 Print process family

```yaml
```

## Common implementation mistakes (avoid these)

- lines that don't go full-bleed
- missing red margin line
- perfect type instead of handwriting

## Pairs with (prototype slugs)

- `style-skeuomorphism (notes-as-legal-pad)`
- `aesthetic-dark-academia`
- `recipe-newspaper-of-record`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 1878–1923 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

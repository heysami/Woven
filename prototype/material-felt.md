# Felt (matted wool, fuzzy) (material)

**Tag:** material-felt  ·  **Family:** analog  ·  **Category:** fabric · matte

A matte analog surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: felt
  name: Felt (matted wool, fuzzy)
  family: analog
  category: fabric
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: no specular
    deforms: yes — squashes on press
    age: ageless
  implementationStrategies:
    css: |
      background: oklch(45% 0.14 145);  /* poker green */
      filter: url(#feltFuzz);
    svg: |
      <filter id="feltFuzz">
        <feTurbulence baseFrequency="3" numOctaves="2"/>
        <feColorMatrix values="0 0 0 0 0.1  0 0 0 0 0.1  0 0 0 0 0.1  0 0 0 0.15 0"/>
      </filter>
    raster: photographed felt for accuracy
  reactiveBehaviors:
    light: no
    highlight: no
    depth: minor press deformation
    parallax: no
  pairsWith:
    prototypeStyles: [style-skeuomorphism (poker felt, billiards), aesthetic-dark-academia, aesthetic-cottagegoth]
  killsTheIllusion:
    - smooth colour with no fuzz
    - no soft edges (felt cuts soft)
```

## Common implementation mistakes (avoid these)

- smooth colour with no fuzz
- no soft edges (felt cuts soft)

## Pairs with (prototype slugs)

- `style-skeuomorphism (poker felt`
- `billiards)`
- `aesthetic-dark-academia`
- `aesthetic-cottagegoth`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 2411–2441 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

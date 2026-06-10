# VHS-Frutiger (Frutiger Aero with VHS distortion) (material)

**Tag:** material-vhs-frutiger  ·  **Family:** hybrid  ·  **Category:** digital-effect · glossy

A glossy hybrid surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: vhs-frutiger
  name: VHS-Frutiger (Frutiger Aero with VHS distortion)
  family: hybrid
  category: digital-effect
  physicalBehavior:
    surfaceFinish: glossy
    transparency: translucent
    reactsToLight: yes
    deforms: yes — VHS tracking bars
    age: shows wear (drop-outs)
  implementationStrategies:
    css: |
      filter: contrast(1.05) saturate(1.05);
    svg: glass panel + VHS chromatic-aberration filter stack
    raster: photographic plate + VHS overlay
    video: 30fps VHS distortion loop atop the Frutiger glass scene
  reactiveBehaviors:
    light: glass highlight via pointer; VHS shifts at periodic intervals
    highlight: yes
    depth: minimal
    parallax: substrate parallaxes
  pairsWith:
    prototypeStyles: [aesthetic-vaporwave, aesthetic-y2k-myspace, aesthetic-cassette-futurism]
  killsTheIllusion:
    - VHS effect blocking the Frutiger water/sky motif (riso-style overlay should let plate through)
  examples:
    - corporate-melancholic Vektroid record sleeves
    - PrismCorp fake-multinational catalogues
```

## Common implementation mistakes (avoid these)

- VHS effect blocking the Frutiger water/sky motif (riso-style overlay should let plate through)

## Pairs with (prototype slugs)

- `aesthetic-vaporwave`
- `aesthetic-y2k-myspace`
- `aesthetic-cassette-futurism`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 3046–3074 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

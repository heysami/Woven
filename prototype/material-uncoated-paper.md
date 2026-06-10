# Uncoated Paper (soft, porous, ink-absorbing) (material)

**Tag:** material-uncoated-paper  ·  **Family:** analog  ·  **Category:** paper · matte

A matte analog surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: uncoated-paper
  name: Uncoated Paper (soft, porous, ink-absorbing)
  family: analog
  category: paper
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: no specular
    deforms: yes — wrinkles, tears, dog-ears
    age: shows wear (yellowing, foxing)
  implementationStrategies:
    css: |
      background:
        url('paper-grain-2048.jpg') center/512px,
        oklch(97% 0.012 85);  /* warm white, never #FFF */
      background-blend-mode: multiply;
    svg: |
      <filter id="paperGrain">
        <feTurbulence baseFrequency="0.9" numOctaves="2" seed="3"/>
        <feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 0.06 0"/>
      </filter>
      <!-- 6% noise opacity -->
    raster: 2048×2048 scanned uncoated paper (Crane Lettra, Mohawk Superfine)
  reactiveBehaviors:
    light: no specular; ambient only
    highlight: minor warmth in hover state
    depth: corner curl on hover (CSS mask gradient)
    parallax: very subtle on scroll
  pairsWith:
    prototypeStyles: [style-serif-warm-paper, aesthetic-cottagecore, aesthetic-dark-academia, aesthetic-cottagegoth, style-raster-cutout]
  killsTheIllusion:
    - perfectly flat #FFF background (uncoated is always warm-tinted)
    - high-contrast specular highlight (uncoated has none)
    - tile pattern visibly repeating (use masking to break the seam)
    - body text at 16px with line-height 1.4 (editorial paper wants 18–19px / 1.55)
  examples:
    - The New Yorker print
    - Aeon longform
    - book covers from Penguin Modern Classics
  references:
    - https://www.jampaper.com/blog/paper-textures-and-finishes-2/
```

## Common implementation mistakes (avoid these)

- perfectly flat #FFF background (uncoated is always warm-tinted)
- high-contrast specular highlight (uncoated has none)
- tile pattern visibly repeating (use masking to break the seam)

## Pairs with (prototype slugs)

- `style-serif-warm-paper`
- `aesthetic-cottagecore`
- `aesthetic-dark-academia`
- `aesthetic-cottagegoth`
- `style-raster-cutout`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 1740–1781 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

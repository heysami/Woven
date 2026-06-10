# Marble (veined stone) (material)

**Tag:** material-marble  ·  **Family:** analog  ·  **Category:** stone · glossy (polished) or matte (honed)

A glossy (polished) or matte (honed) analog surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: marble
  name: Marble (veined stone)
  family: analog
  category: stone
  physicalBehavior:
    surfaceFinish: glossy (polished) or matte (honed)
    transparency: opaque
    reactsToLight: yes — soft sheen
    deforms: no
    age: ageless
  implementationStrategies:
    css: |
      background:
        radial-gradient(ellipse at 30% 20%, rgba(255,255,255,0.2), transparent 35%),
        linear-gradient(135deg, oklch(96% 0.005 0) 0%, oklch(85% 0.008 250) 100%);
      filter: url(#vein);
    svg: |
      <filter id="vein">
        <feTurbulence type="turbulence" baseFrequency="0.012" numOctaves="3"/>
        <feColorMatrix values="0 0 0 0 0.4  0 0 0 0 0.4  0 0 0 0 0.45  0 0 0 0.6 -0.4"/>
        <feComposite in2="SourceGraphic" operator="in"/>
      </filter>
    raster: photographed marble is the highest fidelity
  reactiveBehaviors:
    light: soft sheen tracks pointer
    highlight: yes
    depth: no
    parallax: minimal
  pairsWith:
    prototypeStyles: [aesthetic-dark-academia, aesthetic-defi-cosmic, aesthetic-vaporwave (the marble bust!), recipe-editorial-magazine]
  killsTheIllusion:
    - veins drawn perfectly (real marble is organic chaos)
    - matte without sheen (most marble is polished)
```

## Common implementation mistakes (avoid these)

- veins drawn perfectly (real marble is organic chaos)
- matte without sheen (most marble is polished)

## Pairs with (prototype slugs)

- `aesthetic-dark-academia`
- `aesthetic-defi-cosmic`
- `aesthetic-vaporwave (the marble bust!)`
- `recipe-editorial-magazine`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 2909–2942 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

# Wood Grain (walnut, dark, vertical grain) (material)

**Tag:** material-wood-grain-walnut  ·  **Family:** analog  ·  **Category:** wood · semi-gloss (varnished) or matte (raw)

A semi-gloss (varnished) or matte (raw) analog surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: wood-grain-walnut
  name: Wood Grain (walnut, dark, vertical grain)
  family: analog
  category: wood
  physicalBehavior:
    surfaceFinish: semi-gloss (varnished) or matte (raw)
    transparency: opaque
    reactsToLight: yes — anisotropic along grain
    deforms: no
    age: acquired patina (darkening over time)
  implementationStrategies:
    css: |
      background:
        linear-gradient(180deg, oklch(35% 0.08 40) 0%, oklch(22% 0.06 30) 100%);
      filter: url(#grain);
    svg: |
      <filter id="grain">
        <feTurbulence type="turbulence" baseFrequency="0.02 0.3" numOctaves="3"/>
        <feColorMatrix values="0 0 0 0 0.1  0 0 0 0 0.06  0 0 0 0 0.04  0 0 0 0.4 0"/>
      </filter>
      /* baseFrequency y ≫ x → vertical grain */
    raster: scanned walnut at 2048px, mask with noise to hide tile seam
  reactiveBehaviors:
    light: glint travels along grain on tilt
    highlight: yes — narrow strip along grain
    depth: minor for varnished
    parallax: no
  pairsWith:
    prototypeStyles: [style-skeuomorphism (library-as-wood-shelf), aesthetic-cottagecore, aesthetic-steampunk, aesthetic-dark-academia]
  killsTheIllusion:
    - regularly repeating tile (mask with noise)
    - isotropic noise (wood grain is directional)
    - perfect varnish gloss without grain
  examples:
    - iBooks wooden shelf
    - GarageBand stage skin
    - vintage radio cabinets
```

## Common implementation mistakes (avoid these)

- regularly repeating tile (mask with noise)
- isotropic noise (wood grain is directional)
- perfect varnish gloss without grain

## Pairs with (prototype slugs)

- `style-skeuomorphism (library-as-wood-shelf)`
- `aesthetic-cottagecore`
- `aesthetic-steampunk`
- `aesthetic-dark-academia`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 2871–2908 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

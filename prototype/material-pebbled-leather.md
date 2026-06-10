# Pebbled Leather (luxury goods finish) (material)

**Tag:** material-pebbled-leather  ·  **Family:** analog  ·  **Category:** leather · semi-gloss

A semi-gloss analog surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: pebbled-leather
  name: Pebbled Leather (luxury goods finish)
  family: analog
  category: leather
  physicalBehavior:
    surfaceFinish: semi-gloss
    transparency: opaque
    reactsToLight: yes — per-pebble micro-highlight
    deforms: yes — bends
    age: acquired patina (shines at touch points)
  implementationStrategies:
    css: |
      background: oklch(35% 0.04 50);
      filter: url(#pebble);
    svg: |
      <filter id="pebble">
        <feTurbulence type="fractalNoise" baseFrequency="0.18" numOctaves="3"/>
        <feSpecularLighting surfaceScale="2" specularConstant="0.8" specularExponent="20" lighting-color="#fff">
          <feDistantLight azimuth="225" elevation="45"/>
        </feSpecularLighting>
        <feComposite in2="SourceGraphic" operator="in"/>
      </filter>
    raster: scanned pebbled leather is the gold standard
  reactiveBehaviors:
    light: per-pebble highlight tracks light direction
    highlight: yes via DeviceOrientation/pointer
    depth: hover lift; press depresses
    parallax: minimal
  pairsWith:
    prototypeStyles: [style-skeuomorphism (leather wallet), aesthetic-dark-academia, aesthetic-defi-cosmic]
  killsTheIllusion:
    - perfectly uniform pebble pattern (real pebble varies)
    - no specular per pebble (luxury leather glints)
    - cold colour (leather is warm)
  examples:
    - vintage iCal leather header
    - Saffiano luxury wallets
    - bookbinding spines
  references:
    - https://leathera.com/textured-leather
```

## Common implementation mistakes (avoid these)

- perfectly uniform pebble pattern (real pebble varies)
- no specular per pebble (luxury leather glints)
- cold colour (leather is warm)

## Pairs with (prototype slugs)

- `style-skeuomorphism (leather wallet)`
- `aesthetic-dark-academia`
- `aesthetic-defi-cosmic`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 2478–2518 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

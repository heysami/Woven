# Ink Wash (sumi-e / brush-and-ink) (material)

**Tag:** material-ink-wash-sumi-e  ·  **Family:** analog  ·  **Category:** ink · matte

A matte analog surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: ink-wash-sumi-e
  name: Ink Wash (sumi-e / brush-and-ink)
  family: analog
  category: ink
  physicalBehavior:
    surfaceFinish: matte
    transparency: translucent
    reactsToLight: no
    deforms: no
    age: ageless
  implementationStrategies:
    css: |
      color: #1a1a1a;
      filter: url(#sumiEdge);
    svg: |
      <filter id="sumiEdge">
        <feTurbulence baseFrequency="0.04" numOctaves="2"/>
        <feDisplacementMap scale="3"/>
      </filter>
      <!-- Edge irregularity at SMALL scale — sumi brush keeps a recognizable form -->
    raster: scanned sumi-e brushwork is the most direct path
  reactiveBehaviors:
    light: no
    highlight: no
    depth: no
    parallax: minimal
  pairsWith:
    prototypeStyles: [aesthetic-anti-design, aesthetic-dark-academia, aesthetic-cottagegoth, aesthetic-vaporwave (Japanese gloss element)]
  killsTheIllusion:
    - regular vector stroke (sumi varies in pressure)
    - black at #000 (sumi ink is dark grey with brown undertone)
    - no paper bleed at terminals
```

## Common implementation mistakes (avoid these)

- regular vector stroke (sumi varies in pressure)
- black at #000 (sumi ink is dark grey with brown undertone)
- no paper bleed at terminals

## Pairs with (prototype slugs)

- `aesthetic-anti-design`
- `aesthetic-dark-academia`
- `aesthetic-cottagegoth`
- `aesthetic-vaporwave (Japanese gloss element)`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 2169–2201 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

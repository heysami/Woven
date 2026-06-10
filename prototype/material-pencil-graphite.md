# Pencil Graphite (HB to 6B sketch) (material)

**Tag:** material-pencil-graphite  ·  **Family:** analog  ·  **Category:** ink · matte

A matte analog surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: pencil-graphite
  name: Pencil Graphite (HB to 6B sketch)
  family: analog
  category: ink
  physicalBehavior:
    surfaceFinish: matte
    transparency: translucent
    reactsToLight: yes — graphite glints at angle
    deforms: no
    age: shows wear (smudges)
  implementationStrategies:
    css: |
      mix-blend-mode: multiply;
      filter: url(#graphite) contrast(0.8);
    svg: |
      <filter id="graphite">
        <feTurbulence baseFrequency="0.7" numOctaves="2"/>
        <feColorMatrix values="0 0 0 0 0.2  0 0 0 0 0.2  0 0 0 0 0.22  0 0 0 0.5 0"/>
      </filter>
    raster: scanned graphite drawing on textured paper
  reactiveBehaviors:
    light: subtle glint on hover (pointer-driven)
    highlight: minimal
    depth: smudge on press
    parallax: no
  pairsWith:
    prototypeStyles: [style-doodle, aesthetic-dark-academia, aesthetic-corporate-grunge, aesthetic-anti-design]
  killsTheIllusion:
    - pure black (graphite is blue-grey)
    - no paper texture visible underneath
  examples:
    - architectural sketches
    - storyboards
    - magazine essay illustrations
```

## Common implementation mistakes (avoid these)

- pure black (graphite is blue-grey)
- no paper texture visible underneath

## Pairs with (prototype slugs)

- `style-doodle`
- `aesthetic-dark-academia`
- `aesthetic-corporate-grunge`
- `aesthetic-anti-design`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 2233–2267 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

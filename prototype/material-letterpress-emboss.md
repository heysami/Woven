# Letterpress / Emboss (raised-impression printing) (material)

**Tag:** material-letterpress-emboss  ·  **Family:** analog  ·  **Category:** print · matte

A matte analog surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: letterpress-emboss
  name: Letterpress / Emboss (raised-impression printing)
  family: analog
  category: print
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: yes — directional shadow into the pressed area
    deforms: yes — paper is permanently deformed
    age: ageless
  implementationStrategies:
    css: |
      /* Pressed text (debossed) */
      color: transparent;
      text-shadow:
        0 1px 0 rgba(255,255,255,0.8),  /* light from top — highlight at bottom of impression */
        0 -1px 0 rgba(0,0,0,0.4);       /* shadow at top */
      /* Raised text (embossed) */
      .emboss {
        text-shadow:
          -1px -1px 0 rgba(255,255,255,0.8),
           1px  1px 0 rgba(0,0,0,0.4);
      }
    svg: |
      <feSpecularLighting> with offset light source for photoreal letterpress
    raster: scanned letterpress for ultra-high fidelity
  reactiveBehaviors:
    light: ALL pressed elements respect the same light direction
    highlight: shadow direction matches committed light
    depth: hover deepens the impression
    parallax: no
  pairsWith:
    prototypeStyles: [style-serif-warm-paper, aesthetic-cottagecore, aesthetic-dark-academia, recipe-editorial-magazine]
  killsTheIllusion:
    - light source disagreeing with rest of page
    - emboss/deboss on a non-paper substrate
    - colour text inside the impression (letterpress ink colour is muted)
  examples:
    - wedding stationery
    - business cards (Mast Brothers, Aesop)
    - premium book jackets
  references:
    - https://www.smashingmagazine.com/2012/07/letterpress-effect-fireworks-css/
```

### 4.3 Drawing / painting medium family

```yaml
```

## Common implementation mistakes (avoid these)

- light source disagreeing with rest of page
- emboss/deboss on a non-paper substrate
- colour text inside the impression (letterpress ink colour is muted)

## Pairs with (prototype slugs)

- `style-serif-warm-paper`
- `aesthetic-cottagecore`
- `aesthetic-dark-academia`
- `recipe-editorial-magazine`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 2080–2127 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

# RGB Channel Split (intentional large-displacement chromatic split) (material)

**Tag:** material-rgb-channel-split  ·  **Family:** digital  ·  **Category:** digital-effect · matte

A matte digital surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: rgb-channel-split
  name: RGB Channel Split (intentional large-displacement chromatic split)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: yes — displacement amount can react to pointer / tilt
    deforms: no (the channels shift, the structure stays)
    age: ageless
  implementationStrategies:
    css: |
      .rgb-split {
        position: relative;
        color: transparent;
      }
      .rgb-split::before,
      .rgb-split::after {
        content: attr(data-text);
        position: absolute; inset: 0;
        mix-blend-mode: screen;
      }
      .rgb-split::before { color: #ff0040; transform: translate(-2px, 0); }
      .rgb-split::after  { color: #00ffff; transform: translate( 2px, 0); }
    svg: |
      <feOffset> + <feColorMatrix> to isolate the R, G, B channels, then
      <feMerge> them with horizontal offsets. Drives reactive splits via
      animated <feOffset dx>.
    webgl: |
      sample input three times at (uv - offset, uv, uv + offset), output
      (sampleA.r, sampleB.g, sampleC.b). Trivial fragment shader.
    raster: not appropriate — RGB split needs the live composition
  reactiveBehaviors:
    light: split amount can grow with pointer velocity
    highlight: pointer-distance modulates the displacement
    depth: hover spreads the channels (treat as "depth on attention")
    parallax: scroll-velocity drives split amount
  pairsWith:
    prototypeStyles: [aesthetic-cyberpunk, aesthetic-acid-graphics, aesthetic-vaporwave, aesthetic-y2k-futurism, aesthetic-acid-design, recipe-terminal-on-web]
  killsTheIllusion:
    - applying to body text at any displacement that breaks legibility
    - symmetric offsets (real chromatic aberration is radial, biased toward edges)
    - flat across the whole frame (real lens CA gets worse toward corners)
  examples:
    - Blade Runner 2049 type treatment
    - 1980s VHS title cards
    - Kraftwerk "Computer World" sleeve
  references:
    - https://en.wikipedia.org/wiki/Chromatic_aberration
```

## Common implementation mistakes (avoid these)

- applying to body text at any displacement that breaks legibility
- symmetric offsets (real chromatic aberration is radial, biased toward edges)
- flat across the whole frame (real lens CA gets worse toward corners)

## Pairs with (prototype slugs)

- `aesthetic-cyberpunk`
- `aesthetic-acid-graphics`
- `aesthetic-vaporwave`
- `aesthetic-y2k-futurism`
- `aesthetic-acid-design`
- `recipe-terminal-on-web`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 1004–1053 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

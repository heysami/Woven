# ANSI Art (16-color extended-box character art) (material)

**Tag:** material-ansi-art  ·  **Family:** digital  ·  **Category:** digital-effect · glossy (CRT phosphor inheritance)

A glossy (CRT phosphor inheritance) digital surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: ansi-art
  name: ANSI Art (16-color extended-box character art)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: glossy (CRT phosphor inheritance)
    transparency: opaque
    reactsToLight: no
    deforms: no
    age: feels 1985-1995 BBS / hacker era
  implementationStrategies:
    css: |
      font-family: 'IBM Plex Mono', 'Px437 IBM VGA', monospace;
      background: #000;
      color: #aaaaaa;
      white-space: pre;
      line-height: 1;
      letter-spacing: 0;
      /* 16 ANSI colors: black, red, green, yellow, blue, magenta, cyan, white
                          + bright variants. Use CSS classes per glyph. */
    svg: not appropriate
    webgl: |
      shader sampling a 16-color ANSI palette LUT; each cell renders one of
      256 codepoints from CP437 (IBM PC code page, includes ░▒▓█).
    raster: pre-rendered ANSI art PNG (with native CP437 font)
  reactiveBehaviors:
    light: scanline overlay (often paired with crt-phosphor)
    highlight: pointer-hover can ripple through the character grid
    depth: ░▒▓█ stair-step encodes depth/distance
    parallax: stepped only (character grid is integer)
  pairsWith:
    prototypeStyles: [recipe-terminal-on-web, style-terminal-mono, aesthetic-cyberpunk, aesthetic-cassette-futurism, aesthetic-atompunk, aesthetic-corporate-grunge]
  killsTheIllusion:
    - using more than the 16 ANSI colors
    - non-CP437 codepoints (no curly quotes, no em-dashes)
    - proportional or anti-aliased fonts
  examples:
    - BBS title screens
    - ACiD Productions ANSI gallery
    - early hacker zine title pages
  references:
    - https://en.wikipedia.org/wiki/ANSI_art
```

## Common implementation mistakes (avoid these)

- using more than the 16 ANSI colors
- non-CP437 codepoints (no curly quotes, no em-dashes)
- proportional or anti-aliased fonts

## Pairs with (prototype slugs)

- `recipe-terminal-on-web`
- `style-terminal-mono`
- `aesthetic-cyberpunk`
- `aesthetic-cassette-futurism`
- `aesthetic-atompunk`
- `aesthetic-corporate-grunge`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 1644–1686 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

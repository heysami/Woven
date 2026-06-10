---
materialId: ansi-art
name: ANSI Art (16-color extended-box character art)
family: digital
category: digital-effect
surfaceFinish: glossy (CRT phosphor inheritance)
transparency: opaque
pairsPrototypes: [recipe-terminal-on-web, style-terminal-mono, aesthetic-cyberpunk, aesthetic-cassette-futurism, aesthetic-atompunk, aesthetic-corporate-grunge]
---

# ANSI Art (16-color extended-box character art)

A glossy (CRT phosphor inheritance) surface.

## Physical behavior

**Surface finish**: glossy (CRT phosphor inheritance)

**Transparency**: opaque

**Reacts to light**: no

**Deforms**: no

**Age / wear**: feels 1985-1995 BBS / hacker era

## Implementation strategies

```yaml
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
```

## Reactive behaviors

**Light**: scanline overlay (often paired with crt-phosphor)

**Highlight**: pointer-hover can ripple through the character grid

**Depth**: ░▒▓█ stair-step encodes depth/distance

**Parallax**: stepped only (character grid is integer)

## Common implementation mistakes (avoid these)

- using more than the 16 ANSI colors
- non-CP437 codepoints (no curly quotes, no em-dashes)
- proportional or anti-aliased fonts

## Examples in the wild

- BBS title screens
- ACiD Productions ANSI gallery
- early hacker zine title pages

## References

- https://en.wikipedia.org/wiki/ANSI_art

## Pairs with (prototype slugs)

- `recipe-terminal-on-web`
- `style-terminal-mono`
- `aesthetic-cyberpunk`
- `aesthetic-cassette-futurism`
- `aesthetic-atompunk`
- `aesthetic-corporate-grunge`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

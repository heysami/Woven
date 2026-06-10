---
materialId: monospace-code-grid
name: Monospace Code Grid (IDE / terminal text as visual material)
family: digital
category: digital-effect
surfaceFinish: matte
transparency: opaque
pairsPrototypes: [recipe-devtools-marketing, recipe-terminal-on-web, recipe-ai-foundry-dark, style-terminal-mono, style-dense-mono-dark, recipe-restrained-ai-marketing]
---

# Monospace Code Grid (IDE / terminal text as visual material)

A matte surface.

## Physical behavior

**Surface finish**: matte

**Transparency**: opaque

**Reacts to light**: no

**Deforms**: no

**Age / wear**: ageless (or feels current dev-tools era)

## Implementation strategies

```yaml
css: |
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-feature-settings: 'liga' 1, 'calt' 1;  /* ligatures: ≠ ⇒ ≤ ≥ */
  line-height: 1.5;
  letter-spacing: 0;
  /* syntax highlight via classes, not inline styles */
  .keyword { color: #c792ea }
  .string  { color: #c3e88d }
  .comment { color: #546e7a; font-style: italic }
svg: not appropriate
webgl: |
  WebGL text-rendering for code-as-particle (e.g. Matrix rain) uses MSDF
  fonts with per-glyph instancing.
```

## Reactive behaviors

**Light**: none

**Highlight**: pointer can advance type-on animation

**Depth**: stack of code panes at different opacities

**Parallax**: scroll-driven code scroll (canonical recipe-devtools-marketing)

## Common implementation mistakes (avoid these)

- non-monospace fonts (alignment dies)
- line-height < 1.3 (lines crush together)
- proportional ligature spacing
- rainbow syntax themes (most code is 3-5 colors, not 12)

## Examples in the wild

- GitHub editor
- VSCode default theme
- Anthropic devtools marketing pages

## References

- https://www.jetbrains.com/lp/mono/

## Pairs with (prototype slugs)

- `recipe-devtools-marketing`
- `recipe-terminal-on-web`
- `recipe-ai-foundry-dark`
- `style-terminal-mono`
- `style-dense-mono-dark`
- `recipe-restrained-ai-marketing`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

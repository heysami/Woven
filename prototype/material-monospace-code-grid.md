# Monospace Code Grid (IDE / terminal text as visual material) (material)

**Tag:** material-monospace-code-grid  ·  **Family:** digital  ·  **Category:** digital-effect · matte

A matte digital surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: monospace-code-grid
  name: Monospace Code Grid (IDE / terminal text as visual material)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: no
    deforms: no
    age: ageless (or feels current dev-tools era)
  implementationStrategies:
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
  reactiveBehaviors:
    light: none
    highlight: pointer can advance type-on animation
    depth: stack of code panes at different opacities
    parallax: scroll-driven code scroll (canonical recipe-devtools-marketing)
  pairsWith:
    prototypeStyles: [recipe-devtools-marketing, recipe-terminal-on-web, recipe-ai-foundry-dark, style-terminal-mono, style-dense-mono-dark, recipe-restrained-ai-marketing]
  killsTheIllusion:
    - non-monospace fonts (alignment dies)
    - line-height < 1.3 (lines crush together)
    - proportional ligature spacing
    - rainbow syntax themes (most code is 3-5 colors, not 12)
  examples:
    - GitHub editor
    - VSCode default theme
    - Anthropic devtools marketing pages
  references:
    - https://www.jetbrains.com/lp/mono/
```

---

## 4. Analog materials

Materials that exist physically and pass through a scanner, camera, or sampler before they land on the web. The orchestrator must respect that PATH — analog materials at flat opacity, perfectly regular, instantly betray themselves.

### 4.1 Paper family

```yaml
```

## Common implementation mistakes (avoid these)

- non-monospace fonts (alignment dies)
- line-height < 1.3 (lines crush together)
- proportional ligature spacing

## Pairs with (prototype slugs)

- `recipe-devtools-marketing`
- `recipe-terminal-on-web`
- `recipe-ai-foundry-dark`
- `style-terminal-mono`
- `style-dense-mono-dark`
- `recipe-restrained-ai-marketing`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 1687–1739 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

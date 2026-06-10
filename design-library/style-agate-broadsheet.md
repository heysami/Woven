---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: style-agate-broadsheet-ui.png
    reason: Style surface UI mockup.
  - src: style-agate-broadsheet-isolated.png
    reason: Signature surface, isolated.
---
# Agate-numeric broadsheet (style)

**Tag:** `style-agate-broadsheet`

**Canonical references:** WSJ, NYT, FT, Guardian, Bloomberg print

## Surface treatment

**Background**
- Paper-white `oklch(98% 0.005 90)` default
- FT salmon `oklch(94% 0.04 50)` as a brand-specific alternative
- Pure white reserved for tombstones and pull quotes

**Ink**
- Body: near-black `oklch(15% 0.01 80)`
- Greys: dot-screen `oklch(70% 0.005 80)` for rules, captions, agate scaffolding
- Accent: a **single** brand colour — WSJ red, FT orange-red, NYT cobalt op-ed, Guardian blue. Never two accents on one page.

**Type stack — three jobs, three faces**
- **Display serif (optical-size cuts):** Escrow, Cheltenham, Financier, Tiempos Headline — Display / Text / Banner cuts switched by size
- **Sans deck / kicker:** Exchange, Franklin Gothic, Guardian Sans — uppercase kickers, sentence-case decks
- **Agate numeric face (mandatory for any numeric column):** Retina, Empirica, Benton Modern Compressed, Bureau Grotesque Agate. Tabular figures, condensed widths. Without it the surface dies.

**Sizes**
- Agate: 9 / 10 px (tables, market data, scores)
- Body: 13–15 px serif
- Deck: 16–18 px sans
- Kicker: 12 px sans uppercase, +80 tracking
- Display: 28 / 36 / 48 / 64 / 96 px serif

**Line-height**
- Body 1.3–1.4 (denser than magazine; this is a tell)
- Agate 1.15
- Display 0.95–1.05

**Radius:** 0. Everything. No exceptions.

**Borders / rules**
- 1px hairline rules between sections (`oklch(70% 0.005 80)`)
- 2px black masthead rule above **and** below the title
- 0.5px column rules optional in dense tables
- Kicker bar: 2px solid accent, 24–40px wide, sitting above the headline

**Shadow:** none. Ever. This is print.

**Gradients / blur:** none.

**Decoration grammar (mandatory)**
- Hairline rules between sections
- Kicker bars in the single accent colour
- Drop caps on lede paragraphs (3-line, display serif)
- Byline dingbats (em-dash, bullet, or small caps "BY")
- Table tombstones — boxed numeric callouts with rule-top, rule-bottom

**Decoration grammar (forbidden)**
- Rounded corners
- Soft shadows or glow
- Gradient fills
- Coloured backgrounds beyond the paper/salmon base
- More than one accent hue
- Tabular-figure-less proportional digits in any data column

## Motion

Ticker marquee only — linear, infinite, ~40s per cycle. No hover lifts, no fades, no parallax. Page loads as a static document.

## Failure mode

Single Georgia for everything + grey `#6b7280` everywhere + no agate face in the tables = magazine cosplay wearing a newspaper costume. The agate numeric face is non-negotiable; without it the dense tables read as bad typography rather than as a broadsheet voice.

## Best for

Subjects where a fact-of-record voice is the point: market data, election results, sports box scores, obituaries, investigative longform, financial filings, anything that wants the authority of a paper of record.

## Pairs well with

- **Shells:** shell-editorial-broken-grid (primary), shell-three-column-app, shell-two-column-app, shell-centered-column (for the article-page variant), shell-top-bar-canvas (with masthead as the top bar)
- **Aesthetics:** aesthetic-swiss-modernist, aesthetic-anti-design, aesthetic-bauhaus, aesthetic-constructivism, aesthetic-maximalism (editorial-considered variant)

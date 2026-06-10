---
# Sample-image references for the System-tab design library. Images sit
# next to this file in prototype/ and were generated via image_gen.
images:
  - src: style-serif-warm-paper-ui.png
    reason: Generated UI mockup showing this style's surface treatment — type, color, shadow, corner, and component register together.
  - src: style-serif-warm-paper-isolated.png
    reason: Isolated subject sample — the style's signature surface (component, card, or hero element) on a neutral background.
---
# Serif warm-paper editorial (style)

**Tag:** `style-serif-warm-paper`

**Canonical references:** The New Yorker longform, Aeon essays, The Atlantic features, Harper's Magazine, Matter (Medium)

## Surface treatment

**Background:** warm paper white — `#FBF7F0` / `oklch(0.97 0.012 85)`. Never pure white. Optional faint paper grain at 2-4% opacity.

**Ink:** soft black `#1B1A17` / `oklch(0.22 0.01 60)` for body — never `#000`. Secondary `#5C544A`. Hairline rules `#D8CFC0`.

**Accent:** a single restrained editorial color — burgundy `#7A2A2A`, ink blue `#1F3A5F`, or forest `#2C4A3A`. Used for links, drop caps, dingbats only.

**Type stack:**
- Body serif: Source Serif Pro, Iowan Old Style, Spectral, Lyon, or Tiempos
- Display: same serif at large size, or a quiet grotesque (Söhne, Untitled Sans, Inter) for headings
- Italics are mandatory and used freely — titles, emphasis, foreign words

**Sizes (px):** 12 / 14 / 17–19 (body) / 24 / 32 / 48 / 72. Body at 18-19px is the workhorse.

**Line-height:** body 1.55–1.65; headings 1.1–1.2. Letter-spacing near 0; small-caps and tracked-out caps allowed for labels.

**Radius:** 0 to 2px. Square corners. No card shadows.

**Borders:** hairline rules (0.5–1px) in `#D8CFC0`. Used to separate sections, byline, footer.

**Decoration grammar (mandatory):**
- Drop caps: `:first-letter { float: left; font-size: 4em; line-height: 0.85; padding-right: 0.1em }` on opening paragraph
- Pull quotes: serif italic, 1.4–1.6em, generous vertical margin, optional thin rule above/below
- Dingbats (`§`, `❧`, `✦`, `* * *`) to separate sections
- Hairline rule above bylines and after the dek
- Numerals: oldstyle figures (`font-variant-numeric: oldstyle-nums`)

**Forbidden:** gradients, glass effects, neon, drop shadows on text, all-caps body, sans-serif body text, emoji, neon accent colors.

## Motion budget

Minimal. Smooth scroll, gentle fade-in on long-form sections (200-400ms ease-out). No parallax. No hover lifts. Links underline on hover with a subtle color shift (120ms). Footnote reveals can use a quiet expand (200ms).

## Failure mode

The trashy AI tell: Times New Roman on a `#fff` background with `text-align: justify`, no drop cap, body set at 16px with line-height 1.4, and a stock photo banner. Reads as a printed Wikipedia page, not an editorial object. The warm paper, the 18px body, the oldstyle figures, and the drop cap are non-negotiable.

## Best for

Longform journalism, essays, criticism, manifestos, considered product writing, brand storytelling, archival/scholarly content. Subjects where the reader is expected to slow down. Audiences who read for pleasure.

## Pairs well with

- Shells: `shell-centered-column`, `shell-editorial-broken-grid`, `shell-hero-stack`, `shell-masonry`
- Aesthetics: `aesthetic-dark-academia`, `aesthetic-coastal-grandmother`, `aesthetic-cottagecore`, `aesthetic-maximalism`, `aesthetic-anti-design`

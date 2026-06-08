# Brutalist raw web (style)

**Tag:** `style-brutalist-raw`

**Canonical references:** Bloomberg.com pre-redesign, Craigslist, bloomberg.com/businessweek special features, Balenciaga.com, Bloomberg Hyperdrive

## Surface treatment

**Color**
- Background: `#FFFFFF` pure paper white OR `#000000` pure ink black
- Text: opposite of background, no off-tones
- One accent only, at full saturation: `#FF0000`, `#0000FF`, `#FFFF00`, or `#00FF00` — pick ONE per page
- Forbidden: greys between `#111` and `#EEE`, off-whites, off-blacks, tinted neutrals

**Type stack**
- Headlines: `Times New Roman, serif` OR `Helvetica, Arial, sans-serif` — pick ONE for the whole document
- Body: same family as headlines (no mixing serif + sans)
- Mono (only if needed for code/tabular): `Courier, monospace`
- Sizes: extreme contrast — `14px / 24px / 96px / 200px` — no in-between scale
- Line-height: `1.0` on display, `1.2` on body — tight
- Letter-spacing: `0` always, never tracked

**Borders and corners**
- `border-radius: 0` everywhere, no exceptions
- Borders: `1px solid currentColor` or `2px solid currentColor`, no half-pixel hairlines
- No shadows. No `box-shadow`. No `text-shadow`.
- No gradients. No `background: linear-gradient(...)`.
- No blur. No `backdrop-filter`.

**Links and interactive states**
- Every link underlined by default (`text-decoration: underline`)
- No color change on hover — underline stays, color stays
- Buttons are `<a>` or `<button>` with `border: 2px solid` and no fill, or full-bleed inverted block
- Focus: `outline: 2px solid` accent color, never `outline: none`

**Decoration grammar**
- Mandatory: intentional ugliness — xerox texture, halftone dots, blocky type used as graphic element, oversized type that breaks the viewport
- Allowed: raw `<hr>` rules, ASCII separators (`---`, `***`), system-default form controls
- Forbidden: rounded buttons, drop shadows, soft pastels, illustrations, icons (use Unicode glyphs `→ ← ↓ ↑ × ✓`), stock photography unless deliberately degraded

**Voice (visible on surface)**
- Blunt, declarative, all-lowercase OR ALL UPPERCASE — pick one and hold it
- No marketing softeners ("just", "simply", "easily")

## Motion budget

- `transition: none` is the default
- Allowed: instant state swap (`:hover` flips background to accent in one frame)
- Forbidden: ease curves, fade-ins, scroll reveals, parallax, hover-lift, spring physics
- If motion is unavoidable: `transition: none` plus a hard cut via `@keyframes` step-end

## Failure mode

The trashy AI tell is **soft brutalism** — `border-radius: 4px` "for accessibility", a `box-shadow: 0 1px 2px rgba(0,0,0,.05)` "for depth", grey `#F5F5F5` backgrounds "for hierarchy", and `transition: all 0.2s ease` on hovers. The result is a normal SaaS page with Helvetica. Real brutalism refuses every comfort: square corners, full-contrast color, no transitions, no shadows, underlined links. If a designer would call it "harsh", it's correct.

## Best for

- Editorial / news verticals that want to signal seriousness or anti-design credibility
- Fashion houses and gallery sites where withholding polish IS the polish
- Indie tools, manifestos, zines, archives
- Anti-corporate brands, art-school portfolios
- Subjects where readability and information density beat visual seduction

## Pairs well with

- Shells: `shell-editorial-broken-grid`, `shell-centered-column`, `shell-two-column-app`, `shell-three-column-app`, `shell-top-bar-canvas`, `shell-masonry`
- Aesthetics: `aesthetic-web-brutalism`, `aesthetic-anti-design`, `aesthetic-constructivism`, `aesthetic-corporate-grunge`, `aesthetic-acid-graphics`

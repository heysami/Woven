---
# Sample-image references for the System-tab design library. Images sit
# next to this file in prototype/ and were generated via image_gen.
images:
  - src: style-restrained-hairline-ui.png
    reason: Style surface UI mockup.
  - src: style-restrained-hairline-isolated.png
    reason: Signature surface, isolated.
---
# Restrained-hairline (style)

**Tag:** `style`

**Canonical references:** Linear app UI, Vercel dashboard, Read.cv, Stripe Dashboard 2023, Raycast.

## Surface treatment

**Palette (greys do the work):**
- Background: `oklch(0.99 0.004 250)` light / `oklch(0.18 0.008 250)` dark
- Surface: `oklch(0.97 0.004 250)` / `oklch(0.21 0.008 250)`
- Border hairline: `oklch(0.90 0.005 250)` / `oklch(0.28 0.01 250)`
- Text primary: `oklch(0.22 0.01 250)` / `oklch(0.95 0.005 250)`
- Text secondary: `oklch(0.50 0.01 250)` / `oklch(0.68 0.008 250)`
- Single accent: `oklch(48% 0.13 252)` — used sparingly, one per view max
- Semantic only when machine-stated: success `oklch(60% 0.13 145)`, warn `oklch(70% 0.14 75)`, error `oklch(58% 0.18 27)`

**Type stack:**
- UI / body: Inter or IBM Plex Sans, weight 400/500 only — 600 forbidden except in `<th>`
- Mono: JetBrains Mono — reserved for machine state (IDs, timestamps, keybinds, code, status)
- No display face. No serif.

**Sizes (px):** 10 / 10.5 / 11.5 / 12 / 12.5 / 14 / 16. Body sits at 13. Line-height 1.45 body, 1.2 headings.

**Radius:** 4 (inputs, chips), 6 (cards, buttons), 10 (modals, large surfaces). Never 0, never above 12.

**Borders:** hairline 1px only. No 2px+ strokes. Border-color carries hierarchy; no double borders.

**Shadows:**
- `shadow-sm`: `0 1px 0 oklch(0% 0 0 / 0.04)` — seam, not depth
- `shadow-md`: `0 1px 2px oklch(0% 0 0 / 0.06), 0 4px 12px oklch(0% 0 0 / 0.04)` — popovers only
- No glow, no colored shadow, no inset.

**Gradients:** forbidden on surfaces. Permitted only on a single hairline accent (e.g. a 1px progress bar).

## Decoration grammar

Mandatory: hairline dividers, mono for machine state, single-accent rule per view, focus ring is `outline: 1px solid accent; outline-offset: 2px`.

Forbidden: drop shadows on text, blur backdrops, gradient surfaces, icon fills above 1.5px stroke, emoji, exclamation marks, marketing adjectives in UI copy.

## Motion budget

- Hover state change: `120ms cubic-bezier(.2,.8,.2,1)`
- Panel transitions: `180ms`
- Progress / determinate loaders: `400ms` linear
- One ambient pulse permitted (e.g. live indicator dot at 2s ease-in-out)
- No parallax, no easing bounce, no spring overshoot.

## Voice

Terse, technical, lowercase labels acceptable. Numbers and IDs preferred over words. No marketing voice.

## Failure mode

Treating "minimal" as "empty + one purple button." The look isn't absence — it's density of typographic information at 13px with hairline seams. AI tells: oversized hero with one CTA, rounded-2xl cards, gradient buttons, drop shadows on text, emoji in nav, sentence-case marketing copy in tooltips.

## Best for

Developer tools, internal dashboards, IDE-adjacent products, project management for power users, status pages, anything where the user opens it 40 times a day and density beats delight.

## Pairs well with

- Shells: shell-three-column-app, shell-two-column-app, shell-top-bar-canvas, shell-bento-grid, shell-centered-column
- Aesthetics: aesthetic-anti-design, aesthetic-swiss-modernist, aesthetic-cassette-futurism (restrained variants only)

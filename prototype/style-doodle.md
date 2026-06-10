---
# Sample-image references for the System-tab design library. Images sit
# next to this file in prototype/ and were generated via image_gen.
images:
  - src: style-doodle-ui.png
    reason: Style surface UI mockup.
  - src: style-doodle-isolated.png
    reason: Signature surface, isolated.
---
# Doodle UI (hand-drawn) (style)

**Tag:** `style`

**Canonical references:** Excalidraw, tldraw draw-style, Rough.js, Shantell Sans, Whimsical

## Surface treatment

**Background:** paper #F9F9F7 (light) / ink-slate #121212 with #1E1E1E panels (dark). Optional subtle paper grain at 4–6% opacity max — never visible texture.

**Color:** ink #1B1B1F as the only true black, mid-grey #6B6B70, hairline #E5E5E0. Marker accents in muted gouache — red #E03131, orange #F08C00, yellow #F59F00, green #2F9E44, teal #099268, blue #1971C2, violet #6741D9. All ~70% chroma, never full sRGB primaries. Fills use 15–25% alpha of stroke color, never solid.

**Type stack:**
- Handwritten labels, callouts, sticky-note text: Excalifont or Shantell Sans (Informality axis 50, Bounce 30)
- Toolbar / menu / property-panel chrome: Inter or IBM Plex Sans 500
- Code shapes: Cascadia Code or JetBrains Mono

Chrome type is NEVER hand-drawn.

**Sizes:** handwritten 14 / 16 / 20 / 28 / 40px · chrome 12 / 13 / 14px · code 13px mono.

**Line-height:** 1.35 body handwritten (looser to fake baseline jitter), 1.45 display, 1.5 chrome.

**Radius:** shapes 2–4px (rough.js wobble does the rounding visually) · buttons 8px · panels 12px · sticky-notes 1px (corners drawn, not CSS).

**Borders:** three discrete stroke weights only — thin 1.25px, bold 2px, extra-bold 3.5px. Never a continuous slider. `stroke-linecap: round`, `stroke-linejoin: round`. Chrome panels get 1px hairline #E5E5E0 only.

**Shadow:** forbidden on shapes. Chrome panels get one shadow `0 1px 2px rgba(0,0,0,0.04), 0 8px 24px rgba(0,0,0,0.06)`. Sticky-notes get a single offset `2px 2px 0 rgba(0,0,0,0.08)` flat ink-shadow, no blur.

## Decoration grammar

**Mandatory:** rough.js (or rough-svg equivalent) for every drawn shape — `roughness: 1.0–1.8`, `bowing: 1–2`, multi-stroke on, `fillStyle: hachure` or `zigzag` at `hachureAngle: -41°` and `hachureGap: 4–8px`, `fillWeight: 1px`. Each shape gets a UNIQUE random seed.

**Forbidden:** paper-texture backgrounds above 8% opacity, decorative scribbles/stars used as filler, gradients of any kind, glow, embossed type, Comic Sans, perfectly straight 1px SVG strokes underneath the handwritten labels.

## Motion budget

- 140–200ms ease-out for chrome
- Shape entry can use a `stroke-dashoffset` draw-in over 320ms `cubic-bezier(.2, .7, .2, 1)`
- Hover wobble allowed only by re-seeding rough.js with a new seed (no CSS transform jitter loops)
- Forbidden: bounce easings, parallax, gradient sweeps, any "shake to be playful" idle animation

## Voice

Lowercase, conversational, present-tense, contractions welcome ("let's sketch this", "drop a note"). Never marketing exclamation, never emoji in chrome.

## Failure mode

Comic Sans over geometrically perfect SVG strokes with no roughness/bowing, uniform 1px lines everywhere, crayon-rainbow primaries at full chroma, drop-shadows and gradients carried over from a Material template, scribbles/stars scattered as decoration instead of as annotation, paper-grain texture cranked so it reads as parchment, every wobble using the same seed so all shapes jitter in identical lock-step.

## Best for

Whiteboarding and diagramming tools · flowchart and mind-map editors · kids' learning apps and storytelling tools · design-thinking workshop canvases · lecture-note and study apps · low-fi wireframing · brainstorming and retro boards · anywhere the product wants to signal "this is a draft, edit me" rather than "this is final, submit it".

## Pairs well with

- **Shells:** shell-infinite-canvas, shell-canvas-floating, shell-top-bar-canvas, shell-three-column-app, shell-two-column-app, shell-centered-column, shell-scrapbook-substrate
- **Aesthetics:** aesthetic-cottagecore, aesthetic-positivity-kawaii, aesthetic-solarpunk, aesthetic-corporate-memphis, aesthetic-curly-girly, aesthetic-cluttercore

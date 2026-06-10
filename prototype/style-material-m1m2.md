---
# Sample-image references for the System-tab design library. Images sit
# next to this file in prototype/ and were generated via image_gen.
images:
  - src: style-material-m1m2-ui.png
    reason: Generated UI mockup showing this style's surface treatment — type, color, shadow, corner, and component register together.
  - src: style-material-m1m2-isolated.png
    reason: Isolated subject sample — the style's signature surface (component, card, or hero element) on a neutral background.
---
# Material Design (M1/M2) (style)

**Tag:** `style`

**Canonical references:** Android Lollipop 2014; Inbox by Gmail 2014-2019; Google Calendar / Keep / Play Music; m2.material.io spec; Pablo Costa "Paper & Ink" history.

## Surface treatment

Flat color on lifted paper. White or grey-50 cards float on a tinted canvas, each one a discrete 2dp rectangle with a two-layer key+ambient shadow. One saturated brand hue carries the surface; one accent hue carries action. The 2px corner radius is the M1/M2 tell — not the 12-28px softness of M3.

**Color**: page canvas `#FAFAFA` (Grey 50) so white cards read as lifted paper. Pick ONE primary family + ONE accent from the M1 palette — primary 500 for the brand hue (e.g. Indigo 500 `#3F51B5`, Red 500 `#F44336`, Teal 500 `#009688`), primary 700 (`#303F9F` for Indigo) for status-bar-style accents, accent A200 (`#FF4081` Pink, `#536DFE` Indigo A200) for FAB/selection/links only. Text uses black at three opacities — primary `rgba(0,0,0,.87)`, secondary `rgba(0,0,0,.60)`, disabled/hint `rgba(0,0,0,.38)`, dividers `rgba(0,0,0,.12)`. Never pick grey hexes by eye.

**Type stack**: `Roboto` (Light 300 / Regular 400 / Medium 500) as the universal sans for everything; `Roboto Mono` for code; `Roboto Slab` only for editorial display in Keep-style notes.

**Sizes** (M2 scale, letter-spacing values mandatory in px):
- Headline 1 96px Light -1.5
- Headline 2 60px Light -0.5
- Headline 3 48px Regular 0
- Headline 4 34px Regular 0.25
- Headline 5 24px Regular 0
- Headline 6 20px Medium 0.15
- Subtitle 1 16px Regular 0.15
- Subtitle 2 14px Medium 0.1
- Body 1 16px Regular 0.5
- Body 2 14px Regular 0.25
- Button 14px Medium 1.25 UPPERCASE
- Caption 12px Regular 0.4
- Overline 10px Regular 1.5 UPPERCASE

**Line-height**: body 1.5, display 1.2, app-bar title 1.0.

**Radius**: card `2px`, raised button `2px`, dialog `2px`, text-field underline 0px (1px bottom border, 2px on focus in primary 500), FAB `50%` (perfect circle), chip `16px` pill.

**Borders**: cards have NO border, only shadow. Text fields use a 1px bottom rule `rgba(0,0,0,.42)` thickening to 2px in primary 500 on focus. Dividers are full-bleed 1px `rgba(0,0,0,.12)` inside lists.

**Shadow** (two-layer key+ambient per elevation, NEVER a single shadow; a screen MUST show at least three distinct levels):
- 2dp card: `0 1px 3px rgba(0,0,0,.12), 0 1px 2px rgba(0,0,0,.24)`
- 4dp raised button / app bar: `0 3px 6px rgba(0,0,0,.16), 0 3px 6px rgba(0,0,0,.23)`
- 6dp FAB / snackbar: `0 10px 20px rgba(0,0,0,.19), 0 6px 6px rgba(0,0,0,.23)`
- 8dp menu / pressed button: `0 14px 28px rgba(0,0,0,.25), 0 10px 10px rgba(0,0,0,.22)`
- 16dp drawer / 24dp dialog: `0 19px 38px rgba(0,0,0,.30), 0 15px 12px rgba(0,0,0,.22)`

**Motion budget**: standard easing `cubic-bezier(0.4, 0.0, 0.2, 1)`, decelerate (incoming) `cubic-bezier(0.0, 0.0, 0.2, 1)`, accelerate (outgoing) `cubic-bezier(0.4, 0.0, 1, 1)`. Durations 150ms small (icon toggle), 250ms medium (card expand), 375ms large (full-screen transition). Mandatory ink-ripple on every tap target: a circle scales from touch point to bounds in 300ms with `rgba(0,0,0,.12)` (or white on dark). FAB morphs into a sheet, never just fades. Forbidden: parallax, blur, spring overshoot bouncier than 1.05.

**Decoration grammar**:
- Mandatory — one bold saturated brand hue used assertively; Material Icons in 24dp grid (filled style, never mix with outlined); UPPERCASE in buttons (`SEND`, `LEARN MORE`) and overlines — the all-caps button is the era signature; sentence case in body.
- Forbidden — gradients (M1/M2 is flat color on lifted paper); glassmorphism; neumorphism; drop-shadow on text; mixed filled+outlined icons; multi-hue rainbow palettes (one primary + one accent, that's it); rounded corners > 4px on any rectangle.

## Failure mode

Same flat single-layer shadow on every element so nothing reads as elevated. Grey backgrounds picked by eye instead of `#FAFAFA` + black-with-opacity text. Roboto missing so display renders in system-ui Regular and loses the Light/Medium contrast. FAB drawn as a square chip or omitted. Sentence-case buttons kill the all-caps signature. Saturated 500 used as page background instead of confined to a chrome element. 8-12px radius everywhere — that's M3, not M2.

## Best for

Productivity inboxes and triage tools (Inbox/Gmail/Calendar genre); note-taking with colored cards (Keep genre); music and media players with bold hero art (Play Music genre); enterprise Android dashboards; fitness/health trackers from the 2015-2019 era; retro re-skins of utilities that want to feel like "an Android app from when Android had a point of view."

## Pairs well with

- Shells: shell-mobile-app, shell-two-column-app, shell-three-column-app, shell-top-bar-canvas, shell-bento-grid, shell-masonry, shell-hero-stack
- Aesthetics: aesthetic-frutiger-aero, aesthetic-frutiger-bright-tertiaries, aesthetic-frutiger-four-colors, aesthetic-corporate-memphis, aesthetic-positivity-kawaii

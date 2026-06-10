---
# Sample-image references for the System-tab design library. Images sit
# next to this file in prototype/ and were generated via image_gen.
images:
  - src: style-raster-cutout-ui.png
    reason: Style surface UI mockup.
  - src: style-raster-cutout-isolated.png
    reason: Signature surface, isolated.
---
# Raster cutout collage (style)

**Tag:** `style-raster-cutout`

**Canonical references:** Heaven by Marc Jacobs, SSENSE Editorial / Eric Hu, Toiletpaper Magazine, Apartamento, Hack Club Scrapbook CSS

> **Raster required:** the surface IS raster cutouts on a raster substrate. Before drawing, follow the [**Raster requirements**](../prototype.md#raster-requirements--when-svg-will-not-deliver-the-genre) decision tree — image-gen MCP first, then `WebFetch` from public-domain archives, then project assets, then ask. If all fail, switch to a different style rather than fake cutouts in SVG.

## Surface treatment

**Substrate (the page background — always a raster texture, never flat CSS):**
- Paper: warm off-white `#F2EBDC` scan at 1600px+ with visible fibers
- Corkboard: tan `#B5894A` with grain at 12–18% contrast
- Fabric / felt: muted `#7A8B6E` or `#C8A488` weave at 30–60% scale
- Journal page: ruled `#FAF7EF` with cyan `#6FA8C7` lines and red `#D14B4B` margin
- Substrate is `position: fixed; inset: 0; z-index: 0;` and full-bleed — never tile, never blur, never tint

**Color (driven by the cutouts, not by tokens):**
- Cutout images carry their own palette — do not recolor them
- Marginalia ink: `#1A1A1A` (felt-tip), `#1B3A8C` (ballpoint blue), `#C42A2A` (red pen)
- Highlighter swipes: `#FFF35C` at 50% multiply, `#FF8AC2` at 50% multiply
- Forbidden: brand-palette tokens applied to images, hue-rotate filters, duotone treatments

**Type stack:**
- Marginalia / labels: handwritten — `Caveat`, `Kalam`, `Patrick Hand`, `Homemade Apple`
- Stamped / printed-on-tape: `Special Elite`, `Courier Prime`, or `IBM Plex Mono`
- Cut-from-magazine headlines: tightly-cropped raster strips of real type (Druk, Times, Cooper Black) — NOT webfonts
- Body chrome (only when unavoidable): `Inter` 14px, demoted

**Sizes:** marginalia 14–22px · stamped 11–14px tracked +60 · cut-headline strips sized by image, never re-rendered

**Line-height:** 1.35 on handwritten (let it wander), 1.2 on stamped

**Radius:** never. Edges are torn, cut, or photographed — not rounded. `border-radius: 0` on every CSS element. Roundness comes from the image alpha.

**Edges and shadows:**
- Every cutout gets a paper-edge shadow: `filter: drop-shadow(0 2px 1px rgba(0,0,0,0.18)) drop-shadow(0 8px 14px rgba(0,0,0,0.12))`
- Rotation: each cutout gets `rotate(-6deg)` to `rotate(7deg)` — never `0deg`, never identical neighbors
- Overlap is mandatory — cutouts must touch and occlude
- Forbidden: CSS `box-shadow`, `border-radius`, gradients, `backdrop-filter`, `filter: blur()`

**Decoration grammar (the tape / pin / staple layer):**
- Washi tape: 4–8 colored SVG or PNG strips at random angles, 8–14% opacity over the cutout edge
- Push pins: tiny PNG pin heads (red, yellow, blue) at cutout corners
- Staples: 6×2px dark grey rectangles, two per attachment
- Doodles in margins: arrows, underlines, hearts, asterisks — hand-drawn raster or SVG with `stroke-linecap: round`
- Highlighter: rectangle with `mix-blend-mode: multiply` and slight rotation
- Forbidden: emoji as decoration, geometric icon sets, perfectly aligned tape, symmetrical pin placement

**Voice (visible on surface):**
- Handwritten asides, crossed-out words, parenthetical notes, dated entries
- Lowercase, fragmentary, personal
- Never marketing copy in a handwritten font

## Motion budget

- Cutouts on hover: `transform: rotate(+/-1deg) translateY(-2px)` over 180ms `cubic-bezier(.2,.7,.2,1)` — like a paper scrap being nudged
- Tape and pins: no motion, they're fixed
- Entry: stagger cutouts in with a `transform: scale(0.94) rotate(initial-rotation)` to final over 220ms — never fade-in alone
- Forbidden: parallax substrates, gradient sweeps, glow pulses, scroll-jacked reveals, any motion that would shake the paper metaphor

## Failure mode

The trashy AI tell is **scrapbook without cutouts** — a flat tan `#D2B48C` background with `border-radius: 12px` cards, a "handwritten" Google Font on every label, three emoji as "stickers", `box-shadow: 0 4px 12px rgba(0,0,0,.1)`, and not a single raster PNG-with-alpha anywhere. The substrate looks like a CSS color, every "tape" is a flat coloured div, every "cutout" is a rounded card. Real raster collage is unmistakable because the components are PHOTOGRAPHS of physical things — a pressed leaf, a torn ticket, a polaroid, a scanned magazine clipping — sitting on a SCAN of a real surface. If you can rebuild it with `<div>` and CSS, it isn't this style.

## Best for

- Fashion / cultural editorial that needs collected-not-designed energy
- Personal sites, journals, mood boards, fan pages, are.na-style curators
- Music release pages, zine covers, exhibition microsites
- Any subject where the cutout LIBRARY (the things) is the brand — and the chrome should disappear
- Products where "this person made this by hand" is the message

## Pairs well with

- Shells: `shell-scrapbook-substrate`, `shell-masonry`, `shell-editorial-broken-grid`, `shell-infinite-canvas`, `shell-canvas-floating`, `shell-centered-column`
- Aesthetics: `aesthetic-y2k-myspace`, `aesthetic-cluttercore`, `aesthetic-cottagecore`, `aesthetic-cottagegoth`, `aesthetic-dark-academia`, `aesthetic-fairycore`, `aesthetic-goblincore`, `aesthetic-dreamcore`, `aesthetic-angelcore`, `aesthetic-coastal-grandmother`, `aesthetic-curly-girly`, `aesthetic-acid-graphics`

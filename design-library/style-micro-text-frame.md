---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: style-micro-text-frame-ui.png
    reason: Style surface UI mockup.
  - src: style-micro-text-frame-isolated.png
    reason: Signature surface, isolated.
---
# Micro-text frame (style)

**Tag:** `style-micro-text-frame`

**Canonical references:** Japanese kids/service brand sites (SVG textPath rings circulating hero-card borders) · zine archive sites with marquee ribbons crossing section boundaries · recruit-site mirrored slogan double-bands · security-print micro-lettering on banknotes (the physical referent)

## Surface treatment

Tiny typography as BORDER AND FRAME: micro-text travels continuously around a
card's rounded-rect edge via SVG `textPath`, marquee ribbons of small repeated
words run along section boundaries (sometimes rotated, sometimes mirrored with
`scaleY(-1)` into a reflected double-band), and short label loops ring
circular badges. The page's edges and seams become animated typography while
the content inside stays still. Distinct from `style-outline-marquee`: that
style is display-size type AS the wallpaper; this one is caption-size type AS
the chrome - frames, borders, dividers.

### The grammar

- ONE hero element may wear a full circulating border (the most expensive
  gesture - never two on screen)
- Section seams take straight ribbon loops: 10-14px repeated phrase +
  separator glyph (`•`, `/`, `→`), duplicated for seamless wrap
- The circulating text is REAL words doing light labeling work - a tagline,
  a date, a section name - looping; lorem or random glyphs void the device
- Rotated variants run up page margins; mirrored double-bands sit at hero
  bottoms
- Speed is ambient: 20-60s per loop, linear, no easing; pauses on hover when
  the text is a link

### Background / color

- The micro-text takes the page's ink at 60-100%, or the accent when the frame
  IS the brand moment; the framed surface underneath stays calm (flat fill or
  soft tint)
- Works on any register's palette - the style is structural, not chromatic;
  one accent rule still applies

### Type stack

- A clean grotesque or mono at 9-14px, letter-spaced +2-6%; caps or small-caps
  read best in motion
- Counts as the page's micro-register: pairs with one normal heading face;
  it must NOT compete with another micro-system (agate tables, dense captions)

### Motion

`<textPath>` with `startOffset` animated 0→100% (SVG SMIL or rAF) for curved
paths; `transform: translateX` keyframe loops for straight ribbons (content
duplicated 2×, animate -50%); `animation-play-state: paused` on hover for
interactive frames. `prefers-reduced-motion`: frames render static - the
micro-text stays as a printed border.

## Failure mode

Marquee speeds (this is drift, not a news ticker); more than one circulating
border per viewport; micro-text carrying load-bearing information (it's
ambient labeling - anything the user must read sits still); ribbons at every
single seam (two or three per page; at every seam it becomes wrapping paper);
fonts below 9px rendered size (decorative or not, it must remain legible at a
lean-in).

## Best for

Kids/education service brands, campaign one-pagers, recruit sites, event
identities, zine archives - pages that want continuous gentle energy at the
edges while content stays readable; any brief that says "alive but not busy."

## Pairs well with

- Shells: `shell-hero-stack` (the canonical host - inset hero card with a circulating border), `shell-editorial-broken-grid`
- Styles: `style-flat-design` (host surface), `style-bold-display`, `style-doodle`
- Aesthetics: `aesthetic-positivity-kawaii`, `aesthetic-jp-recruit-pop`, `aesthetic-pastel-pop-fmcg`, `aesthetic-zine-type-wall`

---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-zine-type-wall-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-zine-type-wall-isolated.png
    reason: Signature motif, isolated.
---
# Zine type wall (aesthetic)

**Tag:** `aesthetic-zine-type-wall`

**Canonical references:**
- nippori.lamm.tokyo (日暮里ゼミナール) - the complete register: a
  full-viewport hero that is nothing but colliding type blocks (vertical
  columns interleaved with giant horizontal display), marker-framed "episode
  posters" stacked down the page, candy-solid zine colors on a monochrome field
- Japanese flyer/handbill (チラシ) maximal-typography lineage - street-posted
  event bills where density IS the appeal
- Photocopied fanzine paste-up: type set at war, one staple away from falling
  apart, but rigorously art-directed underneath

**NOT to be confused with:** `aesthetic-japanese-poster-layout` (photo-dominant,
quiet, gallery register - this is its loud type-dominant inversion) or
`aesthetic-y2k-memphis-loud` (sticker/chrome-era Western maximalism - the zine
wall is print-born, ink-on-paper, no gloss).

## Cultural identity

Typography as CROWD: the hero is a wall of text blocks at violently different
scales and orientations - viewport-width numerals against 11px captions,
columns running vertical against horizontal slogans - composed so the collision
itself is the image. No photography needed above the fold; the words are the
crowd scene. Below it, content arrives as a scroll-through stack of one-off
"posters," each framed by a thick hand-drawn marker outline in a dedicated
candy color.

The underlying discipline is real: a monochrome ink-on-paper field
(black/white) carries everything; the candy solids live ONLY in frames, tags,
and fills. It reads as chaos and navigates like a system.

Language-agnostic core: **orthogonal type collision + extreme scale contrast +
per-item hand-drawn framing** - any script supplies the wall; mixing two
scripts (or one script + numerals) heightens the orthogonal tension.

## Palette anchor

- Field: paper white `#FFFFFF`/`#FCFCFC` + ink black `#000`, full-strength,
  alternating in full-bleed bands (fixed UI survives via
  `mix-blend-mode: difference`)
- Candy zine solids for frames/tags: cobalt `#4F6D9F`, mint `#60C1A9`, pink
  `#F890CD`, teal `#74CFD4`, chartreuse `#C1D746`, orange `#F2A167` - several
  may coexist, but each ITEM gets exactly one
- Pastel card tints (`#FBE5F2`, `#EAF4E0`, …) for index grids
- Stroke grey `#959595` for secondary marker work

## Composition principles

1. **The type wall hero:** 15-40 text blocks tiling the full viewport -
   mixed orientations (vertical columns × horizontal display), mixed scales
   (8-12vw display against 11px metadata), tight margins, zero images. It must
   read as a printed handbill at every zoom level.
2. **Extreme scale contrast as hierarchy:** the ratio between largest and
   smallest type on screen is 20:1 or more; size does ALL the ranking work.
3. **One-off marker frames per item** (`material-marker-stroke-frame`): each
   featured entry gets a unique outline silhouette + dedicated color -
   scannability by shape.
4. **Marquee ribbons crossing seams:** repeating micro-text strips
   (`style-micro-text-frame`) rotated/mirrored across section boundaries.
5. **Strict index after the chaos:** the archive/list section snaps to a
   rigorous colored grid - the genre's tell that the chaos was authored.
6. **Numbers as decoration:** issue numbers, episode counts, dates at display
   scale (#26, #87) - the zine's love of enumeration.

## Voice register

Enthusiast-editorial: headline slogans declarative and a touch breathless;
metadata everywhere (numbers, dates, durations, tags); captions in plain
reporting voice. Bilingual/biscript welcomed - the second script is another
texture in the wall.

## Raster requirement

None required for the wall itself (it IS type) - but the marker frames want
hand-drawn SVG paths, and episode/item thumbnails (when present) should be
flat-color-treated or grayscale so they join the print register rather than
floating photographic above it.

## Failure mode

First tell: the wall built from ONE typeface at ONE size repeated - the
collision needs scale + orientation + weight variety (though 2-3 families
suffice; it's not ransom-glyph-mix). Second tell: candy colors flooding
section backgrounds (solids belong to frames/tags; the FIELD stays
black-and-white). Third tell: identical frame shapes on every item. Fourth
tell: gradients, shadows, gloss anywhere - this aesthetic is flat ink. Fifth
tell: a photographic hero above the type wall - the words are the hero, or
it's a different genre.

## Best for

- Podcast/episode archives, event series, festival programs
- Independent media, culture magazines, radio/label sites
- Community/club pages with heavy enumeration (issues, episodes, sessions)
- Any brief that says "alive, dense, DIY-but-sharp"

## Pairs well with

- **Shells:** `shell-editorial-broken-grid` (canonical), `shell-masonry` (index sections)
- **Styles:** `style-bold-display` + `style-oversized-neo-grotesque` (display layer), `style-outline-marquee`, `style-micro-text-frame`, `style-doodle` (frame layer)
- **Motion:** `motion-cursor-character` (native - velocity cursor + image trail), `motion-ambient-loop-atmosphere` (floating deco)
- **Materials:** `material-marker-stroke-frame` (native), `material-risograph` / `material-silkscreen` (print finish on thumbnails)

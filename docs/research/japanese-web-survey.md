# Japanese-inspired web design survey → design-library candidates

19 contemporary Japanese sites browsed and classified against the design-library taxonomy
(shell / style / aesthetic / motion / material / recipe). Goal: extract **language-agnostic**
patterns — compositional, structural, motion, and material devices that work in any script —
and group the uncovered ones into proposed new library entries.

Method note: each site's HTML, CSS, and JS bundles were fetched and read (GSAP/Lenis/three.js
configs, keyframes, shader uniforms, font stacks, palette hexes); where JS-rendering or
geo-blocks prevented full rendering, Wayback snapshots and award-gallery coverage
(Awwwards/CSSDA) corroborated. Confidence per site is noted inline.

---

## 1 · Per-site classification

| Site | Genre | Shell (closest) | Style (closest) | Aesthetic (closest) | Recipe (closest) | Confidence |
|---|---|---|---|---|---|---|
| ogud.co.jp/urbanex/next21 | Real-estate concept LP | hero-stack (close) | doodle + kinetic-line-accents | **gap** — "craft sketchbook" | **gap** | high (code) |
| muscatgroup.co.jp | Brand-production corp | hero-stack (exact) | pixel-dissolve + bold-display | monochrome-pop-poster | neo-grotesque-portfolio | high |
| polaris-toyota.jp | Kids day-service brand | hero-stack (close, inset card) | flat-design (sticker-pill twist) | positivity-kawaii (exact) | **gap** | high |
| nippori.lamm.tokyo | Podcast archive zine | editorial-broken-grid (exact) | bold-display + oversized-neo-grotesque + doodle + outline-marquee | **gap** — zine maximal-editorial | editorial-magazine (close) | high |
| maikasui.com | Luxury hand-care DTC | scroll-journey-scene (close) | restrained-hairline | sculptural-minimal | warm-restraint | med-high |
| milez.jp | Craft-culture archive | canvas-floating (close) | **gap** — dark multi-serif editorial | luxury-cinematic-dark | editorial-magazine | medium |
| 2026.qlip.co.jp | Agency New-Year microsite | hero-stack (close) | oversized-neo-grotesque (exact) | monochrome-pop-poster | neo-grotesque-portfolio | high |
| daimaru-matsuzakaya.com/vi | Generative-VI explainer | scroll-journey-scene (exact) | restrained-hairline | sculptural-minimal | **gap** — VI explainer film | high |
| nekozenworld.jp | Cat-brand manifesto | hero-stack (close) | bold-display + cream-humanist | positivity-kawaii (close) | warm-restraint (close) | med-high |
| kokuyo.com curiosity-is-life | 120th-anniv. WebGL book | scroll-journey-scene (exact) | restrained-hairline | sculptural-minimal × kawaii | object-stage-hero (stretched) | high |
| kai-group.com/global/design | Blade-maker design dept | scroll-journey-scene (close) | restrained-hairline (exact) | japanese-poster-layout (close, gothic-clinical) | swiss-grid (half) | high |
| wpups.jp | WP-agency service LP | hero-stack (exact) | flat-design + doodle | positivity-kawaii | **gap** | high |
| komeinc.com | Creative agency portfolio | hero-stack (close) | oversized display but **condensed serif** | japanese-poster-layout (close) | neo-grotesque-portfolio | high |
| daishin-s.co.jp | Engineering corp/recruit | hero-stack (close) | flat-design + aurorism | **gap** — JP recruit-pop | **gap** | high |
| biccamera.com bicidea | Retail PB promo | hero-stack (close) | bold-display + raster-cutout | pastel-pop-fmcg (close) | object-stage-hero (hero only) | medium (Wayback) |
| recruit.sanso-gifu.jp | Construction recruiting | hero-stack (close) | outline-marquee (exact) + bold-display | **gap** — JP recruit-pop | **gap** | high |
| toootegram.tote.co.jp | Playable music toy | canvas-floating (close, but NO scroll) | flat-design (all chrome = sprites) | positivity-kawaii (exact) | **gap** — playable toy site | high |
| taikisato.com | Art-director portfolio | hero-stack (close) | restrained-hairline; **gap** serif-on-dark | japanese-poster-layout × luxury-cinematic-dark | **gap** — Mincho portfolio | high |
| gyre-omotesando.com shibuya | Exhibition microsite | scroll-journey-scene (close) | restrained-hairline + pixel-dissolve; **gap** ransom-glyph | monochrome-tech-editorial | **gap** — exhibition microsite | high-med |

Coverage read: existing shells hold up (hero-stack and scroll-journey-scene absorb 17/19).
The gaps cluster overwhelmingly in **motion**, **material**, **aesthetic registers**, and
**recipes** — plus one entirely missing dimension: **audio**.

---

## 2 · Grouped findings (the actual Japanese-web vernacular, language-agnostic)

### Group A — Threshold rituals (entering the site is a designed moment)
Seen on: milez (On/Sound/Off three-column gate), kokuyo ("turn your sound on" screen),
maikasui (codec-gated preloader ceremony), sanso-gifu (10s skippable Lottie title film with
SKIP chip), muscat (%-counter preloader). The pattern: the site withholds itself until the
visitor makes a choice or watches a title sequence — a TV-commercial / theatre mental model.
Fully language-agnostic (the device is the gate, not the words).

### Group B — Hand-made mark as system (not decoration)
Seen on: ogud (every headline, nav label, and full scene illustration is a hand-drawn SVG that
draws itself stroke-by-stroke on scroll), nippori (each list item gets a one-off thick marker
outline — blob / burst / parallelogram — in a dedicated color), wpups (radial crayon draw-on
via conic clip-path; 5-frame "boil" sprite wobble on drawn edges). Distinct from style-doodle:
doodle is a skin; this is hand-made marks as *entrance grammar and containment system*.

### Group C — Per-glyph typographic play
Seen on: qlip (giant numerals/ideographs woven from a lattice of a single micro-pictogram,
particle-morphed between slides), gyre (ransom-note headlines — each character set in a
different clashing face: ultra-bold / outline / pixel / calligraphic / hand-drawn, with
slot-machine roulette shuffle), toootegram (anamorphic 3D type that resolves only at one
camera angle), nippori (typographic-wall hero: a full-viewport collage of colliding vertical
and horizontal type blocks, no photography). The unit of design is the glyph, not the line.
Works in any script — the device is per-glyph alternation/construction.

### Group D — Two-axis / two-register type systems
Seen on: daishin + sanso (bilingual eyebrow: small condensed label-register line OVER the large
main heading, treated as one component), komeinc (tiny vertical-rl accent-color micro-labels
pinned to section corners as wayfinding), polaris (vertical tagline as stacked sticker pills,
lead glyph per column in a different brand color), kai + taikisato + milez (vertical writing
used surgically — captions/labels only, never the organizing axis). Language-agnostic form:
a **secondary micro-register axis** (rotated/vertical/eyebrow) orbiting the primary heading.

### Group E — Paper as a world, not a texture
Seen on: daimaru (photoreal die-cut colored-paper strata with apertures, cut-edge highlights,
inter-layer shadows — custom GLSL; scroll dives *through the holes*), kokuyo (pop-up-book 3D:
hinged paper constructions that fold open; page-flip as scene transition), ogud (full-bleed
video `mix-blend-mode: multiply` over woven-paper texture — motion footage reads as printed on
the substrate). Library paper materials are 2D surfaces; these are paper *constructions*.

### Group F — Interaction as meaning (the device carries the message)
Seen on: daimaru (tap regenerates the generative brand emblem — "different each time you see
it"), maikasui (page state bound to real wall-clock time in a reference timezone; draggable
day-timeline as primary nav), toootegram (touching/rotating objects toggles audio stems — the
page is an instrument), taikisato (whole-page dark→light theme inversion at one scroll
threshold), gyre (image planes hop along random Manhattan grid paths — "the city block
reshuffling"). These aren't polish; they ARE the concept.

### Group G — Pop chrome devices (the JP-commercial vernacular)
Seen on: polaris (SVG textPath micro-text continuously circulating the hero card's rounded
border), nippori + sanso + daishin (marquee ribbons; sanso mirrors one with scaleY(-1)),
biccamera (walls/bands of 30+ repeated identical icons/arrows as animated section dividers),
muscat (pixel-confetti field over monochrome photography; 5×5 image-tile grid whose cells
march around the perimeter like a conveyor ring), wpups (day↔night scenic section banding),
nekozen (one accent hue per chapter from a named feeling↔color legend; 30vw display glyphs as
section wallpaper). High-energy, flat, textureless — the opposite pole from Group E.

### Group H — Audio (a missing taxonomy dimension)
Seen on: kokuyo (per-scene musical beds + foley on hover/click/check/page-flip), toootegram
(17 additive mp3 stems as interaction feedback + timer/score), milez + maikasui (scored
ambience with consent gates). The library currently has zero audio vocabulary.

### Group I — Expressive cursors
Seen on: nippori (cursor rotates to motion angle, squashes/stretches with velocity; spawns a
decaying trail of thumbnail images over the hero), toootegram (cursor replaced by character
sprites — cursor identity changes with selected subject), biccamera + kai (custom cursor with
contextual states, magnetic scale/fade). No entry covers cursor-as-subject.

---

## 3 · Proposed new entries

> **Status (2026-06-12):** all 11 Tier-1 entries below are AUTHORED in
> `design-library/` (indexes rebuilt, PROTOTYPE.md menus + primers updated),
> plus two Tier-2 aesthetics promoted to keep their pairings valid:
> `aesthetic-craft-sketchbook` and `aesthetic-zine-type-wall`. Sample PNGs
> still need an image_gen pass. The remaining Tier-2 entries and the Tier-3
> audio family are open.

### Tier 1 — multi-site corroborated, write first

| Proposed tag | Type | Spec (one line) | Sources |
|---|---|---|---|
| `motion-svg-self-draw` | motion | Hand-made SVG lettering/illustration draws itself stroke-by-stroke on scroll entry (stroke-dashoffset 0→100% then fill swap) — entrance grammar for an entire page's chrome | ogud, wpups |
| `motion-threshold-ritual` | motion | Entry gate as composition: sound-consent choice, %-counter ceremony, or skippable title film with SKIP chip that seeks the timeline and re-syncs load states | milez, kokuyo, maikasui, sanso, muscat |
| `material-paper-construction` | material | Paper as built volume: die-cut layered strata with apertures + inter-layer shadows; hinged pop-up folds; page-flip transitions; cut-edge highlights (GLSL or layered raster) | daimaru, kokuyo |
| `material-marker-stroke-frame` | material | One-off thick hand-drawn marker/crayon outlines (blob/burst/polygon) as per-item containment frames + radial draw-on reveal + frame-flip "boil" wobble | nippori, wpups |
| `style-ransom-glyph-mix` | style | Per-character typeface alternation as emphasis: each glyph of a headline set in a deliberately clashing face (ultra-bold/outline/pixel/calligraphic/hand-drawn), optional roulette shuffle before settling | gyre, (qlip cousin) |
| `style-micro-text-frame` | style | Animated micro-typography as border/frame: textPath circulating a card's edge, marquee ribbons crossing section boundaries, mirrored stroked-text double-bands | polaris, nippori, sanso, daishin |
| `style-two-register-heading` | style | Heading as a typed pair: condensed micro-eyebrow label over the large main line, plus rotated/vertical micro-labels in accent color as persistent corner wayfinding | daishin, sanso, komeinc, kai |
| `motion-cursor-character` | motion | Cursor as expressive subject: velocity squash-stretch + rotation-to-heading, contextual identity swaps, decaying image trails spawned along the pointer path | nippori, toootegram, biccamera |
| `aesthetic-jp-recruit-pop` | aesthetic | The contemporary JP corporate/recruit vernacular: white ground + 2 signal accents, bilingual eyebrow headings, marquee slogan loops, stats band, interview storytelling, pill radius tokens — energetic but systematized | daishin, sanso, polaris, biccamera |
| `recipe-jp-corporate-recruit` | recipe | Full bundle for the above: hero film/slideshow → about → "company in numbers" stat band → interview carousel → business slider → jobs/FAQ → dual entry CTAs | daishin, sanso |
| `recipe-brand-story-journey` | recipe | Brand-identity/anniversary explainer as fixed-viewport scroll film: chaptered WebGL scenes, breadcrumb "Element N : Name," narration set inside the scene's negative space, optional score | daimaru, kokuyo |

### Tier 2 — single-site but high-value, distinctive

| Proposed tag | Type | Spec | Source |
|---|---|---|---|
| `motion-glyph-lattice-morph` | motion | Display glyphs constructed from a dense lattice of one meaningful micro-pictogram, particle-morphed between states | qlip |
| `motion-clock-synced-scene` | motion | Page state (scene/palette/copy) bound to real wall-clock time in a reference timezone, live clock as UI, scrubbable override timeline | maikasui |
| `motion-tap-regenerate` | motion | Pointer tap recomposes a live generative emblem/artwork — never the same twice | daimaru |
| `motion-theme-inversion-threshold` | motion | Whole-page light↔dark register flip keyed to one scroll boundary; persistent UI re-skins in counter-color | taikisato |
| `motion-reversible-vector-slider` | motion | Carousel arrows scrub vector animations forward/backward (reverse playback on prev) instead of swapping slides | sanso |
| `motion-scroll-velocity-lag` | motion | Per-element elastic translateY lag driven by a frame-updated CSS variable — layout breathes against scroll | kai |
| `motion-grid-walk-planes` | motion | Media planes relocate in discrete orthogonal grid steps of random length inside sticky sections | gyre |
| `motion-perimeter-conveyor` | motion | Image-tile grid whose cells march around the outer ring positions like a conveyor | muscat |
| `motion-anamorphic-reveal` | motion | Fragmented 3D geometry resolves into a legible figure/letterform only at one camera angle the user must find | toootegram |
| `material-substrate-blend-media` | material | Full-bleed video/imagery mix-blend-multiplied into a paper/fabric texture so motion footage reads as printed on the substrate | ogud |
| `material-particle-mist` | material | Subject dissolved into a mouse-reactive noise-displaced point cloud — particles as surface | kai |
| `material-mosaic-finish` | material | Mouse-reactive mosaic/pixelation shader as a standing surface finish on photos and video (resolves/degrades with proximity) | gyre |
| `style-drafting-instrument-chrome` | style | Measurement furniture as editorial decoration: numbered rulers, 4-corner registration brackets, gray marker-swipe highlight boxes | gyre, kai |
| `style-sticker-pill-tategaki` | style | Headline broken into stacked rounded pills along the secondary (vertical/rotated) axis, lead glyph per column in a different brand color | polaris |
| `shell-toy-stage` | shell | No-scroll single-screen stage: one fixed full-viewport canvas + corner-anchored overlay clusters (nav rail, drawer, toggle, timer); the page is an instrument/toy, not a document | toootegram |
| `aesthetic-craft-sketchbook` | aesthetic | Pencil-on-warm-paper register: entire chrome hand-lettered/hand-drawn, woven-paper ground, one vivid accent, self-drawing entrances | ogud |
| `aesthetic-zine-type-wall` | aesthetic | Type-dominant maximal editorial: full-viewport collage hero of colliding vertical+horizontal type blocks, candy-solid zine frames, monochrome field | nippori |
| `recipe-exhibition-microsite` | recipe | KV + long-form curatorial dialogue + artist accordion roster + visit-info table, shader-treated imagery, hairline chassis | gyre |
| `recipe-playable-toy-site` | recipe | Game-like single-screen experience: drag-physics subjects, score/timer overlay, audio-stem feedback, sprite-baked chrome | toootegram |

### Tier 3 — new dimension to consider

**Audio (`audio-*` or `sound-*` family).** Three sites treat sound as a first-class layer the
taxonomy cannot express: per-scene musical beds, interaction foley (hover/click/page-flip),
additive instrument stems as interaction feedback, and consent-gated ambience. Candidate
starter entries: `audio-foley-ui`, `audio-scene-score`, `audio-stem-toy`, plus the consent
gate already covered by `motion-threshold-ritual`.

---

## 4 · Language-agnostic translation notes

- **Vertical writing** is never the organizing axis on these sites — it appears as a surgical
  accent (captions, micro-labels, one tagline), often conditionally (`html[lang=ja]` only).
  The portable abstraction is *a secondary rotated/vertical micro-register*, not "vertical text."
- **Bilingual pairing** (EN eyebrow + JP heading) generalizes to *two-register heading pairs*:
  any label-script/display-script combination works (e.g. condensed caps label + serif display).
- **Mincho × condensed-sans** (already in `aesthetic-japanese-poster-layout`) generalizes to
  high-contrast-serif × condensed-grotesque pairing; komeinc shows the condensed-*serif*
  display variant (FreightBig Compressed) the style list doesn't cover.
- **Kanji-lattice type** (qlip) generalizes to "display glyphs woven from a repeated meaningful
  pictogram" — the unit can be any motif (logo mark, product silhouette, zodiac animal).
- The cliché-Japan traps listed in `aesthetic-japanese-poster-layout` (sakura, brush strokes,
  kanji-as-decoration) were absent from ALL 19 real Japanese sites — confirming that entry's
  forbidden list. The actual vernacular is: threshold rituals, hand-made mark systems,
  per-glyph play, paper constructions, pop chrome, and interaction-as-meaning.

---

## 5 · Existing entries validated (no action needed)

`shell-hero-stack`, `shell-scroll-journey-scene` (dominant high-craft JP pattern: fixed
viewport, scrollHeight ≈ 900, wheel as hijacked input), `shell-editorial-broken-grid`,
`style-restrained-hairline`, `style-oversized-neo-grotesque`, `style-outline-marquee`,
`style-pixel-dissolve`, `aesthetic-positivity-kawaii`, `aesthetic-monochrome-pop-poster`,
`motion-scroll-sequence-frames` (taikisato's 133-frame moon scrub is a textbook case),
`motion-scroll-pinned-transform`, `motion-stylize-shader-pass`, `motion-scene-zoom-through`
(daimaru's dive-through-the-aperture is the canonical demo), `motion-background-swap-fixed-ui`,
`motion-match-cut-morph` (GSAP Flip thumbnail→fullscreen on ogud).

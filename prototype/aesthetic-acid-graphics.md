---
# Sample-image references for the System-tab design library. Images sit
# next to this file in prototype/ and were generated via image_gen.
images:
  - src: aesthetic-acid-graphics-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-acid-graphics-isolated.png
    reason: Signature motif, isolated.
---
# Acid Graphics (aesthetic)

**Tag:** Acid Graphics / Acid Design — David Rudnick, Jonathan Castro / Boiler Room, Heaven by Marc Jacobs, Nina Protocol, AIGA Eye on Design "Acid Graphics"

**Canonical references:**
- **David Rudnick** — OPN sleeves and warped-Arial type that codified the move
- **Jonathan Castro / Boiler Room** — chrome wordmarks and rave-flyer maximalism
- **Heaven by Marc Jacobs** — subcultural fashion drops adopting the language commercially
- **Nina Protocol** — independent music platform built end-to-end in the aesthetic
- **AIGA Eye on Design "Acid Graphics"** — the explainer that named the movement

## Cultural identity

Acid Graphics is the post-2018 graphic-design language of the underground electronic-music scene — a deliberate refusal of clean Helvetica-on-white SaaS in favour of something that reads as **belonging** to people who go to warehouse parties and read footnotes on Discogs. It descends from 1988 rave-flyer culture (Boy's Own, Helter Skelter, the original acid-house smiley) but is reanimated by a generation that grew up on Photoshop chrome, Russian-constructivist asymmetry, and the Boiler Room visual identity. It is record-sleeve thinking applied to digital surfaces — the audience reads a chrome wordmark + 1988 smiley as **in-group signal**, not as cosplay. It peaks in club / festival promo, label sites, fashion drops aimed at subcultural Gen-Z, and zines; it dies the moment it tries to sell a B2B SaaS.

## Palette anchor

High-chroma rave neons on **pure black** — the "colourful black" `#000000` that makes neons read as fluorescent, never `#0A0A0A` or charcoal. Anchor colours:

- Acid green `oklch(88% 0.30 135)` — the 1988-smiley signal
- Hot magenta `oklch(65% 0.32 340)`
- Electric cyan `oklch(82% 0.20 215)`
- Hazard yellow `oklch(92% 0.22 100)`
- Blood red `oklch(55% 0.28 25)`

Pick **two clashing accents max** per composition — the rest of the chroma comes from the chrome gradient. Off-white `#EDEDED` for foreground type, never pure `#FFF` (pure white reads Y2K, not acid).

## Decoration motifs

- **One warped chrome wordmark** as the hero — Arial Bold Italic stretched + skewed, OR a custom display face (Migra, PP Mondwest, Dinamo Whyte Inktrap), with a layered silver→navy→silver gradient as `background-clip: text`
- **One wireframe 3D object** floating off-grid — globe, torus, coil, molecule, drawn as 0.5px line art in an accent colour, on a slow continuous rotation
- **The flat-vector 1988 acid-house smiley** in `#FFD700` on black (drawn as SVG, never the unicode 🙂 emoji)
- **Tribal / Op-Art curls** as SVG paths — never a stock pattern fill
- **Catalogue codes and agate metadata** as decoration in their own right — `LA047 / 12" / 2024`, `side a · 138 bpm`
- **Marquee / ticker strips** at the foot of the page
- **Raster captures** of melting chrome distortion, neon-glow-on-black photography, scanned flyer textures — pure CSS reads as "web-2.0 dark with neon accents," not acid

## Voice register

Cynical-knowing, lowercase-defiant, catalogue-coded. Microcopy reads like the back of a 12" sleeve: `LA047 / 12" / 2024`, `side a · 138 bpm`, `pre-order ships august`, `void where prohibited`, `mastered at the exchange`. Never benefit-led marketing copy. Never `Get started →`. Never a sentence that ends in an em-dash to sound thoughtful — that is corporate-Aesop, not acid.

## Failure mode

Stock chrome-gradient `linear-gradient(silver → cyan)` dropped on `#000` as the **only** acid move, plus a free "blackletter acid" Google Font on every heading, plus the unicode 🙂 emoji instead of the flat 1988 smiley, plus raw `#00ff00 / #ff00ff` named-colours with no chroma curve, plus Inter at 14px body, plus a rounded-8px card sitting under the chrome word — "AI dressed a SaaS landing in chrome." Second failure: **warping every element simultaneously** so nothing reads. The canonical flyers warp **one** thing per composition and keep everything else typographically quiet.

## Best for

Independent electronic-music labels · club and festival promo · fashion drops aimed at subcultural Gen-Z · music-publishing platforms (Nina, Bandcamp-adjacent) · zines · archive shops · mixtape and radio-show sites · anything where the audience treats chrome + smiley as **in-group belonging** rather than as cheap edge.

## Pairs well with

- **Shells:** `shell-editorial-broken-grid` (default — overlapping misaligned modules), `shell-hero-stack` (single warped wordmark + tracklist), `shell-scrapbook-substrate` (layered ephemera), `shell-canvas-floating` (wireframe object + floating catalogue panels)
- **Styles:** `style-raster-cutout` (when chrome captures and flyer scans carry the look), `style-oversized-neo-grotesque` (for the warped-Arial hero treatment), `style-brutalist-raw` (for the catalogue-table substrate underneath), `style-terminal-mono` (for the OCR-A/Berkeley Mono catalogue codes)

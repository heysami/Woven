---
# Sample-image references for the System-tab design library. Images sit
# next to this file in prototype/ and were generated via image_gen.
images:
  - src: aesthetic-frutiger-four-colors-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-frutiger-four-colors-isolated.png
    reason: Signature motif, isolated.
---
# Frutiger Four Colors (aesthetic)

**Tag:** `aesthetic`

**Canonical references:**
- Apple iPod Silhouette ads 2003-08 — the urtext: one block colour, one black dancer, one white iPod
- Nintendo Wii / Wii Sports box 2006 — the four-colour grid applied to mass-market consumer goods
- Gorillaz *Demon Days* 2005 — pop-art figures isolated on saturated single-hue fields
- iPod Nano 2g hardware colorways 2006 — the palette as physical product, not just print
- Fujifilm FinePix Z20fd 2008 — late-era consumer electronics borrowing the same look

## Cultural identity

The mid-2000s Apple-led pop optimism. Music had just gone portable and personal, MP3 players were status objects, and the dominant cultural image was a faceless silhouette dancing alone with white earbuds — democratic, joyful, anonymous. The aesthetic flattens identity (everyone is a black silhouette) and elevates the product (the only thing rendered in white) against a wall of confident single-hue colour. It is pre-iPhone, pre-social, pre-irony: the last moment when a consumer device was sold as pure dopamine.

Where Frutiger Aero (the sibling) is wet-glass and biophilia, Four Colors is dry-flat and human-gesture. Where Corporate Memphis is communal blob-people, Four Colors is one person, alone, with one device. The mood is energetic, declarative, and slightly anonymous in a way that reads as freedom rather than alienation.

## Palette anchor

Four saturated hues, used one-per-panel, never blended:

- `#A0CB3B` electric lime
- `#0094E1` sky blue
- `#EC5298` hot pink
- `#FAB71F` neon orange

Plus pure `#000` for silhouettes and pure `#FFFFFF` for the product. Greys are forbidden — if you reach for grey you have already lost the aesthetic.

## Decoration motifs

- **High-contrast silhouettes** — pure-black flat figures, mid-gesture (dancing, listening, jumping). Never 3D-shaded, never photographic.
- **The white earbud cord** — a gestural curve drawn as a 2-3px white stroke, often the only "line" in the composition.
- **The floating white product** — iPod, controller, can, phone — rendered as a pure-white silhouette of the device itself, hovering free of any card or container.
- **Hard-edged colour blocks** — when more than one hue appears, they sit in a rigid 2x2 or 1x4 grid with no gradient between cells.
- **One panel = one hue** — the discipline of the aesthetic is restraint of palette per surface.

## Voice register

Imperative, two or three words, declarative period. Lowercase product names beside title-case verbs. "iPod. shuffle." "Play Like A Pro." "1,000 songs in your pocket." Never sentence-case explanations, never feature lists, never "Discover your next favourite…". The product does the explaining; the type does the proclaiming.

## Failure mode

Pastel-shifting the palette into millennial-pink + sage + powder-blue + butter-yellow (that's Corporate Memphis cosplay, not Four Colors) — the hues must stay saturated and slightly garish. Using a 3D-shaded or photographic figure instead of a pure-black flat silhouette. Letting two saturated hues fight on the same panel instead of committing one block per surface. Adding drop-shadows under the silhouette or the colour block (the aesthetic is borderless flat — only the product device gets a faint shadow). Reaching for Inter or Poppins (the era is Myriad Pro / Frutiger). Adding glossy Aqua orbs (that's the parent Frutiger Aero, a different sibling).

## Best for

Music players, dance and fitness apps, single-product launch pages, gaming consoles pitched to non-gamers, headphone brands, anything where the pitch collapses to *one device + one human gesture*. Works for app marketing, hardware reveals, playlist covers, festival lineups. Does not work for dense data, professional tools, or anything that needs more than one idea per screen.

## Pairs well with

- **Shells:** `shell-hero-stack` (one block, one figure, one product per fold — native fit), `shell-mobile-app` (each screen takes one of the four hues), `shell-bento-grid` (the 2x2 colour grid is itself a bento), `shell-centered-column` (single-hue field with floating product), `shell-masonry` (only if every tile commits its own single hue)
- **Styles:** `style-flat-design` (the closest CSS substrate — extend by adding silhouette raster), `style-bold-display` (for the type discipline), `style-oversized-neo-grotesque` (compatible if you swap the typeface for Myriad / Frutiger). Note: this aesthetic requires raster silhouette photography or illustration; CSS alone collapses it into generic Flat Design.

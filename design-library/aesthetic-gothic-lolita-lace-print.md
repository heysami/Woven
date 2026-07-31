---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-gothic-lolita-lace-print-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-gothic-lolita-lace-print-isolated.png
    reason: Signature motif, isolated.
---
# Gothic-lolita lace print (aesthetic)

**Tag:** romantic engraved-print register

**Canonical references:**
- *Gothic & Lolita Bible* (Index Communications, 2001-2017) - the mook that codified the page grammar
- *KERA* magazine and its brand-catalog inserts
- Baby, The Stars Shine Bright / Moi-meme-Moitie catalogs - the frill-catalog layout with garment plates
- Victorian mourning stationery and 19th-century engraved fashion plates - the print ancestry the mooks quote

## Cultural identity

The print register of the gothic-lolita mook: cream paper framed by engraved lace borders in black and blood red, Didone display serifs (Mademoiselle-grade contrast) over etched ribbon banners, and garments drawn as pen-and-ink plates - a black tiered one-piece rendered stroke by stroke like a Victorian fashion engraving. Everything is FURNITURE: ribbon-banner buttons, scalloped card frames, bow and scissor dingbats, a French loanword floating in italic. The mood is romance with a mourning edge - lace as devotion, red as blood, but always tidy, cataloged, and price-tagged (¥24,800), because this is a shopping culture as much as a subculture.

Differentiation: `aesthetic-dark-academia` is the tweed-library register - scholarly, masculine-leaning, coffee and marginalia; no lace, no ribbon, no catalog. This entry is the dressmaker's parlor, not the library. And `aesthetic-angelcore` is heaven-lit softness - glow, feathers, pastel divinity; gothic-lolita lace print is EARTHLY and inked, its light source is a reading lamp on cream stock, its sweetness always bordered in black.

## Palette anchor

Three inks on cream, no more:
- Ink black `oklch(17% 0 0)`
- Blood red `oklch(42% 0.16 25)`
- Cream stock `oklch(96% 0.01 90)`
- Pattern tissue `oklch(92% 0.01 350)`
- Lace black (texture tone) `oklch(22% 0 0)`

Red is the accent ink, used for one banner, one seal, one "New" ribbon per view - never a second red element competing.

## Decoration motifs

- Engraved lace borders occupying page corners and frame edges, black on cream, red for emphasis
- Etched ribbon banners as buttons and section caps ("Shop Now" on a furling ribbon)
- Didone display with an italic secondary line ("Atelier de Mode")
- Pen-and-ink garment plates - clothing drawn as engravings, not photographed flat
- Scalloped and hairline double-rule card frames; bow, scissor, and hanger dingbats
- Wax-seal / rosette badges for state ("New" ribbons, favorite hearts in red)

**Raster required:** the engraved lace borders and the pen-and-ink garment plates (illustration `engraved-lace-frame`, `fashion-plate-etching`). CSS borders cannot fake thread; the etch density is the genre.

## Voice register

Romantic, slightly formal, French-scented: "Romance, Lace, Ribbon", "Atelier de Mode", "Mix, layer, and make it your own." Item names are precise catalog nouns (Lace Tiered One-piece, Frill Blouse). Never slangy, never loud, never minimalist-cold - the voice curtsies.

## Failure mode

Swapping the engraved lace for a repeating CSS damask tile = goth restaurant menu, not lolita mook; the lace must read as drawn thread. Second tell: black-on-black gloom - the ground is CREAM; darkness is carried by ink density, not by a dark theme. Third tell: photographing garments as e-commerce flat-lays; the genre draws its clothes as plates. Fourth tell: more than three inks - one pastel gradient and the mourning romance collapses into generic cute.

## Best for

- Fashion brands in the lolita / romantic / vintage lane, indie dressmakers
- Stationery, tea, and confectionery brands with Victorian leanings
- Event pages for subculture markets, doll and craft communities
- Any brief asking for "romantic gothic" that must stay elegant, not spooky

## Pairs well with

- Shells: `shell-centered-column`, `shell-hero-stack`, `shell-editorial-broken-grid`
- Styles: `style-serif-warm-paper`, `style-editorial-italic-accent`, `style-restrained-hairline`

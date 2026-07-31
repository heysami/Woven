---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-angura-silkscreen-poster-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-angura-silkscreen-poster-isolated.png
    reason: Signature motif, isolated.
---
# Angura silkscreen poster (aesthetic)

**Tag:** underground-theatre ink clash

**Canonical references:**
- Tadanori Yokoo's theatre posters (1965 onward) - the sunburst rays, flat clashing inks, and collaged faces that define the genre
- Shuji Terayama's Tenjo Sajiki company and Kara Juro's Situation Theatre - the angura (underground) troupes the posters served
- Kiyoshi Awazu and Akira Uno - the parallel poster lineages of the same movement
- 1960s Shinjuku street-poster culture - wheat-pasted, silkscreened, cash-only

## Cultural identity

The poster voice of Japan's 1960s underground theatre: silkscreened sheets in deliberately CLASHING flat spot inks - vermilion against jade against cadmium yellow - with hand-slashed dry-brush lettering for the troupe name, halftone-screened photographic faces of the cast, a sunburst ray field radiating from the center, and the business end handled by ticket-stub borders running dates and prices around the entire edge like perforated currency. Everything is flat, registration is imperfect on purpose, and the paper shows through. It is carnival urgency with a printing-press budget: loud because the show is Friday and the rent is due.

Differentiation: `aesthetic-japanese-poster-layout` is the OPPOSITE voice from the same country - photographic restraint, implied grids, one accent; angura is ink-clash, hand-lettering, and every edge working. And `material-silkscreen` is the print MATERIAL itself - the flat-ink texture and registration slip as a surface treatment; this entry is the whole compositional and cultural register that happens to be printed that way: sunbursts, cast halftones, stub borders, troupe voice.

## Palette anchor

Three clashing screens plus paper, all flat:
- Vermilion screen `oklch(60% 0.21 30)`
- Jade screen `oklch(52% 0.12 165)`
- Cadmium yellow screen `oklch(85% 0.17 95)`
- Paper white `oklch(96% 0.01 90)`
- Deep jade accent `oklch(40% 0.10 170)`

No gradients, no tints except halftone screens of these same inks. The clash is chosen: red and green at equal weight is correct here and nowhere else in the JP canon.

## Decoration motifs

- Dry-brush slash display lettering, hand-pulled and irregular
- Halftone-screened faces (cast portraits) printed in a single spot ink
- Sunburst / radiating ray fields behind the title block
- Ticket-stub borders: dates and prices in perforated cells running the full page edge
- Starburst seals (ALL SHOWS, CASH ONLY), boxed venue blocks
- Raised-ink texture on flat color panels; deliberate slight misregistration between inks

**Raster required:** the halftone cast faces and the dry-brush lettering (photo-treatment `spot-ink-halftone-portrait`, typography `dry-brush-slash-lockup`). The ray fields and stub borders are SVG; the faces and brush are print artifacts.

## Voice register

Barker-direct: "NEW WORKS. RAW VOICES. NO APOLOGIES." Dates, prices, doors time, venue - the poster is also the box office. Declarative shouts in short lines, troupe manifesto energy. Never corporate, never polite, never vague about when and how much.

## Failure mode

Harmonizing the palette kills it - if the inks agree, it is a nice retro poster, not angura; the vermilion/jade collision is load-bearing. Second tell: smooth vector lettering where the brush should be; the title must look pulled by hand. Third tell: full-color photography - faces enter ONLY as single-ink halftones. Fourth tell: dropping the ticket-stub economy (dates, prices, CASH ONLY); without the box-office furniture it loses the underground-hustle context that separates it from art-print pastiche.

## Best for

- Theatre, live music, and festival promotion; event calendars
- Indie zines, film retrospectives, counterculture brands
- Ticketing UIs that want box-office character
- Any brief asking for "vintage Japan, loud" - the licensed alternative to tired ukiyo-e remixes

## Pairs well with

- Shells: `shell-editorial-broken-grid`, `shell-hero-stack`, `shell-scrapbook-substrate`
- Styles: `style-bold-display`, `style-raster-cutout`, `style-brutalist-raw`

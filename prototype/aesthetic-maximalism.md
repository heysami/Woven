---
# Sample-image references for the System-tab design library. Images sit
# next to this file in prototype/ and were generated via image_gen.
images:
  - src: aesthetic-maximalism-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-maximalism-isolated.png
    reason: Signature motif, isolated.
---
# Maximalism (considered abundance) (aesthetic)

**Tag:** `aesthetic`

**Canonical references:**
- Wes Anderson title cards — centered symmetry, period palette, chapter-card type
- The Gentlewoman — modular asymmetry, warm-neutral editorial restraint inside abundance
- SSENSE Magazine / Eric Hu — bespoke modified-Arial, layered photographic z-order
- Apartamento — period interiors, marginalia, long literary captions
- A24 Civil War / MW® — constructed-world film microsite, single-era palette discipline

## Cultural identity

Maximalism (the *considered* kind, not the chaotic kind) is high-editorial abundance held together by one-period discipline. It descends from the broadsheet, the literary quarterly, the fashion-house archive, and the auteur title card — places where many decorative moves are allowed *because* they all come from the same era, the same vocabulary, the same world. Wes Anderson is the patron saint: every prop, every typeface, every colour swatch from one constructed period. The Gentlewoman is the prose register: warm, literary, third-person, long captions. SSENSE / Eric Hu is the photographic z-order: multiple images overlapping with deliberate intent.

The key tension is *abundance on a grid*. The 12-column architecture stays strict underneath; the abundance happens *inside* the modules. Pick one period (Edwardian, mid-century Anderson, 1990s Comme, Art Deco), commit to its palette, ornament, and typography, and let many decorative moves coexist because they all belong to the same world.

## Palette anchor

Pick ONE era's set and stay there. Saturated but period, never neon.

- **Anderson Grand Budapest** — `#F1BB7B` peach · `#FD6467` coral · `#5B1A18` oxblood · `#E6A0C4` rose · `#7294D4` blue
- **Gentlewoman warm-neutral** — `#EFE9DD` warm white · `#C9A36B` ochre · `#6B4F2A` walnut · `#8B1A1A` claret · `#2B2B2B` ink
- **A24 Civil War night** — `#0D0D0D` black · `#C9362A` flag-red · `#F1E4C6` cream · `#4A6B3A` field-green
- **Edwardian** — Bodoni-friendly cream `#F4ECDB` · damask gold · oxblood · ink

Chroma `0.08–0.16`. One palette per project. Never the Y2K cyan-magenta-lime collision.

## Decoration motifs

- Period pattern wallpaper as low-contrast substrate (toile, Art Deco fans, Victorian damask, Edwardian diaper) — `opacity: 0.10–0.18`
- Multiple photographs overlapping in deliberate z-order — not collaged chaos, composed depth
- Period ornament: fleurons (`❦` `❧`), dingbats (`✦` `§`), drop caps, ornamental section numerals (`i. ii. iii.`)
- Double-rule frames around hero modules — `2px solid` + `1px outline` with `4px offset`
- Marginalia in the outer columns; footnotes with `*` `†` `‡` markers
- Oversized chapter numerals in the display face (`120px+`)
- All decoration sourced from the *one* committed period — Edwardian + Edwardian, never Edwardian + Memphis

## Voice register

Period-coherent, literary, third-person, semi-formal. Long captions are encouraged.

- "A correspondent reports from Nebelsbad, where Mendl's continues to operate as it has since 1897."
- "Concerning the matter of the autumn collection."
- "Volume IV, Number 2. A study in red."

Never marketing-flat ("Shop now!"). Never slangy. Never sentence-fragment hype. The voice should sound like it was set in lead type.

## Failure mode

The cheap version is *chaos pretending to be abundance*. Tells:

- Rainbow palette + four display faces + terrazzo background + rotated stickers + marquee = Y2K cosplay pretending to be maximalist
- A Wes-Anderson title-card composition dropped on a plain white SaaS landing with Inter 14 and a soft drop-shadow = Anderson cosplay with no commitment
- Period ornament `❦` next to Lucide icons and a `border-radius: 999px` "Subscribe" pill — vocabularies from three different worlds
- No visible grid underneath the abundance — chaos, not editorial
- Reaching for lens flare, terrazzo, or Druk Wide hot-pink — that's the *loud* maximalism (Y2K/Memphis), a different aesthetic

If you can't name the *one* period and the *one* grid underneath, you're not doing considered maximalism.

## Best for

- Literary magazines and quarterlies
- Fashion houses with archive depth (Marni, Comme des Garçons, SSENSE editorial)
- Film microsites with a constructed-world conceit (A24, Wes Anderson)
- Restaurants and hotels with a period brand
- Perfume and beauty houses with heritage storytelling
- Cultural-institution exhibition pages
- Cookbook and travel-guide longform

## Raster note

This aesthetic requires real raster: period pattern wallpapers and multiple overlapping photographs in deliberate z-order. Without raster, it collapses to Swiss-grid. Before drawing, follow the raster-requirements decision tree in the main playbook (image-gen MCPs → public-domain archives → project assets → ask user → switch genre rather than fake it in SVG).

## Pairs well with

- **Shells:** `shell-editorial-broken-grid` · `shell-centered-column` · `shell-hero-stack` · `shell-masonry` · `shell-scrapbook-substrate` · `shell-bento-grid`
- **Styles:** `style-serif-warm-paper` · `style-cream-humanist` · `style-oversized-neo-grotesque` · `style-restrained-hairline` · `style-raster-cutout`

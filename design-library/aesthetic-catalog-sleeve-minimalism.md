---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-catalog-sleeve-minimalism-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-catalog-sleeve-minimalism-isolated.png
    reason: Signature motif, isolated.
---
# Catalog sleeve minimalism (aesthetic)

**Tag:** numbered-identity restraint

**Canonical references:**
- Peter Saville's Factory Records sleeves - the FAC catalog-number system as identity
- Joy Division *Unknown Pleasures* (FAC 10) - a found scientific diagram as the entire cover
- New Order *Blue Monday* (FAC 73) - die-cut code, color-block cipher strip, no band name
- OMD and Section 25 sleeves - color-coded wheels and strips carrying meaning wordlessly
- Matte board, etched aluminum and debossed ink as sleeve materials

## Cultural identity

Identity as CATALOG SYSTEM: everything is an entry with a number (FAC 51), set in wide-tracked mono capitals on near-black sleeve board, and the hero image is an engraved technical diagram - a radar plot, a pulsar stack, contour rings - presented without caption or explanation. The only chroma on the page is a color-code strip: a row of small solid swatches that functions as a cipher, repeated on cards, in the nav, on the mobile screen, carrying the release's identity the way a barcode would. The confidence is in what is withheld: no logo lockup, no photography, no persuasion - the catalog speaks.

Where `aesthetic-monochrome-tech-editorial` builds around archival black-and-white PHOTOGRAPHY, catalog sleeve minimalism is diagram-led - its one image is drawn data, not a photo. And where `aesthetic-industrial-catalog` is light-ground spec sheets - utilitarian white pages dense with part tables - this is dark-ground and ceremonial: matte black materiality, one artifact per surface, the sparseness itself the luxury.

## Palette anchor

Grayscale plus a cipher strip.
- Void black `oklch(13% 0 0)`
- Pulse white `oklch(96% 0 0)`
- Industrial gray `oklch(60% 0 0)`
- Strip blue `oklch(48% 0.14 262)`
- Strip teal `oklch(60% 0.10 195)`
- Strip yellow `oklch(83% 0.16 95)`
- Strip red `oklch(55% 0.20 25)`

The strip colors appear ONLY inside the code strip - never as button fills, never as link color, never bleeding into the layout.

## Decoration motifs

- The color-code strip: 6-8 small solid swatches in a row, the sole chroma, repeated as identity
- One engraved line diagram as hero: radar/polar plots, contour rings, waveform stacks, hairline white on black
- Wide-tracked monospace capitals for every label; the catalog number as the de facto logotype
- Hairline rules (1px, 40-60% white) separating numbered sections (01, 02, 03)
- Outline-only display lettering, engraved weight, never filled
- Material swatches: matte board, pulse-ink ridge patterns, etched aluminum - confined to panels

## Voice register

Transmission terseness: "SYSTEMS ALIGN. SIGNALS TRANSMIT." "END OF TRANSMISSION." Labels over sentences; numbers over names; duration and series metadata presented as content. Never enthusiastic, never explanatory - the reader is assumed to be in the know.

## Failure mode

Letting the strip colors leak into buttons or links turns the cipher into a rainbow UI theme. Adding a photograph - any photograph - breaks the diagram-led premise and drifts it toward `aesthetic-monochrome-tech-editorial`. Filling the outline display type, tightening the mono tracking, or adding a friendly rounded button betrays the engraved austerity. Worst: explaining the diagram with a caption. The withholding IS the brand.

## Best for

- Record labels, music catalogs, release and archive browsers
- Design studios and foundries with numbered-works portfolios
- Limited-edition product drops where scarcity is the message
- Data-art projects and generative-audio tools

## Pairs well with

- Shells: `shell-centered-column`, `shell-hero-stack`, `shell-two-column-app`
- Styles: `style-dense-mono-dark`, `style-restrained-hairline`, `style-micro-text-frame`

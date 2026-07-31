---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-home-sewing-pattern-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-home-sewing-pattern-isolated.png
    reason: Signature motif, isolated.
---
# Home sewing pattern (aesthetic)

**Tag:** vintage pattern-envelope vernacular

**Canonical references:**
- Simplicity / Butterick / McCall's / Vogue Patterns envelopes, 1940s-1970s
- The tissue inside: printed cutting lines, notches, grain arrows on crackly manila tissue
- Commercial drafting-ink fashion flats - clean contour garments with flat fills, lettered View A / B / C
- Instruction sheets: numbered steps with tiny diagram vignettes

## Cultural identity

The codified language of home dressmaking: a tissue-manila ground, condensed commercial caps for the headline (letterpress-flavored, tightly set), and garments drawn as drafting-ink fashion flats - clean dark contour, flat pastel fill, no shading theatrics. Variants are LETTERED: View A in blue, View B in sage, View C in coral, each letter set large and colored to match its garment. Below the display layer runs the notation system - red dashed rules meaning cut-here, black dashed lines meaning stitch, notch triangles, circles-and-dots markings, and the grain arrow with its double head.

It is instructional graphic design with domestic warmth: everything teaches, but the paper is soft and the colors are kitchen-curtain pastels. Buttons wear dashed "stitched" inner borders; steps are numbered in small square tags; a ruler lives at the end of every measurement field.

## Palette anchor

Warm paper plus drafting ink plus three view pastels and one selected red.
- Tissue manila `oklch(92% 0.035 92)` - the ground
- Drafting ink `oklch(21% 0.004 100)` - contours and text
- View A blue `oklch(80% 0.05 235)`
- View B sage `oklch(80% 0.06 135)`
- View C coral `oklch(78% 0.08 40)`
- Selected red `oklch(57% 0.18 27)` - dashed rules, primary actions, chosen size line

## Decoration motifs

- Dashed everything with MEANING: red dash = cut / primary, black dash = stitch / secondary
- Lettered view variants (A / B / C) as oversized colored initials beside their flats
- Notch triangles, dot-and-circle markings, and grain arrows as micro-iconography
- Numbered instruction steps in small square tags with diagram vignettes
- Stitched-border buttons: solid fill with an inset dashed keyline
- Tissue-crackle and envelope-stock paper textures; faint printed-tissue linework in backgrounds

**Raster required:** the drafting-ink fashion flats (illustration - clean contour garments with flat pastel fills) and the tissue-crackle paper texture. The dashed notation system itself stays CSS/SVG.

## Voice register

Patient instructional imperative. "Pin pattern to fabric, matching notches." "Cut along the selected size line." Sizes and measurements delivered plainly ("View B - Size 12"). Warm but never cute; the voice of a pattern that has taught three generations.

## Failure mode

Where `aesthetic-craft-sketchbook` is loose personal doodle - wobbly lines, marginalia, happy accidents - this is COMMERCIAL NOTATION: every dash is a rule with a meaning, every mark is standardized. Freehand squiggle borders and hand-scrawled arrows break the register. Equally fatal: crisp vector-flat modern illustration with no paper - without tissue warmth it becomes a generic pastel wireframe kit.

## Best for

- Craft, sewing, knitting, and DIY tutorial products
- Step-by-step builders and configurators (the "views" map to variants)
- Fashion and made-to-measure commerce with a heritage angle
- Recipe-like structured instruction content of any kind

## Pairs well with

- Shells: `shell-centered-column`, `shell-two-column-app`, `shell-masonry`
- Styles: `style-cream-humanist`, `style-serif-warm-paper`
- Aesthetic kin: `aesthetic-craft-sketchbook` (the loose cousin to diverge from), `aesthetic-cottagecore` (shared domestic warmth, none of the notation)

---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-toy-aisle-window-box-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-toy-aisle-window-box-isolated.png
    reason: Signature motif, isolated.
---
# Toy aisle window box (aesthetic)

**Tag:** toy-packaging construction

**Canonical references:**
- Calico Critters / Sylvanian Families window boxes - gingham trim, cellophane pane, diorama inside
- Re-Ment and miniature-collectible packaging - contents lists, series checklists
- American Girl / Our Generation shelf presentation - scalloped stickers, shelf-tag pricing
- Toy-aisle shelf furniture: "NEW" and "BEST SELLER" splat badges, ranked shelf tags

## Cultural identity

The box is the interface: cream die-cut board framed in gingham trim, with a cellophane window through which a miniature diorama glows - a tiny kitchen, a tiny bathroom, tiny shelves fully dressed. Every edge is finished like packaging: scalloped sticker borders on swatches, rounded chubby lowercase logotype, flower-shaped bullet marks, and a contents list that inventories the joy inside ("1 Kitchen Set, 1 Mini Figure, 6 Accessories, 1 Recipe Card, Sticker Sheet"). Shelf furniture completes it - a yellow price tag, and flower-splat ranking badges in green ("new"), yellow ("best seller"), and blue ("staff pick").

The register is retail tenderness: country-kitchen palette, gingham in three colorways doing the work of brand color, and the collector's pleasure of sets, series, and checklists.

## Palette anchor

Country-kitchen tints on cream, each hue owning a gingham colorway.
- Cream board `oklch(97% 0.015 95)` - the ground
- Berry red `oklch(50% 0.15 20)` - logotype and primary actions
- Meadow green `oklch(63% 0.11 135)`
- Sky blue `oklch(75% 0.07 240)`
- Shelf-tag yellow `oklch(86% 0.14 90)` - price tags only
- Cocoa ink `oklch(36% 0.04 55)` - body text

## Decoration motifs

- The cellophane window: a gingham-framed pane with a gloss sweep, holding a diorama photo
- Gingham trim as border, page frame, and active-state fill (colorway = category)
- Scalloped / pinked sticker edges on swatches, cards, and badges
- Flower-splat badges ("new", "best seller", "staff pick") and flower bullet marks
- Contents lists as first-class UI - itemized set inventories with tiny icons
- Dotted-rule dividers and shelf-tag price chips

**Raster required:** the miniature-diorama product shots (photo - fully dressed tiny rooms with warm toy-shelf lighting, seen through a slight cellophane sheen) and the gingham fabric swatch textures. The scallops, splats, and trims stay CSS/SVG.

## Voice register

Gentle collector's retail. "Tiny worlds, big imagination." "Collect the sets, build your own playroom." Lowercase logotype warmth; inventories spoken with quiet pride. Never shouting, never scarcity pressure.

## Failure mode

Where `aesthetic-cottagecore` is the fabric MOOD - meadows, linen, unhurried life - this is retail packaging CONSTRUCTION: die-cut board, window, shelf tag, contents list; remove the packaging logic and you have drifted into cottagecore. Against `aesthetic-toy-catalogue-primaries` the split is flat printed page vs constructed box: that one shouts unmixed primaries and price splats; this one whispers gingham and staff picks. Mixing the two (starbursts on gingham) reads as a clearance bin.

## Best for

- Collectible and miniature commerce; subscription-box products
- Kids' and family brands with a handmade-adjacent register
- Curated shops where "what's inside the set" is the selling point
- Wishlists, registries, and gift-guide experiences

## Pairs well with

- Shells: `shell-bento-grid`, `shell-mobile-app`, `shell-masonry`
- Styles: `style-cream-humanist`, `style-skeuomorphism` (the box dimensionality, used gently)
- Aesthetic kin: `aesthetic-cottagecore` (the mood without the retail), `aesthetic-toy-catalogue-primaries` (the loud flat-print sibling)

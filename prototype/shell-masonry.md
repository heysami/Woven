---
# Sample-image references for the System-tab design library. Images sit
# next to this file in prototype/ and were generated via image_gen.
images:
  - src: shell-masonry-ui.png
    reason: Shell structure UI mockup.
---
# Masonry / gallery shell

**Tag:** `[showcase · column-flow · image-led]`

## Structure

CSS columns or grid auto-flow producing cascading layout.

```css
.gallery { columns: 280px 3; column-gap: 16px; }
.gallery > .tile { break-inside: avoid; margin-bottom: 16px; }
```

Column min-width 240-320px. Gap 12-24px. Tile aspect variable.

## Density

Image-led. Type minimal.

## Mandatory interactions

Hover reveal on tiles (caption, action overlay). Click to expand into lightbox/detail modal. Infinite scroll OR pagination.

## Best for

Portfolios, art galleries, mood boards (Pinterest, Are.na), product catalogs with varying images.

## Pairs well with

Style: oversized-neo-grotesque, restrained-hairline, raster-cutout. Aesthetic: any.

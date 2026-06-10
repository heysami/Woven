---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: shell-bento-grid-ui.png
    reason: Shell structure UI mockup.
---
# Bento grid shell

**Tag:** `[marketing · 12-col asymmetric · low-density]`

## Structure

12-column CSS grid with asymmetric cell spans. Apple feature page.

```css
.bento { display: grid; grid-template-columns: repeat(12, 1fr); gap: 16-24px; }
.cell-hero { grid-column: span 8; }
.cell-side { grid-column: span 4; }
.cell-wide { grid-column: span 12; }
```

Cells: large radius (16-24px), generous padding (32-48px).

## Density

Low. One bold visual per cell.

## Mandatory interactions

Hover lift on cells (translateY + shadow). Scroll-driven entrance reveal (optional). CTA buttons clickable.

## Forbidden

Dense list rows. Multi-column tables in cells. App-shell chrome.

## Best for

Product marketing pages, feature showcases, app-store-style hero pages.

## Pairs well with

Style: bold-display, glassmorphism, aurorism. Aesthetic: none usually.

---
# Optional sample-image references. Each entry pairs an image (relative to
# the prototype/ folder, or absolute under the project root) with the
# *reason* it belongs to this genre. The landing System tab's design
# library surfaces these so a project picking this shell can adopt the
# images as visual references. Picks aren't deterministic — multiple refs
# are encouraged.
images:
  - src: shell-bento-grid-1.png
    reason: Placeholder — replace with an Apple privacy-page-style asymmetric 12-col bento (one bold visual per cell)
  - src: shell-bento-grid-2.png
    reason: Placeholder — replace with a low-density bento showing 24px gaps + 16-24px cell radii + generous 32-48px padding
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

---
# Sample-image references for the System-tab design library. Images sit
# next to this file in prototype/ and were generated via image_gen.
images:
  - src: shell-centered-column-ui.png
    reason: Generated UI mockup showing this shell's structural grammar — grid, density, regions, and characteristic component placement.
---
# Centered narrow-column shell

**Tag:** `[content · single-column · max 65-72ch]`

## Structure

Single column centered on the page. Classic blog / longform / profile layout.

```css
.page { max-width: 65-72ch; margin: 0 auto; padding: 80px 24px; }
```

## Macro proportions

Body column 65-72ch. Margins generous (80-120px between sections, 1.5em between paragraphs). Drop-cap era-dependent.

## Density

Low. Reading is the activity.

## Mandatory interactions

Smooth scroll. Link follow (full page nav fine). Optional footnote popover, TOC anchor jump.

## Forbidden

Sidebar nav. Multi-column. Marketing CTAs in body.

## Best for

Editorial longform, blog posts, profile pages (Read.cv, Cargo), wellness journal pages, essay-feel docs.

## Pairs well with

Style: serif-warm-paper, restrained-hairline, cream-humanist. Aesthetic: any era (Bauhaus, Anti-design, Maximalism for art-directed editorial).

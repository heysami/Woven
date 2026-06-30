---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: shell-scrapbook-substrate-ui.png
    reason: Shell structure UI mockup.
---
# Scrapbook substrate shell

**Tag:** `[any-aesthetic · raster-cutouts · layered z-order]`

## Structure

Full-bleed substrate texture hosts raster cutouts with overlap and rotation.

- Substrate: full-viewport background (PNG of paper / cork / fabric / journal)
- Cutouts: PNG/WebP-with-alpha positioned absolutely or freeform grid
  - `box-shadow: 2px 4px 6px rgba(0,0,0,0.18)` (paper-edge shadow)
  - `transform: rotate(-4deg)` to `rotate(4deg)` (hand-pasted feel)
  - z-index stacking for overlap
- Decorations: washi tape SVGs, push-pin PNGs, stapled corners, margin notes

Freeform composition. **Maximalist density** is the default register: tightly overlapped layers, the substrate barely showing through, every region carrying something - the opposite of a clean airy grid. Density escalates rather than thins. Ambient drift keeps it alive (slow per-element `translate`/`rotate`, never synced) so it reads as a living scrapbook, not a frozen paste-up.

## This is a WHOLE-PAGE build mode (not an iframe)

The scrapbook is the **real page** - real nav, sections, content, components - rendered as raster cutouts. The cutouts ARE the nav / cards / headers / buttons. Never box it inside an iframe. The heavy raster work (commissioning every cutout via `visual-orchestrator`, then composing them onto the real page freeform/animated/maximalist) is driven by `scrapbook-experience-orchestrator` over this real page; you build the skeleton here.

## Raster-richness minimums (commit all three by default)

A scrapbook that reaches for one of these and skips the others reads as half-committed. Mark each cutout `<img data-slot="<id>" data-medium="raster-foreground" alt="...">` so the commission pass fills it:

1. **Still raster cutouts** - the bulk: hero photo, sticker cutouts, paper-tape attachments, scanned textures, polaroid frames, handlettering. These are the page's real elements.
2. **≥1 PNG-sequence "key visual"** (the transparent-GIF substitute - see `step-motion.md`): one looping element (rotating bust, sparkling divider, blinking cursor, flickering lantern). Drop only when the brief explicitly forbids motion. `prefers-reduced-motion` freezes frame 0.
3. **≥1 raster UI element** with transparent background (button / nav tab / scroll arrow / marker checkbox / sticker CTA). A CSS `<button>` with rounded corners + gradient inside a hand-made collage screams "I gave up here." Drop only when the page is non-interactive.

## Mandatory interactions

Hover lift on cutouts. Optional drag-to-rearrange. Tap-to-flip/reveal.

## Forbidden

Lucide icons. Geometric SVG shapes. border-radius on cutouts. Pure white substrate.

## Best for

Aesthetic blogs, mood boards, fashion lookbooks, journal apps, fan catalogs.

## Pairs well with

Style: raster-cutout (mandatory). Aesthetic: cottagecore, dark-academia, y2k-myspace, goblincore, coastal-grandmother, dreamcore, cottagegoth, angelcore, cluttercore - pick ONE.

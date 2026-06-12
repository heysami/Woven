---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: style-pixel-dissolve-ui.png
    reason: Style surface UI mockup.
  - src: style-pixel-dissolve-isolated.png
    reason: Signature surface, isolated.
---
# Pixel dissolve (style)

**Tag:** `style-pixel-dissolve`

**Canonical references:** HR-SaaS pastel heroes with pixel-block edges (motionsites corpus) · Bayer-dither revival posters · transition language from 16-bit games recoded as a static surface treatment

## Surface treatment

Surfaces, gradients, and images DISSOLVE into square pixel blocks at their edges — a controlled digital crumble where one material hands off to another. The dissolve is the signature; everything else stays clean and modern.

### The grammar

- One or two dissolve events per viewport: a gradient field crumbling into the background, a photo's edge breaking into 8-24px squares, a color band pixelating out
- Block sizes step in powers of two (8 → 16 → 24px) as the dissolve progresses
- Blocks sample their color FROM the dissolving surface (it's the same material breaking up, not confetti)
- Direction is intentional: dissolve toward whitespace, away from the content's reading path

### Background / color

- Works on light pastel grounds (`#f3f0fa`, `#eef5f1`) and dark (`#0c0d12`)
- The dissolving surface is usually the page's one gradient or one image
- Ink and UI chrome stay sharp — ONLY the designated surface dissolves

### Type stack

- Clean grotesque for everything; optionally ONE headline word rendered in the pixel-block treatment as an echo (max once per page)

### Motion

Blocks may shimmer in/out near the dissolve frontier (200-400ms, staggered) or stay fully static — the style reads at rest. Scroll-linked variant: dissolve progresses 10-20% with section entry. Respect `prefers-reduced-motion`.

## Failure mode

Random pixel confetti scattered as decoration (the blocks must be the EDGE of something dissolving); whole-page pixelation (that's `style-pixel-bitmap`, a different commitment); dissolve on every section (one or two events, or it's wallpaper); mixed block sizes that don't step cleanly.

## Best for

HR/product SaaS wanting a quiet tech signature, data/AI brands ("solid becomes signal"), transition-heavy promos, anywhere a gradient hero needs one memorable detail without abandoning modern cleanliness.

## Pairs well with

- Shells: `shell-hero-stack`, `shell-centered-column`
- Styles: `style-editorial-italic-accent` (the corpus pairing), `style-aurorism` (the dissolving gradient), `style-restrained-hairline`
- Aesthetics: `aesthetic-pastoral-serene` pastel variants; pixel-art aesthetics for harder retro reads

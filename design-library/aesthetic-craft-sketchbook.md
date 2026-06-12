---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-craft-sketchbook-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-craft-sketchbook-isolated.png
    reason: Signature motif, isolated.
---
# Craft sketchbook (aesthetic)

**Tag:** `aesthetic-craft-sketchbook`

**Canonical references:**
- ogud.co.jp/urbanex/next21 ("TRANS×HOME") — the complete register: every
  headline, nav label, and full architectural scene illustration hand-drawn,
  self-drawing in on scroll, on cream woven paper with one vivid blue
- Architectural concept-book tradition: pencil perspective sketches with
  ink-line people, annotation handwriting, the designer's working notebook
  published as-is
- Field-notes / travel-sketchbook publishing (Moleskine-journal register)

**NOT to be confused with:** `style-doodle` (Excalidraw-style sketchy UI skin
— playful, tool-like) or `aesthetic-cottagecore` (pastoral nostalgia). Craft
sketchbook is a PROFESSIONAL's working drawings — an architect's or
illustrator's hand, observational and intentional, warm but precise.

## Cultural identity

The page pretends to be a working sketchbook: warm woven/uncoated paper as
the ground, every graphic element drawn by a confident hand — monoline ink
figures, pencil-textured buildings in cutaway, hand-lettered headings — and
exactly one vivid printed accent color asserting that this is design, not
nostalgia. The register says: *we thought this through by hand before we
built it.* Concept-stage honesty as brand value.

Distinct energy from doodle: doodle is fast and goofy; sketchbook is SLOW and
observed — perspective is roughly correct, line weight varies with pressure,
hatching follows form.

## Palette anchor

- Ground: cream/kraft paper `#DCD5BC`–`#EDE6D5` with a real woven or
  uncoated-paper texture (this aesthetic NEEDS the substrate)
- Ink: near-black `#1A1A1A`–`#333` for line work; graphite grey `#6B6B6B`
  for shading layers
- ONE vivid accent, printed-feeling: vivid blue `#0068FE`, vermillion, or
  stamp red — used for emphasis marks, active states, and one accent per
  composition
- Photography/video, when present, blends INTO the paper
  (`mix-blend-mode: multiply`) so it reads as printed on the page

## Composition principles

1. **Everything graphic is drawn.** Headlines hand-lettered (as SVG strokes),
   nav labels hand-written, illustrations full scenes with people — webfonts
   only for body copy, kept small and quiet.
2. **The hand arrives live:** marks self-draw on scroll entry
   (`motion-svg-self-draw` is this aesthetic's native entrance grammar).
3. **Annotation logic:** arrows, underlines, circled numbers, margin notes —
   layout devices borrowed from a worked-on drawing, not from UI chrome.
4. **Asymmetric, generous paper:** content sits like sketches on a spread —
   unequal margins, one dominant drawing per view, white (cream) space as rest.
5. **Media multiplied into paper:** any raster/video runs through multiply
   blend over the paper texture; nothing glossy floats above the page.

## Voice register

First-person studio voice, present tense, explanatory — captions like a
designer talking you through their notebook ("the wall opens here"). Measured
warmth; no exclamation marks; numbers hand-written when decorative, tabular
when factual.

## Raster requirement

⚠ Raster required: the paper substrate must be a real texture (woven linen /
uncoated stock scan or generated equivalent) — flat hex cream reads as a
wireframe, not a sketchbook. The drawings themselves are stroke SVGs
(hand-traced register), not raster.

## Failure mode

First tell: Comic Sans-adjacent "handwriting" webfonts doing the lettering —
the hand must be drawn (SVG paths), not typed. Second tell: flat `#F5F0E0`
background with no paper texture. Third tell: perfect geometric icons sharing
the page with sketches (one hand draws everything, or the spell breaks).
Fourth tell: more than one accent color — a sketchbook has one pen besides
the ink. Fifth tell: glossy photography in hard-cornered boxes floating over
the paper instead of multiplied into it.

## Best for

- Architecture / real-estate concept campaigns, urban-planning projects
- Craft, atelier, and maker brands; design-process storytelling
- Education and workshop programs; museum hands-on exhibits
- Any brief whose promise is "thoughtfully made by people who draw"

## Pairs well with

- **Shells:** `shell-hero-stack`, `shell-centered-column`, `shell-editorial-broken-grid`
- **Styles:** `style-doodle` (nearest style host — calmed down), `style-outline-wireframe`, `style-serif-warm-paper` (body layer)
- **Motion:** `motion-svg-self-draw` (native), `motion-threshold-ritual` (counter ceremony)
- **Materials:** `material-uncoated-paper`, `material-linen-weave`, `material-pencil-graphite`, `material-marker-stroke-frame`

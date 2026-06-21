---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: recipe-brand-story-journey-ui.png
    reason: Full recipe UI mockup.
  - src: recipe-brand-story-journey-isolated.png
    reason: Signature scene, isolated.
---
# Brand story journey (identity explainer as scroll film)

A `(shell + style + material + motion)` bundle for **brand-identity,
anniversary, and philosophy explainers staged as a fixed-viewport scroll
film** - the register of Daimaru Matsuzakaya's generative-VI site and KOKUYO's
"Curiosity is Life": the page IS a sequence of chaptered scenes the wheel
travels through, the brand's own design system is the protagonist, and
narration text lives INSIDE the scene's negative space rather than in
overlays.

## Picks

- **Shell:** `scroll-journey-scene` - read `shell-scroll-journey-scene.md`.
  Fixed viewport (`overflow: hidden`), wheel/scroll as scrubbed input,
  stations instead of sections.
- **Style:** `restrained-hairline` for the UI chrome - 10-24px labels,
  hairline progress indicator, text links only; ALL visual mass belongs to
  the scene, none to the components.
- **Material (the protagonist's body, pick per brief):**
  `paper-construction` (die-cut strata / pop-up book - the observed canon) ·
  any hero material the brand's identity dictates.
- **Motion:** `scene-zoom-through` (dive through apertures/layers as chapter
  transitions) + `scroll-scrub-journey` (camera travel) + optional
  `threshold-ritual` (sound-consent gate or opening ceremony) + optionally,
  when the identity is generative, a tap-to-regenerate moment (pointer tap
  recomposes the live emblem - no library entry yet; see
  `docs/research/japanese-web-survey.md` Tier 2).
- **Voice:** curatorial first-person-plural, short narration beats (one
  sentence per station), a persistent chapter breadcrumb ("Element 2 :
  Shape") as the only wayfinding.

## Pattern

- **Chapters, not sections:** 4-8 named stations (History → Color → Shape →
  Pattern…), each ONE idea, each labeled by the persistent breadcrumb
- **Narration inside the scene:** copy typeset into the scene's negative
  space (inside a die-cut aperture, in the lighting's quiet zone) - never a
  text card floating OVER the scene
- **The identity is the material:** the brand's actual design elements
  (colors, marks, papers, glyph systems) are the 3D/visual substance being
  traveled through - no stock metaphors
- **Type stays small:** 14-24px throughout; the scene is the display type;
  near-zero type-scale contrast is correct here
- **One interactive proof moment:** if the identity claims something
  ("different every time," "sharp," "modular"), one station lets the visitor
  verify it by acting (tap to regenerate, drag to slice, click to recompose)
- **Entry/exit discipline:** loading veil or threshold ritual at the front;
  a conventional footer (credits, corporate links) only after the final
  station hands scroll back to the document

## Best for

Brand-identity/VI guideline launches, anniversary microsites, corporate
philosophy pages, rebrand announcements, design-department showcases -
anywhere the design system itself is the story.

## What distinguishes this from existing recipes

- `editorial-magazine` explains with prose and images IN a document; this
  explains by traveling THROUGH a scene.
- `object-stage-hero` reveres one object on a stage; this narrates a SYSTEM
  across chapters - the camera moves, the argument accumulates.
- `aurora-marketing` uses atmosphere as backdrop for product claims; here
  the visual world IS the claim (the identity demonstrating itself).

## Build routing

Scene chapters route to the motion-studio / narrative-experience orchestrators
(storyboard → concept plates → scenes); `paper-construction` worlds at hero
grade route to the 3d/hero-3d path; the interactive proof moment routes to
interactive-media if input→output mapping is the point.

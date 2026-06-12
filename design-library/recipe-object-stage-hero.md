---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: recipe-object-stage-hero-ui.png
    reason: Full recipe UI mockup.
  - src: recipe-object-stage-hero-isolated.png
    reason: Signature scene, isolated.
---
# Object stage hero (Spline-grade 3D scene + UI in the quiet zone)

A `(shell + style + material + motion)` bundle for **heroes and full-page
scenes where ONE studio-lit 3D object (or object cluster) carries the brand**
— the register shared by every high-grade Spline community scene: physically-
based materials, disciplined monochrome field, ambient motion always running,
damped pointer response, and UI text laid INTO the scene's quiet zone rather
than boxed beside it.

## Picks

- **Shell:** `canvas-floating` (full-bleed scene + floating UI) or
  `hero-stack` (object stage as hero, normal page below) — read the shell
  files.
- **Style:** scene-dependent — `restrained-hairline` UI chrome over dark
  stages; `oversized-neo-grotesque` when type shares the stage with the
  object.
- **Materials (the cast, pick ONE lead):** `dispersion-prism-glass` ·
  `reeded-fluted-glass` · `smoked-obsidian-glass` · `chrome-extruded-type` ·
  `anodized-chainmail` · `edge-lit-acrylic` · `filament-strand-ribbon` —
  staged under `volumetric-light-shaft` when the field is dark.
- **Motion:** `mouse-scrub-orbit` / `pointer-parallax-layers` /
  `drag-physics-cluster` for the object; `slow-push-zoom` for entrance;
  ambient idle ALWAYS (drift, turntable, breathe — a frozen object stage is
  a broken one).
- **Voice:** few words, large or spare; the object is the argument. Mono
  micro-labels at corners (coordinates, indexes, "FORM / TARGET") are the
  register's jewelry.

## Pattern

- ONE hero object (or one cluster) — never a crowd of competing subjects
- Monochrome scene discipline: the field, the object, and the light share one
  hue family; a single accent at most (the R2 prism page is mint-on-mint, the
  R10 torus is black-on-black)
- Studio lighting story: one key direction committed; every specular, shadow,
  and shaft agrees
- UI lives in the scene's quiet zone — headline and CTA placed where the
  lighting leaves room, checked against the object's full motion arc
- Damped easing on EVERYTHING pointer-driven (`cur += (t - cur) * 0.05–0.12`)
  — nothing snaps; the smoothness is the quality signal
- Idle is alive: turntable, drift, breathe, or shaft-flicker at 10–30s
  periods; `prefers-reduced-motion` freezes at the hero frame
- Film grain or subtle noise pass over dark stages ties render to page
- Loading discipline: poster/baked frame paints first, scene fades in over it

## Best for

Brand/product heroes where material quality IS the message (hardware, AI
infra, luxury, security), portfolio statements, launch teasers, museum/
exhibition microsites — anywhere "we sweat details you can feel" is the
posture.

## What distinguishes this from existing recipes

- `aurora-marketing` leads with atmosphere-as-gradient; this leads with an
  OBJECT under real lighting physics.
- `bento-marketing` celebrates many small cells; this celebrates one subject
  on one stage.
- `aesthetic-sculptural-minimal` is the white-gallery cousin; this recipe
  generalizes the plinth to dark stages, glass refractors, and physics toys,
  and commits the interaction grammar (damped pointer, ambient idle).

## Build routing

Hero-grade scenes route to the `3d` drawer at `performance: hero` (interim)
or the proposed hero-3d orchestrator (scene / material / interaction /
runtime trio split — see `docs/research/spline-grade-3d-study.md` §4).
DOM-worn materials (reeded pane over an image, edge-lit cards) route to
`material-orchestrator`; 2D print-process passes to
`interactive-polish-orchestrator`.

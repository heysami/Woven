---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-lcars-elbow-console-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-lcars-elbow-console-isolated.png
    reason: Signature motif, isolated.
---
# LCARS elbow console (aesthetic)

**Tag:** starship wall-panel futurism

**Canonical references:**
- Michael Okuda's LCARS for Star Trek: The Next Generation (1987) - the founding grammar: backlit flat panels, elbow frames, pastel pills on black.
- Star Trek: Voyager / DS9 bridge consoles - the mature vocabulary of numeric code labels and segmented color bars.
- Okudagram set-dressing plates - entire walls of decorative-but-plausible interface, designed to read from ten feet away.
- Fan-built LCARS terminals and padd apps - proof the system survives as a real usable UI, not just set dressing.

## Cultural identity

The wall-panel operating system of an optimistic starship future. The defining move is **structural**: curved elbow frames - thick rounded bars that run along an edge, turn a corner with a generous radius, and terminate in a pill cap - are the layout itself, not decoration on top of it. Content lives in the voids the elbows carve out. Every interactive element is a pill or a lozenge segment in a flat pastel; every label is condensed caps; half the text on screen is numeric code ("47-21-9A", "33-AE") that signifies systems depth without needing to be read. The surface is flat backlit plastic - perfectly matte, zero gloss, zero texture, zero wear.

This is NOT `aesthetic-cassette-futurism` - that world is worn beige hardware, CRT curvature, institutional dust; LCARS is pristine, weightless, and backlit. And it is NOT `aesthetic-atompunk` - no raygun chrome, no googie starbursts, no 1950s optimism; LCARS optimism is procedural and calm, a screen that assumes competence.

## Palette anchor

Pastel pills on absolute void. The black is total; the accents are soft but saturated enough to glow:
- Lilac `oklch(80% 0.10 295)`
- Peach `oklch(83% 0.10 55)`
- Gold `oklch(85% 0.15 85)`
- Periwinkle `oklch(72% 0.13 270)`
- Muted lilac-gray `oklch(72% 0.04 290)` for secondary text
- Void black `oklch(0% 0 0)` - the background is never charcoal, never navy

Active state swaps a segment's fill to gold; alert states go red-orange. Never gradients, never shadows, never white backgrounds.

## Decoration motifs

- **Elbow frames as layout** - rounded corner bars with pill terminals framing every region; the frame IS the grid.
- **Segmented color bars** - runs of pills in alternating pastels along edges, occasionally interrupted by a numeric label.
- **Numeric code labels everywhere** - hyphenated hex-flavored codes as button text, list rows, and filler data.
- **Pill and lozenge components** - buttons with one flat side and one rounded side; notched hexagonal caps on inputs.
- **Condensed caps display type** - tall, tightly-set, slightly squared; numerals as display-scale heroes.
- **Dot-matrix status fields** - grids of small dots in mixed pastels standing in for dense telemetry.

## Voice register

Calm shipboard procedure. Terse system nouns and confirmations: "SYSTEMS ONLINE", "LAUNCH BAY", "POWER DISTRIBUTION 87%", "NOMINAL". Never exclamatory, never marketing, never lowercase. The voice assumes a trained operator.

## Failure mode

Rounded-rectangle cards with drop shadows on dark gray, a glowing cyan sci-fi HUD font, scanlines, or chrome bevels = generic space UI, not LCARS. The tells of the real thing: black is pure, surfaces are flat, the elbow frame touches the screen edge, and at least a third of the visible text is numeric code. Gloss, glow bloom, or texture of any kind breaks the backlit-plastic material logic. So does gray - LCARS has no neutral midtones, only black and pastel.

## Best for

- Fleet/ops dashboards, mission-control and telemetry products that want warmth instead of menace.
- Sci-fi fan properties, episode guides, starship-flavored community tools.
- Smart-home and panel-mounted control surfaces (the wall-panel metaphor is literal).
- Status boards and kiosk screens read at a distance.

## Pairs well with

- Shells: `shell-top-bar-canvas`, `shell-three-column-app`, `shell-bento-grid`, `shell-mobile-app`
- Styles: `style-flat-design`, `style-bold-display`, `style-micro-text-frame`

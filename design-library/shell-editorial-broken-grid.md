---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: shell-editorial-broken-grid-ui.png
    reason: Shell structure UI mockup.
---
# Editorial broken-grid shell

**Tag:** `[art-directed · asymmetric · per-spread]`

## Structure

Art-directed magazine spreads. Each spread/section has custom layout - text floating around images, deliberate misalignment, oversized display.

```css
.spread {
  display: grid;
  grid-template-areas: "title title image" "body body image" "body body caption";
  grid-template-columns: 1fr 1fr 1.4fr;
}
```

Each spread defines its own grid-template-areas.

## Density

High typographic and visual density.

## Mandatory interactions

Smooth scroll between spreads. Hover reveal on captions/footnotes. Pull-quote callouts. Optional parallax on hero imagery.

## Best for

Magazine features, art-directed editorial, photo essays, fashion editorials.

## Pairs well with

Style: serif-warm-paper, agate-broadsheet, oversized-neo-grotesque, bold-display. Aesthetic: any (each spread can lean into a different cultural reference).

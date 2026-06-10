---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: shell-canvas-floating-ui.png
    reason: Shell structure UI mockup.
---
# Full-bleed canvas + floating panels shell

**Tag:** `[full-bleed · overlay chrome · scene/tool]`

## Structure

One full-viewport canvas with floating overlay chrome.

- Canvas: full-bleed, fills viewport
- Floating panels: position absolute/fixed
  - Top-left: logo/title pill
  - Top-right: layer toggles, settings
  - Bottom-center: transport controls (for video / scene)
  - Right side: properties/inspector overlay

Panels inset 16-24px from viewport edges.

## Mandatory interactions

Pan/zoom on canvas. Layer toggle. Hover-reveal on canvas elements. Panel collapse/expand. Tool selection.

## Best for

Maps, video editors, 3D scenes, design tools, photo viewers (deep-zoom).

## Pairs well with

Style: glassmorphism (panels), restrained-hairline (chrome), dense-mono-dark (data overlays). Scene moments: immersive-3d, real-world-map, globe, deep-zoom-document.

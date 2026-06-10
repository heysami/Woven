---
# Sample-image references for the System-tab design library. Images sit
# next to this file in prototype/ and were generated via image_gen.
images:
  - src: shell-top-bar-canvas-ui.png
    reason: Generated UI mockup showing this shell's structural grammar — grid, density, regions, and characteristic component placement.
---
# Top-bar + canvas + status footer shell

**Tag:** `[single-canvas-tool · header + main + footer · variable]`

## Structure

Single canvas with utility chrome above and status below.

- Top bar (48-56px): title + utility actions (save, share, settings)
- Main canvas (1fr): the work surface
- Status footer (24-32px): readouts (page / zoom / cursor / save state)

## Mandatory interactions

Save state indicator. Zoom controls. Undo/redo. Keyboard shortcuts.

## Best for

Document editors, image viewers, single-page tools.

## Pairs well with

Style: restrained-hairline, terminal-mono, outline-wireframe.

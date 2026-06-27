---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: shell-infinite-canvas-ui.png
    reason: Shell structure UI mockup.
---
# Infinite canvas shell

**Tag:** `[node-graph / whiteboard · pannable · z-zoom]`

## Structure

Pannable, zoomable canvas with no fixed viewport bounds.

- Canvas: position absolute; transform: translate(x,y) scale(z) controlled by pan/zoom state
- Nodes: positioned in canvas-space, typically 200-400px wide
- Edges: SVG bezier curves between nodes (when applicable)
- Toolbar: fixed overlay (top-left or top-center)
- Minimap: bottom-right, click-to-fly

## Mandatory interactions

Pan (drag empty space). Zoom (scroll/pinch). Node drag-to-move. Edge create (drag handle to handle). Selection (rubber-band, shift-add). Fit-to-content (F shortcut). Optional collaborative cursors.

## Best for

Workflow tools, mind maps, whiteboards (Miro, tldraw, Excalidraw), agent-graph editors, design canvas.

## Pairs well with

Style: restrained-hairline, doodle. Scene moments: node-graph (native mode).

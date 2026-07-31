---
materialId: split-flap-board
name: Split-Flap Board (mechanical per-character flap cells)
family: analog
category: mechanical
surfaceFinish: matte (printed plastic flaps) with brushed-steel frame
scope: object
transparency: opaque
pairsPrototypes: [aesthetic-cassette-futurism, aesthetic-industrial-catalog, style-dense-mono-dark, shell-terminal-frame, recipe-bloomberg-dashboard]
images:
  - src: material-split-flap-board.png
    reason: Material fidelity sample.
---

# Split-Flap Board (mechanical per-character flap cells)

Departure-board typography: every character lives in its own hinged flap cell with a visible horizontal split line at mid-height, mounted in a steel frame - text changes by physically flipping through the character drum.

## Physical behavior

**Surface finish**: matte printed plastic flaps (white or amber/red paint on black); brushed-steel frame with screw heads

**Transparency**: opaque

**Reacts to light**: reflectively only - flaps are lit by room light and row lamps; the glyphs never emit

**Deforms**: rotates - each flap flips on its horizontal hinge; mid-flip, the falling half casts a shadow on the lower half

**Age / wear**: slightly misaligned flaps, paint wear on high-traffic characters

## Implementation strategies

```yaml
css: |
  --flap-black: #0d0d0f; --flap-shadow: #1b1b1e; --flap-white: #f2f2f2;
  --delay-amber: #ffb400; --cancel-red: #d32f2f; --steel: #b6bbc2;
  /* one span per character - the cell is the atom */
  .cell { display: inline-block; width: 1.1ch; background: var(--flap-black);
    border-radius: 2px; margin-inline: 1px; position: relative; }
  /* the split line: always visible, exactly mid-cap-height */
  .cell::after { content: ""; position: absolute; left: 0; right: 0; top: 50%;
    height: 1px; background: rgba(0,0,0,0.75);
    box-shadow: 0 1px 0 rgba(255,255,255,0.06); }
animation: |
  flip = two half-cells; top half rotateX(0 to -90deg) with darkening,
  then bottom half of the NEXT character rotateX(90deg to 0); 60-110ms per step,
  cells cascade left to right with 15-30ms stagger; cycle through 2-4
  intermediate characters when the change is large
frame: |
  board = steel bezel (linear-gradient brushed texture) + corner screws;
  status cells fill the WHOLE flap with amber/red, glyph in black
```

## Reactive behaviors

**Light**: row lamps (small warm LEDs under the frame) may glow; flaps only reflect

**Highlight**: attention = a re-flip - the cell flutters through its drum and lands on the same character

**Depth**: mid-flip shadowing on the lower half; cells sit 1-2px proud of the board

**Parallax**: none

## Common implementation mistakes (avoid these)

- text without cell division (every character owns a flap cell; a plain styled string is not a board)
- missing the split line (the horizontal seam at mid-height is the single most identifying mark)
- cross-fading characters (changes are FLIPS - rotation with intermediate characters, plus the clack cadence)
- glowing glyphs (flaps are printed plastic; light comes from lamps and the room, never from the letterform)
- soft rounded cells with drop shadows (flaps are crisp rectangles in a rigid steel grid)
- status color as text color (delay amber and cancel red are whole-flap paint fills, glyph knocked out in black)

## Examples in the wild

- rail-concourse and airport Solari boards
- Vestaboard installations
- mid-century hotel and stock-exchange boards

## Pairs with (prototype slugs)

- `aesthetic-cassette-futurism`
- `aesthetic-industrial-catalog`
- `style-dense-mono-dark`
- `shell-terminal-frame`
- `recipe-bloomberg-dashboard`

## Differentiation

- vs `material-crt-phosphor`: CRT emits scanned light; split-flap is reflective printed plastic that moves mechanically
- vs `material-led-segment-display`: LED digits re-light segments in place; split-flap physically rotates through a character drum - the change itself is visible, shadowed, and sequential

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

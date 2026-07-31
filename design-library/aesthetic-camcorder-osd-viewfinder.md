---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-camcorder-osd-viewfinder-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-camcorder-osd-viewfinder-isolated.png
    reason: Signature motif, isolated.
---
# Camcorder viewfinder OSD (aesthetic)

**Tag:** framing-bracket on-screen display

**Canonical references:**
- Sony Handycam / Betacam viewfinder OSDs - the founding grammar: REC dot, timecode, battery glyph, corner brackets.
- Broadcast ENG camera overlays - zebra stripes on blown highlights, white-balance and iris readouts pinned to edges.
- The "REC 00:02:18" home-video vernacular - instantly legible shorthand for "this is being recorded".
- Modern mirrorless/cine UIs (RED, ARRI status pages) - the descendants that kept the edge-pinned readout discipline.

## Cultural identity

The live overlay a camera draws over the world: everything is **framing grammar**. Corner brackets - four L-shaped ticks - stand in for a full border on every component; readouts pin to the frame's edges (FPS and shutter top-left, white balance and ISO top-right, timecode bottom-left, zoom bar bottom-right) leaving the center empty except for a crosshair, because the center belongs to the subject. Type is a segmented LCD face, white on letterbox black, with one amber accent reserved for the armed state: the REC dot, the active control, the zoom position. Zebra diagonal stripes crawl over anything blown out. The screen never fills - the aesthetic is the discipline of staying out of the shot.

This is NOT `material-vhs-distortion` - that is what the TAPE does to the image afterwards (tracking noise, chroma smear, playback degradation); this is what the CAMERA draws live - crisp, functional, frame-edge chrome with zero degradation. A viewfinder page can be pin-sharp and still be unmistakably this world.

## Palette anchor

- OSD white `oklch(100% 0 0)` - readouts and brackets
- Accent amber `oklch(80% 0.16 75)` (#ffb000) - REC, active states, zoom fill
- Letterbox black `oklch(0% 0 0)` - the ground
- Shadow gray `oklch(30% 0 0)` and mid gray `oklch(52% 0 0)` - inactive chrome
- Zebra overlay - white/transparent 45-degree stripes, never a solid fill

Two-color discipline: white for information, amber for armed. A third hue means something is wrong.

## Decoration motifs

- **Corner framing brackets** - four ticks replacing full borders on buttons, cards, inputs, and the page itself.
- **Edge-pinned readouts** - data lives at the frame boundary; the center stays clear (a crosshair at most).
- **Segmented LCD type** - fourteen-segment display faces for headings and numerals alike.
- **REC dot** - the filled circle plus "REC", the aesthetic's one-glyph signature.
- **Zebra stripes** - diagonal hatch flagging overexposure, borrowed as a hover/warning texture.
- **Meter bars** - zoom W-to-T pips, battery segments, audio level blocks.
- **Timecode** - "TC 00:02:18:07" as ambient ornament that also tells the truth.

## Voice register

Readout language only: abbreviations, values, units. "FPS 24.00", "WB 5600K", "SHUTTER 1/48", "A 68 MIN". Verbs are single armed words: "REC", "MENU". No sentences on the chrome - if prose must exist, it is a menu item, terse and capitalized. The system reports; you frame.

## Failure mode

Full borders on every card, center-stacked content, and a digital font used decoratively = dashboard cosplay. The real thing keeps the middle empty, replaces borders with corner ticks, and pins everything to edges - break that and the framing metaphor dies. Also fatal: adding tape grain, glitch, or chromatic aberration (that is the VHS-playback world, not the live viewfinder), more than one accent color, or letting the amber leak into non-armed elements so REC stops meaning anything.

## Best for

- Recording, streaming, and capture tools - anything with an armed/live state.
- Video-editing, dailies-review, and camera-log products.
- Monitoring dashboards that want operator-grade focus (the empty center = the thing being watched).
- Filmmaker portfolios and film-festival microsites framed as footage.

## Pairs well with

- Shells: `shell-hero-stack` (full-bleed viewport with pinned readouts), `shell-top-bar-canvas`, `shell-scroll-journey-scene`
- Styles: `style-micro-text-frame` (the edge-pinned readout discipline, canonical), `style-dense-mono-dark`

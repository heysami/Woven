---
materialId: marker-stroke-frame
name: Marker stroke frame (hand-drawn containment outlines)
family: analog
category: ink
surfaceFinish: matte
transparency: opaque
pairsPrototypes: [style-doodle, aesthetic-zine-type-wall, aesthetic-y2k-memphis-loud, aesthetic-positivity-kawaii, recipe-editorial-magazine]
images:
  - src: material-marker-stroke-frame.png
    reason: Material fidelity sample.
---

# Marker stroke frame (hand-drawn containment outlines)

Thick, imperfect marker/crayon strokes used as CONTAINMENT - each item in a
list or grid gets its own one-off hand-drawn outline (a rough rounded blob, a
zigzag burst, a skewed parallelogram) in a dedicated solid color, so entries
become scannable by silhouette the way zine pages are. Distinct from
style-doodle (a whole-page sketchy skin) and from ink-wash-sumi-e (brush
calligraphy): this is felt-tip POSTER energy, opaque and saturated, deployed
per-item as a framing system.

## Physical behavior

**Surface finish**: matte, fully opaque pigment - marker lays flat color with
slight edge darkening where strokes overlap, no watercolor bleed

**Transparency**: opaque; overlap darkening (multiply at ~12%) is the only
translucency tell

**Reacts to light**: no

**Deforms**: no - but the "boil" variant wobbles: 3-5 hand-redrawn frames of
the same outline cycled at 6-10fps make the stroke shimmer like a pencil-test
animation

**Age / wear**: ageless

## Implementation strategies

```yaml
svg: |
  The primary path. Each frame is a closed <path> with stroke-width 16-48
  (relative to a ~600px viewBox), stroke-linejoin="round",
  stroke-linecap="round", fill="none". Hand-imperfection via:
  <feTurbulence baseFrequency="0.012" numOctaves="2"/>
  <feDisplacementMap scale="6"/>
  - LOW frequency, SMALL scale: marker wobbles at wrist scale, not at
  bristle scale (high-frequency jitter reads as pencil, a different tool).
  Every frame shape must be UNIQUE per item - blob, burst, parallelogram,
  cloud - sameness kills the zine read.
css: |
  /* boil variant - cycle 3 pre-drawn frame variants: */
  @keyframes boil { 0%,32% {opacity:1} 33%,100% {opacity:0} }
  .frame-v1,.frame-v2,.frame-v3 { animation: boil .45s steps(1) infinite; }
  .frame-v2 { animation-delay: .15s } .frame-v3 { animation-delay: .3s }
raster: scanned real marker strokes (the most honest path) as 9-slice or
  per-item PNGs with transparency; keep ink color editable by recoloring
  a black scan via CSS filter or SVG feColorMatrix
```

## Reactive behaviors

**Light**: no

**Highlight**: hover may swap the frame to its filled variant (the outline
floods with its own color at 15-20% opacity behind the content) - the zine
"selected" state

**Depth**: no - marker sits ON the page plane, never shadows

**Parallax**: minimal; frames belong to their content and move with it

## Common implementation mistakes (avoid these)

- One frame shape reused for every item (the entire point is one-off
  silhouettes - generate/draw a unique outline per entry)
- Geometrically perfect rounded-rect with a wobble filter (start from a
  hand-drawn path; filters only roughen, they can't add intent)
- Thin strokes (under ~12px at rendered size it becomes outline-wireframe,
  a different register - marker is THICK)
- Drop shadows or gradients on the stroke (marker is flat pigment on paper)
- Boil running on every frame simultaneously at high fps (one or two boiling
  frames per viewport, 6-10fps steps() - more reads as glitch, not pencil test)
- Pastel-on-pastel (the frame color must hit hard against the ground;
  marker is a poster tool)

## Examples in the wild

- nippori.lamm.tokyo - every featured episode gets its own thick marker
  outline (blob / burst / polygon) in a dedicated color; list scannable by
  silhouette
- wpups.jp - crayon circles drawn on radially (conic clip-path sweep) +
  5-frame boil on drawn wave dividers
- Physical referents: zine paste-up, school-festival posters, fanzine layouts

## Pairs with (prototype slugs)

- `style-doodle`
- `aesthetic-zine-type-wall`
- `aesthetic-y2k-memphis-loud`
- `aesthetic-positivity-kawaii`
- `recipe-editorial-magazine`

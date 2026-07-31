---
materialId: hand-processed-filmstrip
name: Hand-Processed Filmstrip (sprockets, scratches, chemical bloom)
family: analog
category: film
surfaceFinish: matte (emulsion) with glossy leader black
scope: both
transparency: opaque (light leaks read as burned-through exposure)
pairsPrototypes: [aesthetic-luxury-cinematic-dark, aesthetic-corporate-grunge, aesthetic-monochrome-pop-poster, style-brutalist-raw, recipe-editorial-magazine]
images:
  - src: material-hand-processed-filmstrip.png
    reason: Material fidelity sample.
---

# Hand-Processed Filmstrip (sprockets, scratches, chemical bloom)

The physical film strip as interface chrome: sprocket-hole rails frame every component, and hand-processing artifacts - scratches, chemical stains, light leaks, burnt edges - become the surface treatment.

## Physical behavior

**Surface finish**: matte emulsion gray inside frames; deep leader black between them

**Transparency**: opaque; orange light leaks are burn-through, not translucency

**Reacts to light**: only as recorded damage - leaks and blooms are baked into the strip

**Deforms**: no, but carries abrasion - fine white emulsion scratches along the transport direction

**Age / wear**: central to the look - chemistry sepia stains, irregular bloom blotches, burnt frame edges

## Implementation strategies

```yaml
css: |
  --leader-black: #0b0b0c; --emulsion-gray: #8e9094; --silver: #d9dadc;
  --leak-orange: #ff6a1a; --chem-sepia: #7a5a3a; --burnt: #2a241f;
  /* sprocket rails: repeating punched rectangles flanking any strip-framed element */
  .strip { border-inline: 18px solid var(--leader-black); position: relative; }
  .strip::before, .strip::after { content: ""; position: absolute; top: 0; bottom: 0;
    width: 10px; background: repeating-linear-gradient(to bottom,
      transparent 0 6px, #000 6px 14px, transparent 14px 20px); }
  /* light leak: burns in from an edge, always asymmetric */
  .leak { background: radial-gradient(120% 80% at 100% 50%,
    rgba(255,106,26,0.85), rgba(255,106,26,0.25) 40%, transparent 70%);
    mix-blend-mode: screen; }
svg: |
  emulsion scratches: 1px near-vertical polylines at 5-12% white opacity;
  chemical bloom: feTurbulence-displaced blobs in sepia, irregular and clustered
webgl: |
  shader: per-frame grain + scratch streaks in transport axis + edge burn
  vignette keyed to frame boundaries, leak hue clamped to orange
raster: scanned hand-processed 16mm strips as overlay ground truth
```

## Reactive behaviors

**Light**: no - damage is fixed in the emulsion

**Highlight**: active states re-expose - the leak orange floods the component (default silver, active burned orange)

**Depth**: no

**Parallax**: strip transport - content advances frame by frame (vertical shunt), never smooth-scrolls

## Common implementation mistakes (avoid these)

- grain overlay only (grain alone is a film-grain grade; THIS material requires the physical strip - sprockets, frame lines, edge codes)
- sprocket holes as decorative dots (they are structural rails: consistent pitch, flanking the frame, punched through leader black)
- symmetric or centered light leaks (leaks enter from an edge and decay; a centered glow reads as a lens flare)
- full-color imagery inside frames (the strip is silver-gelatin mono; only leaks and chemistry bring color)
- clean strips (no scratches, no stains = unexposed stock; hand-processing is the point)

## Examples in the wild

- hand-processed 16mm experimental cinema
- contact sheets and leader-countdown title cards
- film-lab test strips with edge codes and frame numerals

## Pairs with (prototype slugs)

- `aesthetic-luxury-cinematic-dark`
- `aesthetic-corporate-grunge`
- `aesthetic-monochrome-pop-poster`
- `style-brutalist-raw`
- `recipe-editorial-magazine`

## Differentiation

- vs `material-film-grain-tri-x` / `material-film-grain-cinestill-800t`: those are photographic grain GRADES applied to an image in place; this is the physical strip as an object - sprocket rails, frame boundaries, edge codes, and processing damage as UI chrome

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

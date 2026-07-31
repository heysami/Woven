---
materialId: guilloche-security-print
name: Guilloche Security Print (passport / banknote engraving system)
family: analog
category: print
surfaceFinish: matte (crisp security paper) with embossed leather cover accents
scope: both
transparency: opaque
pairsPrototypes: [aesthetic-dark-academia, style-serif-warm-paper, style-micro-text-frame, recipe-newspaper-of-record, aesthetic-coastal-grandmother]
images:
  - src: material-guilloche-security-print.png
    reason: Material fidelity sample.
---

# Guilloche Security Print (passport / banknote engraving system)

Security-document printing as a surface language: guilloche microline lattices tint the paper, display type is engraved with hatched strokes, machine-readable OCR-B rows anchor the data layer, and visa stamps scatter across it in their own inks.

## Physical behavior

**Surface finish**: matte, crisp pale-cream security paper; cover chips are embossed grained leather with gold foil

**Transparency**: opaque; guilloche fields read as pale tints woven from hairlines

**Reacts to light**: only the foil and embossing catch light; the paper does not

**Deforms**: no

**Age / wear**: stamps accumulate; inks bleed slightly into the paper; the lattice itself never degrades

## Implementation strategies

```yaml
css: |
  --paper: #f4efe4; --burgundy: #5b0f1a; --gold: #c8a45a;
  --visa-rose: #e6c7c3; --security-green: #d7e6d0; --stamp-navy: #1e2a5a;
  /* microline fields are background tints, always behind content, never on top */
  .guilloche-field { color: var(--burgundy); opacity: 0.35; }
svg: |
  guilloche: rosette/spirograph paths - many overlapping sine-modulated ellipses,
  stroke-width 0.3-0.5px, no fill; parametric: r(t) = R + a*sin(k*t + phase)
  engraved display caps: hatch-fill via <pattern> of 0.4px parallel lines
  clipped inside the letterforms, with a solid outline stroke
typography: |
  data rows in OCR-B (or a faithful mono) with chevron fillers: "P<USA<<DOE<JOHN";
  display in engraved roman capitals; labels in small tracked caps
stamps: |
  each stamp is a rotated (-12deg to +9deg) bordered chip - oval, rect, round -
  in its OWN ink (navy, red, green, purple) at 65-85% opacity with 0.5px bleed blur
emboss: |
  cover elements: dark leather grain + inset text-shadow (0 1px 0 rgba(0,0,0,0.6),
  0 -1px 0 rgba(255,255,255,0.12)) + gold foil fill for crests
```

## Reactive behaviors

**Light**: gold foil crest and embossing shift brightness subtly with pointer angle; paper stays inert

**Highlight**: approval states arrive as a fresh stamp - rotated, inked, slightly bled

**Depth**: embossed cover only; interior pages are flat print

**Parallax**: none

## Common implementation mistakes (avoid these)

- aging the paper (security stock is crisp and pale; foxing and stains belong to parchment, not passports)
- stamps aligned to the grid (scatter, rotation, and overlap are what make stamps read as accumulated travel)
- guilloche as a raster texture (it must be vector hairlines; a photo tile moires and pixelates on zoom)
- one ink for all stamps (every stamp carries its own ink color and its own geometry)
- guilloche drawn over content (the lattice is an under-layer tint; content prints on top of it)
- skipping the machine-readable register (the OCR-B rows with < fillers are half the document's identity)

## Examples in the wild

- passport data and visa pages
- banknote and bond-certificate engraving
- stock certificates and diplomas with rosette borders

## Pairs with (prototype slugs)

- `aesthetic-dark-academia`
- `style-serif-warm-paper`
- `style-micro-text-frame`
- `recipe-newspaper-of-record`
- `aesthetic-coastal-grandmother`

## Differentiation

- vs `material-parchment`: parchment is an aged organic sheet - warm, mottled, historied; security print is precision anti-forgery engineering on crisp modern paper - microlines, machine rows, and controlled inks

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

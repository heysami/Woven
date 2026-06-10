---
materialId: ceramic-glaze
name: Ceramic Glaze (high-gloss porcelain finish)
family: digital
category: ceramic
surfaceFinish: glossy
transparency: opaque
pairsPrototypes: [style-skeuomorphism (porcelain mascot), aesthetic-cottagecore (enamelware)]
images:
  - src: material-ceramic-glaze.png
    reason: Material fidelity sample.
---

# Ceramic Glaze (high-gloss porcelain finish)

A glossy surface that reacts to light: yes — sharp specular sweep.

## Physical behavior

**Surface finish**: glossy

**Transparency**: opaque

**Reacts to light**: yes — sharp specular sweep

**Deforms**: no

**Age / wear**: ageless

## Implementation strategies

```yaml
css: |
  background:
    radial-gradient(circle at 30% 20%, rgba(255,255,255,0.65), transparent 35%),
    linear-gradient(135deg, oklch(75% 0.06 200) 0%, oklch(60% 0.08 200) 100%);
  box-shadow: 0 12px 32px -8px rgba(0,0,0,0.25);
  border-radius: 50%;
raster: optional photo of real ceramic at 8% multiply
```

## Reactive behaviors

**Light**: highlight tracks pointer at 0.5× pointer speed

**Highlight**: --hl-x/--hl-y custom props update specular position

**Depth**: minimal — glaze is hard

**Parallax**: none

## Common implementation mistakes (avoid these)

- matte fill (ceramic without glaze isn't ceramic — it's terracotta)
- off-centre highlight stuck at fixed position

## Examples in the wild

- Apple memoji ceramic mode
- 3D-icon stocks (Iconscout)

## Pairs with (prototype slugs)

- `style-skeuomorphism (porcelain mascot)`
- `aesthetic-cottagecore (enamelware)`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

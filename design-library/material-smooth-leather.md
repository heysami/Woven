---
materialId: smooth-leather
name: Smooth Leather (full-grain, polished)
family: analog
category: leather
surfaceFinish: semi-gloss
transparency: opaque
pairsPrototypes: [style-skeuomorphism, aesthetic-dark-academia]
images:
  - src: material-smooth-leather.png
    reason: Material fidelity sample.
---

# Smooth Leather (full-grain, polished)

A semi-gloss surface that reacts to light: yes - soft specular sweep and deforms: yes.

## Physical behavior

**Surface finish**: semi-gloss

**Transparency**: opaque

**Reacts to light**: yes - soft specular sweep

**Deforms**: yes

**Age / wear**: acquired patina

## Implementation strategies

```yaml
css: |
  background:
    linear-gradient(115deg, rgba(255,255,255,0.10) 0%, transparent 35%),
    oklch(40% 0.08 40);
svg: subtle <feTurbulence> at 0.4 baseFrequency for grain
raster: scanned smooth leather
```

## Reactive behaviors

**Light**: soft specular tracks pointer at low intensity

**Highlight**: yes

**Depth**: hover lift; press inset

**Parallax**: minimal

## Common implementation mistakes (avoid these)

- matte uniform (smooth leather always has subtle sheen)
- no grain variation

## Examples in the wild

- iBooks library shelf
- high-end notebook covers

## Pairs with (prototype slugs)

- `style-skeuomorphism`
- `aesthetic-dark-academia`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

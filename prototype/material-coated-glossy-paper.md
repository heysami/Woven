---
materialId: coated-glossy-paper
name: Coated Glossy Paper (magazine cover stock)
family: analog
category: paper
surfaceFinish: glossy
transparency: opaque
pairsPrototypes: [recipe-editorial-magazine, aesthetic-y2k-memphis-loud, aesthetic-coastal-grandmother]
---

# Coated Glossy Paper (magazine cover stock)

A glossy surface that reacts to light: yes — specular sheen and deforms: minimal.

## Physical behavior

**Surface finish**: glossy

**Transparency**: opaque

**Reacts to light**: yes — specular sheen

**Deforms**: minimal

**Age / wear**: ageless (or shows fingerprints)

## Implementation strategies

```yaml
css: |
  background:
    linear-gradient(115deg, rgba(255,255,255,0.18) 0%, transparent 35%),
    url('coated-paper-1024.jpg') center/512px,
    oklch(98% 0.005 80);
  background-blend-mode: overlay, multiply, normal;
raster: scanned coated stock; finer grain than uncoated
```

## Reactive behaviors

**Light**: glossy sheen tracks pointer at low intensity

**Highlight**: yes (linear sweep on hover, 0.2 opacity)

**Depth**: minimal

**Parallax**: minimal

## Common implementation mistakes (avoid these)

- the same fibers as uncoated (coated is much smoother)
- missing the sheen on hover

## Examples in the wild

- Vogue covers
- National Geographic
- airline in-flight magazines

## Pairs with (prototype slugs)

- `recipe-editorial-magazine`
- `aesthetic-y2k-memphis-loud`
- `aesthetic-coastal-grandmother`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

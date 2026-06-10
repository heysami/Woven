---
materialId: paper-with-watercolor
name: Paper with Watercolor (botanical illustration substrate)
family: hybrid
category: paper
surfaceFinish: matte
transparency: translucent (washes)
pairsPrototypes: [aesthetic-cottagecore, aesthetic-coastal-grandmother, aesthetic-fairycore]
---

# Paper with Watercolor (botanical illustration substrate)

A matte surface (translucent (washes)) and deforms: yes.

## Physical behavior

**Surface finish**: matte

**Transparency**: translucent (washes)

**Reacts to light**: no

**Deforms**: yes

**Age / wear**: shows wear

## Implementation strategies

```yaml
css: |
  background: var(--paper);
svg: |
  paper grain layer + watercolor wash filter layer; multiply blend
raster: scanned watercolor on watercolor paper
```

## Reactive behaviors

**Light**: no

**Highlight**: no

**Depth**: no

**Parallax**: paper static; wash subtle scroll-bind

## Common implementation mistakes (avoid these)

- watercolor without paper texture (looks plastic)
- watercolor with hard edges

## Examples in the wild

- Beatrix Potter
- children's book illustration

## Pairs with (prototype slugs)

- `aesthetic-cottagecore`
- `aesthetic-coastal-grandmother`
- `aesthetic-fairycore`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

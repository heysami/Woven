---
materialId: kraft-paper
name: Kraft Paper (brown unbleached cardstock)
family: analog
category: paper
surfaceFinish: matte
transparency: opaque
pairsPrototypes: [aesthetic-cottagecore, aesthetic-cottagegoth, aesthetic-goblincore, recipe-newspaper-of-record]
---

# Kraft Paper (brown unbleached cardstock)

A matte surface and deforms: yes — wrinkles, tears.

## Physical behavior

**Surface finish**: matte

**Transparency**: opaque

**Reacts to light**: no specular

**Deforms**: yes — wrinkles, tears

**Age / wear**: shows wear (creases at fold)

## Implementation strategies

```yaml
css: |
  background:
    url('kraft-fibre-1024.jpg') center/384px,
    oklch(60% 0.06 60);  /* warm brown */
  background-blend-mode: multiply;
raster: scan of real brown kraft; visible long fibers
```

## Reactive behaviors

**Light**: no specular

**Highlight**: minimal

**Depth**: yes — paper can curl

**Parallax**: minimal

## Common implementation mistakes (avoid these)

- kraft as a solid brown swatch (it needs visible fibers)
- clean rectangular crop (kraft tears on edges)

## Examples in the wild

- Aesop product wrap
- Trader Joe's bag aesthetic
- small-batch coffee bag fronts

## Pairs with (prototype slugs)

- `aesthetic-cottagecore`
- `aesthetic-cottagegoth`
- `aesthetic-goblincore`
- `recipe-newspaper-of-record`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

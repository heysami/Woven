---
materialId: legal-pad
name: Legal Pad (ruled yellow paper)
family: analog
category: paper
surfaceFinish: matte
transparency: opaque
pairsPrototypes: [style-skeuomorphism (notes-as-legal-pad), aesthetic-dark-academia, recipe-newspaper-of-record]
---

# Legal Pad (ruled yellow paper)

A matte surface and deforms: yes — pages tear from spiral.

## Physical behavior

**Surface finish**: matte

**Transparency**: opaque

**Reacts to light**: no

**Deforms**: yes — pages tear from spiral

**Age / wear**: shows wear

## Implementation strategies

```yaml
css: |
  background:
    repeating-linear-gradient(180deg,
      transparent 0px,
      transparent 21px,
      #D9C46B 22px
    ),
    linear-gradient(90deg,
      transparent 0px,
      transparent 47px,
      #C44 48px,
      #C44 49.5px,
      transparent 50px
    ),
    #F8E9A4;
raster: optional yellow-pad scan
```

## Reactive behaviors

**Light**: no

**Highlight**: no

**Depth**: corner curl on hover

**Parallax**: minimal

## Common implementation mistakes (avoid these)

- lines that don't go full-bleed
- missing red margin line
- perfect type instead of handwriting

## Examples in the wild

- iOS 6 Notes app
- office-supply photography

## Pairs with (prototype slugs)

- `style-skeuomorphism (notes-as-legal-pad)`
- `aesthetic-dark-academia`
- `recipe-newspaper-of-record`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

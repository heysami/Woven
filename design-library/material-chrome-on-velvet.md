---
materialId: chrome-on-velvet
name: Chrome on Velvet (Y2K luxury substrate)
family: hybrid
category: metal
surfaceFinish: metallic (chrome) on matte (velvet)
transparency: opaque
pairsPrototypes: [aesthetic-urbling, aesthetic-defi-cosmic, aesthetic-y2k-futurism, style-holographic]
images:
  - src: material-chrome-on-velvet.png
    reason: Material fidelity sample.
---

# Chrome on Velvet (Y2K luxury substrate)

A metallic (chrome) on matte (velvet) surface that reacts to light: yes - strong.

## Physical behavior

**Surface finish**: metallic (chrome) on matte (velvet)

**Transparency**: opaque

**Reacts to light**: yes - strong

**Deforms**: no

**Age / wear**: ageless

## Implementation strategies

```yaml
css: |
  /* chrome chip atop a deeply textured velvet background */
  background:
    radial-gradient(ellipse at 50% 50%, oklch(15% 0.02 320) 0%, oklch(8% 0.01 320) 100%);
  filter: url(#velvetNap);  /* on the substrate only */
raster: velvet substrate scan + chrome objects
```

## Reactive behaviors

**Light**: chrome reacts; velvet does not

**Highlight**: yes - strong on chrome

**Depth**: no

**Parallax**: minimal

## Common implementation mistakes (avoid these)

- velvet that looks like flat dark grey
- chrome at low saturation

## Examples in the wild

- hip-hop album-cover lineage
- luxury watch ads

## Pairs with (prototype slugs)

- `aesthetic-urbling`
- `aesthetic-defi-cosmic`
- `aesthetic-y2k-futurism`
- `style-holographic`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

---
materialId: aurora-mesh
name: Aurora Mesh Gradient (Stripe / Vercel / Linear)
family: digital
category: digital-effect
surfaceFinish: glossy
transparency: translucent
pairsPrototypes: [style-aurorism, recipe-aurora-marketing, aesthetic-frutiger-aero, aesthetic-frutiger-dark-aero]
images:
  - src: material-aurora-mesh.png
    reason: Material fidelity sample.
---

# Aurora Mesh Gradient (Stripe / Vercel / Linear)

A glossy surface (translucent).

## Physical behavior

**Surface finish**: glossy

**Transparency**: translucent

**Reacts to light**: no — it is the light

**Deforms**: no

**Age / wear**: ageless

## Implementation strategies

```yaml
css: |
  .aurora {
    position: relative;
    background: #fafafa;
  }
  .aurora::before {
    content: '';
    position: absolute; inset: 0;
    background:
      radial-gradient(at 20% 30%, oklch(70% 0.20 220) 0%, transparent 50%),
      radial-gradient(at 80% 20%, oklch(75% 0.22 340) 0%, transparent 50%),
      radial-gradient(at 50% 80%, oklch(80% 0.18 60) 0%, transparent 50%);
    filter: blur(80px);
    opacity: 0.75;
  }
svg: noise overlay at 4–8% opacity to kill banding
webgl: minigl noise loop for single-WebGL alternative
raster: optional grain texture multiply
```

## Reactive behaviors

**Light**: blobs drift on a 12s + 8s counter-rotation

**Highlight**: none — the mesh IS the highlight

**Depth**: none

**Parallax**: very subtle on scroll (0.4× scroll speed)

## Common implementation mistakes (avoid these)

- full saturation rainbow blobs (no falloff)
- no blur (banding visible)
- mesh repeated in every section (it's a singular event)
- emoji or icons over the mesh
- second gradient on the CTA

## Examples in the wild

- Stripe homepage
- Linear marketing
- Vercel prism
- Cron / Notion Calendar

## References

- https://css-tricks.com/grainy-gradients/
- https://dev.to/albertwalicki/aurora-ui-how-to-create-with-css-4b6g

## Pairs with (prototype slugs)

- `style-aurorism`
- `recipe-aurora-marketing`
- `aesthetic-frutiger-aero`
- `aesthetic-frutiger-dark-aero`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this material -->

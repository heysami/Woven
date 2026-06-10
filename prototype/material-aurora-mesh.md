# Aurora Mesh Gradient (Stripe / Vercel / Linear) (material)

**Tag:** material-aurora-mesh  ·  **Family:** digital  ·  **Category:** digital-effect · glossy

A glossy digital surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: aurora-mesh
  name: Aurora Mesh Gradient (Stripe / Vercel / Linear)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: glossy
    transparency: translucent
    reactsToLight: no — it is the light
    deforms: no
    age: ageless
  implementationStrategies:
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
  reactiveBehaviors:
    light: blobs drift on a 12s + 8s counter-rotation
    highlight: none — the mesh IS the highlight
    depth: none
    parallax: very subtle on scroll (0.4× scroll speed)
  pairsWith:
    prototypeStyles: [style-aurorism, recipe-aurora-marketing, aesthetic-frutiger-aero, aesthetic-frutiger-dark-aero]
  killsTheIllusion:
    - full saturation rainbow blobs (no falloff)
    - no blur (banding visible)
    - mesh repeated in every section (it's a singular event)
    - emoji or icons over the mesh
    - second gradient on the CTA
  examples:
    - Stripe homepage
    - Linear marketing
    - Vercel prism
    - Cron / Notion Calendar
  references:
    - https://css-tricks.com/grainy-gradients/
    - https://dev.to/albertwalicki/aurora-ui-how-to-create-with-css-4b6g
```

## Common implementation mistakes (avoid these)

- full saturation rainbow blobs (no falloff)
- no blur (banding visible)
- mesh repeated in every section (it's a singular event)

## Pairs with (prototype slugs)

- `style-aurorism`
- `recipe-aurora-marketing`
- `aesthetic-frutiger-aero`
- `aesthetic-frutiger-dark-aero`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 698–748 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

# Liquid Glass (Apple WWDC25) (material)

**Tag:** material-liquid-glass  ·  **Family:** digital  ·  **Category:** glass · glossy

A glossy digital surface.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/material-library.md`](../docs/research/material-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- materialId: liquid-glass
  name: Liquid Glass (Apple WWDC25)
  family: digital
  category: glass
  physicalBehavior:
    surfaceFinish: glossy
    transparency: transparent
    reactsToLight: yes — specular highlight tracks tilt/pointer; chromatic edge
    deforms: minor on press
    age: ageless
  implementationStrategies:
    css: |
      backdrop-filter: blur(20px) saturate(180%) brightness(108%);
      background: rgba(255,255,255,0.12);
      border: 0.5px solid rgba(255,255,255,0.30);
      box-shadow:
        inset 0 1px 0 rgba(255,255,255,0.75),
        inset 0 -1px 0 rgba(255,255,255,0.10),
        0 1px 2px rgba(0,0,0,0.08),
        0 8px 24px -12px rgba(0,0,0,0.18);
      border-radius: 9999px;   /* pills for nav; 22px concentric for cards */
    svg: |
      <filter id="liquidRefract">
        <feTurbulence type="fractalNoise" baseFrequency="0.012 0.018" numOctaves="2"/>
        <feDisplacementMap in="SourceGraphic" scale="20"/>
        <feGaussianBlur stdDeviation="1"/>
      </filter>
      /* Apply to chrome shapes ONLY — text becomes illegible above scale=20 */
    webgl: |
      Real-time variant: sample the page-behind-canvas as a render-target, do
      fragment-shader refraction (UV offset by gradient of pressed region) at
      30fps. WebGL2 + drawingBufferStorage. ~3ms/frame budget.
    raster: substrate required (photo / map / multi-stop gradient)
    video: video underlay works (live wallpapers)
  reactiveBehaviors:
    light: |
      specular highlight subtly shifts 2–4px on `pointermove` or
      `DeviceOrientationEvent`. Update --hl-x and --hl-y CSS custom props.
    highlight: |
      element.addEventListener('pointermove', e => {
        const r = el.getBoundingClientRect();
        el.style.setProperty('--hl-x', (e.clientX - r.left) / r.width);
        el.style.setProperty('--hl-y', (e.clientY - r.top) / r.height);
      });
      /* CSS: background-position: calc(var(--hl-x) * 100%) calc(var(--hl-y) * 100%); */
    depth: press 250ms cubic-bezier(0.32,0.72,0,1) — controls morph via FLIP into one continuous shape
    parallax: shells the substrate parallaxes; the glass tracks viewport
  pairsWith:
    prototypeStyles: [style-liquid-glass, style-glassmorphism, aesthetic-frutiger-aero, aesthetic-frutiger-dark-aero, aesthetic-holographic, aesthetic-y2k-futurism]
  killsTheIllusion:
    - displacement map applied to text (illegible)
    - displacement scale > 30 (text swims even on chrome)
    - glass nested inside glass (HIG explicitly forbids it)
    - brand colour baked into the fill instead of inherited from content
    - conic-gradient rainbow rotation on the rim (TikTok-glass tell)
    - autoplay shine sweeps
  examples:
    - iOS 26 system
    - Apple Music 2025
    - visionOS Glass Materials
    - Halide camera app
  references:
    - https://developer.apple.com/videos/play/wwdc2025/219/
    - https://en.wikipedia.org/wiki/Liquid_Glass
```

## Common implementation mistakes (avoid these)

- displacement map applied to text (illegible)
- displacement scale > 30 (text swims even on chrome)
- glass nested inside glass (HIG explicitly forbids it)

## Pairs with (prototype slugs)

- `style-liquid-glass`
- `style-glassmorphism`
- `aesthetic-frutiger-aero`
- `aesthetic-frutiger-dark-aero`
- `aesthetic-holographic`
- `aesthetic-y2k-futurism`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 120–184 of `docs/research/material-library.md`. Full index: `docs/research/material-library.index.json`._

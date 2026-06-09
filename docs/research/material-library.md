# Material Library — research dossier for material-orchestrator

> Canonical reference for the `material-orchestrator` subagent. The orchestrator walks source HTML, identifies elements that wear a material aesthetic (glassmorphism / claymorphism / paper / fabric / risograph / film grain / etc.), and commits a fidelity pass that makes the material FEEL like the real thing — including reactive behaviour to light direction, pointer, device tilt, scroll.
>
> Quality > breadth. Each entry is IMPLEMENTABLE TODAY by a competent frontend developer using only the snippets and citations below — no external assets unless noted.

---

## 1. Material principles

A material has FELT physical properties. The web fakes those properties by combining (a) a luminance model — how light enters, scatters, exits — with (b) a substrate model — what's beneath, what's pressed, what's torn. The orchestrator's job is to commit BOTH per material instance, not just paint a surface colour.

### 1.1 Light interaction by surface finish

- **Matte (uncoated paper, raw cotton, unglazed clay, suede).** Light is absorbed and scattered diffusely; no specular highlight is visible. The web move is to AVOID `box-shadow` with strong specular layers, AVOID gloss gradients, ADD micro-texture (`<feTurbulence>` at high baseFrequency) at low opacity (3–8%) to break the perfect plane. Matte materials read as matte because they have NO highlight — adding one kills the illusion.
- **Glossy (varnished wood, ceramic glaze, polished plastic, fresh ink on coated paper).** Light bounces off the surface in a coherent specular reflection. The web move is a SINGLE top-edge highlight, usually a `linear-gradient(180deg, rgba(255,255,255,0.4) 0%, transparent 45%)` masked to the top half — never full-height. The canonical iOS-6 / Frutiger Aero "wet button" gloss covers the top 45%; covering the full height collapses the read to "generic gradient button".
- **Textured (oatmeal paper, linen, brick, concrete, burlap).** Light scatters at micro-scale; the texture reads at the resolution of the screen. The web move is a tile pattern (PNG or SVG `<pattern>`) at 30–60% scale so the weave/grain is legible. A texture larger than the element prints as a single colour swatch.
- **Semi-gloss (eggshell paint, satin photo paper, polished concrete).** A weak specular under a diffuse base. The web move is a low-opacity gloss gradient (`linear-gradient(...) at opacity 0.10–0.18`) layered over a textured substrate.
- **Metallic (chrome, brushed aluminium, gold leaf, copper patina).** Light is reflected coherently (specular) AND the colour gradient depends on the angle to the viewer. Real metal needs an ENVIRONMENT MAP — chrome reflects "something nearby", which on the web is faked with a captured photograph of an indoor scene tinted to the metal's hue. A solid silver gradient without an environment lookup reads as plastic.
- **Iridescent (Pokemon foil, oil-on-water, butterfly wing, soap bubble).** Light splits into wavelengths because the surface has microscale thickness variations. The hue depends on angle — Pokemon-card iridescence shifts cyan→magenta→gold as you tilt. The web move is a `conic-gradient` in OKLCH for perceptual smoothness, masked into a `mix-blend-mode: color-dodge` layer, with `hue-rotate(var(--tilt))` driven by pointer or gyro.

### 1.2 Depth cueing

- **Soft contact shadow vs. drop shadow:** real objects in real light cast a sharp shadow at the contact point and a softer ambient one further away. `0 1px 2px rgba(0,0,0,0.08), 0 8px 24px -12px rgba(0,0,0,0.18)` is closer to physical accuracy than a single `0 4px 12px rgba(0,0,0,0.1)`.
- **Multi-layer shadow:** the canonical claymorphism / Apple-glass / Frutiger-Aero stack is THREE layers — outer ambient, contact, and inset specular highlight. Never one layer.
- **Ambient occlusion fakery:** where one surface meets another, darken the intersection 4–6% with an inset shadow on the host element. AO sells the layering — without it, stacked surfaces float.
- **Light direction discipline:** commit ONE light direction per page (typically top-left, 315° / 10 o'clock). EVERY shadow on every element MUST agree. The single most common AI-tell is per-component shadow tuning that scrambles the light source.

### 1.3 Deformation

Materials flex. Paper bends, wrinkles, tears. Clay deforms on press. Fabric drapes. Most web "materials" are static rectangles. The orchestrator should commit a deformation budget per material:

- **Paper / cardstock:** corner curl on hover (a CSS gradient masked to a triangle in the top-right), page-flip on next/prev.
- **Clay / soft plastic:** `transform: scale(0.97)` on press; the inset shadow grows on hover to suggest finger-impression depth.
- **Fabric:** drape animation (subtle `transform: skewY(0.5deg)` on scroll, or an SVG wave on the bottom edge).
- **Glass / metal / hard plastic:** NO deformation; press = highlight shift only.
- **Liquid (mercury, water, oil-on-water):** displacement via `<feDisplacementMap>` driven by pointer.

### 1.4 Translucency and refraction

- **Translucent (vellum, frosted glass, rice paper, tracing paper):** light passes through but is scattered. CSS: `backdrop-filter: blur()`. The substrate beneath MUST be saturated/photographic — translucent material over flat white reads as fogged plastic.
- **Refraction (real glass, lens, water droplet):** light bends. The 2025 Apple Liquid Glass material uses `<feDisplacementMap scale="20">` driven by a chromatic-noise turbulence source, applied ONLY to chrome shapes (not text — text refraction = unreadable).
- **Dichroic (some films, oil slicks):** colour depends on transmission angle. Layer two `conic-gradient` at different rotations with `mix-blend-mode: difference`.
- **Layered ink (risograph, screenprint, watercolour):** each ink layer is partially transparent; overlap creates new hues via `mix-blend-mode: multiply`.

### 1.5 Surface anisotropy

Brushed metal looks different at different viewing angles because the micro-grooves run in one direction. So does corduroy, vinyl record grooves, silk satin, sandblasted glass. The web move is a directional gradient (`linear-gradient` perpendicular to the grain direction) with a perpendicular noise pattern. On tilt, the highlight stretches ALONG the grain, never across it.

### 1.6 Age and wear

Materials acquire patina. Copper greens, paper yellows, leather creases at the same handle-points. The orchestrator may commit `wearProfile: ageless | shows-wear | acquired-patina` per material. Acquired-patina materials need ASYMMETRIC distress — wear that lives where a hand or hinge would touch, not random global noise.

---

## 2. Material taxonomy

Each entry below uses YAML-in-markdown. The schema is consistent: `materialId`, `name`, `family` (digital / analog / hybrid), `category`, `physicalBehavior`, `implementationStrategies` (CSS / SVG / WebGL / raster / video), `reactiveBehaviors`, `pairsWith.prototypeStyles`, `killsTheIllusion`, `examples`, `references`.

Forty-eight entries follow, organised into Digital (§3), Analog (§4), and Hybrid (§5).

---

## 3. Digital materials

Materials defined by computation — gradients, filters, shaders. They have no analog ancestor that doesn't go through a rendering pipeline.

### 3.1 Glass family

```yaml
- materialId: frosted-glass
  name: Frosted Glass (canonical glassmorphism)
  family: digital
  category: glass
  physicalBehavior:
    surfaceFinish: glossy
    transparency: translucent
    reactsToLight: yes — top-edge specular highlight, tinted by substrate beneath
    deforms: no
    age: ageless
  implementationStrategies:
    css: |
      background: rgba(255,255,255,0.18);
      backdrop-filter: blur(24px) saturate(180%);
      -webkit-backdrop-filter: blur(24px) saturate(180%);
      border: 0.5px solid rgba(255,255,255,0.35);
      box-shadow:
        inset 0 1px 0 rgba(255,255,255,0.5),
        inset 0 0 0 1px rgba(255,255,255,0.18),
        0 8px 32px rgba(0,0,0,0.18),
        0 2px 8px rgba(0,0,0,0.08);
      border-radius: 22px;
    svg: optional fffuel-style noise overlay at 3–5% opacity to mask blur banding
    webgl: not needed for this tier
    raster: SUBSTRATE is mandatory — saturated photo or mesh-gradient beneath
    video: looping iridescent-substrate underlay is one variant
  reactiveBehaviors:
    light: substrate visible through the panel changes if the substrate moves (scroll parallax); panel itself is otherwise static
    highlight: top-edge inset highlight is fixed; on tilt the substrate shifts but the highlight does not
    depth: hover lift 2px; press scales 0.99
    parallax: substrate moves slower than glass card on scroll
  pairsWith:
    prototypeStyles: [style-glassmorphism, style-liquid-glass, aesthetic-frutiger-aero, aesthetic-frutiger-dark-aero, aesthetic-frutiger-chromecore, aesthetic-y2k-futurism, aesthetic-vaporwave, aesthetic-positivity-kawaii]
  killsTheIllusion:
    - blur on flat #fff page (refracts nothing → fogged plastic)
    - missing 1px inset white top-edge highlight (reads as sticker, not lens)
    - body text directly on glass with no vibrancy chip backing
    - 4–6px SaaS radius instead of 16–22px continuous corner
    - stacking glass-on-glass-on-glass (compounds to mush)
    - no `saturate()` boost — blur drains chroma without it, reads grey gauze
  examples:
    - macOS Big Sur sidebars
    - iOS Control Center
    - visionOS materials
    - Microsoft Fluent Acrylic
  references:
    - https://caniuse.com/css-backdrop-filter
    - https://developer.apple.com/videos/play/wwdc2025/219/

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

- materialId: thin-glass-chip
  name: Thin Glass Chip (iOS-style toggle, Control Center pill)
  family: digital
  category: glass
  physicalBehavior:
    surfaceFinish: glossy
    transparency: translucent
    reactsToLight: yes — but lighter than full glass; substrate shows through more
    deforms: no
    age: ageless
  implementationStrategies:
    css: |
      backdrop-filter: blur(12px) saturate(140%);
      background: rgba(255,255,255,0.22);
      border: 0.5px solid rgba(255,255,255,0.4);
      border-radius: 9999px;
      padding: 6px 12px;
    svg: none
    raster: requires saturated substrate
  reactiveBehaviors:
    light: substrate shifts on scroll
    highlight: subtle on hover (background opacity +0.04)
    depth: 1px lift on hover
    parallax: tracks scroll
  pairsWith:
    prototypeStyles: [style-glassmorphism, style-liquid-glass, recipe-ios-system]
  killsTheIllusion:
    - too much blur (the chip becomes invisible)
    - chip on flat solid colour with no substrate
  examples:
    - iOS Control Center toggles
    - Apple Maps mode pills

- materialId: vellum-translucency
  name: Vellum / Tracing Paper Translucency
  family: digital
  category: glass
  physicalBehavior:
    surfaceFinish: matte
    transparency: translucent
    reactsToLight: no specular — light scatters
    deforms: no
    age: ageless
  implementationStrategies:
    css: |
      background: rgba(252,250,245,0.62);
      backdrop-filter: blur(8px) saturate(80%);  /* desaturate, not boost */
      box-shadow: 0 2px 8px rgba(60,40,20,0.08);
      /* WARM tone, not cool — vellum is yellowish */
    svg: |
      <filter id="vellumGrain">
        <feTurbulence baseFrequency="0.9" numOctaves="2"/>
        <feColorMatrix values="0 0 0 0 0.95  0 0 0 0 0.93  0 0 0 0 0.88  0 0 0 0.08 0"/>
      </filter>
      /* paper-fibre noise at 8% opacity over the panel */
    raster: optional 2048px vellum scan multiplied at low opacity
  reactiveBehaviors:
    light: minimal; vellum doesn't glint
    highlight: none
    depth: 1px lift on hover only
    parallax: minimal
  pairsWith:
    prototypeStyles: [style-serif-warm-paper, aesthetic-cottagecore, aesthetic-cottagegoth, aesthetic-dark-academia]
  killsTheIllusion:
    - cool/blue blur (vellum is warm)
    - high saturate boost (vellum desaturates, doesn't intensify)
    - sharp specular highlight (matte material can't glint)
  examples:
    - architectural drawing overlays
    - wedding invitation overlays
    - Apple visionOS "Plate" material (when configured matte)
```

### 3.2 Plastic and ceramic family

```yaml
- materialId: glossy-plastic-aqua
  name: Glossy Plastic (Frutiger Aero / Apple Aqua / Windows Vista wet button)
  family: digital
  category: plastic
  physicalBehavior:
    surfaceFinish: glossy
    transparency: opaque
    reactsToLight: yes — single top-half specular gloss
    deforms: minor on press (inner shadow grows)
    age: ageless
  implementationStrategies:
    css: |
      background:
        linear-gradient(180deg,
          rgba(255,255,255,0.55) 0%,
          rgba(255,255,255,0.10) 45%,
          rgba(0,0,0,0.0) 46%,
          rgba(0,0,0,0.08) 100%
        ),
        linear-gradient(180deg, oklch(60% 0.18 240) 0%, oklch(45% 0.20 240) 100%);
      box-shadow:
        inset 0 1px 0 rgba(255,255,255,0.7),
        inset 0 -1px 0 rgba(0,0,0,0.15),
        0 1px 3px rgba(0,0,0,0.25),
        0 4px 12px rgba(0,0,0,0.12);
      border-radius: 14px;
    raster: optional photographic plate beneath the button group (sky / water)
  reactiveBehaviors:
    light: highlight is fixed (button has one canonical light); subtle background shift on scroll
    highlight: hover increases the top-half gloss opacity 0.05
    depth: press inverts the inner shadow (raised → inset)
    parallax: substrate parallaxes if photographic plate is present
  pairsWith:
    prototypeStyles: [aesthetic-frutiger-aero, aesthetic-y2k-futurism, aesthetic-frutiger-chromecore, style-skeuomorphism]
  killsTheIllusion:
    - gloss covers full height (collapses to generic gradient)
    - flat solid colour with no gradient
    - cool greyscale instead of saturated colour
    - sharp drop shadow with no inset highlight
    - >40% lightness step (reads plastic-toy)
  examples:
    - iOS 1–6 lozenge icons
    - Windows Vista Start button
    - Apple Aqua buttons
  references:
    - https://en.wikipedia.org/wiki/Aqua_(user_interface)

- materialId: matte-clay
  name: Matte Clay (claymorphism)
  family: digital
  category: clay
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: yes — inset highlight + dark inset shadow
    deforms: minor on press (squash)
    age: ageless
  implementationStrategies:
    css: |
      background: oklch(85% 0.08 50);   /* peach pastel */
      border-radius: 32px;
      box-shadow:
        8px 8px 16px 0 oklch(50% 0.04 50 / 0.18),
        inset -6px -6px 12px 0 oklch(45% 0.06 50 / 0.22),
        inset 8px 8px 12px 0 oklch(100% 0 0 / 0.45);
      /* RULE: outer offset = inner offset, blur = 2× offset; outer shadow tinted with surface hue, NEVER black */
    svg: none
    raster: none
  reactiveBehaviors:
    light: shadow remains static (light source committed)
    highlight: hover scales 1.03 + translateY(-2px) with cubic-bezier(0.34, 1.56, 0.64, 1) overshoot
    depth: press scales 0.97 + inverts the inner highlight
    parallax: none — clay is grounded
  pairsWith:
    prototypeStyles: [style-claymorphism, aesthetic-positivity-kawaii, aesthetic-frutiger-eco, aesthetic-corporate-memphis]
  killsTheIllusion:
    - every container puffed (clay must be ONE moment per screen)
    - saturated 0.20+ chroma instead of 0.04–0.08 pastels
    - dark bottom-right inset shadow missing (reads flat pill with glow)
    - black drop shadow instead of surface-hue-tinted
    - clay extended to dark mode (inset highlight stops reading)
  examples:
    - Coursera 2022 rebrand
    - Pitch key visuals
    - Matter app
    - clay.css by Adrian Bece
  references:
    - https://hype4.academy/articles/coding/how-to-create-claymorphism-using-css
    - https://blog.openreplay.com/implementing-claymorphism-with-css/

- materialId: soft-ui-foam
  name: Soft UI / Neumorphic Foam
  family: digital
  category: clay
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: yes — dual highlight + shadow
    deforms: yes (raised ↔ pressed)
    age: ageless
  implementationStrategies:
    css: |
      /* Container background MUST equal page background */
      background: #E0E5EC;
      border-radius: 28px;
      box-shadow:
        9px 9px 16px #A3B1C6,
        -9px -9px 16px #FFFFFF;
      /* Pressed variant */
      .pressed {
        box-shadow:
          inset 6px 6px 12px #A3B1C6,
          inset -6px -6px 12px #FFFFFF;
      }
    raster: none
  reactiveBehaviors:
    light: single committed light direction (top-left); never deviates
    highlight: shadow blur 16 → 20 on hover
    depth: 180ms ease-out swap to inset on press
    parallax: none
  pairsWith:
    prototypeStyles: [style-neumorphism, aesthetic-frutiger-tranquil-serenity, aesthetic-positivity-kawaii, aesthetic-frutiger-eco]
  killsTheIllusion:
    - pure #FFF or #000 background (kills one shadow)
    - symmetric shadows with no implied light source
    - per-component shadow tuning (light jumps around)
    - sharp <12px radii (breaks soft-plastic read)
    - text or icons extruded (only containers extrude)
  examples:
    - Alexander Plyuto Skeuomorph Bank 2019
    - neumorphism.io
  references:
    - https://neumorphism.io/

- materialId: ceramic-glaze
  name: Ceramic Glaze (high-gloss porcelain finish)
  family: digital
  category: ceramic
  physicalBehavior:
    surfaceFinish: glossy
    transparency: opaque
    reactsToLight: yes — sharp specular sweep
    deforms: no
    age: ageless
  implementationStrategies:
    css: |
      background:
        radial-gradient(circle at 30% 20%, rgba(255,255,255,0.65), transparent 35%),
        linear-gradient(135deg, oklch(75% 0.06 200) 0%, oklch(60% 0.08 200) 100%);
      box-shadow: 0 12px 32px -8px rgba(0,0,0,0.25);
      border-radius: 50%;
    raster: optional photo of real ceramic at 8% multiply
  reactiveBehaviors:
    light: highlight tracks pointer at 0.5× pointer speed
    highlight: --hl-x/--hl-y custom props update specular position
    depth: minimal — glaze is hard
    parallax: none
  pairsWith:
    prototypeStyles: [style-skeuomorphism (porcelain mascot), aesthetic-cottagecore (enamelware)]
  killsTheIllusion:
    - matte fill (ceramic without glaze isn't ceramic — it's terracotta)
    - off-centre highlight stuck at fixed position
  examples:
    - Apple memoji ceramic mode
    - 3D-icon stocks (Iconscout)
```

### 3.3 Metal family

```yaml
- materialId: chrome-mirror
  name: Chrome Mirror (Y2K chromecore / cyber-sigil)
  family: digital
  category: metal
  physicalBehavior:
    surfaceFinish: metallic
    transparency: opaque
    reactsToLight: yes — environment reflection, hue shift with angle
    deforms: no
    age: ageless
  implementationStrategies:
    css: |
      background:
        linear-gradient(180deg,
          #f7f7fa 0%,
          #8a8d96 35%,
          #4e525c 55%,
          #c5c8d2 80%,
          #f7f7fa 100%
        );
      /* Chrome read demands a HORIZON-BANDED gradient — not a smooth one */
      box-shadow:
        inset 0 1px 0 rgba(255,255,255,0.9),
        inset 0 -1px 0 rgba(0,0,0,0.5),
        0 2px 4px rgba(0,0,0,0.3);
      border-radius: 999px;
    svg: optional `<feSpecularLighting>` for high-fidelity
    webgl: cube-map environment lookup for the highest-fidelity chrome
    raster: captured indoor environment photo (4096×2048 equirectangular)
  reactiveBehaviors:
    light: horizon line shifts position with pointer; chrome inverts top↔bottom
    highlight: |
      element.style.setProperty('--horizon', 30 + e.clientY/window.innerHeight * 40 + '%');
      /* gradient stops snap to --horizon */
    depth: no deformation; metal is hard
    parallax: cube-map rotates on `DeviceOrientationEvent`
  pairsWith:
    prototypeStyles: [aesthetic-frutiger-chromecore, aesthetic-y2k-futurism, style-holographic, aesthetic-cyberpunk, aesthetic-urbling]
  killsTheIllusion:
    - smooth grey gradient (chrome is BANDED — sky-on-top, ground-on-bottom)
    - no inset highlight at the seam between bands
    - chrome on a colourful chaotic page (the reflection has to be coherent)
  examples:
    - Y2K Gucci silver
    - Boiler Room 2024 identity
    - Daniel Arsham Drift jewelry mark
  references:
    - https://www.happy-digital.com/freebies/tip_chrome.html

- materialId: brushed-aluminum
  name: Brushed Aluminum (anisotropic metal)
  family: digital
  category: metal
  physicalBehavior:
    surfaceFinish: semi-gloss
    transparency: opaque
    reactsToLight: yes — anisotropic highlight perpendicular to brush direction
    deforms: no
    age: shows wear (scratches deepen)
  implementationStrategies:
    css: |
      background:
        repeating-linear-gradient(90deg,
          rgba(255,255,255,0.06) 0px,
          rgba(0,0,0,0.06) 1px,
          rgba(255,255,255,0.06) 2px
        ),
        linear-gradient(180deg, #d6d8db 0%, #a8abb1 100%);
      box-shadow:
        inset 0 1px 0 rgba(255,255,255,0.4),
        inset 0 -1px 0 rgba(0,0,0,0.3),
        0 1px 2px rgba(0,0,0,0.2);
    svg: |
      <filter id="brushed">
        <feTurbulence type="turbulence" baseFrequency="0.8 0.01" numOctaves="2"/>
        <feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 0.18 0"/>
      </filter>
      /* baseFrequency x ≫ y → directional grain */
    raster: 2048px scan of real brushed metal at 0.18 opacity multiply
  reactiveBehaviors:
    light: highlight stretches ALONG the grain direction on tilt (90deg), never across
    highlight: pointer tracks but highlight is elongated
    depth: hairline scratch overlay reveals at hover
    parallax: minimal
  pairsWith:
    prototypeStyles: [aesthetic-cassette-futurism, aesthetic-dieselpunk, aesthetic-steampunk, style-skeuomorphism (recorder-as-tape-deck)]
  killsTheIllusion:
    - isotropic noise instead of directional grain
    - brushed pattern at huge scale (the grain has to be sub-mm)
    - circular highlight instead of elongated one
  examples:
    - iPod nano body
    - MacBook Pro casing
    - Sony WALKMAN front face

- materialId: gold-leaf
  name: Gold Leaf (rich warm metal)
  family: digital
  category: metal
  physicalBehavior:
    surfaceFinish: metallic
    transparency: opaque
    reactsToLight: yes — warm specular, slight wrinkle
    deforms: no
    age: acquired patina
  implementationStrategies:
    css: |
      background:
        linear-gradient(180deg,
          oklch(95% 0.10 90) 0%,
          oklch(70% 0.14 75) 50%,
          oklch(50% 0.12 60) 100%
        );
      box-shadow:
        inset 0 1px 0 rgba(255,250,210,0.9),
        inset 0 -1px 0 rgba(80,40,0,0.5),
        0 2px 6px rgba(80,40,0,0.3);
    svg: |
      crinkle texture via <feTurbulence> baseFrequency="0.04" numOctaves="3"
      blended at mix-blend-mode: overlay, opacity 0.25
    raster: scanned gold-leaf texture at 1024px tile, multiplied
  reactiveBehaviors:
    light: warm highlight tracks pointer; on tilt, deep amber shadows emerge
    highlight: yes via pointer
    depth: no
    parallax: minimal
  pairsWith:
    prototypeStyles: [aesthetic-dark-academia, aesthetic-defi-cosmic, aesthetic-urbling, style-holographic]
  killsTheIllusion:
    - cool-white gold (gold is warm — pull hue toward 80–90 in OKLCH)
    - smooth perfect surface (real gold leaf wrinkles)
  examples:
    - religious iconography
    - Nike Mag chrome
    - DeFi-cosmic certificate cards

- materialId: copper-patina
  name: Copper with Verdigris Patina
  family: digital
  category: metal
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: yes — but the patina kills most specular
    deforms: no
    age: acquired patina
  implementationStrategies:
    css: |
      background:
        radial-gradient(ellipse at 30% 20%, oklch(60% 0.14 35) 0%, transparent 35%),
        radial-gradient(ellipse at 70% 80%, oklch(70% 0.08 165) 0%, transparent 45%),
        oklch(40% 0.10 35);  /* copper base */
    svg: |
      patina spots — <feTurbulence baseFrequency="0.02"/> + <feColorMatrix> tinted toward verdigris green
    raster: real-world copper-patina photograph as the truth
  reactiveBehaviors:
    light: highlight only on un-patinated areas (use mask)
    highlight: minimal — patina absorbs light
    depth: none
    parallax: none
  pairsWith:
    prototypeStyles: [aesthetic-steampunk, aesthetic-dieselpunk, aesthetic-solarpunk, aesthetic-dark-academia]
  killsTheIllusion:
    - uniform green (real patina is ASYMMETRIC, lives in crevices)
    - bright orange copper (it tarnishes within weeks)
  examples:
    - Statue of Liberty
    - vintage scientific instruments
```

### 3.4 Iridescent and dichroic family

```yaml
- materialId: holographic-foil
  name: Holographic Foil (Pokemon card / Apple Pay Cash)
  family: digital
  category: iridescent
  physicalBehavior:
    surfaceFinish: glossy
    transparency: opaque
    reactsToLight: yes — full spectrum hue shift on angle
    deforms: no
    age: ageless
  implementationStrategies:
    css: |
      background:
        conic-gradient(
          in oklch from 45deg,
          oklch(85% 0.10 200),
          oklch(82% 0.11 310),
          oklch(88% 0.09 60),
          oklch(84% 0.10 155),
          oklch(85% 0.10 200)
        );
      filter: hue-rotate(calc(var(--px,0) * 25deg));
      transform: rotateX(calc(var(--py,0) * 8deg)) rotateY(calc(var(--px,0) * 8deg));
      mix-blend-mode: color-dodge;  /* atop a dark substrate */
    svg: |
      grain noise overlay at 4% to break the conic bands
    webgl: |
      fragment shader: sample HDR environment cubemap, modulate by surface
      angle; gives true Pokemon-card foil. ~5ms/frame budget on M-series.
    raster: oil-on-water iridescent photographs for the highest fidelity
  reactiveBehaviors:
    light: hue rotates ±25deg on pointer X; rotateY/rotateX on pointer
    highlight: yes (the conic gradient IS the highlight)
    depth: hover scale 1.02; press 0.98
    parallax: gyro-driven on mobile via DeviceOrientationEvent
  pairsWith:
    prototypeStyles: [style-holographic, aesthetic-frutiger-chromecore, aesthetic-y2k-futurism, aesthetic-vaporwave, style-liquid-glass]
  killsTheIllusion:
    - conic-gradient(#f0f, #0ff, #ff0, #f0f) in sRGB — muddy brown bands at cyan→magenta
    - autoplay 2s infinite hue-rotate spin (epileptic + tells "AI generated")
    - iridescence on body type or form inputs
    - light substrate (kills the specular — iridescence needs dark backing)
    - full 360° hue traversal (real iridescence travels 40–50° arc)
  examples:
    - Apple Pay Cash
    - Apple TV+ 2025 rebrand
    - poke-holo.simey.me reverse-engineered Pokemon
    - Boiler Room 2024 identity
  references:
    - https://poke-holo.simey.me/
    - https://github.com/simeydotme/pokemon-cards-css

- materialId: oil-on-water
  name: Oil-on-Water Iridescence (organic dichroic)
  family: digital
  category: iridescent
  physicalBehavior:
    surfaceFinish: glossy
    transparency: translucent
    reactsToLight: yes — chaotic hue swirls
    deforms: yes — surface ripples
    age: ageless
  implementationStrategies:
    css: |
      background:
        radial-gradient(circle at 30% 40%, oklch(75% 0.18 200), transparent 30%),
        radial-gradient(circle at 70% 60%, oklch(75% 0.18 310), transparent 30%),
        radial-gradient(circle at 50% 30%, oklch(75% 0.18 60), transparent 30%),
        oklch(15% 0.02 250);
      filter: blur(20px) saturate(180%);
    svg: |
      <feTurbulence baseFrequency="0.008" numOctaves="3"/>
      <feDisplacementMap scale="40"/>
      /* swirls the radial blobs into oil-slick patterns */
    webgl: real-time noise + UV distort gives the highest fidelity
    raster: stock oil-on-water photograph at substrate
  reactiveBehaviors:
    light: distort scale increases on pointer proximity
    highlight: tracks pointer
    depth: surface ripples on press (canvas ripple shader)
    parallax: subtle on scroll
  pairsWith:
    prototypeStyles: [style-aurorism, style-holographic, aesthetic-vaporwave, aesthetic-cyberpunk]
  killsTheIllusion:
    - regular gradient blobs without displacement
    - sRGB hue mixing (always OKLCH for iridescence)
  examples:
    - Linear visual ID
    - Apple TV+ marketing background
```

### 3.5 Aurora and gradient family

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

- materialId: material-tonal-surface
  name: Material 3 Tonal Surface (dynamic-color elevation)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: yes via subtle tint shift on elevation
    deforms: no
    age: ageless
  implementationStrategies:
    css: |
      :root {
        --primary: oklch(58% 0.15 268);
        --surface: oklch(98% 0.005 268);
      }
      .elev-1 { background: color-mix(in oklch, var(--primary) 5%, var(--surface)); box-shadow: 0 1px 2px rgb(0 0 0 / 0.3), 0 1px 3px 1px rgb(0 0 0 / 0.15); }
      .elev-2 { background: color-mix(in oklch, var(--primary) 8%, var(--surface)); box-shadow: 0 1px 2px rgb(0 0 0 / 0.3), 0 2px 6px 2px rgb(0 0 0 / 0.15); }
      .elev-3 { background: color-mix(in oklch, var(--primary) 11%, var(--surface)); box-shadow: 0 4px 8px 3px rgb(0 0 0 / 0.15), 0 1px 3px rgb(0 0 0 / 0.3); }
    raster: none
  reactiveBehaviors:
    light: state layers (hover 8% / focus 12% / press 16% on-color overlay)
    highlight: ripple from touch point on press, 0.4s expansion
    depth: containment morph — FAB expands into bottom sheet via shared bounds
    parallax: none
  pairsWith:
    prototypeStyles: [style-material-m3, recipe-material-3, aesthetic-positivity-kawaii, aesthetic-frutiger-eco]
  killsTheIllusion:
    - applying M3 tokens without surface-tint ladder (flat white-on-white)
    - mixing Material Symbols Outlined with Rounded
    - seed colour not propagated into containers and on-colors
  examples:
    - Android 14/15 system UI
    - Google Calendar / Keep / Tasks 2023+
    - Pixel Launcher dynamic theming
  references:
    - https://m3.material.io/blog/tone-based-surface-color-m3
```

### 3.6 Pixel / retro digital family

```yaml
- materialId: pixel-bitmap
  name: Pixel Bitmap (integer-grid surface)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: no
    deforms: no — instant or stepped state changes only
    age: ageless
  implementationStrategies:
    css: |
      image-rendering: pixelated;
      -webkit-font-smoothing: none;
      border-radius: 0;
      box-shadow:
        inset 0 0 0 2px var(--ink),
        2px 2px 0 var(--ink),
        4px 4px 0 var(--shade);
      transition: none;
    raster: pixel-perfect bitmap at exact native resolution
  reactiveBehaviors:
    light: none
    highlight: instant palette swap
    depth: 1-frame state flip
    parallax: stepped only (sprite-sheet steps)
  pairsWith:
    prototypeStyles: [style-pixel-bitmap, aesthetic-pixel-nes-mario, aesthetic-pixel-snes-jrpg, aesthetic-pixel-game-boy-mono, aesthetic-pc-98]
  killsTheIllusion:
    - antialiased SVG icons next to pixel sprites
    - drop-shadow blur on sprites
    - Press Start 2P at 14px (mush)
    - smooth 250ms fades anywhere
  examples:
    - NES.css
    - Pokemon R/B
    - Lospec palettes
    - PICO-8

- materialId: crt-phosphor
  name: CRT Phosphor (raster scan with subpixel RGB)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: glossy
    transparency: opaque
    reactsToLight: yes — phosphor glow blooms with viewing angle
    deforms: no — but the surface curves
    age: shows wear (burn-in)
  implementationStrategies:
    css: |
      .crt::after {
        content: '';
        position: absolute; inset: 0;
        background:
          repeating-linear-gradient(0deg,
            rgba(0,0,0,0.15) 0px,
            transparent 1px,
            transparent 2px,
            rgba(0,0,0,0.15) 3px
          ),
          repeating-linear-gradient(90deg,
            rgba(255,0,0,0.06) 0px,
            rgba(0,255,0,0.06) 1px,
            rgba(0,0,255,0.06) 2px
          );
        mix-blend-mode: multiply;
        pointer-events: none;
      }
    svg: |
      barrel-distortion via <feDisplacementMap> driven by a radial gradient
      gives the CRT curvature
    webgl: |
      fragment shader with phosphor mask, scanline darkness, and bloom is the
      highest-fidelity path. libretro CRT-Royale is the reference.
    raster: optional CRT-curvature mask PNG
  reactiveBehaviors:
    light: phosphor bloom intensifies on bright content
    highlight: scanlines roll slowly (subtle pause-frame look)
    depth: barrel distortion is static
    parallax: none
  pairsWith:
    prototypeStyles: [aesthetic-cassette-futurism, aesthetic-atompunk, aesthetic-vaporwave, aesthetic-cyberpunk, style-pixel-bitmap]
  killsTheIllusion:
    - scanlines on already-pixel content (double pattern fights)
    - scanlines without subpixel RGB
    - flat scanline opacity (real phosphor varies)
    - missing the curvature (CRT is convex)
  examples:
    - libretro/glsl-shaders CRT-Royale
    - Vayce CRT Screen Effect
  references:
    - https://deepwiki.com/libretro/glsl-shaders/3.5-crt-aperture-and-specialized-effects

- materialId: dithered-1bit
  name: 1-bit Dither (Obra Dinn / Game Boy threshold)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: no
    deforms: no
    age: ageless
  implementationStrategies:
    css: |
      image-rendering: pixelated;
      filter: contrast(2) saturate(0);
    svg: |
      Bayer ordered dither via <feComponentTransfer> with a threshold table —
      shader-friendly because it's parallelizable.
    webgl: |
      Floyd-Steinberg error-diffusion gives the highest fidelity; difficult in
      shaders (serial), so use canvas-2d for FS, WebGL for Bayer.
    raster: pre-rendered 1-bit assets at native resolution
  reactiveBehaviors:
    light: none — threshold is fixed
    highlight: none
    depth: none
    parallax: stepped only
  pairsWith:
    prototypeStyles: [style-pixel-bitmap, aesthetic-pixel-game-boy-mono, aesthetic-web-brutalism, aesthetic-corporate-grunge]
  killsTheIllusion:
    - Bayer + Floyd-Steinberg in the same scene (pick one)
    - dither over already-low-contrast content (clamps to single shade)
  examples:
    - Return of the Obra Dinn
    - Macintosh System 1 graphics
    - 1-bit Tumblr
  references:
    - https://www.alanzucconi.com/2018/10/24/shader-showcase-saturday-11/

- materialId: ascii-art-surface
  name: ASCII Art Surface (text-as-pixel)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: no
    deforms: no
    age: ageless
  implementationStrategies:
    css: |
      font-family: ui-monospace, 'IBM Plex Mono';
      line-height: 1;
      letter-spacing: 0;
      white-space: pre;
    webgl: |
      Codrops "Efecto" — quantize image luminance to an ASCII charset, render
      to a font-grid canvas. Charset density carries luminance.
    raster: pre-rendered ASCII PNG for static content
  reactiveBehaviors:
    light: pointer can resample the ASCII density
    highlight: cursor-position changes character density
    depth: none
    parallax: stepped
  pairsWith:
    prototypeStyles: [style-terminal-mono, recipe-terminal-on-web, aesthetic-web-brutalism]
  killsTheIllusion:
    - proportional font (must be monospace)
    - line-height > 1
  examples:
    - tympanus.net Codrops Efecto
    - figlet headers
  references:
    - https://tympanus.net/codrops/2026/01/04/efecto-building-real-time-ascii-and-dithering-effects-with-webgl-shaders/
```

### 3.7 Glitch / distortion / vector-line family

Digital materials whose "physical" behaviour is the texture of the medium itself — codec failure, signal interference, lens optics, plotter pen on paper, schematic engraving. These are NOT analog (they're born digital or are simulated digitally), and they're not UI-surface materials (glass / clay) — they're the texture of digital media as material.

```yaml
- materialId: datamosh-compression-smear
  name: Datamosh (codec interpolation failure)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: no
    deforms: yes — frame motion stretches old pixels along predicted vectors
    age: ageless (or feels 2008-Tumblr era)
  implementationStrategies:
    css: |
      /* approximation only — true datamosh needs WebGL */
      filter: blur(0.5px) saturate(1.2);
      mix-blend-mode: screen;
    webgl: |
      sample previous frame, displace UVs by motion vectors derived from current
      frame's flow field; never refresh the I-frame. Shadertoy "datamosh" examples
      from beesandbombs and dwitter are the references. Best driven by an
      input video (mp4) and shader stage.
    raster: pre-rendered datamosh video texture under content (looped mp4 or webm)
  reactiveBehaviors:
    light: none — datamosh smears existing pixels
    highlight: pointer can seed the motion-vector field for interactive smear
    depth: stuck-frame "pause" reads as compressed time
    parallax: motion compounds with scroll position (each scroll-tick adds a smear)
  pairsWith:
    prototypeStyles: [aesthetic-vaporwave, aesthetic-cyberpunk, aesthetic-acid-design, aesthetic-y2k-futurism, aesthetic-dreamcore, aesthetic-weirdcore]
  killsTheIllusion:
    - datamosh over still imagery (it needs motion to smear)
    - clean cuts between datamoshed clips (real datamosh is continuous)
    - excessive opacity (datamosh reads as material, not as filter)
  examples:
    - Kanye West "Welcome to Heartbreak" music video
    - Takeshi Murata datamosh fine-art
    - Sapeur album covers
  references:
    - https://www.shadertoy.com/results?query=datamosh

- materialId: rgb-channel-split
  name: RGB Channel Split (intentional large-displacement chromatic split)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: yes — displacement amount can react to pointer / tilt
    deforms: no (the channels shift, the structure stays)
    age: ageless
  implementationStrategies:
    css: |
      .rgb-split {
        position: relative;
        color: transparent;
      }
      .rgb-split::before,
      .rgb-split::after {
        content: attr(data-text);
        position: absolute; inset: 0;
        mix-blend-mode: screen;
      }
      .rgb-split::before { color: #ff0040; transform: translate(-2px, 0); }
      .rgb-split::after  { color: #00ffff; transform: translate( 2px, 0); }
    svg: |
      <feOffset> + <feColorMatrix> to isolate the R, G, B channels, then
      <feMerge> them with horizontal offsets. Drives reactive splits via
      animated <feOffset dx>.
    webgl: |
      sample input three times at (uv - offset, uv, uv + offset), output
      (sampleA.r, sampleB.g, sampleC.b). Trivial fragment shader.
    raster: not appropriate — RGB split needs the live composition
  reactiveBehaviors:
    light: split amount can grow with pointer velocity
    highlight: pointer-distance modulates the displacement
    depth: hover spreads the channels (treat as "depth on attention")
    parallax: scroll-velocity drives split amount
  pairsWith:
    prototypeStyles: [aesthetic-cyberpunk, aesthetic-acid-graphics, aesthetic-vaporwave, aesthetic-y2k-futurism, aesthetic-acid-design, recipe-terminal-on-web]
  killsTheIllusion:
    - applying to body text at any displacement that breaks legibility
    - symmetric offsets (real chromatic aberration is radial, biased toward edges)
    - flat across the whole frame (real lens CA gets worse toward corners)
  examples:
    - Blade Runner 2049 type treatment
    - 1980s VHS title cards
    - Kraftwerk "Computer World" sleeve
  references:
    - https://en.wikipedia.org/wiki/Chromatic_aberration

- materialId: jpeg-block-corruption
  name: JPEG Block Corruption (8×8 macroblock aesthetic)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: no
    deforms: no (the blocks SHIFT, the underlying content stays)
    age: ageless (or feels 2003-MySpace era)
  implementationStrategies:
    css: |
      /* approximation via clip-path mosaic */
      filter: contrast(1.4) saturate(1.6);
      image-rendering: pixelated;
    svg: |
      <feFlood> + <feComposite> with 8×8 tile <pattern> to introduce blocky
      color shifts; combine with <feColorMatrix> for chroma subsampling.
    webgl: |
      quantize uvs to 8-pixel grid: vec2 q = floor(uv * resolution / 8.) * 8. / resolution;
      sample at q for the color, sample at uv for the luminance; combine.
      This is the "true" JPEG aesthetic (block color + finer luminance).
    raster: re-save the source PNG as JPEG at quality 12-18 for the authentic look
  reactiveBehaviors:
    light: none
    highlight: blocks can desaturate locally under pointer (hint of decay)
    depth: none — JPEG corruption is structural
    parallax: stepped — block-grid feels stuck
  pairsWith:
    prototypeStyles: [aesthetic-vaporwave, aesthetic-y2k-myspace, aesthetic-internetcore, aesthetic-cyberpunk, aesthetic-weirdcore, aesthetic-dreamcore]
  killsTheIllusion:
    - blocks that don't align to an 8×8 grid (real JPEG is rigid)
    - smooth gradients between blocks (real JPEG has hard block edges)
    - applying to text (illegibility)
  examples:
    - early MySpace profile photos
    - art of Petra Cortright early-era
    - aesthetic Tumblr 2012
  references:
    - https://en.wikipedia.org/wiki/Compression_artifact

- materialId: signal-interference
  name: Signal Interference (hum bars, sync errors, vertical hold drift)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: glossy
    transparency: opaque
    reactsToLight: yes — interference modulates with content luminance
    deforms: yes (frame skew, scroll, sync loss)
    age: feels analog-CRT era despite digital implementation
  implementationStrategies:
    css: |
      .interference::after {
        content: '';
        position: absolute; inset: 0;
        background: linear-gradient(180deg,
          transparent 0%,
          rgba(255,255,255,0.08) 47%,
          rgba(0,0,0,0.15) 50%,
          transparent 53%
        );
        background-size: 100% 4px;
        animation: hum 0.8s linear infinite;
      }
      @keyframes hum { 0% { background-position: 0 0 } 100% { background-position: 0 100vh } }
    svg: |
      <feTurbulence type="turbulence" baseFrequency="0 4" numOctaves="2"> for
      horizontal noise band; modulate with <feComposite in2="SourceAlpha"> for
      the hum bar drift.
    webgl: |
      fragment shader: sin(uv.y * 200. + time * 8.) modulates a horizontal band
      offset that displaces UVs. Combine with sync-loss frame-skew (uv.x += step * uv.y).
    raster: looping mp4 of CRT hum bars as overlay layer
  reactiveBehaviors:
    light: interference intensity scales with content luminance
    highlight: pointer can seed sync-loss spikes
    depth: frame-skew creates apparent depth via the slip-line
    parallax: scroll triggers transient sync loss
  pairsWith:
    prototypeStyles: [aesthetic-vaporwave, aesthetic-cassette-futurism, aesthetic-atompunk, aesthetic-cyberpunk, recipe-terminal-on-web, style-dense-mono-dark]
  killsTheIllusion:
    - regular sine-wave (real interference is stochastic)
    - hum bars at the same position every frame (real ones drift)
    - applying with linear blend (use mix-blend-mode: screen or color-dodge)
  examples:
    - 1980s broadcast TV
    - VHS recorded off-air
    - synthwave music video establishing shots
  references:
    - https://en.wikipedia.org/wiki/Image_quality_television

- materialId: nes-rom-corruption
  name: NES ROM Corruption (palette-flipped sprites, garbled tile data)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: no
    deforms: yes (tiles re-index, palette swaps)
    age: ageless (feels 1986-Famicom era)
  implementationStrategies:
    css: |
      image-rendering: pixelated;
      filter: hue-rotate(var(--rom-shift, 0deg)) saturate(2);
    webgl: |
      shader samples a palette LUT texture; randomize indices for sprite tiles
      at random intervals; for the deepest corruption, swap tile-index lookup
      tables mid-frame.
    raster: pre-rendered glitched sprite sheets at native NES resolution (256×240)
  reactiveBehaviors:
    light: palette swap is the only response (binary)
    highlight: pointer-press flips a tile region's palette
    depth: stepped only (sprite-sheet frame swap)
    parallax: stepped (8-pixel scroll register only)
  pairsWith:
    prototypeStyles: [style-pixel-bitmap, aesthetic-pixel-nes-mario, aesthetic-pixel-arcade, aesthetic-cyberpunk, aesthetic-acid-graphics]
  killsTheIllusion:
    - sub-pixel scroll on glitched tiles (NES had no sub-pixel)
    - more than 4 colors in a single sprite (NES sprite limit was 3+transparent)
    - non-8×8 tile alignment
  examples:
    - corrupted Pokemon Red R/B (MissingNo aesthetic)
    - retro homebrew NES demos
    - lospec palette work
  references:
    - https://www.nesdev.org/wiki/PPU_palettes

- materialId: chromatic-aberration-lens
  name: Lens Chromatic Aberration (radial RGB split toward corners)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: glossy
    transparency: opaque
    reactsToLight: yes — CA peaks at high-contrast luminance transitions
    deforms: no (channels shift radially)
    age: ageless
  implementationStrategies:
    css: |
      /* limited — CSS can fake at edges with two filter layers */
      filter: drop-shadow(-1px 0 0 #ff0044) drop-shadow(1px 0 0 #00ddff);
    svg: |
      <feOffset> per channel via <feColorMatrix>, scaled by radial distance
      from frame center using <feDisplacementMap>.
    webgl: |
      vec2 dir = uv - 0.5;
      float r = length(dir);
      vec3 rgb = vec3(
        sample(uv + dir * r * 0.012).r,
        sample(uv).g,
        sample(uv - dir * r * 0.012).b
      );
      Real lenses bias the red toward the edge — tune signs accordingly.
    raster: not appropriate
  reactiveBehaviors:
    light: aberration peaks at content high-contrast edges
    highlight: pointer position can simulate "focal point" (zero CA at pointer)
    depth: stronger at edges = depth cue
    parallax: scroll velocity doesn't move CA (it's optical, not motion)
  pairsWith:
    prototypeStyles: [aesthetic-cyberpunk, aesthetic-cinematic, recipe-bento-marketing, aesthetic-frutiger-aero, aesthetic-frutiger-dark-aero, recipe-restrained-ai-marketing]
  killsTheIllusion:
    - uniform CA across the frame (real lens CA is radial)
    - very large displacement (becomes glitch, not optics — see rgb-channel-split for that)
    - applied to text without limit (illegibility)
  examples:
    - Anamorphic lens cinematography
    - high-quality digital camera RAW files
    - subtle film-emulation effects
  references:
    - https://en.wikipedia.org/wiki/Chromatic_aberration

- materialId: barrel-pincushion-warp
  name: Barrel / Pincushion Lens Warp (wide-lens optical distortion)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: glossy
    transparency: opaque
    reactsToLight: no
    deforms: yes — radial geometric distortion
    age: ageless
  implementationStrategies:
    css: |
      /* faked via transform: perspective + radial mask */
      transform: perspective(800px) rotateX(0.01deg);
      mask: radial-gradient(circle, black 60%, transparent 100%);
    svg: |
      <feDisplacementMap scale="<intensity>"> driven by a radial gradient
      (white in center, black at edges) gives proper barrel distortion;
      invert the gradient for pincushion.
    webgl: |
      vec2 ctr = uv - 0.5;
      float r2 = dot(ctr, ctr);
      uv -= ctr * r2 * k;       // k > 0 = barrel, k < 0 = pincushion
      Common k = 0.15-0.35 for noticeable warp.
    raster: not appropriate
  reactiveBehaviors:
    light: none
    highlight: pointer can drag the warp center (off-axis lens)
    depth: warp = depth cue (fish-eye reads as wide-angle)
    parallax: scroll changes warp intensity for "zoom-breath" effect
  pairsWith:
    prototypeStyles: [aesthetic-vaporwave, aesthetic-cyberpunk, aesthetic-y2k-futurism, aesthetic-cinematic, recipe-aurora-marketing, recipe-bento-marketing]
  killsTheIllusion:
    - applying to UI controls that need precise hit-targeting
    - warping without pixel-snap correction (creates moire)
    - applying without a vignette (real wide lenses also vignette)
  examples:
    - GoPro footage
    - fisheye music videos (early 2010s indie)
    - VR / 360-degree projection
  references:
    - https://en.wikipedia.org/wiki/Distortion_(optics)

- materialId: displacement-ripple
  name: Displacement Ripple (interactive pointer-driven warp)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: glossy
    transparency: translucent
    reactsToLight: yes (the ripple bends light)
    deforms: yes — local UV displacement
    age: ageless
  implementationStrategies:
    css: |
      /* limited — pure CSS can't do per-pixel displacement */
      transition: transform 0.3s ease-out;
      &:hover { transform: scale(1.02); }
    svg: |
      <feTurbulence baseFrequency="0.02 0.04" seed="<random>" /> →
      <feDisplacementMap scale="20" /> applied to backdropFilter.
      Animate seed for live ripple.
    webgl: |
      fragment shader: sample with uv displaced by sin(distance_from_pointer * k - time * v).
      Provides genuine ripple/wave deformation driven by pointer position.
    raster: not appropriate (needs live interaction)
  reactiveBehaviors:
    light: ripple bends light around the displacement
    highlight: pointer is the ripple origin
    depth: ripple = local depth perturbation
    parallax: subtle ripple on scroll velocity
  pairsWith:
    prototypeStyles: [style-liquid-glass, style-glassmorphism, style-aurorism, aesthetic-dreamcore, aesthetic-frutiger-aero, recipe-aurora-marketing]
  killsTheIllusion:
    - ripple amplitude > 30px (too cartoonish)
    - ripple over text (always readable rests > ripple)
    - displacement without coherent damping (rings should fade with distance)
  examples:
    - Apple Liquid Glass material (2025)
    - WebGL water demos
    - shadertoy ripple references
  references:
    - https://www.shadertoy.com/view/3lsXR4

- materialId: heat-haze-shimmer
  name: Heat Haze Shimmer (mirage / hot tarmac warp)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: glossy
    transparency: transparent
    reactsToLight: yes
    deforms: yes — low-amplitude noise displacement
    age: ageless
  implementationStrategies:
    css: |
      filter: blur(0.4px);
      animation: shimmer 3s ease-in-out infinite alternate;
      @keyframes shimmer { from { transform: translateY(0) } to { transform: translateY(-1px) } }
    svg: |
      <feTurbulence baseFrequency="0.01 0.02" type="fractalNoise"> →
      <feDisplacementMap scale="3"> with seed animated for live shimmer.
    webgl: |
      tiny UV displacement driven by Perlin noise sampled with time;
      magnitude < 0.003 of viewport.
  reactiveBehaviors:
    light: shimmer intensifies at bright regions
    highlight: pointer creates a heat source (radial shimmer amp)
    depth: minor — shimmer reads as atmospheric warmth
    parallax: continuous, slow
  pairsWith:
    prototypeStyles: [aesthetic-vaporwave, aesthetic-dreamcore, aesthetic-frutiger-aero, aesthetic-coastal-grandmother, recipe-aurora-marketing]
  killsTheIllusion:
    - too-fast shimmer (real heat is slow)
    - shimmer that crosses sharp UI edges (always damp at edges)
    - over text (illegibility)
  examples:
    - mirage in cinema (Mad Max Fury Road)
    - desert documentary
    - synthwave intro shimmer
  references:
    - https://en.wikipedia.org/wiki/Mirage

- materialId: motion-blur-streak
  name: Motion Blur Streak (directional motion artifact)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: glossy
    transparency: translucent
    reactsToLight: yes
    deforms: yes — directional smear along motion vector
    age: ageless
  implementationStrategies:
    css: |
      transition: transform 0.15s ease-out;
      will-change: transform;
      filter: blur(0); /* clean rest state */
      /* runtime sets filter: blur(2px) during fast pointer drag */
    svg: |
      <feGaussianBlur stdDeviation="<dx> <dy>"> with anisotropic blur along
      motion direction. Drive dx/dy from pointer velocity.
    webgl: |
      multi-tap blur in the motion-vector direction; 4-8 samples is enough for UI.
  reactiveBehaviors:
    light: streaks extend specular highlights
    highlight: pointer velocity drives blur amount + direction
    depth: faster motion = more apparent speed = more depth perception
    parallax: scroll velocity drives vertical streak
  pairsWith:
    prototypeStyles: [aesthetic-cyberpunk, aesthetic-cassette-futurism, aesthetic-cinematic, recipe-bento-marketing, recipe-aurora-marketing, aesthetic-frutiger-aero]
  killsTheIllusion:
    - persistent blur at rest (real motion blur clears in 1 frame)
    - omnidirectional blur (real motion blur is directional)
    - applied to text mid-action (illegibility)
  examples:
    - Apple iOS scrolling speed-blur (subtle)
    - racing games
    - WebGL "fluid" demos
  references:
    - https://en.wikipedia.org/wiki/Motion_blur

- materialId: plotter-pen-line
  name: Plotter Pen Line (HP 7475 single-weight ink-on-paper)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: no
    deforms: no
    age: feels 1985-CAD-lab era
  implementationStrategies:
    css: |
      stroke: #1a1a1a;
      stroke-width: 0.5;
      stroke-linecap: round;
      fill: none;
      filter: url(#pen-jitter);  /* subtle hand-tremor displacement */
    svg: |
      <filter id="pen-jitter">
        <feTurbulence baseFrequency="0.5" numOctaves="2" />
        <feDisplacementMap scale="0.4" />
      </filter>
      Apply to all stroked paths. Use vector geometry only; no fills.
    webgl: |
      line shader with subtle width noise + ink-blot simulation at line ends
    raster: avoid — plotter is inherently vector
  reactiveBehaviors:
    light: paper grain shows under raking light
    highlight: pointer can advance a stroke (drawing-in-progress register)
    depth: none — flat ink on paper
    parallax: none
  pairsWith:
    prototypeStyles: [aesthetic-swiss-modernist, aesthetic-bauhaus, recipe-scientific-infra-marketing, style-outline-wireframe, recipe-newspaper-of-record, style-restrained-hairline]
  killsTheIllusion:
    - variable stroke width (a plotter uses one pen at a time)
    - filled regions (plotters don't fill — they hatch)
    - antialiased curves without ink-jitter
  examples:
    - early CAD output (AutoCAD 1.0 era)
    - vintage Tufte information graphics
    - Casey Reas / processing.org early sketches
  references:
    - https://en.wikipedia.org/wiki/HP_7475

- materialId: cad-blueprint
  name: CAD Blueprint (white-on-blue technical drawing)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: no
    deforms: no
    age: feels 1900-1980 architectural era
  implementationStrategies:
    css: |
      background: #1e3a5f;  /* deep blueprint blue */
      color: #ffffff;
      font-family: 'Courier Prime', 'Architects Daughter', monospace;
      .blueprint-line { stroke: #c8d8e8; stroke-width: 0.6; fill: none; }
      .blueprint-grid {
        background-image:
          linear-gradient(rgba(255,255,255,0.06) 1px, transparent 1px),
          linear-gradient(90deg, rgba(255,255,255,0.06) 1px, transparent 1px);
        background-size: 20px 20px;
      }
    svg: |
      grid as <pattern>, vectors with stroke="#c8d8e8" fill="none".
      Dimension lines with <marker> arrows and <text> labels per technical convention.
    webgl: not typically needed
    raster: scanned grid paper PNG as substrate; vectors atop
  reactiveBehaviors:
    light: none — it's a print
    highlight: pointer-hover reveals dimension annotations
    depth: minor — pseudo-3D iso projection often present
    parallax: scroll between detail views
  pairsWith:
    prototypeStyles: [aesthetic-bauhaus, aesthetic-swiss-modernist, recipe-scientific-infra-marketing, aesthetic-atompunk, aesthetic-steampunk, style-restrained-hairline]
  killsTheIllusion:
    - blueprint blue too saturated (real blueprints fade toward cyan-grey)
    - antialiased grid lines (real blueprints have crisp 1px ferrocyanide trace)
    - sans-serif body type (blueprint convention is mono / technical letterer)
  examples:
    - Frank Gehry sketches
    - vintage car schematics
    - Le Corbusier's published drawings
  references:
    - https://en.wikipedia.org/wiki/Blueprint

- materialId: wireframe-3d-line
  name: Wireframe 3D (Tron-style line-only volumetric)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: matte (or glowing)
    transparency: transparent
    reactsToLight: yes — lines can glow with bloom
    deforms: no
    age: feels 1982 (Tron) / 1990s CGI titles
  implementationStrategies:
    css: |
      /* css can't render true 3D — use CSS transforms for simple wireframes */
      transform: perspective(800px) rotateY(20deg) rotateX(15deg);
      border: 1px solid #00ff88;
    svg: |
      pre-projected vector silhouette of geometry; stroke="<accent>" fill="none";
      stroke-width: 1px. For rotation, swap among pre-rendered SVG keyframes.
    webgl: |
      three.js LineSegments material with edges geometry helper. Real wireframe
      means rendering the EdgesGeometry — never just MeshBasicMaterial with
      wireframe:true (that gives triangulated wireframe, not edges-only).
      Add bloom for the Tron register.
    raster: not appropriate
  reactiveBehaviors:
    light: lines glow under bloom
    highlight: pointer-near lines intensify
    depth: depth-fade (far lines fainter)
    parallax: free rotation on pointer drag
  pairsWith:
    prototypeStyles: [aesthetic-cyberpunk, aesthetic-vaporwave, aesthetic-atompunk, aesthetic-cassette-futurism, recipe-terminal-on-web, style-terminal-mono, recipe-scientific-infra-marketing]
  killsTheIllusion:
    - triangulated wireframe (use edges-geometry instead)
    - line thickness variation per face (real wireframe has uniform stroke)
    - antialiasing without bloom for the Tron variant
  examples:
    - Tron (1982)
    - Atari Star Wars arcade (1983)
    - early 3D motion graphics
  references:
    - https://threejs.org/docs/#api/en/objects/LineSegments

- materialId: schematic-pcb-trace
  name: Schematic / PCB Trace (circuit-board aesthetic)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: minor — gold pads catch raking light
    deforms: no
    age: ageless
  implementationStrategies:
    css: |
      background: #00553a;  /* solder mask green */
      color: #e2c376;       /* silkscreen yellow */
      font-family: 'IBM Plex Mono', monospace;
      .trace { stroke: #b58b3a; stroke-width: 1.6; }   /* copper trace */
      .pad { fill: #f5d480; stroke: #b58b3a; }          /* solder pad */
    svg: |
      orthogonal-routed paths only (45° / 90° angles), <pattern> dot grid for
      vias, <circle> for component pins, <text> for silkscreen labels in mono.
    webgl: not typically needed
    raster: PCB texture PNG as substrate
  reactiveBehaviors:
    light: minor — pads glint subtly
    highlight: pointer can activate trace-flow animation (electron path)
    depth: layered traces (top + bottom copper) at different opacities
    parallax: scroll reveals additional copper layers
  pairsWith:
    prototypeStyles: [aesthetic-cyberpunk, aesthetic-cassette-futurism, aesthetic-atompunk, recipe-terminal-on-web, recipe-scientific-infra-marketing, recipe-devtools-marketing]
  killsTheIllusion:
    - diagonal trace routing at non-45° angles (PCB design has strict angles)
    - antialiased traces without copper-fill texture
    - solder-mask color too bright (real green is muted)
  examples:
    - Raspberry Pi board photography
    - KiCAD render output
    - vintage electronic component diagrams
  references:
    - https://en.wikipedia.org/wiki/Printed_circuit_board

- materialId: iso-line-drawing
  name: Isometric Line Drawing (axonometric vector, no fill)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: no
    deforms: no
    age: ageless
  implementationStrategies:
    css: |
      /* css can fake simple iso boxes */
      transform: matrix(0.866, 0.5, -0.866, 0.5, 0, 0);  /* 30°/30° iso */
      border: 1px solid var(--ink);
      background: transparent;
    svg: |
      pre-project geometry to iso coords:
        sx = (x - y) * cos(30°)
        sy = (x + y) * sin(30°) - z
      stroke only; no fill. Use stroke-dasharray for hidden edges convention.
    webgl: three.js OrthographicCamera + axes aligned for isometric; LineSegments material
    raster: not appropriate
  reactiveBehaviors:
    light: none — vector
    highlight: pointer-hover on a face fills it with a tint
    depth: line-weight encodes z-depth (further = thinner)
    parallax: rotate around iso angle on scroll
  pairsWith:
    prototypeStyles: [aesthetic-bauhaus, aesthetic-swiss-modernist, recipe-scientific-infra-marketing, style-outline-wireframe, aesthetic-atompunk, aesthetic-cassette-futurism]
  killsTheIllusion:
    - perspective convergence (iso is by definition parallel)
    - filled regions inconsistent with the line-only register
    - stroke joins not crisp at vertices
  examples:
    - SimCity 2000 building diagrams
    - vintage technical isometric instruction manuals
    - Monument Valley navigation prompts
  references:
    - https://en.wikipedia.org/wiki/Axonometric_projection

- materialId: hand-architect-sketch
  name: Hand Architect Sketch (Le Corbusier / Frank Lloyd Wright register)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: subtle — paper grain breathes under raking light
    deforms: no
    age: feels 1920-1960 master-architect era
  implementationStrategies:
    css: |
      font-family: 'Architects Daughter', 'Caveat', sans-serif;
      color: #1a1a1a;
      .sketch-line { stroke: #1a1a1a; stroke-width: 0.8; fill: none; }
    svg: |
      <filter id="hand-tremor">
        <feTurbulence baseFrequency="0.8" numOctaves="2" />
        <feDisplacementMap scale="1.5" />
      </filter>
      Apply to all paths. Use varying stroke widths (0.5-1.4) for "pressure" effect.
      Don't close every shape — leave a 5-10% gap (real hand sketches "breathe").
    webgl: not typically needed
    raster: scanned hand-drawn sketches OK as substrate (combine with vector overlay)
  reactiveBehaviors:
    light: paper texture subtly catches light
    highlight: pointer can advance an unfinished sketch
    depth: stroke weight implies depth (heavier = closer)
    parallax: stack of trace-paper overlays on scroll
  pairsWith:
    prototypeStyles: [recipe-warm-restraint, recipe-editorial-magazine, aesthetic-dark-academia, style-cream-humanist, style-serif-warm-paper, aesthetic-cottagecore]
  killsTheIllusion:
    - uniform stroke width (real hand has pressure variation)
    - perfectly closed shapes (real sketches breathe)
    - antialiased curves with no tremor
  examples:
    - Frank Lloyd Wright Falling Water sketches
    - Le Corbusier's published sketches
    - Steven Holl watercolor architectural ideation
  references:
    - https://en.wikipedia.org/wiki/Architectural_drawing

- materialId: ansi-art
  name: ANSI Art (16-color extended-box character art)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: glossy (CRT phosphor inheritance)
    transparency: opaque
    reactsToLight: no
    deforms: no
    age: feels 1985-1995 BBS / hacker era
  implementationStrategies:
    css: |
      font-family: 'IBM Plex Mono', 'Px437 IBM VGA', monospace;
      background: #000;
      color: #aaaaaa;
      white-space: pre;
      line-height: 1;
      letter-spacing: 0;
      /* 16 ANSI colors: black, red, green, yellow, blue, magenta, cyan, white
                          + bright variants. Use CSS classes per glyph. */
    svg: not appropriate
    webgl: |
      shader sampling a 16-color ANSI palette LUT; each cell renders one of
      256 codepoints from CP437 (IBM PC code page, includes ░▒▓█).
    raster: pre-rendered ANSI art PNG (with native CP437 font)
  reactiveBehaviors:
    light: scanline overlay (often paired with crt-phosphor)
    highlight: pointer-hover can ripple through the character grid
    depth: ░▒▓█ stair-step encodes depth/distance
    parallax: stepped only (character grid is integer)
  pairsWith:
    prototypeStyles: [recipe-terminal-on-web, style-terminal-mono, aesthetic-cyberpunk, aesthetic-cassette-futurism, aesthetic-atompunk, aesthetic-corporate-grunge]
  killsTheIllusion:
    - using more than the 16 ANSI colors
    - non-CP437 codepoints (no curly quotes, no em-dashes)
    - proportional or anti-aliased fonts
  examples:
    - BBS title screens
    - ACiD Productions ANSI gallery
    - early hacker zine title pages
  references:
    - https://en.wikipedia.org/wiki/ANSI_art

- materialId: monospace-code-grid
  name: Monospace Code Grid (IDE / terminal text as visual material)
  family: digital
  category: digital-effect
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: no
    deforms: no
    age: ageless (or feels current dev-tools era)
  implementationStrategies:
    css: |
      font-family: 'JetBrains Mono', 'Fira Code', monospace;
      font-feature-settings: 'liga' 1, 'calt' 1;  /* ligatures: ≠ ⇒ ≤ ≥ */
      line-height: 1.5;
      letter-spacing: 0;
      /* syntax highlight via classes, not inline styles */
      .keyword { color: #c792ea }
      .string  { color: #c3e88d }
      .comment { color: #546e7a; font-style: italic }
    svg: not appropriate
    webgl: |
      WebGL text-rendering for code-as-particle (e.g. Matrix rain) uses MSDF
      fonts with per-glyph instancing.
  reactiveBehaviors:
    light: none
    highlight: pointer can advance type-on animation
    depth: stack of code panes at different opacities
    parallax: scroll-driven code scroll (canonical recipe-devtools-marketing)
  pairsWith:
    prototypeStyles: [recipe-devtools-marketing, recipe-terminal-on-web, recipe-ai-foundry-dark, style-terminal-mono, style-dense-mono-dark, recipe-restrained-ai-marketing]
  killsTheIllusion:
    - non-monospace fonts (alignment dies)
    - line-height < 1.3 (lines crush together)
    - proportional ligature spacing
    - rainbow syntax themes (most code is 3-5 colors, not 12)
  examples:
    - GitHub editor
    - VSCode default theme
    - Anthropic devtools marketing pages
  references:
    - https://www.jetbrains.com/lp/mono/
```

---

## 4. Analog materials

Materials that exist physically and pass through a scanner, camera, or sampler before they land on the web. The orchestrator must respect that PATH — analog materials at flat opacity, perfectly regular, instantly betray themselves.

### 4.1 Paper family

```yaml
- materialId: uncoated-paper
  name: Uncoated Paper (soft, porous, ink-absorbing)
  family: analog
  category: paper
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: no specular
    deforms: yes — wrinkles, tears, dog-ears
    age: shows wear (yellowing, foxing)
  implementationStrategies:
    css: |
      background:
        url('paper-grain-2048.jpg') center/512px,
        oklch(97% 0.012 85);  /* warm white, never #FFF */
      background-blend-mode: multiply;
    svg: |
      <filter id="paperGrain">
        <feTurbulence baseFrequency="0.9" numOctaves="2" seed="3"/>
        <feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 0.06 0"/>
      </filter>
      <!-- 6% noise opacity -->
    raster: 2048×2048 scanned uncoated paper (Crane Lettra, Mohawk Superfine)
  reactiveBehaviors:
    light: no specular; ambient only
    highlight: minor warmth in hover state
    depth: corner curl on hover (CSS mask gradient)
    parallax: very subtle on scroll
  pairsWith:
    prototypeStyles: [style-serif-warm-paper, aesthetic-cottagecore, aesthetic-dark-academia, aesthetic-cottagegoth, style-raster-cutout]
  killsTheIllusion:
    - perfectly flat #FFF background (uncoated is always warm-tinted)
    - high-contrast specular highlight (uncoated has none)
    - tile pattern visibly repeating (use masking to break the seam)
    - body text at 16px with line-height 1.4 (editorial paper wants 18–19px / 1.55)
  examples:
    - The New Yorker print
    - Aeon longform
    - book covers from Penguin Modern Classics
  references:
    - https://www.jampaper.com/blog/paper-textures-and-finishes-2/

- materialId: coated-glossy-paper
  name: Coated Glossy Paper (magazine cover stock)
  family: analog
  category: paper
  physicalBehavior:
    surfaceFinish: glossy
    transparency: opaque
    reactsToLight: yes — specular sheen
    deforms: minimal
    age: ageless (or shows fingerprints)
  implementationStrategies:
    css: |
      background:
        linear-gradient(115deg, rgba(255,255,255,0.18) 0%, transparent 35%),
        url('coated-paper-1024.jpg') center/512px,
        oklch(98% 0.005 80);
      background-blend-mode: overlay, multiply, normal;
    raster: scanned coated stock; finer grain than uncoated
  reactiveBehaviors:
    light: glossy sheen tracks pointer at low intensity
    highlight: yes (linear sweep on hover, 0.2 opacity)
    depth: minimal
    parallax: minimal
  pairsWith:
    prototypeStyles: [recipe-editorial-magazine, aesthetic-y2k-memphis-loud, aesthetic-coastal-grandmother]
  killsTheIllusion:
    - the same fibers as uncoated (coated is much smoother)
    - missing the sheen on hover
  examples:
    - Vogue covers
    - National Geographic
    - airline in-flight magazines

- materialId: kraft-paper
  name: Kraft Paper (brown unbleached cardstock)
  family: analog
  category: paper
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: no specular
    deforms: yes — wrinkles, tears
    age: shows wear (creases at fold)
  implementationStrategies:
    css: |
      background:
        url('kraft-fibre-1024.jpg') center/384px,
        oklch(60% 0.06 60);  /* warm brown */
      background-blend-mode: multiply;
    raster: scan of real brown kraft; visible long fibers
  reactiveBehaviors:
    light: no specular
    highlight: minimal
    depth: yes — paper can curl
    parallax: minimal
  pairsWith:
    prototypeStyles: [aesthetic-cottagecore, aesthetic-cottagegoth, aesthetic-goblincore, recipe-newspaper-of-record]
  killsTheIllusion:
    - kraft as a solid brown swatch (it needs visible fibers)
    - clean rectangular crop (kraft tears on edges)
  examples:
    - Aesop product wrap
    - Trader Joe's bag aesthetic
    - small-batch coffee bag fronts

- materialId: parchment
  name: Parchment / Vellum (animal hide, premium document)
  family: analog
  category: paper
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: no specular but visible thickness
    deforms: yes — curls dramatically at corners
    age: acquired patina (yellowing, blotches)
  implementationStrategies:
    css: |
      background:
        radial-gradient(ellipse at 30% 20%, oklch(94% 0.04 70) 0%, transparent 50%),
        radial-gradient(ellipse at 80% 80%, oklch(86% 0.06 50) 0%, transparent 50%),
        oklch(91% 0.05 60);
      filter: contrast(1.05);
    svg: |
      blotch turbulence pattern at low opacity
    raster: real parchment scan ideal
  reactiveBehaviors:
    light: edge highlight only
    highlight: no
    depth: corner curl prominent
    parallax: no
  pairsWith:
    prototypeStyles: [aesthetic-dark-academia, aesthetic-steampunk, aesthetic-defi-cosmic (achievement certificates)]
  killsTheIllusion:
    - uniform colour (parchment is naturally splotchy)
    - perfect rectangle (parchment has irregular hand-cut edges)

- materialId: legal-pad
  name: Legal Pad (ruled yellow paper)
  family: analog
  category: paper
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: no
    deforms: yes — pages tear from spiral
    age: shows wear
  implementationStrategies:
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
  reactiveBehaviors:
    light: no
    highlight: no
    depth: corner curl on hover
    parallax: minimal
  pairsWith:
    prototypeStyles: [style-skeuomorphism (notes-as-legal-pad), aesthetic-dark-academia, recipe-newspaper-of-record]
  killsTheIllusion:
    - lines that don't go full-bleed
    - missing red margin line
    - perfect type instead of handwriting
  examples:
    - iOS 6 Notes app
    - office-supply photography
```

### 4.2 Print process family

```yaml
- materialId: risograph
  name: Risograph (limited-palette spot-color print)
  family: analog
  category: print
  physicalBehavior:
    surfaceFinish: matte
    transparency: translucent (per ink layer)
    reactsToLight: no
    deforms: no
    age: ageless
  implementationStrategies:
    css: |
      /* Each "ink" is a colour layer with mix-blend-mode: multiply */
      .layer-fluo-pink { background: color-mix(in srgb, #ff48b0 60%, transparent); mix-blend-mode: multiply; }
      .layer-teal { background: color-mix(in srgb, #00a89c 60%, transparent); mix-blend-mode: multiply; }
      .registration-shift { transform: translate(1.5px, -1px); }  /* trapping miss */
    svg: |
      halftone via <pattern> of dots at varying spacing per ink layer
    webgl: |
      shader: posterise to N inks, apply per-ink halftone screen, slight per-ink
      offset to fake registration shift. Spectrolite-style.
    raster: scanned risograph print as ground truth
  reactiveBehaviors:
    light: no
    highlight: no
    depth: no
    parallax: subtle — each ink layer at slightly different scroll rate
  pairsWith:
    prototypeStyles: [aesthetic-acid-design, aesthetic-acid-graphics, aesthetic-corporate-grunge, aesthetic-y2k-myspace, aesthetic-corporate-memphis]
  killsTheIllusion:
    - perfect registration (riso is famously misregistered — 1–3px offset is the look)
    - smooth gradients (riso halftones, never blends)
    - full opacity inks (riso ink is semi-transparent)
    - warm paper substrate missing (riso usually prints on cream paper)
  examples:
    - RISOTTO Studio prints
    - Spectrolite Riso-ify tool
    - small-press zines
    - Are.na editorial banners
  references:
    - https://risottostudio.com/pages/printing-faq
    - https://spectrolite.app/how-to/overview/riso-ify

- materialId: silkscreen
  name: Silkscreen / Serigraphy (textile + poster print)
  family: analog
  category: print
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque (ink layer)
    reactsToLight: no
    deforms: no
    age: shows wear (ink crackle on textile)
  implementationStrategies:
    css: |
      /* per-color layer with slight registration shift and ink-trap edges */
      .ink-layer { mix-blend-mode: multiply; transform: translate(1px, 1px); }
    svg: |
      <feMorphology operator="dilate" radius="0.5"/> for ink trap;
      <feTurbulence baseFrequency="2"/> for ink texture mask
    raster: scanned silkscreen print as substrate
  reactiveBehaviors:
    light: no
    highlight: no
    depth: no (flat sheet)
    parallax: minimal
  pairsWith:
    prototypeStyles: [aesthetic-acid-design, aesthetic-bauhaus, aesthetic-constructivism, aesthetic-corporate-grunge]
  killsTheIllusion:
    - too-clean ink edges (real silkscreen has slight bleed)
    - perfect registration
    - high gloss inks
  examples:
    - Andy Warhol Marilyn series
    - vintage concert posters
    - merch tees with cracked ink

- materialId: halftone-cmyk
  name: Halftone CMYK (newspaper / comic process)
  family: analog
  category: print
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: no
    deforms: no
    age: shows wear
  implementationStrategies:
    css: |
      background:
        radial-gradient(circle at center, #000 0.5px, transparent 1.5px) 0 0/4px 4px;
      transform: rotate(45deg);  /* black at 45° */
    svg: |
      Per-channel halftone: C @ 15°, M @ 75°, Y @ 0°, K @ 45° — the rosette
      pattern that hides moiré. Use <pattern> with rotated transforms.
    webgl: |
      Sample image luminance, per-channel threshold against rotated dot grid.
    raster: stack of 4 PNG halftone screens at correct angles
  reactiveBehaviors:
    light: no
    highlight: no
    depth: no
    parallax: stepped only
  pairsWith:
    prototypeStyles: [aesthetic-corporate-grunge, style-raster-cutout, aesthetic-acid-design, aesthetic-y2k-memphis-loud, recipe-newspaper-of-record]
  killsTheIllusion:
    - grid-aligned dots for all channels (must rotate per channel)
    - dot size too uniform (real halftone is luminance-driven)
    - moiré-pattern alarms (caused by wrong screen angles)
  examples:
    - Lichtenstein paintings
    - Marvel comics 1960s
    - daily newspaper photos
  references:
    - http://the-print-guide.blogspot.com/2009/05/halftone-screen-angles.html

- materialId: photocopy-xerox
  name: Photocopy / Xerox (toner crush)
  family: analog
  category: print
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: no
    deforms: no
    age: shows wear (streaks, dirt)
  implementationStrategies:
    css: |
      filter: grayscale(1) contrast(1.8);
      mix-blend-mode: multiply;
    svg: |
      <feComponentTransfer> with steep sigmoid for toner crush;
      <feGaussianBlur stdDeviation="0.4"/> + <feColorMatrix> threshold for toner spread
    webgl: |
      sigmoid contrast → grayscale → noise overlay → soft blur → threshold —
      matches CopyCat / Vayce algorithms
    raster: photocopy texture overlays (Indieground packs) at multiply
  reactiveBehaviors:
    light: no
    highlight: no
    depth: no
    parallax: stepped
  pairsWith:
    prototypeStyles: [aesthetic-corporate-grunge, aesthetic-cottagegoth, aesthetic-web-brutalism, aesthetic-acid-graphics, aesthetic-curly-girly]
  killsTheIllusion:
    - clean colour photocopy (the look is mono-thresholded)
    - no streaks or dirt (real Xerox is messy)
    - smooth midtones (toner crushes midtones to black/white)
  examples:
    - punk flyers
    - underground zines
    - photocopy-noise stock packs (Indieground)
  references:
    - https://vayce.app/tools/photocopy-scan-lines-effect/
    - https://effect.app/effects/xerox

- materialId: letterpress-emboss
  name: Letterpress / Emboss (raised-impression printing)
  family: analog
  category: print
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: yes — directional shadow into the pressed area
    deforms: yes — paper is permanently deformed
    age: ageless
  implementationStrategies:
    css: |
      /* Pressed text (debossed) */
      color: transparent;
      text-shadow:
        0 1px 0 rgba(255,255,255,0.8),  /* light from top — highlight at bottom of impression */
        0 -1px 0 rgba(0,0,0,0.4);       /* shadow at top */
      /* Raised text (embossed) */
      .emboss {
        text-shadow:
          -1px -1px 0 rgba(255,255,255,0.8),
           1px  1px 0 rgba(0,0,0,0.4);
      }
    svg: |
      <feSpecularLighting> with offset light source for photoreal letterpress
    raster: scanned letterpress for ultra-high fidelity
  reactiveBehaviors:
    light: ALL pressed elements respect the same light direction
    highlight: shadow direction matches committed light
    depth: hover deepens the impression
    parallax: no
  pairsWith:
    prototypeStyles: [style-serif-warm-paper, aesthetic-cottagecore, aesthetic-dark-academia, recipe-editorial-magazine]
  killsTheIllusion:
    - light source disagreeing with rest of page
    - emboss/deboss on a non-paper substrate
    - colour text inside the impression (letterpress ink colour is muted)
  examples:
    - wedding stationery
    - business cards (Mast Brothers, Aesop)
    - premium book jackets
  references:
    - https://www.smashingmagazine.com/2012/07/letterpress-effect-fireworks-css/
```

### 4.3 Drawing / painting medium family

```yaml
- materialId: watercolor-wash
  name: Watercolor Wash (wet-on-wet, granulation)
  family: analog
  category: wash
  physicalBehavior:
    surfaceFinish: matte
    transparency: translucent (multiple washes)
    reactsToLight: no
    deforms: no
    age: ageless
  implementationStrategies:
    css: |
      mix-blend-mode: multiply;
      filter: url(#watercolor);
    svg: |
      <filter id="watercolor">
        <feTurbulence type="turbulence" baseFrequency="0.01 0.05" numOctaves="2"/>
        <feDisplacementMap in="SourceGraphic" scale="8"/>
        <feGaussianBlur stdDeviation="0.4"/>
      </filter>
      <!-- Higher numOctaves for granulation; scale ≥10 starts shifting too much -->
    raster: scanned real watercolor wash as substrate
  reactiveBehaviors:
    light: no
    highlight: no
    depth: no (paper underneath has depth)
    parallax: yes — washes layer at different scroll rates
  pairsWith:
    prototypeStyles: [aesthetic-cottagecore, aesthetic-coastal-grandmother, aesthetic-fairycore, style-doodle]
  killsTheIllusion:
    - hard edges (watercolor bleeds — edges must be soft)
    - perfectly even wash (real watercolor pools at edges)
    - no paper substrate visible through the wash
  examples:
    - Beatrix Potter botanical plates
    - children's book illustration
    - botanical print apothecary brands
  references:
    - https://codepen.io/origan/pen/YOGpjp
    - https://andyjakubowski.com/tutorial/ink-bleed-effect-with-svg-filters

- materialId: ink-wash-sumi-e
  name: Ink Wash (sumi-e / brush-and-ink)
  family: analog
  category: ink
  physicalBehavior:
    surfaceFinish: matte
    transparency: translucent
    reactsToLight: no
    deforms: no
    age: ageless
  implementationStrategies:
    css: |
      color: #1a1a1a;
      filter: url(#sumiEdge);
    svg: |
      <filter id="sumiEdge">
        <feTurbulence baseFrequency="0.04" numOctaves="2"/>
        <feDisplacementMap scale="3"/>
      </filter>
      <!-- Edge irregularity at SMALL scale — sumi brush keeps a recognizable form -->
    raster: scanned sumi-e brushwork is the most direct path
  reactiveBehaviors:
    light: no
    highlight: no
    depth: no
    parallax: minimal
  pairsWith:
    prototypeStyles: [aesthetic-anti-design, aesthetic-dark-academia, aesthetic-cottagegoth, aesthetic-vaporwave (Japanese gloss element)]
  killsTheIllusion:
    - regular vector stroke (sumi varies in pressure)
    - black at #000 (sumi ink is dark grey with brown undertone)
    - no paper bleed at terminals

- materialId: ink-bleed-on-paper
  name: Ink Bleed (fountain pen / felt-tip on uncoated)
  family: analog
  category: ink
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: no
    deforms: no
    age: ageless
  implementationStrategies:
    css: |
      filter: url(#inkBleed);
    svg: |
      <filter id="inkBleed">
        <feMorphology operator="dilate" radius="0.4"/>
        <feGaussianBlur stdDeviation="0.6"/>
        <feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 12 -4"/>
      </filter>
    raster: scanned ink for the highest fidelity
  reactiveBehaviors:
    light: no
    highlight: no
    depth: no
    parallax: no
  pairsWith:
    prototypeStyles: [style-raster-cutout, style-doodle, aesthetic-cottagecore, aesthetic-cottagegoth, aesthetic-dark-academia]
  killsTheIllusion:
    - perfect type (ink bleeds organically)
    - uniform stroke width (ink width varies with paper absorbency)

- materialId: pencil-graphite
  name: Pencil Graphite (HB to 6B sketch)
  family: analog
  category: ink
  physicalBehavior:
    surfaceFinish: matte
    transparency: translucent
    reactsToLight: yes — graphite glints at angle
    deforms: no
    age: shows wear (smudges)
  implementationStrategies:
    css: |
      mix-blend-mode: multiply;
      filter: url(#graphite) contrast(0.8);
    svg: |
      <filter id="graphite">
        <feTurbulence baseFrequency="0.7" numOctaves="2"/>
        <feColorMatrix values="0 0 0 0 0.2  0 0 0 0 0.2  0 0 0 0 0.22  0 0 0 0.5 0"/>
      </filter>
    raster: scanned graphite drawing on textured paper
  reactiveBehaviors:
    light: subtle glint on hover (pointer-driven)
    highlight: minimal
    depth: smudge on press
    parallax: no
  pairsWith:
    prototypeStyles: [style-doodle, aesthetic-dark-academia, aesthetic-corporate-grunge, aesthetic-anti-design]
  killsTheIllusion:
    - pure black (graphite is blue-grey)
    - no paper texture visible underneath
  examples:
    - architectural sketches
    - storyboards
    - magazine essay illustrations

- materialId: charcoal-drawing
  name: Charcoal Drawing (smudged, expressive)
  family: analog
  category: ink
  physicalBehavior:
    surfaceFinish: matte
    transparency: translucent
    reactsToLight: no
    deforms: no
    age: shows wear (smudge)
  implementationStrategies:
    css: |
      filter: contrast(1.3) brightness(0.85);
      mix-blend-mode: multiply;
    svg: |
      <feTurbulence baseFrequency="0.05" numOctaves="3"/>
      <feDisplacementMap scale="2"/>
      <!-- coarser than pencil — charcoal pieces are bigger -->
    raster: scanned charcoal artwork
  reactiveBehaviors:
    light: no
    highlight: no
    depth: smudge intensifies on press
    parallax: no
  pairsWith:
    prototypeStyles: [aesthetic-dark-academia, aesthetic-cottagegoth, aesthetic-anti-design]
  killsTheIllusion:
    - clean uniform fill (charcoal smudges)
    - high-saturation accents alongside (charcoal is monochrome)
```

### 4.4 Fabric and textile family

```yaml
- materialId: linen-weave
  name: Linen Weave (Apple-linen / textbook substrate)
  family: analog
  category: fabric
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: no specular
    deforms: yes — fabric drapes
    age: ageless
  implementationStrategies:
    css: |
      background:
        repeating-linear-gradient(0deg,
          transparent 0px,
          rgba(0,0,0,0.04) 1px,
          transparent 2px
        ),
        repeating-linear-gradient(90deg,
          transparent 0px,
          rgba(0,0,0,0.04) 1px,
          transparent 2px
        ),
        oklch(80% 0.02 80);  /* warm beige */
    svg: <feTurbulence baseFrequency="2"/> noise atop the weave
    raster: scanned linen as ground truth
  reactiveBehaviors:
    light: no
    highlight: no
    depth: very subtle skew on scroll (drape)
    parallax: no
  pairsWith:
    prototypeStyles: [style-skeuomorphism (iOS Game Center linen), aesthetic-cottagecore, aesthetic-coastal-grandmother, aesthetic-dark-academia]
  killsTheIllusion:
    - the weave at huge scale (you can't see it)
    - the weave at sub-pixel scale (Moiré)
    - no warmth in the colour (linen is naturally warm-cream)
  examples:
    - iOS Game Center
    - Apple Notification Center pre-iOS-7
    - book endpapers

- materialId: denim
  name: Denim (twill weave, indigo fade)
  family: analog
  category: fabric
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: no specular
    deforms: yes — soft drape
    age: acquired patina (whiskers, fade at stress points)
  implementationStrategies:
    css: |
      background:
        repeating-linear-gradient(45deg,
          oklch(35% 0.10 250) 0px,
          oklch(40% 0.10 250) 2px,
          oklch(33% 0.10 250) 4px
        );
    svg: noise + slight horizontal-fade gradient at wear points (whiskers)
    raster: scanned denim is the truth
  reactiveBehaviors:
    light: no
    highlight: no
    depth: yes — drape
    parallax: minimal
  pairsWith:
    prototypeStyles: [aesthetic-y2k-myspace, aesthetic-cottagecore, aesthetic-corporate-grunge]
  killsTheIllusion:
    - perfect uniform indigo (denim is uneven)
    - no twill direction visible
    - no fade at stress points
  examples:
    - Levi's tab stitching
    - fashion editorial denim closeups

- materialId: silk
  name: Silk (lustrous fabric)
  family: analog
  category: fabric
  physicalBehavior:
    surfaceFinish: semi-gloss
    transparency: opaque
    reactsToLight: yes — anisotropic lustre
    deforms: yes — flowing drape
    age: shows wear (fray, water spots)
  implementationStrategies:
    css: |
      background:
        linear-gradient(135deg,
          rgba(255,255,255,0.3) 0%,
          transparent 30%,
          rgba(255,255,255,0.2) 60%,
          transparent 100%
        ),
        oklch(75% 0.12 350);
    raster: silk photograph
  reactiveBehaviors:
    light: lustre band shifts with pointer angle
    highlight: yes — narrow band perpendicular to fibre direction
    depth: drape via scroll-driven skewY
    parallax: yes — gentle
  pairsWith:
    prototypeStyles: [aesthetic-y2k-futurism, aesthetic-vaporwave, aesthetic-coastal-grandmother, aesthetic-defi-cosmic]
  killsTheIllusion:
    - flat fabric (silk is always shifting in light)
    - no drape (silk hangs)

- materialId: felt
  name: Felt (matted wool, fuzzy)
  family: analog
  category: fabric
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: no specular
    deforms: yes — squashes on press
    age: ageless
  implementationStrategies:
    css: |
      background: oklch(45% 0.14 145);  /* poker green */
      filter: url(#feltFuzz);
    svg: |
      <filter id="feltFuzz">
        <feTurbulence baseFrequency="3" numOctaves="2"/>
        <feColorMatrix values="0 0 0 0 0.1  0 0 0 0 0.1  0 0 0 0 0.1  0 0 0 0.15 0"/>
      </filter>
    raster: photographed felt for accuracy
  reactiveBehaviors:
    light: no
    highlight: no
    depth: minor press deformation
    parallax: no
  pairsWith:
    prototypeStyles: [style-skeuomorphism (poker felt, billiards), aesthetic-dark-academia, aesthetic-cottagegoth]
  killsTheIllusion:
    - smooth colour with no fuzz
    - no soft edges (felt cuts soft)

- materialId: corduroy
  name: Corduroy (ribbed pile fabric)
  family: analog
  category: fabric
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: yes — directional pile reflects per-rib
    deforms: yes
    age: ageless
  implementationStrategies:
    css: |
      background:
        repeating-linear-gradient(90deg,
          rgba(0,0,0,0.18) 0px,
          transparent 6px,
          rgba(255,255,255,0.06) 8px,
          rgba(0,0,0,0.18) 12px
        ),
        oklch(50% 0.10 60);
    raster: corduroy photograph
  reactiveBehaviors:
    light: rib shadow band shifts with pointer (corduroy's signature)
    highlight: per-rib gradient updates
    depth: minor press
    parallax: no
  pairsWith:
    prototypeStyles: [aesthetic-cottagecore, aesthetic-dark-academia, aesthetic-coastal-grandmother]
  killsTheIllusion:
    - ribs without highlight asymmetry
    - rib spacing too small (becomes Moiré) or too large (becomes stripes)
```

### 4.5 Leather and skin family

```yaml
- materialId: pebbled-leather
  name: Pebbled Leather (luxury goods finish)
  family: analog
  category: leather
  physicalBehavior:
    surfaceFinish: semi-gloss
    transparency: opaque
    reactsToLight: yes — per-pebble micro-highlight
    deforms: yes — bends
    age: acquired patina (shines at touch points)
  implementationStrategies:
    css: |
      background: oklch(35% 0.04 50);
      filter: url(#pebble);
    svg: |
      <filter id="pebble">
        <feTurbulence type="fractalNoise" baseFrequency="0.18" numOctaves="3"/>
        <feSpecularLighting surfaceScale="2" specularConstant="0.8" specularExponent="20" lighting-color="#fff">
          <feDistantLight azimuth="225" elevation="45"/>
        </feSpecularLighting>
        <feComposite in2="SourceGraphic" operator="in"/>
      </filter>
    raster: scanned pebbled leather is the gold standard
  reactiveBehaviors:
    light: per-pebble highlight tracks light direction
    highlight: yes via DeviceOrientation/pointer
    depth: hover lift; press depresses
    parallax: minimal
  pairsWith:
    prototypeStyles: [style-skeuomorphism (leather wallet), aesthetic-dark-academia, aesthetic-defi-cosmic]
  killsTheIllusion:
    - perfectly uniform pebble pattern (real pebble varies)
    - no specular per pebble (luxury leather glints)
    - cold colour (leather is warm)
  examples:
    - vintage iCal leather header
    - Saffiano luxury wallets
    - bookbinding spines
  references:
    - https://leathera.com/textured-leather

- materialId: smooth-leather
  name: Smooth Leather (full-grain, polished)
  family: analog
  category: leather
  physicalBehavior:
    surfaceFinish: semi-gloss
    transparency: opaque
    reactsToLight: yes — soft specular sweep
    deforms: yes
    age: acquired patina
  implementationStrategies:
    css: |
      background:
        linear-gradient(115deg, rgba(255,255,255,0.10) 0%, transparent 35%),
        oklch(40% 0.08 40);
    svg: subtle <feTurbulence> at 0.4 baseFrequency for grain
    raster: scanned smooth leather
  reactiveBehaviors:
    light: soft specular tracks pointer at low intensity
    highlight: yes
    depth: hover lift; press inset
    parallax: minimal
  pairsWith:
    prototypeStyles: [style-skeuomorphism, aesthetic-dark-academia]
  killsTheIllusion:
    - matte uniform (smooth leather always has subtle sheen)
    - no grain variation
  examples:
    - iBooks library shelf
    - high-end notebook covers

- materialId: weathered-leather
  name: Weathered Leather (vintage, distressed)
  family: analog
  category: leather
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: minor specular at non-worn areas
    deforms: yes — creases at handle points
    age: acquired patina (cracks, discoloration)
  implementationStrategies:
    css: |
      background:
        radial-gradient(ellipse at 25% 75%, rgba(0,0,0,0.3), transparent 35%),
        radial-gradient(ellipse at 75% 25%, rgba(255,255,255,0.06), transparent 35%),
        oklch(30% 0.06 35);
    svg: |
      crack pattern via <feTurbulence baseFrequency="0.08"/> threshold-passed
    raster: photograph of real weathered leather is essential
  reactiveBehaviors:
    light: minor specular at un-worn patches
    highlight: low intensity, asymmetric
    depth: subtle crease deepening on hover
    parallax: minimal
  pairsWith:
    prototypeStyles: [aesthetic-dark-academia, aesthetic-steampunk, aesthetic-dieselpunk, aesthetic-cottagegoth, aesthetic-corporate-grunge]
  killsTheIllusion:
    - uniform wear (real wear lives at touch-points)
    - no creases at all
    - bright fresh leather colour
```

### 4.6 Film / video / capture family

```yaml
- materialId: film-grain-tri-x
  name: Film Grain — Tri-X 400 (B&W, coarse grain)
  family: analog
  category: film
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: yes — grain heavier in shadows
    deforms: no
    age: ageless
  implementationStrategies:
    css: |
      .grain { mix-blend-mode: overlay; opacity: 0.7; }
    svg: |
      <feTurbulence baseFrequency="0.9" numOctaves="2" stitchTiles="stitch"/>
      <feColorMatrix values="0 0 0 0 0.7  0 0 0 0 0.7  0 0 0 0 0.7  0 0 0 1.2 -0.6"/>
    webgl: |
      For LUMINANCE-AWARE grain: sample base image luminance per fragment,
      modulate noise amplitude inversely. Heavier grain in shadow regions
      mimics real silver-halide.
    raster: scanned 35mm Tri-X grain at 4K, looping
    video: 30fps grain video underlay (mix-blend-mode: overlay)
  reactiveBehaviors:
    light: grain density is luminance-driven, not pointer-driven
    highlight: none
    depth: none
    parallax: grain doesn't parallax (it's per-frame noise)
  pairsWith:
    prototypeStyles: [recipe-editorial-magazine, aesthetic-dark-academia, aesthetic-corporate-grunge, aesthetic-vaporwave, aesthetic-cottagegoth]
  killsTheIllusion:
    - flat-opacity grain over everything (grain follows luminance)
    - too-fine grain (Tri-X is COARSE)
    - colour grain (Tri-X is B&W)
    - static grain not animating per frame (real film moves)
  examples:
    - Filmbox film emulation
    - Caleb Salvadori Lightroom presets
    - editorial photography
  references:
    - https://videovillage.com/filmbox/

- materialId: film-grain-portra-400
  name: Film Grain — Portra 400 (colour, fine grain, warm)
  family: analog
  category: film
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: yes — heavier in shadow
    deforms: no
    age: ageless
  implementationStrategies:
    css: |
      mix-blend-mode: overlay;
      opacity: 0.4;
      filter: saturate(0.92) hue-rotate(2deg);
    svg: |
      finer noise — baseFrequency="1.4"
    raster: scanned Portra grain looping
  reactiveBehaviors:
    light: luminance-aware
    highlight: none
    depth: none
    parallax: none
  pairsWith:
    prototypeStyles: [aesthetic-coastal-grandmother, aesthetic-cottagecore, recipe-editorial-magazine, aesthetic-cottagegoth]
  killsTheIllusion:
    - too coarse grain (Portra is fine)
    - cold colour grade (Portra is warm)
  examples:
    - Magnum portraits
    - lifestyle editorial

- materialId: film-grain-cinestill-800t
  name: Film Grain — CineStill 800T (tungsten, halation, neon glow)
  family: analog
  category: film
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: yes — bright lights bloom with red halation
    deforms: no
    age: ageless
  implementationStrategies:
    css: |
      filter: contrast(1.05) saturate(0.95);
    svg: |
      <feGaussianBlur stdDeviation="2"/>
      <feColorMatrix values="1.2 0 0 0 0  0 0.9 0 0 0  0 0 0.85 0 0  0 0 0 1 0"/>
      <!-- red boom at highlights — the CineStill signature -->
    webgl: |
      threshold luminance, dilate red channel, additive composite — gives
      authentic halation around lamp posts and signs
    raster: CineStill scan loop
  reactiveBehaviors:
    light: red halation tracks high-luminance regions
    highlight: no separate
    depth: no
    parallax: no
  pairsWith:
    prototypeStyles: [aesthetic-cyberpunk, aesthetic-vaporwave, aesthetic-cassette-futurism, recipe-editorial-magazine]
  killsTheIllusion:
    - halation everywhere (must be tied to bright spots)
    - flat blue tungsten (CineStill has WARM-red halation against the cool base)

- materialId: vhs-distortion
  name: VHS Distortion (chromatic aberration + scanlines + bleed)
  family: analog
  category: film
  physicalBehavior:
    surfaceFinish: glossy
    transparency: opaque
    reactsToLight: no
    deforms: yes — tape head distortion bands
    age: shows wear (drop-outs)
  implementationStrategies:
    css: |
      filter: contrast(1.05) saturate(1.1);
    svg: |
      <feOffset in="SourceGraphic" dx="2" dy="0" result="R"/>
      <feOffset in="SourceGraphic" dx="-2" dy="0" result="B"/>
      <feColorMatrix in="R" values="1 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0"/>
      <feColorMatrix in="B" values="0 0 0 0 0  0 0 0 0 0  0 0 1 0 0  0 0 0 1 0"/>
      <feBlend mode="screen"/>
    webgl: |
      RGB-shift in fragment shader; horizontal scanline darken; periodic
      vertical roll bar at 6s interval (the tape-tracking jitter)
    raster: real VHS rip overlay at multiply
    video: looping VHS distortion source at overlay
  reactiveBehaviors:
    light: no
    highlight: no
    depth: no
    parallax: no
  pairsWith:
    prototypeStyles: [aesthetic-vaporwave, aesthetic-cassette-futurism, aesthetic-cyberpunk, aesthetic-y2k-myspace, aesthetic-acid-graphics]
  killsTheIllusion:
    - static RGB shift (real VHS varies)
    - no scanlines (VHS interlace is signature)
    - no horizontal bleed
  examples:
    - 90s home video aesthetic
    - vaporwave music videos
  references:
    - https://halisavakis.com/write-up-vhs-image-effect/

- materialId: polaroid-instant
  name: Polaroid / Instant Photo (square frame, faded chemistry)
  family: analog
  category: film
  physicalBehavior:
    surfaceFinish: glossy
    transparency: opaque
    reactsToLight: yes — reflective sheen
    deforms: minimal
    age: acquired patina (yellowing, fade)
  implementationStrategies:
    css: |
      .polaroid {
        background: #f4ede1;
        padding: 12px 12px 56px;
        box-shadow:
          0 1px 2px rgba(0,0,0,0.2),
          0 14px 28px -8px rgba(0,0,0,0.4);
        transform: rotate(-2deg);
        font-family: 'Caveat', cursive;
      }
      .polaroid img { filter: saturate(0.85) contrast(0.95); }
    raster: polaroid frame PNG
  reactiveBehaviors:
    light: subtle gloss on hover
    highlight: minimal
    depth: hover lifts the frame
    parallax: in scrapbook layouts, yes
  pairsWith:
    prototypeStyles: [style-raster-cutout, aesthetic-cottagecore, aesthetic-y2k-myspace, aesthetic-coastal-grandmother, recipe-readcv]
  killsTheIllusion:
    - all polaroids at the same angle (real ones scatter)
    - no chemistry fade
    - caption in a digital font (must be handwritten)
```

### 4.7 Distress / age family

```yaml
- materialId: dust-scratches
  name: Dust + Scratches (archival distress)
  family: analog
  category: digital-effect
  physicalBehavior:
    surfaceFinish: matte
    transparency: translucent
    reactsToLight: no
    deforms: no
    age: acquired patina
  implementationStrategies:
    css: |
      .distress::after {
        content: '';
        position: absolute; inset: 0;
        background-image: url('dust-scratches-overlay.png');
        mix-blend-mode: screen;
        opacity: 0.4;
        pointer-events: none;
      }
    svg: |
      sparse Voronoi spots + <feTurbulence> at low baseFrequency for sub-pixel scratch lines
    raster: dust + scratches overlay at 2048×2048
  reactiveBehaviors:
    light: no
    highlight: no
    depth: no
    parallax: yes — dust at FIXED layer (not parallaxed) gives "screen dust"
  pairsWith:
    prototypeStyles: [aesthetic-vaporwave, aesthetic-cottagegoth, aesthetic-dark-academia, aesthetic-corporate-grunge, recipe-editorial-magazine]
  killsTheIllusion:
    - regular spacing of "scratches"
    - same overlay tiled visibly
    - high opacity dust (must be subtle)

- materialId: foxing-stain
  name: Foxing / Tea Stain (paper aging)
  family: analog
  category: digital-effect
  physicalBehavior:
    surfaceFinish: matte
    transparency: translucent
    reactsToLight: no
    deforms: no
    age: acquired patina
  implementationStrategies:
    css: |
      background:
        radial-gradient(ellipse at 18% 24%, oklch(70% 0.12 60 / 0.4) 0%, transparent 18%),
        radial-gradient(ellipse at 85% 65%, oklch(60% 0.10 50 / 0.3) 0%, transparent 22%),
        var(--paper);
      mix-blend-mode: multiply;
    raster: scanned aged-paper for ground truth
  reactiveBehaviors:
    light: no
    highlight: no
    depth: no
    parallax: tied to paper layer
  pairsWith:
    prototypeStyles: [style-serif-warm-paper, aesthetic-dark-academia, aesthetic-cottagecore, aesthetic-cottagegoth]
  killsTheIllusion:
    - symmetric stains (real foxing is asymmetric, lives where moisture pooled)
    - stains over photos (paper-edge-only)

- materialId: torn-edge
  name: Torn Edge (paper / fabric / film)
  family: analog
  category: digital-effect
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: no
    deforms: yes
    age: ageless (or shows wear)
  implementationStrategies:
    css: |
      mask-image: url(torn-edge.svg);
      mask-size: cover;
      filter: drop-shadow(0 2px 1px rgba(0,0,0,0.18));
    svg: |
      irregular fractal-noise mask along one edge:
      <feTurbulence baseFrequency="0.06"/> + <feComponentTransfer> threshold
    raster: torn-paper PNG with alpha
  reactiveBehaviors:
    light: small shadow on hover
    highlight: no
    depth: hover lift 2px
    parallax: optional
  pairsWith:
    prototypeStyles: [style-raster-cutout, aesthetic-cottagecore, aesthetic-y2k-myspace, aesthetic-corporate-grunge]
  killsTheIllusion:
    - rounded "torn" edges (real tear is irregular and SHARP at peaks)
    - same tear pattern repeated
  examples:
    - Hack Club Scrapbook
    - SSENSE editorial torn type
```

### 4.8 Wood, stone, organic family

```yaml
- materialId: wood-grain-walnut
  name: Wood Grain (walnut, dark, vertical grain)
  family: analog
  category: wood
  physicalBehavior:
    surfaceFinish: semi-gloss (varnished) or matte (raw)
    transparency: opaque
    reactsToLight: yes — anisotropic along grain
    deforms: no
    age: acquired patina (darkening over time)
  implementationStrategies:
    css: |
      background:
        linear-gradient(180deg, oklch(35% 0.08 40) 0%, oklch(22% 0.06 30) 100%);
      filter: url(#grain);
    svg: |
      <filter id="grain">
        <feTurbulence type="turbulence" baseFrequency="0.02 0.3" numOctaves="3"/>
        <feColorMatrix values="0 0 0 0 0.1  0 0 0 0 0.06  0 0 0 0 0.04  0 0 0 0.4 0"/>
      </filter>
      /* baseFrequency y ≫ x → vertical grain */
    raster: scanned walnut at 2048px, mask with noise to hide tile seam
  reactiveBehaviors:
    light: glint travels along grain on tilt
    highlight: yes — narrow strip along grain
    depth: minor for varnished
    parallax: no
  pairsWith:
    prototypeStyles: [style-skeuomorphism (library-as-wood-shelf), aesthetic-cottagecore, aesthetic-steampunk, aesthetic-dark-academia]
  killsTheIllusion:
    - regularly repeating tile (mask with noise)
    - isotropic noise (wood grain is directional)
    - perfect varnish gloss without grain
  examples:
    - iBooks wooden shelf
    - GarageBand stage skin
    - vintage radio cabinets

- materialId: marble
  name: Marble (veined stone)
  family: analog
  category: stone
  physicalBehavior:
    surfaceFinish: glossy (polished) or matte (honed)
    transparency: opaque
    reactsToLight: yes — soft sheen
    deforms: no
    age: ageless
  implementationStrategies:
    css: |
      background:
        radial-gradient(ellipse at 30% 20%, rgba(255,255,255,0.2), transparent 35%),
        linear-gradient(135deg, oklch(96% 0.005 0) 0%, oklch(85% 0.008 250) 100%);
      filter: url(#vein);
    svg: |
      <filter id="vein">
        <feTurbulence type="turbulence" baseFrequency="0.012" numOctaves="3"/>
        <feColorMatrix values="0 0 0 0 0.4  0 0 0 0 0.4  0 0 0 0 0.45  0 0 0 0.6 -0.4"/>
        <feComposite in2="SourceGraphic" operator="in"/>
      </filter>
    raster: photographed marble is the highest fidelity
  reactiveBehaviors:
    light: soft sheen tracks pointer
    highlight: yes
    depth: no
    parallax: minimal
  pairsWith:
    prototypeStyles: [aesthetic-dark-academia, aesthetic-defi-cosmic, aesthetic-vaporwave (the marble bust!), recipe-editorial-magazine]
  killsTheIllusion:
    - veins drawn perfectly (real marble is organic chaos)
    - matte without sheen (most marble is polished)

- materialId: concrete
  name: Concrete (raw industrial)
  family: analog
  category: stone
  physicalBehavior:
    surfaceFinish: matte
    transparency: opaque
    reactsToLight: no specular
    deforms: no
    age: shows wear (cracks, stains)
  implementationStrategies:
    css: |
      background: oklch(70% 0.005 250);
      filter: url(#concrete);
    svg: |
      <filter id="concrete">
        <feTurbulence baseFrequency="0.6" numOctaves="3"/>
        <feColorMatrix values="0 0 0 0 0.4  0 0 0 0 0.4  0 0 0 0 0.4  0 0 0 0.2 0"/>
      </filter>
    raster: concrete photograph is direct
  reactiveBehaviors:
    light: no
    highlight: no
    depth: no
    parallax: no
  pairsWith:
    prototypeStyles: [aesthetic-web-brutalism, aesthetic-corporate-grunge, aesthetic-cassette-futurism, recipe-brutalist-web]
  killsTheIllusion:
    - too clean (concrete is messy)
    - no cracks or stains
    - flat colour with no aggregate visible
  examples:
    - Bauhaus poster substrates
    - architectural photo overlays
```

---

## 5. Hybrid / cross-over materials

Materials that combine digital + analog grammar — each one is a stack of two or more materials from §3 or §4, applied as a single committed surface.

```yaml
- materialId: scanned-glass
  name: Scanned Glass (digital glass on analog paper substrate)
  family: hybrid
  category: glass
  physicalBehavior:
    surfaceFinish: glossy
    transparency: translucent
    reactsToLight: yes
    deforms: no
    age: shows wear
  implementationStrategies:
    css: |
      /* Layer 1: paper substrate. Layer 2: glass panel. */
      background:
        url('paper-texture.jpg'),
        rgba(255,255,255,0.18);
      backdrop-filter: blur(20px) saturate(180%);
    svg: paper grain + glass refraction filters stacked
    raster: REQUIRED — paper substrate is the load-bearing element
  reactiveBehaviors:
    light: glass highlight tracks pointer; paper substrate doesn't
    highlight: yes
    depth: hover lift glass slightly above paper
    parallax: paper stays put; glass moves with viewport
  pairsWith:
    prototypeStyles: [aesthetic-cottagegoth, aesthetic-dark-academia, recipe-editorial-magazine]
  killsTheIllusion:
    - both layers at same z (glass must SIT ON paper)
    - no paper grain visible behind glass
  examples:
    - editorial book design (glass insert over endpaper)
    - museum archival labels (modern UI under aged paper)

- materialId: risograph-glass
  name: Risograph-Glass (frosted glass under riso grain)
  family: hybrid
  category: glass
  physicalBehavior:
    surfaceFinish: matte
    transparency: translucent
    reactsToLight: minimal
    deforms: no
    age: ageless
  implementationStrategies:
    css: |
      backdrop-filter: blur(20px) saturate(160%);
      mix-blend-mode: multiply;
    svg: |
      stack riso ink halftone over glass panel, slight offset
    raster: riso grain overlay + photographic substrate
  reactiveBehaviors:
    light: no — riso kills the gloss
    highlight: no
    depth: hover lift only
    parallax: substrate parallaxes
  pairsWith:
    prototypeStyles: [aesthetic-acid-design, aesthetic-corporate-grunge, aesthetic-y2k-myspace]
  killsTheIllusion:
    - glass sheen visible through the riso (riso must dominate top)

- materialId: vhs-frutiger
  name: VHS-Frutiger (Frutiger Aero with VHS distortion)
  family: hybrid
  category: digital-effect
  physicalBehavior:
    surfaceFinish: glossy
    transparency: translucent
    reactsToLight: yes
    deforms: yes — VHS tracking bars
    age: shows wear (drop-outs)
  implementationStrategies:
    css: |
      filter: contrast(1.05) saturate(1.05);
    svg: glass panel + VHS chromatic-aberration filter stack
    raster: photographic plate + VHS overlay
    video: 30fps VHS distortion loop atop the Frutiger glass scene
  reactiveBehaviors:
    light: glass highlight via pointer; VHS shifts at periodic intervals
    highlight: yes
    depth: minimal
    parallax: substrate parallaxes
  pairsWith:
    prototypeStyles: [aesthetic-vaporwave, aesthetic-y2k-myspace, aesthetic-cassette-futurism]
  killsTheIllusion:
    - VHS effect blocking the Frutiger water/sky motif (riso-style overlay should let plate through)
  examples:
    - corporate-melancholic Vektroid record sleeves
    - PrismCorp fake-multinational catalogues

- materialId: holographic-paper
  name: Holographic-Paper (iridescent foil on textured paper)
  family: hybrid
  category: iridescent
  physicalBehavior:
    surfaceFinish: glossy
    transparency: opaque
    reactsToLight: yes — strong on foil, none on paper
    deforms: yes — paper underneath
    age: ageless
  implementationStrategies:
    css: |
      /* foil regions get the holographic recipe; rest is paper */
      background:
        url('paper-grain.jpg'),
        conic-gradient(in oklch from 45deg, /* full iridescence */) ;
    raster: paper texture as ground; holographic mask
  reactiveBehaviors:
    light: foil reacts to pointer/gyro; paper doesn't
    highlight: yes — masked to foil region only
    depth: paper deformation possible
    parallax: paper static; foil rotates with gyro
  pairsWith:
    prototypeStyles: [style-holographic, aesthetic-y2k-futurism, recipe-editorial-magazine]
  killsTheIllusion:
    - iridescence over the whole card (must be foil REGIONS, like a Pokemon card)
  examples:
    - foil-stamped business cards
    - Pokemon card (the canonical reference)

- materialId: paper-with-watercolor
  name: Paper with Watercolor (botanical illustration substrate)
  family: hybrid
  category: paper
  physicalBehavior:
    surfaceFinish: matte
    transparency: translucent (washes)
    reactsToLight: no
    deforms: yes
    age: shows wear
  implementationStrategies:
    css: |
      background: var(--paper);
    svg: |
      paper grain layer + watercolor wash filter layer; multiply blend
    raster: scanned watercolor on watercolor paper
  reactiveBehaviors:
    light: no
    highlight: no
    depth: no
    parallax: paper static; wash subtle scroll-bind
  pairsWith:
    prototypeStyles: [aesthetic-cottagecore, aesthetic-coastal-grandmother, aesthetic-fairycore]
  killsTheIllusion:
    - watercolor without paper texture (looks plastic)
    - watercolor with hard edges
  examples:
    - Beatrix Potter
    - children's book illustration

- materialId: chrome-on-velvet
  name: Chrome on Velvet (Y2K luxury substrate)
  family: hybrid
  category: metal
  physicalBehavior:
    surfaceFinish: metallic (chrome) on matte (velvet)
    transparency: opaque
    reactsToLight: yes — strong
    deforms: no
    age: ageless
  implementationStrategies:
    css: |
      /* chrome chip atop a deeply textured velvet background */
      background:
        radial-gradient(ellipse at 50% 50%, oklch(15% 0.02 320) 0%, oklch(8% 0.01 320) 100%);
      filter: url(#velvetNap);  /* on the substrate only */
    raster: velvet substrate scan + chrome objects
  reactiveBehaviors:
    light: chrome reacts; velvet does not
    highlight: yes — strong on chrome
    depth: no
    parallax: minimal
  pairsWith:
    prototypeStyles: [aesthetic-urbling, aesthetic-defi-cosmic, aesthetic-y2k-futurism, style-holographic]
  killsTheIllusion:
    - velvet that looks like flat dark grey
    - chrome at low saturation
  examples:
    - hip-hop album-cover lineage
    - luxury watch ads
```

---

## 6. Reactive-behaviour reference

The orchestrator dispatches reactive behaviour by INPUT MODALITY, not by material. Each modality has its own permission gating, support, and battery profile.

### 6.1 pointermove (desktop + touch)

- **Support:** Universal (W3C Pointer Events; all modern browsers).
- **Permission:** None.
- **Mobile-vs-desktop:** Works on both, BUT on mobile, hover state is fired on tap and held until next tap. Use `(pointer: fine)` media query to gate hover-only effects.
- **Battery cost:** Low if throttled to `requestAnimationFrame`. High if you transform on every event (60+ Hz on a 120 Hz device).
- **Reduced-motion fallback:** Disable transforms; keep static state.
- **Pattern:**
  ```js
  let pending = false;
  el.addEventListener('pointermove', e => {
    if (pending) return;
    pending = true;
    requestAnimationFrame(() => {
      const r = el.getBoundingClientRect();
      el.style.setProperty('--px', ((e.clientX - r.left) / r.width - 0.5).toFixed(3));
      el.style.setProperty('--py', ((e.clientY - r.top) / r.height - 0.5).toFixed(3));
      pending = false;
    });
  });
  ```
- **Used by:** holographic-foil, liquid-glass, chrome-mirror, silk, pebbled-leather, ceramic-glaze, marble.

### 6.2 DeviceOrientationEvent (mobile gyro)

- **Support:** iOS Safari 13+ (with permission), Android Chrome (auto). Desktop browsers do not support.
- **Permission:** iOS 13+ requires `DeviceOrientationEvent.requestPermission()` called from a user gesture handler; HTTPS only. Android grants without prompt.
- **Mobile-vs-desktop:** Mobile only — desktop must fall back to `pointermove` or no-op.
- **Battery cost:** Moderate. Throttle to 30 Hz max.
- **Reduced-motion fallback:** Freeze to centered (gamma=0, beta=0) state.
- **Pattern:**
  ```js
  async function enableGyro() {
    if (typeof DeviceOrientationEvent.requestPermission === 'function') {
      const result = await DeviceOrientationEvent.requestPermission();
      if (result !== 'granted') return;
    }
    window.addEventListener('deviceorientation', e => {
      // gamma: left/right tilt (-90..90); beta: front/back (-180..180)
      el.style.setProperty('--gx', (e.gamma / 30).toFixed(3));
      el.style.setProperty('--gy', (e.beta / 30).toFixed(3));
    });
  }
  ```
- **Used by:** holographic-foil, liquid-glass, chrome-mirror, brushed-aluminum, silk.

### 6.3 scroll (universal)

- **Support:** Universal. CSS Scroll-driven Animations (Chrome/Edge 115+, Safari 26+, Firefox behind flag).
- **Permission:** None.
- **Battery cost:** Low — use `scroll-timeline` to avoid main-thread blocking.
- **Reduced-motion fallback:** Disable parallax; keep layers at scroll = 1.
- **Pattern (CSS scroll-driven):**
  ```css
  @keyframes parallax-bg {
    from { transform: translateY(0); }
    to   { transform: translateY(-30%); }
  }
  .substrate {
    animation: parallax-bg linear;
    animation-timeline: scroll();
  }
  ```
- **Pattern (JS, IntersectionObserver-aware):**
  ```js
  document.addEventListener('scroll', () => {
    document.documentElement.style.setProperty('--scroll', window.scrollY);
  }, { passive: true });
  ```
- **Used by:** all materials with layered substrate (frosted-glass, aurora-mesh, scanned-glass, paper-with-watercolor).

### 6.4 pointerdown / press (universal)

- **Support:** Universal.
- **Permission:** None.
- **Battery cost:** Negligible.
- **Reduced-motion fallback:** Subtle opacity change instead of scale or ripple.
- **Pattern (CSS-only press):**
  ```css
  .button {
    transition: transform 0.15s, box-shadow 0.15s;
  }
  .button:active {
    transform: scale(0.97);
    box-shadow: inset 6px 6px 12px rgba(0,0,0,0.2);
  }
  ```
- **Used by:** matte-clay, soft-ui-foam, glossy-plastic-aqua, material-tonal-surface (ripple), liquid-glass.

### 6.5 prefers-reduced-motion (universal baseline)

- **Support:** Universal in modern browsers.
- **Permission:** None — driven by OS setting.
- **Battery cost:** Reduces it.
- **Pattern (CSS):**
  ```css
  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
      animation-duration: 0.01ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: 0.01ms !important;
      scroll-behavior: auto !important;
    }
    /* For material-orchestrator: freeze gyro/pointer-driven highlights to centered state */
    [data-reactive] {
      --px: 0; --py: 0; --gx: 0; --gy: 0;
    }
  }
  ```
- **Discipline:** Every reactive material MUST set sensible defaults for the CSS custom props it reads. The reduced-motion override pins those props to neutral and the material falls back to a static, centered state. NEVER hide a material entirely under reduced-motion — it must still be visible, just still.

### 6.6 prefers-reduced-transparency / prefers-contrast (Apple HIG)

- **Support:** Safari/macOS only.
- **Permission:** Driven by OS.
- **Pattern:**
  ```css
  @media (prefers-reduced-transparency: reduce) {
    .glass {
      backdrop-filter: none;
      background: rgb(28,28,36);
    }
  }
  @media (prefers-contrast: more) {
    .glass {
      border: 1.5px solid currentColor;
    }
  }
  ```
- **Used by:** all glass materials.

---

## 7. Prototype-style decision tree

> **Normalised schema (read this before parsing the table below).** Every entry conforms to:
>
> - **Column 1 — `Prototype slug`** — kebab-case slug from prototype.md (recipes, aesthetics, styles, shells). May be wrapped in backticks for visual distinction. Orchestrators match their `committedAesthetic` envelope field against this. Exact-match only; no fuzzy matching.
> - **Column 2 — `Primary material(s)`** — comma-separated `materialId`s (kebab-case, match §2-§5 entries). Default pick is the FIRST entry; orchestrator may apply multiple primaries to different element roles on the page (e.g. card surface + decorative shape + image bg).
> - **Column 3 — `Secondary material(s)`** — additional materials for layered application (e.g. paper PRIMARY + foxing-stain SECONDARY overlay). Used to compose effects.
> - Some rows include explicit "no material — flat is the brief" or "anti-pattern" callouts. Orchestrator MUST honour these — refuse to dispatch material fidelity for those slugs.
>
> The same schema is mirrored in `photography-library.md §3` and `illustration-library.md §3`.

Mapping from prototype.md slugs to applicable materials. The orchestrator consults this table when walking a HTML tree and reading the `GENRE` comment.

| Prototype slug | Primary material(s) | Secondary material(s) |
|---|---|---|
| `style-glassmorphism` | frosted-glass, thin-glass-chip | aurora-mesh (substrate) |
| `style-liquid-glass` | liquid-glass | aurora-mesh, oil-on-water (substrate) |
| `style-claymorphism` | matte-clay | aurora-mesh (background) |
| `style-neumorphism` | soft-ui-foam | (single-material genre) |
| `style-holographic` | holographic-foil, oil-on-water | dust-scratches |
| `style-skeuomorphism` | linen-weave, walnut-grain, pebbled-leather, smooth-leather, weathered-leather, felt, legal-pad, glossy-plastic-aqua | letterpress-emboss, brushed-aluminum |
| `style-aurorism` | aurora-mesh | (single-material genre) |
| `style-material-m3` | material-tonal-surface | (single-material genre) |
| `style-raster-cutout` | uncoated-paper, kraft-paper, torn-edge, polaroid-instant, photocopy-xerox, ink-bleed-on-paper, dust-scratches | washi-tape (raster decoration) |
| `style-serif-warm-paper` | uncoated-paper, letterpress-emboss | foxing-stain (optional) |
| `style-neubrutalism` | (no material — flat) | (anti-pattern: don't apply material) |
| `style-pixel-bitmap` | pixel-bitmap, crt-phosphor (overlay) | dithered-1bit |
| `style-terminal-mono` | ascii-art-surface, crt-phosphor | dithered-1bit |
| `style-doodle` | uncoated-paper, ink-bleed-on-paper, pencil-graphite | watercolor-wash |
| `style-cream-humanist` | uncoated-paper, vellum-translucency | foxing-stain |
| `style-restrained-hairline` | (no material — restraint is the brief) | (single subtle paper grain at <2%) |
| `style-oversized-neo-grotesque` | (no material) | film-grain-tri-x (optional) |
| `style-bold-display` | aurora-mesh (optional) | film-grain-portra-400 (optional) |
| `style-dense-mono-dark` | crt-phosphor (subtle), ascii-art-surface | (mostly material-less) |
| `style-flat-design` | (no material — flat is the brief) | (anti-pattern: don't apply material) |
| `style-brutalist-raw` | concrete | photocopy-xerox |
| `style-outline-wireframe` | (no material) | (anti-pattern: don't apply material) |
| `style-material-m1m2` | material-tonal-surface (legacy mode) | (single) |
| `style-sf-pro-ios` | thin-glass-chip, frosted-glass | (Apple chrome materials) |
| `style-agate-broadsheet` | uncoated-paper | halftone-cmyk (photos) |
| `aesthetic-frutiger-aero` | glossy-plastic-aqua, frosted-glass | aurora-mesh, holographic-foil |
| `aesthetic-frutiger-dark-aero` | glossy-plastic-aqua (dark), liquid-glass | aurora-mesh (dark) |
| `aesthetic-frutiger-chromecore` | chrome-mirror, holographic-foil | aurora-mesh |
| `aesthetic-frutiger-eco` | matte-clay, soft-ui-foam | watercolor-wash |
| `aesthetic-frutiger-bright-tertiaries` | glossy-plastic-aqua | matte-clay |
| `aesthetic-frutiger-four-colors` | glossy-plastic-aqua (saturated CMYK) | (single) |
| `aesthetic-frutiger-tranquil-serenity` | soft-ui-foam, vellum-translucency | aurora-mesh |
| `aesthetic-frutiger-dorfic` | brushed-aluminum, concrete | film-grain-tri-x |
| `aesthetic-y2k-futurism` | chrome-mirror, holographic-foil, glossy-plastic-aqua | liquid-glass |
| `aesthetic-y2k-myspace` | photocopy-xerox, polaroid-instant, dust-scratches | torn-edge |
| `aesthetic-y2k-memphis-loud` | coated-glossy-paper, halftone-cmyk | (single) |
| `aesthetic-vaporwave` | marble, vhs-distortion, polaroid-instant, film-grain-cinestill-800t | dust-scratches |
| `aesthetic-cyberpunk` | crt-phosphor, vhs-distortion, film-grain-cinestill-800t | chrome-mirror |
| `aesthetic-cassette-futurism` | brushed-aluminum, crt-phosphor, vhs-distortion | film-grain-tri-x |
| `aesthetic-atompunk` | brushed-aluminum, crt-phosphor | (Frutiger-Aero-era plastics) |
| `aesthetic-dieselpunk` | brushed-aluminum, weathered-leather, copper-patina | concrete |
| `aesthetic-steampunk` | walnut-grain, copper-patina, gold-leaf, weathered-leather, parchment | brushed-aluminum |
| `aesthetic-solarpunk` | aurora-mesh, watercolor-wash | uncoated-paper |
| `aesthetic-cottagecore` | uncoated-paper, kraft-paper, linen-weave, watercolor-wash, polaroid-instant, paper-with-watercolor, ink-bleed-on-paper | foxing-stain, torn-edge |
| `aesthetic-cottagegoth` | uncoated-paper, foxing-stain, ink-bleed-on-paper, photocopy-xerox, dust-scratches | charcoal-drawing |
| `aesthetic-coastal-grandmother` | linen-weave, polaroid-instant, film-grain-portra-400 | uncoated-paper |
| `aesthetic-dark-academia` | uncoated-paper, weathered-leather, walnut-grain, parchment, gold-leaf, marble, charcoal-drawing, pencil-graphite | foxing-stain, letterpress-emboss |
| `aesthetic-fairycore` | watercolor-wash, paper-with-watercolor | (single) |
| `aesthetic-goblincore` | kraft-paper, weathered-leather | (organic distress stack) |
| `aesthetic-dreamcore` | film-grain-portra-400, dust-scratches | (single) |
| `aesthetic-angelcore` | aurora-mesh, holographic-foil | film-grain-portra-400 |
| `aesthetic-positivity-kawaii` | matte-clay, soft-ui-foam | (single) |
| `aesthetic-curly-girly` | photocopy-xerox, halftone-cmyk | matte-clay |
| `aesthetic-corporate-grunge` | photocopy-xerox, halftone-cmyk, dust-scratches, charcoal-drawing | torn-edge |
| `aesthetic-corporate-memphis` | matte-clay, glossy-plastic-aqua | (single) |
| `aesthetic-web-brutalism` | concrete, dithered-1bit | photocopy-xerox |
| `aesthetic-neubrutalism` | (no material — flat is the brief) | (anti-pattern) |
| `aesthetic-acid-design` | risograph, halftone-cmyk, silkscreen | photocopy-xerox |
| `aesthetic-acid-graphics` | risograph, photocopy-xerox, halftone-cmyk | (single) |
| `aesthetic-avantropop` | risograph, halftone-cmyk | (single) |
| `aesthetic-anti-design` | uncoated-paper, ink-wash-sumi-e | charcoal-drawing |
| `aesthetic-bauhaus` | silkscreen, halftone-cmyk | (constructed) |
| `aesthetic-constructivism` | silkscreen, halftone-cmyk, photocopy-xerox | (single) |
| `aesthetic-de-stijl` | (no material — flat) | (anti-pattern) |
| `aesthetic-swiss-modernist` | (no material) | (single subtle uncoated paper at most) |
| `aesthetic-defi-cosmic` | holographic-foil, gold-leaf, chrome-mirror, marble | aurora-mesh |
| `aesthetic-depin-hardware` | brushed-aluminum, concrete | crt-phosphor |
| `aesthetic-crypto-degen` | chrome-mirror, holographic-foil | crt-phosphor |
| `aesthetic-rgb-gamer` | crt-phosphor, holographic-foil | (single) |
| `aesthetic-cluttercore` | (every analog material in the library) | (intentional pile) |
| `aesthetic-maximalism` | (every material — considered abundance) | (curated pile) |
| `aesthetic-urbling` | chrome-mirror, gold-leaf, chrome-on-velvet | holographic-foil |
| `aesthetic-wacky-pomo` | glossy-plastic-aqua, halftone-cmyk | (Nickelodeon plastics) |
| `aesthetic-pixel-*` | pixel-bitmap, crt-phosphor, dithered-1bit | (genre-locked) |
| `aesthetic-pc-98` | pixel-bitmap, crt-phosphor | (single) |
| `aesthetic-vector-*` | (no material — vector is the brief) | (anti-pattern) |
| `aesthetic-op-art` | (no material) | (anti-pattern) |
| `aesthetic-8-bit-generic` | pixel-bitmap | (single) |
| `recipe-editorial-magazine` | uncoated-paper, coated-glossy-paper, halftone-cmyk, film-grain-portra-400 | letterpress-emboss, foxing-stain |
| `recipe-newspaper-of-record` | uncoated-paper, halftone-cmyk | (newsprint substrate) |
| `recipe-aurora-marketing` | aurora-mesh | (single) |
| `recipe-restrained-ai-marketing` | (no material — restraint) | (subtle paper grain at most) |
| `recipe-scientific-infra-marketing` | (no material) | (subtle aurora-mesh) |
| `recipe-bento-marketing` | (no material baseline) | aurora-mesh in hero |
| `recipe-ai-foundry-dark` | aurora-mesh (dark), crt-phosphor (subtle) | (single) |
| `recipe-devtools-marketing` | aurora-mesh | (single) |
| `recipe-bloomberg-dashboard` | (no material — dense) | (anti-pattern) |
| `recipe-linear-product-ui` | (no material — product) | aurora-mesh in marketing hero only |
| `recipe-ios-system` | thin-glass-chip, frosted-glass, liquid-glass | (Apple chrome) |
| `recipe-material-3` | material-tonal-surface | (single) |
| `recipe-terminal-on-web` | crt-phosphor, ascii-art-surface, dithered-1bit | (single) |
| `recipe-brutalist-web` | concrete, photocopy-xerox | (single) |
| `recipe-swiss-grid` | (no material) | (subtle paper at most) |
| `recipe-neo-grotesque-portfolio` | (no material) | film-grain-tri-x in photos |
| `recipe-readcv` | polaroid-instant, uncoated-paper | torn-edge |
| `recipe-warm-restraint` | uncoated-paper, vellum-translucency | (single) |
| `recipe-y2k-memphis-loud` | coated-glossy-paper, halftone-cmyk | risograph |
| `shell-scrapbook-substrate` | uncoated-paper, kraft-paper, polaroid-instant, torn-edge, dust-scratches | (the substrate is the material) |
| `shell-terminal-frame` | crt-phosphor, ascii-art-surface | (single) |
| `shell-canvas-floating` | frosted-glass, liquid-glass | (over photographic plate) |

Rule of thumb the orchestrator applies: when a slug appears in BOTH the prototype playbook's "Pairs well with" list and this material table, it's a confirmed material pairing. When a slug says "no material — flat is the brief", the orchestrator MUST refuse to apply material (committing siteCount=0 is the correct outcome).

---

## 8. Anti-patterns

The single highest-value contribution of this dossier — common AI-tells the orchestrator must catch and refuse.

### 8.1 Glass anti-patterns

- **Flat `box-shadow: 0 4px 12px rgba(0,0,0,0.1)` on glassmorphism.** Glass casts DIFFUSE shadows. Must be `0 8px 32px rgba(0,0,0,0.18), 0 2px 8px rgba(0,0,0,0.08)` (multi-layer, larger blur, lower opacity).
- **Glass on flat white.** Backdrop-blur over a flat `#fff` page refracts nothing and reads as fogged plastic. Substrate is non-negotiable.
- **Missing the 1px inset white top-edge highlight.** Without it, the panel is a sticker, not a lens.
- **No `saturate(160-180%)` boost.** Blur drains chroma; without the boost the glass looks like grey gauze.
- **Glass nested inside glass.** The Apple HIG explicitly forbids it; more than 2 z-depths of blur compounds to mush.
- **Refraction displacement applied to text.** Above `feDisplacementMap scale="20"` text becomes illegible. Apply to chrome shapes only.
- **Conic-gradient rainbow rim shimmer.** The TikTok-glass tell.
- **Heavy 2021-era drop-shadow clouds.** Liquid Glass uses contact shadow + inset specular only.

### 8.2 Claymorphism anti-patterns

- **Every container puffed.** Clay is a moment, not a system. ONE clay surface per screen.
- **Black drop shadow instead of surface-hue-tinted.** Clay shadows take a desaturated version of the surface hue — never `rgba(0,0,0,0.25)`.
- **Saturated 0.20+ chroma.** Claymorphism palette tops out at 0.04–0.08 — anything brighter reads candy, not clay.
- **Missing the dark bottom-right inset shadow.** Without it, clay reads as a flat pastel pill with a glow.
- **Clay extended to dark mode.** The inset highlight stops reading on dark; clay collapses to neumorphism.
- **Equal outer + inner offsets but blur < 2× offset.** Breaks the doughy read.

### 8.3 Neumorphism anti-patterns

- **Pure `#FFF` or `#000` background.** Both shadows must stay visible — neutral putty grey only.
- **Symmetric shadows with no implied light source.** Commit ONE light direction (canonical: top-left).
- **Per-component shadow tuning.** The light source must agree across the entire page.
- **Sharp <12px radii.** Breaks the soft-plastic read.
- **Text or icons extruded.** Only containers extrude.

### 8.4 Holographic / iridescent anti-patterns

- **Conic-gradient in sRGB.** Produces muddy brown bands at the cyan→magenta crossover. Use `conic-gradient(in oklch ...)`.
- **Autoplay `hue-rotate(360deg)` spin.** Epileptic + tells AI. Real iridescence travels 40–50° arc.
- **Iridescence on body type or form inputs.** Surface is the spectacle; type stays cool monochrome.
- **Light substrate.** Iridescence MUST sit on dark — white kills the specular.

### 8.5 Aurora / mesh-gradient anti-patterns

- **Full-saturation rainbow blobs with no transparent falloff.** Each stop must fade center-to-transparent.
- **No `blur(60-100px)`.** Without it, the mesh reads as a chaotic gradient stack.
- **Mesh repeated in every section.** Singular event, once per page.
- **No grain/noise overlay at 4-8%.** Banding becomes visible.
- **Second gradient on the CTA.** The CTA must be solid.

### 8.6 Film grain anti-patterns

- **Synthetic grain at fixed opacity.** Real grain varies with luminance — heavier in shadows.
- **Static (non-animating) grain.** Real film moves frame-by-frame. Animate the noise pattern.
- **Colour grain on B&W stocks.** Tri-X is grayscale; Portra is colour. Match stock.
- **Grain at the same scale across all stocks.** 16mm is coarser than 35mm; Tri-X is coarser than Portra.

### 8.7 Halftone anti-patterns

- **All-channel dots grid-aligned.** Real CMYK uses C @ 15°, M @ 75°, Y @ 0°, K @ 45° to suppress moiré.
- **Dot size uniform.** Real halftone dot size varies with luminance.
- **Halftone behind crisp digital type.** Mismatched eras.

### 8.8 Risograph anti-patterns

- **Perfect registration.** Real riso is famously off by 1–3px. The misregistration IS the look.
- **Smooth gradients.** Riso halftones; it doesn't blend.
- **Full-opacity inks.** Riso ink is semi-transparent — `opacity: 0.6` and `mix-blend-mode: multiply` per layer.
- **Pure white substrate.** Riso prints on warm-cream paper.

### 8.9 Wood grain anti-patterns

- **Regularly repeating tile.** Mask with noise to break the seam.
- **Isotropic noise.** Wood grain is DIRECTIONAL — use `baseFrequency="0.02 0.3"` (y ≫ x for vertical grain).
- **Perfect varnish gloss without visible grain.** Even polished wood shows grain.

### 8.10 Skeuomorphism anti-patterns

- **Stacked metaphors.** Leather header + felt body + wood-shelf footer = trashy by definition. ONE metaphor per surface.
- **Fake metaphor elements.** Brass screws in Notes corners; tape-reel hubs on a calculator. The metaphor must do functional work.
- **Marker Felt / Comic Sans + "paper" texture.** Cosplay register.
- **40% lightness step on a gradient button.** Big steps read plastic-toy; iOS-6 stays at 4–8%.

### 8.11 Pixel-bitmap anti-patterns

- **Antialiased SVG icons next to pixel sprites.** Mixed-era contamination.
- **`drop-shadow(... blur)` on sprites.** Blurring breaks the grid.
- **Press Start 2P at 14px.** Letters mush at any non-8/16/24/32 size.
- **Smooth 250ms fades.** Era was instant or stepped.

### 8.12 Paper anti-patterns

- **Pure `#FFF` background.** Real paper is always warm-tinted.
- **Tile pattern visibly repeating.** Mask with noise to hide the seam.
- **High-contrast specular highlight on uncoated.** Uncoated has NO specular.
- **`text-align: justify` + 16px body / 1.4 line-height.** Editorial paper wants 18–19px / 1.55.

### 8.13 Letterpress anti-patterns

- **Light source disagreeing with rest of page.** Same committed direction or nothing.
- **Emboss/deboss on a non-paper substrate.** Letterpress only deforms paper.
- **Pure black text inside the impression.** Real letterpress ink is muted, slightly transparent.

### 8.14 Leather anti-patterns

- **Uniform pebble pattern.** Real pebble varies in size and distribution.
- **No specular per pebble.** Luxury leather glints.
- **Cold colour.** Leather is warm-toned (yellow / red / brown bases).
- **Uniform wear.** Real wear lives at touch-points (handle, corners), not random.

### 8.15 VHS / CRT anti-patterns

- **Static RGB shift.** Real VHS shift varies with content and tape head position.
- **Scanlines without subpixel RGB.** Phosphor mask is the soul of CRT.
- **Scanlines over already-pixel content.** Patterns fight each other.
- **No CRT curvature.** Real CRT is convex.
- **VHS distortion on a hi-res 4K asset.** The original tape was 240 lines.

### 8.16 General

- **Multiple light sources on one page.** Commit ONE direction.
- **Material applied to "no material" prototype slugs.** Some genres (neubrutalism, flat-design, vector-vectordelia) WANT the lack of material. Refuse to dispatch.
- **All materials at full intensity.** Materials whisper. Heavier-than-needed material is the tell.
- **Material applied without checking the substrate.** Glass / aurora / iridescent / hybrid materials are USELESS on flat white — refuse, OR commit a substrate first.
- **Reactive behaviour without `prefers-reduced-motion` fallback.** Every reactive material needs a static fallback.
- **Reactive behaviour without `pointer: fine` gating.** Touch devices fake hover; pointer-driven highlights break.
- **Battery-draining reactive loops (60+ Hz on every event).** Throttle to `requestAnimationFrame`.

---

## Appendix: implementation snippets quick-reference

```css
/* Tilt-driven CSS custom props skeleton — used by holographic, liquid-glass, chrome */
.material[data-reactive] {
  --px: 0;  /* pointer X, -0.5..0.5 */
  --py: 0;
  --gx: 0;  /* gyro X, -1..1 */
  --gy: 0;
  transform:
    rotateX(calc((var(--py) + var(--gy) * 0.5) * 8deg))
    rotateY(calc((var(--px) + var(--gx) * 0.5) * 8deg));
  filter: hue-rotate(calc(var(--px) * 25deg));
  background-position:
    calc(50% + var(--px) * 30%)
    calc(50% + var(--py) * 30%);
}
```

```js
/* Universal reactive-input bootstrap — call once per material instance */
function bindReactive(el, opts = {}) {
  const { pointer = true, gyro = false, throttle = true } = opts;
  let raf = 0;
  const setProps = (px, py) => {
    el.style.setProperty('--px', px.toFixed(3));
    el.style.setProperty('--py', py.toFixed(3));
    raf = 0;
  };
  if (pointer) {
    el.addEventListener('pointermove', e => {
      if (throttle && raf) return;
      const r = el.getBoundingClientRect();
      const px = (e.clientX - r.left) / r.width - 0.5;
      const py = (e.clientY - r.top) / r.height - 0.5;
      raf = throttle ? requestAnimationFrame(() => setProps(px, py)) : (setProps(px, py), 0);
    });
  }
  if (gyro) {
    /* lazy — only on first tap, since iOS needs requestPermission() from a gesture */
    el.addEventListener('click', async () => {
      if (typeof DeviceOrientationEvent.requestPermission === 'function') {
        if (await DeviceOrientationEvent.requestPermission() !== 'granted') return;
      }
      window.addEventListener('deviceorientation', e => {
        el.style.setProperty('--gx', (Math.max(-30, Math.min(30, e.gamma)) / 30).toFixed(3));
        el.style.setProperty('--gy', (Math.max(-30, Math.min(30, e.beta)) / 30).toFixed(3));
      });
    }, { once: true });
  }
}
```

```svg
<!-- Reusable filters library — include once at end of <body> -->
<svg width="0" height="0" style="position:absolute">
  <defs>
    <filter id="paperGrain">
      <feTurbulence baseFrequency="0.9" numOctaves="2"/>
      <feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 0.06 0"/>
      <feComposite operator="in" in2="SourceGraphic"/>
    </filter>
    <filter id="watercolor">
      <feTurbulence type="turbulence" baseFrequency="0.01 0.05" numOctaves="2"/>
      <feDisplacementMap in="SourceGraphic" scale="8"/>
      <feGaussianBlur stdDeviation="0.4"/>
    </filter>
    <filter id="halftoneCyan">
      <feFlood flood-color="#00FFFF"/>
      <feComposite operator="in" in2="SourceGraphic"/>
      <feComponentTransfer><feFuncA type="table" tableValues="0 0 1 1"/></feComponentTransfer>
    </filter>
    <filter id="liquidRefract">
      <feTurbulence type="fractalNoise" baseFrequency="0.012 0.018" numOctaves="2"/>
      <feDisplacementMap in="SourceGraphic" scale="20"/>
      <feGaussianBlur stdDeviation="1"/>
    </filter>
    <filter id="inkBleed">
      <feMorphology operator="dilate" radius="0.4"/>
      <feGaussianBlur stdDeviation="0.6"/>
      <feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 12 -4"/>
    </filter>
    <filter id="vhsShift">
      <feOffset in="SourceGraphic" dx="2" dy="0" result="R"/>
      <feOffset in="SourceGraphic" dx="-2" dy="0" result="B"/>
      <feColorMatrix in="R" values="1 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0" result="Rred"/>
      <feColorMatrix in="B" values="0 0 0 0 0  0 0 0 0 0  0 0 1 0 0  0 0 0 1 0" result="Bblue"/>
      <feBlend in="Rred" in2="Bblue" mode="screen"/>
    </filter>
  </defs>
</svg>
```

---

End of dossier. Total entries: **48** (digital: 19, analog: 23, hybrid: 6). Decision tree covers **80+ prototype slugs**. Reactive modalities: **6** (pointermove, DeviceOrientationEvent, scroll, pointerdown, prefers-reduced-motion, prefers-reduced-transparency/contrast).

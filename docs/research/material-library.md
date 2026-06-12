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
- **Structured refraction (reeded/fluted glass, smoked glass solids):** the refractor has GEOMETRY that decides what survives — vertical ribs slice the subject behind into displaced strips (reeded-fluted-glass), a dark solid smears typography through its body (smoked-obsidian-glass). Hero-register: WebGL transmission through real surface curvature (see `docs/research/prism-glass-reference/prism-hero.html`); DOM-register: per-rib `feDisplacementMap` sawtooth maps. Never refract live text — duplicate/rasterize first.
- **Light AS material (volumetric-light-shaft, edge-lit-acrylic):** the luminance gradient in air or inside a translucent volume IS the surface. Shafts need a near-black field and one committed origin corner; edge-lit slabs must out-glow at the edges and SPILL onto neighbors — glow without spill floats in a different scene.
- **Dichroic (some films, oil slicks):** colour depends on transmission angle. Layer two `conic-gradient` at different rotations with `mix-blend-mode: difference`.
- **Layered ink (risograph, screenprint, watercolour):** each ink layer is partially transparent; overlap creates new hues via `mix-blend-mode: multiply`.

### 1.5 Surface anisotropy

Brushed metal looks different at different viewing angles because the micro-grooves run in one direction. So does corduroy, vinyl record grooves, silk satin, sandblasted glass. The web move is a directional gradient (`linear-gradient` perpendicular to the grain direction) with a perpendicular noise pattern. On tilt, the highlight stretches ALONG the grain, never across it.

### 1.6 Age and wear

Materials acquire patina. Copper greens, paper yellows, leather creases at the same handle-points. The orchestrator may commit `wearProfile: ageless | shows-wear | acquired-patina` per material. Acquired-patina materials need ASYMMETRIC distress — wear that lives where a hand or hinge would touch, not random global noise.

### 1.7 Pointer-interaction reactions — proximity, hover, click

Every material the orchestrator commits MUST also commit a reaction (or a deliberate non-reaction) for each of the three pointer-interaction intents. These are distinct AXES, not redundant alternatives — a glass card reacts to all three differently, and the combined choreography is what makes the material feel alive instead of static.

> Intent ≠ modality. §6 organises pointer events by modality (pointermove / pointerdown / etc.) because the permission/perf profiles differ per API. This section organises the same events by INTENT — what the user is doing — because the FELT reaction is the contract the material is honouring. A material's entry should declare both: "responds to proximity → soft sheen drift" + "responds via pointermove handler at viewport scope".

**Proximity (pointer NEAR the element but not over it).** The pointer is inside a radius (typically 200–500px) of the element's bounding box, with the cursor still in dead-zone. Subtlest of the three; the highest-craft layer. Used by Vision OS, Apple visionOS-era marketing pages, Linear's CTA hover sheen, Stripe's gradient bloom. Implementation: a SINGLE viewport-level `pointermove` handler writes `--mx` / `--my` to `:root` once per frame; each material computes its own distance via `calc()` on its bounding-box centre vs the cursor.

- **What reacts to proximity:** glass (sheen drift), holographic (hue lean), chrome (environment-map nudge), aurora-mesh (blob centroid pulls toward cursor), iridescent (hue rotation falls off with distance), liquid-glass (refraction centre shifts), oil-on-water (dichroic phase shift).
- **What MUST NOT react to proximity:** matte materials (uncoated paper, concrete, suede, raw clay) — the illusion is that they DON'T reflect anything. A matte material that leans toward the cursor reads as broken.
- **Falloff curve:** linear is too even; inverse-square (1/d²) feels right, clamped at a max distance. Out beyond ~500px, the reaction is zero.
- **Battery:** highest cost of the three because it runs every frame as long as the cursor moves. Disable entirely under `prefers-reduced-motion` and on `(pointer: coarse)` (touch). Throttle to rAF.

**Hover (pointer OVER the element).** Binary on/off; usually achievable with CSS-only `:hover`. Distinct from proximity in that the reaction is bigger and the cursor's relative position INSIDE the element typically drives a parallax/tilt vector. The middle-cost layer.

- **Glass:** backdrop-blur intensity ticks up (e.g., 12px → 16px); inset 1px white top-edge highlight brightens; saturate boost rises 10–20%.
- **Clay / soft plastic:** inset shadow grows to suggest finger-impression depth — the "press is about to happen" cue.
- **Holographic / iridescent:** full conic-gradient rotation driven by `--px` / `--py` (the cursor's local position inside the element); hue travel of 40–50°.
- **Chrome / brushed metal:** specular highlight tracks the pointer; on anisotropic metals the highlight stretches ALONG the grain, never across.
- **Paper / cardstock:** corner curl reveal (top-right triangle gradient mask appears); subtle lift via `transform: translateY(-1px)`.
- **Wood / leather:** subtle warm-hue tick + faint specular brighten + 1.01–1.02× lift.
- **Liquid-glass:** refraction `feDisplacementMap` scale ticks up.
- **What MUST NOT react to hover:** concrete, raw uncoated paper, brutalist surfaces — committing hover-lift on these breaks the brief (the genre's whole point is that the surface is honest about its weight).

**Click / press (pointerdown → pointerup).** The deformation/feedback moment. Brief (100–250ms), snappy, then snap back. The cheapest layer; CSS `:active` handles most cases.

- **Clay / soft plastic:** `transform: scale(0.97)` + inset shadow growth — the press impression.
- **Glass / liquid-glass:** quick 1px white inset rim-flash; NO scale (glass doesn't squish).
- **Material M3:** ink ripple expanding from the click point — pure M3 signature.
- **Paper:** brief press impression (corner-pinch suggestion) + subtle `translateY(1px)`.
- **Brittle materials (ceramic glaze, frosted glass, marble):** micro-shake animation (3px lateral wobble over 80ms) — like the surface chimes when struck.
- **Liquid (oil-on-water, mercury, water-droplet):** `feDisplacementMap` ripple emanates from the click point; CSS-radial-mask travelling outward at ~600px/s.
- **Metal (brushed-aluminum, chrome, gold-leaf):** brief specular flare at the click point.
- **Holographic / iridescent:** glint flash at click point — a momentary hue-rotate burst.
- **Matte materials:** opacity dip (1.0 → 0.92) — no geometric deformation, just the acknowledgement.
- **Universal rule:** the click reaction MUST resolve back to rest within 250ms. Anything longer reads as a stuck state.

**Three-intent commit per material.** Every entry in §3–§5 SHOULD declare:

```yaml
reactiveBehaviors:
  proximity: "<reaction>, falloff 1/d² over 400px"   # or "none — matte"
  hover:     "<reaction>"                             # or "none — anti-pattern for this material"
  click:     "<reaction>, 150ms resolve"              # or "none — surface absorbs"
```

When the entry does not yet declare these, the orchestrator inherits the default for the surface finish:

| Surface finish | Default proximity | Default hover | Default click |
|---|---|---|---|
| matte | none | opacity +4% | opacity −8% (150ms) |
| semi-gloss | subtle highlight drift | highlight intensify | rim-flash (120ms) |
| glossy | sheen drift along surface | sheen brighten + lift 1px | scale(0.98) (120ms) |
| metallic | env-map nudge | specular tracks pointer | specular flare (100ms) |
| iridescent | hue lean 6–10° | full conic travel | glint burst (180ms) |
| translucent | substrate parallax | blur intensify + saturate | rim-flash (120ms) |
| textured | none (grain is static) | subtle hue tick | opacity dip (150ms) |

**Reduced-motion contract.** Every reactive material MUST honour `prefers-reduced-motion: reduce` by collapsing proximity → none, hover → colour/opacity shift only (no transform), click → opacity shift only (no transform, no ripple, no displacement). Static visual state must remain readable.

**Touch contract.** On `(pointer: coarse)` (touch devices), proximity is meaningless (fingers don't hover from afar) — disable entirely. Hover should be deferred to `:active`/`:focus-visible` only, or fired-and-released on tap. Click reactions are universal.

---

## 2. Material taxonomy

Each entry below uses YAML-in-markdown. The schema is consistent: `materialId`, `name`, `family` (digital / analog / hybrid), `category`, `physicalBehavior`, `implementationStrategies` (CSS / SVG / WebGL / raster / video), `reactiveBehaviors`, `pairsWith.prototypeStyles`, `killsTheIllusion`, `examples`, `references`.

The `reactiveBehaviors` block declares — at minimum — the three pointer-interaction intents from §1.7 (`proximity`, `hover`, `click`), plus the legacy axes (`light`, `highlight`, `depth`, `parallax`). When an entry omits one of the three intents, the orchestrator inherits the surface-finish default from §1.7's defaults table.

Forty-eight entries follow, organised into Digital (§3), Analog (§4), and Hybrid (§5).

---

## Entry catalogue — moved to per-file sources

**Each of the 78 entries in this library is its own source-of-truth file in `design-library/material-<entryId>.md`** — hand-editable, with YAML frontmatter + markdown sections. Editing one entry doesn't require scanning the rest of the library.

Where to find an entry:

- **Browse the System tab → Design library** in the editor. The Material bucket lists all entries as cards with image-sample slots.
- **List from the shell:** `ls design-library/material-*.md`
- **Read one programmatically:** the `.index.json` companion file (e.g. `docs/research/material-library.index.json`) maps every entry id to its source path, and orchestrators consume that index to route a slot to the right entry without scanning the big primer.

To add a new entry, create a new `design-library/material-<entryId>.md` with YAML frontmatter and markdown body (use any existing file as a template), then re-run `python3 scripts/build-library-indexes.py` to refresh the index. That script reads the prototype directory; the primer below is for principles only.

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

### 6.4 pointermove at viewport scope — proximity (universal)

The proximity reaction from §1.7 needs a SINGLE viewport-level handler, not one per material instance. A page with twelve glass cards must not bind twelve `pointermove` listeners — every material reads from one shared `--mx` / `--my` written to `:root`, and computes its own distance via CSS `calc()` on its bounding-box centre.

- **Support:** Universal (W3C Pointer Events).
- **Permission:** None.
- **Mobile-vs-desktop:** Desktop only — touch has no "near" state. Gate behind `@media (pointer: fine)` and `@media (hover: hover)`.
- **Battery cost:** One listener, throttled to rAF, ~1µs work per frame. Cheap. The expensive bit is the per-material `calc()` chain — keep proximity reactions on ≤20 elements per page.
- **Reduced-motion fallback:** Detach the listener entirely; pin `--mx` / `--my` to neutral (50vw / 50vh).
- **Pattern:**
  ```js
  // ONCE per page — not per material
  if (matchMedia('(pointer: fine)').matches && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
    let pending = false;
    addEventListener('pointermove', e => {
      if (pending) return;
      pending = true;
      requestAnimationFrame(() => {
        document.documentElement.style.setProperty('--mx', e.clientX + 'px');
        document.documentElement.style.setProperty('--my', e.clientY + 'px');
        pending = false;
      });
    }, { passive: true });
  }
  ```
  ```css
  /* per-material: compute its own proximity falloff */
  .holo {
    --cx: 50%; /* element centre, can be set via JS once on layout */
    --cy: 50%;
    --d:  max(0px, 400px - hypot(var(--mx) - var(--cx), var(--my) - var(--cy)));
    --lean: calc(var(--d) / 400px);  /* 0..1, peaks when pointer at centre */
    filter: hue-rotate(calc(var(--lean) * 12deg));
  }
  ```
  *(CSS `hypot()` ships in Chromium 125+ and Safari 17.2+; provide a JS fallback for older.)*
- **Used by:** glass (sheen drift), holographic (hue lean), chrome (env-map nudge), aurora-mesh (blob centroid drift), liquid-glass (refraction centre shift). Per §1.7's contract.

### 6.5 pointerdown / press (universal)

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

### 6.6 prefers-reduced-motion (universal baseline)

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

### 6.7 prefers-reduced-transparency / prefers-contrast (Apple HIG)

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
| `style-glassmorphism` | frosted-glass, thin-glass-chip | aurora-mesh (substrate), reeded-fluted-glass (hero panel) |
| `style-liquid-glass` | liquid-glass, reeded-fluted-glass | aurora-mesh, oil-on-water (substrate) |
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
| `style-oversized-neo-grotesque` | (no material on type) | film-grain-tri-x (optional), smoked-obsidian-glass (hero object OVER the type) |
| `style-silk-chrome-flow` | liquid-chrome-silk, filament-strand-ribbon | (dark substrate mandatory) |
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
| `aesthetic-cyberpunk` | anodized-chainmail (full-bleed substrate), crt-phosphor, vhs-distortion, film-grain-cinestill-800t | chrome-mirror |
| `aesthetic-cassette-futurism` | brushed-aluminum, crt-phosphor, vhs-distortion | film-grain-tri-x, edge-lit-acrylic (glowing hardware) |
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
| `aesthetic-depin-hardware` | brushed-aluminum, edge-lit-acrylic, concrete | crt-phosphor |
| `aesthetic-crypto-degen` | chrome-mirror, holographic-foil | crt-phosphor |
| `aesthetic-rgb-gamer` | crt-phosphor, holographic-foil | (single) |
| `aesthetic-cluttercore` | (every analog material in the library) | (intentional pile) |
| `aesthetic-maximalism` | (every material — considered abundance) | (curated pile) |
| `aesthetic-urbling` | chrome-mirror, gold-leaf, chrome-on-velvet, chrome-extruded-type (masthead) | holographic-foil |
| `aesthetic-luxury-cinematic-dark` | volumetric-light-shaft, chrome-extruded-type (one headline), smoked-obsidian-glass | film-grain-tri-x |
| `aesthetic-sculptural-minimal` | volumetric-light-shaft (dark variant) | (white variant: no material — the plinth is the brief) |
| `aesthetic-monochrome-pop-poster` | smoked-obsidian-glass (object over type), reeded-fluted-glass | film grain at 3–5% |
| `aesthetic-wacky-pomo` | glossy-plastic-aqua, halftone-cmyk | (Nickelodeon plastics) |
| `aesthetic-pixel-*` | pixel-bitmap, crt-phosphor, dithered-1bit | (genre-locked) |
| `aesthetic-pc-98` | pixel-bitmap, crt-phosphor | (single) |
| `aesthetic-vector-*` | (no material — vector is the brief) | (anti-pattern) |
| `aesthetic-op-art` | (no material) | (anti-pattern) |
| `aesthetic-8-bit-generic` | pixel-bitmap | (single) |
| `recipe-editorial-magazine` | uncoated-paper, coated-glossy-paper, halftone-cmyk, film-grain-portra-400 | letterpress-emboss, foxing-stain |
| `recipe-newspaper-of-record` | uncoated-paper, halftone-cmyk | (newsprint substrate) |
| `recipe-aurora-marketing` | aurora-mesh | (single) |
| `recipe-restrained-ai-marketing` | (no material — restraint) | (subtle paper grain at most; reeded-fluted-glass or filament-strand-ribbon allowed as the ONE hero gesture) |
| `recipe-scientific-infra-marketing` | (no material) | (subtle aurora-mesh) |
| `recipe-bento-marketing` | (no material baseline) | aurora-mesh in hero |
| `recipe-ai-foundry-dark` | aurora-mesh (dark), crt-phosphor (subtle) | anodized-chainmail / filament-strand-ribbon / edge-lit-acrylic / volumetric-light-shaft (ONE hero substrate, pick one) |
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

### 8.16 Pointer-interaction-reaction anti-patterns

- **Proximity reaction on a matte material.** Concrete, raw paper, suede leaning toward a cursor — the whole illusion of matte is that the surface scatters light diffusely and doesn't track anything. Refuse.
- **Hover-lift on `style-neubrutalism` / `aesthetic-neubrutalism` / `recipe-brutalist-web`.** The brief is HONESTY about weight; nothing lifts. Refuse.
- **Click reaction that doesn't resolve.** Anything held past 250ms reads as a stuck state. Snap back.
- **Scale on glass.** Glass doesn't squish. Use rim-flash or backdrop-blur tick instead.
- **Ripple on materials that aren't Material M3.** The ink ripple is an M3 signature; on a glass card it reads as borrowed-from-Android.
- **Proximity binding per-instance.** Twelve glass cards must NOT bind twelve viewport `pointermove` listeners. ONE handler at `:root`, every material reads `--mx` / `--my` and computes distance via CSS `calc()`.
- **Proximity reaction firing on touch.** Touch has no "near" state — fingers don't hover from afar. Gate with `@media (pointer: fine) and (hover: hover)`.
- **Hover transform driven by JS when CSS `:hover` would do.** Binary on/off doesn't need a JS handler; reserve JS for proximity (continuous distance) and for hover effects that need cursor-local position.
- **Two materials reacting at the same proximity radius with overlapping bounding boxes.** They appear to chase the cursor in lockstep. Stagger radii or commit ONE proximity material per region.
- **Click ripple on a held button.** If the action repeats while held (volume up), the ripple stacks and visually thrashes. One ripple per `pointerdown`, ignore re-fires until pointerup.
- **Hover reaction without click reaction.** Reads as half-finished; the user hovers, the surface lifts, the click does nothing felt. Commit both or commit neither.
- **Conflicting hover and proximity.** If proximity already brightens the highlight, the hover state must intensify FURTHER — not reset to baseline.

### 8.17 General

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

End of dossier. Total entries: **48** (digital: 19, analog: 23, hybrid: 6). Decision tree covers **80+ prototype slugs**. Reactive modalities: **7** (pointermove at element, pointermove at viewport / proximity, DeviceOrientationEvent, scroll, pointerdown, prefers-reduced-motion, prefers-reduced-transparency/contrast). Pointer-interaction intents: **3** (proximity, hover, click) — each material declares a reaction (or deliberate non-reaction) per intent in its `reactiveBehaviors` block.

---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: style-outline-wireframe-ui.png
    reason: Style surface UI mockup.
  - src: style-outline-wireframe-isolated.png
    reason: Signature surface, isolated.
---
# Outline / Wireframe (style)

**Tag:** `style`

**Canonical references:** Excalidraw, Balsamiq, Whimsical, Wired Elements, tldraw Draw

## Surface treatment

**Background.** Warm off-white paper — `#FBF8F3` / `#F8F6F0` (or Excalidraw's `#FFFFFF` with a faint dot-grid `radial-gradient(circle, oklch(85% 0.005 80) 1px, transparent 1px) 0 0 / 20px 20px`). Never pure flat `#FFF`. Dark variant: `#121212` paper, `#E8E6E1` ink — same warmth, inverted.

**Ink and greys.** Warm-charcoal ink `#36383C` (Balsamiq `#555555`, Excalidraw Open Colors gray-9 `#212529`). Never pure `#000`. Grey ladder: `oklch(70% 0.005 80)` / `oklch(55% 0.005 80)` / `oklch(40% 0.005 80)`.

**Accent.** Single chromatic accent on actionable items only — Excalidraw blue `#1971C2` OR Balsamiq red `#D32F2F` OR pencil-orange `oklch(65% 0.15 50)`. Semantic only where required: red `#E03131` destructive, green `#2F9E44` success, amber `#F08C00` warn. Two accents max per page.

**Type stack.** One hand-drawn primary doing all the work; optional mono for code. Primary picks in order: **Excalifont** (2024, canonical, WOFF2 OFL-1.1) → Virgil → Balsamiq Sans → Caveat / Kalam / Architect's Daughter / Patrick Hand. Mono: Comic Shanns or JetBrains Mono. Never Comic Sans. Never two hand-drawn faces in one page.

**Sizes.** Tight scale: `11 / 13 / 15 / 18 / 24 / 36`px. Body 15, labels 13, captions 11, section headings 18–24, hero 36. tldraw's s/m/l/xl ≈ 12/16/24/36.

**Line-height.** Body `1.45`, display `1.15`. Hand-drawn faces need more breathing room than Inter — never tighter than 1.4 on body.

**Radius.** `0` on every container. Boxes look rounded only because the stroke is wobbly. If CSS `border-radius` is unavoidable, cap at `2–4px` on buttons only. Pills and 8px+ rounding are forbidden — they read as "Figma component with handwritten font on top."

**Borders.** Hairline `1.5–2px solid <ink>` on every container — outlines are the entire visual language. To get the jitter in pure CSS: `border-style: solid` + `filter: url(#wobble)` SVG turbulence (`<feTurbulence baseFrequency="0.02" numOctaves="2"/><feDisplacementMap scale="2"/>`). For production, render with rough.js (`roughness: 1.0–1.5`, `bowing: 1`, `strokeWidth: 1.5`). Dashed variants `stroke-dasharray: 4 3` for placeholders/secondary state. No double borders, no inset borders, no border-image gradients.

**Shadow.** None, ever. A drop shadow on an outlined box is the single most-common AI tell here. If you must indicate depth, double-stroke an offset shadow (`box-shadow: 4px 4px 0 0 currentColor`) — but that's a Brutalist move; use sparingly.

**Decoration grammar.** Mandatory: at least one wobble somewhere (a margin note, an arrow, a circled element). Hand-drawn curved arrows with wobbly arrowheads connecting elements; scribble annotations (`← rename this?`); checkbox squiggle-fills; x-marks for unchecked; photo placeholders as a rectangle with a diagonal X (`<svg><rect/><line x1=0 y1=0 x2=100% y2=100%/><line x1=100% y1=0 x2=0 y2=100%/></svg>`); wavy underline for spell-check stand-ins. Forbidden: Lucide / Heroicons / Tabler / any pixel-perfect SVG icon set — they shatter the lo-fi contract. Hand-draw icons (squiggle camera, two-arc-and-a-dot user, three-line hamburger with uneven spacing) or write `[ 📷 ]` as text.

**Voice surface.** Placeholder-honest, present-tense, often UPPERCASE for labels (`USERNAME`, `SUBMIT`, `MENU`). Lorem ipsum or `[ logo ]` / `[ image ]` / `[ icon ]` for unresolved assets. Real product copy stays terse. Never marketing-flat.

## Motion budget

- Stroke-redraw on first paint: `stroke-dasharray + stroke-dashoffset` animated to `0` over `0.4–0.6s ease-out`, one-shot, never loops.
- Hover: stroke-width `1.5 → 2px` in `0.1s`; rough.js re-seed on hover for the "redraw" effect (Wired Elements pattern).
- Forbidden: cubic-bezier spring physics, scale transforms, blur transitions, fades longer than 0.2s, any easing that reads "Material 3."
- Respect `prefers-reduced-motion` — skip the stroke-redraw.

## Failure mode

Comic Sans on perfectly straight 1px `#000` borders + 8px rounded corners + a Lucide icon next to the wobbly button + soft `0 1px 4px rgba(0,0,0,0.08)` shadow + a saturated SaaS-blue filled "Sign up" pill = SaaS in a Halloween costume. Two dead giveaways: (a) every stroke is mathematically perfect — no roughness, no jitter, corners exactly on the pixel grid; (b) full-saturation chromatic palette on pure `#FFF` instead of warm-grey ink on cream paper. Filled buttons, gradients, shadows, and pixel-perfect icons each individually mean you've quit the genre.

## Best for

AI-canvas / make-real demos, dev-tool landing pages that want to feel "early," internal design docs, BRD / spec / RFC pages, AI agent "thinking" UIs (showing the model sketching before rendering), classroom and textbook diagrams, architecture-as-doc pages, pitch decks where the product is intentionally not-yet-built, low-fi prototype mode of design tools themselves.

## Pairs well with

- **Shells:** shell-infinite-canvas, shell-canvas-floating, shell-centered-column, shell-two-column-app, shell-hero-stack, shell-editorial-broken-grid
- **Aesthetics:** aesthetic-neubrutalism, aesthetic-anti-design, aesthetic-bauhaus, aesthetic-swiss-modernist, aesthetic-corporate-grunge

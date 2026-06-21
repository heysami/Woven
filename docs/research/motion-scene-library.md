# Motion-scene library - full-bleed video + motion-raster presentation techniques

The curated reference behind **motion-studio-orchestrator**. Each entry is one
*technique* for putting a full-screen generated video or motion-raster asset on
a page and choreographing UI with it - the register of Apple product pages
(scroll-entrance, scroll-scrub rotation), motionsites.ai heroes (quiet-zone
composition, mouse-tracked subjects), and moooi-style layered parallax.

This file is the **primer** - fundamentals + universal rules, read by humans
and by an agent once per session at most. It carries **no per-entry data**.
The per-technique source of truth lives at `design-library/motion-<techniqueId>.md`
(one file per technique, ~80-100 lines each); the dispatch-time discovery layer
is the auto-generated index at `docs/research/motion-scene-library.index.json`
(rebuild with `python3 scripts/build-library-indexes.py` after editing entries).

## 1. Fundamentals - how to think about this medium

### 1.1 The scene model

A motion-studio piece is a **linear sequence of full-screen scenes**. The
visitor steps forward and back between scenes - wheel notch, swipe, arrow keys,
dot rail - and never navigates freely. This is the structural difference from
the narrative-experience family: narrative gives a *place* with freedom of
attention; motion-studio gives a *presentation* with an authored order. Within
a scene, **hold beats** let the piece pause and do something - a video plays to
an authored hold frame and stops, UI elements animate in, the next input
releases - without ever navigating away. (`frame-hold-ui-sync` is the canonical
primitive.)

Scenes are deliberately FEW and deliberately SIMPLE: 2-6 per piece, one idea +
one asset + one technique each. Presentation-first means the complexity budget
goes to asset quality and choreography precision, never to features. If a brief
needs branching, state, or data, it is not a motion-studio slot.

### 1.2 Video-first, raster-fallback

Per scene, the asset policy ladder is:

1. **Generated video** - the default when a video provider is wired
   (check `GET /__capabilities` → `providerAvailability`).
2. **Motion raster** - generated stills set in motion. Two rungs:
   a **raster sequence** (40-120 generated frames scrubbed on a canvas,
   `scroll-sequence-frames`) when the scene needs scrubbed/keyframed motion,
   or a **single hi-res still + CSS motion** (`slow-push-zoom`, layered
   parallax, drift) when ambient life is enough. This is the standard
   fallback for every register - a generated photograph in motion never
   breaks the aesthetic.
3. **Hyperframes motion piece** - an HTML/GSAP composition (the `motion`
   drawer: animated type, vector shapes, diagrammatic motion). **LAST
   option, and GENRE-GATED**: it only enters the ladder when the committed
   aesthetic reads as vector-native - flat, typographic, editorial-loud,
   neubrutalist, diagrammatic, terminal, Memphis/Y2K-graphic. When the
   register is immersive or photorealistic (cinematic product film,
   photographic hero, atmospheric environment), vector animation breaks the
   spell - the ladder STOPS at motion-raster and a CSS-animated still is the
   floor. Research commits this eligibility per piece
   (`hyperframesEligible: yes|no` + rationale); the scene composer must not
   override it.

A motion-studio scene NEVER ships a dead static image - whichever rung the
ladder lands on, the always-in-motion rule (§1.6) still applies.

### 1.3 Resolution + encoding discipline

- Stills ≥1920×1080; generate at 2.5K+ when the asset will be scaled or pushed
  (`slow-push-zoom`) so motion never softens it. Edge-to-edge composition -
  no internal borders, no letterbox bars baked into the asset (the
  `letterbox-stage` technique paints its bars in CSS, not in the asset).
- Video 1920×1080 minimum, MP4 (H.264/H.265) + WebM. Scrubbed techniques need
  dense keyframes (`-g 12` or lower) - sparse keyframes make seeks visibly snap.
- Every video carries a `poster`; first paint is never a white rectangle.
- Background-matched assets (entrance videos over a page ground) name the exact
  hex in the generation prompt and get edge-pixel-diffed in QA.

### 1.4 Composition IS the layout contract

The single most load-bearing rule of the library: **the asset's generated
composition dictates where the UI goes.** Every storyboard scene commits a
`subjectAnchor` (left-third / right-third / center / center-bottom) and a
`quietZone` (the low-detail, type-safe region) - and BOTH go into the
generation prompt. Subject anchored right → UI lives left. A light sky
occupying the top half → the headline sits there (`quiet-zone-headline`,
the aethera-hero pattern). UI placement is decided by the storyboard *before*
generation and verified against the delivered asset *after* - when generation
drifts (the subject wandered under the headline), the fix is either a mirrored
layout (CSS) or a re-generation with a composition correction, never type
buried in detail.

Text-over-motion contrast is checked **across frames**, not just the poster:
sample the quiet zone at t=0 / mid / end (and at every hold frame) and enforce
≥4.5:1 against the type color. A zone that is quiet at t=0 and busy at t=3 is
a fail.

### 1.5 Interaction-aware generation

When a technique binds the asset to input, the **generation prompt must encode
the interaction**:

- Pointer-scrub techniques (`mouse-scrub-look`, `mouse-scrub-orbit`) need ONE
  continuous motion along ONE axis - a head turn or turntable arc from full-left
  at t=0 to full-right at t=end, fixed camera, no cuts, no lighting change -
  because the binding maps pointer-x linearly onto `currentTime`.
- Scroll-scrub techniques (`scroll-scrub-rotation`, `scroll-scrub-journey`)
  need a single continuous transform (rotation, dolly) so scroll progress reads
  as a position axis.
- Entrance techniques (`scroll-entrance-video`) treat the FINAL frame as the
  layout contract - the object decelerates to a stop exactly where the
  storyboard anchored it, and the hold frame doubles as the reduced-motion still.
- Hold-beat techniques bake distinct, stable poses at each authored hold
  timestamp.

A clip generated without the interaction clause cannot be rescued by the
binding code. Prompt and binding are one decision.

### 1.6 Always something in motion

Every scene keeps at least one living layer at rest: the ambient loop itself,
a specular sweep over a settled product, drifting atmosphere layers, a
breathing idle character. After an entrance settles, the motion duty passes to
a secondary layer - never back to the settled subject. The exceptions are
user-controlled stillness (`prefers-reduced-motion` swaps every video to its
poster and kills scrub/parallax) and off-screen scenes (all rAF work and
playback pause when a scene is not current).

### 1.7 Autoplay + input policy

All video is `muted` + `playsinline` - autoplay is otherwise blocked. The
family uses **no audio** and therefore needs **no permission gates**. Pointer
techniques get a mobile fallback (gyro tilt where permission-free, else a slow
autonomous pan) so no scene sits dead on touch devices. Wheel-step navigation
debounces ≥600ms per notch; pointer→response latency budget is ≤50ms with
eased pursuit (lerp ~0.08/frame) so tracking reads as gaze, not glitch.

### 1.8 Binding modes - self vs host-scroll

A piece is either **self-gestured** (`binding: "self"` - the iframe owns
wheel/swipe for scene stepping; the host page must keep a scroll-past
affordance per the standard iframe ↔ host contract) or **host-scroll-driven**
(`binding: "host-scroll"` - the iframe NEVER traps scroll; the host forwards
`postMessage({type:'ms-scroll', progress})` from its own scroll position and
the runtime maps progress onto scene index + within-scene scrub). Apple-style
sections inside a longer page are host-scroll; motionsites-style full-page
pieces are self.

### 1.9 Concept plates come first (the design gate)

Before any production asset is generated, every scene gets a **concept plate**:
ONE hi-res (1920×1080) generated still of the FULL composed frame - the asset
at its most-stared-at moment AND the UI drawn into it (real headline copy set
in the quiet zone, CTA, nav hint), the way a motion designer boards a site
before touching production. Plates cost one image dispatch each and are
surfaced to the user for approve / steer BEFORE video budget is spent. The
approved plate then becomes the **composition contract**: the video prompt is
derived to reproduce it (and the plate rides along as the image reference when
the provider supports i2v), the UI's type scale / placement / palette / scrim
are read off it (`uiBuildNotes`), and Step-8 QA diffs the shipped scene
against it. Plates are plans, not shipped assets - production text always
ships as real DOM, never as pixels baked into a raster.

## 2. Decision tree (prose context)

The structured decision tree lives in the index
(`docs/research/motion-scene-library.index.json → decisionTree`), built from
each entry's `pairsPrototypes`. How to read it against a storyboard:

- **The slot's role picks the candidate set**: hero openers → ambient-loop /
  quiet-zone-headline / mouse-scrub-look; product reveals → scroll-entrance /
  scroll-scrub-rotation / frame-hold-ui-sync; backgrounds under content →
  living-gradient / depth-drift / ambient-loop; galleries → hover-activate-loop;
  scene joins → the scene-choreography category.
- **The committed aesthetic filters the set**: restrained marketing registers
  (bento, restrained-AI, scientific-infra) take entrance/scrub/quiet-zone
  techniques and reject theatrical wipes; expressive registers (cyberpunk,
  Y2K-futurism, vaporwave) tolerate spotlight masks, speed ramps, match-cuts.
- **The interaction intent disambiguates**: "it notices you" → pointer
  techniques; "it unfolds as I scroll" → scroll-scrub; "it just feels alive" →
  ambient; "it pauses to explain" → frame-hold-ui-sync.
- One **composition** technique (quiet-zone-headline or
  subject-offset-ui-counterweight) applies to EVERY scene regardless of the
  motion technique picked - composition is a layer, not an alternative.
- **Code-rendered techniques (no generated asset)**: seven entries are
  implemented in code rather than commissioned as video/raster -
  `stylize-shader-pass` (live dither/halftone/ASCII over media; the efecto
  register - see `docs/research/efecto-effect-engine-study.md`),
  `lens-magnifier-reveal` + `focus-pull-type` (camera-optics play on DOM
  type), `drag-physics-cluster` (grabbable 3D object swarm; WebGL),
  `svg-self-draw` (hand-made SVG marks drawing themselves in on scroll -
  stroke-dashoffset entrance grammar), `cursor-character`
  (velocity-deforming, identity-swapping pointer; desktop-only), and
  `threshold-ritual` (entry gate as designed moment - sound-consent gate /
  counter ceremony / skippable title film; the title-film variant MAY
  commission a short vector or video opening).
  These route to the shader / polish / hero-3d build paths, NOT to the
  asset-generation pipeline; the §3 negative-keyword list does not apply.
  stylize-shader-pass COMPOSES with media techniques: any video this
  library generates can be run through the pass for print-process registers.
  (The three JP-survey entries - svg-self-draw, cursor-character,
  threshold-ritual - were extracted in `docs/research/japanese-web-survey.md`.)

## 3. Universal negative-keyword list

Append to every generation prompt in this library, stills and video alike:

> no text, no watermark, no logo, no captions, no letterboxing, no black bars,
> no UI elements, no scene cut, no camera shake, no zoom (unless the technique
> IS a zoom), no flicker, no frame jitter, no background drift, no morphing
> artifacts, no duplicated limbs, no extra fingers

For scrubbed video add: `no cuts, single continuous motion, fixed camera,
constant lighting`. For background-matched entrances add the exact page hex:
`seamless background exactly #<hex>`.

## 4. Implementation / orchestrator-integration notes

- **Access pattern** (the standard three-tier read): motion-studio-orchestrator
  and ms-research-technique read the **index** once per session; the decision
  happens on index JSON only (`decisionTree[committedSlug]` → filter on
  `role` / `category` / `notForUseWhen`). The per-scene drawers
  (ms-storyboard-author picks, ms-scene-composer + ms-motion-author +
  ms-interactions-author implement) read each picked entry's `sourceFile`
  (`design-library/motion-<techniqueId>.md`, ~1-5KB) for the generation spec,
  the binding sketch, and the motion-signature numbers. This primer is never
  read in the dispatch hot path.
- **Entry sections are contracts**: `## Asset generation spec` + `## Example
  asset prompt template` feed ms-scene-composer's visual-orchestrator
  co-dispatches; `## Interaction binding` feeds ms-interactions-author;
  `## Motion signature` feeds ms-motion-author; `## UI composition rules` feed
  both the storyboard and Step-8 QA.
- **Adding a technique**: create `design-library/motion-<techniqueId>.md`
  (copy any existing entry; keep the frontmatter keys techniqueId / name /
  category / subCategory / role / binding / medium / pairsPrototypes /
  notForUseWhen and the section order), then re-run
  `python3 scripts/build-library-indexes.py`.
- **Categories**: `scroll-driven`, `pointer-driven`, `ambient`,
  `scene-choreography`, `composition`. Roles: `hero`, `product`, `portrait`,
  `background`, `section`, `gallery`, `transition`. Bindings: `none`,
  `pointer-x`, `pointer-xy`, `hover`, `scroll-trigger`, `scroll-progress`,
  `scroll-velocity`, `wheel-step`.

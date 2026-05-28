---
name: prototype
description: Build or update an HTML/CSS/JS prototype in this repo — commits a genre and inherits everything from it. TRIGGER when the user wants to update the design, rebuild the prototype, regenerate components, add a page or overlay, refresh tokens, or change visual direction. Source is htm + React UMD (no Babel, no build); files are index.html, data.js, styles.css, *.js at the repo root. After applying changes, regenerate editor/data.js + DESIGN.md per AGENTS.md.
---

# Prototype drawing

You **draw** prototypes, you don't architect them. You can't see your own output, so optical correctness must come from structure committed upstream, not tuning at the end.

The craft: **decide a genre, commit its vocabulary in `styles.css :root`, let every downstream decision follow mechanically.**

Five layers, inherited from genre, never invented:
1. Page composition — shell, proportions, placement
2. Component vocabulary — colors, type, spacing, radii, shadows
3. Shape language — strokes, corners, endcaps, fill style
4. Content & voice — what strings say and how they sound
5. Graphics — icons, charts, decoration, imagery

---

## Step -1. Read the input before deciding what mode you're in

**Do NOT ask discovery questions when the user's prompt already contains the answers.** The "Decide the genre" section below is for the MINIMAL-PROMPT case — when the user has handed you a one-liner like "build me a dashboard" or "make a marketing page". When the user has already supplied a real brief, you SKIP discovery entirely and go build.

A prompt qualifies as "non-minimal — skip discovery" if it carries any of these:

- An explicit genre or reference product ("Linear-style", "Bloomberg-ish", "looks like Are.na", "Toca Boca warmth meets Headspace calm")
- A palette specified by hex or token values (e.g. `#FFE9C9`, `oklch(...)`, named colour tokens)
- A typography stack named ("Inter + JetBrains Mono", "Source Serif 4", "Cormorant + IBM Plex")
- A list of specific screens / surfaces / pages (≥2 named views)
- Named characters, personas, brands, or world details ("a creature named Wisp", "the kid's island", "a parent surface and a kid surface")
- A pre-existing brand spec, design tokens, or DS reference
- A reference URL, image, or competitor product to match
- More than ~300 characters of substantive description

If ANY of those apply, commit the genre from the input and proceed straight to Step 1. Do NOT enumerate the six axes back at the user as questions. Do NOT print the discovery form. Do NOT ask "what subject? what audience? what activity?" — those are already answered.

You may ask the user ONE clarification only if the brief is internally contradictory or missing a load-bearing decision (e.g. shell type is ambiguous between two equally good options). Otherwise: build.

If the prompt IS minimal (no genre, no palette, no specific screens, no characters, just "make me X") — then yes, run discovery per Section 0 below.

---

## 0. Decide the genre  (only if the input is minimal — see Step -1)

Single most common cause of "subtly off" AI output. Pick **exactly one** tradition.

**Six axes** (pick where the most align):
1. **Subject** — trading→Bloomberg, productivity→Linear, magazine→editorial.
2. **Audience** — engineers tolerate density; designers expect restraint; consumers expect warmth; finance expects mono + status pills.
3. **Activity** — read (editorial) · scan (dashboard) · decide (focused) · compare (table) · configure (panel-heavy) · browse (masonry). Often beats subject when they conflict.
4. **Density** — high (control-room), medium (product UI), low (editorial).
5. **Temperature** — institutional · warm · bold · edgy.
6. **Tradition fit** — what shipped product would this resemble?

**Shortcut:** "If this product really shipped, by people who knew what they were doing, what would it most resemble?" The answer is almost always a specific product (Linear, Bloomberg, Read.cv, NYT magazine, Apple product page, Material 3, IDE inspector). That product's tradition is your genre.

**Refuse the median.** Default median light-mode SaaS (white bg, blue accent, soft shadows on rounded cards, Inter 14, Lucide icons) is the AI tell — not ugly, just uncommitted. With no signal: ask once, propose one, or pick the closest shipped product.

**Heuristics**
- **80/20 test.** What's 80% of the screen? Data→dashboard. Type→editorial. Imagery→marketing. Whitespace→portfolio. Controls→product UI.
- **Activity beats subject.** A productivity tool that's mostly for reading is closer to editorial than to Linear.
- **One dominant tradition.** Hybrids need optical judgment you can't perform blind; let conflicting axes contribute a single element, never fight throughout.

---

## 1. Commit the genre

Top of `app.js`:
```js
// GENRE: Linear-style observability — OKLCH greys, hairline borders, mono for IDs/timestamps,
// dense rows, single accent in slate-blue. Reference: Datadog meets Linear's project view.
```
This single line cascades into shell, tokens, voice, motion, decoration. Drift becomes obvious — reaching for a soft purple gradient is wrong because Linear-style doesn't have those.

---

## 2. Page shell

Pick one. Internal balance follows mechanically.

| Shell | For | Skeleton |
|---|---|---|
| Three-column app | Dense product UI, observability | nav · canvas · inspector |
| Two-column app | CRUD, docs, dashboards | nav · canvas |
| Top-bar + canvas + footer | Single-canvas tools | header · main · footer |
| Centered narrow column | Editorial, long-form | `max-width: 65–72ch; margin: 0 auto` |
| Hero + feature stack | Marketing landing | hero · features · CTA |
| Bento grid | Showcase, feature matrix | 12-col asymmetric spans |
| Masonry / gallery | Portfolios, image-led | CSS columns / grid auto-flow dense |
| Full-bleed + floating panels | Maps, design tools | canvas + glass overlays |
| Mobile: top + scroll + tab-bar | iOS/Android-style | header · list · bottom tabs |
| Editorial broken grid | Magazine features | grid-template-areas with overlap |

- **Density gradient.** Periphery dense and small, center breathable. Identity TL, global state TR, primary action BR or sticky.
- **Balance by mass.** Heavy left ↔ taller-but-lighter right, or whitespace counterweight. Whitespace has mass.
- **Recall proportions; don't invent.** `1:2:1`, `25-50-25`, `260px 1fr 320px`, `65–72ch`, two-col docs `260+720+240`.
- **Repetition → rhythm; one disruption → focus.** 2–3 hierarchy levels (panel → row → cell).
- **Reading flow matches genre.** F-pattern (dashboards), Z-pattern (marketing), centered stack (editorial), masonry-jump (galleries).

---

## 3. The stack

One HTML file, opens by double-clicking. **No build step, no Babel, ever.**

Use **htm** — JSX-like tagged templates bound to `React.createElement`. No transpile, no `<script type="text/babel">`. Identical when served over HTTP.

```
prototype.json   Declarative manifest of frames / arrows / lanes / links / IA (see AGENTS.md)
index.html       CDN scripts (React UMD + htm), loads app.js
data.js          window.DEMO — all mock data here
styles.css       :root token block + every class
*.js             Components by region (or single app.js for small)
```

**`prototype.json` is what the editor reads** to build Canvas/Flow/IA/Entities views — it carries the things that can't be inferred from JSX (which `useState`s are frames, which frames belong to which lane, entity↔entity cardinality, etc.). Write it alongside the source whenever you author a prototype. Shape and round-trip rules live in `AGENTS.md → Source manifests`.

**Multi-HTML layout — `index.html` is the storyboard.** When the prototype spans multiple actors / personas / distinct workflows, split into per-page HTMLs and make `index.html` itself the Step 0b storyboard. The editor reads `index.html` as the landing page (`meta.sourceEntry`) AND as the workflow-level documentation that lanes / cross-actor arrows / page inventory are extracted from:

```
prototype.json     Manifest — same shape, but frames declare `entry: "<file>.html"`
index.html         Storyboard: personas, workflows, links to every workflow page
                   ↳ NOT a regular UI page; documents the system at the workflow level
                   ↳ See AGENTS.md → Workflow 1 Step 0b for what to include
data.js            window.DEMO — shared across all pages (loaded by each)
styles.css         shared token block + every class (loaded by each)
tc-application.html       Workflow page (e.g. TC submits an application)
pxp-applications.html     Workflow page (e.g. PXP reviews the queue)
pxp-cancellation.html     Workflow page (e.g. PXP determines a cancellation fee)
...
```

What the storyboard `index.html` must include for Step 0b to parse cleanly:
- **Personas list** — either a `personas: [...]` array exposed in script, or visible persona-tagged sections in the DOM. Names + roles, e.g. `{ id: "TC", label: "Training Coordinator" }`, `{ id: "PXP", label: "Programme Experience Partner" }`.
- **Workflow cards** — each card tags 1+ personas and links to 1+ pages. A card naming 2+ personas is the signal for a cross-lane handoff arrow. Quote the workflow number / title in the card so it can be lifted into the arrow's `action`.
- **Page inventory** — every workflow page reachable in the prototype, linked from a card. The editor uses this as the canonical frame list (more trustworthy than "every `.html` is a frame").
- **No regular UI chrome.** The storyboard is metadata, not a screen the user dwells on. Style it as documentation — no nav shell, no app affordances.

**The storyboard never appears as editor data.** The information it carries flows *into* `meta.lanes`, `arrows[].action`, and the frame inventory — but the storyboard page itself is **not** a Canvas frame, not a Prototype iframe, not a Flow node, not an IA node, not an entity. It's a spec, like `prototype.json` or `STORYBOARD.md`: it shapes what gets written into `editor/branches/<slug>.js` and then steps out of the picture. Write `index.html` purely for the agent and the human readers; never for the editor's five views.

This pattern is **a strong default for multi-HTML projects, not a hard rule.** If your project is single-HTML or single-actor, skip it — `index.html` is just the landing page (and the editor renders it normally). The storyboard pattern appears the moment you have two or more actors handing work off through the data layer (see AGENTS.md → "Test for cross-actor handoff"). When unsure, either draft the storyboard up front or expect Step 0b's fallback to surface the ambiguity for the human to resolve.

`index.html`:
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=1440"/>
  <title>{{Project}}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family={{Sans}}:wght@400;500;600;700&family={{Secondary}}&display=swap"/>
  <link rel="stylesheet" href="styles.css"/>
</head>
<body>
  <div id="root"></div>
  <script src="https://unpkg.com/react@18.3.1/umd/react.development.js"></script>
  <script src="https://unpkg.com/react-dom@18.3.1/umd/react-dom.development.js"></script>
  <script src="https://unpkg.com/htm@3.1.1/dist/htm.umd.js"></script>
  <script src="data.js"></script>
  <script src="app.js"></script>
</body>
</html>
```

`app.js` header:
```js
const { useState, useEffect, useRef, useMemo } = React;
const { createRoot } = ReactDOM;
const html = htm.bind(React.createElement);

function App() { return html`<div className="app">Hello ${name}</div>`; }

createRoot(document.getElementById("root")).render(html`<${App}/>`);
```

**htm vs JSX — only differences:**

| JSX | htm |
|---|---|
| `<Comp prop={x}>` | `<${Comp} prop=${x}>` |
| `</Comp>` | `<//>` |
| `{value}` | `${value}` |
| `{...spread}` | `...${spread}` |
| `style={{ color: "red" }}` | `style=${{ color: "red" }}` |
| `<>...</>` | `<${React.Fragment}>...<//>` |

Everything else (className, events, refs, keys, conditional `&&`, `.map`, SVG, hooks) is identical.

For pure HTML/CSS prototypes (static editorial, brutalist), skip React/htm entirely.

---

## 4. Token vocabulary

Token block at the top of `styles.css`. Categories are universal; values are genre-specific (see playbook).

```css
:root {
  /* Surfaces */
  --bg: ...; --surface: ...; --surface-2: ...; --border: ...;
  /* Text */
  --text: ...; --text-muted: ...; --text-faint: ...;
  /* Semantic + paired -soft */
  --accent: ...;  --accent-soft: ...;
  --success: ...; --success-soft: ...;
  --warning: ...; --warning-soft: ...;
  --danger: ...;  --danger-soft: ...;
  /* Type — sans + one secondary with assigned job */
  --font-sans: "...", system-ui, sans-serif;
  --font-secondary: ...;   /* mono for state, serif for editorial, display for marketing */
  /* Radii (3 steps) */
  --radius-sm: ...; --radius: ...; --radius-lg: ...;
  /* Shadows (3 steps) */
  --shadow-sm: ...; --shadow-md: ...; --shadow-lg: ...;
  /* Spacing — hand-tuned, NOT 4/8/16 multipliers */
  --pad: ...; --pad-sm: ...; --gap: ...;
  /* Shape language — pick ONE per axis */
  --stroke-thin: 1px; --stroke: 1.4px; --stroke-bold: 1.75px;
  --endcap: round;          /* round | butt | square */
  --icon-fill: outline;     /* outline | solid | duotone */
}
```

**Universal rules**
- **OKLCH for color.** RGB lies about lightness. Use `color-mix(in oklch, …)` for states; don't invent state-tokens.
- **Every semantic has a paired -soft.** Status indicators are pale-bg + dark-fg (or inverse), never raw saturated.
- **Theme via attribute:** `[data-theme="dark"] { ... }`.
- **≤5 type sizes**, hand-tuned per genre — not 4/8/16 multipliers.
- **≤2 fonts.** Second font has an assigned job (mono for state, serif for body).
- **Line-height does rhythm:** 1.3–1.4 titles, 1.45–1.6 body. Margins don't.
- **Shape language is one of the tokens** — stroke / endcap / corner / fill picked ONCE and applied everywhere.

**Chroma by genre**

| Genre family | Greys | Semantic |
|---|---|---|
| Restrained product UI (Linear, Vercel, Read.cv) | 0.004–0.01 | 0.11–0.16 |
| Editorial / book / paper-feel | 0.002–0.008 | 0.10–0.14 |
| Vibrant marketing / consumer | 0.01–0.02 | 0.16–0.22 |
| Brand-led B2B SaaS | 0.005–0.015 | 0.14–0.20 |
| Y2K / Memphis / loud editorial | 0.02–0.04 | 0.22–0.32 |
| Brutalist | 0 (pure greyscale) | rare, 0.30+ when used |

Never exceed 0.22 chroma unless the genre demands loudness.

---

## 5. Layout via primitives

~95% of layout from primitives where the math IS the visual answer.

```css
.row {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 10px;
  align-items: start;
}
.row-content { min-width: 0; }   /* critical — lets 1fr actually shrink */
```

- **`auto 1fr auto`** for any leading + content + trailing row.
- **`min-width: 0`** on the `1fr` cell — the most important invisible line in CSS prototype work.
- **Tabular content uses a fixed first column:** `130px 1fr` aligns labels at the same x.
- **`grid-template-areas`** for editorial / asymmetric layouts.
- **`gap` vs `padding`** — gap is between siblings (rhythm); padding is breathing inside (can be asymmetric to respond to content).
- **Numbers** in mono auto-align; for sans-font number columns, `font-variant-numeric: tabular-nums`.
- **Before `position: absolute`,** check whether grid spans / template-areas / flex+gap does it (~80% yes). Reserve absolute for genuine overlays.

---

## 6. Optical inheritance — recall, don't compute

| Situation | Recall |
|---|---|
| Icon next to multi-line text | `margin-top: 1–2px` on icon |
| Icon size next to text | 16px for 13–14px text; 14px for 11–12px |
| Inline SVG icon stroke | 1.4–1.6 for 12px viewBox; 1.5–1.75 for 16px |
| Letter-spacing on ≥20px headings | `-0.01em` to `-0.02em` |
| Letter-spacing on uppercase labels | `+0.04–0.06em` |
| Pill with leading dot — padding | `1–2px 6px 1–2px 4–5px` (left tighter) |
| Button padding | sm `5 10` · default `7 12` · primary `9 16` |
| Card padding | sm `12–14` · default `16–20` · feature `24–32` |
| Section vertical rhythm | sm `32–48` · default `64–80` · hero `96–160` |
| Body line-height | 1.45 UI · 1.55 docs · 1.6 long-form |
| Heading line-height | 1.1 display · 1.2 h1 · 1.3 h2/h3 |
| Card border | `1px solid var(--border)` — never thicker on primary surfaces |

---

## 7. Components — flat, no premature abstractions

- **Copy-paste JSX is fine.** Don't extract `<Card>` / `<Button>` / `<Badge>` until used 5+ times.
- **Inline SVG icons** in a `const Icon = { … }` map. ~12 covers most prototypes.
- **One CSS file.** Classes per component. No CSS-in-JS, no Tailwind in output.
- **State is local `useState`,** drilled freely. No Context, Redux, Zustand.
- **Tabs:** `useState('home')`. **Modals:** conditional JSX overlay. **Forms:** `useState` per field. **Routing:** none.

---

## 8. Content cascade

Subject → Genre → Shell → Components → **Slots** → Voice → Drafted content → Specifics.

**You don't draft copy and find a slot. You pick the slot — fixed by genre — and write into its budget.**

| Slot | Length | Form |
|---|---|---|
| Button label | 1–3 words | imperative. "Pause stage" not "Click here to pause this stage." |
| Panel title (uppercase) | 2–4 words | nominal. "Active Runs". |
| Row primary text | a phrase | declarative. "Microtest plan — objection simulation v3." |
| Row metadata (mono) | abbreviated | technical. "S2 / quiet-hours / b3". |
| Status pill | 1 word | uppercase tag. `KEEP` `WARN` `DISCARD`. |
| Description body | 1–2 sentences | full sentences with periods. |
| Editorial body | paragraphs | measured prose with rhythm. |
| Marketing hero | 5–9 words | benefit-led. "Ship when the data says ship." |

A 3-word button slot with 9 words is wrong. Respect the budget.

**Voice — set by genre, applied at every leaf.** One register end-to-end; chatty errors break a terse-technical UI; jokey pills break a poetic hero.

| Genre | Voice |
|---|---|
| Control-room / dashboard | Terse, technical, abbreviated, fragments, present tense |
| Editorial | Measured, narrative, varied sentence length |
| Marketing | Benefit-first, second person, short declaratives |
| Brutalist | Blunt, declarative, no qualifiers |
| iOS / friendly product | Warm, direct, contractions ("you're set") |
| Bloomberg / finance | Nominal phrases, abbreviations, numbers without commentary |
| Read.cv / portfolio | Restrained, precise, plainspoken |

**Specifics at every leaf**
- Named entities, not "Item 1". Real-sounding people, projects, IDs.
- Specific numbers, not round. `$2.10` and `184k`, not `$2.00` and `200k`.
- Voiced strings: "Tester confusion ↓ on tone preset switch (0.42 → 0.31)" beats "Confusion decreased."
- One coherent fictional world. 5–12 high-quality entries beat 50 generic.
- Language density matches layout density.

---

## 9. Graphics

| Category | Function | Decided when |
|---|---|---|
| Iconography | Functional | With components |
| Brand mark / logo | Identity constant | At step 0 |
| Data viz | Functional (data IS graphic) | Drives panel layout |
| Empty-state illustrations | Empty + carries tone | With empty-state component |
| Hero illustrations / shots | Decorative + narrative | With hero section |
| Background patterns / blobs | Decorative only | Last, only if genre demands |
| Editorial ornaments | Genre-mandatory decoration | With body component |
| Photography | Mixed | At the slot |

**Three rules**
1. **Default to no graphics.** Type + space is enough. Empty panels want bigger type, not illustrations.
2. **Functional graphics earn pixels by carrying data.** If a number/label conveys the same thing, it's decorative — cut it.
3. **Decorative graphics earn pixels only when genre demands.** Editorial wants drop caps. Bento wants per-cell treatments. Marketing wants hero imagery. Control-room forbids decoration entirely.

**Rarer = more weight.** One ornament in a sparse design is loud and intentional; five identical ones dilute each other.

**Anti-AI-tell rules**
1. Build functional graphics from primitives — inline SVG, CSS bars/tracks. Never import a chart library.
2. Replace illustrations with typography or geometric shapes when possible (big numbers, oversized type, single solid blocks). These inherit the system automatically.
3. Placeholder rectangles for missing imagery: `<div class="img-placeholder" data-aspect="4:3">PHOTO · café interior</div>`.
4. If you must have an illustration, name it specifically. "Hand-drawn pencil sketch of a café floor plan" not "hero illustration."
5. One decorative move per page, max.
6. Charts use believable data — real shapes with one anomaly, not random noise.

### Slot annotations — handing off to Subagent 1.V (the visual planner)

You don't decide the *medium* per visual slot (raster vs vector vs shader vs particles vs 3D vs lottie vs video). That decision is owned by [`docs/agents/subagents/1V-visual-planner.md`](docs/agents/subagents/1V-visual-planner.md), which runs after you finish source. Your job is to annotate each slot so the planner's classifier can pick correctly.

**For static-imagery slots** — use `img-placeholder`:

```html
<div class="img-placeholder" data-aspect="4:3"
     data-slot="hero-cafe-floorplan"
     data-asset-intent="foreground · hand-drawn pencil sketch of a café floor plan, top-down view, isolated subject">
  PHOTO · café interior
</div>
```

**For motion / animated-loop slots** — use `motion-placeholder` (the new sibling pattern):

```html
<div class="motion-placeholder" data-aspect="16:9"
     data-slot="bg-drift-particles"
     data-motion="particles · slow drift · 40 dots warm white">
  MOTION · ambient drift particles
</div>
```

The `data-motion` modifier drives the planner's motion classifier:

| `data-motion` prefix | Routes to |
|---|---|
| `particles · …` (density hint optional) | `particle-2d` (default) or `particle-gl` (if density > 200 or explicitly `gl`) |
| `loop · …` (figurative subject like a mascot / logo intro / scene transition) | `lottie` |
| `clip · …` (cinematic narrative) | `video` |
| `wash · …` / `aurora · …` / `noise · …` (gradient or shader pattern) | `shader` |
| `scene · …` (3D scene with depth) | `3d` |

**Functional motion stays inline.** Hover transitions, state changes, progress bars, "running" pulses — write them in `styles.css` with `@keyframes` per §10. Don't wrap them in a `motion-placeholder`; that's reserved for decorative loops that get a workflow node.

**Voice / specificity rule applies to `data-asset-intent` and `data-motion` strings.** "Hand-drawn pencil sketch of a café floor plan, top-down view, warm graphite on warm paper" beats "hero illustration". The planner forwards your annotation to the per-medium drawer; specificity in equals specificity out.

---

## 10. Motion budget

Motion only because *data is changing* or *genre demands it*. Never decoration.

Two columns — different ownership:

| | **Functional motion** | **Decorative loop** |
|---|---|---|
| Trigger | State change, data update, user input | Ambient — would still play if the page were paused |
| Examples | Hover, focus, progress, "running" pulse, page transition | Background particles, aurora wash, mascot loop, hero video, 3D ambient scene |
| Lives in | `styles.css` `@keyframes` + `animation:` / `transition:` inline | A `motion-placeholder` slot → workflow node owned by [Subagent 1.V](docs/agents/subagents/1V-visual-planner.md) |
| You write | The CSS yourself | A `data-motion` annotation; the per-medium drawer writes the code |

- Hover: `0.12s` on `background` / `border-color` / `opacity`.
- State changes: `0.15–0.2s`.
- Streaming / progress: `transition: width 0.4s ease`.
- Live signal: one ambient keyframe on a "running" indicator.

**The split test:** would this motion still play if every state were frozen? Yes → decorative loop, becomes a workflow node. No → functional, lives in `styles.css`.

**By genre:** marketing/portfolio → scroll-driven entrance OK · brutalist → zero motion · editorial → maybe one subtle parallax on hero · iOS/Material → spring-easing on state transitions · product UI/dashboards → motion only for changing data.

The genre guardrail propagates: Subagent 1.V's classifier reads the same table and refuses to scaffold decorative-loop nodes when the genre forbids them. A brutalist prototype that handed Subagent 1.V a `motion-placeholder` would get a `drop:genre-forbidden` decision; the static fallback is left to you.

---

## 11. Demo dock — prototype-only controls

Anything that lets a viewer switch view / persona / stage / time is **demo scaffolding**, not product UI. Inline placement reads as a real control even with a "Demo:" caption. **The rule:** every prototype-only switcher goes in a single floating **demo dock** in a fixed corner. Never inline.

**Triggers when** source has ≥2 view variants of the same screen reachable from one state hook (stage / persona / lifecycle / status switcher; time scrubber; feature flag).

**Test for what stays inline:** would a real shipped product have this control? Yes → inline (Overview / Documents tabs). No, only for demo variance → dock.

**Visual rules** — must not look like product UI:
- Dashed 1px border (don't reuse `.btn-primary` / `.card`).
- `🧪` badge + monospace label + "DEMO" chip in panel header.
- Container is `<div class="demo-dock" data-demo-only="true">` so iframe context AND `?demo=off` hide it via one rule.

**Closed:** compact badge `🧪 6 views ▾`. **Open:** screen preamble (1 paragraph: what varies) + one row per variant (label + 1-sentence "what changes") + current row marked. Row click dispatches a `demoview` CustomEvent the page listens for.

**Editor coupling.** Each row maps 1:1 to a `state` / `substep` frame; dock self-hides when iframed (`window.self !== window.top`) so it doesn't compete with the editor's nav.

### Boilerplate

```html
<div class="demo-dock" data-demo-only="true">
  <button type="button" class="demo-dock-toggle" aria-expanded="false">
    <span class="demo-dock-flask">🧪</span><span>3 views</span><span>▾</span>
  </button>
  <div class="demo-dock-panel" hidden>
    <header>
      <span class="demo-dock-chip">DEMO</span>
      <h4>Class lifecycle — 3 views</h4>
      <button type="button" class="demo-dock-x" aria-label="Close">×</button>
    </header>
    <p class="demo-dock-preamble">
      This screen is the TC's view of one in-house class. Capabilities change
      across the run lifecycle — pick a stage to see what the TC can / can't do.
    </p>
    <ul class="demo-dock-views">
      <li data-view="application">
        <strong>During application</strong>
        <span>No pax yet, cancel disabled.</span>
      </li>
      <li data-view="post-application" data-current="true">
        <strong>Post application</strong>
        <span>Runs confirmed, pax editable.</span>
      </li>
      <li data-view="pre-class">
        <strong>Pre-class (final week)</strong>
        <span>100% cancellation fee window.</span>
      </li>
    </ul>
  </div>
</div>

<style>
.demo-dock {
  position: fixed; bottom: 16px; left: 16px; z-index: 9999;
  font-family: var(--font-mono, ui-monospace, monospace);
  font-size: 11.5px; color: var(--text, #1a1a1a);
}
.demo-dock-toggle {
  appearance: none; cursor: pointer;
  display: inline-flex; align-items: center; gap: 6px;
  padding: 5px 10px;
  background: var(--surface, #fff);
  border: 1px dashed var(--text-muted, #888);
  border-radius: 0;  /* off-axis from product-UI radii */
  letter-spacing: 0.01em;
}
.demo-dock-toggle:hover { border-color: var(--text, #1a1a1a); }
.demo-dock-panel {
  display: block;
  max-width: 360px;
  background: var(--surface, #fff);
  border: 1px dashed var(--text-muted, #888);
  padding: 14px 16px 12px;
  margin-bottom: 6px;
}
.demo-dock-panel[hidden] { display: none; }
.demo-dock-panel header {
  display: flex; align-items: center; gap: 8px; margin-bottom: 8px;
}
.demo-dock-panel h4 {
  margin: 0; font: 600 12px var(--font-mono, monospace);
  flex: 1; letter-spacing: 0.02em;
}
.demo-dock-chip {
  background: var(--text, #1a1a1a); color: var(--bg, #fff);
  padding: 1px 6px; font-weight: 700; letter-spacing: 0.08em; font-size: 9.5px;
}
.demo-dock-x {
  appearance: none; background: none; border: 0; cursor: pointer;
  font-size: 16px; color: var(--text-faint, #888); line-height: 1;
}
.demo-dock-preamble {
  margin: 0 0 10px; line-height: 1.55; color: var(--text-muted, #555);
}
.demo-dock-views { list-style: none; margin: 0; padding: 0; }
.demo-dock-views li {
  padding: 8px 0; border-top: 1px dashed var(--border, #ddd);
  cursor: pointer;
}
.demo-dock-views li:first-child { border-top: 0; }
.demo-dock-views li strong { display: block; font-weight: 600; }
.demo-dock-views li span { display: block; color: var(--text-muted, #555); margin-top: 1px; }
.demo-dock-views li[data-current="true"] { color: var(--accent, #5566ee); }
.demo-dock-views li[data-current="true"] strong::after {
  content: " ← current"; font-weight: 400; font-size: 10px; color: var(--accent, #5566ee);
}
/* Iframed (editor) or ?demo=off → hide every dock instance */
[data-demo-only="true"].is-hidden { display: none !important; }
</style>

<script>
(function () {
  // Hide when iframed (editor PrototypeView has its own nav) or ?demo=off.
  var hide = window.self !== window.top
          || /[?&]demo=off\b/.test(window.location.search);
  if (hide) {
    document.querySelectorAll('[data-demo-only="true"]').forEach(function (el) {
      el.classList.add("is-hidden");
    });
    return;
  }
  // Toggle open/close on the badge button.
  document.querySelectorAll(".demo-dock").forEach(function (dock) {
    var btn = dock.querySelector(".demo-dock-toggle");
    var panel = dock.querySelector(".demo-dock-panel");
    var closeBtn = dock.querySelector(".demo-dock-x");
    if (!btn || !panel) return;
    var toggle = function (open) {
      var willOpen = open != null ? open : panel.hasAttribute("hidden");
      if (willOpen) { panel.removeAttribute("hidden"); btn.setAttribute("aria-expanded", "true"); }
      else          { panel.setAttribute("hidden", "");  btn.setAttribute("aria-expanded", "false"); }
    };
    btn.addEventListener("click", function () { toggle(); });
    if (closeBtn) closeBtn.addEventListener("click", function () { toggle(false); });
    // Wire the rows — each one expects a data-view value that maps to the
    // page's view-switching mechanism. The page is responsible for the
    // actual state change; the dock just dispatches a CustomEvent the page
    // can listen for. This keeps the dock decoupled from page state.
    dock.querySelectorAll(".demo-dock-views li").forEach(function (li) {
      li.addEventListener("click", function () {
        var view = li.getAttribute("data-view");
        dock.dispatchEvent(new CustomEvent("demoview", { detail: { view: view }, bubbles: true }));
        // Mark current
        dock.querySelectorAll(".demo-dock-views li").forEach(function (x) { x.removeAttribute("data-current"); });
        li.setAttribute("data-current", "true");
        toggle(false);
      });
    });
  });
})();
</script>
```

Page wires the `demoview` event to its useState: `document.addEventListener("demoview", e => setCurrentView(e.detail.view))`.

---

## 12. `gallery.html` — the design system's kitchen-sink page

The design system is a **first-class library asset**, not a sibling file under each prototype's source folder. It lives at `design-systems/<id>/` and is owned by Workflow 0 (build) and Workflow 6b (proposal-driven update) — see [`docs/agents/workflows/0-design-system.md`](docs/agents/workflows/0-design-system.md). Feature-page authoring (Subagent 1) **consumes** the DS — it never co-authors the gallery.

The gallery is the **source of truth for primitives**: every variant of every primitive rendered in idle state, no behaviour gating. The editor's DS library node renderer, `DESIGN.md` generation (Workflow 3), and audit (Subagent 6) all read it as the authoritative variant matrix.

**The rule.** Every design system ships `design-systems/<id>/gallery.html`. Workflow 0's DS-builder writes it from the DS spec; Workflow 6b updates it surgically when proposals are accepted. Subagent 1 never writes it; feature pages reference DS classes via `<link rel="stylesheet" href="../../design-systems/<id>/styles.css"/>`.

### What this page is

- A real, navigable design-system gallery. Same React UMD + htm + the DS's own `styles.css`. Primitives render with the **real product class names** (`.btn-primary`, `.btn-outline`, `.dropdown-pill`, `.application-card`, …) so the gallery doubles as a live preview of what feature pages use.
- **Every variant rendered in idle state** — modals open as standalone cards (no scrim, no `position: fixed`), drawers expanded inline, toasts shown, disabled buttons present, loading present, error inputs with their error chrome, every tab content panel, every wizard step, every empty state, every persona/stage variant.
- Organised as a TOC + main pane with sticky navigation, hero blurb, sectioned by category. Same structure agents and humans can both read.

### What this page is NOT

- Not a Storybook (no story format). Plain HTML sections.
- Not where you author behaviour. Static idle snapshots; no `useState` driving variants, no click handlers required.
- Not a frame in any branch's prototype. It's outside `source/<slug>/` entirely, so view subagents (Canvas, Prototype, Flow, IA, Entities) never see it.
- Not a sibling of feature pages. It belongs to the DS library node, not to any specific branch.

### Page shell

The gallery lives at `design-systems/<id>/gallery.html`, alongside the DS's own `styles.css`. It includes a small inline `window.DEMO` blob; it does NOT share `data.js` with feature pages (the gallery is self-contained).

```html
<!DOCTYPE html>
<html lang="en"><head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=1440"/>
  <title>Design system — <Project></title>
  <link rel="stylesheet" href="./styles.css"/>
  <style>/* gallery-chrome only — see below */</style>
</head>
<body data-mode="lxp"> <!-- optional brand/mode toggle target -->
  <div id="root"></div>
  <script src="https://unpkg.com/react@18.3.1/umd/react.development.js"></script>
  <script src="https://unpkg.com/react-dom@18.3.1/umd/react-dom.development.js"></script>
  <script src="https://unpkg.com/htm@3.1.1/dist/htm.umd.js"></script>
  <script>
    // GENRE: <one-line committed genre, verbatim from spec.genre>
    window.DEMO = { /* small inline mock — one row per state per primitive */ };
    /* one React component per category — see Sections */
  </script>
</body></html>
```

App layout (mounted into `#root`):

```jsx
<main class="ds-page">
  <aside class="ds-toc">                            <!-- sticky TOC links to each section -->
    <h6>Foundation</h6>
    <a href="#foundation">Color</a>
    <a href="#typography">Typography</a>
    <a href="#spacing">Spacing</a>
    ...
    <h6>Components</h6>
    <a href="#buttons">Buttons</a>
    ...
  </aside>
  <div class="ds-main">
    <div class="ds-hero">
      <h1>Design system — <Project></h1>
      <p>One-paragraph genre/voice summary.</p>
      <ModeToggle/>                                  <!-- optional, see "Mode toggle" -->
    </div>
    <Foundation/>                                    <!-- color / typography / spacing / radii / elevation / iconography -->
    <Components/>                                    <!-- buttons / pills / cards / forms / tables / ... -->
  </div>
</main>
```

### Section structure

Every section follows the same shape:

```jsx
<section class="ds-section" id="<slug>">
  <div class="ds-eyebrow">Foundation</div>          <!-- or Components / Patterns -->
  <h2>Section title</h2>
  <p class="ds-sub">One-paragraph what-this-is and how-to-use blurb.</p>

  <!-- One or more sample frames. Each .ds-sample wraps real product elements. -->
  <div class="ds-sample">
    <button class="btn-primary">Action</button>     <!-- real product class -->
    <button class="btn-outline">Cancel</button>
    <button class="btn-soft.neutral">Discard</button>
  </div>

  <div class="ds-caption">Optional caption explaining trade-offs.</div>
</section>
```

Anchors are stable kebab-case IDs (`#foundation`, `#typography`, `#buttons`, `#cards`, `#pills`, …). Workflow 0's runtime-mirror step (and Workflow 3's `components` YAML generation) walks these sections to enumerate primitives — the section IDs are the contract.

### Class-name discipline (this is the contract with Subagent 0 / 6 / Workflow 3)

Two namespaces, never mixed:

- **`.ds-*` — gallery chrome only.** Defined in the page's inline `<style>` block, NOT in `styles.css`. Examples: `.ds-page`, `.ds-toc`, `.ds-hero`, `.ds-section`, `.ds-eyebrow`, `.ds-sub`, `.ds-sample`, `.ds-sample-row`, `.ds-sample-stack`, `.ds-caption`, `.ds-mode-pill`, `.ds-code`. These never leak into feature pages.
- **Everything else — real product classes.** `.btn-primary`, `.btn-outline`, `.btn-soft`, `.btn-ghost`, `.btn-text`, `.dropdown-pill`, `.icon`, `.neutral`, `.application-card`, `.pill.open`, `.modal-card`, etc. These ARE styled in `design-systems/<id>/styles.css` and ARE referenced from feature pages (which `<link>` the DS stylesheet). The gallery renders them via `class="..."` so the same rules apply.

If you find yourself defining `.ds-btn-primary` in the gallery's inline style block, **stop** — that's the broken path. The gallery should render `<button class="btn-primary">…</button>` so audit (Subagent 6) sees the same class signatures that feature pages will use, and the editor's runtime mirror can resolve every primitive against the DS's `styles.css`.

### Foundation sections (in order)

1. **`#foundation`** — Color. One or more `<Ramp>` blocks per palette (primary, alt brand, semantic, neutrals). Each ramp is a `.ds-ramp` grid of `.ds-swatch` cards showing the hex + token name + foreground-contrast text.
2. **`#typography`** — Type scale. A `.ds-sample` containing one `.ds-type-row` per named level (display, h1, h2, h3, h4, h5, h6, body-md, body-sm, body-xs, caption, micro, plus any property-label / property-value). Each row shows name + size/weight/line-height meta + an actual sample using those styles.
3. **`#spacing`** — Spacing scale. One `.ds-scale-row` per named token (xxs, xs, s, base, m, l, xl, xxl, ...) with the px value and a `.ds-scale-bar` visualising width.
4. **`#radii`** — Radius scale. One `.ds-radius-tile` per radius (sharp, s, soft, m, l, pill) sized to demonstrate the curvature.
5. **`#elevation`** — Shadows. A `.ds-elev-grid` with one `.ds-elev-card` per shadow token. Each card has `box-shadow` set to the token value.
6. **`#iconography`** — Icon sources. One section each for `SvgIcon` (currentColor-tinted inline SVGs) and `AssetIcon` (mask-tinted asset SVGs). Show every available name in a `.ds-icon-grid`.

### Component sections (one per primitive)

Each primitive gets its own `<section class="ds-section" id="<slug>">`. Inside, render every variant in real product markup. Group via `.ds-sample` blocks with brief headers (`<h3>`) when the primitive has sub-groupings.

Examples for a button system with a matrix of styles × tones × shapes:

```jsx
<section class="ds-section" id="buttons">
  <div class="ds-eyebrow">Components</div>
  <h2>Buttons</h2>
  <p class="ds-sub">Composed via matrix: <code>.btn-{style}[.{tone}][.icon]</code>.</p>

  <h3>The matrix — five styles × two tones × two shapes</h3>
  <div class="ds-sample">
    <!-- grid layout showing every cell rendered with real classes -->
    <button class="btn-primary">Action</button>
    <button class="btn-outline">Action</button>
    <button class="btn-outline.neutral">Action</button>
    <button class="btn-soft">Action</button>
    <button class="btn-ghost">Action</button>
    <button class="btn-text">Action</button>
    <button class="btn-primary.icon"><SvgIcon name="more-h"/></button>
    <!-- ... all 20+ combinations ... -->
  </div>

  <h3>Common compositions in context</h3>
  <div class="ds-sample ds-sample-stack">
    <!-- Form footer pattern, toolbar pattern, etc. -->
  </div>
</section>
```

Every state-gated primitive renders ALL its states side-by-side:

- **Modal/Drawer/Popover/Sheet/Dialog/Toast** — render the card standalone (no scrim, no `position: fixed`). Optionally show two side-by-side: closed-trigger affordance + open-state card.
- **Form fields** — `.ds-sample-stack` showing idle / focused / filled / disabled / readonly / error / required.
- **Tabs** — show ALL tab contents in the gallery (not just the active one). Render each tab panel as its own example.
- **Wizard / multi-step** — every step rendered as a separate example.
- **Empty states / loading skeletons** — every variant rendered.
- **Persona/stage variants** — every persona × every stage rendered.

### Mode toggle (optional, gallery-only)

If the design system swaps primary ramps based on brand/mode (e.g. LXP=purple, PXP=orange), wire a `<ModeToggle>` at the top of `.ds-main` that flips `data-mode` on `<body>`. This is gallery-only — the **demo-dock convention from §11 does NOT apply** here. The gallery itself is a tool; the toggle is part of its UX so designers can preview both ramps. The runtime mirror (`editor/design-systems/<id>.js`) records tokens in the default mode.

### Selectors for the runtime mirror

Workflow 0 enumerates primitives by walking `<section class="ds-section" id="<slug>">` blocks. The runtime mirror records each variant with a selector anchored on the section ID + the real product class:

```js
{ entry: "gallery.html", selector: "#buttons .btn-primary:not(.icon)" }
{ entry: "gallery.html", selector: "#buttons .btn-outline.neutral.icon" }
{ entry: "gallery.html", selector: "#pills .pill.open" }
{ entry: "gallery.html", selector: "#cards .application-card[data-state=\"submitted\"]" }
{ entry: "gallery.html", selector: "#modals .modal-card.policy-modal" }
```

No `hash` (the gallery doesn't route by hash). Every variant is already in idle DOM. Selectors resolve on first paint — single-pass `querySelector`.

### Maintenance

Workflow 0's DS-builder (Subagent 0) writes the gallery from the DS spec. Workflow 6b updates it surgically when proposals are accepted. Subagent 6 (audit) reads it to build the DS vocabulary set; Workflow 3 reads it to generate `DESIGN.md`. **Subagent 1 never writes it** — feature pages reference DS classes by linking the DS stylesheet, not by mirroring the gallery.

---

## Forbidden

| Don't | Use |
|---|---|
| Build step / Babel / TypeScript / `<script type="text/babel">` | React UMD + htm in plain .js |
| React Router | `useState('tab')` |
| Redux / Zustand / Context for trivial state | Local `useState`, prop-drill |
| shadcn / MUI / Chakra / Tailwind | One `styles.css` with CSS vars |
| Lucide / Heroicons / Phosphor | Inline SVG icon map |
| Real `fetch` / API calls | `window.DEMO` static blob |
| Custom hooks for trivial state | Inline `useState` |
| `<Card>` / `<Button>` wrappers prematurely | Copy-paste; promote at 5+ uses |
| Generic mock data ("User 1") | Named, voiced, specific |
| 4/8/16/24 spacing scale rigidly | Hand-tuned per content shape |
| Drop shadows on every card | Hairlines + tiny `--shadow-sm` |
| Border-radius 12px+ on every box | `4 / 6 / 10` graded, or `0` brutalist |
| Emoji icons in interface | Inline SVG at cap-height |
| Generic stock illustrations | Typography, geometric shapes, named imagery |
| Charts with placeholder data | Real data shape with believable story |
| Decorative entrance animation | Motion only when data changes |
| Skeleton loaders / suspense | Static demo data |
| Inline `Demo:` / persona / stage / view switchers in page layout | Demo dock (see §11) |
| `console.log`, commented-out code | Remove before final |

---

## Genre playbook — pick exactly one

Each row is a complete vocabulary commit.

**Restrained product UI** (Linear, Vercel, Read.cv-adjacent)
Shell: 2- or 3-col app · Greys: 0.004–0.008 · Accent: `oklch(48% 0.13 252)` · Type: Inter / IBM Plex + JetBrains Mono · Sizes: 10–10.5 / 11.5 / 12 / 12.5 / 14 / 16 · Radius: 4 / 6 / 10 · Borders: hairline · Shadow-sm: `0 1px 0 oklch(0% 0 0 / 0.04)` · Motion: hover 0.12s, progress 0.4s, one ambient pulse · Mono: only for machine state · Voice: terse, technical · Decoration: forbidden.

**Bloomberg / IDE inspector / dense data**
Shell: full canvas + floating panels OR 3-col with status footer · Dark default · Greys: 0.008–0.012 · Accents: amber, cyan, green, magenta — chroma 0.13–0.16 · Type: heavy mono (JetBrains Mono Medium) + sans for prose · Sizes: 10 / 11 / 12 / 13 / 14 · Radius: 2 / 3 / 4 · Density: max, `--row: 22–24px` · Shadow: none internal · Voice: nominal phrases · Decoration: forbidden.

**Editorial — magazine / longform**
Shell: centered narrow, `max-width: 65–72ch` · Bg: warm paper white · Type: serif body (Source Serif, Iowan, Spectral) + grotesque headings · Sizes: 12 / 14 / 17–19 / 24 / 32 / 48 / 72 · Line-height: body 1.55–1.65; headings 1.1–1.2 · Margins: `1.5em` between paragraphs, `2.5–3em` before headings · Drop caps: `:first-letter { float: left; font-size: 4em; line-height: 0.85 }` · Voice: measured, narrative · Decoration: drop caps, dingbats, rules — required.

**Bento — Apple-style feature page**
Shell: 12-col asymmetric spans (`grid-column: span 8`) · Cells: radius 16–24px, padding 32–48px · Type: SF Pro Display-style, large, `-0.02em` letter-spacing on display · Sizes: 14 / 16 / 20 / 32 / 48 / 64 / 80 · Backgrounds: per-cell · Voice: benefit-first · Motion: scroll-driven OK · Decoration: per-cell visual treatment.

**Brutalist**
Shell: broken grid OR single column with intentional misalignment · Type: Times New Roman OR Helvetica only · Sizes: 14 / 24 / 96 / 200 · Color: pure black/white + one full-saturation accent · Border-radius: `0` · No shadows, no gradients, no transitions · Underlines on every link, no hover · Voice: blunt · Motion: zero · Decoration: only intentional ugliness (xerox, halftone, blocky type as graphic).

**Read.cv / Cargo personal site**
Shell: centered single column, generous L/R margin · Bg: `oklch(99% 0.002 80)` warm white · Type: one sans (Söhne, Inter, Geist) at 15–16px body · Sizes: 11 / 13 / 15 / 18 / 24 / 36 · Greys: 0.002–0.005 · Borders: hairlines at oklch 92% · Spacing: 80–120px between sections · Voice: restrained, plainspoken · Decoration: none.

**iOS native feel**
Shell: top bar (44pt) + scrollable list + bottom tab bar (49pt + safe-area) · Bg: `oklch(96% 0.002 240)` system grey or pure white · Lists: grouped sections with radius 10px, hairline separators inside · Type: SF Pro at 13 / 15 / 17 / 20+ · Voice: warm, direct, contractions · Motion: spring-easing on push, instant on taps.

**Material 3**
Shell: top app bar + canvas, FAB BR · Color: dynamic from a single seed, OKLCH-derivable · Surfaces: tinted via `color-mix(in oklch, var(--primary) 5–11%, var(--surface))` · Radius: 12–28px graded by elevation · Type: Roboto Flex or Inter · Motion: emphasized easing, ~0.3s for state changes.

---

## Pre-flight checklist

- [ ] Genre decided explicitly (six axes or closest-shipped-product), committed in top-of-file comment.
- [ ] Page shell matches genre; macro proportions are recalled, not invented; density gradient correct.
- [ ] Token block covers: surfaces · text · semantic+soft · type · radii · shadows · spacing · **shape language**.
- [ ] OKLCH for color; chroma calibrated to genre.
- [ ] ≤5 type sizes, ≤2 fonts, second font has assigned job.
- [ ] One stroke / endcap / icon-fill style across all graphics.
- [ ] All list rows share one grid-template-columns; `min-width: 0` on the flex cell.
- [ ] Numbers in columns use mono or `tabular-nums`.
- [ ] No icon library — inline SVG matching shape-language tokens.
- [ ] No build step; opens by double-clicking the HTML.
- [ ] No `fetch`, no API; all data is `window.DEMO`.
- [ ] Demo data: named entities, specific numbers, voiced microcopy.
- [ ] Voice consistent across every string; slot budgets respected.
- [ ] No generic stock illustrations / gradient blobs / isometric scenes.
- [ ] Functional graphics carry real data; decorative graphics serve genre; ≤1 decorative move per page.
- [ ] Motion matches genre.
- [ ] No drop shadows beyond `--shadow-sm` except on overlays.
- [ ] No `<Card>` / `<Button>` wrappers unless used 5+ times.
- [ ] Every prototype-only switcher (view / persona / stage / time) is in a demo dock (§11), not inline; dock self-hides when iframed and on `?demo=off`.
- [ ] `design-systems/<dsRef.id>/gallery.html` (§12) renders every primitive variant in idle state inside `.ds-sample` blocks with REAL product class names. Gallery chrome uses `.ds-*` prefix only; product classes never carry `.ds-*`. Selectors resolve on first load. (Feature-page authors don't write this file — Workflow 0 / 6b owns it. This checkbox is for the DS-builder and DS-update workflows.)
- [ ] Every visual slot is annotated for Subagent 1.V — `img-placeholder` for static imagery, `motion-placeholder` for decorative loops, each carrying `data-slot` + (`data-asset-intent` or `data-motion`). Functional motion stays inline in `styles.css`.
- [ ] No `console.log`, no commented-out code, no dead CSS.

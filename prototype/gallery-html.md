---
name: gallery-html
description: The full `design-systems/<id>/gallery.html` spec - page shell, section structure, class-name discipline, foundation + component section ordering, mode toggle, runtime-mirror selectors. Loaded only by Workflow 0 (DS-builder / Subagent 0) and Workflow 6b (DS-update). **Feature-page authors NEVER read or write this file** - they consume the DS by `<link>`-ing its `styles.css`, not by mirroring the gallery.

→ Decision lives in PROTOTYPE.md §"`gallery.html` - the DS kitchen-sink page".
---

# `gallery.html` - the design system's kitchen-sink page (Woven-specific)

The design system is a **first-class library asset**, not a sibling file under each prototype's source folder. It lives at `design-systems/<id>/` and is owned by Workflow 0 (build) and Workflow 6b (proposal-driven update) - see [`docs/agents/workflows/0-design-system.md`](docs/agents/workflows/0-design-system.md). Feature-page authoring (Subagent 1) **consumes** the DS - it never co-authors the gallery.

The gallery is the **source of truth for primitives**: every variant of every primitive rendered in idle state, no behaviour gating. The editor's DS library node renderer, `DESIGN.md` generation (Workflow 3), and audit (Subagent 6) all read it as the authoritative variant matrix.

**The rule.** Every design system ships `design-systems/<id>/gallery.html`. Workflow 0's DS-builder writes it from the DS spec; Workflow 6b updates it surgically when proposals are accepted. Subagent 1 never writes it; feature pages reference DS classes via `<link rel="stylesheet" href="../../design-systems/<id>/styles.css"/>`.

### What this page is

- A real, navigable design-system gallery. Same React UMD + htm + the DS's own `styles.css`. Primitives render with the **real product class names** (`.btn-primary`, `.btn-outline`, `.dropdown-pill`, `.application-card`, …) so the gallery doubles as a live preview of what feature pages use.
- **Every variant rendered in idle state** - modals open as standalone cards (no scrim, no `position: fixed`), drawers expanded inline, toasts shown, disabled buttons present, loading present, error inputs with their error chrome, every tab content panel, every wizard step, every empty state, every persona/stage variant.
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
  <title>Design system - <Project></title>
  <link rel="stylesheet" href="./styles.css"/>
  <style>/* gallery-chrome only - see below */</style>
</head>
<body data-mode="lxp"> <!-- optional brand/mode toggle target -->
  <div id="root"></div>
  <script src="https://unpkg.com/react@18.3.1/umd/react.development.js"></script>
  <script src="https://unpkg.com/react-dom@18.3.1/umd/react-dom.development.js"></script>
  <script src="https://unpkg.com/htm@3.1.1/dist/htm.umd.js"></script>
  <script>
    // GENRE: <one-line committed genre, verbatim from spec.genre>
    window.DEMO = { /* small inline mock - one row per state per primitive */ };
    /* one React component per category - see Sections */
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
      <h1>Design system - <Project></h1>
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

Anchors are stable kebab-case IDs (`#foundation`, `#typography`, `#buttons`, `#cards`, `#pills`, …). Workflow 0's runtime-mirror step (and Workflow 3's `components` YAML generation) walks these sections to enumerate primitives - the section IDs are the contract.

### Class-name discipline (this is the contract with Subagent 0 / 6 / Workflow 3)

Two namespaces, never mixed:

- **`.ds-*` - gallery chrome only.** Defined in the page's inline `<style>` block, NOT in `styles.css`. Examples: `.ds-page`, `.ds-toc`, `.ds-hero`, `.ds-section`, `.ds-eyebrow`, `.ds-sub`, `.ds-sample`, `.ds-sample-row`, `.ds-sample-stack`, `.ds-caption`, `.ds-mode-pill`, `.ds-code`. These never leak into feature pages.
- **Everything else - real product classes.** `.btn-primary`, `.btn-outline`, `.btn-soft`, `.btn-ghost`, `.btn-text`, `.dropdown-pill`, `.icon`, `.neutral`, `.application-card`, `.pill.open`, `.modal-card`, etc. These ARE styled in `design-systems/<id>/styles.css` and ARE referenced from feature pages (which `<link>` the DS stylesheet). The gallery renders them via `class="..."` so the same rules apply.

If you find yourself defining `.ds-btn-primary` in the gallery's inline style block, **stop** - that's the broken path. The gallery should render `<button class="btn-primary">…</button>` so audit (Subagent 6) sees the same class signatures that feature pages will use, and the editor's runtime mirror can resolve every primitive against the DS's `styles.css`.

### Foundation sections (in order)

1. **`#foundation`** - Color. One or more `<Ramp>` blocks per palette (primary, alt brand, semantic, neutrals). Each ramp is a `.ds-ramp` grid of `.ds-swatch` cards showing the hex + token name + foreground-contrast text.
2. **`#typography`** - Type scale. A `.ds-sample` containing one `.ds-type-row` per named level (display, h1, h2, h3, h4, h5, h6, body-md, body-sm, body-xs, caption, micro, plus any property-label / property-value). Each row shows name + size/weight/line-height meta + an actual sample using those styles.
3. **`#spacing`** - Spacing scale. One `.ds-scale-row` per named token (xxs, xs, s, base, m, l, xl, xxl, ...) with the px value and a `.ds-scale-bar` visualising width.
4. **`#radii`** - Radius scale. One `.ds-radius-tile` per radius (sharp, s, soft, m, l, pill) sized to demonstrate the curvature.
5. **`#elevation`** - Shadows. A `.ds-elev-grid` with one `.ds-elev-card` per shadow token. Each card has `box-shadow` set to the token value.
6. **`#iconography`** - Icon sources. One section each for `SvgIcon` (currentColor-tinted inline SVGs) and `AssetIcon` (mask-tinted asset SVGs). Show every available name in a `.ds-icon-grid`.

### Component sections (one per primitive)

Each primitive gets its own `<section class="ds-section" id="<slug>">`. Inside, render every variant in real product markup. Group via `.ds-sample` blocks with brief headers (`<h3>`) when the primitive has sub-groupings.

Examples for a button system with a matrix of styles × tones × shapes:

```jsx
<section class="ds-section" id="buttons">
  <div class="ds-eyebrow">Components</div>
  <h2>Buttons</h2>
  <p class="ds-sub">Composed via matrix: <code>.btn-{style}[.{tone}][.icon]</code>.</p>

  <h3>The matrix - five styles × two tones × two shapes</h3>
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

- **Modal/Drawer/Popover/Sheet/Dialog/Toast** - render the card standalone (no scrim, no `position: fixed`). Optionally show two side-by-side: closed-trigger affordance + open-state card.
- **Form fields** - `.ds-sample-stack` showing idle / focused / filled / disabled / readonly / error / required.
- **Tabs** - show ALL tab contents in the gallery (not just the active one). Render each tab panel as its own example.
- **Wizard / multi-step** - every step rendered as a separate example.
- **Empty states / loading skeletons** - every variant rendered.
- **Persona/stage variants** - every persona × every stage rendered.

### Mode toggle (optional, gallery-only)

If the design system swaps primary ramps based on brand/mode (e.g. LXP=purple, PXP=orange), wire a `<ModeToggle>` at the top of `.ds-main` that flips `data-mode` on `<body>`. This is gallery-only - the **demo-dock convention from §11 does NOT apply** here. The gallery itself is a tool; the toggle is part of its UX so designers can preview both ramps. The runtime mirror (`editor/design-systems/<id>.js`) records tokens in the default mode.

### Selectors for the runtime mirror

Workflow 0 enumerates primitives by walking `<section class="ds-section" id="<slug>">` blocks. The runtime mirror records each variant with a selector anchored on the section ID + the real product class:

```js
{ entry: "gallery.html", selector: "#buttons .btn-primary:not(.icon)" }
{ entry: "gallery.html", selector: "#buttons .btn-outline.neutral.icon" }
{ entry: "gallery.html", selector: "#pills .pill.open" }
{ entry: "gallery.html", selector: "#cards .application-card[data-state=\"submitted\"]" }
{ entry: "gallery.html", selector: "#modals .modal-card.policy-modal" }
```

No `hash` (the gallery doesn't route by hash). Every variant is already in idle DOM. Selectors resolve on first paint - single-pass `querySelector`.

### Maintenance

Workflow 0's DS-builder (Subagent 0) writes the gallery from the DS spec. Workflow 6b updates it surgically when proposals are accepted. Subagent 6 (audit) reads it to build the DS vocabulary set; Workflow 3 reads it to generate `DESIGN.md`. **Subagent 1 never writes it** - feature pages reference DS classes by linking the DS stylesheet, not by mirroring the gallery.


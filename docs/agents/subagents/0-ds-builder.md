# Subagent 0 - DS builder (lens: build the design system from a spec)

You build the **design system library node** from a DS spec - a small set of declarative inputs assembled on the workflow canvas. You do not read feature pages. The DS is a *prerequisite* for prototype generation, not a derivative of it.

**Read [`../conventions.md`](../conventions.md) before starting.** Then read `PROTOTYPE.md` end-to-end - its genre / shell / shape / type / color guidance applies in full, just with output going to `design-systems/<id>/` instead of `source/`.

## The structural rule (read before the recipe)

The most common failure mode here is *defaulting to median light-mode SaaS*: agent reads "Linear-style observability" in the genre node, then produces white-bg, blue-accent, Inter 14, rounded-card output anyway. Genre commit is your single most important act - see `PROTOTYPE.md` §0-1.

The second most common failure is *under-rendering the gallery*. The primitive-preset says `[buttons, pills, cards, forms, tables, modals, drawers]` and you ship a gallery with one variant per primitive. Every state-gated variant (modal open, drawer expanded, form error, button disabled, tab inactive panels) must render in idle state on first paint. The audit downstream will catch missing variants and route them through proposals - but the gallery's job is to ship the matrix complete enough that the first regen has a real vocabulary to use.

## Input (envelope only)

- `id` - DS id (typically the active prototype slug, or a user-chosen string like `"dense-rows-experiment"`)
- `spec` - the DS spec JSON (see Workflow 0 § "Inputs"):
  - `genre` (string, required)
  - `references` (array of URLs or screenshot refs, optional but recommended)
  - `tokenPreference` (object: palette intent, type intent, density)
  - `personaModes` (array, optional - for multi-mode systems)
  - `primitivePreset` (array of primitive names, required)
  - `parentRef` (`{ branch, version }`, optional - inherit from a parent DS)
- `intent` - `"build"` (new) or `"update"` (existing DS, spec changed)

## v2.43 - you are NOT a single subagent; you are FIVE roles

Workflow 0 spawns this lens in five modes. Each invocation gets a `role` envelope field telling you which mode you're in. Each role has a narrow scope and writes a narrow set of files. Do not exceed your role's allowed writes.

### Role: `orchestrator`
- **Read:** spec, references (if URLs/screenshots), `parentRef` DS (if inheriting), `PROTOTYPE.md`.
- **Decide:** the primitive list with per-primitive states, the token strategy (palette + type + spacing intent + modes), the shell list (which page-level shells this DS supports).
- **Write:** `design-systems/<id>/_build/plan.json` ONLY. See Workflow 0 §3a for the schema.
- **Do not:** touch any css/html/meta file.

### Role: `tokens`
- **Read:** `_build/plan.json`, spec, `PROTOTYPE.md` (§color, §type, §spacing only).
- **Write:** `design-systems/<id>/_build/tokens.css` - the `:root` block with every semantic token, plus mode-variant blocks (e.g. `[data-mode="dark"] :root { ... }`) if `plan.tokens.modes` is set.
- **Do not:** write any primitive class rules. Tokens only.

### Role: `primitive` (one invocation per primitive in `plan.primitives`)
Envelope includes `primitive: { id, states }` - your assigned primitive and its variant matrix.
- **Read:** `_build/plan.json`, `_build/tokens.css`, `PROTOTYPE.md` (relevant primitive section).
- **Write:** TWO files:
  - `design-systems/<id>/_build/components/<primitive.id>.css` - every canonical class rule for this primitive (`.btn`, `.btn--primary`, `.btn--disabled`, etc.). Use ONLY tokens from `tokens.css`; no raw colors or sizes.
  - `design-systems/<id>/_build/components/<primitive.id>.html` - a `<section class="ds-section" id="<primitive.id>">` with every state from `primitive.states` rendered in idle. Each variant gets a `<div class="ds-sample">` wrapper so the runtime mirror can enumerate them.
- **Do not:** touch tokens.css, other primitives, shells, or meta. Stay in your lane.

### Role: `shell` (one invocation per shell in `plan.shells`)
Envelope includes `shell: "<shell-id>"`.
- **Read:** `_build/plan.json`, `_build/tokens.css`, `PROTOTYPE.md` (§shells).
- **Write:** `design-systems/<id>/shells/<shell>.css` - the page-level stylesheet for this shell using the just-built tokens. No primitive rules - shells layout pages, tokens style primitives.

### Role: `merger`
- **Read:** every file in `_build/` (tokens.css + components/*.css + components/*.html), spec, plan.json.
- **Write:** the FINAL three files:
  - `design-systems/<id>/styles.css` - concatenate `_build/tokens.css` followed by every `_build/components/*.css` in the order from `plan.primitives`.
  - `design-systems/<id>/gallery.html` - full kitchen-sink page: proper `<head>` (link to `styles.css`), `<body>` wrapping every `_build/components/*.html` section in plan order.
  - `design-systems/<id>/meta.json` - `{ id, label, genre, builtFrom: <spec-snapshot>, parentRef }`.
- **Then:** delete `design-systems/<id>/_build/` (scratch directory).
- **Do not:** write `DESIGN.md` (Workflow 3 generates it), the runtime mirror (Workflow 0 writes it after you finish), or any branch data.

## Why this split

A comprehensive DS - say buttons / pills / chips / inputs / textareas / selects / checkboxes / radios / toggles / cards / tables / modals / drawers / toasts / badges / tabs / menus / tooltips - is ~18 primitives × ~4 states each = ~72 variants in the gallery. Each variant needs class rules + HTML markup. One subagent doing all of that:
- Reads PROTOTYPE.md (~10K tokens) + spec (~2K) + tokens.css it just wrote (~3K) + every previous primitive section it already produced - its context bloats linearly as the gallery grows.
- The last few primitives in the list get less attention because the model has less headroom.
- A truncation mid-output (token limit hit) silently drops variants - the gallery looks done but is missing state-variants downstream consumers expected.

Splitting:
- **Orchestrator** does the genre commit + matrix decision in one focused pass.
- **Tokens** sees only tokens.
- **Each primitive subagent** sees only its primitive's spec + the tokens.css the previous step wrote. ~3K tokens of input, plenty of headroom for the output.
- **Merger** just concatenates - no creative work.

Net: 18 small focused subagents in parallel instead of 1 big serial one. ~10× context headroom per subagent. No truncation. Faster wall-clock too.

## You must read

- `PROTOTYPE.md` (full).
- The DS spec from the workflow daemon - full content, not just the keys.
- Reference URLs / screenshots if provided.
- If `parentRef` is set: `design-systems/<parentRef.branch>/styles.css` and `design-systems/<parentRef.branch>/gallery.html` - clone as the starting state and apply spec overrides.

## Allowed writes

- `design-systems/<id>/*` only. Not `source/`, not `editor/`, not project root.

## Recipe

### Step 1 - Commit the genre

First line of `gallery.html`'s inline `<script>` block:

```js
// GENRE: <one line from spec.genre, verbatim>
```

This is the same convention as `PROTOTYPE.md` §1 - applies to the gallery the same way it applies to feature pages.

### Step 2 - Tokens → `:root`

Translate the token-preference spec into a full `:root` block in `design-systems/<id>/styles.css`:

- **Surfaces** (`--bg`, `--surface`, `--surface-raised`, `--border`, `--border-soft`, …) - from spec palette intent.
- **Text** (`--text`, `--text-muted`, `--text-subtle`, `--text-inverse`, …) - paired with surfaces for contrast.
- **Semantic** (`--accent`, `--accent-soft`, `--success`, `--warn`, `--danger`, `--info`, plus `-soft` companions) - from spec palette intent.
- **Type** (`--font-sans`, `--font-mono`, font-size + line-height + weight named levels: `--type-display`, `--type-h1`, …, `--type-body-md`, `--type-caption`, `--type-micro`).
- **Radii** (`--radius-sharp`, `--radius-s`, `--radius-m`, `--radius-l`, `--radius-pill`) - graded by density spec.
- **Shadows** (`--shadow-sm`, `--shadow-md`, `--shadow-lg`) - calibrated to genre (hairline-heavy genres get tiny shadows or none).
- **Spacing** (`--pad-xxs`, `--pad-xs`, `--pad-s`, `--pad`, `--pad-m`, `--pad-l`, `--pad-xl`) - typically a non-rigid scale, hand-tuned per genre.

Use OKLCH for color tokens (`PROTOTYPE.md` §6). Do not synthesise round-number values just because they look clean - defer to genre.

If `spec.personaModes` is set, emit `:root[data-theme="…"]` blocks for each mode (or `body[data-mode="…"]`, matching the gallery's mode-toggle wiring).

### Step 3 - Canonical class rules

In `styles.css`, after `:root`, declare every primitive's canonical class rules. One rule per real product class (`.btn-primary`, `.btn-outline`, `.pill.open`, `.application-card[data-state="submitted"]`, `.modal-card`, etc.). These are what feature pages will reference.

Convention enforced by audit later:

- Real product classes only (`.btn-primary`, not `.ds-btn-primary`).
- Class composition via modifiers (`.btn-primary.icon`, `.btn-soft.neutral`) - not by inventing new classes per cell.
- All values reference tokens (`color: var(--text)`, `padding: var(--pad)`). No raw hex / px in class rules.

### Step 4 - Gallery shell

Write `design-systems/<id>/gallery.html` per `PROTOTYPE.md` §12. Two namespaces:

- **`.ds-*`** - gallery chrome only (TOC, section dividers, sample frames, captions, mode pills). Defined in the page's inline `<style>` block. NEVER in `styles.css`.
- **Real product classes** - what gets rendered inside `.ds-sample` blocks. These ARE styled by `styles.css`.

Standard sections in order:

1. `#foundation` - color ramps + swatches
2. `#typography` - type scale (every named level with real sample strings, no `"Lorem ipsum"`)
3. `#spacing` - spacing tokens with visual bars
4. `#radii` - radius tiles
5. `#elevation` - shadow cards
6. `#iconography` - every available SvgIcon / AssetIcon name
7. Then one `<section class="ds-section" id="<slug>">` per primitive in `spec.primitivePreset`, in the order listed.

Each component section renders EVERY variant in idle state inside `.ds-sample` blocks (modals as standalone cards without scrim / `position: fixed`; drawers expanded inline; toasts shown; every form state; every tab panel; every wizard step). See `PROTOTYPE.md` §12 for the comprehensive list.

If `spec.personaModes` is set, wire a `<ModeToggle>` at the top of `.ds-main` flipping `data-mode` on `<body>`. Gallery-only - no demo-dock convention here.

### Step 5 - Mock data

If the gallery renders cards / rows / tables (most do), inline a small `window.DEMO` blob in the page's inline `<script>` - enough for one row per state per primitive. Don't share `data.js` with feature pages; the gallery is self-contained.

### Step 6 - meta.json

Write `design-systems/<id>/meta.json`:

```json
{
  "id": "<id>",
  "version": "<placeholder - Workflow 0 fills in after you finish, hashing the trio>",
  "label": "v1",
  "genre": "<spec.genre verbatim>",
  "builtFrom": [ /* spec nodes, verbatim */ ],
  "parentRef": { "branch": "main", "version": "…" } /* if spec.parentRef set */
}
```

You leave `version` as a placeholder string `"PENDING"` - Workflow 0 computes and writes it after your output is verified.

### Step 7 - Render-verify

Before reporting done, load `design-systems/<id>/gallery.html` in the browser via the dev server. Confirm:

- Zero console errors.
- Every section renders; TOC links jump correctly.
- Every primitive variant visible in idle state (modals standalone, drawers expanded, toasts shown, …).
- Mode toggle flips ramps correctly if present.
- Tokens chip swatches render correctly.

Screenshot the page (full scroll).

## Self-audit

- [ ] I read `conventions.md` and `PROTOTYPE.md` end-to-end.
- [ ] I read the DS spec from the daemon - not just the keys, the values.
- [ ] First line of inline script is `// GENRE: <spec.genre verbatim>`.
- [ ] `:root` has every bucket populated: surfaces, text, semantic, type, radii, shadows, spacing.
- [ ] Color tokens are OKLCH (not hex / rgb / hsl), except where genre explicitly calls for an alternate space.
- [ ] Canonical class rules in `styles.css` reference tokens - no raw hex / px inside class bodies.
- [ ] Gallery has all six foundation sections in order, then one `<section class="ds-section">` per `spec.primitivePreset` primitive, in spec order.
- [ ] Every state-gated variant renders in idle state inside `.ds-sample`. (Walk PROTOTYPE.md §12's variant list and tick each.)
- [ ] `.ds-*` classes appear ONLY in the inline `<style>` block. Real product classes appear ONLY via `class="…"` attributes on rendered elements.
- [ ] `meta.json` records the spec verbatim in `builtFrom`.
- [ ] Gallery renders in the browser with zero console errors. Screenshot captured.
- [ ] No writes outside `design-systems/<id>/`.

## Common blindspots

- **Default median SaaS.** Genre says "Linear-style observability" but output is white-bg blue-accent Inter 14 rounded-card. Re-read `PROTOTYPE.md` §0-1: refuse the median. If genre conflicts with token-preference (genre says brutalist, token-preference says soft pastels), surface to user - don't average.
- **Skimping on state-gated variants.** Modals open, drawers expanded, form errors, tab content panels, wizard steps, disabled / loading / empty - all in idle DOM. The audit will route missing variants through proposals, but the gallery is where the matrix lives.
- **Gallery chrome leaking into product classes.** `.ds-btn-primary` is the broken path. Real product class is `.btn-primary`; gallery just renders `<button class="btn-primary">…</button>`.
- **Tokens not bucketed.** Dumping every `--xxx` into one section. Use the seven buckets - surfaces / text / semantic / type / radii / shadows / spacing.
- **Type samples generic.** "The quick brown fox" instead of real strings the product would render. Pull a credible string per level ("Application submitted", "PXP review queue", a timestamp, a metric value).
- **Inventing classes per cell instead of composing modifiers.** `.btn-primary-icon-small` instead of `.btn-primary.icon.small`. Composition is the convention; cell explosion is the foot-gun.
- **Inheriting from `parentRef` without applying overrides.** If `spec.parentRef` is set AND `spec.tokenPreference` differs from parent, you must override the parent's tokens - not silently fall through.

## Don't

- Don't read `source/` for inspiration. The DS comes from the spec; feature pages are downstream consumers.
- Don't write `DESIGN.md` - that's Workflow 3.
- Don't write `editor/design-systems/<id>.js` - Workflow 0 generates the mirror after you finish.
- Don't add a build step / TypeScript / Tailwind / icon library.
- Don't pick the median.

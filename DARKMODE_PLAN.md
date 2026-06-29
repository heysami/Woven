# Editor dark mode — study & implementation plan

Status: IMPLEMENTED (Phase 0-2 + landing; literal sweep = breakage-class only). See §10.
Scope: the **Woven editor's own UI/chrome** (`editor/`). NOT the generated prototypes,
NOT the `default-design-system` (which already has dark mode).
Goal: a Light / Dark / **System** preference under Settings → Preferences, applied to the editor chrome.

---

## 1. Why this is risky (and why it broke before)

Anything that paints color through `var(--token)` flips for free when we remap tokens.
Anything that writes a **raw color literal** (hex / rgb / rgba / bare oklch) does **not** flip.
Past color changes broke widely because literals are scattered across both `styles.css` and `app.js`,
and because some literals are *meant* to be fixed (content previews, semantic palettes) and must not be inverted.

History to respect (from git):
- `c80f9e51` — a single dropped `}` inside a `:root[data-theme=…]` block silently swallowed all CSS after it. **Validate brace balance after every block edit.**
- `efad7052` — `color-mix(in oklch, …)` drifted hue (teal → peach); fix was `in oklab`. **Relevant because we chose auto-derivation (see §4).**
- `2f2f7bad` — `--text-faint` had to be darkened so small labels stayed legible. **Faint text is the first thing to fail; verify it explicitly in dark.**
- `49a7c4cb` — an mmcomposer restyle was reverted for breaking the effects UI. **Touch mmcomposer carefully; verify the whole subsystem.**
- Landing page dot-grid is a cursor-reveal radial-gradient mask (`#000`/`rgba(0,0,0,.9)` hardcoded) — **test the reveal interaction in dark.**

---

## 2. Current state (audited)

### Token foundation — GOOD
- `editor/styles.css:7-92` — primary `:root` block, all colors in **oklch**: `--bg`, `--surface`, `--surface-2/3`,
  `--border`, `--border-strong`, `--canvas-bg`, `--canvas-dot`, `--text`, `--text-muted`, `--text-faint`,
  `--accent*`, `--hot*`, `--success/ok/warning/danger(+soft)`, `--shadow-sm/md/lg`.
- Two **scoped** token blocks (additive, not conflicting):
  - `:root` whiteboard palette `--wb-*` at `~8045-8058` (sticky-note / FigJam colors).
  - `:root` data-type port palette `--dtype-*` at `~10676-10684` (logic-graph port identity colors).
- `.workflow-node` (~8793) intentionally re-tints `--surface/--border` warm — keep as-is.

### Dark infrastructure — ABSENT
- No `:root[data-theme="dark"]` block anywhere in `editor/styles.css`.
- No `prefers-color-scheme` in the editor core (only in 3 unrelated tool iframes).
- `editor/index.html` ships `<html data-theme="light">` — the attribute hook exists, unused for dark.

### Persistence + settings — GOOD, reuse it
- `app.js:7216-7225` — `SETTINGS_KEY = "th.editor.settings.v1"`, `loadSettings()`, `saveSettings(patch)` (localStorage, shallow-merge).
- `app.js:7250-7271` — the established live-apply pattern (`loadNodeSimplify`/`applyNodeSimplifyAttr`/`saveNodeSimplify` + `th:node-simplify-changed` custom event + toggle attr on `<body>`). **Mirror this exactly for theme.**
- Settings modal: `WorkflowSettingsDialog` (`app.js:~78676`), Preferences tab body = `WorkflowSendKeySection` (`~78773`). New control goes here.
- Settings-row markup pattern to match: `.workflow-settings-section` + `.onboarding-sendkey-head` + `.onboarding-sendkey-seg[role=radiogroup]` + `.onboarding-sendkey-opt[role=radio][data-active]`.

### Reference pattern that already works in-repo
- `editor/default-design-system/styles.css:~885` — `:root[data-theme="dark"]{}` remaps semantic tokens; style overlays use `:root.ds-scheme-dark[data-theme="<style>"]`. Components reference tokens, so they flip without duplicated CSS. **This is the model for the chrome.**

---

## 3. The six buckets (what flips, what must NOT)

Counts below are approximate magnitudes from the audit, not exact.

| Bucket | What | Where (examples) | Action |
|---|---|---|---|
| **A. Chrome tokens** (already `var()`) | surfaces, text, borders, shadows | styles.css uses throughout | Remap in dark block → flips free |
| **B. Hardcoded chrome colors** (~the real work) | real panel `#fff`, `rgba(0,0,0,.06)` hovers/scrims, code-block `oklch(98% .002 250)` (~22×), `var(--x,#888)` light fallbacks | styles.css broad; app.js inline styles | Tokenize → then flips |
| **C. Semantic identity palettes** | `--wb-*` sticky colors, `--dtype-*` ports, status dots | 8045, 10676; share status dots 27701+ | Keep hue; nudge lightness only. **Do not invert.** |
| **D. Content / preview swatches** | DS style-tile previews, share thumbnails | styles.css **933-1050**, **27701-27850** | **Leave literal.** They depict other designs. Inverting = bug. |
| **E. Embedded iframes** | prototype preview, app-node iframes, share viewer | PrototypeDoor `app.js:~23436`; WorkflowCanvas instances | **Never force-themed.** User content owns its theme. |
| **F. JS-set colors** | SVG marker/node fills (oklch), canvas stats overlay, inline-style literals | app.js: markers `~4028-4030`, flow nodes `~5026-5131`, overlay `~83340` | Tokenize/fix; repaint canvas on theme change |

**Landmines = D and E.** The single largest "hardcoded cluster" (the ~58-color DS style-tile system, 933-1050) is in bucket D and must be **excluded** from the sweep.

---

## 4. Palette derivation — AUTO-DERIVED (chosen) + guardrails

Decision: derive dark tokens programmatically from the existing light oklch tokens rather than hand-authoring each.

Approach:
- Author dark tokens as oklch with **flipped/curved lightness** (not a naive `100 - L`): backgrounds go low-L,
  text goes high-L, mid surfaces compress toward the dark end. Chroma reduced slightly on large surfaces.
- Accent/semantic hues (`--accent`, `--hot`, `--success`, `--warning`, `--danger`, `--wb-*`, `--dtype-*`)
  **keep their hue and chroma**; only lightness is lifted enough to stay legible on dark surfaces.
- Shadows: in dark, drop-shadows read weakly — lean on a faint light **border/inset** instead of darker shadow.

Guardrails (because auto-derivation is what bit us before):
- **Any blending uses `color-mix(in oklab, …)`, never `in oklch`** (avoids the teal→peach drift, efad7052).
- After generating, **eyeball every accent + `--text-faint` on a real dark surface**; bump lightness where contrast < ~4.5:1 for text.
- The derived set is a **static authored block** in `styles.css` (computed once, pasted in), not runtime `color-mix` on every element — keeps it auditable and avoids per-paint drift.

---

## 5. Architecture

1. **One dark block** `:root[data-theme="dark"]{ … }` in `styles.css` remapping the ~40 chrome tokens,
   plus dark variants of `--wb-*` and `--dtype-*` (lightness-lifted, hue-preserved).
2. **Three-way preference** Light / Dark / System. "System" attaches a
   `matchMedia('(prefers-color-scheme: dark)')` listener that live-updates the attribute.
3. **No-flash boot**: a tiny synchronous script in `editor/index.html` `<head>` (before `#boot-veil`)
   reads `localStorage["th.editor.settings.v1"].editorTheme` (resolving "system" via matchMedia) and sets
   `document.documentElement.dataset.theme` before first paint.
4. **Toggle UI** in `WorkflowSendKeySection`, matching `.onboarding-sendkey-*` radio pattern; persists via
   `saveSettings({editorTheme})`, broadcasts `th:editor-theme-changed`.
5. **Live apply + canvas repaint**: an `applyThemeAttr()` listener sets the attribute and forces one workflow-canvas
   repaint so canvas-drawn colors (those read via `getComputedStyle`) refresh; fix the one hardcoded canvas overlay.

---

## 6. Phased plan (each phase shippable + verified before the next)

- **Phase 0 — Plumbing, zero visual change.** Toggle + persistence + System listener + no-flash boot, with the dark
  block initially empty (dark == light). Verify: preference persists across reload, OS-match flips live, no visual diff in light.
- **Phase 1 — Dark token set (auto-derived per §4).** Remap chrome tokens + dark `--wb-*`/`--dtype-*`.
  Verify: screenshot canvas, toolbar, rails, 2-3 modals in dark; check `--text-faint` legibility.
- **Phase 2 — Bucket-B sweep, one region per commit** (bisectable): app shell → toolbar/rails → modals →
  onboarding/new-project → prototype toolbar → mmcomposer (careful) → landing page (test cursor-reveal in dark).
- **Phase 3 — app.js JS-set colors (bucket F).** SVG marker/node oklch fills, canvas stats overlay,
  light-grey `var(--x,#888)` fallbacks; wire canvas repaint-on-theme-change.
- **Phase 4 — Polish + exclusion verification.** Confirm bucket D/E untouched: DS style-tile previews still show
  each style's real colors, share thumbnails intact, prototype/app-node/share iframes unaffected.

---

## 7. Guardrails (standing rules for every phase)

- Validate `{ }` balance after each CSS block edit (one dropped brace swallows the rest of the file).
- One region per commit so a regression is a one-line `git bisect`.
- Screenshot-verify in **both** light and dark before advancing a phase.
- Maintain the explicit **exclusion list** (bucket D content previews + bucket E iframes) — never sweep those.
- `color-mix` only `in oklab`.
- Sync to the IN USE mirror per the usual rsync-wholesale rule after changes land.

---

## 8. Effort

- Phase 0-1: ~half a day → working (if rough) dark mode on core chrome.
- Phase 2-4: ~3-4 days of careful, verifiable sweeping (the long tail of bucket B + F).

---

## 9. Open decisions

- Whether "System" is the default for new users, or "Light". (Currently: **System**.)

---

## 10. Implementation log (what shipped)

Palette derivation: **auto-derived** (user choice) — static authored dark block, lightness curved, hues preserved, no runtime color-mix.

**Phase 0 — plumbing (done, verified `node --check`):**
- `editor/index.html`: synchronous `<head>` boot script sets `data-theme` from `localStorage["th.editor.settings.v1"].editorTheme` (default "system" → resolves via `matchMedia`) before first paint; theme-aware `#boot-veil` (dark variant).
- `editor/app.js` (after the node-simplify block, ~line 7272): `loadEditorTheme` / `resolveEditorTheme` / `applyEditorThemeAttr({repaint})` / `saveEditorTheme`, a `th:editor-theme-changed` event, and a live `matchMedia('(prefers-color-scheme: dark)')` listener that re-applies when pref is "system". Theme change fires a window `resize` so token-caching canvases repaint.
- `editor/app.js` `WorkflowSendKeySection` (Settings → Preferences): **Appearance** radio group — System / Light / Dark.

**Phase 1 — dark token block (done, braces balanced):**
- `editor/styles.css` after `:root` (~line 93): `:root[data-theme="dark"]{}` remapping the ~40 chrome tokens (`color-scheme:dark`), plus `:root[data-theme="dark"] .workflow-node` (warm dark node surface) and a dark `--wb-ink`/`--wb-gray`. Auto-derived; hues/chroma preserved on accents.

**Phase 2 — literal sweep, breakage-class ONLY (done):**
- styles.css: 9 chrome surfaces converted to tokens (newproj input, disabled orchestrator card, system-sidebar, system-threads, mcp-add-form, grid empty cell, prompt-inspector-ds head, comment-card, sv-mini-btn).
- app.js: 1 chrome surface converted (boot fatal-error overlay → tokens).
- Landing (done by hand as scoped overrides): cards + frosted onboarding card → `var(--surface)` (no-op in light); `.landing-root` re-based to `var(--bg)` in dark only; `.landing-bg-canvas` (JS-painted light field, no CSS hook) hidden in dark — the token-driven `::before` dot-grid carries the cursor-reveal field; header already near-black.

**Deliberately LEFT (not breakage; documented):**
- Bucket D content/preview swatches: `.dscz-styletile*` (933-1050), share thumbnails (27701-27900), `.workflow-wb-swatch-*`, flow-legend key swatches.
- Bucket E iframes/preview surfaces: `.dscz-preview-frame`, `.workflow-proto-frame`, `.workflow-browser-body`, `.zoom-iframe*`, `.ut-pick-frame`, the `oklch(100%)` iframe rule (~17204), and all baked/export/srcdoc colors in app.js (exports stay on white ground).
- ~22 colored soft-tint chips/badges/status pills (dark ink on light fill — readable in dark; cosmetic, not breakage).
- ~6 toggle knobs / handle dots; ~41 white-ink-on-accent `color:` values (correct in dark); `var(--x,#fallback)` fallbacks (token always defined).
- SVG markers + flow-node oklch identity fills in app.js (mid-lightness, read fine on dark).

**Verification status:** syntax/brace gates passed; **no live browser pass** (editor is daemon-backed; daemon is user-managed and another session's dev server occupies the folder). Needs a human spot-check in dark, especially: landing (dot-grid reveal + frosted card), mmcomposer, modals, whiteboard.

## 11. Remaining / optional (cosmetic, not blocking)
- Promote soft-tint chips/pills to dark-aware `*-soft` tokens for a more polished dark look (≈22 sites; currently readable but light-on-dark).
- Re-base the SVG markers / flow-node fills to tokens if the graph palette should shift in dark.
- Visual QA the landing field density + frosted blur in dark; tune `--canvas-dot` / node warmth if desired.

**To appear in the running editor:** changes are in `editor/`; sync to the IN USE mirror per the usual rsync-wholesale rule (left to the user given concurrent sessions / user-managed daemon).

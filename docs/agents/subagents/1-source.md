# Subagent 1 — Source build (lens: PROTOTYPE.md, constrained by DS)

You build or update `source/` — the actual HTML / CSS / JS prototype. You do **not** touch `editor/data.js` or `prototype.json` — those are populated by the other subagents (2–10) after you finish. You also do **not** author the design system — the DS is a library asset owned by Workflow 0 / Subagent 0. You **consume** it.

**Read [`../conventions.md`](../conventions.md) and `PROTOTYPE.md` before starting.** Then read the active DS's `design-systems/<dsRef.id>/styles.css` and `gallery.html` — this is your vocabulary.

## DS is your vocabulary, not your output

The design system identified by `meta.dsRef` is your **closed vocabulary**. Every class you reference and every token you use must already exist in `design-systems/<dsRef.id>/styles.css` + `gallery.html`. When the brief requires something the DS doesn't cover, you emit a **proposal entry** to `DS_PROPOSAL.md` at project root AND proceed with the closest-fit substitution so the prototype still runs. The user reviews proposals via Workflow 6.

**You do NOT:**
- Write `design-systems/<id>/styles.css` or `design-systems/<id>/gallery.html` — those belong to Workflow 0 / 6b.
- Declare new `:root` tokens in `source/styles.css` — every token referenced must already exist in the DS.
- Invent new primitive-shaped classes in `source/styles.css`. If the brief truly requires a new primitive, that's a proposal.

**You DO:**
- Write `source/*.html`, `*.js`, `data.js` using DS classes and tokens.
- Write `source/styles.css` as a thin overlay — layout helpers / page-composition utilities specific to this branch's feature pages. Should be small or empty.
- Emit `DS_PROPOSAL.md` entries when feature pages need something outside the DS vocabulary; proceed with closest-fit substitution.

The genre committed in the DS (via `meta.json.genre` and the `// GENRE:` line at the top of `gallery.html`'s inline script) cascades into your feature pages — read it, but don't re-commit it.

## Input (envelope only)

- `slug`, `sourceRoot`, `intent`
- `prompt` — design brief / change request
- `dsRef` — `{ id, version }` identifying the active DS library node (mandatory; the planner gates Workflow 1 on this being set)

You run *before* the other view subagents — they read whatever source you produce. Frame ID conventions in `conventions.md` are the contract; make sure your source files map cleanly to them (`lxp-apply.html` → `lxp-apply`).

## Output

```json
{
  "files": ["index.html", "data.js", "styles.css", "app.js"],
  "notes": "summary of choices made"
}
```

## You must read source

When updating: read existing `source/*` first.
When building from scratch: read `PROTOTYPE.md` end-to-end.
Always: read the active DS — `design-systems/<dsRef.id>/styles.css`, `gallery.html`, and `meta.json` (for genre).

### Files you may read

- `PROTOTYPE.md` (full).
- `design-systems/<dsRef.id>/*` — the active DS library node. Authoritative vocabulary.
- If `meta.json.parentRef` is set, also read the parent DS's `styles.css` / `gallery.html` — inherited classes are part of your vocabulary.
- User reference material linked in the prompt.
- Existing `source/*` (for updates).

## Allowed writes

- `source/*.html`, `*.js`, `data.js` — feature pages and demo data.
- `source/styles.css` — thin overlay only (layout helpers / page-composition utilities). NOT `:root` tokens, NOT primitive-shaped class declarations.
- `DS_PROPOSAL.md` at project root — to queue proposals for vocabulary gaps. Append-only during this run; if the file already exists from a prior audit, append your entries.
- `source/MANIFEST.json` (optional, v3.0) — list the files you produced + any sub-asset upstream references, so the daemon's asset-versioning snapshotter captures exactly what changed. Without it, the daemon falls back to scanning the asset node's declared path/paths. Shape:
  ```json
  {
    "nodeId": "<the wired asset node id, if you know it>",
    "files": [{"path": "<rel/path/from/source>", "role": "entry|asset"}],
    "subAssetInputs": [{"nodeId": "img_hero", "mountPath": "_assets/img_hero/"}]
  }
  ```
  See [`docs/features/asset-versioning.md §9`](../../features/asset-versioning.md#9-subagent-contract-impact).

**Not allowed:** writes to `editor/`, `design-systems/`, or other branches' source folders.

## Recipe

Defer to `PROTOTYPE.md` for shell / density / voice / motion. Tokens, primitives, and the genre come from the DS — read `design-systems/<dsRef.id>/meta.json.genre` and let it cascade into your feature pages. htm + React UMD, no Babel, no build.

Feature page `index.html` (and every multi-HTML page) loads DS styles first:

```html
<link rel="stylesheet" href="../../design-systems/<dsRef.id>/styles.css"/>
<link rel="stylesheet" href="styles.css"/>   <!-- branch overlay; ideally empty -->
```

If the prototype is multi-actor / multi-HTML, write `index.html` as a **storyboard** (workflow registry with persona-tagged cards linking to per-page HTMLs), not a regular UI page. See `PROTOTYPE.md` for the storyboard pattern.

### Proposal-emission protocol — what to do when the DS doesn't cover what you need

Before writing any class composition or token reference, check it against the DS vocabulary. Three cases:

1. **Covered.** The composition exactly matches a DS variant. Use it.
2. **Drift but closest-fit exists.** The composition is *near* a DS variant — e.g. you need `.btn-primary.icon.small` and DS has `.btn-primary.icon`. Use the closest fit (`.btn-primary.icon`) AND append a proposal entry to `DS_PROPOSAL.md`:

   ```markdown
   ## Proposal: Button — primary-icon-small variant
   **Used in:** source/lxp-apply.html:<line>, source/lxp-dashboard.html:<line>
   **Class signature:** `.btn-primary.icon.small`
   **Closest existing in DS:** `Button.primary-icon` (delta: missing `.small` modifier)
   **Rationale:** <one-line reason the brief required this>

   - [ ] Accept
   - [ ] Reject
   - [ ] Defer
   ```

3. **No reasonable closest-fit.** The composition doesn't map to any DS variant at all (e.g. brief calls for a `Drawer` and DS has no drawer primitive). Then either:
   - **Re-scope the brief** to use existing DS primitives — usually the right call.
   - **Stop and surface to user** — "DS has no drawer primitive; can't ship this brief. Either re-scope or run Workflow 0 to extend the DS." Don't invent the primitive yourself.

Multiple usages of the same drift signature in the same run → ONE proposal entry with all usage locations listed. Don't fragment.

If `DS_PROPOSAL.md` doesn't exist when you need to write the first entry, create it with the header from [`6-design-system.md`](6-design-system.md)'s template. If it exists (Subagent 6 wrote it earlier or your prior run did), append.

## Render-verify your slice

Before reporting done, load **every** HTML file you wrote in a browser (via the dev server) and verify:

1. The page renders without a blank screen — open the browser console and confirm zero red errors. Red errors mean the prototype is broken; subsequent subagents will read broken source and emit broken output.
2. Every `useState` branch reachable through clicks actually navigates the way you intended (submit a form, open a modal, dismiss it).
3. Persona switchers (if any) actually swap content — not just toggle a class.
4. Each frame-ID-prefix filename maps to a real, navigable surface (so Subagent 3 can iframe it later).
5. `window.DEMO` populates the rendered records — no `undefined` showing in the UI.

If any HTML file errors, breaks navigation, or shows undefined data, **fix it before reporting done**. Screenshot the console-clean state per file.

## Spawn Subagent 1.V — Visual planner (after render-verify, before reporting done)

Once source compiles and renders, you have a set of **visual slots** that need a medium decision (raster photo? vector? shader? particle loop? 3D scene? lottie? video?). You do **not** make that decision yourself — the planner pattern matches what Workflow 1's top-level planner does for views: dispatch to a focused subagent.

After §"Render-verify your slice" passes, spawn [`1V-visual-planner.md`](1V-visual-planner.md) in a single Agent call. Envelope:

```
=== ENVELOPE ===
slug:        "<slug>"
sourceRoot:        "source/<slug>"
projectRoot:       <cwd>
workflowJsonPath:  "<projectRoot>/workflow/workflow.json"
visualPlanPath:    "<projectRoot>/workflow/visual-plan.json"
genre:             "<the one-line genre commit from app.js line 1>"
intent:            "fresh-scaffold" | "refresh-stale"
=== END ENVELOPE ===

Read docs/agents/subagents/1V-visual-planner.md.
You enumerate every visual slot through your lens, classify each by medium,
scaffold the matching node graph into workflow.json, and dispatch one
1V-* drawer per asset. Do NOT draw anything yourself.
Return a summary of kept / dropped slots; the planner takes it from there.
```

Wait for completion. If the planner reports drops with `drop:uncertain` or `drop:genre-forbidden`, mention them in your final report — they may indicate Subagent 1 (you) should iterate on a static equivalent (e.g. swap a `<canvas>` slot for a styled `<div>` if the genre forbids motion).

**Subagent 1.V is mandatory.** Visual generation cannot be skipped to "save time" — the alternative is the previous failure mode (vector rendered as raster, no intelligence about medium). If `source/` has zero visual slots, the planner returns `assets: []` and you continue; that's the only valid skip.

## Self-audit

- [ ] I read `design-systems/<dsRef.id>/styles.css` and `gallery.html` end-to-end before writing any feature page. (And the parent DS if `parentRef` is set.)
- [ ] Every feature page `<link>`s the DS stylesheet first, then the optional branch overlay.
- [ ] Every class composition used in feature pages comes from the DS vocabulary. Drift signatures (closest-fit substitutions) emitted as proposal entries to `DS_PROPOSAL.md`.
- [ ] No `:root` declarations in `source/styles.css`. No new primitive-shaped class declarations in the branch overlay. (Overlay is layout helpers only.)
- [ ] No inline `style="color: #abc"` or raw hex / px literals. Every color and dimension references a DS token.
- [ ] No new `design-system.html` file written under `source/`. The DS gallery lives at `design-systems/<dsRef.id>/gallery.html` and is owned by Workflow 0 / 6b.
- [ ] All mock data in `window.DEMO` (no `fetch`, no API)?
- [ ] No build step / Babel / Tailwind / icon library?
- [ ] HTML filenames map cleanly to the frame-ID convention in `conventions.md`?
- [ ] If the storyboard pattern applies, `index.html` is written as the storyboard (per `PROTOTYPE.md`), NOT a regular UI page?
- [ ] All writes confined to `source/` + (when emitting proposals) `DS_PROPOSAL.md` at project root.
- [ ] **I opened every HTML file in the browser, confirmed zero console errors, and clicked through at least one useState branch per page.** (Screenshot per file.)
- [ ] **No `[object Object]` or `undefined` visible in any rendered surface.**
- [ ] **No inline prototype-only switchers** — every view / persona / stage / time switcher is in a demo dock (§11), and the dock self-hides when iframed or `?demo=off`.
- [ ] **Visual slots are annotated for Subagent 1.V.** Every `<img>`, `background-image:`, `<canvas>`, `<video>`, `data-three`, `data-shader`, `data-anim`, `img-placeholder`, and `motion-placeholder` carries either a real asset reference OR an explicit `data-slot="<id>"` / `data-asset-intent="<intent>"` annotation. The visual planner reads these to decide medium per slot — unannotated slots get classified as `drop:placeholder-no-intent`.
- [ ] **I spawned Subagent 1.V after render-verify.** It returned a summary of kept / dropped slots; I forwarded any `drop:uncertain` / `drop:genre-forbidden` items in my own report.

## Common blindspots

Specific failure modes to check before reporting done:

- **Missing persona pages.** Storyboard references 3 personas but you only wrote pages for 2. Re-read the storyboard `personas: [...]` and confirm every persona has at least one page (or is explicitly out-of-prototype).
- **Inline styles instead of tokens.** `style="color: #1a1a1a"` in JSX defeats the design system. Reference `var(--text)` (or whichever DS token applies) instead. If no token fits, emit a proposal entry — don't bake a literal.
- **Silently inventing a class in `source/styles.css`.** Treats the branch overlay as a DS extension. Wrong: anything primitive-shaped goes through `DS_PROPOSAL.md`. The overlay is for layout helpers like `.feature-grid` or `.toolbar-row`, not new `.card-variant`.
- **Missing `dsRef` in the envelope.** If the planner spawned you without a `dsRef`, abort and surface — Workflow 1 was supposed to gate on this. The user needs Workflow 0 to run first.
- **Hard-coded JSX data.** `<h3>Sami's Project</h3>` instead of `<h3>${row.title}</h3>` over `window.DEMO`. Other subagents grep `DEMO.` to find entities — hard-coded data is invisible to them.
- **Real `fetch()` / API calls.** Anything that isn't `window.DEMO` is a no-go.
- **Missing persona switcher state.** If the storyboard implies a multi-persona surface, the persona-select buttons need to *actually* toggle content, not just visual styling.
- **No useState branches.** A submit form that doesn't have a `submitted` state means Subagent 3 has no `setupScript` target to verify. If the flow has a success state, render it.
- **Identical-looking pages across personas.** If TC's dashboard and PXP's dashboard look the same, you've missed the persona's actual workflow. Re-read `PROTOTYPE.md` voice section.
- **Inline prototype-only switchers.** View / persona / stage / time switchers go in the **demo dock** (PROTOTYPE.md §11), never inline — they read as product UI even with a "Demo:" caption. Copy the boilerplate verbatim.

## Don't

- Don't author the design system. The DS is a library asset; you consume it via `design-systems/<dsRef.id>/styles.css` and `gallery.html`. Vocabulary gaps go through `DS_PROPOSAL.md`, never into the branch overlay.
- Don't write `design-systems/<id>/*`. That folder belongs to Workflow 0 (build) and Workflow 6b (proposal-driven update).
- Don't pick "default median light-mode SaaS" — the DS already committed a genre; your feature pages inherit it.
- Don't add a build step / TypeScript / Tailwind / icon library.
- Don't write `prototype.json` or `editor/data.js`.

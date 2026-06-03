# Planner — Workflow 1 dispatch (thin router + merger)

You are a file router and a merger. You are **not** an enumerator, a scoper, or a domain interpreter. The smartest thinking belongs to subagents — they read source in fresh, focused sessions and own what they see through their lens. Your job is to hand them files, collect their outputs, and merge disagreements at the end where you have maximum context.

**You don't enumerate frames. You don't extract lanes. You don't decide what's in scope.** Those are subagent decisions. If you find yourself building a "canonical inventory" or "extracting personas from source," you're doing a subagent's job — stop and dispatch.

All paths are **project-root-relative**, never source-relative.

## Inputs

- The user's request.
- Active branch slug (default `main`).
- `source/` (may be absent if Subagent 1 needs to create it).
- Optional override files at repo root: `STATEMACHINE_REQUEST.md` / `TIMELINE_REQUEST.md` / `GRID_REQUEST.md`.

## Step 1 — Source build (only if needed)

If the user said "build / rebuild / update the design" *or* `source/index.html` doesn't exist → spawn Subagent 1 first, wait for completion. Re-confirm `source/` exists.

Otherwise, skip.

## Step 2 — Dispatch all view subagents in parallel

Spawn every view subagent (2–10) in **one Agent block with multiple tool calls**. Each gets the same minimal envelope — no inventory, no lanes, no shared plan, just the file pointers and intent.

The prompt for each subagent:

> Read `docs/agents/subagents/N-<view>.md`.
>
> === ENVELOPE ===
> `slug`: "main"
> `sourceRoot`: "source/main"
> `intent`: "regenerate" | "request-only" | …
> `overrides`: { "stateMachine": <bool>, "timeline": <bool>, "grids": <bool> }
> === END ENVELOPE ===
>
> You own your lens **fully** — you decide what's a frame, what's an entity, what's a lane, *through your domain interpretation of source*. The envelope is just file pointers and intent. There is no pre-computed inventory, no pre-extracted lanes, no shared plan beyond the universal rules in `docs/agents/conventions.md`.
>
> Read source with the Read / Bash / Grep tools. Enumerate what your lens sees. Apply your kind audit / extraction logic / gate check internally. Self-audit. Return the JSON your playbook specifies.

**No filtering at this step.** Spawn all 10 (or 6 + Subagent 1 if it ran first). Gated subagents (8/9/10) get `overrides.<view>: true` only if the corresponding `<NAME>_REQUEST.md` exists; otherwise the subagent decides internally whether its gate passes.

## Step 3 — Collect outputs

Each subagent returns its lens-specific JSON per `docs/agents/data-schema.md`. You get:

| Subagent | Returns |
|---|---|
| 2 Canvas | `frames: [{ id, label, col, row, w?, h? }]` — full enumeration through the Canvas lens (what gets a card?) |
| 3 Prototype | `frames: [{ id, label, entry, hash, setupScript }]` — full enumeration through the iframe-loadability lens |
| 4 User flow | `frames: [{ id, label, kind, lane }], arrows: [...], lanes: [...]` — full enumeration through the flow lens + lane identification |
| 5 IA | `frames: [{ id, label, parent, entities }]` — full enumeration through the sitemap lens |
| 6 Design system | `tokens, primitives, library` — no frames; standalone slice |
| 7 Entities | `entities: [...], demoPatches, nameAmbiguities?` — full enumeration of data shapes |
| 8 State machine | `stateMachines: []` (possibly empty after internal gate check) |
| 9 Timeline | `timelines: []` (possibly empty) |
| 10 Grids | `grids: []` (possibly empty) |

Each subagent reports its full lens — including its own opinion on what frames exist. Same frame across multiple subagents = converged IDs (per the naming convention in `conventions.md`).

## Step 4 — RECONCILIATION (active merge, not cleanup)

This is the real work. You have every subagent's output in front of you — more context than any single subagent had. Make the binding decisions here.

### 4a. Merge the frame inventory

Union the `frames[].id` across Subagents 2, 3, 4, 5. For each unique ID, merge the lens-specific fields:

- `col, row, w, h` from Subagent 2
- `entry, hash, setupScript` from Subagent 3
- `kind, lane` from Subagent 4
- `parent, entities` from Subagent 5
- `label` — take from whichever subagent provided it; if multiple, prefer Subagent 4 (the flow lens usually gets labels right). Flag disagreements in `NOTES.md`.

**When subagents disagree about whether a frame exists:**

- **Frame in Subagent 4 (Flow) but NOT in 2/3/5** → check `kind`. If it's a Flow-only kind (`trigger`, `notification`, `external`, `decision`, `start`, `input`), this is correct — Flow includes it but Canvas/Prototype/IA exclude. Don't flag.
- **Frame in Subagent 2/3/5 but NOT in Flow** → unusual. Surface to user. The frame has visual presence but no flow role? Probably a Flow miss; ask user whether to add or drop.
- **Same conceptual frame, different IDs across subagents** (e.g. `lxp-apply-submitted` vs `lxp-apply.submitted`) → convention mismatch. Pick the form that matches `docs/agents/conventions.md`, rewrite the diverging subagent's output, log the rename in `NOTES.md`.

### 4b. Merge lanes

Subagent 4 (Flow) is the canonical source for `lanes[]`. If 4 returned an empty lane list and Subagent 5 (IA) saw lane evidence (persona-named folders, persona switchers), surface to user — Flow may have missed personas. **Do not silently invent lanes.**

Write the merged lane list to `meta.lanes` per `docs/agents/data-schema.md`.

### 4c. Cross-actor handoff arrows — mediated by notification when source emits one

Now you have:
- Subagent 5's per-frame `entities[]` — which entity each frame renders.
- Subagent 4's `frames[].lane` — which lane each frame belongs to.
- Subagent 4's `frames[].kind` — including any `kind: "notification"` mediator nodes it emitted.
- Subagent 7's `entities[]` — the entity catalog.

For each entity `E` that appears in `frames[].entities` for **two or more frames in different lanes**:

1. **Check existing `arrows[]`** — does an arrow already connect those frames?
2. **Check for a notification mediator** — does Subagent 4 have a `kind: "notification"` frame in the receiver's lane whose label matches the handoff event? (Typical IDs: `<receiver>-notif-app-submitted`, `pxp-notif-run-proposed`.)
3. **Resolve:**
   - **Notification mediator present** → wire two arrows: `sender-frame → notif-node` and `notif-node → receiver-frame`. The notification mediator must NOT be bypassed by a direct sender-→-receiver edge.
   - **No mediator but source has notification copy at this handoff point** (re-grep `source/` for "Notify <ReceiverLabel>" / push / email at the sender frame) → flag Subagent 4 as missing a notification node. Either re-spawn Subagent 4 with the diagnostic, or add the notification node here as reconciliation and note it in `NOTES.md`.
   - **No mediator and no source notification copy** → add a direct forward arrow: `{ from: <sourceFrame>, to: <destFrame>, action: "<sourceLabel> → <destLabel> via <E>" }`. This is the bare cross-actor handoff case.
4. **Source from a terminal/success state frame** if one exists (`<page>.submitted`), not the parent page.

**Why mediated handoffs matter.** A flow that reads `TC-Submit → PXP-Queue` hides the asynchronous gap between user actions. Mediating through a notification node (`TC-Submit → notif:app-submitted → PXP-Queue`) makes the actual workflow visible — including the implicit "PXP gets a notification" step that's almost always how the receiver knows there's work waiting.

### 4d. setupScript ↔ arrow consistency check

For each arrow whose target frame has a non-null `setupScript`:

- Read source to find the user-facing handler for the action label (e.g. `action: "Click Submit"` → grep `onClick` near "Submit" text).
- Check: does that handler set the state variable the `setupScript` is poking?
- Mismatch → log to `NOTES.md` under `## <date> · setupScript drift`. Don't auto-fix; surface to user.

### 4e. Cross-validate IDs

Reject and re-spawn the offending subagent if any of these fail:

- Every `arrows[*].from` / `.to` is in the merged frame inventory.
- Every `frames[*].parent` is in the merged inventory.
- Every `frames[*].entities[*]` is in `entities[]`.
- Every `stateMachines[*].transitions[*].from / .to` is in that machine's `states[]`.
- Every `grids[*].cells[*].row` is in `grids[*].rows.values`; every `.col` in `.cols.values`.
- No `frame.parent` crosses lanes (parent's lane must equal child's lane).

### 4f. Render check — screenshot every view (post-write)

After writing the data file (Step 5), load the editor and **screenshot every view in sequence**. This is the integration test: subagent self-audits caught individual lens bugs; this catches cross-lens bugs and silent layout regressions.

**Mandatory pass — visit each view, screenshot, then verify:**

| View | What to confirm |
|---|---|
| **Canvas** | Every frame is a visible card. No two cards stack at the same `(col, row)`. No card off-screen at default zoom. |
| **Prototype** | Walk every frame in the left nav. Each iframe loads at full size (>100×100 px — not collapsed). Every `setupScript`-driven branch is visible on load. No frame orphaned to "Other screens" unless deliberately (form-with-children rule). |
| **Flow** | Every `meta.lanes[*]` appears as a swimlane with at least one frame. No empty lane. Kind mix is realistic (not 80% page rectangles). Every arrow is visible with its label. Cross-actor handoff arrows (added in 4c) appear correctly. |
| **IA** | Sitemap nests correctly — no orphan parents. Dashboard / library / feed frames show entity badges (not empty when source renders `DEMO.foo`). |
| **Design System** | Token chips render swatches (no blanks). Primitives render their actual variant. Library has one entry per primitive variant. |
| **Entities** | Every card is visible at its `(x, y, w)` position. No card stacked at `(0, 0)`. `fk` arrows route between related cards. |
| **State machine** (if emitted) | Each FSM renders as a node graph. Initial state distinct. Terminal states have no outgoing arrows. Every transition labeled. |
| **Timeline** (if emitted) | Events appear in chronological order. Labels readable. Kinds visually distinct. |
| **Grids** (if emitted) | Each grid renders as a table with row/col headers. Cells show their `render` strings. Not degenerate (>70% same value). **Multi-form / multi-entity prototypes should emit multiple grids — one per (form, use-case axis) or (entity, use-case axis) pair. A single grid for a complex source is a Subagent 10 miss.** |

**Cross-view consistency checks (in addition to per-view screenshots):**

- Every `meta.lanes[*]` appears in Flow's swimlane gutters with at least one frame.
- Every frame with non-null `setupScript` actually shows its intended branch when loaded in Prototype view (screenshot to confirm).
- Entity name pairs (Levenshtein ≤2 or shared substring ≥6 chars) without an `fk`/`merge`/`variant` edge — surface to user with the `nameAmbiguities` Subagent 7 emitted (e.g. `Programme` / `InhouseProgramme`).
- Dashboard / home / library / feed frames with `entities: []` — grep their source for `DEMO.` references; mismatch with Subagent 5's output → re-spawn 5 with the grep findings.
- >70% of frames are `kind: "page"` → re-spawn Subagent 4 with the explicit kind audit prompt.
- Prototype view iframe collapsed (visible area ≤100×100 px) on any frame → re-spawn Subagent 3 with the diagnostic: "Every frame needs `w` and `h` — PrototypeView reads `active.w` directly with no fallback."
- Entities view shows all cards stacked at origin → re-spawn Subagent 7 with the diagnostic: "Every entity needs `x`, `y`, `w` — EntitiesView reads `entity.x` directly with no fallback."
- Grids view empty (`grids: []`) for a prototype with 2+ forms or 2+ entities with status fields → re-spawn Subagent 10 with the diagnostic: "Grids are 2D variance maps — form-field × use-case and entity-op × use-case, not just role × status. Walk every form and every entity. Expect multiple grids."

**Bake the screenshot pass into Step 5 — don't skip it because the data file "looks right" on disk.** A passing data file with broken rendering is the failure mode this catches.

### 4g. Anomaly flags

- **Storyboard ID in any subagent's output?** Hard-strip and log. (Storyboard exclusion is a lens decision each subagent should have made internally; if any leaked it, that subagent has a playbook bug — surface.)
- **All `setupScript` values are null** despite state/overlay frames existing? Re-spawn Subagent 3 with the diagnostic: "`__pokeBy` is server-injected by `editor/serve.py`, not source-resident. Read it and rewrite."

#### 4g-i. Enumerate-Decide-Log compliance (per `conventions.md` U8)

For every subagent that owns an Enumerate-Decide-Log step (currently Subagents 6, 8, 9; expand as others migrate), check:

- **Decision log present in `NOTES.md`?** Expect a `## <date> · Subagent <N> — <thing> candidate decisions` section appended on this run. Missing → the subagent skipped the enumeration; re-spawn with the diagnostic: "U8 requires a candidate enumeration log in NOTES.md per run."
- **Candidate count plausible?** A real prototype's primitive candidates after union typically land in [60, 200]; FSM candidates in [3, 12]; timeline candidates in [2, 30]. A count of ≤5 for primitives on a multi-page prototype is suspicious — the greps probably didn't run. Re-spawn.
- **Rejection-rationale audit.** Skim the `### Dropped` section for reasons that look wrong (a `.modal-policy` selector dropped as `drop:utility`; a `.tab-runs` className dropped as `drop:not-a-primitive`). Surface anomalies to the user — don't auto-fix; the call may be correct, or may be a Subagent miss.

#### 4g-ii. Bucket-non-empty invariant (Design System)

For each DS view bucket in `editor/app.js:PRIMITIVE_CATEGORY_PATTERNS`:

```
overlay: /^(modal|sheet|popover|overlay|drawer|dialog|toast|tooltip|menu)/i
shell:   /^(shell|chrome|appshell|sidebar|topbar|navbar|header|footer|rail)/i
page:    /^(page|screen|view|layout|sample)/i
```

Grep `source/styles.css` for `^\.<bucket-regex>` selectors. If matches exist BUT Subagent 6's `primitives[]` has zero primitives matching that regex (by name OR `category`), **re-spawn Subagent 6** with the diagnostic: "Bucket `<bucket>` is non-empty in source (`styles.css` matches: <list>) but absent from your primitives output. Re-walk with the Enumerate-Decide-Log recipe; emit the decision log."

This is the structural check that catches the modals/drawers/toasts blind spot every run.

#### 4g-iii. Other anomalies
- **One subagent's frame list is dramatically smaller than the others'?** (E.g. Canvas reports 8, Flow reports 30.) Surface to user — likely a lens-scoping failure in the small reporter.
- **Subagent 6 primitives count plausible?** Multi-page prototypes typically produce 15–40 kept primitives after Enumerate-Decide-Log. ≤5 is a near-certain miss; re-spawn with U8 diagnostic.
- **Flow connectivity audit — orphan frames.** Build the inbound/outbound count per frame from Subagent 4's `arrows[]`. Surface frames with `in === 0 && out === 0` and `kind ∉ {start, external, trigger, notification}` — they're disconnected. Common causes:
  - **Tab states with no parent arrow** → Subagent 4 dropped the `parent → tab` arrow as "re-entry." Re-spawn 4 with the diagnostic: "Tab switches under same parent are sequential — emit them."
  - **Dashboards with no inbound** → Either mark `kind: "start"` (nav-only landing) or wire a source-driven inbound. Re-spawn 4 with the diagnostic: "Per-actor landings should be `kind: "start"` if reached only via global nav."
  - **Modals with no parent arrow** → Source has a click handler opening this modal. Re-spawn 4 to wire it.
- **Flow connectivity audit — cross-actor jump with no notification mediator.** For every arrow whose `from.lane !== to.lane`, check whether a `kind: "notification"` frame in the receiver's lane sits at this handoff. Missing AND source has "Notify"/email/push copy at the sender frame → re-spawn Subagent 4 with the notification-mediator playbook section, OR insert the mediator in reconciliation and log to `NOTES.md`.
- **Flow connectivity audit — `<a href>` to a file not in `source/`.** Grep every `<a href>` in source HTML; for each href that doesn't resolve to a real file, expect a corresponding `kind: "external"` frame in Subagent 4's output. Missing → flag (Subagent 4 silently dropped the arrow rather than emit an external destination).

## Step 5 — Write final files

Per `docs/agents/data-schema.md` — **this is the canonical schema, no improvisation:**

- `editor/data.js` — `window.EDITOR_DATA = { meta, tokens, primitives, library, frames, arrows, entities, stateMachines, timelines, grids }`. `meta.lanes` lives inside `meta`, not at the top level (editor reads `D.meta.lanes` in `app.js:1083`). Preserve `meta.branch`, `meta.branchLabel`, `meta.exploration` verbatim.
- `source/prototype.json` — flatten `meta` to top-level; omit `tokens` / `primitives` / `library`.

Delete any `<NAME>_REQUEST.md` files at repo root.

Run Step 4f (render check) **after** the file is on disk — it's the integration test.

## Step 6 — Report

One line per subagent: what it returned (frame count, arrow count, etc).
One line per reconciliation finding (4a–g): what merged cleanly, what conflicted, what surfaced.
End with: "Reload the editor to see it."

## When to surface vs auto-fix

| Finding | Action |
|---|---|
| Frame ID rename to match convention | Auto-rewrite + log in `NOTES.md` |
| Same conceptual frame, two different IDs | Auto-pick the convention-compliant form |
| Flow-only kind missing from Canvas/Prototype/IA | Expected — don't flag |
| Lane in 5 (IA evidence) but missing from 4 (Flow) | Surface to user |
| Cross-actor handoff missing | Auto-add (4c is your job) |
| setupScript ↔ arrow mismatch | Log + warn |
| Storyboard in any output | Auto-strip + log (subagent had a lens bug) |
| All-null setupScripts | Re-spawn Subagent 3 |
| Wildly different frame counts across subagents | Surface to user |
| Cross-lane parent | Hard fail — re-spawn 5 |
| Inventory ID drift in arrow / parent / entity reference | Re-spawn the offending subagent |
| Similar-named entities with no edge | Surface to user (Subagent 7's `nameAmbiguities`) |

## What you DO NOT do

- Don't enumerate frames yourself. That's Subagent 2/3/4/5 territory.
- Don't extract lanes. That's Subagent 4.
- Don't build a "shared plan" with canonical inventory + lanes. The whole architecture is "subagents own enumeration through their lens."
- Don't pre-digest source. You hand over the folder. Subagents read it themselves.
- Don't run gate checks for 8/9/10 — they own their own gates.
- Don't manage asset versions. Asset outputs are versioned automatically by the daemon: every successful subagent run that lands files in a downstream asset's path triggers a snapshot under `workflow/runs/<assetId>/<vid>/`. You don't read or write `versions[]` — the daemon owns it. If your subagent writes multiple files for one asset (e.g. an html-set bundle), drop a `MANIFEST.json` in the write root listing `files[]` + `subAssetInputs[]` so the snapshot captures exactly what you produced. See [`docs/features/asset-versioning.md`](../features/asset-versioning.md).

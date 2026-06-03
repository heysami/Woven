# Workflow 0 — Build / update the design system

**Triggers:** "build design system" / "update DS" / DS spec nodes change on the workflow canvas / no DS library node exists for the active branch and Workflow 1 was requested.

**Prerequisite for Workflow 1.** Workflow 1 (regenerate prototype) is gated on the active branch having `meta.dsRef` pointing at a DS library node. If no DS exists, Workflow 0 runs first and Workflow 1 picks up after.

## What this workflow produces

The design system trio + its runtime mirror + its meta record:

```
design-systems/<id>/
├── styles.css        ← tokens (:root) + canonical class rules — source of truth for tokens
├── gallery.html      ← the kitchen-sink page — source of truth for primitives (every variant in idle state)
├── DESIGN.md         ← human-readable rationale (YAML frontmatter + prose) — derived by Workflow 3
└── meta.json         ← { id, version, label, genre, builtFrom, parentRef? }

editor/design-systems/<id>.js  ← runtime mirror window.EDITOR_DS_<id>
```

See [`../data-schema.md` § "Design system library nodes"](../data-schema.md) for full shape.

## Inputs (the DS spec)

The DS is built from a **DS spec** — a small set of declarative inputs that the user assembles on the workflow canvas before requesting a build:

| Spec input | Purpose | Required |
|---|---|---|
| **Genre node** | Single committed genre line (`PROTOTYPE.md` §0–1). Drives every downstream decision: shell proportions, density, shape language, voice, motion. | Yes |
| **Reference node(s)** | One or more URLs or screenshots of shipped products that anchor the genre. | Recommended |
| **Token-preference node** | Coarse palette + type intent: "OKLCH greys, slate-blue accent, Inter, mono for IDs / timestamps". | Yes |
| **Persona/mode node** | If the system swaps brand ramps by mode (LXP=purple, PXP=orange) or supports light/dark, declare the modes here. | Optional |
| **Primitive-preset selector** | The minimum set of primitives the gallery must render at v1 — typically `buttons, pills, cards, forms, tables, modals, drawers`. | Yes |
| **Parent DS node** | For an exploration branch's DS, reference the parent DS by `{ branch, version }` so the new DS inherits and overrides instead of starting from scratch. | Optional |

The spec lives on the workflow canvas; the agent reads it as JSON via the daemon. The DS-builder subagent uses the spec — not feature pages — as its sole input. If the user has not assembled a spec, this workflow refuses to run and surfaces the missing fields.

## Recipe

1. **Read DS spec** from the workflow canvas (the daemon exposes it; ask the user for the exact endpoint when running). Confirm minimum fields: genre, token-preference, primitive-preset.

2. **Determine target `<id>`.** Default to the active branch slug (`main`, `dense-rows-experiment`, …). If the spec includes a `parentRef`, the new DS inherits from that parent — clone its trio as the starting state and apply overrides.

3. **Spawn Subagent 0 in PLANNER + parallel-section + MERGER mode** (v2.43).

   The DS build is not one subagent any more — it's a fan-out. One Claude session reading + writing the whole trio in a single pass blows context on a comprehensive DS (gallery alone can be 30–50KB for a full primitive matrix; styles.css with semantic tokens + canonical class rules adds another 10–20KB; the spec, references, parent DS, and playbook the agent has to read sit on top of that). Each sub-task gets its own subagent, each with a fresh context budget and a narrow scope.

   **3a. Planner subagent.** Reads the spec + references + parent DS (if inheriting). Outputs a plan JSON to `design-systems/<id>/_build/plan.json`:
   ```jsonc
   {
     "tokens":     { "palette": "<intent>", "type": "<intent>", "spacing": "<intent>",
                     "modes": ["<mode-id>", ...] },        // for multi-mode DS
     "primitives": [
       { "id": "buttons",   "states": ["default","hover","active","disabled","loading"] },
       { "id": "cards",     "states": ["default","selected","hover"] },
       { "id": "forms",     "states": ["idle","focus","error","disabled","valid"] },
       { "id": "tables",    "states": ["idle","sorted","selected-row","empty"] },
       { "id": "modals",    "states": ["open"] },
       { "id": "drawers",   "states": ["open"] },
       // …
     ],
     "shells":     ["centered-narrow", "mobile-top-tabs", "editorial-broken", "..."],
     "rationale":  "one-paragraph genre commit — what tonal axis this DS is committing to"
   }
   ```
   The planner does NOT write css/html. It only writes the plan.

   **3b. Tokens subagent** (one). Reads plan.json + spec. Writes `design-systems/<id>/_build/tokens.css` — just the `:root` block with every token (color, type, spacing, radius, shadow) named semantically. Includes mode variants if `tokens.modes` is set.

   **3c. Per-primitive subagents** (one per primitive in plan.json, fanned out via Task tool in parallel). Each reads plan.json + tokens.css + spec. Each writes TWO files:
   - `design-systems/<id>/_build/components/<primitive>.css` — every canonical class rule for that primitive's variants and states.
   - `design-systems/<id>/_build/components/<primitive>.html` — gallery section: one `<section class="ds-section" id="<primitive>">` with every variant in every declared state rendered in idle.

   Each per-primitive subagent only sees ONE primitive's worth of work. Buttons subagent doesn't think about tables. Tables subagent doesn't think about modals. Parallel + focused.

   **3d. Per-shell subagents** (if `plan.shells.length > 0`, one per shell, parallel via Task tool). Each writes `design-systems/<id>/shells/<shell>.css` — the page-level stylesheet for that shell using the just-built tokens.

   **3e. Merger subagent.** Reads the `_build/` outputs from 3b+3c+3d. Writes the final three files:
   - `design-systems/<id>/styles.css` — concatenates tokens.css + every components/*.css.
   - `design-systems/<id>/gallery.html` — wraps every components/*.html into the full kitchen-sink page with proper `<head>` + sectioned body.
   - `design-systems/<id>/meta.json` — id, label, genre, builtFrom, parentRef.

   Then deletes the `_build/` scratch directory.

   See [`../subagents/0-ds-builder.md`](../subagents/0-ds-builder.md) for the per-subagent contracts (input envelope, allowed writes, output schema).

4. **Compute `version`.** Content hash of `styles.css + gallery.html` (DESIGN.md is derived, so it doesn't enter the hash). Write to `meta.json.version`.

5. **Spawn Workflow 3** (`3-design-md.md`) to generate `design-systems/<id>/DESIGN.md` from the new `styles.css` + `gallery.html`. Workflow 3 runs in DS-aware mode: its source is the DS folder, not `source/`.

6. **Build runtime mirror.** Write `editor/design-systems/<id>.js`:
   - Read the four files in `design-systems/<id>/`.
   - Enumerate `tokens` from `styles.css :root` (same buckets as today's Subagent 6).
   - Enumerate `primitives` from `gallery.html` sections (same shape — one primitive per `<section class="ds-section" id="…">`, variants extracted from `.ds-sample` blocks).
   - Build `library[]` — one entry per primitive variant.
   - Inline `trio.tokensCss / galleryHtml / designMd` from the files.
   - Emit `window.EDITOR_DS_<id> = { … }`.

7. **Update branches that reference this DS.** For every `editor/data.js` with `meta.dsRef.id === <id>`, planner re-stamps `meta.dsRef.version` to the new hash and re-mirrors `tokens` / `primitives` / `library` from the DS. This is the same mirror step the planner does in Workflow 1 — extracted as a function.

8. **Render-verify.** Load `design-systems/<id>/gallery.html` in the browser via the dev server. Every section renders; no console errors; every primitive variant visible in idle state. Screenshot the page.

## Idempotency

If the spec has not changed since the last build (hash of spec nodes matches `meta.json.builtFrom` hash), Workflow 0 short-circuits: it reports "DS up to date at version X" and exits. The user can force a rebuild by passing `--force` or by tweaking any spec node.

## Difference from Workflow 6b (DS update via proposal)

| | Workflow 0 | Workflow 6b |
|---|---|---|
| Trigger | DS spec changes, or no DS exists yet | Proposal in `DS_PROPOSAL.md` accepted |
| Input | DS spec nodes | Accepted proposal entries + current DS |
| Scope | Full rebuild of trio | Surgical edit — adds/modifies specific variants |
| When | Foundational changes (genre shift, palette shift, new primitive class) | Incremental drift resolution (new variant, new state) |

Both write the same artifacts and both bump `meta.json.version`. The difference is the input shape.

## Self-audit

- [ ] DS spec has at least genre + token-preference + primitive-preset.
- [ ] `design-systems/<id>/` folder created with all four files.
- [ ] `meta.json.builtFrom` records the spec nodes verbatim (so future audits can diff against the live spec).
- [ ] `meta.json.version` is the content hash of `styles.css + gallery.html`.
- [ ] `editor/design-systems/<id>.js` exposes `window.EDITOR_DS_<id>` with the full shape per `data-schema.md`.
- [ ] Workflow 3 ran and `DESIGN.md` exists in the DS folder.
- [ ] Every branch with `meta.dsRef.id === <id>` has been re-stamped to the new version.
- [ ] Gallery renders without console errors. Screenshot captured.
- [ ] No writes to `source/` from this workflow.

## Don't

- Don't read feature pages as input. The DS is bootstrapped from the spec, not extracted from a prototype. (Workflow 6b is the path for "feature page revealed a missing variant"; this workflow is for foundational changes.)
- Don't write `source/styles.css` or `source/design-system.html`. The latter no longer exists; the former is branch-specific overrides only.
- Don't skip Workflow 3. The DS's `DESIGN.md` is part of its identity — without it, the library node is incomplete.
- Don't manually edit `editor/design-systems/<id>.js`. It's a generated mirror; edits would be overwritten on the next Workflow 0 or 6b run.

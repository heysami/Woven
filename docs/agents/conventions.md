# Conventions — read this before any subagent work

Universal rules that apply to every subagent. Replaces the old "shared plan rules R1–R9" — kept short and stable so subagents can internalize them across runs.

There is NO canonical inventory or lane list handed down by the orchestrator. **You enumerate through your lens.** These conventions ensure your enumeration converges with what other subagents see independently.

---

## U1. Read source, don't infer

The envelope your orchestrator hands you is a file pointer (`sourceRoot`, `slug`), not source content. Use Read / Bash / Grep on the files your playbook authorises. A subagent that returns output without exercising the file-read tools is broken.

## U2. Read `editor/serve.py` once if your work touches runtime behaviour

The dev server injects helpers (notably `window.__poke` / `window.__pokeBy`) into served source HTML. Grepping source for those identifiers returns nothing — they aren't in source on disk. Subagent 3 (Prototype) has this constraint primarily, but any subagent that reasons about runtime should know.

## U3. Project-root-relative paths

All file paths in your playbook resolve against the project root, not against `source/`. If you `cd source/main` in a Bash command, every subsequent relative path is wrong until you `cd` back.

## U4. Don't fabricate

- Lanes from filename prefixes (`lxp-` / `pxp-` / `admin-`) alone — those are author convention, not declared structure. Look for actual evidence (persona arrays, persona switchers, explicit actor labels, folder structure).
- Entities from frame labels — `lxp-dashboard` does not mean a `Task` entity exists. Walk `window.DEMO` or `entities.json`.
- Primitives from imagination — extract from rendered DOM.
- Type-scale samples — use real strings from rendered source.

## U5. Kind → view matrix

The data file's `frames[]` is shared across multiple editor views. Each view filters by kind:

| Kind | Renders in |
|---|---|
| `page`, `state`, `overlay`, `form`, `substep` | Canvas, Prototype, IA, Flow |
| `start`, `decision`, `input`, `trigger`, `notification`, `external` | Flow only |

If your lens is Canvas / Prototype / IA, you ignore Flow-only kinds. If your lens is Flow, you include them.

## U6. `kind` vs `parent` are independent signals

- `kind` drives Flow's rank algorithm (column position).
- `parent` drives IA's sitemap tree.
- A drill-down page needs **both**: an arrow into it (for Flow ordering) AND `parent: <listingId>` (for IA nesting). Without parent, IA shows the frame as a flat top-level orphan.
- `parent` is **intra-lane**. Cross-lane is captured by an arrow, never by parent. Setting `parent: "tc-submit"` on `pxp-queue` wrongly buries the PXP queue under TC in the sitemap.

## U7. Self-audit with evidence before returning

Walk your playbook's self-audit checklist. Every item that says "did I read X" / "did I grep Y" / "did I screenshot Z" requires an actual tool call — not implicit ticking. If you can't point at the evidence, the check failed and you should re-do.

## U8. Enumerate-Decide-Log (the antidote to selective recall)

The single most common failure across all subagents is *selective recall*: reading source, noticing the loud/always-rendered items, writing those down, silently missing everything quieter. Modals that only render when open, tabs that only show their content when active, entities that only appear in one persona's pages, transitions that only fire under specific conditions — all are routinely missed by "find X in source" recipes.

**When your playbook says "find X / enumerate X / identify X" and X is grep-derivable from source, you must use this three-step shape:**

### Step 1 — Enumerate the candidate set

Derive an **objective, finite, grep-derivable** candidate list from source. The list should be the union of every grep that could plausibly contain a member of the set you want.

Examples by lens:
- **Primitives** (Subagent 6): every `^\.<class>` selector in `styles.css` + every named component def in `*.html` / `*.js` + every distinct `className="..."` literal.
- **State-machine candidates** (Subagent 8): every entity field whose values in `window.DEMO` span ≥3 distinct strings + every `setStatus` / `setState(... "...")` literal in source.
- **Timeline candidates** (Subagent 9): every match for `setTimeout` / `setInterval` / `cron` / `schedule` / `\d+\s*(day|hour|week)` / deadline copy.
- **Tab substeps** (Subagent 3): every `activeTab` / `currentTab` / `selectedTab` / `active` useState in `*.html` AND the distinct values the source compares them against.
- **Entity links** (Subagent 7): every field with `Id` / `Ids` suffix + every value pattern that looks like another entity's `id`.

If your playbook has a "find X" step, formulate the enumeration as: "What greps, when unioned, are guaranteed to surface every X that exists in source?" Then run them. Selective recall after this step is impossible — the candidates are listed.

### Step 2 — Decide per candidate (keep / drop with a reason)

For every member of the candidate set, output exactly one of:

- **keep** → with the resulting output entry (the primitive, the FSM state, the timeline event, etc.)
- **drop:<reason-category>** → e.g. `drop:utility`, `drop:duplicate`, `drop:not-a-primitive`, `drop:binary-toggle`, `drop:placeholder-copy`, `drop:not-rendered` — each with a short specific reason.

Every member gets a decision. None is silently skipped. If you don't know whether to keep something, log it as `drop:uncertain` with what you know, and reconciliation surfaces it.

### Step 3 — Emit decision log to `NOTES.md`

Append a section to `NOTES.md` with the structure:

```markdown
## <date> · Subagent <N> — <thing> candidate decisions

Sources scanned: <list>
Total candidates: <N> (union of <a> + <b> + <c> after dedupe)

### Kept (M)
- <candidate> → <resulting output entry>

### Dropped (N - M)
- <candidate> — drop:<category> (<reason>)
```

Reconciliation reads the rejection log. The user can audit reasons and disagree. A candidate that wasn't enumerated can't be rejected — so silent omission becomes impossible. **This is the structural protection against selective recall.**

### When this applies

Every "find / enumerate / identify X" step in any subagent playbook where X is grep-derivable. If your task is enumeration, use this pattern. If your task is reasoning over an already-bounded set (e.g. "for each frame I enumerated, assign entities"), you don't need it — but the upstream enumeration that produced the set probably does.

The other side of the same rule: **if you find yourself thinking "I'll just read the file and write down what I notice," stop**. That's the recall pattern that fails. Formulate the enumeration grep first, then walk.

---

## Frame ID naming convention

All subagents derive frame IDs from source using the same convention. This is how independent subagent enumerations converge on the same IDs without a orchestrator-handed inventory.

### Base rule

Frame ID = `<filename-base>` where `<filename-base>` is the HTML filename without extension, kebab-cased.

- `lxp-apply.html` → `lxp-apply`
- `pxp-cancellations.html` → `pxp-cancellations`
- `home.html` → `home`

For single-HTML sources (SPA + hash routing), the base is derived from the route or page identifier the source uses internally:

- `#page=settings` → `settings`
- `#cmdk` → `cmdk` (or namespaced: `library-cmdk` if it's a child of `library`)

### Sub-frame suffix

Sub-frames (useState branches, modals, tabs) take the parent base + `-` + sub-frame slug (NOT a `.` separator — kebab-case throughout):

- `lxp-apply` + `submitted` useState branch → `lxp-apply-submitted`
- `home` + `invite-modal` overlay → `home-invite-modal`
- `settings` + `team` tab → `settings-tab-team`

The suffix should describe the state, not just append "modal" / "tab" / "state". Examples:

- `pxp-applications-fee-modal` (the cancellation-fee modal under `pxp-applications`)
- `pxp-applications-confirm-postpone` (the confirm-postpone branch under the same page)

### When in doubt

Subagents converging on different IDs for the same conceptual frame → reconciliation picks the convention-compliant form and logs the rename. If you're unsure which form is canonical, prefer:

- Lowercase, kebab-case (no dots, no underscores, no camelCase).
- Filename-prefix + state-suffix.
- ≤ 50 characters.

## Lane ID naming convention

Lane IDs are persona-slug: lowercase, no spaces, alphanumeric + hyphens.

- "Training Coordinator" → `tc` (if the storyboard uses an abbreviation) OR `training-coordinator` (if it spells it out).
- "Programme Experience Partner" → `pxp` OR `programme-experience-partner`.

Subagent 4 (Flow) is the canonical source of lane definitions — it identifies lanes from source evidence. Other subagents reference `lane.id` from Subagent 4's output (after reconciliation merges lanes).

## Entity ID naming convention

Entity IDs are singular PascalCase of the `window.DEMO.<key>` array name:

- `DEMO.applications` → `Application`
- `DEMO.references` → `Reference`
- `DEMO.inhouseTasks` → `InhouseTask`
- `DEMO.classesToAttend` → `ClassToAttend`

If two arrays look like they should be one entity (≥80% shared fields per merge check), the merged entity takes the more general name with `tag: "merged"`, `mergedFrom: [<original-array-names>]`.

If the entity is a variant of a base (strict superset), the variant carries the qualifying name (`InhouseApplication extends Application`) with `tag: "variant"`, `extends: <Base>`.

## Arrow ID naming convention

Auto-generated unique IDs (`a1`, `a2`, …) are fine. Subagent 4 picks them at write time. Reconciliation may renumber for stability.

## `design-system.html` — the gallery page

Every prototype with primitives ships `source/design-system.html` (PROTOTYPE.md §12). It's a TOC-driven gallery rendering every primitive variant in idle state with real product class names. Subagent 1 owns it; Subagent 6 extracts from it exclusively; Workflow 3 derives DESIGN.md from it.

- **Subagent 6**: every `primitive.from.<variant>.entry` is `"design-system.html"`. Selectors use **real product class names scoped by section anchor** (`#buttons .btn-primary`, `#cards .application-card[data-state="submitted"]`), NEVER `.ds-*` gallery chrome. Single-pass `querySelector` resolves all selectors on first paint.
- **Subagents 3 / 4 / 5 / 7**: exclude `design-system.html` from frame / sitemap / entity enumeration. It's metadata (like the storyboard), not a UI screen the user dwells on.
- **Workflow 3**: DESIGN.md's `components` section walks `design-system.html`'s `<section class="ds-section" id="<slug>">` blocks. Don't scrape feature pages.

Same exclusion rationale as the storyboard: lens-level decision each subagent makes through their own interpretation. If you find yourself enumerating `design-system.html` as a frame / page / iframe target, stop — that's a category error.

## Storyboard exclusion (a lens decision, not a global rule)

The storyboard `index.html` (titled "Overview" / "Storyboard" / "Workflows", or any file that documents the system at workflow level rather than page level) is **metadata**, not editor data. **But this is a lens decision your subagent makes — there is no shared-plan flag from the orchestrator.**

Through each lens (applies to BOTH the storyboard `index.html` AND `design-system.html`):

- **Canvas:** is this a UI page that should appear as a card? No — it's documentation / a gallery. Exclude.
- **Prototype:** is this a screen users dwell on inside the prototype? No — it's a workflow registry / primitive gallery. Exclude.
- **Flow:** is this a task-progression node? No — it's the index of tasks / a gallery, not a task. Exclude.
- **IA:** is this a sitemap node? No — it's the sitemap *description* / a primitive gallery, not a node. Exclude.
- **Entities:** is this a data shape? No — it's a workflow document / primitive gallery. Exclude.

If your lens-specific reasoning leads you to *include* a file with "Overview" / "Storyboard" / "Workflows" in its title, or a file named `design-system.html`, **stop and check.** Almost certainly a misread of intent.

Reconciliation (Step 4g) will hard-strip any storyboard / `design-system.html` ID that leaked into output and flag the subagent that emitted it.

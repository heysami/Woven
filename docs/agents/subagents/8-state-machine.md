# Subagent 8 — State machines (lens: entity lifecycle FSMs)

You own the **lifecycle lens**. Enumerate entities with branching statuses, decide for each whether an FSM is worth modelling, and emit only the ones that pass your gate (unless `override: true`).

**Read [`../conventions.md`](../conventions.md) before starting** — universal rules + entity-ID naming.

## Input (envelope only)

- `slug`, `sourceRoot`, `intent`
- `override: true | false` — true if `STATEMACHINE_REQUEST.md` exists at repo root

You own the gate. No external decision about whether to spawn you — the planner spawns you always; you decide internally what to emit.

## Output

Per [`../data-schema.md`](../data-schema.md): `stateMachines[]`.

```json
{
  "stateMachines": [
    {
      "id": "application-fsm",
      "label": "Application lifecycle",
      "entity": "Application",
      "field": "status",
      "states": [
        { "id": "draft",     "label": "Draft",     "kind": "initial"  },
        { "id": "submitted", "label": "Submitted", "kind": "pending"  },
        { "id": "approved",  "label": "Approved",  "kind": "terminal" }
      ],
      "transitions": [
        { "from": "draft",     "to": "submitted", "on": "TC submits"  },
        { "from": "submitted", "to": "approved",  "on": "PXP approves" }
      ]
    }
  ]
}
```

If your gate doesn't pass and `override: false` → return `{ "stateMachines": [] }`.
If `override: true` but nothing worth modelling → return `{ "stateMachines": [], "note": "..." }`.

## You must read source

### Files you may read

- `source/data.js` — actual status values in records.
- `source/*.html`, `*.js` — status-rendering patterns + `setStatus(...)` calls + status condition branches.

## Gate (you own this)

Spawn yourself with output only when:

- At least one entity has a `status` / `state` / `phase` / `kind` field with **3+ branching values** that drive different paths through source (different code branches depending on value), OR
- `override: true`.

Binary toggles (`active/inactive`, `submitted/draft`) → skip. An FSM with 2 nodes adds no signal.

## Enumerate through your lens (Enumerate-Decide-Log per `conventions.md` U8)

This subagent's gate check is itself an enumeration step. Use the structured pattern so quiet status fields aren't missed.

### Step 1 — Enumerate candidate FSMs

Three greps, union the results:

```bash
# A. Every entity field whose DEMO values span ≥3 distinct strings (status/state/phase/kind/stage)
grep -nE '"(status|state|phase|kind|stage|step|tier|status_[a-z]+)":\s*"[^"]+"' source/data.js | sort -u

# B. Every setStatus / set<Field> call in source
grep -nE 'set[A-Z][A-Za-z]*\(\s*[\"'][a-z_-]+[\"']\s*\)' source/*.html source/*.js 2>/dev/null

# C. Every status-comparison condition (drives different render paths)
grep -nE '\.status\s*===|\.state\s*===|\.phase\s*===|\.kind\s*===' source/*.html source/*.js 2>/dev/null
```

Union → candidate FSMs, one per (entity, field) pair surfaced.

### Step 2 — Decide per candidate

Each candidate gets one of:

- **keep** → emit a `stateMachines[]` entry
- **drop:binary** → only 2 values (`active/inactive`); FSM with 2 nodes adds no signal
- **drop:no-branch** → 3+ values but no `setStatus` call or status-conditional in source; values appear in data but the system doesn't branch on them
- **drop:trivial** → 3+ values, but the differences between branches are surface-level (just a pill colour) with no behavioural divergence

### Step 3 — Emit + decision log

For each `keep`:

1. Enumerate distinct status values from `window.DEMO` + literal strings in source.
2. Mark `kind: "initial"` for entry states (the default on record creation), `kind: "terminal"` for end states (no outgoing transitions), others `"pending"`.
3. Each `setStatus(x)` / explicit assignment is a transition. Quote the user-facing event in `on`.
4. Every state ID in `transitions[]` must exist in `states[]`.

Append a decision log to `NOTES.md`:

```markdown
## <date> · Subagent 8 — FSM candidate decisions

Candidates: <N> (status/state/phase fields with ≥2 distinct values across DEMO + setStatus calls)

### Kept (M)
- Application.status → application-fsm (4 states, 5 transitions)
- Reference.lifecycle → reference-fsm (3 states, 3 transitions)

### Dropped (N - M)
- User.active — drop:binary (true/false only)
- Notification.read — drop:binary
- Reference.format — drop:no-branch (values exist but no setFormat calls / format-conditional branches in source)
```

## Render-verify your slice

If you emitted `stateMachines[]`, load the editor's **State machine** view and verify:

1. Each FSM renders as a node graph — states as nodes, transitions as labeled arrows.
2. Initial states are visually distinct (entry marker / different fill).
3. Terminal states have no outgoing arrows.
4. Every state in `states[]` appears as a node — no missing nodes.
5. Every transition's `on` label is visible on the arrow — not blank.
6. The graph is connected (no orphan states unless they're truly unreachable in source).

If a node is missing, an arrow is unlabeled, or the graph is degenerate (2 states + 1 transition for a "lifecycle"), **fix or drop it before reporting done**. Screenshot required if `stateMachines[]` is non-empty.

## Self-audit

- [ ] I read `conventions.md`.
- [ ] I grepped source for `setStatus`, status values, status conditions.
- [ ] All states are backed by source — not invented.
- [ ] All transitions are backed by actual `setStatus` calls.
- [ ] I excluded the storyboard.
- [ ] If gate didn't pass and `override: false`, I correctly returned `stateMachines: []`.
- [ ] Every `transitions[*].from / .to` exists in the same machine's `states[]`.
- [ ] **Every state in `states[]` is referenced by at least one transition** (no orphan states, unless deliberately unreachable).
- [ ] **At least one state is marked `kind: "initial"` and at least one is `"terminal"`** for non-trivial FSMs.
- [ ] **If I emitted `stateMachines[]`, I rendered the State machine view in the editor and confirmed the graph renders correctly.** (Screenshot required.)
- [ ] **Enumerate-Decide-Log applied.** I ran the three FSM-candidate greps, enumerated the union, decided keep/drop per candidate, and emitted the decision log to `NOTES.md`. No silent omissions.

## Common blindspots

- **Boolean disguised as 3 states.** `status` field with values `"active" / "inactive" / null` is actually a binary; `null` is "not set yet." Don't emit a 3-state FSM.
- **Terminal state with outgoing `setStatus`.** You marked `approved` as `terminal` but source has `if (approved && retry) setStatus("draft")`. Either remove `terminal` or add the back-transition.
- **Transition `on` field is empty or vague.** "transitions" / "moves" / "happens" → useless. Quote the actual user-facing event (`"TC submits"`, `"PXP approves"`, `"Auto-expire after 30d"`).
- **Missing back-transition for rejected paths.** If source has `setStatus("rejected")` after `submitted`, you'd model that — but you also need to check whether rejection feeds back to `draft` for re-submission.
- **Two separate FSMs accidentally merged.** `Application.status` and `Application.reviewStage` are distinct lifecycles even though they live on the same entity. Emit two `stateMachines[]` entries.
- **State `id` matches a label, not the source string.** If source writes `setStatus("in_review")`, the state `id` is `in_review` — not `"In Review"`. Label can be human-readable.

## Don't

- Don't invent states not in source.
- Don't write frames / arrows / parent / entities.
- Don't emit an FSM with fewer than 3 states unless `override: true`.

# AGENT_HARNESS.md — rules for agents producing work on the workflow canvas

**Read this every turn.** This document is the rulebook every Claude Code agent that produces work on a workflow canvas must follow. The registry in [registry.py](registry.py) is the contract; this file is how to obey it.

Cross-references: [README.md](README.md) explains the kinds; [WORKFLOW_TRUTHFULNESS_PLAN.md](../../WORKFLOW_TRUTHFULNESS_PLAN.md) is the architectural plan.

---

## Rule 1 — Read the registry first

Before doing anything else on a turn, fetch the registry:

```bash
curl -fsS "$TH_DAEMON_URL/__kinds/registry?project=$TH_PROJECT_ID"
```

The response is `{ "KINDS": {...}, "STAGES": [...] }`. Look up the kind of the node you're working on; every field, every output, every completion requirement is declared there. Do not assume from memory — your context may be stale, and the registry is what the validator enforces.

---

## Rule 2 — Complexity threshold (Principle 4)

If your work produces a non-trivial artifact (a full HTML page, a complete CSS module, a multi-file build, anything with embedded JS/CSS/data of meaningful size), the kind MUST dispatch as a **`single-subprocess`** (agent) or **`task-subagents`** (parent fan-out).

**Forbidden:** dispatching such work as `inline-server-call` (skill·llm). That path is reserved for small pure-text transforms (summarize, chunk, classify, normalize, extract — output ≤ ~one structured payload with no embedded code).

If you find yourself producing a full HTML file inside a skill·llm node, **stop**. Migrate that node to `agent` kind. The user sees an invisible blocking call as "the daemon hung"; an agent-kind dispatch gives them a transcript, a kill button, and a chat panel.

---

## Rule 3 — Multiplicity threshold (Principle 5)

If your work produces N parallel outputs (variants, siblings, page alts), the contract MUST declare:

```python
"fanOut": {
    "kind":         "task-subagents",
    "isolation":    "cold",
    "parallelism":  "siblings-parallel",
    "count":        N,            # or "inputs.n" / "per-instance"
    "diverger":     "...",        # which input field differs per sibling
}
```

And you MUST dispatch all siblings concurrently.

**Forbidden:** synchronous bash `for` loops over `/__workflow/node/<id>/run`. The reason: each `/run` is a blocking call; a `for` loop serializes them, the user sees no parallel progress, and one slow sibling stalls all the rest. This is exactly what bit super at stage E (3 sequential bs_html runs in one bash loop, ~10 minutes blocked).

**Required pattern (preferred):** use the Claude Code Task tool to spawn N isolated subagents. Each Task receives ONLY the parent inputs + its own diverger value; each Task commits its own result via `/__workflow/node/<id>/commit`.

**Required pattern (fallback if Task is unavailable):** background the curl calls (`curl … &`) and `wait`. Never block.

The validator records the caller's Claude session_id on every `/commit` call. If sibling N+1 of a cold-isolated group commits from the **same session_id** as sibling N, the server returns 409. That's the structural enforcement.

---

## Rule 4 — Cold isolation between siblings (Principle 5)

When `fanOut.isolation: "cold"`, each sibling subagent receives ONLY:

- The shared parent inputs (`inputs.*` other than the diverger)
- Its own diverger value (e.g. `inputs.variants[i]` or this sibling's `spec.genre`)

It does NOT see:

- Other siblings' outputs (in-progress or finished)
- Other siblings' chat transcripts
- Your context (the parent's session)

This is the whole point. If siblings see each other, they homogenize — the model is trained to produce coherent continuations. We want divergence, not coherence. Cold isolation is structural divergence.

---

## Rule 5 — Folder, not list (Principles 2, 6)

Every producer kind declares an `outputsRoot` path. Drop **everything you produce** into that folder. The consumer enumerates the folder and routes files per its `consumeFrom` rules.

**You do not need to enumerate files in advance.** If your work organically produces a new module (a `net.js` for a WebGL viz, a `motion.json` for an animation spec), drop it in `outputsRoot/` alongside `index.html` and the consumer routes it.

**Consequence:** chat refinements flow through automatically. If the user asks you to add a new WebGL coordination graph to a variant you've already produced, write the new file into the variant's outputsRoot. The next time the design-system consumer runs, it sees the new file and routes it (or the validator surfaces "unhandled file" as drift, prompting the user to extend the contract).

---

## Rule 6 — Atomic commit (Principle 10)

All output landing MUST go through:

```
POST /__workflow/node/<id>/commit?project=<id>
Content-Type: application/json

{
  "outputs":   {...},                          # per the kind's outputs schema
  "files": [                                   # files to stage + atomically place
    { "relPath": "index.html",     "content": "<!DOCTYPE html>..." },
    { "relPath": "assets/net.js",  "content": "// ..." },
    { "relPath": "assets/img.png", "contentBase64": "iVBOR..." }
  ],
  "runStatus": "done",                         # or "running" / "error"
  "runError":  "...",                          # required if runStatus=error

  // ONLY for kinds with extendsGraph: true
  "addNodes":  [{...}, ...],
  "addEdges":  [{...}, ...]
}
```

The server:

1. Validates against the kind's contract (must-consume strict for consumers).
2. Stages files atomically: writes to `outputsRoot_staging/`, validates non-empty, then renames to `outputsRoot/`.
3. Updates workflow.json (outputs + runStatus + optional addNodes/addEdges).
4. Fires SSE `asset-changed` events. Canvas cards refresh themselves.

**Forbidden:** writing files directly to `outputsRoot/` from your shell, then PATCHing `runStatus` in a separate request. Partial state is the root of every truthfulness lie observed today (super's `bs_ds_a/b/c queued despite HTML on disk`, `bp_ds_gen queued despite DS built`, empty `page_1.html` with `bs_html_1 queued`). The commit endpoint makes these failures structurally impossible.

---

## Rule 7 — Status never lies (Principle 8)

A node may be marked `runStatus: "done"` only when the kind's `completion.requires` list is satisfied. The validator enforces this on every `/commit` and `/status` call.

If a write fails, set `runStatus: "error"` with a non-empty `runError`. Don't silently leave it in `running` and exit. Don't mark `done` because you "tried." The reconciler detects lying status and surfaces drift — but the cleaner path is to never lie in the first place.

---

## Rule 8 — Pause where the contract says (Principle 12)

Before advancing past a stage with `pauseAfter: True` in the STAGES dict, you MUST emit a status comment naming the artifact produced and wait for an explicit user signal (a chat message, a `<decision-request>` resolution, or a project event recording confirmation).

Today's `pauseAfter` stages: **D (Generate DS)** and **G (Refine PRD with picked alts)**. Stages C and F have inherent pause points (decision checkpoints `cp_ds_pick` and `cp_remix_pick`). All other stages run through.

Don't roll through stage D into stage E (chunking + page dispatch) without checking with the user — they often want to refine the DS in chat between D and E, and your auto-progression discards that opportunity. This is what bit super.

---

## Rule 9 — Detours are first-class (Principles 6, 9)

When a chat run on an existing node produces files or modules beyond the scaffold:

1. **Place new files in an existing producer's outputsRoot** when possible — the consumer routes them automatically per its `consumeFrom` rules.
2. **Use `/commit` with `addNodes`** (only for `extendsGraph: true` kinds — visual-orchestrator, prototype, ds-brainstorm with image-pipeline scaffolding) to add a new node representing the extension.
3. **The user can make N variants** — `_ds_brainstorm/d/`, `/e/`, `/f/` — without the scaffold needing to be edited. The reconciler auto-promotes any new variant folder to a card silently.

Files created outside both paths are surfaced by the reconciler as orphan artifacts. The producing node's runStatus does not flip to done until the orphan is resolved (either incorporated into a node or moved/deleted).

---

## Rule 10 — Visual-orchestrator runs per variant (Principle 9 + super case)

When a `ds-brainstorm` subagent finishes writing its variant folder, it dispatches the visual-orchestrator via the Task tool, **SCOPED TO THIS VARIANT'S `outputsRoot` ONLY**. The orchestrator returns image-pipeline trios (prompt + skill + rembg + asset nodes); commit them via `/commit` with `parentVariant: <this-id>` so the canvas renders them visually grouped under this variant's card.

**Forbidden:** running the visual-orchestrator across all variants' folders at once. That's what produced super's "17 mystery nodes appear in one blob" surprise (orchestrator scanned abandoned variants a/b/c plus picked variant d together). Each variant gets its own legible plan; user compares side by side; picks one direction with full visibility.

---

## Quick reference — common dispatch shapes

```
Single complex artifact      →  agent (single-subprocess), visible session
Multiple variants            →  task-subagents, cold, siblings-parallel
Small text op                →  skill·llm (inline-server-call), one-shot
2-agent conversation         →  iterator-refiner (client-iterator)
N inputs → 1 output          →  iterator-blend (single-subprocess)
```

If you find yourself reaching for `inline-server-call` to produce something complex, you've made a mistake — fix the contract, don't ship a workaround.

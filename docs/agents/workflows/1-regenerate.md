# Workflow 1 — Parse source → regenerate editor data

**Triggers:** "process the prototype", "update the canvas", "regenerate frames", new prototype dropped in, or any `<NAME>_REQUEST.md` file at repo root.

## Architecture: thin router + lens subagents + active merge

The planner is a **file router and a merger** — not an enumerator. Each subagent owns its lens fully, including deciding what's in scope from its perspective. Reconciliation is where binding decisions happen, because that's where context is maximal.

The smartest reasoning happens **inside subagents** (fresh session, focused on one lens, full token budget). The planner does the cheap work (route files, merge fragments). Reconciliation does the active comparison between lens outputs.

**Read [`../planner.md`](../planner.md)** — that's the orchestrator's playbook.

## Subagent index

| # | Subagent | Lens | Playbook | Spawned |
|---|---|---|---|---|
| 1 | Source | Build / update `source/` | [`../subagents/1-source.md`](../subagents/1-source.md) | Only when user says "build" / "rebuild" / source missing. Runs alone, first. |
| 2 | Canvas | Visual workspace cards | [`../subagents/2-canvas.md`](../subagents/2-canvas.md) | Always (parallel batch) |
| 3 | Prototype | Iframe loadability | [`../subagents/3-prototype.md`](../subagents/3-prototype.md) | Always |
| 4 | User flow | Task progression + lanes | [`../subagents/4-user-flow.md`](../subagents/4-user-flow.md) | Always |
| 5 | IA | Sitemap nesting + entity rendering | [`../subagents/5-ia.md`](../subagents/5-ia.md) | Always |
| 6 | Design system | Tokens + primitives | [`../subagents/6-design-system.md`](../subagents/6-design-system.md) | Always |
| 7 | Entities | Data shapes | [`../subagents/7-entities.md`](../subagents/7-entities.md) | Always |
| 8 | State machine | Entity lifecycle FSMs | [`../subagents/8-state-machine.md`](../subagents/8-state-machine.md) | Always — gate evaluated by subagent itself |
| 9 | Timeline | Time-driven changes | [`../subagents/9-timeline.md`](../subagents/9-timeline.md) | Always — gate evaluated by subagent itself |
| 10 | Grids | 2D variance maps (form/entity × use-case) | [`../subagents/10-grids.md`](../subagents/10-grids.md) | Always — gate evaluated by subagent itself |

## Architecture diagram

```
1 Source                                                  (optional, runs alone first)
       │
       ▼
[ Planner — just hands files, no enumeration ]
       │
       ▼  envelope: { slug, sourceRoot, intent, overrides }
       ▼
═══════ PARALLEL DISPATCH (all 9 view subagents) ══════════════
   2 Canvas    3 Prototype    4 User flow
   5 IA        6 DS           7 Entities
   8 State machine    9 Timeline    10 Grids
   (each in fresh session, reads source for its lens,
    enumerates what its lens sees, applies its own gates if any,
    self-audits, returns lens-specific JSON)
═══════════════════════════════════════════════════════════════
       │ (all 9 return JSON fragments)
       ▼
[ Planner — ACTIVE MERGE ]
       │  • 4a: merge frame inventory by ID
       │       — same ID across subagents → unify fields
       │       — convention-mismatched IDs → renormalise
       │       — disagreements (e.g. Canvas missing what Flow has) → resolve by kind matrix
       │  • 4b: merge lanes (Flow canonical, IA evidence cross-checked)
       │  • 4c: cross-actor handoff arrows (from entities × frames × lanes)
       │  • 4d: setupScript ↔ arrow consistency check
       │  • 4e: cross-validate all IDs
       │  • 4f: render check (post-write)
       │  • 4g: anomaly flags (storyboard leak, all-null setupScripts, wild count mismatches)
       ▼
[ Planner — write editor/data.js + prototype.json ]
       │     per docs/agents/data-schema.md
       ▼
[ Render check + report ]
```

## Why this shape

**The planner doesn't scope.** It hands every subagent the same envelope: `slug`, `sourceRoot`, `intent`, optional overrides. There is no canonical inventory, no extracted lanes, no "shared plan" of pre-decisions. The smart thinking lives in the subagent that has the lens-specific context to do it.

**Each subagent owns enumeration through its lens.** Flow decides what's a flow node *through the flow lens*. Canvas decides what's a canvas card *through the canvas lens*. They may legitimately disagree — Flow includes triggers/notifications/externals; Canvas excludes them. That's the architecture working correctly.

**Reconciliation is active merging, not anomaly cleanup.** When subagents disagree about what frames exist, the planner has every output in front of it and decides what to do. When IA's grep finds entities Subagent 5 missed, reconciliation respawns 5 with the conflict. When two subagents converge on different IDs for the same conceptual frame, reconciliation picks the convention-compliant one and propagates.

**Conventions, not pre-decisions.** Subagent enumerations converge because they follow the same naming convention (`docs/agents/conventions.md`) — not because a planner pre-decided IDs. This is what lets enumeration stay in subagents while output stays merge-able.

## Universal rules — in `conventions.md`

Every subagent reads `../conventions.md` before starting. It carries:

- U1. Read source, don't infer.
- U2. Read `editor/serve.py` if runtime helpers matter (`__pokeBy` is server-injected).
- U3. Project-root-relative paths.
- U4. Don't fabricate (lanes from filename, entities from labels, primitives from imagination).
- U5. Kind → view matrix.
- U6. `kind` vs `parent` are independent signals.
- U7. Self-audit with evidence.

Plus naming conventions: frame IDs (kebab-case, filename-prefix, no dots), lane IDs (persona slugs), entity IDs (singular PascalCase of `DEMO.<key>`).

Plus the **storyboard exclusion lens reasoning** — explained as a lens-level decision each subagent makes through their own interpretation, NOT as a planner-handed flag.

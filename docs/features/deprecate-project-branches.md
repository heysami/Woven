# Deprecate project-level branches

Follow-up to the asset-versioning rewrite ([asset-versioning.md](asset-versioning.md)). The branch feature is being removed: one project = one source tree. The "explore alternatives without losing the current line" need is now served by **per-asset branching** on the workflow canvas (sibling asset nodes, ~~not whole-source forks~~).

## 1. Goals

- One project owns one `source/` tree. No `source/<slug>/` nesting.
- Remove `editor/branches/` directory and the `EDITOR_BRANCHES` registry.
- Remove Workflows 4 (fork) and 5 (merge), their trigger files (`FORK_REQUEST.md`, `MERGES.md`), and the per-frame promote endpoint.
- Remove the diff-badge UI (Δ main) — no second tree to diff against.
- Existing multi-branch projects migrate by picking a surviving branch; the others archive.

## 2. Out of scope

- Renaming the existing asset-versioning "branch" affordance — it stays. (Sibling asset nodes ARE the new branching primitive.)
- Touching `design-systems/<id>/`. DS library nodes remain referenced by id; the per-branch `meta.dsRef` becomes a per-project `meta.dsRef`.
- Replacing the chat-history-per-branch JSONL with a versioned ledger. Chat history flattens to a single project-level `editor/chat.jsonl`; archiving prior branch chats is left to a one-shot migration script.

## 3. Surface map (from explore agent)

Roughly broken into five concentric rings:

| Ring | Files | Notes |
|---|---|---|
| **A — Path templates** | `editor/kinds/registry.py` 40+ entries with `{branch}` | Mechanical replace `source/{branch}/` → `source/`. |
| **B — Daemon endpoints** | `editor/serve.py` `_branch_create`, `_branch_promote`, `_frame_promote`, `_compose_initial_prompt`/`_default_run_title` branch params, chat JSONL per-branch | Delete the three endpoints; simplify agent-dispatch helpers to drop the `branch` param. |
| **C — Editor UI** | `editor/app.js` `EDITOR_BRANCHES`, branch dropdown, `IS_MAIN_BRANCH` diff gates, `?branch=` URL param, `frameDiffsMain`/`primVariantDiffsMain`/`entityDiffsMain` | Largest surgery. Diff badge logic deletes outright; branch fallback chains collapse to `"main"` literal or just drop. |
| **D — Bootstrap** | `editor/serve.py` `_write_registry()` generating `editor/data.js` with dual-load script | Rewrite to emit a single `data.js` that loads one `EDITOR_DATA` from a single source. |
| **E — Docs** | `AGENTS.md`, `docs/agents/planner.md`, `docs/agents/data-schema.md`, `docs/agents/conventions.md`, all subagent playbooks (1-source through 10-grids), workflows 0/4/5/6, the visual-policy + media subagents | Remove `branchSlug` from envelopes; delete workflow 4 + 5 playbooks; rewrite `source/<branch>/` references everywhere. |

## 4. Phased execution (decisions locked in — no migration needed; no live projects)

| Phase | Scope | Risk |
|---|---|---|
| **7.A** | Registry path templates: strip `{branch}` from all `outputsRoot`/`completion` entries in `editor/kinds/registry.py`. | Low — mechanical. |
| ~~7.B~~ | ~~Migration tool~~ — **SKIPPED**: confirmed no live multi-branch projects to migrate. | — |
| **7.C** | Daemon: delete `/__branch`, `/__promote`, `/__promote_frame`. Drop `branch` parameter from agent-dispatch helpers. Collapse chat JSONL to single file. Rewrite `_write_registry()` to single-data-file bootstrap (`editor/data.js` carries `EDITOR_DATA` directly; `editor/branches/` deleted). | Medium |
| **7.D** | Editor: remove branch dropdown, `IS_MAIN_BRANCH` gates, `frameDiffsMain` / `primVariantDiffsMain` / `entityDiffsMain` helpers, `?branch=` URL handling, all `EDITOR_BRANCHES` reads, all `EDITOR_MAIN_DATA` sidecar logic, diff-badge rendering throughout. | High |
| **7.E** | Docs: delete Workflows 4 + 5 outright. Scrub `branchSlug` from subagent envelopes; flatten `source/<branch>/` to `source/` in all references; update `AGENTS.md`, `data-schema.md`, `conventions.md`, `planner.md`, `kinds/README.md`. | Low (high volume) |
| **7.F** | Cleanup: delete `MERGES.md` / `FORK_REQUEST.md` triggers from allow-lists; remove trigger detection from orchestrator. | Low |

## 5. Locked-in decisions

1. **No migration.** Confirmed no live projects exist. The migration tool and `.archive/branches/` archival concept are dropped from scope.
2. **Rename:** `editor/branches/main.js` → `editor/data.js`. `editor/branches/` directory deleted entirely. The old `editor/data.js` (registry-bootstrap script) is replaced with a static `window.EDITOR_DATA = {...}` payload.
3. **Diff-badge UI deleted outright.** `IS_MAIN_BRANCH`, all three `*DiffsMain` helpers, all Δ-main badge rendering. Asset-versioning's lineage chip (Phase 5) is the only "what's changed?" affordance going forward.
4. **Workflows 4 + 5 deleted from repo.** Git history preserves the prior shape if anyone needs it.

## 6. Migration script outline (Phase 7.B)

```python
def migrate_flat(project_root, surviving_branch="main"):
    # 1. Validate: branches/<surviving_branch>.js exists.
    # 2. Move source/<surviving_branch>/* → source/* (overwriting source/ if it
    #    already had loose files; preserve loose files into source/.archive/loose/).
    # 3. Move other source/<slug>/ → .archive/branches/<slug>/source/.
    # 4. Move editor/branches/<slug>.* → .archive/branches/<slug>/editor/.
    # 5. Move editor/branches/<surviving>.js → editor/data.js (replace).
    # 6. Move editor/branches/<surviving>.chat.jsonl → editor/chat.jsonl.
    # 7. Delete editor/branches/ entirely.
    # 8. Rewrite workflow.json:
    #    - drop meta.branch / meta.branchLabel / meta.exploration / meta.sourceRoot / meta.sourceEntry
    #    - rewrite asset.path / asset.paths entries that start with "source/<slug>/" to "source/"
    # 9. Delete MERGES.md and FORK_REQUEST.md (archive into .archive/).
    return {"ok": True, "archived": [...]}
```

Idempotent: re-running on an already-flat project does nothing.

## 7. Anti-goals

- Don't try to preserve cross-branch diffing semantics in a new form. The diff-badge feature dies.
- Don't try to expose `.archive/branches/` in the editor. It's a one-way escape hatch for the migration; users who want to browse it use the filesystem.
- Don't try to add a "soft branch" replacement (project clone). Asset-versioning's sibling-branch already covers the explore-alternatives need.

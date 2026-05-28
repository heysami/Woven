# Workflow 6 — Review DS proposals

**Triggers:** `DS_PROPOSAL.md` at project root.

This workflow is the user-facing decision point in the DS reconciliation loop. Subagent 6 (DS-audit) generates `DS_PROPOSAL.md` when it finds feature-page usage outside the DS vocabulary. This workflow walks each proposal, applies the user's verdict, and routes to the appropriate downstream workflow.

## What it does

For each proposal entry in `DS_PROPOSAL.md`, the user has checked exactly one of three boxes:

| Verdict | Downstream action |
|---|---|
| **Accept** | Add to `Workflow 6b` queue — atomically updates DS trio, bumps version, propagates to referencing branches |
| **Reject** | Edit feature pages to use the closest existing DS variant (substitution recorded in NOTES.md) |
| **Defer** | No DS change, no source change; drift stays visible until next regen re-emits the proposal or user resolves manually |

The workflow validates the file, partitions entries by verdict, and dispatches.

## Inputs

- `DS_PROPOSAL.md` at project root — emitted by Subagent 6 against `design-systems/<dsRef.id>/@<version>`
- Branch context — `editor/branches/<active>.js → meta.dsRef`

## Recipe

### Step 1 — Validate the file

Parse `DS_PROPOSAL.md`. For each proposal entry, confirm:

- Exactly one of `Accept` / `Reject` / `Defer` is checked. Zero or multiple → surface to user; do not proceed on that entry.
- The `dsRef.version` in the file header matches the current `design-systems/<dsRef.id>/meta.json.version`. If not, the DS has changed since audit — surface "audit is stale; re-run Subagent 6 first."
- Every proposal has a "Class signature" or "Token signature" field and a "Closest existing in DS" field. Missing → audit emitted a malformed entry; surface for re-run.

### Step 2 — Partition by verdict

Build three lists:

- `accepted[]` — proposals where Accept is checked. Pass to Workflow 6b.
- `rejected[]` — proposals where Reject is checked. Pass to the edit substitution pass (Step 3).
- `deferred[]` — proposals where Defer is checked. Move to a deferred-log archive (see Step 4).

### Step 3 — Edit substitutions for rejected entries

For each `rejected[]` entry:

1. Identify every usage location listed in the "Used in:" field.
2. For each, replace the drift class signature with the "Closest existing in DS" variant. Example: `<button class="btn-primary icon small">` → `<button class="btn-primary icon">`.
3. Append to `NOTES.md` under a `## YYYY-MM-DD · DS reject — substitutions applied` section:

```markdown
## 2026-05-19 · DS reject — substitutions applied

- `.btn-primary.icon.small` → `.btn-primary.icon` (closest existing: Button.primary-icon)
  - source/main/lxp-apply.html:142
  - source/main/lxp-dashboard.html:87
  - Reason: rejected from DS — dense-row icon button rejected as primary affordance variant
```

Substitution is mechanical text replacement scoped to the usage locations the audit listed. Don't broaden — don't fix "similar usages" the audit didn't flag. The audit's locations are authoritative.

### Step 4 — Move deferred entries

Append `deferred[]` to a `DS_DEFERRED.md` archive at project root (creates if absent). The archive accumulates across audits; next audit run reads it and skips re-emitting proposals already deferred (unless the underlying usage changes).

### Step 5 — Hand `accepted[]` to Workflow 6b

Write a small handoff file `DS_ACCEPTED.json` at project root with the accepted entries verbatim. Workflow 6b picks it up (see [`6b-ds-update.md`](6b-ds-update.md)).

### Step 6 — Clear `DS_PROPOSAL.md`

After all entries are partitioned and dispatched, **delete `DS_PROPOSAL.md`**. The file's lifecycle is per-audit; next audit emits a fresh one if drift still exists. Keeping it around stale would confuse the next reviewer.

## Idempotency & failure recovery

- If Workflow 6b fails mid-update, `DS_ACCEPTED.json` is preserved on disk. Re-running Workflow 6 with no `DS_PROPOSAL.md` is a no-op; re-running 6b consumes the leftover handoff.
- If Step 3 (substitution) fails on a file (e.g. the class signature has shifted since audit), that proposal is moved back to deferred and `NOTES.md` records the failure for human review.
- If Step 1 surfaces a stale audit (version mismatch), do not proceed on any entry. Re-run Subagent 6 first.

## Self-audit

- [ ] Every entry in `DS_PROPOSAL.md` had exactly one verdict checked. Unresolved entries surfaced, not silently skipped.
- [ ] `dsRef.version` matched current DS. Stale audit aborted.
- [ ] Every `rejected[]` entry produced a substitution in the listed usage files AND a NOTES.md log line.
- [ ] `deferred[]` archived to `DS_DEFERRED.md`.
- [ ] `accepted[]` handed off via `DS_ACCEPTED.json`; Workflow 6b spawned.
- [ ] `DS_PROPOSAL.md` deleted after dispatch.

## Don't

- Don't accept and apply DS updates inline in this workflow — that's Workflow 6b's job. Separation of concerns: this workflow is partitioning; 6b is atomic mutation.
- Don't broaden Step 3 substitutions beyond the audit's listed locations.
- Don't leave `DS_PROPOSAL.md` on disk after dispatch.
- Don't proceed when audit is stale; re-audit first.

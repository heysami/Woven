# Workflow 6b — Apply accepted DS proposals

**Triggers:** `DS_ACCEPTED.json` at project root (handed off by Workflow 6).

This workflow atomically applies accepted proposals to the design system: edits the trio, bumps the version, regenerates the runtime mirror, and propagates the new version to all referencing branches.

## What it does

For each accepted proposal:

1. Add the new variant / token to `design-systems/<id>/styles.css` (canonical class rule or token declaration).
2. Add a row to the matching section in `design-systems/<id>/gallery.html` so the variant renders in idle state alongside existing variants.
3. (After all accepted entries are applied) Re-run Workflow 3 to regenerate `design-systems/<id>/DESIGN.md`.
4. Compute new `version` (content hash of `styles.css + gallery.html`); update `meta.json`.
5. Rebuild `editor/design-systems/<id>.js` runtime mirror.
6. Re-stamp `meta.dsRef.version` on every branch that references this DS, and re-mirror their `tokens` / `primitives` / `library` fields from the new DS.

This is the atomic write path. Either all accepted entries land cleanly and the version bumps, or nothing changes and the workflow surfaces a recoverable error.

## Inputs

- `DS_ACCEPTED.json` at project root — list of proposal entries the user accepted. Format:

```json
{
  "audit": {
    "generatedAt": "2026-05-19T14:32:00Z",
    "dsId": "main",
    "dsVersion": "<hash from time of audit>",
    "slug": "main"
  },
  "proposals": [
    {
      "primitive": "Button",
      "variantId": "primary-icon-small",
      "classSignature": ".btn-primary.icon.small",
      "closestExisting": { "primitive": "Button", "variant": "primary-icon" },
      "rationale": "dense-row contexts need a smaller icon button without losing primary affordance",
      "usedIn": [
        { "file": "source/main/lxp-apply.html", "line": 142 },
        { "file": "source/main/lxp-dashboard.html", "line": 87 }
      ]
    }
  ]
}
```

## Recipe

### Step 1 — Validate stale-state guard

Before any write:

- `DS_ACCEPTED.json → audit.dsVersion` must match `design-systems/<dsId>/meta.json.version`. If not, the DS was bumped by a concurrent operation after the audit ran; abort and surface "DS shifted under accepted proposals; re-audit and re-review."
- Every proposal entry's `usedIn` files must still exist and still contain the class signature at the listed line (±5 lines for drift tolerance). If any usage has moved or vanished, mark that proposal as `skipped` in the run report — don't abort the rest.

### Step 2 — Apply edits to `styles.css`

For each proposal in `proposals[]`:

- **New variant** (`classSignature` is a class composition like `.btn-primary.icon.small`):
  - Locate the matching base rule in `design-systems/<id>/styles.css` (`.btn-primary.icon`).
  - Add the new combined rule (`.btn-primary.icon.small`) immediately after the closest-existing rule, with overrides for the size delta.
  - Use tokens (`var(--pad-xs)`, etc.) not raw px / hex. If the proposal rationale implies a new token is needed, defer to Step 3.
- **New token** (`classSignature` is a CSS custom property like `--accent-soft-2`):
  - Add to the appropriate bucket in `:root` (`semantic` if accent-named, etc.).
  - If `:root[data-theme="..."]` variants exist, add the corresponding mode-specific values.

Validate: every new rule references existing tokens; no raw color / size literals introduced (those would be new proposals).

### Step 3 — Apply edits to `gallery.html`

For each proposal:

- Locate the section anchor (`#buttons`, `#cards`, `#modals`, …) matching the primitive.
- Append a `.ds-sample` row (or extend an existing one) rendering the new variant in idle state. Use real product class names — NEVER `.ds-*` prefix on the rendered element.
- If the variant is state-gated (modal open, drawer expanded), render it in idle state inline, not behind any handler.

### Step 4 — Workflow 3 regen

After all accepted entries are written to `styles.css` and `gallery.html`, spawn [`Workflow 3`](3-design-md.md) to regenerate `design-systems/<id>/DESIGN.md` from the new trio.

### Step 5 — Bump `version` and `meta.json`

- Compute new `version` = content hash of `styles.css + gallery.html`.
- Update `design-systems/<id>/meta.json`:
  - `version` → new hash
  - `label` → bump (if previous was `v3`, new is `v4`; if user provided a label in the proposal, use that)
  - `builtFrom` stays unchanged — that records the original spec, not incremental edits. Append an `updates: []` array entry recording this proposal cycle:

```json
{
  "version": "<new hash>",
  "label": "v4",
  "appliedAt": "2026-05-19T14:45:00Z",
  "appliedProposals": ["primary-icon-small", "pill-disabled-state", "..."]
}
```

### Step 6 — Rebuild runtime mirror

Re-enumerate `tokens` / `primitives` / `library` from the updated trio and write `editor/design-systems/<id>.js` (same logic as Workflow 0 Step 6).

### Step 7 — Propagate to referencing branches

For every `editor/data.js` with `meta.dsRef.id === <dsId>`:

- Re-stamp `meta.dsRef.version` to the new hash.
- Re-mirror `tokens` / `primitives` / `library` from the new DS library node.

This is a orchestrator-level field write — same as Step 5 DS mirror in Workflow 1. No view subagent runs.

Branches that pinned an old `dsRef.version` explicitly (via `meta.dsRef.pinned: true` — TBD config) are skipped and flagged in the run report: "branch X is pinned at version Y; not updated."

### Step 8 — Cleanup

- Delete `DS_ACCEPTED.json` after successful completion.
- Append a summary to `NOTES.md` under `## YYYY-MM-DD · DS update applied`:

```markdown
## 2026-05-19 · DS update applied

DS: design-systems/main/ — bumped to version <new hash> (v4)
Applied proposals:
- Button.primary-icon-small (added .small modifier to .btn-primary.icon)
- Pill.disabled (added [data-state="disabled"] variant to .pill)
Branches re-stamped: main, dense-rows-experiment
```

## Atomicity & failure recovery

The workflow is best-effort atomic via staged writes:

1. Compute all edits in memory (Steps 2-3).
2. Write a staging copy: `design-systems/<id>/.staging/{styles.css, gallery.html}`.
3. Validate staging via Workflow 3 dry-run + runtime-mirror dry-build.
4. If valid, atomically rename staging files into place; then run Steps 5-8.
5. If invalid, log the failure and leave `DS_ACCEPTED.json` on disk for retry.

If Step 7 (propagate) fails partway, the DS is already updated but some branches are stale. Re-running the workflow with an empty `DS_ACCEPTED.json` plus a `--re-propagate` flag re-runs only Step 7.

## Self-audit

- [ ] Stale-state guard passed (`audit.dsVersion === meta.json.version` before any write).
- [ ] Every accepted proposal either applied or skipped-and-reported. No silent skips.
- [ ] `styles.css` edits use tokens, never raw literals.
- [ ] `gallery.html` edits use real product class names, never `.ds-*` on rendered elements.
- [ ] Workflow 3 ran and `DESIGN.md` reflects the new variants.
- [ ] `meta.json.version` is the content hash of `styles.css + gallery.html`. `meta.json.updates[]` has a new entry.
- [ ] `editor/design-systems/<id>.js` rebuilt.
- [ ] Every referencing branch has `meta.dsRef.version` re-stamped (or is flagged as pinned).
- [ ] `DS_ACCEPTED.json` deleted on success.
- [ ] `NOTES.md` summary written.

## Don't

- Don't write to `source/` from this workflow. (That's Workflow 6's rejection path, not 6b's job.)
- Don't bump `meta.json.version` until all accepted edits have landed in `styles.css` and `gallery.html`.
- Don't propagate to pinned branches.
- Don't proceed when stale-state guard fails; re-audit first.
- Don't introduce raw color / size / spacing literals — every new value goes through a token.

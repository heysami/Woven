# Subagent 6 — DS audit (lens: feature pages vs design system)

You audit the **active branch's feature pages against the design system** identified by `meta.dsRef`. Your output is a drift report — a list of feature-page class and token usages that are NOT covered by the DS — written to `DS_PROPOSAL.md` at project root for the user to review.

**You do NOT extract primitives. You do NOT write `tokens` / `primitives` / `library` in the branch data file.** Those fields mirror the DS library node and are populated by the planner. You read the DS, you read feature pages, and you diff.

**Read [`../conventions.md`](../conventions.md) before starting** — including the **Enumerate-Decide-Log** pattern. The audit is its purest application: two finite sets, a strict diff, no creative enumeration.

## The structural rule (read this before the recipe)

Auditing is a fundamentally easier task than the old "extract primitives from feature pages" — the DS provides a closed vocabulary, and your job is just `feature-page-uses ∖ DS-vocabulary`. The failure mode here is *being too permissive*: glossing over a feature-page usage as "close enough to Button.primary" when it actually uses `.btn-primary.icon.small` and the DS only has `.btn-primary.icon`. Permissiveness defeats the entire reconciliation loop — the variant never surfaces, the prototype keeps drifting, the user has no decision point.

**Every difference is logged. Closeness to an existing variant is a hint for the proposal entry's "Closest existing" field, not grounds for silent omission.**

## Input (envelope only)

- `slug`, `sourceRoot`, `intent`
- `dsRef` — `{ id, version }` from `editor/data.js → meta.dsRef`

## Output

### Primary output — `DS_PROPOSAL.md` at project root

Appears only when drift exists. Format:

```markdown
# DS proposals — generated <YYYY-MM-DDTHH:MM> against ds-<id>@<version>

Slug: <slug>
DS: design-systems/<id>/ @ <version>
Audited files: <count> HTML, <count> JS

## Summary

<N> proposals queued: <breakdown by primitive>.

## Proposal 1: Button — primary-icon-small variant

**Used in:** source/lxp-apply.html:142, source/lxp-dashboard.html:87
**Class signature:** `.btn-primary.icon.small`
**Closest existing in DS:** `Button.primary-icon` (delta: missing `.small` modifier — 32px → 24px size step)
**Rationale (inferred):** dense-row contexts need a smaller icon button without losing primary affordance.

- [ ] **Accept** — add `.small` size modifier to `.btn-primary.icon` in `design-systems/<id>/styles.css`; add a row to `#buttons` in `gallery.html`; bump DS version.
- [ ] **Reject** — Subagent 1 rewrites the two usages to `Button.primary-icon` (32px) on next regen.
- [ ] **Defer** — log only; no DS change, no source change, drift persists in audit until resolved.

## Proposal 2: <Next…>
```

### Secondary output (returned to planner, NOT written to disk)

```json
{
  "auditedAt": "2026-05-19T14:32:00Z",
  "dsVersion": "<hash>",
  "filesAudited": { "html": 8, "js": 3 },
  "proposalCount": 7,
  "byPrimitive": { "Button": 2, "Pill": 1, "Modal": 0, … },
  "tokenViolations": 3
}
```

This is the audit summary that surfaces in the editor's status bar / library node header.

## You must read

### Files you read

- `design-systems/<dsRef.id>/styles.css` — the DS's canonical class rules + `:root` tokens.
- `design-systems/<dsRef.id>/gallery.html` — the variant matrix.
- `design-systems/<dsRef.id>/meta.json` — to confirm `version` matches `dsRef.version`. If mismatch, surface "DS has drifted from the version this audit targets; re-stamp branch first".
- `source/*.html`, `*.js`, `*.jsx` — every feature page in the branch.
- `<project>/editor/data.js` — for `meta.dsRef` only.

### Files you do NOT read

- Any other branch's `source/`.
- Any other DS folder unless the active DS's `parentRef` points at one (then read the parent recursively to build the full inherited vocabulary).

## Recipe — Enumerate → Diff → Log

### Step 1 — Build the DS vocabulary set

Two grep passes against `design-systems/<dsRef.id>/`:

```bash
# A. Every canonical class declared in DS styles.css
grep -oE '^\.[A-Za-z][A-Za-z0-9_.-]*' design-systems/<id>/styles.css | sort -u > /tmp/ds-vocab-classes.txt

# B. Every variant rendered in DS gallery.html (as a class composition appearing inside .ds-sample blocks)
grep -ohE 'class="[^"]+"' design-systems/<id>/gallery.html | sort -u > /tmp/ds-vocab-variants.txt
```

Union these → the **DS vocabulary set**. Also enumerate `:root` tokens from `styles.css` for token-level audit:

```bash
grep -oE -- '--[A-Za-z][A-Za-z0-9_-]*' design-systems/<id>/styles.css | sort -u > /tmp/ds-tokens.txt
```

If `meta.json.parentRef` is set, recursively union the parent DS's vocabulary into this set (inherited classes are part of the active DS).

### Step 2 — Build the feature-page usage set

Three grep passes against `source/`:

```bash
# C. Every class composition used in feature pages
grep -ohE 'class(?:Name)?="[^"]+"' source/*.html source/*.js 2>/dev/null | sort -u > /tmp/fp-classes.txt

# D. Every CSS custom property referenced in JSX / HTML (var(--foo) or directly)
grep -ohE -- 'var\(\s*--[A-Za-z][A-Za-z0-9_-]*' source/*.html source/*.js source/styles.css 2>/dev/null | sort -u > /tmp/fp-tokens.txt

# E. Every inline hex / rgb / hsl / oklch literal in feature-page styles or inline style attrs (token bypass)
grep -ohE '(#[0-9a-fA-F]{3,8}|rgb\([^)]+\)|hsl\([^)]+\)|oklch\([^)]+\))' source/*.html source/*.js source/styles.css 2>/dev/null | sort -u > /tmp/fp-inline-colors.txt
```

The first two are *usages to check against the DS*. The third is *token bypass evidence* — inline colors mean a feature page is sidestepping the token system entirely.

### Step 3 — Diff per usage

For each entry in the feature-page usage set, decide one of:

| Decision | When | Action |
|---|---|---|
| **covered** | The class composition matches a DS variant exactly. | No action. |
| **drift:new-variant** | The composition uses DS classes but in a combination the gallery doesn't render (`.btn-primary.icon.small` when DS has `.btn-primary.icon`). | Emit proposal entry with closest-existing hint. |
| **drift:unknown-class** | The composition uses a class not declared in DS `styles.css`. | Emit proposal entry; closest-existing field is the most similar DS class by name. |
| **drift:token-bypass** | Inline color / size / spacing literal where a token should be used. | Emit proposal entry; closest-existing is the suggested token. |
| **drift:undeclared-token** | `var(--foo)` reference where `--foo` is not in DS `:root`. | Emit proposal entry. |
| **utility** | Atomic helper (`.mt-2`, `.flex-1`, single-property layout). Not a primitive concern. | No action. Log in audit summary as "N utility usages skipped." |

The audit MUST be exhaustive — every feature-page class composition gets a decision. Silent omission is the bug this playbook prevents.

### Step 4 — Group into proposals

Multiple usages of the same drift signature (`.btn-primary.icon.small` used in five files) become **one proposal** with all five usage locations listed under "Used in:". Don't fragment.

### Step 5 — Compute "closest existing" per proposal

For each drift entry, identify the nearest DS variant by:

1. **Class-overlap distance** — how many class tokens are shared. `.btn-primary.icon.small` vs `Button.primary-icon` shares `.btn-primary, .icon`; delta is `.small`.
2. **Token-substitution proximity** — `oklch(54% 0.16 252)` inline vs `var(--accent)` whose value is `oklch(54% 0.16 252)` is a perfect substitution.

Closest-existing is a *hint* for the user reviewing the proposal — it's how Reject would resolve the drift if chosen.

### Step 6 — Write `DS_PROPOSAL.md`

Format per the template above. One section per proposal, numbered. If zero proposals, **do not write the file** (don't create a misleading empty artifact). Instead report in the secondary output: `proposalCount: 0`.

## Self-audit

- [ ] I read `conventions.md` and the DS vocabulary from `design-systems/<dsRef.id>/`.
- [ ] `dsRef.version` matches `design-systems/<dsRef.id>/meta.json.version`. If not, I surfaced the mismatch.
- [ ] I ran all five greps (A, B, C, D, E) and produced finite candidate lists. (Bash output evidence required.)
- [ ] Every feature-page class composition got one of the six decisions. No silent omissions.
- [ ] Multiple usages of the same drift signature were grouped into one proposal entry, with all usage locations listed.
- [ ] Each proposal has a "Closest existing in DS" field with a real DS variant + a delta description.
- [ ] No `tokens` / `primitives` / `library` writes to the branch data file. (Those mirror the DS library node — the planner does that.)
- [ ] If `proposalCount === 0`, `DS_PROPOSAL.md` was NOT created.
- [ ] If `proposalCount > 0`, `DS_PROPOSAL.md` exists at project root with the full template.

## Common blindspots

- **Permissive auditing.** "Close enough to Button.primary" silently omits the drift. Closeness is a hint for the proposal, not a reason to skip.
- **Treating utility classes as drift.** `.mt-2`, `.flex-1`, `.gap-3` are atomic helpers — not DS concerns. Skip them but log the count.
- **Missing `meta.json.parentRef` inheritance.** If the active DS inherits from a parent, the parent's classes ARE part of the vocabulary. Failing to union them produces false-positive drift.
- **Inline `style="color: #abc"` not caught.** Run grep E (inline color literals) — these bypass tokens and are a primary form of drift.
- **Source-file scope.** The audit covers the active branch's `source/` only. Other branches have their own audits.
- **Grouping miss.** Five files using `.btn-primary.icon.small` should produce ONE proposal with five usage locations, not five identical proposals.
- **Stale audit against an outdated DS.** Always check `dsRef.version === design-systems/<id>/meta.json.version`. If the DS bumped after the branch was last regen'd, the audit may be flagging things the new DS already handles.

## Don't

- Don't write `tokens` / `primitives` / `library` to the branch data file. Those are planner-mirrored from the DS.
- Don't write `DS_PROPOSAL.md` if zero proposals — no empty artifact.
- Don't read other branches' source folders.
- Don't be permissive. Every drift gets a logged proposal.
- Don't propose a variant that already exists in DS — that's a "covered" decision, not a proposal.

# Subagent 9 — Timelines (lens: time-driven changes)

You own the **time-axis lens**. Enumerate time-driven changes in source and decide whether they merit a timeline.

**Read [`../conventions.md`](../conventions.md) before starting** — universal rules.

## Input (envelope only)

- `branchSlug`, `sourceRoot`, `intent`
- `override: true | false` — true if `TIMELINE_REQUEST.md` exists.

## Output

Per [`../data-schema.md`](../data-schema.md): `timelines[]`.

```json
{
  "timelines": [
    {
      "id": "application-timeline",
      "label": "Application review lifecycle",
      "anchor": "Application.submittedAt",
      "events": [
        { "id": "submitted",   "at": "T+0",  "label": "TC submits",         "kind": "user"         },
        { "id": "queue",       "at": "T+1h", "label": "PXP queue receives", "kind": "system"       },
        { "id": "reminder",    "at": "T+5d", "label": "Reminder email",     "kind": "notification" }
      ]
    }
  ]
}
```

If your gate doesn't pass and `override: false` → `{ "timelines": [] }`.
If `override: true` and nothing found → `{ "timelines": [], "note": "..." }`.

## You must read source

### Files you may read

- `source/<slug>/*.html`, `*.js` — scheduled-task definitions, deadline copy, auto-expire logic.

## Gate (you own this)

Spawn output only when:

- Source has at least one **time-driven change** — `setTimeout` / `setInterval` / cron-style scheduled trigger, reminder schedule, auto-expire / auto-archive logic, SLA window, copy that mentions "after N days" / "within X hours", OR
- `override: true`.

Pure user-initiated flows → no time axis. Skip.

## Recipe (Enumerate-Decide-Log per `conventions.md` U8)

### Step 1 — Enumerate candidate time-driven events

Three greps, union the results:

```bash
# A. Code-level scheduling / timeout / cron
grep -nE 'setTimeout|setInterval|cron|schedule|setSchedule' source/<slug>/*.html source/<slug>/*.js 2>/dev/null

# B. Time-relative copy in source
grep -onE '(after|in|within|every)\s+\d+\s*(min(utes?)?|h(ours?|rs?)?|d(ays?)?|w(eeks?|ks?)?|mo(nths?)?|y(ears?|rs?)?)' source/<slug>/*.html source/<slug>/*.js 2>/dev/null

# C. Auto-* logic and deadline / expire / SLA keywords
grep -nE 'auto-?(expire|archive|cancel|complete|approve|reject|close)|deadline|expir|SLA|reminder|due-?date' source/<slug>/*.html source/<slug>/*.js 2>/dev/null
```

Union → candidate events. Each independent anchor field (e.g. `Application.submittedAt`, `Class.startsAt`) groups its candidates into one timeline.

### Step 2 — Decide per candidate

Each candidate gets one of:

- **keep** → maps to a `timelines[*].events[*]` entry under the appropriate anchor's timeline
- **drop:illustrative** → copy that mentions a duration but isn't enforced by code (a static marketing line "We'll review your application within 5 business days" with no scheduler / deadline check)
- **drop:non-temporal** → the keyword appears but the surrounding code doesn't actually schedule anything (e.g. `schedule` in a class name unrelated to time)
- **drop:duplicate** → same event surfaced by multiple greps (`setTimeout(..., 5 * DAY)` + copy "after 5 days") — collapse to one event

### Step 3 — Emit + decision log

For each kept event:

- Event `at` format: `"T+0"` / `"T+1h"` / `"T+5d"` / `"T+2w"` / `"T-1d"`. Relative to `anchor`.
- Event `kind`: `user` / `system` / `trigger` / `notification`.
- At least 2 events per timeline. Skip single-event unless `override: true`.

Append a decision log to `NOTES.md`:

```markdown
## <date> · Subagent 9 — Timeline candidate decisions

Candidates: <N> (setTimeout/setInterval/cron + time-relative copy + auto-* / deadline / SLA / reminder keywords)

### Kept (M)
- `setTimeout(autoExpire, 14 * DAY)` → application-timeline · T+14d · "Auto-expire" (system)
- copy "PXP receives within 1h" → application-timeline · T+1h · "PXP queue receives" (system)

### Dropped (N - M)
- copy "scheduled review on Mondays" — drop:illustrative (no cron handler in source enforces this)
- `scheduledClasses` (variable name) — drop:non-temporal (data field name, not a schedule)
- `setTimeout(saveDraft, 30000)` — drop:non-temporal (UI debounce, not a flow event)
```

## Render-verify your slice

If you emitted `timelines[]`, load the editor's **Timeline** view and verify:

1. Each timeline renders as a horizontal axis with ordered event markers.
2. Events appear in chronological order based on their `at` values — `T+0` before `T+1h` before `T+5d`.
3. Event labels are readable, not truncated to garbage.
4. Event `kind` (user / system / trigger / notification) is visually distinct (different marker color or shape).
5. The anchor field reference (e.g. `Application.submittedAt`) is visible / makes sense.

If events render out of order, labels are missing, or the axis is empty, **fix it before reporting done**. Screenshot required if `timelines[]` is non-empty.

## Self-audit

- [ ] I read `conventions.md`.
- [ ] I grepped source for time keywords + deadline copy.
- [ ] Events are backed by source code or explicit copy — not invented.
- [ ] `at` values use the `T+/-Nh/d/w` format.
- [ ] If gate didn't pass and `override: false`, I correctly returned `timelines: []`.
- [ ] Each timeline has at least 2 events (unless override).
- [ ] **Events are unique** — no two events share both `at` and `label`.
- [ ] **Anchor `Entity.field` references an entity that exists in Subagent 7's catalog naming.**
- [ ] **If I emitted `timelines[]`, I rendered the Timeline view in the editor and confirmed events appear in order, labels readable, kinds visually distinct.** (Screenshot required.)
- [ ] **Enumerate-Decide-Log applied.** I ran the three timeline-candidate greps, enumerated the union, decided keep/drop per candidate, and emitted the decision log to `NOTES.md`. No silent omissions.

## Common blindspots

- **Anchor field doesn't exist.** You wrote `anchor: "Application.submittedAt"` but Subagent 7's `Application` entity has no `submittedAt` field. Cross-check.
- **Anchor isn't a timestamp.** `anchor: "Application.status"` is wrong — status is an enum, not a moment. Anchor should be `"<Entity>.<dateField>"`.
- **Events extracted from illustrative copy.** "We'll review within 5 business days" in a static marketing-style paragraph is not a real time-driven event unless source actually schedules / enforces it.
- **`at` values not relative to anchor.** You wrote `at: "2024-06-15"` (absolute) when the format is relative (`T+5d`). Use `T+/-` form.
- **Hour vs day mix.** `T+1h` and `T+5d` are fine to coexist, but `T+0.04d` is wrong — convert to `T+1h`.
- **Single-event timeline.** If only one event exists, it's a deadline copy line, not a timeline. Skip unless `override: true`.
- **Multiple anchors in one timeline.** A timeline has one anchor. If you find events anchored to two different moments (`submittedAt` and `approvedAt`), emit two `timelines[]` entries.

## Don't

- Don't invent timelines from layout patterns. Only time-driven changes.
- Don't write frames / arrows / entities / state machines.
- Don't emit single-event timelines unless override.

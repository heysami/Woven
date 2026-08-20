# User stories + the prototype story map

A project can carry its user stories as an Excel sheet, and a map saying where
each story lives in the built prototype. Both are plain files under the project
root, both are editable by a person and by an agent, and either one can be
re-checked against the other and against the build.

| File | What it is | Who writes it |
|---|---|---|
| `docs/user-stories.xlsx` | The stories, keyed by ID | A person, in Excel. Or `Template` seeds it. |
| `docs/story-map.json` | Story ID to screen / page / element / how to reach it | A wired agent, or a person typing in the node |

The point of the pair is the gap between them. A sheet alone tells you what was
asked for; a build alone tells you what exists. Only the map says which screen
answers which story, and only re-checking it tells you that the answer moved.

## The sheet

Any column layout is read. Headers are matched against an alias table
(`_ALIASES` in [editor/stories.py](../../editor/stories.py)) and normalised
into canonical fields:

| Field | Header names it answers to |
|---|---|
| `id` | ID, Ref, Reference, Key, Ticket, Jira, Story key |
| `epic` | Epic, Feature, Module, Area, Theme, Category |
| `title` | Title, User story, Story, Summary, Name, Description |
| `role` | As a, As an, Role, Persona, Actor, User type |
| `want` | I want, Want, Action, Need, Requirement |
| `benefit` | So that, Benefit, Value, Outcome, Why |
| `acceptance` | Acceptance criteria, AC, Criteria, Definition of done |
| `priority` | Priority, Prio, MoSCoW, Severity, Importance |
| `status` | Status, State, Progress, Stage |
| `notes` | Notes, Note, Comment, Remarks, Details |

Header detection scans the first ten rows and picks the best match, so a sheet
with a title block or an export banner above the real header still parses.
Columns it does not recognise are kept and reported as `extraColumns`; they are
never dropped. Sheets are searched for one named like stories / requirements /
backlog first, then the first sheet that yields rows.

**The ID column is the load-bearing one.** Mappings key off it, so a sheet with
no IDs gets generated ones (`US-001`, `US-002`) plus a `no-id-column` finding,
and those generated IDs shift the moment somebody reorders rows. Add a real ID
column before mapping anything.

Reading and writing .xlsx is done by [editor/xlsx_io.py](../../editor/xlsx_io.py),
which is stdlib only (an .xlsx is a zip of XML). Woven installs from a release
zip with no pip step, so openpyxl is not available on a fresh machine; this is
why there is a hand-rolled reader rather than a dependency. Cells come back as
text, written cells go out as inline strings, and the round trip is verified
against openpyxl in both directions.

## The map

`docs/story-map.json`:

```json
{
  "version": 1,
  "prototype": "main",
  "updatedAt": "2026-08-20T14:48:00",
  "rows": [
    {
      "id": "US-001",
      "screen": "Login",
      "page": "login.html",
      "selector": "#login-form .btn-primary",
      "reach": "Home > click Sign in > Login",
      "note": "",
      "confidence": "high",
      "source": "agent",
      "storyHash": "ecd6790c681c245e",
      "checkedAt": ""
    }
  ]
}
```

`page` is relative to `source/<prototype>/`. `selector` is a CSS selector, or
literal visible text in quotes (`"Pay now"`) when the markup has no stable hook.
`reach` is the interaction path in the user's language, steps separated by `>`;
it is the field the whole map exists for.

`storyHash` is a fingerprint of the story's meaning-bearing fields (title, role,
want, benefit, acceptance) taken when the mapping was recorded. Status and notes
are deliberately excluded, so moving a story to "done" does not mark its mapping
stale.

## Re-checking

`POST /__stories/validate` cross-checks sheet against map against build. It is
mechanical: it answers "does this mapping still resolve", never "does this
element satisfy this story". The judgement half is the
[requirement-QA agent](../agents/requirement-qa.md)'s job, and it reads this
output as its checklist.

| Finding | Severity | Means |
|---|---|---|
| `duplicate-id` | high | The sheet uses one ID twice, so a mapping is ambiguous |
| `blank-id` | high | A story row has no ID |
| `orphan-mapping` | high | A map row points at an ID the sheet no longer has |
| `missing-page` | high | The mapped page is not in `source/<prototype>/` |
| `missing-element` | high | The mapped selector's id / class / attribute / tag is not on that page |
| `stale` | medium | The story text changed since the mapping was recorded |
| `unmapped` | medium | A story with no location |
| `no-id-column` | medium | IDs were generated from row order |
| `no-reach` | low | A mapping with no interaction path |

`missing-element` is a textual check, not a real selector match: it asks whether
the page still contains the id, class, attribute or tag the mapping names. A
selector whose every token is present passes even if the nesting changed. That
false negative is deliberate, because the alternative is a false alarm on every
DOM reshuffle. It also means a deep descendant chain reads as broken the moment
anything moves, so prefer an id or a `data-testid`.

## The canvas node

Kind `story-map`. Dragged from the workflow library's Others section, or the
command palette. It is a table of the joined rows, one per story.

Story columns are read-only: the sheet owns them, and a story edited on the
canvas would be silently overwritten on the next import. Location columns are
inputs, and editing one stamps that row `source: manual`, which the mapping
agent is told to preserve. An edit also clears that row's `storyHash` so the
daemon re-stamps it, since the person just looked at the story and the location
together.

Every edit posts the whole table back, same full-replace contract as
`/__workflow`. This is why the client round-trips `storyHash` verbatim: a row
that came back blank would be re-stamped by the daemon, clearing the stale flag
on rows nobody touched.

Ports:

- `edit` (in) - wire an agent here to fill or refresh the locations. It receives
  the schema and the production rules from `_STORY_MAP_AUTHORING` in
  [editor/kinds/registry.py](../../editor/kinds/registry.py), including the rule
  that a story it cannot locate gets no row. Leaving a story unmapped is the
  correct visible outcome; a fabricated location destroys the only thing the
  file is for.
- `out` - the map as context for anything downstream, resolved from
  `bakedPath: docs/story-map.json`.

## Design-system validate

The design-system node has the same shape of re-run, on its own axis. `Validate`
runs [editor/tools/qa/ds_lint.py](../../editor/tools/qa/ds_lint.py) over the
built pages via `POST /__ds/validate` and lists where the prototype forked away
from the bound DS: component classes a page redefines in its own `<style>`,
tokens that do not exist in the DS, hardcoded values that duplicate a token, and
one class forked across sibling pages with different bodies. Read-only, and
`status: no-ds` (no design system bound) is reported as not-applicable rather
than as a failure.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/__stories` | Joined rows + validation + the page list for the Page column |
| GET | `/__stories/download` | The .xlsx itself, for editing in Excel |
| POST | `/__stories/upload` | Raw .xlsx body. Parsed into a temp file before it replaces the live sheet, so a wrong-format drop cannot destroy existing stories |
| POST | `/__stories/template` | Write the canonical sheet with three example rows (`{force:true}` to overwrite) |
| POST | `/__stories/map` | Replace the map (`{prototype, rows}`) |
| POST | `/__stories/validate` | Re-check |
| POST | `/__ds/validate` | Design-system drift check |

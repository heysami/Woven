# Plan First

Drop this into a system prompt, `CLAUDE.md`, `AGENTS.md`, a custom plan mode, or paste it at the top of a request. It works with any agent harness: nothing here depends on a specific app, tool, or file layout.

---

## PLAN FIRST - mandatory gate

Before you BUILD anything asked for, your reply is a PLAN and nothing else. Do not write a file, run a mutating command, or dispatch a sub-agent until the user has answered the gate at the end of the plan. Reading to understand the request first is expected; changing things is not.

### Hard format rules

Every section, no exceptions:

- ONE SENTENCE per point. A point that needs a second sentence becomes a second bullet instead.
- At most 4 bullets ELABORATING ANY ONE POINT.
- NO paragraphs anywhere in the plan.

THE 4 CAP IS ABOUT BREVITY, NEVER ABOUT COVERAGE. It limits how much you may say about one thing; it does NOT limit how many things the plan covers. Table rows are NOT capped: if the user asked for nine changes, the logic table has nine rows. Dropping a request to fit a number is the worst thing this plan can do - it looks complete and silently loses work.

### First, enumerate the request

Before you plan or read any file, list every DISCRETE thing the user asked for, in their order, in their words. A request written as prose or as a bulleted list of screens usually holds 5-15 of these; treat each bullet, each "and also", each clause naming a different field / screen / rule as its own item.

That enumeration is the checklist the finished plan is measured against: EVERY item must appear somewhere in the UI, Logic or Copy sections. If you deliberately leave one out (already built, contradicts another, needs a decision), say so in one line under the plan - never by omission.

### Second, establish what already exists, per item, by looking

For each enumerated item, decide NEW vs UPDATE by OPENING the file that renders it and reading the region it names.

GREP IS FOR LOCATING, NOT FOR CONCLUDING. A term you cannot grep may still be on screen under a different label, built from a variable, rendered by a shared component, or spelled differently in markup than in the user's words - "no grep hit" is NOT evidence that something is absent. Never decide NEW from a failed search. If after reading you still cannot tell, say "could not confirm" for that item rather than guessing; a wrong NEW silently rebuilds something that exists.

### The plan: exactly these four sections, in this order

**1. UI** - how the request becomes screen. Text only, no images, no code.

- Something NEW: one text wireframe - an ASCII box sketch in a fenced `text` block, naming the regions and the controls inside them, and nothing else.
- An UPDATE to something that exists: a BEFORE wireframe and an AFTER wireframe of the SAME region, so the change reads as a diff. Go look at what is there now before you draw the BEFORE.
- No screen involved at all (pure backend, tooling, data): write `No UI change.` and move on.

**2. Logic** - one markdown table, columns exactly:

`Trigger | What happens | State read or written | Edge case`

**3. Copy** - one markdown table of the text you will WRITE, columns exactly:

`New copy | Component | Dynamic value | Case | Type family`

- `Dynamic value` is the live value that copy interpolates or reacts to, or `-` for static text.
- Fill `Case` and `Type family` ONLY for text that is not the label of an action component: a button, link, tab or menu item takes its case and type from the component it lives in, so write `-` in both columns for those.
- No user-facing text changes: write `No copy change.`

**4. Split** - the work items this plan breaks into, numbered, at most 4, one sentence each, each followed by an `Owns:` line (see Claims below). Each must be buildable on its own by an agent that never sees this plan.

### How to split

SPLIT BY INDEPENDENT CHANGE, NOT BY FILE. Split items are meant to run AT THE SAME TIME, by separate agents. Two changes belong in ONE item only when they are COUPLED, which means one of exactly two things:

- (a) one needs the other's output to exist first (it acts on a field, component or data the other builds), or
- (b) they edit the same REGION of code - the same function, the same markup block, the same CSS rule.

Anything else runs in parallel.

- SHARING A FILE IS NOT COUPLING, as long as the parallel agents edit with targeted replacements (never whole-file rewrites) and are told each other's claimed regions. Several unrelated asks on one screen is the NORMAL case for a split, not an exception to it: never merge them because "they all touch the same file".
- Merge only what truly couples: a label that must read the same in the form and in its validator is ONE change (one item takes both regions); two features that edit the same function are one item; a step that acts on what another item builds goes in that item, after it.
- Group the independent changes into at most 4 items of similar weight. One item is right only when every change couples to the others; then say in one line WHICH coupling, naming the shared function or the dependency - "they share a file" is never that reason.
- Never pad the list, and never split by "phase" (design, then logic, then copy): that is a sequence by definition.

### Claims

Each split item's `Owns:` line lists EVERYTHING that item will write, one claim each:

- `path` for a file no other item touches.
- `path#region` for the item's part of a shared file, where the region names the functions, markup blocks or CSS rules, e.g. `src/form.html#awardDueCard()`, `src/model.js#validators: award date`.

A valid split never has two items claiming the same file whole, one item claiming a file whole while another claims part of it, or two items naming the same region. A missing or vague claim is exactly how one agent ends up overwriting another.

### Split manifest

After the four sections, emit the split as one fenced `json` block so it can be handed straight to parallel agents or a script:

```json
{"items": [{"title": "<short run title, <=60 chars>", "owns": ["<claim>", "..."], "brief": "<the whole self-contained brief for this item>"}]}
```

- One entry per Split item, at most 4, IN ORDER.
- Each `brief` must stand alone: the agent that receives it sees neither this plan nor this conversation, so restate that item's UI rows, logic rows and copy rows inside it, name what it claims, list its siblings' claims so it stays out of them, and say what done looks like.
- If your harness can write files while planning, also save the manifest to `plan-splits/<unique-plan-id>.json`. Never use one fixed shared filename: plans running at the same time overwrite each other's manifest.

### The gate

Then STOP. End the reply with this, and nothing after it:

> **Plan ready - reply "execute" to run each Split item as its own parallel agent, or reply with what to change.**

If your harness has a native plan-approval step (an exit-plan-mode tool, an approval button), submit the plan through it instead of the closing line. If it renders choice buttons, offer exactly ONE, **Execute the plan**: never a "review" or "revise" button, because a click on it only makes you ask what to change, and the user can just type the change.

### After the gate

- On **execute**: if you can launch parallel agents or sessions, start one per manifest item with its `brief` and nothing else, then stay out of their claims. If you cannot, say so in one line and build the items yourself in order, still respecting each item's claims.
- On any other reply: it is a revision. Apply what the user says, rewrite the manifest to match the REVISED plan, then re-emit the WHOLE plan and the gate. Never start building on a partial approval or on silence.
- Once a plan is approved, this gate is SPENT for that request: carry it out, and do NOT re-plan the follow-ups it produces (an answer to the gate, a correction, a "yes go"). A genuinely NEW request re-arms it.
- This gate does NOT re-open a decision already locked elsewhere. If you were handed an already-approved plan to execute, execute it; the planning happened before you got here.

### Skeleton

````markdown
**Request**
1. <item, in the user's words>
2. <item>

**1. UI**
BEFORE - <region>
```text
+----------------------------+
| Header         [Settings]  |
| ...                        |
+----------------------------+
```
AFTER - <region>
```text
+----------------------------+
| Header  [Export] [Settings]|
| ...                        |
+----------------------------+
```

**2. Logic**
| Trigger | What happens | State read or written | Edge case |
|---|---|---|---|

**3. Copy**
| New copy | Component | Dynamic value | Case | Type family |
|---|---|---|---|---|

**4. Split**
1. <one sentence>
   Owns: `src/a.js#exportCsv()`, `src/header.html#toolbar`
2. <one sentence>
   Owns: `src/b.js`

Left out: <item> - <one-line reason> (only if any)

```json
{"items": [...]}
```

> **Plan ready - reply "execute" to run each Split item as its own parallel agent, or reply with what to change.**
````

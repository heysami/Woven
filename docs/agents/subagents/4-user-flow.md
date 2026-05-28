# Subagent 4 — User flow (lens: task progression)

You own the **task-progression lens**. Read source, enumerate what *you* see as a flow node, identify what *you* see as lanes, and draw what *you* see as direct arrows. You are not handed an inventory — you produce one through your lens.

**Read [`../conventions.md`](../conventions.md) before starting.** It carries the universal rules (U1–U7), the frame-ID + lane-ID naming conventions that let your enumeration converge with other subagents', and the storyboard-exclusion lens reasoning.

## Input (envelope only)

- `branchSlug`, `sourceRoot`, `intent`

No inventory. No shared plan. No lanes pre-extracted. You decide what's a node and what's a lane.

## Output

Per [`../data-schema.md`](../data-schema.md). You write `frames[i].kind`, `frames[i].lane`, the lane catalog `lanes[]`, and `arrows[]`:

```json
{
  "frames": [
    { "id": "library",       "label": "Library",         "kind": "page",   "lane": "user" },
    { "id": "library-cmdk",  "label": "Command palette", "kind": "overlay","lane": "user" },
    { "id": "tc-submit",     "label": "TC submit form",  "kind": "form",   "lane": "tc"   },
    { "id": "pxp-queue",     "label": "PXP review queue","kind": "page",   "lane": "pxp"  }
  ],
  "arrows": [
    { "id": "a1", "from": "library", "to": "library-cmdk", "action": "Press ⌘K" }
  ],
  "lanes": [
    { "id": "user", "label": "User", "kind": "user" },
    { "id": "tc",   "label": "Training Coordinator", "kind": "user" },
    { "id": "pxp",  "label": "Programme Experience Partner", "kind": "user" }
  ]
}
```

Include `label` on every frame — other subagents reuse it via reconciliation.

## You must read source

### Files you may read

- `source/<slug>/*.html` — page bodies, persona switchers, `<a href>` arrows, useState declarations
- `source/<slug>/*.js` — onClick handlers, location.href navigation, state machinery
- `source/<slug>/data.js` — `window.DEMO` shape (for cross-checking entity-driven flows)
- Any storyboard document (`index.html` titled Overview/Workflows, `STORYBOARD.md`, `PERSONAS.md`) — as **input**, never as data; see U-rules / storyboard lens decision
- Existing `source/<slug>/prototype.json` — preserve `kind` / `lane` for unchanged frames (your prior enumeration)
- `editor/serve.py` — only if you need to understand server-injected helpers (`__pokeBy`)

## Enumerate through your lens

A flow node is anything the user dwells on as part of task progression. Specifically:

1. **Top-level pages** (one per source HTML file, OR one per hash route if SPA)
2. **useState branches that produce a distinct dwelling state** — `if (submitted) return html\`...\`` → a node; toast/spinner → NOT
3. **Modals / sheets / popovers that the user dwells inside** — `${modalOpen ? html\`...\` : null}` → a node
4. **System events that gate progression** — cron triggers, scheduled jobs, webhook handlers → kind `trigger`
5. **System-to-user messages** that prompt re-entry — push, email, toast notifications → kind `notification`
6. **Out-of-prototype surfaces** referenced in flow but not built in source → kind `external`
7. **Decision points** the system makes (validation, eligibility) → kind `decision`

Storyboard files are not flow nodes — they're metadata describing the workflow. Read them for personas + workflow pairings, but don't include them in your `frames[]`. See `conventions.md` → "Storyboard exclusion" for the lens reasoning.

**Demo dock is scaffolding too.** `<div class="demo-dock" data-demo-only="true">` (PROTOTYPE.md §11) is the prototype-only switcher panel — don't enumerate it or its rows as flow frames. The rows map 1:1 to `state` / `substep` variants of the screen, which you already enumerate via useState detection.

## Identify lanes through the persona lens

You own lane identification. Walk this cascade:

1. **Storyboard `personas: [...]` array** — copy verbatim, slug each persona per `conventions.md` lane naming.
2. **Header persona switcher** in source DOM (`<button>View as TC</button>`).
3. **Explicit persona tags** (`<span class="persona-tag">PXP</span>`, `data-persona="..."`).
4. **Persona-named folders** under `source/<slug>/` (`tc/`, `pxp/`).
5. **Nothing found** → emit a single default `[{ id: "user", label: "User", kind: "user" }]`. Don't fabricate from filename prefixes.

If you find 2+ lanes via the storyboard or DOM evidence, **use them**. Don't collapse to one because "most frames look similar." The reconciliation step compares your lane output against IA's persona evidence — silent collapse will be caught.

## Kind audit per frame

For each enumerated frame, walk the kind audit (first match wins):

1. **Form? — and a leaf?** Multi-input fill-in (>~3 inputs + submit) **with no child frames** (no state/overlay/substep descendants) → `kind: "form"`.
   - **⚠️ Form-with-children rule (editor coupling).** The Prototype view's left-nav filters top-level entries on `kind === "page"`; any `kind: "form"` frame with child frames gets dropped to "Other screens" and its children get orphaned alongside. If the form has *any* child frame (even one `submitted` state), use `kind: "page"` instead — you keep the Form-ness conceptually but the editor doesn't orphan it. Reserve `kind: "form"` strictly for leaf forms with no descendants.
2. **Substep?** Section under a parent (form section, stepper stage, significant tab) → `kind: "substep"`.
3. **System decision?** Branch chosen by validation / eligibility / role-check / feature flag → `kind: "decision"`. Outgoing arrows: "Yes"/"No", "Approved"/"Rejected".
4. **Single-input gate?** → `kind: "input"`.
5. **System-triggered?** Cron / webhook / timer / queue-consumer → `kind: "trigger"`.
6. **System-to-user message at a cross-actor handoff?** Push / email / toast / "Notify X" copy → `kind: "notification"`. Place this in the *receiver's* lane (the actor being notified is the one for whom this is a flow entry). See "Cross-actor handoff via notification" above. The handoff should always read as `sender → notification → receiver`, never as a direct cross-actor jump.
7. **Context-only?** Real surface outside this source → `kind: "external"`.
8. **Modal / sheet / popover scrim?** → `kind: "overlay"`.
9. **useState branch sibling under a page?** → `kind: "state"`.
10. **Default `page`** only if none of 1–9 fit.

**Audit your mix.** 80% `page` + 0 `decision` + 0 `form` + 0 `trigger` means you missed something. Real systems have a mix.

`kind: "start"` is a cycle-breaker only — for wizard `step1 ↔ step2 ↔ step3` cycles where step1 needs to be root. Don't sprinkle on tab-bar landings.

## Direct arrows

For each pair of enumerated frames `A → B`, include in `arrows[]` if it's:

- **Sequential** — user clicks something on A and source navigates to B. Action quotes the click ("Click Submit").
- **Tab / substep switch under same parent** — clicking a tab on a page that swaps content within the same shell IS task progression. Emit `parent → tab` for each tab the user can switch to. Don't drop these because they're "nav-driven" — they're sequential.
- **Dashboard / list → specific item / form** — clicking a task tile, a queue row, a list card, or a "Start application" tile that opens a specific item/form IS task progression. Emit it even though the dashboard is in the global nav.
- **External page link** — `<a href>` pointing at a page that doesn't exist in `source/<slug>/`. Don't silently drop it; instead emit a `kind: "external"` frame for the destination (with that filename as the label) and arrow into it.

Exclude only if it's:

- **Hub-and-spoke nav re-entry** — clicking the global "Home" link from a deep page back to the home page, or the sidebar/topbar logo link back to the landing. The destination is reachable from EVERY page via the same control. Drop these. (A nav link that goes somewhere specific from one particular page is NOT hub-and-spoke — keep it.)
- **"Done" / "Back to" / "Cancel and return" verbs** — explicit reverse navigation after a workflow ends.
- **Transactional reversal** — arrow from `submitted` / `cancelled` / `approved` back to the pre-commit form, even if `location.href` goes there.
- **Cross-actor handoff** — these are reconciliation's job, not yours. You only emit direct user-action arrows. (See "Cross-actor handoff via notification" below — you DO emit the `notification` mediator nodes; reconciliation wires the arrows.)

**The re-entry test, refined.** When in doubt, ask: "Would the user click this control as part of completing their task, or to navigate elsewhere unrelated?" Task-driven → keep. Generic-nav → drop. Tabs and dashboard tiles almost always pass the task-driven test.

## Cross-actor handoff via notification

When the system handoffs a task from one actor to another, source typically emits a notification at the handoff point. The flow shouldn't read as a direct frame-to-frame jump — it should pass through a `kind: "notification"` mediator.

**Emit a `kind: "notification"` frame when:**

- Source has any copy that signals "we'll notify X" / "X is notified" / "Notify TC" / "Email sent to..." at a handoff point.
- A configurable notifications page lists named notifications (e.g. `pxp-notification.html` enumerating "Application Submitted", "Run Date Proposed") — each named notification that fires at a handoff earns a `notification` flow node.
- Webhook / push / email-template code at handoff.

**Lane placement.** A notification mediator sits in the **receiver's lane** (the actor who *gets* notified), since the notification is the receiver's entry point into the next step. Frame ID: `<receiver>-notif-<event>` (e.g. `pxp-notif-app-submitted`). Label is the human-readable notification title.

**Reconciliation owns the arrows.** Your job is to emit the notification node + flag it; the planner's Step 4c wires `sender-frame → notification → receiver-frame` as a 2-hop replacement for the direct cross-actor edge. Do NOT draw those arrows yourself.

**Disambiguation — notification settings page vs notification flow event.** A *settings page* where the user toggles which notifications they receive is a regular `kind: "page"` frame (it's a UI surface the user dwells on). A *flow event* representing the moment a notification fires is a `kind: "notification"` frame (Flow-only, not iframeable). They have different IDs (`pxp-notifications` settings page vs `pxp-notif-app-submitted` flow event). Don't conflate.

## Nav-only landing pages

A frame that's reachable ONLY through global navigation (sidebar item, top nav link) and has no inbound flow arrow is **not orphaned** — it's a nav landing. Mark it `kind: "start"` to declare it as a flow entry point.

Common cases:
- Settings, profile, notifications-config pages
- Per-actor dashboards / inboxes that are the actor's landing page
- Help / search / browse hubs

Setting `kind: "start"` tells the Flow view to render them with the start glyph instead of looking abandoned. Don't fabricate an inbound arrow just to make the dashboard appear "connected."

## Render-verify your slice

After producing your output (and after the planner has written `editor/branches/<slug>.js`), load the editor's **Flow** view and verify:

1. Every lane in your `lanes[]` appears as a swimlane gutter with at least one frame in it. An empty lane is a fabrication.
2. Every frame appears in its declared lane — no frame is in "Unknown" or a default lane it doesn't belong to.
3. Every arrow you wrote is visible — sequential, with the right action label.
4. Cross-actor handoff arrows added by reconciliation (not by you) appear correctly between lanes.
5. Kinds render with the right visual treatment — `decision` as diamond, `trigger` / `notification` / `external` with their distinct chips, `form` as form chip, etc.
6. Mix sanity: if your Flow view is 80% white page-rectangles with no decisions / triggers / notifications, you probably missed something. Real systems have a mix.

If a lane is empty, a kind looks wrong, or an arrow is missing/spurious, **fix it before reporting done**. Screenshot required.

## Self-audit (run before returning)

Each item requires **evidence** — a Read / Bash / Grep / screenshot call. Don't tick implicitly.

- [ ] I read `conventions.md` (U-rules + naming conventions).
- [ ] I scanned every `.html` for `useState(`, `<a href>`, persona switchers. (Bash grep required.)
- [ ] I read the storyboard (if one exists) for personas + workflow pairings, and excluded it from `frames[]`.
- [ ] My frame IDs follow the naming convention (kebab-case, filename-prefix, no dots).
- [ ] If 2+ lanes are evident in source, my `lanes[]` reflects that — I did NOT collapse to 1 lane just because most frames look similar.
- [ ] My kind mix is realistic — not 80% `page`. (I have at least one of `decision`, `trigger`, `notification`, `external`, or `form` if source justifies it.)
- [ ] My arrows are only sequential clicks — no re-entry, no transactional reversal, no cross-actor handoff.
- [ ] **I did NOT drop tab-switch arrows** (parent → tab is sequential, not re-entry).
- [ ] **I did NOT drop dashboard / list → task-item arrows** (clicking a task tile / queue row is task-driven, not nav).
- [ ] **For each cross-actor handoff where source emits a notification (push, email, "Notify X" copy, named entry in a notification config page), I emitted a `kind: "notification"` frame in the receiver's lane.** A handoff with no notification mediator reads as a direct cross-actor jump — wrong.
- [ ] **For nav-only landings** (settings, dashboards, profile, help) with no inbound flow arrow, I marked `kind: "start"` so the Flow view doesn't render them as orphans.
- [ ] **For `<a href>` to a page not in `source/<slug>/`**, I emitted a `kind: "external"` destination frame (not just dropped the arrow).
- [ ] **Notification settings page vs notification flow event are not conflated** — the settings page is a regular `kind: "page"`, the flow event is `kind: "notification"`, with distinct IDs.
- [ ] I checked every `kind: "form"` frame for child frames; any form with descendants was promoted to `kind: "page"` (editor coupling rule).
- [ ] **I rendered the Flow view in the editor and confirmed every lane has frames, every kind renders correctly, and the arrow set looks right.** (Screenshot required.)

## Common blindspots

- **Storyboard `personas: [...]` missed because it's in a JS literal, not JSON.** Search both `personas:` AND `personas =` in `.js` files, not just `.json`.
- **One-shot lane collapse.** You found 3 personas in the storyboard but the bulk of source pages aren't persona-tagged — so you collapsed to a single `user` lane. Wrong: emit all 3 lanes; let IA-level evidence assign individual frames.
- **Missing decision nodes for validation gates.** A form has `if (!isEligible(user)) return <ErrorState/>` — that's a `decision` node with two outgoing arrows ("Eligible" / "Not eligible"). Skipping it leaves a logic gap in the flow.
- **All-page kind mix.** If your output has 0 `decision`, 0 `trigger`, 0 `notification`, 0 `external`, 0 `form` — re-audit. A multi-actor system almost always has at least one of each.
- **Arrow direction reversed.** Click on A goes to B → arrow is A→B. Common mistake: writing it as B→A because "B is the result." The arrow follows the user gesture's chronology, not the data flow.
- **Re-entry arrow leaked.** "Back to library" from a settings page → re-entry via nav, NOT a flow arrow. Source's `location.href = "library.html"` is a navigation, not a sequential flow click.
- **Transactional reversal leaked.** "Cancel" or "Discard" buttons that return to the pre-commit form — these aren't sequential flow, they're undo. Exclude.
- **Tab arrows dropped as "re-entry."** Tab switches within the same parent page are sequential task progression. Parent → each tab is a real arrow. A page with 3 tabs should produce 3 arrows out of the parent, not 0.
- **Dashboard / list → task-item arrows dropped.** The dashboard is in the global nav, so the re-entry test fires too eagerly. But a click on a specific task tile / queue row / list card is a task-driven action with a specific destination — keep it.
- **Cross-actor handoff with no notification mediator.** Source has "Notify TC", "Email sent", or a configurable-notification settings page enumerating named events at the handoff point — but you wrote a direct A-lane → B-lane arrow. Insert a `kind: "notification"` node in the receiver's lane between them.
- **Notification settings page collapsed into notification flow events.** They're different things. The settings page is a `kind: "page"` (config UI the user dwells on). Each named notification in it that fires at a handoff is its own `kind: "notification"` flow event with a distinct ID.
- **Per-actor landing dashboard left orphaned.** No inbound arrow because the dashboard is reached from global nav. Mark `kind: "start"` so the Flow view renders it as an entry point, not as a missing connection.
- **Dropped arrow to non-existent source page.** `<a href="lxp-inhouse-applications.html">` but that file doesn't exist in `source/`. Don't silently drop; emit a `kind: "external"` frame for the destination so the gap is visible.

## Don't

- Don't expect a planner-provided inventory or lanes list — there isn't one.
- Don't include the storyboard as a frame.
- Don't write `parent`, `col`, `row`, `entry`, `hash`, `setupScript`, `entities` — those are other lenses.
- Don't draw cross-actor handoff arrows — reconciliation owns those.
- Don't fabricate lanes from filename prefixes alone (U4).

# Live Session - host-authoritative multiplayer over the share tunnel

> Status: **built (v1)** - phases 1-5. Sibling of share mode
> ([share-mode.md](share-mode.md)); reuses its tunnel, gate, registry and SSE
> plumbing and adds presence, per-element leases, authenticated guest writes,
> and the git/GitHub backbone. **Setup:** [live-session-setup.md](live-session-setup.md).
>
> Implementation:
> - `editor/live.py` - sessions, presence, leases, gate routes (`/s/<tok>/live*`), GitHub device-flow/fork/PR
> - `editor/git_ops.py` - connect / commit (with Co-authored-by) / publish / fork / PR / device OAuth
> - `editor/shares.py` - gate delegation (`register_live`)
> - `editor/serve.py` - broadcast bridge, node-finish lease release, `/__live/*` + `/__git/*` host endpoints, callbacks
> - `editor/live/client.{html,css,js}` - the gate-served guest collab client
> - `editor/app.js` - host controls in the Shares tab (Go live / roles / Commit / Publish)
> - Tests: `editor/tests/test_live_core.py`, `test_live_gate_http.py`, `test_git_ops.py`; demo `live_demo_server.py`
>
> Verified end-to-end in a real browser: join → SSE roster → live cursors →
> leases/locks → role enforcement. The §-numbered sections below remain the
> design of record.

Live Session lets a host open ONE prototype/project to invited guests who join
**through a URL in a browser** - no install - and **edit the host's single
project together** in real time: live cursors, live node moves, and per-element
locks so two people never clobber the same thing. There is exactly one source
of truth (the host's tree) and exactly one agent (the host's daemon). A guest
who wants to go solo can **fork a copy**; pull / fork / merge are **delegated to
git + GitHub** (see §7), gated per project.

It is the *collaborative-editing* sibling of share mode. Share mode is
view + comment on a frozen-ish surface; Live Session is co-edit on the living
tree. They share machinery deliberately.

---

## 1. The model in one breath

```
        ┌─────────────────── HOST machine (the only Woven) ───────────────────┐
        │  serve.py daemon  ─────────────  workflow.json + source/<slug>/**     │
        │      │  per-project SSE channel (WorkflowWaiter)  serve.py:3038       │
        │      │  per-project workflow lock                  serve.py:3493      │
        │   GATE (shares.py:618) ── widened: presence + leases + scoped writes  │
        └──────────┬──────────────────────────────────────────────────────────┘
                   │  cloudflared quick tunnel (existing)
        ┌──────────┴───────────┐        ┌───────────────────────┐
   GUEST browser (editor)  GUEST browser (editor)   …  (no install, no files)
   cursor + edits  ───────────────────►  all writes land on the HOST's tree
```

- **Only the host runs Woven.** Guests are browser-only. Files never leave the
  host's disk except as streamed through the host's own tunnel. Close the
  laptop → the session is gone. This preserves local-first; the tunnel is just
  the host briefly exposing their *own* daemon to invited guests.
- **One tree, one agent.** Every guest edit goes URL → tunnel → host daemon →
  host files. Every agent run a guest triggers executes on the **host's
  machine, with the host's API key**. There is no per-guest agent in-session -
  that is what fork is for (§7).
- **Locks make co-edit safe**, not a global freeze. Leases are per *thing*
  (node / whiteboard item / file region), so different people edit different
  things simultaneously; you only block on the *same* thing.
- **Editing the prototype *source* requires the project be GitHub-connected.**
  Live cursors, node moves, whiteboard, comments and triggering the host's agent
  work on **any** project. Letting guests change `source/<slug>/**` directly is
  unlocked only once there's a repo behind it (history + fork + PR = the safety
  net). Opt-in per project; the cloud dependency is taken on exactly when
  outsiders start mutating files, and never before. See §7.

---

## 2. Access - how a guest joins

Same tunnel and token scheme as share mode, one new route family:

```
https://<rand>.trycloudflare.com/s/<token>/            existing: comment viewer
                                          /live          NEW: collab editor client
                                          /live/api/...   NEW: scoped collab API
                                          /live/events    NEW: guest SSE (presence
                                                               + workflow + locks)
```

1. Host opens the **node dock** (workflow mode) or **Shares tab** → toggles
   **"Live session"** on a share → tunnel starts (or is already up).
2. Host copies the `/live` link, sends it. (Same "⚠ URL changed on restart"
   caveat as share mode - quick-tunnel hostnames churn; the registry's
   `prevUrl`/`lastUrlChangedAt` warning applies unchanged.)
3. Guest opens it → gate serves the **focused collab client** (§4) → guest
   enters a display name (and email if the share's email-gate is on) → joins.
   Identity lives in the guest's localStorage and is enforced server-side at
   write time, exactly like comments today.

The host's **main daemon port is never exposed** - guests only ever reach the
gate. Widening the gate to accept *writes* is the security crux; see §6.

---

## 3. The three new layers

Everything below rides on machinery that already exists; the work is additive.

### 3.1 Presence (cursors + selection) - ephemeral, never persisted

- New SSE event type `presence` on the per-project channel. `WorkflowWaiter`
  already multiplexes event types (`workflow-changed`, `asset-changed`,
  `share-comments-changed`) - `presence` is one more (serve.py:3050 `push`).
- Guests POST throttled cursor/selection (~20-30 Hz, coalesced) to
  `/live/api/presence`; the daemon fans it out to all subscribers and **does
  not write workflow.json** (presence is volatile session state in memory).
- A `participants` roster (who's here, color, role) is session-scoped memory on
  the daemon, gone when the session ends. No registry change.

### 3.2 Leases (the "blocked from editing" behavior)

- A **lease** = a short-lived claim on one editable target:
  `{ target: "node:<id>" | "wb:<id>" | "file:<rel>", holder, expiresAt }`.
- Guest begins editing → `POST /live/api/lease/acquire` → daemon grants iff
  free → broadcasts a `lock` SSE event → every client paints "✎ <name> editing"
  and disables that target. Release on blur OR TTL expiry (heartbeat keeps it
  alive; a dropped guest's lease auto-frees).
- **Enforced server-side, not just visually.** This is the load-bearing part:
  workflow.json is saved **whole-document, last-writer-wins** today, so a write
  to a leased target held by someone else must be **rejected at the gate**, not
  merely greyed out in the UI. Leases serialize the coarse save so two
  simultaneous editors of the same node can't lose updates.
- Reuse the existing per-project workflow mutex (serve.py:3493
  `_workflow_lock` / `_workflow_lock_timeout`) for the *save*; the lease is the
  higher-level, longer-lived, user-visible claim layered above it.

### 3.3 Agent leases (the "agent blocks others" behavior)

- When a guest (or the host) triggers a run, the run **acquires leases over its
  target node + the files it will touch** before it starts, and broadcasts them
  as `lock` events → everyone sees "🔒 agent editing Hero".
- Released by the **completion hook you already have** (the subprocess-completion
  path that broadcasts workflow/asset changes today). On release, an
  `asset-changed` broadcast already exists - guests' prototype iframes refresh
  themselves (serve.py:3129 `_broadcast_asset_change`).
- UX truth to design for: an agent run can hold a lock for *minutes*. Show it
  as a first-class, named, cancellable state - not a frozen UI.

---

## 4. The guest client - focused collab surface (decision: (b))

Guests get a **slimmed editor**, not the full `app.js`:

- **In:** the workflow canvas (nodes, positions, edges, whiteboard) read/write,
  the prototype iframe, comments, presence cursors, lease indicators, and
  "trigger a run on this node" (host-permitting).
- **Out:** settings, project management, DS customizer, export, onboarding,
  workspace switching - anything that is *administering the host's machine*
  rather than *collaborating on this prototype*.

Rationale: a guest is a collaborator on one prototype, not an admin of the
host's workspace. Serving the whole editor is more attack surface than value.
(If we ever want true Live-Share parity for guests who *also* run Woven, a
"attach my local Woven to a remote session" mode can speak the same `/live/api`
wire protocol later - strictly an upgrade, not a v1 requirement.)

---

## 5. Identity & roles

- Two tiers, set by the host per guest (or per share default): **editor** and
  **viewer**. Viewer = cursors + live updates, but writes/leases rejected at the
  gate. Editor = leases + writes + (optional) run-trigger.
- Rides on the same per-guest scoped token needed for gate-write security (§6).
- The email gate stays what it is: **attribution, not auth.** Real auth (e.g.
  Cloudflare Access) remains the documented future upgrade and slots in without
  touching the collab model - same note as share-mode.md.

---

## 6. Security - widening the gate, deliberately

share-mode.md's gate is read-only + comment-CRUD by design ("widen the gate
deliberately or not at all"). Live Session **does** widen it - to accept
*editing* writes - so this is the section to get right:

- **Scoped guest tokens.** A session issues a per-guest capability token
  (separate from the share token) carrying role (editor/viewer) and the share
  it's bound to. Every `/live/api/*` write checks it. Tokens are revocable; the
  host can kick a guest (revoke → their next write 403s, their presence drops).
- **Write whitelist unchanged in spirit.** Guests may mutate only:
  workflow.json (via lease-checked ops), comments, and - if we allow direct
  prototype edits at all - files under `source/<slug>/**` only, same realpath
  containment + extension allowlist as `_gate_project_paths_ok` (shares.py:609).
  Never the daemon's file-write/LLM/project endpoints; never other prototypes.
- **Lease enforcement is a security control, not just UX.** A rejected write on
  a non-held lease is a 409; a write from a revoked/!editor token is a 403.
- **Rate + size limits** on presence and writes (presence is high-frequency;
  cap it server-side so a hostile guest can't flood the host's daemon).
- **Kill switch.** "End session" revokes all guest tokens and drops the
  `/live` routes back to 404 in one action, independent of the tunnel.

---

## 7. Fork & merge - delegated to git / GitHub

We do **not** build a merge engine. v3.1 already cut the bespoke
`MERGES.md` / `FORK_REQUEST.md` system (serve.py:153, serve.py:2580) - and that
was the right call. The lesson was *don't hand-roll merge*, not *merge is
impossible*. So pull / fork / merge are **delegated to git, with GitHub as the
durable remote**, wrapped behind Woven buttons so non-git users never see a
command line (the GitHub-Desktop / Abstract-for-design model).

**Opt-in per project, but the prerequisite for guest source-editing.** A project
is not a repo by default. The host can **connect a project to GitHub** at any
time; doing so is what *unlocks* **guests editing the prototype source** (§1, §4)
- because the moment outsiders mutate your prototype you want every change
versioned, revertible, forkable, and mergeable. Canvas-only multiplayer needs no
repo.

- **Fork = GitHub fork (or `git clone`).** A guest takes a real copy into their
  own GitHub + their own Woven - own files, own agent, own API key, no longer in
  the live session. Durable and offline-capable, unlike a session that dies with
  the host's laptop.
- **Bring it back = a Pull Request.** The forker opens a PR; the host reviews and
  merges. PRs **are** the reviewed-merge feature - for free, with diff view,
  comments, and history.
- **LLM-file conflicts = agent-assisted resolution - the signature move.** Git's
  one real weakness is exactly the old objection: two agents that rewrote
  `index.html` wholesale → a whole-file conflict. Woven resolves it with the
  thing it already has: hand base + both sides to the **host's agent** -
  *"merge these two intents"* - instead of making a human reconcile two blobs of
  generated CSS. No other git wrapper can do this. It turns git's weakness into
  Woven's differentiator.
- **Pull = fetch + agent rebuilds the iframe.** Reviewers see the merged result
  on reload - same live-source loop as share mode.
- **Committing is deliberate, modelled on agent harnesses (Claude Code).** Two
  tiers. *Bottom (automatic, already built):* Woven's node-finish snapshot +
  `_history_bracket` (serve.py:4612-4618) is the fine-grained **undo** layer -
  fires every run, NOT git, nothing lost between commits. *Top (deliberate,
  new):* git commit is a **button the host presses** when a batch is a
  meaningful checkpoint - never automatic, never per-drag/per-run. Exactly like
  Claude Code: the harness tracks every edit; git history is human-curated.
  Woven proposes the message (summarise the bracket labels since last commit);
  **"Publish"** pushes. See §10.
- **Shared-session authorship:** the repo is the host's (their machine + git
  identity), so **the host commits**, crediting in-session guests as
  `Co-authored-by:` trailers (the Claude Code convention). A guest who wants
  their own commit history forks - their repo, their commits, their PR.

**Identity split:** the *live layer* identifies guests by name/email (§5) - for
cursors + attribution. The *git layer* uses each collaborator's **own GitHub
account** - forks and PRs are authored under their identity, which doubles as the
audit trail for who changed what.

**The one rough edge - `workflow.json`.** Node *positions* churn and merge
noisily. Pragmatic stance: treat canvas **layout** as cosmetic / last-writer-wins
(don't fight git over pixel coords); truly merge node **content** + `source/**`.
It is already written `indent=2`, so content diffs are line-meaningful.

---

## 8. Data-model / wire additions (summary)

Registry (`shares.json`) - per share, additive fields:

```
liveActive       bool         // session running (intent), sibling of `active`
roleDefault      "editor"|"viewer"
```

Project config (NOT shares.json - repo is a property of the project) - additive:

```
repo             { provider:"github", remote, defaultBranch } | null
                 // null = not connected. REQUIRED to be non-null for guests to
                 // edit source/<slug>/**; canvas-only multiplayer ignores it.
```

Session state - **in daemon memory, not persisted** (volatile by design):

```
participants[]   { guestId, name, color, role, lastSeen }
leases[]         { target, holder(guestId), expiresAt }
guestTokens{}    { token -> { guestId, role, shareId } }   // revocable
```

New gate routes (all under `/s/<token>/live`):

```
GET  /live                       focused collab client shell
GET  /live/events                guest SSE: presence | workflow-changed |
                                 asset-changed | lock
POST /live/api/join              { name, email? } -> guest token + roster
POST /live/api/presence          { cursor, selection }            (throttled)
POST /live/api/lease/acquire     { target } -> grant | 409 held
POST /live/api/lease/release     { target }
POST /live/api/lease/heartbeat   { targets[] }
POST /live/api/workflow/op       lease-checked node/move/wb mutation
POST /live/api/run               { nodeId } -> trigger HOST agent (editor+host-permit)
POST /live/api/comments…         (reuse share-mode comment CRUD verbatim)
```

New SSE event types on the existing per-project channel: `presence`, `lock`.
Main-daemon (host-editor-facing) additions mirror share mode's `/__share/*`:
`/__live/<id>/start|stop|kick|role`, roster read.

---

## 9. Phased build plan

1. **Presence only (no writes).** `/live` client renders the canvas read-only +
   live cursors + roster. Proves the SSE fan-out and the focused client with
   **zero new write surface.** Guests watch the host edit, live. Genuinely
   useful on its own and the safest first slice.
2. **Leases + guest editing.** Lease acquire/release/heartbeat, server-side
   enforcement on `/live/api/workflow/op`, the "✎ editing" UI. Now guests
   co-edit nodes/whiteboard.
3. **Agent leases.** Guest-triggered runs on the host's LLM, with lock
   broadcast + completion-hook release; the "🔒 agent editing" state.
4. **Roles + kill switch + hardening.** editor/viewer, kick/revoke, rate
   limits, "End session". (Security review gate before this ships externally.)
5. **Git / GitHub backbone (the pull + merge half).** Connect-project-to-GitHub,
   fork (GitHub fork), PR-based bring-back, and the agent-assisted conflict
   resolver. Connecting a repo is what **unlocks guest source-editing** as a
   gated capability - so this phase and "guests edit `source/**`" ship together.

Each phase is shippable and reversible; phase 1 alone is a real feature. Phases
1-3 (presence → canvas co-edit → agent leases) need **no git at all** - they run
on any project. Git enters only at phase 5, exactly when guests touch source.

---

## 10. Open questions (flag before phase 2)

- **Guest source-editing is gated on a connected GitHub repo (DECIDED).**
  Non-repo project → guests get canvas + whiteboard + comments + run-trigger
  only. GitHub-connected project → guests may also edit `source/<slug>/**`,
  because git provides the history / fork / PR safety net. This resolves the
  earlier canvas-vs-source question: it is not v1-vs-later, it is a per-project
  **capability gate**.
- **Commit = deliberate user action (DECIDED).** Modelled on agent harnesses
  (Claude Code): the agent + guests edit the working tree freely, and **git
  commit is a button the host presses**, never automatic. Woven's existing
  node-finish snapshot + `_history_bracket` (serve.py:4612-4618) remain the
  automatic fine-grained **undo** layer (NOT git) - nothing is lost between
  commits. Two tiers, exactly like Claude Code: the harness tracks every edit;
  git history is human-curated. Woven proposes the commit message by summarising
  the bracket labels since the last commit; **"Publish"** pushes. Shared-session
  commits are **host-authored** with guest `Co-authored-by:` trailers; a guest
  wanting their own commit history forks. Realtime edits are NEVER in the git hot
  path - they land on the host's working tree via leases; git observes only when
  the host commits.
- **Guest GitHub auth = full OAuth in the collab client (DECIDED).** The collab
  client runs the GitHub OAuth flow so a guest authenticates in-place; forks +
  PRs are then authored under their own account (the §7 identity split). No
  hand-off to github.com - the whole loop (fork → edit in session → PR) stays
  inside Woven. Implication for the build: register a GitHub OAuth app + a
  token-exchange endpoint on the host daemon (tokens stored per guest session,
  scoped to repo + PR, revoked on session end).
- **Presence transport at scale.** SSE + POST is fine for a handful of guests;
  if sessions ever want dozens, revisit (WebSocket, or a presence-only WS beside
  the SSE channel). Not a v1 concern.
- **Concurrent run policy.** One agent run at a time per session (queue), or
  allow parallel runs on disjoint nodes? The per-project semaphore
  (serve.py:3527) already caps this; surface the cap in the UI.

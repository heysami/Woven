# Share mode — Cloudflare quick tunnels + per-element review comments

> Status: shipped (v3.8). Server: `editor/shares.py` + wiring in `editor/serve.py`.
> Visitor surface: `editor/share/viewer.{html,js,css}`. Editor UI: `SharesLanding`
> (landing tab) + `WorkflowCommentsPanel` (prototype node dock) in `editor/app.js`.

Share mode publishes ONE prototype (`source/<slug>/` of one project) through a
**Cloudflare quick tunnel** so anyone with the link can browse the live prototype
and pin comments on specific elements. Comments flow back into the project, surface
on the prototype node in workflow mode, and can be batch-dispatched to the build
agent ("process these comments"). It is the live, collaborative sibling of the
export feature: export produces a frozen offline bundle; share exposes the living
source tree behind a revocable URL.

## The three surfaces

1. **Share viewer** (visitors) — `https://<rand>.trycloudflare.com/s/<token>/`.
   The prototype runs in a same-origin iframe under viewer chrome: a comment mode
   (click any element → pin + composer), numbered pins that track scroll/reflow,
   and a sidebar of threads (reply / done / archive / delete, filters). Clicking a
   comment navigates to its page and flash-highlights its element. Visitors
   identify with a name (always) and email (when the share's **email gate** is on);
   identity lives in their localStorage and the gate enforces it server-side at
   POST time.

2. **Landing "Shares" tab** (before System) — every share across the workspace
   with live tunnel status (`running / starting / stopped / exited / error /
   no-cloudflared`), the public URL (copy / open), a **URL changed** warning,
   per-share comment counts, and start / stop / delete / email-gate controls.
   Polls `GET /__shares` every 5s while open.

3. **Prototype node comments dock** (workflow mode) — a 💬 top-action on the
   prototype node (sibling of the `</>` code toggle) docks a panel on the node's
   LEFT edge: share controls (create / start / stop / copy URL), the comment
   threads (same ops as the viewer, authored as "Owner"), and checkbox-select →
   **Send to agent**, which builds a structured prompt (page + selector + request
   + replies per comment), dispatches it through the workflow chat
   (`onStartChatWithPrompt` → `triggerRun`), and stamps the comments
   `processedAt`. Clicking a comment flash-highlights the element in the node's
   live iframe when it is showing that page.

## Security model — the gate

`cloudflared` never points at the main daemon port. At boot, serve.py starts a
**second listener** (the *gate*, first free port after the daemon's; see
`[share] gate listening …` in the console) whose handler serves ONLY:

```
GET  /s/<token>/                       viewer shell (301 from the slash-less form)
GET  /s/<token>/viewer.js|viewer.css   viewer assets
GET  /s/<token>/api/meta               { label, prototype, emailGate, entry }
GET  /s/<token>/api/comments           threads for this share's prototype
POST /s/<token>/api/comments           add (requires author name; +email if gated)
POST /s/<token>/api/comments/<cid>/(reply|status|delete)
GET  /s/<token>/p/<project-rel-path>   whitelisted files ONLY:
                                       source/<slug>/** and design-systems/**,
                                       extension-whitelisted, no dotfiles,
                                       realpath-contained in the project root
GET  /__global_fonts/<file>            read-only font passthrough (DS stylesheets
                                       reference these root-absolute)
```

Everything else 404s — `/__workflow`, `/__write_text`, `/editor/**`, other
prototypes, `workflow/`, `../` traversal all verified unreachable. Tokens are
32-hex `secrets.token_hex(16)`; deleting a share revokes its token immediately.
**Widen the gate deliberately or not at all.**

## Registry + stores

- **`shares.json`** (workspace root, sibling of workspace.json):
  `{ shares: [{ id: "shr-…", token, project, prototype, label, emailGate,
  active, createdAt, lastUrl, prevUrl, lastUrlChangedAt, lastStartedAt }] }`.
  `active` is *user intent*, not liveness — on daemon boot,
  `restore_active_tunnels()` restarts tunnels for every `active` share.
- **`<project_root>/share/comments.json`** — all comments for the project
  (records carry `prototype`):
  `{ id: "c-…", prototype, page, anchor: { selector, tag, text }, pin: {x,y},
  text, author: { name, email }, createdAt, status: open|done|archived,
  processedAt, replies: [{ id: "r-…", text, author, createdAt }] }`.
  `anchor.selector` is the primary locator; tag+text are fuzzy fallbacks for DOM
  drift after agent edits. `pin` is a fraction of the element's box, so pins
  survive responsive reflow. `processedAt` is orthogonal to `status` — the agent
  ran, but the reviewer decides when it's *done*.

## Quick tunnels — what to expect

- Requires the `cloudflared` binary (`brew install cloudflared`). No Cloudflare
  account. The UI degrades gracefully when missing (install hint, Start disabled).
- **URLs change on every tunnel start** (daemon restart included). The registry
  keeps `prevUrl` + `lastUrlChangedAt`; the UI shows a "⚠ URL changed" chip until
  the user copies the new link (copy ACKs via `POST /__share/<id>/ack_url`).
- Tunnels are daemon-managed subprocesses: SIGTERMed on shutdown
  (`_cleanup_subprocesses`), restored on boot for `active` shares.
- The email gate is app-level identity for comment attribution, **not** real
  auth. A future alternative is Cloudflare Access (named tunnels + Zero Trust),
  which slots in as a second gate mode without touching the comment model.

## Main-daemon endpoints (editor-facing)

```
GET  /__shares                           all shares + status + commentCounts
                                         + cloudflared availability + gatePort
POST /__share/create?project=<id>        { prototype, emailGate?, label?, start? }
                                         idempotent per (project, prototype)
POST /__share/<id>/start|stop|delete|update|ack_url
GET  /__share_comments?project=&prototype=
POST /__share_comments?project=<id>      { op: add|reply|status|delete|processed, … }
```

Comment mutations broadcast `share-comments-changed` on the per-project
`/__workflow/events` SSE channel; the editor panels also poll (5–6s) since
visitors write through the gate at any time.

## Live source, not a snapshot

The gate serves the project's CURRENT `source/<slug>/` tree. When the agent
processes comments and edits the prototype, reviewers see the changes on their
next reload — that's the loop: share → comment → send-to-agent → updated
prototype → reviewer re-checks → mark done.

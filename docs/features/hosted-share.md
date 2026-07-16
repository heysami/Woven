# Hosted shares - snapshot hosting on getwoven.design

Share links used to be tunnel-only: the viewer's browser reached the user's
own machine through cloudflared, so the link died the moment the laptop
slept. A HOSTED share removes that dependency: the daemon uploads a static
snapshot of the prototype to Woven-run storage and the SAME stable URL
(`https://<install>.getwoven.design/s/<token>/`) serves it - laptop off,
daemon dead, doesn't matter. Toggle it off and the snapshot is deleted, so
hosting never accumulates storage.

## How the pieces fit

```
 daemon (shares.py)                broker (Render)               Cloudflare
 ──────────────────               ────────────────              ───────────
 build snapshot tar.gz  ──POST──▶ /shares/upload   ──S3 API──▶  R2 bucket
   share/…  fonts/…               validates, caps,              woven-shares
                                  extracts, uploads
                                                                     ▲
 visitor browser ──▶ <install>.getwoven.design/s/<token>/… ──▶ share worker
                     (proxied DNS, so the worker route fires)  (worker/)
                                                                     │
                                                        miss / live paths
                                                                     ▼
                                                        cloudflared tunnel
                                                        (exactly as before)
```

- **Same URL for tunnel and snapshot.** `<install>.getwoven.design` DNS is a
  PROXIED CNAME to the install's named tunnel, so every request already flows
  through Cloudflare's edge. The worker (route `*.getwoven.design/s/*`)
  intercepts: if R2 holds `s/<token>/__hosted.json`, the share is hosted and
  static requests are answered from the bucket; otherwise every byte falls
  through to the tunnel and the worker is invisible.
- **The snapshot mirrors the gate's URL space.** `share/<sub>` members map to
  `s/<token>/<sub>` objects: the viewer shell at `index.html`, a static
  `api/meta`, and the whitelisted project files under `p/source/<slug>/` +
  `p/design-systems/` - the exact same extension whitelist and dotfile rules
  the tunnel gate enforces (`_GATE_SERVE_EXTS`), so hosting can never expose
  more than tunnelling does. Workspace fonts ship as `fonts/<name>` members →
  `fonts/<install>/<name>` objects, served on the `/__global_fonts/*` route
  (DS stylesheets reference them root-absolute).
- **Live things stay live.** `/s/<token>/live*` (multiplayer + live editor)
  always passes through to the tunnel. `/api/*` (comments CRUD) passes
  through too, so commenting works normally whenever the daemon is up; when
  it is down, the worker degrades - `api/meta` is served from the snapshot
  (the viewer boots), comment reads return an empty list, and NEW comments
  queue at the broker's OFFLINE INBOX (below). Replies / status flips /
  screenshots need the daemon and get a readable "owner is offline" error.
  `liveOnly` shares (multiplayer transport) cannot be hosted at all.

### Offline comment inbox

Visitors can leave comments even while the owner's machine is off:

- Worker: a failed origin `POST /api/comments` on a hosted share forwards
  `{token, comment}` to `BROKER_URL/shares/inbox` and returns
  `{ok, queued: true, comment}`. The viewer shows the comment locally with a
  green "the owner will receive it when they're back" notice (screenshots +
  attachments are dropped offline - they need the daemon).
- Broker: `POST /shares/inbox` is public but bounded - only currently-hosted
  tokens, whitelisted + clipped fields (the exact comments.json record shape,
  id/createdAt minted broker-side, `viaInbox: true` provenance flag), 200
  pending per token, 30 posts/hour/IP. Rows live in `hosted_comments`.
- Daemon: while any share is hosted, an inbox loop (2min interval, first pull
  at boot) does a crash-safe two-phase drain: `POST /shares/inbox_pull`
  {installId} → merge each item into the project's comments.json (same locks
  and shape the gate uses, deduped by comment id, orphaned/bogus items
  dropped) → `POST /shares/inbox_ack` {installId, ids}. Redelivery after a
  crash is harmless thanks to the id dedup.
- Cleanup: inbox rows purge with their share (delete/deprovision/reap) and
  the reaper drops uncollected rows after `INBOX_TTL_DAYS` (60).
- Snapshots ship the viewer, so shares uploaded BEFORE this feature queue
  comments correctly (the worker handles that side) but show the old error
  copy until their owner presses Update to refresh the snapshot.

### Offline comment visibility

Existing comments stay VISIBLE while the owner is off (they used to vanish -
reads passed through to the dead tunnel and fell back to an empty list):

- The snapshot bakes in `share/api/comments` (the discussion as JSON) plus
  every comment screenshot (`api/comments/<cid>/shot`, jpg) and attachment
  (`api/comments/<cid>/attach/<aid>`).
- The daemon RE-PUSHES the comment list on every change via
  `POST /shares/update_comments` {installId, token, comments} (installId-
  bound like delete, 2MB cap, coalesced 3s daemon-side in
  `_hosted_comments_push_soon`, hooked into `_notify_comments_changed`) - so
  the stored copy is current as of the last moment the owner was online, not
  the upload date. Inbox merges trigger the same hook, so collected offline
  comments appear in the stored copy too.
- Worker, offline: GET `api/comments` serves the stored copy (empty-list
  fallback only when none exists); GET shot/attach paths serve the stored
  images (404 with a readable message otherwise). Online reads always pass
  through live. Shots/attachments added after the upload only ship on the
  next snapshot Update; their comments still show, imageless, via the push.
- **Snapshot semantics, on purpose.** Visitors see the uploaded version until
  the owner presses Update (share panel ↻ / "Update snapshot"). This is a
  prototype share, not a production deploy - publish-to-online remains the
  path for real products.

## Lifecycle and storage bounds

- Toggle ON → daemon ensures the install is provisioned (broker HTTP only -
  NO cloudflared needed), builds the tar.gz, uploads in a background thread.
  `hostedStatus` polls through uploading → hosted.
- Toggle OFF / share deleted / install deprovisioned → broker deletes the R2
  prefix and the registry row (best-effort daemon-side, idempotent).
- TTL backstop: the daily reaper cron also deletes snapshots whose install
  has not heartbeat in `HOSTED_TTL_DAYS` (30). The daemon heartbeats every 6h
  while any share is hosted (`ensure_hosted_heartbeat`), independent of the
  woven tunnel.
- Caps (broker env): `HOSTED_SNAPSHOT_MAX_MB` 100 (gz body),
  `HOSTED_UNPACKED_MAX_MB` 300, `HOSTED_QUOTA_MB` 500 per install, 60
  uploads/hour/IP. Oversized single files are skipped daemon-side
  (`_HOSTED_FILE_MAX` 100MB) with a log line.

## Ownership / auth model

The share token (random 32-hex, lives only in the owner's shares.json) is the
credential. First upload binds token → installId in the broker's
`hosted_shares` table; later uploads/deletes must present the same installId.
The R2 credentials live only in the broker env (like the Cloudflare API
token); the worker reads the bucket through a zero-credential binding.

### Hosting passcode

Uploading additionally requires a HOSTING PASSCODE, so having the (public)
Woven code is not enough to park bytes on getwoven.design. Properties:

- Codes live server-side only: hashed (sha256) rows in the broker's
  `hosted_passcodes` table, managed via ADMIN_TOKEN-gated endpoints
  (`POST /admin/passcodes` {code,label}, `POST /admin/passcodes/revoke`,
  `GET /admin/passcodes` - list shows labels + hash prefixes, never codes).
  `HOSTED_PASSCODES` env (comma-separated) is a bootstrap/break-glass
  fallback. NOTHING in the repo contains or can derive a valid code.
- The broker enforces it on `/shares/upload` (header `X-Woven-Passcode`) and
  offers `POST /shares/passcode_check` so clients pre-flight a code in
  milliseconds instead of after shipping a snapshot. Failed attempts are
  rate-limited (30/hour/IP); valid ones never trip the limiter.
- The BROWSER owns the entered code: localStorage key `wovenHostedPasscode`,
  prompted once via `ensureHostedPasscode()`, sent with every hosted toggle-on
  / update, cleared + re-prompted once when the broker rejects it
  (`passcodeRequired: true` from the daemon).
- The daemon relays it per request and keeps it ONLY in process memory
  (`_HOSTED_PASSCODE`) so background re-uploads work; it is never written to
  shares.json or any file, and a daemon restart requires the browser to send
  it again (it does, automatically, from localStorage).
- `hosted_update` pre-flights the code on EVERY (re)upload, so a code revoked
  broker-side surfaces as a 403 the UI can react to, not a silent background
  failure. Toggling OFF and deleting need no passcode.
- One code today, many tomorrow: rows are independent, so per-person codes
  with labels + individual revocation already work.

## One-time infra runbook

Everything is idempotent; re-running any step is safe.

1. **R2 bucket + S3 credentials** (Cloudflare dashboard → R2, same account
   that owns getwoven.design):
   - Create bucket `woven-shares`.
   - R2 → Manage API tokens → Create token, permission "Object Read & Write",
     scoped to the `woven-shares` bucket. Note the Access Key ID + Secret.
   - The S3 endpoint is `https://<account-id>.r2.cloudflarestorage.com`
     (account id `0d7b52ff0f6513b1c175d33761c497a7`).
2. **Broker env** (Render dashboard → woven-broker → Environment): set
   `R2_ENDPOINT`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`. `R2_BUCKET` and
   the caps come from render.yaml. Deploy (the hosted_shares table
   self-creates on boot).
3. **Hosting passcode**: either set `HOSTED_PASSCODES` in the Render env
   (comma-separated, quickest), or add a DB-backed code (revocable, labelled):
   ```
   curl -X POST https://woven-broker.onrender.com/admin/passcodes \
     -H "X-Admin-Token: $ADMIN_TOKEN" -H "Content-Type: application/json" \
     -d '{"code": "<the passcode>", "label": "sami"}'
   ```
4. **Worker** (from `worker/`, needs Node):
   ```
   npx wrangler login
   npx wrangler deploy
   ```
   wrangler.toml pins the account, the two routes
   (`*.getwoven.design/s/*`, `*.getwoven.design/__global_fonts/*`) and the R2
   binding. Until the worker is deployed the Hosted toggle uploads fine but
   visitors still get the tunnel - deploying it flips snapshots live with no
   client change.

## Client surface

- shares.json record: `hostedOn` (intent), `hostedAt`, `hostedBytes`,
  `hostedFiles`.
- `/__share/<id>/update` body accepts `hostedOn`; `/__share/<id>/host_update`
  re-uploads. `share_summary` exposes `hostedOn/hostedStatus/hostedUrl/
  hostedError/hostedAt/hostedBytes`; `shareUrl` prefers wovenUrl, then a
  hosted URL, then quickUrl.
- UI: third switch "Hosted" in ShareModeToggle (share menu, Shares landing
  tab, workflow comments panel), with per-link row, upload state, and an
  Update affordance. The switch needs no cloudflared - only the broker.

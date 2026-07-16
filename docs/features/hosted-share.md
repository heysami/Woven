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
  through too, so commenting keeps working whenever the daemon is up; when it
  is down, the worker degrades gracefully - `api/meta` is served from the
  snapshot (the viewer boots), comment reads return an empty list, comment
  writes get a readable "owner is offline" error. `liveOnly` shares
  (multiplayer transport) cannot be hosted at all.
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
3. **Worker** (from `worker/`, needs Node):
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

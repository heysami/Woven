# Woven share broker

Hands each Woven install its own stable Cloudflare tunnel, so the public share
URL never changes. The client calls `/provision` **once** on first run, saves
the credentials locally, and runs the tunnel itself thereafter - the broker is
not in the data path and need not even be up for existing users.

```
client first run ──POST /provision {installId}──▶ broker
                                                   ├─ create CF tunnel (config_src=local)
                                                   ├─ upsert CNAME <id>.getwoven.design
                                                   └─ return {hostname, credentials}
client saves creds ──cloudflared tunnel run──▶ Cloudflare edge ──▶ this laptop
```

Files: `main.py` (API), `cloudflare.py` (CF API client), `store.py` (Postgres),
`schema.sql`, `render.yaml`, `requirements.txt`.

---

## One-time setup (you, the operator)

### 1. Cloudflare API token  🔒
Dashboard → **My Profile → API Tokens → Create Token → Create Custom Token**:
- **Account** › `Cloudflare Tunnel` › **Edit**
- **Zone** › `DNS` › **Edit** → scope to **Zone: getwoven.design**
Create it, copy the token **once**. This is the only Cloudflare secret; it lives
**only** in the broker env. Never commit it, never ship it in Woven.

### 2. Supabase
Create a project → **SQL Editor** → run `schema.sql`. Then **Project Settings →
Database → Connection string (URI)** and copy it (the `postgres://...` value) -
this is `DATABASE_URL`. Use the **session / direct** connection string.

### 3. Render
New → **Blueprint** → point at this repo (it reads `render.yaml`, `rootDir:
broker`). In the dashboard set the secret env vars (marked `sync:false`):

| Env | Value |
|-----|-------|
| `CF_API_TOKEN` | the token from step 1 🔒 |
| `DATABASE_URL` | the Supabase URI from step 2 🔒 |
| `ADMIN_TOKEN` | any long random string you generate 🔒 (protects `/admin/reap`) |
| `BROKER_URL` | the service URL Render assigns, e.g. `https://woven-broker.onrender.com` (for the reaper cron) |

`CF_ACCOUNT_ID`, `CF_ZONE_ID`, `BASE_DOMAIN`, `REAP_TTL_DAYS` are already in
`render.yaml`.

### 4. Bake the broker URL into Woven
The client needs to know where to call. Put the Render URL
(`https://woven-broker.onrender.com`) into the client config constant (wired in
the Phase-1 `shares.py` change). If that constant is absent, Woven stays
quick-tunnel-only - the broker is purely additive.

---

## Verify

```bash
curl https://woven-broker.onrender.com/healthz
# {"ok":true}

curl -X POST https://woven-broker.onrender.com/provision \
  -H 'content-type: application/json' \
  -d '{"installId":"00000000000000000000000000000001"}'
# {"hostname":"00000000000000000000000000000001.getwoven.design","tunnelId":"...","credentials":{...}}
```
Then clean that test up:
```bash
curl -X POST https://woven-broker.onrender.com/deprovision \
  -H 'content-type: application/json' \
  -d '{"installId":"00000000000000000000000000000001"}'
```

---

## Endpoints

| Method | Path | Body | Notes |
|--------|------|------|-------|
| POST | `/provision` | `{installId}` | idempotent; per-IP rate limited; returns credentials |
| POST | `/heartbeat` | `{installId}` | bumps `last_seen`; `{ok,known}` |
| POST | `/deprovision` | `{installId}` | deletes tunnel + DNS + row |
| POST | `/admin/reap` | — | `X-Admin-Token` header; prunes idle installs |
| GET | `/healthz` | — | liveness |

## Scaling notes (Phase 2)
- Rate-limit state is in-memory → fine for one Render instance; move to
  Postgres/Redis before running >1 replica.
- One tunnel + one DNS record per install. Cloudflare per-account/zone limits
  cap this at low thousands; beyond that, shard across zones/accounts.
- Cloudflare free-tier ToS restricts disproportionate non-HTML traffic.

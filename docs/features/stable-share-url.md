# Stable share URLs (woven mode)

Share mode publishes a prototype through a Cloudflare tunnel. By default that is
a **quick tunnel** - a random `*.trycloudflare.com` hostname that **changes every
time the daemon restarts**. Woven mode gives a share a **stable** URL
(`https://<install>.getwoven.design/s/<token>/`) that survives restarts, reboots,
and network blips.

Each share carries a `mode`: `"quick"` (default, unchanged behaviour) or
`"woven"`. The choice is per share, toggled in the UI - quick stays the
zero-infra floor; woven is an opt-in upgrade that needs the broker.

## How the stable URL holds

`https://<install>.getwoven.design/s/<shareToken>/` - both halves are stable:

| Half | Source | Stable across restart? |
|------|--------|------------------------|
| `<install>` subdomain | `~/.woven/install-id` (persisted) → broker maps it to a fixed subdomain | yes |
| `/s/<shareToken>` path | `shares.json` (already persisted today) | yes |

The URL only changes if `~/.woven/install-id` is deleted or the machine/OS-user
changes (a genuinely new install). A daemon reset never touches it.

## Architecture

- **One named tunnel per install** (not per share). Every woven share multiplexes
  through it via its own `/s/<token>/` path, so each shared prototype still has a
  distinct, permanent URL. (Quick mode stays one tunnel per share.)
- **The broker is first-run only.** First time woven mode is used, the client
  calls the broker's `/provision`, caches the returned credentials in
  `~/.woven/`, and from then on runs the tunnel itself - the broker being down
  never breaks an already-provisioned install.
- **The broker holds the Cloudflare API token**; the client only ever sees its
  own tunnel credentials. See `broker/` and `broker/README.md`.

### Client (editor/shares.py)
- `woven_install_id()` - persist/read `~/.woven/install-id` (32 hex).
- `_woven_ensure_credentials()` - cache in `~/.woven/woven.json` +
  `~/.woven/<tunnelId>.json`; calls the broker only on first run / lost creds.
- `_woven_write_config()` - regenerates `~/.woven/config.yml` each start with the
  CURRENT gate port (broker creates the tunnel with `config_src=local`, so the
  client owns ingress).
- `_woven_tunnel_start/stop` - the single shared `cloudflared --config … tunnel
  run` process + a `/heartbeat` loop (every 6h) so the reaper keeps the tunnel.
- `tunnel_start` / `tunnel_stop` / `tunnel_status` branch on `share_mode(rec)`;
  the quick path is unchanged. The shared tunnel runs while `_woven_active_count()
  > 0`.
- `share_set_mode(share_id, mode)` - switch quick⇄woven, restarting if live.

### Server (editor/serve.py)
- `/__shares` now returns `woven: {available, baseUrl}`.
- `/__share/<id>/update` accepts `{mode: "quick"|"woven"}` → `share_set_mode`.

### UI (editor/app.js)
- A per-share **Quick / Stable** segmented toggle in both the right-rail
  "Live & shares" panel and the landing "Shares" tab. Shown only when
  `woven.available`.

## Multiplayer

Live sessions ride the same gate + `/s/<token>/live` path, so woven mode changes
only the `<base>` - join URLs and the share-URL indicator work unchanged. Because
the woven base never rotates, the "URL changed" warning simply never fires for a
woven share.

## Deployment record

- Share domain: **getwoven.design** (Cloudflare Registrar / zone).
- Cloudflare account ID: `0d7b52ff0f6513b1c175d33761c497a7`
- Cloudflare zone ID: `c25b3eee7496fa194bb7afded911aa35`
- Broker: **https://woven-broker.onrender.com** (Render web service + daily
  reaper cron; Supabase Postgres registry). Baked into the client as
  `WOVEN_BROKER_URL` (overridable via env).

## Scaling notes (open)
- One tunnel + one DNS record per install → Cloudflare per-account/zone limits cap
  this at low thousands; beyond that, shard across zones/accounts.
- No accounts → abuse defense is the broker's per-IP rate limit + reaper only.

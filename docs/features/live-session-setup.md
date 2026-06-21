# Live Session - setup (host)

> Companion to [live-session.md](live-session.md) (the design + how it works).
> This is the one-time host setup. Phases 1-4 (the multiplayer) need **only
> cloudflared**. Phase 5 (fork / PR / commit-with-co-authors) adds **git** and
> an optional **GitHub OAuth app**.

## 1. cloudflared (required for any sharing)

Already part of share mode. Install once:

```
brew install cloudflared
```

or via **Settings ⚙ → Local skills → Install cloudflared**. No Cloudflare
account needed (quick tunnels).

## 2. Going live

1. Open the **Shares** tab (landing).
2. On a shared prototype row, click **Go live ▶** - this starts the tunnel (if
   needed) and opens a session.
3. Copy the **live link** (`…/s/<token>/live/`) and send it. Guests open it in a
   browser - no install. They enter a name (and email if the share's email gate
   is on) and join.
4. Guests get **editor** role by default - live cursors, node moves, per-element
   locks, and a **Run** button that triggers **your** agent (your machine, your
   API key). Click a guest's avatar in the row to toggle them **editor ⇄
   viewer**. **End session** disconnects everyone (the tunnel keeps running for
   comments).

> Quick-tunnel URLs change every restart - the same "⚠ URL changed" caveat as
> share mode. Re-copy + resend after a daemon restart.

## 3. git (for Commit / Publish)

`git` must be installed (it is, on any dev Mac). In the live row:

- **Commit…** - stages the project and commits. You choose **when** (never
  automatic). It drafts a message from what changed; in-session guests who
  edited or triggered runs are added as `Co-authored-by:` trailers. First
  Commit on a non-repo prompts you to connect a GitHub remote (or leave blank
  for a local-only repo).
- **Publish** - pushes to the connected `origin`.

This layer is **fully local** - it works offline and needs no GitHub account.
Connecting a repo is also what **unlocks guests forking** (below).

## 4. GitHub OAuth app (optional - enables guest Fork / PR)

Guests authenticate **inside the collab client** via GitHub's **Device Flow**
(chosen because quick-tunnel hostnames change every restart, so a fixed OAuth
callback URL can't work - device flow needs none). To enable it, register one
OAuth app and drop its credentials on the host:

1. **github.com → Settings → Developer settings → OAuth Apps → New OAuth App.**
   - *Application name:* `Woven Live` (anything)
   - *Homepage URL:* `https://woven.local` (anything)
   - *Authorization callback URL:* `https://woven.local/callback` (anything -
     device flow ignores it, but GitHub requires a value)
2. Open the created app and **check “Enable Device Flow.”** (This is the
   load-bearing step - without it the device flow returns an error.)
3. **Generate a client secret.**
4. Create **`~/.woven/github-oauth.json`** (or `editor/github-oauth.json`):

   ```json
   { "client_id": "Iv1.xxxxxxxx", "client_secret": "xxxxxxxxxxxxxxxx" }
   ```

   (This file is read by `editor/git_ops.py`; keep it out of the repo.)

Restart the daemon. Now the collab client shows a **⑂ Fork** button: a guest
clicks it → enters a short code at `github.com/login/device` → forks the
prototype repo to **their** account → clones into **their** Woven to work
independently → opens a **PR** back to the host when ready. The token stays
server-side on the host; the browser never sees it.

> Without this file, everything except guest Fork/PR still works - the ⑂ Fork
> button just stays hidden.

## 5. Quick local test (no tunnel, no GitHub)

```
python3 editor/tests/live_demo_server.py
```

prints a `http://127.0.0.1:<port>/s/<token>/live/` URL. Open it in two browser
tabs to see cursors + co-editing locally. (Also wired as the `live-demo`
config in `.claude/launch.json`.)

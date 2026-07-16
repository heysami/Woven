"""Share mode - publish a prototype through a Cloudflare quick tunnel with
per-element review comments.

Three cooperating pieces, all daemon-side (serve.py imports this module the
same way it imports exports.py):

  1. REGISTRY  - shares.json at the workspace root (sibling of
     workspace.json). One record per shared prototype:
       { id, token, project, prototype, label, emailGate, active,
         createdAt, lastUrl, prevUrl, lastUrlChangedAt, lastStartedAt }
     `active` is USER INTENT (should a tunnel be running), not liveness -
     liveness comes from the tunnel process table below.

  2. TUNNELS   - one `cloudflared tunnel --url http://127.0.0.1:<gate>`
     subprocess per active share. Quick tunnels need no Cloudflare account;
     the price is a random *.trycloudflare.com hostname that CHANGES on
     every restart. We parse the URL from cloudflared's log output, persist
     it on the share record, and keep the previous URL around so the UI can
     surface "URL changed since you last copied it".

  3. GATE      - a second HTTP listener (separate port from the main daemon)
     that is the ONLY thing a tunnel ever points at. It serves exactly:
       /s/<token>/                      → review viewer shell (editor/share/)
       /s/<token>/viewer.js|viewer.css  → viewer assets
       /s/<token>/p/<project-rel-path>  → whitelisted prototype files
                                          (source/<slug>/** + design-systems/**)
       /s/<token>/api/meta|comments…    → share metadata + comment CRUD
       /__global_fonts/<file>           → read-only font passthrough (DS
                                          stylesheets may reference these
                                          root-absolute)
     Everything else 404s. The main daemon port - with its file writes, LLM
     runs and project management - is never exposed. This is the security
     boundary the whole feature rests on; widen it deliberately or not at all.

  COMMENTS     - per-project store at <project_root>/share/comments.json
     (all prototypes of a project in one file, records carry `prototype`).
     Written by visitors through the gate AND by the editor through the main
     daemon's /__share_comments endpoint - both funnel through the same
     functions here, under the same lock.

serve.py wiring (see "share mode" section there):
     init(...)                 once at boot
     start_gate_server(port)   once at boot  → gate port
     restore_active_tunnels()  once at boot  (active shares get tunnels back;
                                              their URLs will have changed)
     stop_all_tunnels()        from the shutdown hooks
"""
from __future__ import annotations  # keep annotations 3.9-safe (daemon runs system py)

import base64
import http.server
import json
import mimetypes
import os
import re
import secrets
import shutil
import socketserver
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

# ── Module config (set once by init()) ──────────────────────────────────────

WORKSPACE_DIR = None          # where shares.json lives
INSTALL_ROOT  = None          # where editor/share/viewer.* live
_RESOLVE_PROJECT_ROOT = None  # fn(project_id:str) -> abs path (raises ValueError)
_ON_COMMENTS_CHANGED  = None  # fn(project_id:str, prototype:str) | None
GATE_PORT = None              # set by start_gate_server()

_REGISTRY_LOCK = threading.Lock()
_COMMENTS_LOCK = threading.Lock()

TOKEN_OK     = re.compile(r"^[a-f0-9]{24,64}$")
SHARE_ID_OK  = re.compile(r"^shr-[a-f0-9]{8,16}$")
COMMENT_ID_OK = re.compile(r"^[cr]-[a-f0-9]{8,16}$")
ATTACH_ID_OK = re.compile(r"^a-[a-f0-9]{8,16}$")
EMAIL_OK     = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_TUNNEL_URL_RE = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")

COMMENT_STATUSES = ("open", "done", "archived")

# ── Woven (stable-URL) mode ──────────────────────────────────────────────────
# A share's `mode` is "quick" (anonymous *.trycloudflare.com, rotates on every
# restart - the default) or "woven" (a STABLE https://<install>.getwoven.design
# URL served through a named tunnel the broker provisions). Woven mode uses ONE
# named tunnel per install (not per share): every woven share multiplexes through
# it via its own /s/<token>/ path, so each shared prototype still has a distinct,
# permanent URL. The broker (broker/) holds the Cloudflare API token; the client
# only ever sees its own tunnel credentials. See docs/features/stable-share-url.md.
WOVEN_BROKER_URL  = (os.environ.get("WOVEN_BROKER_URL") or "https://woven-broker.onrender.com").rstrip("/")
WOVEN_BASE_DOMAIN = os.environ.get("WOVEN_BASE_DOMAIN") or "getwoven.design"
WOVEN_DIR         = os.path.expanduser("~/.woven")
INSTALL_ID_RE     = re.compile(r"^[a-f0-9]{32}$")
_WOVEN_HEARTBEAT_INTERVAL = 6 * 3600   # seconds; reaper TTL is 45 days, so this is ample


def init(workspace_dir, install_root, resolve_project_root, on_comments_changed=None):
    """Called once from serve.py before any other function here."""
    global WORKSPACE_DIR, INSTALL_ROOT, _RESOLVE_PROJECT_ROOT, _ON_COMMENTS_CHANGED
    WORKSPACE_DIR = workspace_dir
    INSTALL_ROOT  = install_root
    _RESOLVE_PROJECT_ROOT = resolve_project_root
    _ON_COMMENTS_CHANGED  = on_comments_changed


def _now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())


# ═════════════════════════════════════════════════════════════════════════
# 1. Registry - shares.json
# ═════════════════════════════════════════════════════════════════════════

def _shares_json_path():
    root = WORKSPACE_DIR or INSTALL_ROOT or "."
    return os.path.join(root, "shares.json")


def shares_load():
    p = _shares_json_path()
    if not os.path.isfile(p):
        return {"shares": []}
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f) or {}
    except Exception:
        return {"shares": []}
    if not isinstance(data, dict):
        return {"shares": []}
    data.setdefault("shares", [])
    if not isinstance(data["shares"], list):
        data["shares"] = []
    return data


def _shares_save(data):
    p = _shares_json_path()
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, p)


def share_get(share_id):
    for s in shares_load().get("shares", []):
        if isinstance(s, dict) and s.get("id") == share_id:
            return s
    return None


def share_get_by_token(token):
    if not token or not TOKEN_OK.match(token):
        return None
    for s in shares_load().get("shares", []):
        if isinstance(s, dict) and s.get("token") == token:
            return s
    return None


# Sentinel "prototype" for a project's multiplayer transport share. Never a real
# source/ dir - the live editor loads /source/<files> by project root, so this
# share needs no prototype of its own.
LIVE_PROTO = "__multiplayer__"


def live_share_get_or_create(project):
    """Get (or create) the project's dedicated MULTIPLAYER transport share - the
    live-only share Go Live hosts its session on, independent of any prototype
    share. Idempotent per project."""
    rec, _created = share_create(project, LIVE_PROTO,
                                 label="Multiplayer session", live_only=True)
    if not rec.get("liveOnly"):
        rec = share_update(rec["id"], {"liveOnly": True}) or rec
    return rec


def share_create(project, prototype, label=None, email_gate=False, live_only=False):
    """Create a share record. One share per (project, prototype) - creating
    again returns the existing record (idempotent, so the node's Share
    button can't mint duplicate tunnels for the same prototype).

    live_only=True marks a project-level MULTIPLAYER transport share: it hosts
    the live co-edit session on its own tunnel but the gate refuses the public
    prototype-review routes for it, and the editor hides it from every "shared
    prototype" list. This keeps Go Live fully independent of prototype sharing."""
    with _REGISTRY_LOCK:
        data = shares_load()
        for s in data["shares"]:
            if s.get("project") == project and s.get("prototype") == prototype:
                return s, False
        rec = {
            "id":         "shr-" + secrets.token_hex(5),
            "token":      secrets.token_hex(16),
            "project":    project,
            "prototype":  prototype,
            "label":      (label or "").strip() or f"{project} / {prototype}",
            "emailGate":  bool(email_gate),
            "liveOnly":   bool(live_only),
            # A share can expose a stable (woven) link, a randomised (quick)
            # link, or BOTH at once - they are independent intents (quickOn /
            # wovenOn). New shares default to the stable link when a broker is
            # configured, else the randomised one. `mode` is kept as a derived
            # back-compat hint; share_modes() is the source of truth and migrates
            # legacy records (no quickOn/wovenOn) from `mode` + `active`.
            "mode":       ("woven" if WOVEN_BROKER_URL else "quick"),
            "quickOn":    (not WOVEN_BROKER_URL),
            "wovenOn":    bool(WOVEN_BROKER_URL),
            "active":     False,
            "createdAt":  _now_iso(),
            "lastUrl":    "",
            "prevUrl":    "",
            "lastUrlChangedAt": "",
            "lastStartedAt":    "",
        }
        data["shares"].append(rec)
        _shares_save(data)
        return rec, True


def share_update(share_id, patch):
    """Shallow-merge `patch` into the record. Returns the updated record or
    None if the id is unknown. Only fields in `patch` change."""
    with _REGISTRY_LOCK:
        data = shares_load()
        for s in data["shares"]:
            if s.get("id") == share_id:
                s.update(patch)
                _shares_save(data)
                return s
    return None


def share_delete(share_id):
    with _REGISTRY_LOCK:
        data = shares_load()
        before = len(data["shares"])
        rec = next((s for s in data["shares"] if s.get("id") == share_id), None)
        data["shares"] = [s for s in data["shares"] if s.get("id") != share_id]
        if len(data["shares"]) != before:
            _shares_save(data)
            # Best-effort thumbnail cleanup so a re-created share for the same
            # prototype doesn't show a stale preview.
            if rec is not None:
                try:
                    root = _RESOLVE_PROJECT_ROOT(rec.get("project") or "")
                    tp = share_thumbnail_abspath(root, rec.get("prototype"))
                    if os.path.isfile(tp):
                        os.remove(tp)
                except Exception:
                    pass
                # A hosted snapshot dies with its share (best-effort; the
                # broker's TTL reaper is the backstop).
                if rec.get("hostedOn") or rec.get("hostedAt"):
                    threading.Thread(target=_hosted_delete_worker,
                                     args=(rec.get("token") or "",),
                                     daemon=True, name="hosted-delete").start()
            return True
    return False


# ── Thumbnails - one PNG per shared prototype ────────────────────────────
# Captured by the daemon (headless Chrome) at share-create / start / source
# change, stored beside the comment store at <project_root>/share/thumb-
# <safe-slug>.png. The daemon owns capture (it has the Chrome helpers); this
# module only owns the canonical PATH so registry summaries + the capture
# code agree on where the file lives.

def share_thumbnail_relpath(prototype):
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", prototype or "main")
    return os.path.join("share", f"thumb-{safe}.png")


def share_thumbnail_abspath(project_root, prototype):
    return os.path.join(project_root, share_thumbnail_relpath(prototype))


# ═════════════════════════════════════════════════════════════════════════
# 2. Tunnels - cloudflared quick-tunnel subprocess per share
# ═════════════════════════════════════════════════════════════════════════

def find_cloudflared():
    """Locate the cloudflared binary. Our own tools/bin/ (direct-download
    install) FIRST, then PATH, then the usual install spots (brew on Apple
    Silicon / Intel, manual /usr/local). tools/bin/ is checked first so a
    machine with no Homebrew still resolves the daemon's own copy."""
    # editor/tools/bin/ - this file lives in editor/.
    tools_bin = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools", "bin")
    for ext in ("", ".exe"):
        cand = os.path.join(tools_bin, "cloudflared" + ext)
        if os.path.isfile(cand) and os.access(cand, os.X_OK):
            return cand
    p = shutil.which("cloudflared")
    if p:
        return p
    for cand in ("/opt/homebrew/bin/cloudflared", "/usr/local/bin/cloudflared",
                 "/usr/bin/cloudflared"):
        if os.path.isfile(cand) and os.access(cand, os.X_OK):
            return cand
    return None


class _Tunnel:
    """One cloudflared subprocess + its parsed state. State machine:
    starting → running (URL parsed) → exited / error (process died).
    `stopping` flags an intentional stop so the reader thread doesn't
    misreport a user-requested stop as an error."""
    __slots__ = ("share_id", "proc", "url", "state", "error",
                 "started_at", "stopping", "log_tail", "user_refresh")

    def __init__(self, share_id, proc):
        self.share_id   = share_id
        self.proc       = proc
        self.url        = ""
        self.state      = "starting"
        self.error      = ""
        self.started_at = time.time()
        self.stopping   = False
        self.log_tail   = []   # last ~30 log lines for error reporting
        # True when this (re)start was a user-initiated link refresh - the new
        # URL is then treated as already acknowledged, so it does NOT raise the
        # "Need refresh" badge (the user just did the refresh it was asking for).
        self.user_refresh = False


TUNNELS = {}                  # {share_id: _Tunnel}
_TUNNELS_LOCK = threading.Lock()


def _tunnel_reader(t):
    """Drains cloudflared's merged stdout/stderr. Responsibilities:
    parse the *.trycloudflare.com URL (→ state running + persist on the
    share record, detecting URL changes across restarts), keep a small
    log tail for diagnostics, and mark the tunnel exited/error when the
    process dies."""
    try:
        for line in iter(t.proc.stdout.readline, ""):
            if not line:
                break
            line = line.rstrip("\n")
            t.log_tail.append(line)
            if len(t.log_tail) > 30:
                t.log_tail.pop(0)
            if not t.url:
                m = _TUNNEL_URL_RE.search(line)
                if m:
                    t.url = m.group(0)
                    t.state = "running"
                    rec = share_get(t.share_id)
                    if rec is not None:
                        patch = {"lastUrl": t.url, "lastStartedAt": _now_iso()}
                        old = (rec.get("lastUrl") or "").strip()
                        if t.user_refresh:
                            # User just refreshed the link on purpose - this URL
                            # is already "the current one", so clear any pending
                            # change flag instead of raising it.
                            patch["prevUrl"] = ""
                        elif old and old != t.url:
                            patch["prevUrl"] = old
                            patch["lastUrlChangedAt"] = _now_iso()
                        share_update(t.share_id, patch)
                    print(f"[share] tunnel up for {t.share_id}: {t.url}", flush=True)
    except Exception:
        pass
    # Pipe closed → process is exiting (or already gone).
    try:
        t.proc.wait(timeout=5)
    except Exception:
        pass
    if t.stopping:
        t.state = "stopped"
    elif t.url:
        t.state = "exited"
        print(f"[share] tunnel for {t.share_id} exited", flush=True)
    else:
        t.state = "error"
        t.error = (t.log_tail[-1] if t.log_tail else "cloudflared exited before announcing a URL")
        print(f"[share] tunnel for {t.share_id} failed: {t.error}", flush=True)


def _quick_start(share_id, *, user_refresh=False):
    """Spawn (or reuse) the per-share quick cloudflared tunnel → gate port.
    user_refresh=True marks the new URL as already acknowledged (see _Tunnel)."""
    if GATE_PORT is None:
        raise RuntimeError("share gate server not started")
    binary = find_cloudflared()
    if not binary:
        raise RuntimeError("cloudflared not found - install it (macOS: brew install cloudflared)")
    with _TUNNELS_LOCK:
        t = TUNNELS.get(share_id)
        if t and t.proc.poll() is None:
            return t
        proc = subprocess.Popen(
            [binary, "tunnel", "--url", f"http://127.0.0.1:{GATE_PORT}",
             "--no-autoupdate"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1,
            # Detach from our TTY; cloudflared only needs the network.
            stdin=subprocess.DEVNULL,
        )
        t = _Tunnel(share_id, proc)
        t.user_refresh = user_refresh
        TUNNELS[share_id] = t
    threading.Thread(target=_tunnel_reader, args=(t,), daemon=True,
                     name=f"share-tunnel-{share_id}").start()
    print(f"[share] quick tunnel starting for {share_id} (pid {proc.pid}) → gate :{GATE_PORT}", flush=True)
    return t


def _quick_stop(share_id):
    """SIGTERM the per-share quick tunnel process (if any). Intent-agnostic."""
    with _TUNNELS_LOCK:
        t = TUNNELS.pop(share_id, None)
    if t is not None:
        t.stopping = True
        try: t.proc.terminate()
        except Exception: pass
        try: t.proc.wait(timeout=3)
        except Exception:
            try: t.proc.kill()
            except Exception: pass
    return t is not None


def _persist_modes(share_id, quick, woven):
    """Write the two independent intents (plus derived back-compat fields)."""
    share_update(share_id, {
        "quickOn": bool(quick),
        "wovenOn": bool(woven),
        "active":  bool(quick or woven),          # derived: any link wanted
        "mode":    ("woven" if woven else "quick"),  # legacy hint only
    })


def set_modes(share_id, *, quick=None, woven=None, user_refresh=False):
    """Set the share's two link intents independently (None = leave unchanged),
    then reconcile the running tunnels to match. Either, both, or neither may be
    on; with neither on the share is effectively stopped. Raises on tunnel
    failure (cloudflared/broker).

    user_refresh=True marks a freshly-spawned quick tunnel's URL as already
    acknowledged - used when the caller is a deliberate user toggle (flip the
    randomised link off then on), so re-minting the URL does NOT leave a stale
    "Need refresh" badge. Boot restore leaves it False on purpose: a URL that
    silently changed across a daemon restart SHOULD raise the badge."""
    rec = share_get(share_id)
    if rec is None:
        raise ValueError(f"unknown share: {share_id}")
    cur = share_modes(rec)
    q = cur["quick"] if quick is None else bool(quick)
    w = cur["woven"] if woven is None else bool(woven)
    # Persist intents FIRST so _woven_active_count() reflects the new state when
    # we decide whether to tear the shared tunnel down.
    _persist_modes(share_id, q, w)
    if q:
        _quick_start(share_id, user_refresh=user_refresh)
    else:
        _quick_stop(share_id)
    if w:
        _woven_tunnel_start()
        share_update(share_id, {"lastStartedAt": _now_iso()})
    elif _woven_active_count() == 0:
        _woven_tunnel_stop()
    return share_get(share_id)


def refresh_quick(share_id):
    """User-initiated link refresh: restart the quick tunnel to mint a fresh
    randomised URL and mark it acknowledged, so the "Need refresh" badge clears
    (the user just performed the refresh the badge was asking for). The old link
    stops working, exactly like the ↻ regenerate did before."""
    rec = share_get(share_id)
    if rec is None:
        raise ValueError(f"unknown share: {share_id}")
    _quick_stop(share_id)
    _persist_modes(share_id, True, share_modes(rec)["woven"])
    _quick_start(share_id, user_refresh=True)
    return share_get(share_id)


def tunnel_start(share_id):
    """One-click publish: start every enabled link, defaulting to one when none
    is set yet (stable if a broker is configured, else randomised). Idempotent."""
    rec = share_get(share_id)
    if rec is None:
        raise ValueError(f"unknown share: {share_id}")
    m = share_modes(rec)
    if not m["quick"] and not m["woven"]:
        if WOVEN_BROKER_URL: m["woven"] = True
        else: m["quick"] = True
    return set_modes(share_id, quick=m["quick"], woven=m["woven"])


def tunnel_stop(share_id, *, keep_intent=False):
    """Stop BOTH links for the share. keep_intent=True leaves the intents as-is
    (used during shutdown so boot-time restore re-opens user-wanted tunnels);
    the normal Stop button clears both."""
    if not keep_intent:
        _persist_modes(share_id, False, False)
    stopped = _quick_stop(share_id)
    # Tear the shared woven tunnel down only when no woven share wants it.
    if _woven_active_count() == 0:
        if _woven_tunnel_stop():
            stopped = True
    return stopped


def stop_all_tunnels():
    with _TUNNELS_LOCK:
        ids = list(TUNNELS.keys())
    for sid in ids:
        _quick_stop(sid)
    if ids:
        print(f"[share] stopped {len(ids)} tunnel(s) on shutdown", flush=True)
    # The shared woven tunnel isn't in TUNNELS - stop it too (intents persist so
    # active woven shares are restored on next boot).
    if _woven_tunnel_stop():
        print("[share] stopped woven tunnel on shutdown", flush=True)


def restore_active_tunnels():
    """Boot-time: restart every link a share still wants (quickOn / wovenOn).
    Quick-tunnel URLs WILL differ - the reader thread records prevUrl/
    lastUrlChangedAt so the UI can flag it."""
    # Hosted snapshots live broker-side and need nothing restarted - just the
    # heartbeat that keeps the reaper away. Independent of cloudflared.
    if any(share_hosted_on(s) for s in shares_load().get("shares", [])):
        ensure_hosted_heartbeat()
    if not find_cloudflared():
        actives = [s for s in shares_load().get("shares", [])
                   if share_modes(s)["quick"] or share_modes(s)["woven"]]
        if actives:
            print(f"[share] {len(actives)} share(s) want a link but cloudflared "
                  "is not installed - tunnels NOT restored", flush=True)
        return
    for s in shares_load().get("shares", []):
        m = share_modes(s)
        if m["quick"] or m["woven"]:
            try:
                set_modes(s["id"], quick=m["quick"], woven=m["woven"])
            except Exception as e:
                print(f"[share] failed to restore tunnel for {s.get('id')}: {e}", flush=True)


def _quick_status(rec):
    """Liveness + URL of the per-share quick tunnel. Status values:
    running / starting / stopped / exited / error / no-cloudflared."""
    with _TUNNELS_LOCK:
        t = TUNNELS.get(rec.get("id"))
    if t is not None and t.proc.poll() is None:
        status = "running" if t.url else "starting"
        return {"status": status, "url": t.url or "", "pid": t.proc.pid, "error": ""}
    if t is not None:
        status = t.state if t.state in ("error", "exited", "stopped") else "stopped"
        return {"status": status, "url": "", "pid": None, "error": t.error or ""}
    if share_modes(rec)["quick"] and not find_cloudflared():
        return {"status": "no-cloudflared", "url": "", "pid": None,
                "error": "cloudflared binary not found"}
    return {"status": "stopped", "url": "", "pid": None, "error": ""}


def tunnel_status(rec):
    """Overall liveness for a share, folding both links (running wins). Kept for
    back-compat; share_summary computes the per-link detail directly."""
    modes = share_modes(rec)
    sts = []
    if modes["quick"]: sts.append(_quick_status(rec))
    if modes["woven"]: sts.append(_woven_status(rec))
    if not sts:
        return {"status": "stopped", "url": "", "pid": None, "error": ""}
    for want in ("running", "starting"):
        for s in sts:
            if s["status"] == want:
                return s
    return sts[0]


# ═════════════════════════════════════════════════════════════════════════
# 2b. Woven mode - one stable named tunnel per install, shared by all woven shares
# ═════════════════════════════════════════════════════════════════════════

def share_mode(rec):
    """A record's primary tunnel mode (back-compat hint). Prefer share_modes()."""
    m = share_modes(rec)
    return "woven" if m["woven"] else "quick"


def share_modes(rec):
    """The two independent link intents for a share: {"quick": bool, "woven": bool}.
    Source of truth = the quickOn/wovenOn fields. Legacy records (written before
    both-links support) carry only `mode` + `active`, so derive from those."""
    rec = rec or {}
    if "quickOn" in rec or "wovenOn" in rec:
        return {"quick": bool(rec.get("quickOn")), "woven": bool(rec.get("wovenOn"))}
    active = bool(rec.get("active"))
    woven = active and rec.get("mode") == "woven"
    quick = active and rec.get("mode") != "woven"
    return {"quick": quick, "woven": woven}


def woven_install_id():
    """Stable per-install identity that the broker maps to a fixed subdomain.
    Persisted to ~/.woven/install-id so the URL survives daemon restarts; the
    ONLY thing whose loss changes a user's stable URL. 32 hex chars to match the
    broker's installId validation."""
    os.makedirs(WOVEN_DIR, exist_ok=True)
    p = os.path.join(WOVEN_DIR, "install-id")
    try:
        with open(p, "r", encoding="utf-8") as f:
            iid = f.read().strip()
        if INSTALL_ID_RE.match(iid):
            return iid
    except OSError:
        pass
    iid = secrets.token_hex(16)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(iid)
    os.replace(tmp, p)
    return iid


def _woven_state_path():
    return os.path.join(WOVEN_DIR, "woven.json")


def _woven_state_load():
    try:
        with open(_woven_state_path(), "r", encoding="utf-8") as f:
            d = json.load(f) or {}
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _woven_state_save(d):
    os.makedirs(WOVEN_DIR, exist_ok=True)
    tmp = _woven_state_path() + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2)
    os.replace(tmp, _woven_state_path())


def _woven_creds_path(tunnel_id):
    return os.path.join(WOVEN_DIR, f"{tunnel_id}.json")


def woven_base_url():
    """https://<install>.getwoven.design once provisioned, else "" - the base
    every woven share's link is built on (base + /s/<token>/)."""
    host = (_woven_state_load().get("hostname") or "").strip()
    return ("https://" + host) if host else ""


def _woven_provision(install_id):
    """Ask the broker for this install's tunnel. Returns {hostname, tunnelId,
    credentials}. Raises RuntimeError with a readable message on failure."""
    body = json.dumps({"installId": install_id}).encode("utf-8")
    req = urllib.request.Request(
        WOVEN_BROKER_URL + "/provision", data=body,
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = (json.load(e) or {}).get("detail") or e.read().decode("utf-8", "ignore")
        except Exception:
            pass
        raise RuntimeError(f"broker /provision failed ({e.code}): {detail or e.reason}")
    except Exception as e:
        raise RuntimeError(f"broker unreachable at {WOVEN_BROKER_URL}: {e}")
    if not (data.get("hostname") and data.get("tunnelId") and data.get("credentials")):
        raise RuntimeError(f"broker returned an incomplete provision response: {data}")
    return data


def _woven_ensure_credentials():
    """Make sure we hold a usable credentials file + hostname for this install.
    First run (or lost creds) calls the broker once and caches the result; every
    later run reuses the cache and never touches the broker. Returns the state
    dict {installId, hostname, tunnelId}."""
    install_id = woven_install_id()
    state = _woven_state_load()
    tid = state.get("tunnelId")
    if (state.get("installId") == install_id and state.get("hostname") and tid
            and os.path.isfile(_woven_creds_path(tid))):
        return state
    res = _woven_provision(install_id)
    tid = res["tunnelId"]
    cp = _woven_creds_path(tid)
    tmp = cp + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(res["credentials"], f)
    os.replace(tmp, cp)
    state = {"installId": install_id, "hostname": res["hostname"], "tunnelId": tid}
    _woven_state_save(state)
    print(f"[share] woven install provisioned: {res['hostname']}", flush=True)
    return state


def _woven_write_config(state):
    """Write the local cloudflared config that maps our stable hostname to the
    gate port. config_src is 'local' broker-side, so the CLIENT owns ingress -
    we regenerate this each start with the CURRENT gate port."""
    cp = os.path.join(WOVEN_DIR, "config.yml")
    cfg = (
        f"tunnel: {state['tunnelId']}\n"
        f"credentials-file: {_woven_creds_path(state['tunnelId'])}\n"
        f"no-autoupdate: true\n"
        f"ingress:\n"
        f"  - hostname: {state['hostname']}\n"
        f"    service: http://127.0.0.1:{GATE_PORT}\n"
        f"  - service: http_status:404\n"
    )
    tmp = cp + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(cfg)
    os.replace(tmp, cp)
    return cp


class _WovenTunnel:
    """The single shared named-tunnel process for this install. starting →
    running (a connection registered) → exited / error. Unlike a quick tunnel
    its URL is known up front (the provisioned hostname)."""
    __slots__ = ("proc", "url", "state", "error", "started_at", "stopping", "log_tail")

    def __init__(self, proc, url):
        self.proc       = proc
        self.url        = url
        self.state      = "starting"
        self.error      = ""
        self.started_at = time.time()
        self.stopping   = False
        self.log_tail   = []


_WOVEN = None                  # the single _WovenTunnel (or None)
_WOVEN_LOCK = threading.Lock()
_WOVEN_CONN_RE = re.compile(r"[Rr]egistered tunnel connection|Connection .* registered")


def _woven_reader(t):
    """Drain the named tunnel's output: flip to running once a connection
    registers, keep a log tail, classify exit."""
    try:
        for line in iter(t.proc.stdout.readline, ""):
            if not line:
                break
            line = line.rstrip("\n")
            t.log_tail.append(line)
            if len(t.log_tail) > 30:
                t.log_tail.pop(0)
            if t.state == "starting" and _WOVEN_CONN_RE.search(line):
                t.state = "running"
                print(f"[share] woven tunnel up: {t.url}", flush=True)
    except Exception:
        pass
    try:
        t.proc.wait(timeout=5)
    except Exception:
        pass
    if t.stopping:
        t.state = "stopped"
    elif t.state == "running":
        t.state = "exited"
        print("[share] woven tunnel exited", flush=True)
    else:
        t.state = "error"
        t.error = (t.log_tail[-1] if t.log_tail else "cloudflared exited before connecting")
        print(f"[share] woven tunnel failed: {t.error}", flush=True)


def _woven_heartbeat_loop(t):
    """While the named tunnel is alive, ping /heartbeat periodically so the
    broker's reaper leaves this install's tunnel in place. Best-effort."""
    iid = woven_install_id()
    while True:
        slept = 0
        while slept < _WOVEN_HEARTBEAT_INTERVAL:
            time.sleep(30)
            slept += 30
            with _WOVEN_LOCK:
                if _WOVEN is not t or t.proc.poll() is not None:
                    return
        try:
            body = json.dumps({"installId": iid}).encode("utf-8")
            req = urllib.request.Request(
                WOVEN_BROKER_URL + "/heartbeat", data=body,
                headers={"Content-Type": "application/json"}, method="POST")
            urllib.request.urlopen(req, timeout=15).close()
        except Exception:
            pass


def _woven_foreign_connector_pids():
    """PIDs of cloudflared connectors for THIS install's named tunnel that were
    NOT spawned by this daemon. The named tunnel is a machine-global singleton
    (one stable hostname routing to ONE gate port): when a second daemon starts
    its own connector, Cloudflare balances the hostname across both and every
    share minted by the first daemon 404s as "unknown or revoked" on the gate
    of the second. First daemon wins; later daemons must skip - and must NOT
    rewrite ~/.woven/config.yml to their own gate port."""
    cfg = os.path.join(WOVEN_DIR, "config.yml")
    own = None
    if _WOVEN is not None and _WOVEN.proc.poll() is None:
        own = _WOVEN.proc.pid
    try:
        out = subprocess.run(["pgrep", "-f", cfg],
                             capture_output=True, text=True, timeout=5).stdout
    except Exception:
        return []
    pids = []
    for line in out.splitlines():
        line = line.strip()
        if line.isdigit():
            pid = int(line)
            if pid not in (own, os.getpid()):
                pids.append(pid)
    return pids


def _woven_tunnel_start():
    """Ensure the single shared named tunnel is running (idempotent).
    Provisions credentials on first use. Raises on cloudflared/broker failure,
    and when another daemon on this machine already owns the tunnel."""
    global _WOVEN
    if GATE_PORT is None:
        raise RuntimeError("share gate server not started")
    binary = find_cloudflared()
    if not binary:
        raise RuntimeError("cloudflared not found - install it (macOS: brew install cloudflared)")
    with _WOVEN_LOCK:
        ours = _WOVEN is not None and _WOVEN.proc.poll() is None
    if not ours:
        foreign = _woven_foreign_connector_pids()
        if foreign:
            raise RuntimeError(
                "another Woven daemon on this machine already runs the stable share "
                f"tunnel (cloudflared pid {foreign[0]}); the stable hostname can only "
                "route to one daemon at a time. Manage woven links from that daemon, "
                "or use the quick link here.")
    state = _woven_ensure_credentials()          # may call the broker (first run only)
    cfg = _woven_write_config(state)
    with _WOVEN_LOCK:
        if _WOVEN is not None and _WOVEN.proc.poll() is None:
            return _WOVEN
        proc = subprocess.Popen(
            [binary, "--config", cfg, "tunnel", "run"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1, stdin=subprocess.DEVNULL,
        )
        t = _WovenTunnel(proc, "https://" + state["hostname"])
        _WOVEN = t
    threading.Thread(target=_woven_reader, args=(t,), daemon=True,
                     name="woven-tunnel").start()
    threading.Thread(target=_woven_heartbeat_loop, args=(t,), daemon=True,
                     name="woven-heartbeat").start()
    print(f"[share] woven tunnel starting (pid {proc.pid}) → gate :{GATE_PORT}", flush=True)
    return t


def _woven_tunnel_stop():
    with _WOVEN_LOCK:
        global _WOVEN
        t, _WOVEN = _WOVEN, None
    if t is not None:
        t.stopping = True
        try: t.proc.terminate()
        except Exception: pass
        try: t.proc.wait(timeout=3)
        except Exception:
            try: t.proc.kill()
            except Exception: pass
    return t is not None


def _woven_active_count():
    """How many shares currently want the stable link - the shared named tunnel
    runs iff this is > 0."""
    return sum(1 for s in shares_load().get("shares", [])
               if share_modes(s)["woven"])


def _woven_status(rec):
    """tunnel_status() equivalent for a share's STABLE link - liveness comes from
    the single shared tunnel, the URL is this install's stable base. Keyed on the
    woven intent (not the generic active flag) so a quick-only share never reads
    as having a live stable link."""
    if not share_modes(rec)["woven"]:
        return {"status": "stopped", "url": "", "pid": None, "error": ""}
    base = woven_base_url()
    with _WOVEN_LOCK:
        t = _WOVEN
    alive = t is not None and t.proc.poll() is None
    if alive:
        status = "running" if t.state == "running" else "starting"
        return {"status": status, "url": base if status == "running" else "",
                "pid": t.proc.pid, "error": ""}
    if not find_cloudflared():
        return {"status": "no-cloudflared", "url": "", "pid": None,
                "error": "cloudflared binary not found"}
    if t is not None and t.state == "error":
        return {"status": "error", "url": "", "pid": None, "error": t.error or ""}
    return {"status": "stopped", "url": "", "pid": None, "error": ""}


def share_set_mode(share_id, mode):
    """Legacy single-mode switch - sets the chosen link on and the other off.
    Prefer set_modes() for independent control."""
    if mode == "woven":
        return set_modes(share_id, quick=False, woven=True)
    return set_modes(share_id, quick=True, woven=False)


# ═════════════════════════════════════════════════════════════════════════
# 2c. Hosted mode - snapshot uploaded to Woven storage, served with the
#     daemon OFF. Same stable URL as the woven link: the share worker on
#     *.getwoven.design/s/* prefers the R2 snapshot and falls through to the
#     tunnel when none exists. Toggle off = the snapshot is deleted broker-
#     side, so hosting never accumulates storage. See worker/ + broker/.
# ═════════════════════════════════════════════════════════════════════════

_HOSTED_JOBS = {}                 # share_id -> {"state","error","startedAt"}
_HOSTED_JOBS_LOCK = threading.Lock()
_HOSTED_HB_STARTED = False

# Hosting passcode - REQUIRED by the broker for snapshot uploads. The browser
# owns it (localStorage) and sends it with every hosted toggle / update; the
# daemon keeps it ONLY in memory for this process (so a background re-upload
# can reuse it) and never writes it to shares.json or any file.
_HOSTED_PASSCODE = ""

# Per-file ceiling inside a snapshot - anything bigger is skipped with a log
# line rather than sinking the whole upload (broker also caps the totals).
_HOSTED_FILE_MAX = 100 * 1024 * 1024


def share_hosted_on(rec):
    return bool((rec or {}).get("hostedOn"))


def _hosted_job_set(share_id, state, error=""):
    with _HOSTED_JOBS_LOCK:
        _HOSTED_JOBS[share_id] = {"state": state, "error": error,
                                  "startedAt": time.time()}


def _hosted_job_get(share_id):
    with _HOSTED_JOBS_LOCK:
        return dict(_HOSTED_JOBS.get(share_id) or {})


def _hosted_add_tree(tf, src_dir, arc_prefix):
    """Add every gate-servable file under src_dir to the tar (same extension
    whitelist + dotfile rules the tunnel gate enforces, so hosting can never
    expose more than tunnelling does)."""
    count = 0
    for root, dirs, files in os.walk(src_dir):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for name in sorted(files):
            if name.startswith("."):
                continue
            ext = os.path.splitext(name)[1].lower()
            if ext not in _GATE_SERVE_EXTS:
                continue
            p = os.path.join(root, name)
            try:
                if os.path.getsize(p) > _HOSTED_FILE_MAX:
                    print(f"[share] hosted snapshot skipping oversized file: {p}", flush=True)
                    continue
                rel = os.path.relpath(p, src_dir).replace(os.sep, "/")
                tf.add(p, arcname=arc_prefix + "/" + rel, recursive=False)
                count += 1
            except OSError:
                continue
    return count


def _hosted_build_snapshot(rec, out_path):
    """Build the snapshot tar.gz at out_path. Members mirror the gate's URL
    space under share/ (viewer shell, static api/meta, whitelisted project
    files) plus the workspace fonts under fonts/. Returns the file count."""
    import io as _io
    import tarfile

    project_root = _RESOLVE_PROJECT_ROOT(rec.get("project") or "")
    slug = rec.get("prototype") or ""
    count = 0

    def add_bytes(tf, arcname, data):
        info = tarfile.TarInfo(arcname)
        info.size = len(data)
        info.mtime = int(time.time())
        tf.addfile(info, _io.BytesIO(data))

    with tarfile.open(out_path, "w:gz") as tf:
        # Viewer shell - the same review page the tunnel gate serves at /s/<t>/.
        share_dir = os.path.join(INSTALL_ROOT, "editor", "share")
        for src, arc in (
            (os.path.join(share_dir, "viewer.html"), "share/index.html"),
            (os.path.join(share_dir, "viewer.js"),   "share/viewer.js"),
            (os.path.join(share_dir, "viewer.css"),  "share/viewer.css"),
            (os.path.join(INSTALL_ROOT, "editor", "favicon.svg"), "share/favicon.svg"),
        ):
            if os.path.isfile(src):
                tf.add(src, arcname=arc, recursive=False)
                count += 1
        # Static /api/meta so the viewer boots with the daemon offline.
        meta = {
            "label":     rec.get("label") or "",
            "prototype": slug,
            "emailGate": bool(rec.get("emailGate")),
            "entry":     "p/source/{}/index.html".format(slug),
        }
        add_bytes(tf, "share/api/meta", json.dumps(meta).encode("utf-8"))
        # Hosted marker - the worker treats its presence as "this share is
        # hosted" (static misses become real 404s instead of tunnel fallthrough).
        add_bytes(tf, "share/__hosted.json", json.dumps({
            "uploadedAt": _now_iso(),
            "prototype":  slug,
            "label":      rec.get("label") or "",
        }).encode("utf-8"))
        count += 2
        # The prototype tree + the design-system library it links - exactly the
        # two prefixes _gate_project_paths_ok() allows.
        src_tree = os.path.join(project_root, "source", slug)
        if not os.path.isdir(src_tree):
            raise RuntimeError("prototype has no source/{}/ directory".format(slug))
        count += _hosted_add_tree(tf, src_tree, "share/p/source/" + slug)
        ds_tree = os.path.join(project_root, "design-systems")
        if os.path.isdir(ds_tree):
            count += _hosted_add_tree(tf, ds_tree, "share/p/design-systems")
        # Workspace fonts - DS stylesheets reference /__global_fonts/<name>
        # root-absolute; the worker serves them from fonts/<install>/.
        fonts_dir = os.path.join(WORKSPACE_DIR or INSTALL_ROOT, "fonts")
        if os.path.isdir(fonts_dir):
            for name in sorted(os.listdir(fonts_dir)):
                p = os.path.join(fonts_dir, name)
                if (os.path.isfile(p) and NAME_SAFE.match(name)
                        and not name.startswith(".")
                        and os.path.getsize(p) <= _HOSTED_FILE_MAX):
                    tf.add(p, arcname="fonts/" + name, recursive=False)
                    count += 1
    return count


def _hosted_broker_post(path, data=None, timeout=30, content_type="application/json",
                        passcode=None):
    headers = {"Content-Type": content_type}
    if passcode:
        headers["X-Woven-Passcode"] = passcode
    req = urllib.request.Request(
        WOVEN_BROKER_URL + path, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = (json.load(e) or {}).get("detail") or ""
        except Exception:
            pass
        raise RuntimeError("broker {} failed ({}): {}".format(
            path, e.code, detail or e.reason))
    except Exception as e:
        raise RuntimeError("broker unreachable at {}: {}".format(WOVEN_BROKER_URL, e))


def _hosted_upload_worker(share_id):
    """Background: build the snapshot and push it to the broker. Status lands
    in _HOSTED_JOBS; the share record gets hostedAt/hostedBytes on success."""
    import tempfile
    rec = share_get(share_id)
    if rec is None:
        return
    tmp = None
    try:
        fd, tmp = tempfile.mkstemp(suffix=".tar.gz", prefix="woven-share-")
        os.close(fd)
        _hosted_build_snapshot(rec, tmp)
        with open(tmp, "rb") as f:
            body = f.read()
        qs = urllib.parse.urlencode({
            "installId": woven_install_id(),
            "token":     rec.get("token") or "",
            "prototype": rec.get("prototype") or "",
            "label":     rec.get("label") or "",
        })
        res = _hosted_broker_post("/shares/upload?" + qs, data=body,
                                  timeout=600, content_type="application/gzip",
                                  passcode=_HOSTED_PASSCODE)
        share_update(share_id, {
            "hostedAt":    _now_iso(),
            "hostedBytes": int(res.get("bytes") or 0),
            "hostedFiles": int(res.get("files") or 0),
        })
        _hosted_job_set(share_id, "done")
        print("[share] hosted snapshot uploaded for {} ({} files, {} bytes)".format(
            share_id, res.get("files"), res.get("bytes")), flush=True)
    except Exception as e:
        _hosted_job_set(share_id, "error", str(e))
        print("[share] hosted upload failed for {}: {}".format(share_id, e), flush=True)
    finally:
        if tmp:
            try:
                os.unlink(tmp)
            except OSError:
                pass


def _hosted_delete_worker(token):
    try:
        body = json.dumps({"installId": woven_install_id(),
                           "token": token}).encode("utf-8")
        _hosted_broker_post("/shares/delete", data=body, timeout=60)
        print("[share] hosted snapshot deleted", flush=True)
    except Exception as e:
        # Best-effort: the broker's TTL reaper is the backstop.
        print("[share] hosted delete failed (reaper will collect it): {}".format(e), flush=True)


def hosted_passcode_verify(passcode):
    """True iff the broker accepts this hosting passcode. Cheap pre-flight so a
    wrong code fails in milliseconds instead of after a snapshot upload."""
    body = json.dumps({"passcode": passcode or ""}).encode("utf-8")
    try:
        res = _hosted_broker_post("/shares/passcode_check", data=body, timeout=15)
        return bool(res.get("ok"))
    except RuntimeError as e:
        # 403 = limiter tripped; anything else is a reachability problem the
        # caller should see as-is.
        if "403" in str(e):
            return False
        raise


def set_hosted(share_id, on, passcode=None):
    """Flip the hosted-snapshot intent. ON requires a valid hosting passcode
    (broker-verified - the codes live server-side, never in this repo), then
    provisions the stable hostname if needed (broker HTTP only - no tunnel, no
    cloudflared required) and uploads in the background. OFF deletes the
    snapshot broker-side and needs no passcode."""
    global _HOSTED_PASSCODE
    rec = share_get(share_id)
    if rec is None:
        raise ValueError("unknown share: {}".format(share_id))
    if rec.get("liveOnly"):
        raise ValueError("a multiplayer session cannot be hosted - it is inherently live")
    if not WOVEN_BROKER_URL:
        raise RuntimeError("hosted shares need the Woven broker configured")
    if on:
        code = (passcode or "").strip() or _HOSTED_PASSCODE
        if not hosted_passcode_verify(code):
            raise PermissionError(
                "A valid hosting passcode is required to publish on getwoven.design.")
        _HOSTED_PASSCODE = code            # memory only - never persisted
        # The hosted URL is the same stable hostname the woven tunnel uses -
        # make sure this install has one (first call asks the broker once).
        _woven_ensure_credentials()
        share_update(share_id, {"hostedOn": True})
        hosted_update(share_id)
        ensure_hosted_heartbeat()
    else:
        token = rec.get("token") or ""
        share_update(share_id, {"hostedOn": False, "hostedAt": "",
                                "hostedBytes": 0, "hostedFiles": 0})
        with _HOSTED_JOBS_LOCK:
            _HOSTED_JOBS.pop(share_id, None)
        threading.Thread(target=_hosted_delete_worker, args=(token,),
                         daemon=True, name="hosted-delete").start()
    return share_get(share_id)


def hosted_update(share_id, passcode=None):
    """(Re)upload the snapshot - the Update button, and the ON half of the
    toggle. No-op unless the share wants hosting. A passcode argument refreshes
    the in-memory code (e.g. after a daemon restart); without one the cached
    code is used and the broker rejects the upload if it has gone stale."""
    global _HOSTED_PASSCODE
    rec = share_get(share_id)
    if rec is None:
        raise ValueError("unknown share: {}".format(share_id))
    if not share_hosted_on(rec):
        raise ValueError("share is not hosted - turn hosting on first")
    # Pre-flight the passcode on EVERY (re)upload, not just toggle-on: a code
    # revoked broker-side would otherwise fail silently in the background
    # thread with no way for the UI to re-prompt.
    code = (passcode or "").strip() or _HOSTED_PASSCODE
    if not code or not hosted_passcode_verify(code):
        raise PermissionError(
            "A valid hosting passcode is required to publish on getwoven.design.")
    _HOSTED_PASSCODE = code                          # memory only - never persisted
    job = _hosted_job_get(share_id)
    if job.get("state") == "uploading":
        return rec                                   # already in flight
    _hosted_job_set(share_id, "uploading")
    threading.Thread(target=_hosted_upload_worker, args=(share_id,),
                     daemon=True, name="hosted-upload-" + share_id).start()
    return rec


def hosted_status(rec):
    """{"status": off|uploading|hosted|error, "url", "error", "at", "bytes"}."""
    if not share_hosted_on(rec):
        return {"status": "off", "url": "", "error": "", "at": "", "bytes": 0}
    base = woven_base_url()
    url = (base.rstrip("/") + "/s/" + (rec.get("token") or "") + "/") if base else ""
    job = _hosted_job_get(rec.get("id") or "")
    if job.get("state") == "uploading":
        return {"status": "uploading", "url": url, "error": "",
                "at": rec.get("hostedAt") or "", "bytes": int(rec.get("hostedBytes") or 0)}
    if job.get("state") == "error":
        return {"status": "error", "url": url, "error": job.get("error") or "",
                "at": rec.get("hostedAt") or "", "bytes": int(rec.get("hostedBytes") or 0)}
    if rec.get("hostedAt"):
        return {"status": "hosted", "url": url, "error": "",
                "at": rec.get("hostedAt") or "", "bytes": int(rec.get("hostedBytes") or 0)}
    # Intent on but never uploaded (e.g. daemon died mid-upload) - resumable.
    return {"status": "error", "url": url,
            "error": "snapshot not uploaded yet - press Update",
            "at": "", "bytes": 0}


def _hosted_heartbeat_loop():
    """Keep the broker's HOSTED_TTL reaper away while any share is hosted -
    independent of the woven tunnel (hosting works with the tunnel off)."""
    while True:
        try:
            if any(share_hosted_on(s) for s in shares_load().get("shares", [])):
                body = json.dumps({"installId": woven_install_id()}).encode("utf-8")
                req = urllib.request.Request(
                    WOVEN_BROKER_URL + "/heartbeat", data=body,
                    headers={"Content-Type": "application/json"}, method="POST")
                urllib.request.urlopen(req, timeout=15).close()
        except Exception:
            pass
        time.sleep(_WOVEN_HEARTBEAT_INTERVAL)


# ── Offline comment inbox sync ─────────────────────────────────────────────
# Comments visitors leave on a hosted share while this daemon is OFF queue at
# the broker (worker → /shares/inbox). This loop pulls them, merges them into
# the project's comments.json (same shape + locks the gate uses), then acks so
# the broker deletes them. Two-phase pull/ack: a crash mid-merge re-delivers
# next round, and the id-dedup makes redelivery harmless.

_HOSTED_INBOX_INTERVAL = 120   # seconds between pulls while any share is hosted


def _hosted_inbox_apply(item):
    """Merge ONE pulled inbox item into its project's comment store. Returns
    "applied" (merged), "drop" (permanently unusable / duplicate - ack without
    merging), or "retry" (temporary failure - leave in the inbox)."""
    token = item.get("token") or ""
    payload = item.get("comment")
    rec = share_get_by_token(token)
    if rec is None or rec.get("liveOnly") or not isinstance(payload, dict):
        return "drop"                    # share gone / bogus - drop from inbox
    cid = payload.get("id") or ""
    if not COMMENT_ID_OK.match(cid):
        return "drop"
    try:
        root = _RESOLVE_PROJECT_ROOT(rec.get("project") or "")
    except Exception:
        return "retry"                   # project temporarily unavailable
    text = _clip(payload.get("text"), 5000).strip()
    if not text:
        return "drop"
    anchor = payload.get("anchor") if isinstance(payload.get("anchor"), dict) else {}
    pin = payload.get("pin") if isinstance(payload.get("pin"), dict) else {}

    def _frac(v):
        try:
            return max(0.0, min(1.0, float(v)))
        except (TypeError, ValueError):
            return 0.5

    entry = {
        "id":        cid,
        "prototype": rec.get("prototype") or "",
        "page":      _clip(payload.get("page"), 500) or "index.html",
        "anchor": {
            "selector": _clip(anchor.get("selector"), 1000),
            "tag":      _clip(anchor.get("tag"), 40),
            "text":     _clip(anchor.get("text"), 200),
        },
        "pin":       {"x": _frac(pin.get("x", 0.5)), "y": _frac(pin.get("y", 0.5))},
        "text":      text,
        "author":    _clean_author(payload.get("author")),
        "createdAt": _clip(payload.get("createdAt"), 40) or _now_iso(),
        "status":    "open",
        "processedAt": "",
        "replies":   [],
        "shot":      "",
        "shotAt":    "",
        "attachments": [],
        "viaInbox":  True,               # arrived while this daemon was offline
    }
    with _COMMENTS_LOCK:
        data = comments_load(root)
        if any(c.get("id") == cid for c in data.get("comments", [])):
            return "drop"                # redelivery - already merged
        data["comments"].append(entry)
        _comments_save(root, data)
    _notify_comments_changed(rec.get("project"), rec.get("prototype"))
    return "applied"


def hosted_inbox_sync():
    """One pull/merge/ack round. Returns the number of comments applied."""
    iid = woven_install_id()
    body = json.dumps({"installId": iid}).encode("utf-8")
    res = _hosted_broker_post("/shares/inbox_pull", data=body, timeout=30)
    items = res.get("items") or []
    if not items:
        return 0
    acked = []
    applied = 0
    for item in items:
        try:
            outcome = _hosted_inbox_apply(item)
            if outcome != "retry":
                acked.append(int(item.get("inboxId")))
            if outcome == "applied":
                applied += 1
        except Exception as e:
            print("[share] inbox item failed (will retry): {}".format(e), flush=True)
    if acked:
        ack = json.dumps({"installId": iid, "ids": acked}).encode("utf-8")
        _hosted_broker_post("/shares/inbox_ack", data=ack, timeout=30)
    if applied:
        print("[share] collected {} offline comment(s) from the inbox".format(applied), flush=True)
    return applied


def _hosted_inbox_loop():
    while True:
        try:
            if any(share_hosted_on(s) for s in shares_load().get("shares", [])):
                hosted_inbox_sync()
        except Exception:
            pass
        time.sleep(_HOSTED_INBOX_INTERVAL)


def ensure_hosted_heartbeat():
    """Start the hosted heartbeat + inbox-sync threads once (boot + first
    toggle-on). The inbox loop runs its first pull within seconds, so comments
    left while the daemon was off land shortly after boot."""
    global _HOSTED_HB_STARTED
    if _HOSTED_HB_STARTED or not WOVEN_BROKER_URL:
        return
    _HOSTED_HB_STARTED = True
    threading.Thread(target=_hosted_heartbeat_loop, daemon=True,
                     name="hosted-heartbeat").start()
    threading.Thread(target=_hosted_inbox_loop, daemon=True,
                     name="hosted-inbox").start()


# ═════════════════════════════════════════════════════════════════════════
# 3. Comments - per-project store, shared by gate + editor endpoints
# ═════════════════════════════════════════════════════════════════════════

def _comments_path(project_root):
    return os.path.join(project_root, "share", "comments.json")


def comments_load(project_root):
    p = _comments_path(project_root)
    if not os.path.isfile(p):
        return {"comments": []}
    try:
        with open(p, "r", encoding="utf-8") as f:
            raw = f.read()
    except Exception:
        return {"comments": []}
    try:
        data = json.loads(raw) or {}
    except Exception:
        # A git merge that baked conflict markers into the file would otherwise
        # read as "every comment vanished". Recover by splitting the marker
        # hunks into the two sides and semantically merging them (in-memory
        # only - the next comment write persists the healed structure, and the
        # git resolve path stages its own merge).
        data = _comments_from_conflict_text(raw)
        if data is None:
            return {"comments": []}
    if not isinstance(data, dict):
        return {"comments": []}
    data.setdefault("comments", [])
    if not isinstance(data["comments"], list):
        data["comments"] = []
    return data


def _comments_save(project_root, data):
    p = _comments_path(project_root)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, p)


# ── Comment sync (git) ───────────────────────────────────────────────────────
# share/comments.json rides each project's git sync - it is deliberately NOT in
# the daemon's per-project .gitignore set, so commit/push/pull carry the review
# comments (and their share/comment-shots/ + share/comment-attach/ files)
# across machines. But two machines can both append comments between syncs,
# and a single JSON array line-merges into a conflict git can't resolve.
# These helpers do the SEMANTIC merge instead: union comments by id, union
# replies/attachments by id inside a comment, resolve scalar fields 3-way
# (the side that changed a field vs base wins; ours wins when both changed;
# a deletion on either side wins over the stale copy). serve.py feeds the
# conflict stages of share/comments.json through comments_merge_texts() after
# pull / branch-merge and stages the result, so comment traffic never needs
# hand-merging.

def _comments_of_text(text):
    """The comments list encoded in one side's file content ([] when blank or
    unparseable - the merge then just keeps the other side)."""
    try:
        data = json.loads(text or "") or {}
    except Exception:
        return []
    if not isinstance(data, dict):
        return []
    cs = data.get("comments")
    return [c for c in cs if isinstance(c, dict)] if isinstance(cs, list) else []


def _union_subitems(ours, theirs):
    """Union two id-keyed sublists (replies / attachments), chronological."""
    out = [x for x in ours if isinstance(x, dict)]
    seen = set(x.get("id") for x in out)
    for x in theirs:
        if isinstance(x, dict) and x.get("id") not in seen:
            out.append(x)
            seen.add(x.get("id"))
    out.sort(key=lambda x: x.get("createdAt") or x.get("addedAt") or "")
    return out


def _merge_comment_entry(base, ours, theirs):
    """Field-level 3-way merge of ONE comment present on both sides."""
    base = base if isinstance(base, dict) else {}
    merged = dict(ours)
    for k in set(list(ours.keys()) + list(theirs.keys())):
        if k in ("replies", "attachments"):
            merged[k] = _union_subitems(ours.get(k) or [], theirs.get(k) or [])
            continue
        ov = ours.get(k)
        # ours untouched vs base → take theirs (their change, or same value);
        # ours changed → ours wins (host-authoritative on double edits).
        merged[k] = theirs.get(k) if ov == base.get(k) else ov
    return merged


def comments_merge_texts(base_text, ours_text, theirs_text):
    """Semantic 3-way merge of comments.json sides. Returns the merged dict
    ready for json.dump (add/add conflicts pass base_text='')."""
    base = dict((c.get("id"), c) for c in _comments_of_text(base_text))
    ours_list = _comments_of_text(ours_text)
    theirs = dict((c.get("id"), c) for c in _comments_of_text(theirs_text))
    ours_ids = set(c.get("id") for c in ours_list)
    merged = []
    for c in ours_list:
        cid = c.get("id")
        if cid in theirs:
            merged.append(_merge_comment_entry(base.get(cid), c, theirs[cid]))
        elif cid not in base:
            merged.append(c)              # new on our side
        # else: in base but gone from theirs → they deleted it; deletion wins
    for c in _comments_of_text(theirs_text):
        cid = c.get("id")
        if cid not in ours_ids and cid not in base:
            merged.append(c)              # new on their side
    merged.sort(key=lambda c: c.get("createdAt") or "")
    return {"comments": merged}


def _comments_from_conflict_text(raw):
    """Recover a comments.json whose content still carries git conflict markers:
    split the hunks into the two sides (diff3 base sections are dropped) and
    union-merge them. None when the text has no markers or neither side parses."""
    if "<<<<<<<" not in raw:
        return None
    ours_lines, theirs_lines = [], []
    mode = "keep"    # keep | ours | base | theirs
    for ln in raw.splitlines(True):
        if ln.startswith("<<<<<<<"):
            mode = "ours"; continue
        if mode == "ours" and ln.startswith("|||||||"):
            mode = "base"; continue
        if mode in ("ours", "base") and ln.startswith("======="):
            mode = "theirs"; continue
        if ln.startswith(">>>>>>>"):
            mode = "keep"; continue
        if mode in ("keep", "ours"):
            ours_lines.append(ln)
        if mode in ("keep", "theirs"):
            theirs_lines.append(ln)
    try:
        merged = comments_merge_texts("", "".join(ours_lines), "".join(theirs_lines))
    except Exception:
        return None
    return merged if merged.get("comments") else None


def _clip(s, n):
    if not isinstance(s, str):
        return ""
    return s[:n]


def _clean_author(raw):
    raw = raw if isinstance(raw, dict) else {}
    return {
        "name":  _clip(raw.get("name"), 80).strip(),
        "email": _clip(raw.get("email"), 120).strip().lower(),
    }


def comments_list(project_root, prototype=None):
    items = comments_load(project_root).get("comments", [])
    if prototype:
        items = [c for c in items if c.get("prototype") == prototype]
    return items


def comment_counts(project_root, prototype):
    counts = {"open": 0, "done": 0, "archived": 0, "total": 0}
    for c in comments_list(project_root, prototype):
        st = c.get("status") if c.get("status") in COMMENT_STATUSES else "open"
        counts[st] += 1
        counts["total"] += 1
    return counts


def comment_add(project_root, prototype, *, page, anchor, pin, text, author):
    """Append one comment. `anchor` is the element handle the viewer
    computed: { selector, tag?, text? } - selector is the primary locator,
    the rest are fuzzy fallbacks for when the prototype's DOM drifts after
    agent edits. `pin` is {x,y} in 0..1 fractions of the element box."""
    text = _clip(text, 5000).strip()
    if not text:
        raise ValueError("comment text required")
    anchor = anchor if isinstance(anchor, dict) else {}
    pin    = pin if isinstance(pin, dict) else {}
    entry = {
        "id":        "c-" + secrets.token_hex(5),
        "prototype": prototype,
        "page":      _clip(page, 500) or "index.html",
        "anchor": {
            "selector": _clip(anchor.get("selector"), 1000),
            "tag":      _clip(anchor.get("tag"), 40),
            "text":     _clip(anchor.get("text"), 200),
        },
        "pin": {
            "x": max(0.0, min(1.0, float(pin.get("x", 0.5)) if isinstance(pin.get("x", 0.5), (int, float)) else 0.5)),
            "y": max(0.0, min(1.0, float(pin.get("y", 0.5)) if isinstance(pin.get("y", 0.5), (int, float)) else 0.5)),
        },
        "text":      text,
        "author":    _clean_author(author),
        "createdAt": _now_iso(),
        "status":    "open",
        "processedAt": "",
        "replies":   [],
        "shot":      "",     # filename of the page screenshot, set by comment_set_shot
        "shotAt":    "",
        # Reviewer-attached images, distinct from the auto screenshot. Each is
        # {id, name, ext, addedAt}; bytes live at share/comment-attach/<cid>/<id>.<ext>.
        "attachments": [],
    }
    with _COMMENTS_LOCK:
        data = comments_load(project_root)
        data["comments"].append(entry)
        _comments_save(project_root, data)
    return entry


def _find_comment(data, comment_id):
    for c in data.get("comments", []):
        if c.get("id") == comment_id:
            return c
    return None


def comment_reply(project_root, comment_id, *, text, author):
    text = _clip(text, 5000).strip()
    if not text:
        raise ValueError("reply text required")
    with _COMMENTS_LOCK:
        data = comments_load(project_root)
        c = _find_comment(data, comment_id)
        if c is None:
            raise ValueError(f"unknown comment: {comment_id}")
        reply = {
            "id":        "r-" + secrets.token_hex(5),
            "text":      text,
            "author":    _clean_author(author),
            "createdAt": _now_iso(),
        }
        c.setdefault("replies", []).append(reply)
        _comments_save(project_root, data)
    return reply


def comment_edit(project_root, comment_id, *, text):
    text = _clip(text, 5000).strip()
    if not text:
        raise ValueError("comment text required")
    with _COMMENTS_LOCK:
        data = comments_load(project_root)
        c = _find_comment(data, comment_id)
        if c is None:
            raise ValueError(f"unknown comment: {comment_id}")
        c["text"] = text
        c["editedAt"] = _now_iso()
        _comments_save(project_root, data)
    return c


def comment_set_status(project_root, comment_id, status):
    if status not in COMMENT_STATUSES:
        raise ValueError(f"invalid status: {status!r}")
    with _COMMENTS_LOCK:
        data = comments_load(project_root)
        c = _find_comment(data, comment_id)
        if c is None:
            raise ValueError(f"unknown comment: {comment_id}")
        c["status"] = status
        _comments_save(project_root, data)
    return c


def comment_delete(project_root, comment_id):
    with _COMMENTS_LOCK:
        data = comments_load(project_root)
        before = len(data["comments"])
        data["comments"] = [c for c in data["comments"] if c.get("id") != comment_id]
        if len(data["comments"]) == before:
            return False
        _comments_save(project_root, data)
    # Drop the page screenshot too - the comment it belonged to is gone.
    try:
        p = comment_shot_abspath(project_root, comment_id)
        if p and os.path.isfile(p):
            os.remove(p)
    except OSError:
        pass
    # And the reviewer image attachments (a whole per-comment directory).
    try:
        import shutil
        d = _comment_attach_dir(project_root, comment_id)
        if os.path.isdir(d):
            shutil.rmtree(d, ignore_errors=True)
    except OSError:
        pass
    return True


# ── Page screenshots ────────────────────────────────────────────────────
# When a reviewer posts a comment the viewer captures what they're looking at
# (html2canvas on the same-origin prototype iframe) and uploads it here. We
# store it as a JPEG at share/comment-shots/<comment-id>.jpg - keyed purely on
# the comment id so the file is resolvable without a path stored in the record
# (which could drift). The gate serves it back to the viewer sidebar; the
# editor serves it back to the comment inbox.

# Decoded-byte ceiling for an uploaded screenshot. A viewport JPEG is well
# under this even at 2x DPR; the cap just bounds a hostile/buggy client.
_SHOT_MAX_BYTES = 12 * 1024 * 1024


def _comment_shots_dir(project_root):
    return os.path.join(project_root, "share", "comment-shots")


def comment_shot_abspath(project_root, comment_id):
    """Absolute path the screenshot for `comment_id` would live at (whether or
    not it exists yet). None for a malformed id - guards path traversal."""
    if not COMMENT_ID_OK.match(comment_id or ""):
        return None
    return os.path.join(_comment_shots_dir(project_root), comment_id + ".jpg")


def comment_set_shot(project_root, comment_id, data_url):
    """Decode a `data:image/...;base64,…` URL and store it as the comment's
    page screenshot. Returns the updated comment, or raises ValueError on a
    malformed / oversized / non-image payload or an unknown comment id."""
    if not isinstance(data_url, str) or "," not in data_url:
        raise ValueError("shot must be a data URL")
    head, _comma, b64 = data_url.partition(",")
    if "base64" not in head:
        raise ValueError("shot must be base64-encoded")
    try:
        raw = base64.b64decode(b64)
    except Exception:
        raise ValueError("shot is not valid base64")
    if not raw:
        raise ValueError("shot is empty")
    if len(raw) > _SHOT_MAX_BYTES:
        raise ValueError("shot is too large")
    # Sniff a real image header - JPEG (FFD8) or PNG - so we never persist
    # arbitrary bytes under an image filename.
    if not (raw[:2] == b"\xff\xd8" or raw[:8] == b"\x89PNG\r\n\x1a\n"):
        raise ValueError("shot is not a JPEG or PNG image")
    with _COMMENTS_LOCK:
        data = comments_load(project_root)
        c = _find_comment(data, comment_id)
        if c is None:
            raise ValueError(f"unknown comment: {comment_id}")
        out = comment_shot_abspath(project_root, comment_id)
        if out is None:
            raise ValueError(f"invalid comment id: {comment_id}")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        tmp = out + ".tmp"
        with open(tmp, "wb") as f:
            f.write(raw)
        os.replace(tmp, out)
        c["shot"]   = comment_id + ".jpg"
        c["shotAt"] = _now_iso()
        _comments_save(project_root, data)
    return c


# ── Reviewer image attachments ──────────────────────────────────────────
# Separate from the auto screenshot: a reviewer can attach one or more images
# to a comment (a reference mock, a photo, a screenshot from elsewhere). They
# land in share/comment-attach/<comment-id>/<attach-id>.<ext> and are listed in
# the comment's `attachments` array as {id, name, ext, addedAt}. Keyed on
# comment+attach id so the file is resolvable from the record alone.

_ATTACH_MAX_BYTES = 12 * 1024 * 1024
_ATTACH_MAX_COUNT = 8
# ext → (allowed, header sniff). Mirrors the formats a browser <input
# type=file accept=image/*> can hand us as a data URL.
_ATTACH_TYPES = {
    "jpg":  b"\xff\xd8",
    "jpeg": b"\xff\xd8",
    "png":  b"\x89PNG\r\n\x1a\n",
    "gif":  b"GIF8",
    "webp": b"RIFF",          # RIFF....WEBP - we check the WEBP tag below too
}


def _comment_attach_dir(project_root, comment_id):
    return os.path.join(project_root, "share", "comment-attach", comment_id)


def comment_attach_abspath(project_root, comment_id, attach_id, ext):
    """Absolute path one attachment would live at. None for a malformed id or
    a disallowed extension - guards path traversal + filetype."""
    if not COMMENT_ID_OK.match(comment_id or ""):
        return None
    if not ATTACH_ID_OK.match(attach_id or ""):
        return None
    ext = (ext or "").lower().lstrip(".")
    if ext not in _ATTACH_TYPES:
        return None
    return os.path.join(_comment_attach_dir(project_root, comment_id),
                        attach_id + "." + ext)


def comment_attach_lookup(project_root, comment_id, attach_id):
    """Resolve an existing attachment to (abspath, ext) from the stored record,
    or (None, None) if the comment/attachment is unknown or the file is gone."""
    for c in comments_load(project_root).get("comments", []):
        if c.get("id") != comment_id:
            continue
        for a in c.get("attachments", []) or []:
            if a.get("id") == attach_id:
                path = comment_attach_abspath(project_root, comment_id,
                                              attach_id, a.get("ext"))
                if path and os.path.isfile(path):
                    return path, a.get("ext")
                return None, None
    return None, None


def comment_add_attachment(project_root, comment_id, data_url, name):
    """Decode a `data:image/...;base64,…` URL and store it as one image
    attachment on the comment. Returns the attachment record, or raises
    ValueError on a malformed / oversized / non-image payload, an unknown
    comment id, or when the per-comment attachment cap is reached."""
    if not isinstance(data_url, str) or "," not in data_url:
        raise ValueError("attachment must be a data URL")
    head, _comma, b64 = data_url.partition(",")
    if "base64" not in head:
        raise ValueError("attachment must be base64-encoded")
    # Derive the extension from the data-URL mime, falling back to png.
    mime = head[5:].split(";")[0].strip().lower()  # strip leading "data:"
    ext = {
        "image/jpeg": "jpg", "image/jpg": "jpg", "image/png": "png",
        "image/gif": "gif", "image/webp": "webp",
    }.get(mime)
    if ext is None:
        raise ValueError("attachment must be a JPEG, PNG, GIF or WebP image")
    try:
        raw = base64.b64decode(b64)
    except Exception:
        raise ValueError("attachment is not valid base64")
    if not raw:
        raise ValueError("attachment is empty")
    if len(raw) > _ATTACH_MAX_BYTES:
        raise ValueError("attachment is too large")
    # Sniff a real image header so we never persist arbitrary bytes.
    magic = _ATTACH_TYPES[ext]
    ok = raw.startswith(magic)
    if ext == "webp":
        ok = raw[:4] == b"RIFF" and raw[8:12] == b"WEBP"
    if not ok:
        raise ValueError("attachment does not match its declared image type")
    attach_id = "a-" + secrets.token_hex(5)
    rec = {
        "id":      attach_id,
        "name":    _clip(name, 200).strip() or ("image." + ext),
        "ext":     ext,
        "addedAt": _now_iso(),
    }
    with _COMMENTS_LOCK:
        data = comments_load(project_root)
        c = _find_comment(data, comment_id)
        if c is None:
            raise ValueError(f"unknown comment: {comment_id}")
        atts = c.setdefault("attachments", [])
        if not isinstance(atts, list):
            atts = c["attachments"] = []
        if len(atts) >= _ATTACH_MAX_COUNT:
            raise ValueError("too many attachments on this comment")
        out = comment_attach_abspath(project_root, comment_id, attach_id, ext)
        if out is None:
            raise ValueError("could not store attachment")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        tmp = out + ".tmp"
        with open(tmp, "wb") as f:
            f.write(raw)
        os.replace(tmp, out)
        atts.append(rec)
        _comments_save(project_root, data)
    return rec


def comment_image_stats(project_root):
    """Per-prototype screenshot inventory for the housekeeping view:
    {prototype: {"total": n, "withImages": n, "imageBytes": n}}. `withImages`
    and `imageBytes` count only screenshots that still exist on disk."""
    out = {}
    for c in comments_load(project_root).get("comments", []):
        proto = c.get("prototype") or "-"
        g = out.setdefault(proto, {"total": 0, "withImages": 0, "imageBytes": 0})
        g["total"] += 1
        if c.get("shot"):
            p = comment_shot_abspath(project_root, c.get("id"))
            try:
                if p and os.path.isfile(p):
                    g["withImages"] += 1
                    g["imageBytes"] += os.path.getsize(p)
            except OSError:
                pass
    return out


def comments_clear_shots(project_root, comment_ids):
    """Strip the page screenshot from each given comment - removes the file and
    clears shot/shotAt, leaving the comment thread intact. Returns the ids that
    had a screenshot to clear. One load/save for the whole batch."""
    wanted = set(comment_ids or [])
    cleared, paths = [], []
    with _COMMENTS_LOCK:
        data = comments_load(project_root)
        for c in data.get("comments", []):
            if c.get("id") in wanted and c.get("shot"):
                cleared.append(c["id"])
                paths.append(comment_shot_abspath(project_root, c["id"]))
                c["shot"] = ""
                c["shotAt"] = ""
        if cleared:
            _comments_save(project_root, data)
    for p in paths:
        try:
            if p and os.path.isfile(p):
                os.remove(p)
        except OSError:
            pass
    return cleared


def comments_mark_processed(project_root, comment_ids):
    """Stamp processedAt on the given comments - called when the editor
    dispatches them to an agent run. Status is left alone; 'processed' is
    an orthogonal chip in the UI (the agent's edit may or may not satisfy
    the reviewer - they decide when to mark done)."""
    stamped = []
    when = _now_iso()
    with _COMMENTS_LOCK:
        data = comments_load(project_root)
        wanted = set(comment_ids or [])
        for c in data.get("comments", []):
            if c.get("id") in wanted:
                c["processedAt"] = when
                stamped.append(c["id"])
        if stamped:
            _comments_save(project_root, data)
    return stamped


def _notify_comments_changed(project_id, prototype):
    if _ON_COMMENTS_CHANGED:
        try:
            _ON_COMMENTS_CHANGED(project_id, prototype)
        except Exception:
            pass


# ═════════════════════════════════════════════════════════════════════════
# 4. Gate - the ONLY surface a tunnel exposes
# ═════════════════════════════════════════════════════════════════════════

_GATE_SERVER = None

# Live Session - late-bound so live.py can import shares without a cycle.
# serve.py calls register_live(live.GATE) at boot; the gate delegates any
# /s/<token>/live* route to it. None → live session disabled (gate still
# serves view+comment routes).
_LIVE = None

def register_live(gate):
    global _LIVE
    _LIVE = gate

# User Testing - same late-bound delegation as live (usertesting_gate.py imports
# shares without a cycle). serve.py calls register_usertesting(GATE) at boot; the
# gate delegates /t/<token>/* (testee recorder) and /r/<token>/* (reviewer
# replay) to it. None -> user testing disabled (gate still serves share routes).
_UT = None

def register_usertesting(gate):
    global _UT
    _UT = gate


def gate_serve_project_file(handler, project_root, prototype, sub):
    """Serve ONE whitelisted prototype / design-system file for `sub` shaped
    like '/p/source/<slug>/...', '/source/...', or '/design-systems/...'. Same
    realpath-contained, extension-whitelisted logic the share viewer block uses
    (do_GET ~/p/ branch), factored out so the user-testing gate reuses it
    verbatim. Returns True once it has sent a response (hit or 404); False if
    `sub` is not a project-file route at all."""
    if not (sub.startswith("/p/") or sub.startswith("/source/") or sub.startswith("/design-systems/")):
        return False
    raw = sub[len("/p/"):] if sub.startswith("/p/") else sub.lstrip("/")
    rel = urllib.parse.unquote(raw).split("?")[0].split("#")[0].strip("/")
    if not rel or ".." in rel.split("/") or rel.startswith("."):
        handler._send_json(404, {"error": "not found"}); return True
    slug = prototype or ""
    allowed_prefixes = (f"source/{slug}/", "design-systems/")
    if not any(rel == p.rstrip("/") or rel.startswith(p) for p in allowed_prefixes):
        handler._send_json(404, {"error": "not found"}); return True
    abs_path = os.path.realpath(os.path.join(project_root, rel))
    rp = os.path.realpath(project_root)
    if not (abs_path == rp or abs_path.startswith(rp + os.sep)):
        handler._send_json(404, {"error": "not found"}); return True
    if os.path.isdir(abs_path):
        abs_path = os.path.join(abs_path, "index.html")
    base = os.path.basename(abs_path)
    ext  = os.path.splitext(base)[1].lower()
    if base.startswith(".") or ext not in _GATE_SERVE_EXTS:
        handler._send_json(404, {"error": "not found"}); return True
    if not os.path.isfile(abs_path):
        handler._send_json(404, {"error": "not found"}); return True
    is_media = ext not in (".html", ".htm", ".css", ".js", ".mjs", ".json")
    handler._send_file(abs_path, cache=is_media); return True

# File extensions the gate will serve out of a project. Everything a
# build-less htm+React prototype legitimately uses; notably NO .py and no
# dotfiles (filtered separately).
_GATE_SERVE_EXTS = {
    ".html", ".htm", ".css", ".js", ".mjs", ".json", ".txt", ".md", ".xml",
    ".svg", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif", ".ico",
    ".mp4", ".webm", ".mov", ".mp3", ".wav", ".ogg", ".m4a",
    ".woff", ".woff2", ".ttf", ".otf",
    ".glb", ".gltf", ".bin", ".hdr", ".ktx2",
}


def _gate_project_paths_ok(rec, rel):
    """Whitelist check for /s/<token>/p/<rel>. Only the shared prototype's
    own tree and the design-system library it links are reachable - NOT
    the project's other prototypes, workflow/, editor/, or docs."""
    slug = rec.get("prototype") or ""
    allowed_prefixes = (f"source/{slug}/", "design-systems/")
    return any(rel == p.rstrip("/") or rel.startswith(p) for p in allowed_prefixes)


class GateHandler(http.server.BaseHTTPRequestHandler):
    """Minimal, share-scoped request handler. Deliberately NOT a subclass
    of the daemon's H - sharing zero routing code is the point."""
    server_version = "WovenShareGate/1.0"
    protocol_version = "HTTP/1.1"

    # ── plumbing ──────────────────────────────────────────────────────
    def log_message(self, fmt, *args):
        pass  # tunnels are chatty; keep the daemon console readable

    def _send_json(self, code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(body)
        except Exception:
            pass

    def _send_file(self, abs_path, *, cache=False):
        try:
            with open(abs_path, "rb") as f:
                body = f.read()
        except OSError:
            return self._send_json(404, {"error": "not found"})
        ctype = mimetypes.guess_type(abs_path)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript", "application/json", "image/svg+xml"):
            ctype += "; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        # Live-source shares: HTML/CSS/JS must always be fresh; media can
        # cache briefly to keep tunnel chatter down.
        self.send_header("Cache-Control", "max-age=300" if cache else "no-store")
        self.end_headers()
        try:
            self.wfile.write(body)
        except Exception:
            pass

    def _read_json_body(self, max_bytes=64 * 1024):
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = 0
        if n <= 0 or n > max_bytes:
            raise ValueError("body required (and must be under 64KB)")
        raw = self.rfile.read(n)
        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception:
            raise ValueError("invalid JSON body")
        if not isinstance(data, dict):
            raise ValueError("body must be an object")
        return data

    def _route(self):
        """Parse /s/<token>/<sub…>. Returns (rec, sub) or (None, None)
        after replying with the error itself."""
        parsed = urllib.parse.urlparse(self.path)
        m = re.match(r"^/s/([a-f0-9]+)(/.*)?$", parsed.path)
        if not m:
            self._send_json(404, {"error": "not found"})
            return None, None
        rec = share_get_by_token(m.group(1))
        if rec is None:
            self._send_json(404, {"error": "unknown or revoked share"})
            return None, None
        # NOTE: "" (no trailing slash) and "/" are distinct - do_GET 301s
        # the former so the viewer's relative paths resolve.
        return rec, (m.group(2) if m.group(2) is not None else "")

    def _project_root(self, rec):
        try:
            return _RESOLVE_PROJECT_ROOT(rec.get("project") or "")
        except Exception:
            return None

    def _require_author(self, rec, body):
        """Visitor identity policy. Always need a display name; the email
        gate additionally requires a plausible email."""
        author = _clean_author(body.get("author"))
        if not author["name"]:
            raise PermissionError("a display name is required to comment")
        if rec.get("emailGate") and not EMAIL_OK.match(author["email"] or ""):
            raise PermissionError("this share requires an email address to comment")
        return author

    # ── GET ───────────────────────────────────────────────────────────
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        # Root-absolute font passthrough - DS stylesheets may reference
        # /__global_fonts/<file> (read-only static font bytes, safe).
        if parsed.path.startswith("/__global_fonts/"):
            name = os.path.basename(parsed.path)
            if not name or not NAME_SAFE.match(name):
                return self._send_json(404, {"error": "not found"})
            # Mirrors the daemon's _global_fonts_dir(): workspace-level
            # font collection at <workspace>/fonts/.
            abs_path = os.path.join(WORKSPACE_DIR or INSTALL_ROOT, "fonts", name)
            if os.path.isfile(abs_path):
                return self._send_file(abs_path, cache=True)
            return self._send_json(404, {"error": "not found"})
        # User Testing - /t/<token>/ (testee recorder) and /r/<token>/ (reviewer
        # replay) ride the same gate/tunnel; delegated wholesale to the
        # usertesting gate, which resolves its own token registry.
        # MUST run BEFORE the live-cookie branch: a stale th_live cookie left
        # by an earlier live-share session would otherwise hijack every
        # user-testing link into the project-file proxy → JSON not-found for
        # perfectly valid links (seen in the wild: Arc kept the cookie while
        # Chrome/Safari/Edge did not, so the same link failed only in Arc).
        if _UT is not None:
            # Tolerant token match: links copied through chat apps / notes pick
            # up invisible junk (zero-width spaces, %20) glued to the token and
            # arrive uppercased by some autocorrects - accept and normalize.
            mut = re.match(r"^/([tr])/([A-Fa-f0-9]{32})[^/]*(/.*)?$", parsed.path)
            if mut and _UT.handle_get(self, mut.group(1), mut.group(2).lower(),
                                      mut.group(3) if mut.group(3) is not None else ""):
                return
        # Live Session - the REAL editor (served at /s/<tok>/live/) makes
        # root-absolute requests (/app.js, /__workflow, /__ds_bootstrap…).
        # When the th_live cookie is present and this is NOT a /s/<tok>/ route,
        # delegate to live.py's read-only, project-scoped proxy.
        if _LIVE is not None and not parsed.path.startswith("/s/"):
            tok = self._live_cookie()
            if tok and _LIVE.handle_rooted(self, tok, parsed.path, parsed.query):
                return
        rec, sub = self._route()
        if rec is None:
            return
        # /s/<token> without the trailing slash → redirect so the viewer's
        # relative asset/api paths resolve under /s/<token>/.
        if sub == "":
            self.send_response(301)
            self.send_header("Location", parsed.path + "/")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        # Live Session routes (/s/<token>/live*) - delegated to live.py.
        if _LIVE is not None and (sub == "/live" or sub.startswith("/live/")):
            if _LIVE.handle_get(self, rec, sub):
                return
        # A multiplayer transport share hosts ONLY the live co-edit; it never
        # publishes the prototype-review surface. Any non-/live route 404s so the
        # tunnel can't be used to browse the project.
        if rec.get("liveOnly"):
            return self._send_json(404, {"error": "not found"})
        # Viewer shell + assets.
        if sub == "/":
            return self._send_file(os.path.join(INSTALL_ROOT, "editor", "share", "viewer.html"))
        if sub in ("/viewer.js", "/viewer.css"):
            return self._send_file(os.path.join(INSTALL_ROOT, "editor", "share", sub.lstrip("/")))
        # Woven logo as the share page's tab icon (viewer.html links it
        # relative, so it arrives as /s/<token>/favicon.svg).
        if sub == "/favicon.svg":
            return self._send_file(os.path.join(INSTALL_ROOT, "editor", "favicon.svg"), cache=True)
        # Share metadata for the viewer boot.
        if sub == "/api/meta":
            return self._send_json(200, {
                "label":     rec.get("label") or "",
                "prototype": rec.get("prototype") or "",
                "emailGate": bool(rec.get("emailGate")),
                "entry":     f"p/source/{rec.get('prototype')}/index.html",
            })
        if sub == "/api/comments":
            root = self._project_root(rec)
            if root is None:
                return self._send_json(500, {"error": "project unavailable"})
            return self._send_json(200, {"comments": comments_list(root, rec.get("prototype"))})
        m = re.match(r"^/api/comments/(c-[a-f0-9]+)/shot$", sub)
        if m:
            root = self._project_root(rec)
            if root is None:
                return self._send_json(500, {"error": "project unavailable"})
            path = comment_shot_abspath(root, m.group(1))
            if not path or not os.path.isfile(path):
                return self._send_json(404, {"error": "no screenshot"})
            return self._send_file(path, cache=True)
        ma = re.match(r"^/api/comments/(c-[a-f0-9]+)/attach/(a-[a-f0-9]+)$", sub)
        if ma:
            root = self._project_root(rec)
            if root is None:
                return self._send_json(500, {"error": "project unavailable"})
            path, _ext = comment_attach_lookup(root, ma.group(1), ma.group(2))
            if not path:
                return self._send_json(404, {"error": "no attachment"})
            return self._send_file(path, cache=True)
        # Whitelisted project files. /p/ is the share viewer's prefix; the live
        # editor's prototype iframes load /source/… and /design-systems/…
        # directly (resolved relative to /s/<tok>/live/) - serve both through
        # the same realpath-contained, extension-whitelisted logic.
        if sub.startswith("/p/") or sub.startswith("/source/") or sub.startswith("/design-systems/"):
            root = self._project_root(rec)
            if root is None:
                return self._send_json(500, {"error": "project unavailable"})
            raw = sub[len("/p/"):] if sub.startswith("/p/") else sub.lstrip("/")
            rel = urllib.parse.unquote(raw)
            rel = rel.split("?")[0].split("#")[0].strip("/")
            if not rel or ".." in rel.split("/") or rel.startswith("."):
                return self._send_json(404, {"error": "not found"})
            if not _gate_project_paths_ok(rec, rel):
                return self._send_json(404, {"error": "not found"})
            abs_path = os.path.realpath(os.path.join(root, rel))
            if not (abs_path == os.path.realpath(root)
                    or abs_path.startswith(os.path.realpath(root) + os.sep)):
                return self._send_json(404, {"error": "not found"})
            if os.path.isdir(abs_path):
                abs_path = os.path.join(abs_path, "index.html")
            base = os.path.basename(abs_path)
            ext  = os.path.splitext(base)[1].lower()
            if base.startswith(".") or ext not in _GATE_SERVE_EXTS:
                return self._send_json(404, {"error": "not found"})
            if not os.path.isfile(abs_path):
                return self._send_json(404, {"error": "not found"})
            is_media = ext not in (".html", ".htm", ".css", ".js", ".mjs", ".json")
            return self._send_file(abs_path, cache=is_media)
        return self._send_json(404, {"error": "not found"})

    def _live_cookie(self):
        """th_live=<token> cookie set when the editor index was served - scopes
        the real editor's root-absolute requests to one share."""
        raw = self.headers.get("Cookie") or ""
        for part in raw.split(";"):
            k, _eq, v = part.strip().partition("=")
            if k == "th_live" and TOKEN_OK.match(v or ""):
                return v
        return None

    # ── POST ──────────────────────────────────────────────────────────
    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        # User Testing POST - /t/<token>/api/* (recording upload) and
        # /r/<token>/api/markers. MUST run before the live-cookie branch
        # (stale th_live cookie hijack - see do_GET) and before the /s/ route.
        if _UT is not None:
            # Same tolerant token match as the GET route (copy-paste junk).
            mut = re.match(r"^/([tr])/([A-Fa-f0-9]{32})[^/]*(/.*)?$", parsed.path)
            if mut and _UT.handle_post(self, mut.group(1), mut.group(2).lower(),
                                       mut.group(3) if mut.group(3) is not None else ""):
                return
        # Real-editor root-absolute writes (guest mode is read-only) → no-op.
        if _LIVE is not None and not parsed.path.startswith("/s/"):
            tok = self._live_cookie()
            if tok and _LIVE.handle_rooted_post(self, tok, parsed.path):
                return
        rec, sub = self._route()
        if rec is None:
            return
        # Live Session routes (/s/<token>/live*) - delegated to live.py.
        if _LIVE is not None and sub.startswith("/live/"):
            if _LIVE.handle_post(self, rec, sub):
                return
        # Multiplayer transport share: only /live routes; no review surface.
        if rec.get("liveOnly"):
            return self._send_json(404, {"error": "not found"})
        root = self._project_root(rec)
        if root is None:
            return self._send_json(500, {"error": "project unavailable"})
        # Page-screenshot upload - a base64 image far exceeds the 64KB JSON
        # body the comment routes use, so handle it before the generic read.
        ms = re.match(r"^/api/comments/(c-[a-f0-9]+)/shot$", sub)
        if ms:
            try:
                shot_body = self._read_json_body(max_bytes=20 * 1024 * 1024)
            except ValueError as e:
                return self._send_json(400, {"error": str(e)})
            try:
                comment_set_shot(root, ms.group(1), shot_body.get("shot"))
            except ValueError as e:
                return self._send_json(400, {"error": str(e)})
            return self._send_json(200, {"ok": True})
        # Image attachment upload - also a base64 image, so handle it before the
        # generic 64KB JSON read.
        ma = re.match(r"^/api/comments/(c-[a-f0-9]+)/attach$", sub)
        if ma:
            try:
                att_body = self._read_json_body(max_bytes=20 * 1024 * 1024)
            except ValueError as e:
                return self._send_json(400, {"error": str(e)})
            try:
                rec_att = comment_add_attachment(
                    root, ma.group(1), att_body.get("data"), att_body.get("name"))
            except ValueError as e:
                return self._send_json(400, {"error": str(e)})
            _notify_comments_changed(rec.get("project"), rec.get("prototype"))
            return self._send_json(200, {"ok": True, "attachment": rec_att})
        try:
            body = self._read_json_body()
        except ValueError as e:
            return self._send_json(400, {"error": str(e)})
        try:
            if sub == "/api/comments":
                author = self._require_author(rec, body)
                entry = comment_add(
                    root, rec.get("prototype"),
                    page=body.get("page"), anchor=body.get("anchor"),
                    pin=body.get("pin"), text=body.get("text"), author=author,
                )
                _notify_comments_changed(rec.get("project"), rec.get("prototype"))
                return self._send_json(200, {"ok": True, "comment": entry})
            m = re.match(r"^/api/comments/([cr]-[a-f0-9]+)/(reply|status|delete|edit)$", sub)
            if m:
                cid, op = m.group(1), m.group(2)
                if op == "reply":
                    author = self._require_author(rec, body)
                    reply = comment_reply(root, cid, text=body.get("text"), author=author)
                    _notify_comments_changed(rec.get("project"), rec.get("prototype"))
                    return self._send_json(200, {"ok": True, "reply": reply})
                if op == "edit":
                    self._require_author(rec, body)
                    c = comment_edit(root, cid, text=body.get("text"))
                    _notify_comments_changed(rec.get("project"), rec.get("prototype"))
                    return self._send_json(200, {"ok": True, "comment": c})
                if op == "status":
                    c = comment_set_status(root, cid, body.get("status"))
                    _notify_comments_changed(rec.get("project"), rec.get("prototype"))
                    return self._send_json(200, {"ok": True, "comment": c})
                if op == "delete":
                    ok = comment_delete(root, cid)
                    _notify_comments_changed(rec.get("project"), rec.get("prototype"))
                    return self._send_json(200 if ok else 404,
                                           {"ok": ok} if ok else {"error": "unknown comment"})
        except PermissionError as e:
            return self._send_json(403, {"error": str(e)})
        except ValueError as e:
            return self._send_json(400, {"error": str(e)})
        except Exception as e:
            return self._send_json(500, {"error": f"internal error: {e}"})
        return self._send_json(404, {"error": "not found"})


NAME_SAFE = re.compile(r"^[A-Za-z0-9._-]+$")


class _GateServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def start_gate_server(main_port):
    """Bind the gate on the first free port after the daemon's. Returns the
    port. Idempotent - repeated calls return the existing port."""
    global _GATE_SERVER, GATE_PORT
    if _GATE_SERVER is not None:
        return GATE_PORT
    last_err = None
    for offset in range(1, 21):
        port = main_port + offset
        try:
            srv = _GateServer(("", port), GateHandler)
        except OSError as e:
            last_err = e
            continue
        _GATE_SERVER = srv
        GATE_PORT = port
        threading.Thread(target=srv.serve_forever, daemon=True,
                         name="share-gate").start()
        print(f"[share] gate listening on http://127.0.0.1:{port} "
              "(share-scoped routes only)", flush=True)
        return port
    raise RuntimeError(f"no free port for share gate near {main_port}: {last_err}")


# ═════════════════════════════════════════════════════════════════════════
# 5. Status summary - what GET /__shares returns per record
# ═════════════════════════════════════════════════════════════════════════

def share_summary(rec):
    """Record + live status + comment counts, ready for the UI."""
    out = dict(rec)
    token = rec.get("token", "")
    out.pop("token", None)   # editor uses the *Url fields below; token stays server-side-ish
    modes = share_modes(rec)
    qst = _quick_status(rec) if modes["quick"] else {"status": "stopped", "url": "", "pid": None, "error": ""}
    wst = _woven_status(rec) if modes["woven"] else {"status": "stopped", "url": "", "pid": None, "error": ""}

    def _link(base):
        return (base.rstrip("/") + "/s/" + token + "/") if base else ""

    hst = hosted_status(rec)

    out["quickOn"]  = modes["quick"]
    out["wovenOn"]  = modes["woven"]
    out["mode"]     = share_mode(rec)   # legacy hint (woven if the stable link is on)
    # Hosted snapshot (served from Woven storage, daemon-off capable).
    out["hostedOn"]     = share_hosted_on(rec)
    out["hostedStatus"] = hst["status"]
    out["hostedUrl"]    = hst["url"]
    out["hostedError"]  = hst["error"]
    out["hostedAt"]     = hst["at"]
    out["hostedBytes"]  = hst["bytes"]
    # Per-link liveness so the UI can show each link's own state (running /
    # starting / exited / error) instead of silently hiding a link with no URL.
    out["quickStatus"] = qst["status"] if modes["quick"] else "off"
    out["wovenStatus"] = wst["status"] if modes["woven"] else "off"
    out["quickError"]  = qst["error"] if modes["quick"] else ""
    out["wovenError"]  = wst["error"] if modes["woven"] else ""
    # Per-link public URLs - a share can carry BOTH at once.
    qurl = qst["url"] or (rec.get("lastUrl") if (modes["quick"] and qst["status"] == "running") else "")
    out["quickUrl"] = _link(qurl)
    out["wovenUrl"] = _link(wst["url"])
    # shareUrl stays the single canonical link for back-compat readers; prefer
    # the stable link when both are live. The hosted link IS the stable URL
    # (same hostname, snapshot-served), so it slots in at the same priority.
    out["shareUrl"] = out["wovenUrl"] or (hst["url"] if hst["status"] == "hosted" else "") or out["quickUrl"]
    # Overall status folds both links (running wins, then starting).
    sts = [s["status"] for s in ([qst] if modes["quick"] else []) + ([wst] if modes["woven"] else [])]
    out["status"] = ("running" if "running" in sts else
                     "starting" if "starting" in sts else
                     (sts[0] if sts else "stopped"))
    out["pid"]    = qst["pid"] or wst["pid"]
    out["error"]  = qst["error"] or wst["error"]
    out["localUrl"] = (f"http://127.0.0.1:{GATE_PORT}/s/{token}/"
                       if GATE_PORT else "")
    # URL-change detection only applies to the randomised (quick) link, whose
    # *.trycloudflare.com URL is reassigned on every restart. The stable (woven)
    # link is a fixed getwoven.design URL that never changes, so it never raises
    # the "URL changed - resend the link" flag.
    out["urlChanged"] = (modes["quick"]
                         and bool(rec.get("prevUrl"))
                         and rec.get("prevUrl") != rec.get("lastUrl"))
    out["hasThumbnail"] = False
    out["thumbnailV"] = 0
    try:
        root = _RESOLVE_PROJECT_ROOT(rec.get("project") or "")
        out["commentCounts"] = comment_counts(root, rec.get("prototype"))
        try:
            st = os.stat(share_thumbnail_abspath(root, rec.get("prototype")))
            out["hasThumbnail"] = True
            out["thumbnailV"] = int(st.st_mtime)   # cache-bust key for the <img>
        except OSError:
            pass
    except Exception:
        out["commentCounts"] = {"open": 0, "done": 0, "archived": 0, "total": 0}
    return out


def shares_summary_all():
    return [share_summary(s) for s in shares_load().get("shares", [])]

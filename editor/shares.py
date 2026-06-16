"""Share mode — publish a prototype through a Cloudflare quick tunnel with
per-element review comments.

Three cooperating pieces, all daemon-side (serve.py imports this module the
same way it imports exports.py):

  1. REGISTRY  — shares.json at the workspace root (sibling of
     workspace.json). One record per shared prototype:
       { id, token, project, prototype, label, emailGate, active,
         createdAt, lastUrl, prevUrl, lastUrlChangedAt, lastStartedAt }
     `active` is USER INTENT (should a tunnel be running), not liveness —
     liveness comes from the tunnel process table below.

  2. TUNNELS   — one `cloudflared tunnel --url http://127.0.0.1:<gate>`
     subprocess per active share. Quick tunnels need no Cloudflare account;
     the price is a random *.trycloudflare.com hostname that CHANGES on
     every restart. We parse the URL from cloudflared's log output, persist
     it on the share record, and keep the previous URL around so the UI can
     surface "URL changed since you last copied it".

  3. GATE      — a second HTTP listener (separate port from the main daemon)
     that is the ONLY thing a tunnel ever points at. It serves exactly:
       /s/<token>/                      → review viewer shell (editor/share/)
       /s/<token>/viewer.js|viewer.css  → viewer assets
       /s/<token>/p/<project-rel-path>  → whitelisted prototype files
                                          (source/<slug>/** + design-systems/**)
       /s/<token>/api/meta|comments…    → share metadata + comment CRUD
       /__global_fonts/<file>           → read-only font passthrough (DS
                                          stylesheets may reference these
                                          root-absolute)
     Everything else 404s. The main daemon port — with its file writes, LLM
     runs and project management — is never exposed. This is the security
     boundary the whole feature rests on; widen it deliberately or not at all.

  COMMENTS     — per-project store at <project_root>/share/comments.json
     (all prototypes of a project in one file, records carry `prototype`).
     Written by visitors through the gate AND by the editor through the main
     daemon's /__share_comments endpoint — both funnel through the same
     functions here, under the same lock.

serve.py wiring (see "share mode" section there):
     init(...)                 once at boot
     start_gate_server(port)   once at boot  → gate port
     restore_active_tunnels()  once at boot  (active shares get tunnels back;
                                              their URLs will have changed)
     stop_all_tunnels()        from the shutdown hooks
"""
from __future__ import annotations  # keep annotations 3.9-safe (daemon runs system py)

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
import urllib.parse

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
EMAIL_OK     = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_TUNNEL_URL_RE = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")

COMMENT_STATUSES = ("open", "done", "archived")


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
# 1. Registry — shares.json
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


def share_create(project, prototype, label=None, email_gate=False):
    """Create a share record. One share per (project, prototype) — creating
    again returns the existing record (idempotent, so the node's Share
    button can't mint duplicate tunnels for the same prototype)."""
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
            return True
    return False


# ── Thumbnails — one PNG per shared prototype ────────────────────────────
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
# 2. Tunnels — cloudflared quick-tunnel subprocess per share
# ═════════════════════════════════════════════════════════════════════════

def find_cloudflared():
    """Locate the cloudflared binary. PATH first, then the usual install
    spots (brew on Apple Silicon / Intel, manual /usr/local)."""
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
                 "started_at", "stopping", "log_tail")

    def __init__(self, share_id, proc):
        self.share_id   = share_id
        self.proc       = proc
        self.url        = ""
        self.state      = "starting"
        self.error      = ""
        self.started_at = time.time()
        self.stopping   = False
        self.log_tail   = []   # last ~30 log lines for error reporting


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
                        if old and old != t.url:
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


def tunnel_start(share_id):
    """Spawn a quick tunnel for the share, pointing at the gate port.
    Idempotent: an already-live tunnel is returned as-is. Marks the share
    active (user intent persists across daemon restarts)."""
    if GATE_PORT is None:
        raise RuntimeError("share gate server not started")
    rec = share_get(share_id)
    if rec is None:
        raise ValueError(f"unknown share: {share_id}")
    binary = find_cloudflared()
    if not binary:
        raise RuntimeError("cloudflared not found — install it (macOS: brew install cloudflared)")
    with _TUNNELS_LOCK:
        t = TUNNELS.get(share_id)
        if t and t.proc.poll() is None:
            share_update(share_id, {"active": True})
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
        TUNNELS[share_id] = t
    threading.Thread(target=_tunnel_reader, args=(t,), daemon=True,
                     name=f"share-tunnel-{share_id}").start()
    share_update(share_id, {"active": True})
    print(f"[share] tunnel starting for {share_id} (pid {proc.pid}) → gate :{GATE_PORT}", flush=True)
    return t


def tunnel_stop(share_id, *, keep_intent=False):
    """SIGTERM the share's tunnel. keep_intent=True leaves `active` as-is
    (used during shutdown so boot-time restore re-opens user-wanted
    tunnels); the normal Stop button clears it."""
    with _TUNNELS_LOCK:
        t = TUNNELS.pop(share_id, None)
    if t is not None:
        t.stopping = True
        try:
            t.proc.terminate()
        except Exception:
            pass
        try:
            t.proc.wait(timeout=3)
        except Exception:
            try: t.proc.kill()
            except Exception: pass
    if not keep_intent:
        share_update(share_id, {"active": False})
    return t is not None


def stop_all_tunnels():
    with _TUNNELS_LOCK:
        ids = list(TUNNELS.keys())
    for sid in ids:
        tunnel_stop(sid, keep_intent=True)
    if ids:
        print(f"[share] stopped {len(ids)} tunnel(s) on shutdown", flush=True)


def restore_active_tunnels():
    """Boot-time: restart tunnels for every share whose `active` intent
    survived the last daemon. Quick-tunnel URLs WILL differ — the reader
    thread records prevUrl/lastUrlChangedAt so the UI can flag it."""
    if not find_cloudflared():
        actives = [s for s in shares_load().get("shares", []) if s.get("active")]
        if actives:
            print(f"[share] {len(actives)} share(s) marked active but cloudflared "
                  "is not installed — tunnels NOT restored", flush=True)
        return
    for s in shares_load().get("shares", []):
        if s.get("active"):
            try:
                tunnel_start(s["id"])
            except Exception as e:
                print(f"[share] failed to restore tunnel for {s.get('id')}: {e}", flush=True)


def tunnel_status(rec):
    """Liveness + URL summary for one share record. Status values:
    running / starting / stopped / exited / error / no-cloudflared."""
    with _TUNNELS_LOCK:
        t = TUNNELS.get(rec.get("id"))
    if t is not None and t.proc.poll() is None:
        status = "running" if t.url else "starting"
        return {"status": status, "url": t.url or "", "pid": t.proc.pid,
                "error": ""}
    if t is not None:
        # Process object still known but dead.
        status = t.state if t.state in ("error", "exited", "stopped") else "stopped"
        return {"status": status, "url": "", "pid": None, "error": t.error or ""}
    if rec.get("active") and not find_cloudflared():
        return {"status": "no-cloudflared", "url": "", "pid": None,
                "error": "cloudflared binary not found"}
    return {"status": "stopped", "url": "", "pid": None, "error": ""}


# ═════════════════════════════════════════════════════════════════════════
# 3. Comments — per-project store, shared by gate + editor endpoints
# ═════════════════════════════════════════════════════════════════════════

def _comments_path(project_root):
    return os.path.join(project_root, "share", "comments.json")


def comments_load(project_root):
    p = _comments_path(project_root)
    if not os.path.isfile(p):
        return {"comments": []}
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f) or {}
    except Exception:
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
    computed: { selector, tag?, text? } — selector is the primary locator,
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
    return True


def comments_mark_processed(project_root, comment_ids):
    """Stamp processedAt on the given comments — called when the editor
    dispatches them to an agent run. Status is left alone; 'processed' is
    an orthogonal chip in the UI (the agent's edit may or may not satisfy
    the reviewer — they decide when to mark done)."""
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
# 4. Gate — the ONLY surface a tunnel exposes
# ═════════════════════════════════════════════════════════════════════════

_GATE_SERVER = None

# Live Session — late-bound so live.py can import shares without a cycle.
# serve.py calls register_live(live.GATE) at boot; the gate delegates any
# /s/<token>/live* route to it. None → live session disabled (gate still
# serves view+comment routes).
_LIVE = None

def register_live(gate):
    global _LIVE
    _LIVE = gate

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
    own tree and the design-system library it links are reachable — NOT
    the project's other prototypes, workflow/, editor/, or docs."""
    slug = rec.get("prototype") or ""
    allowed_prefixes = (f"source/{slug}/", "design-systems/")
    return any(rel == p.rstrip("/") or rel.startswith(p) for p in allowed_prefixes)


class GateHandler(http.server.BaseHTTPRequestHandler):
    """Minimal, share-scoped request handler. Deliberately NOT a subclass
    of the daemon's H — sharing zero routing code is the point."""
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
        # NOTE: "" (no trailing slash) and "/" are distinct — do_GET 301s
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
        # Root-absolute font passthrough — DS stylesheets may reference
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
        # Live Session — the REAL editor (served at /s/<tok>/live/) makes
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
        # Live Session routes (/s/<token>/live*) — delegated to live.py.
        if _LIVE is not None and (sub == "/live" or sub.startswith("/live/")):
            if _LIVE.handle_get(self, rec, sub):
                return
        # Viewer shell + assets.
        if sub == "/":
            return self._send_file(os.path.join(INSTALL_ROOT, "editor", "share", "viewer.html"))
        if sub in ("/viewer.js", "/viewer.css"):
            return self._send_file(os.path.join(INSTALL_ROOT, "editor", "share", sub.lstrip("/")))
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
        # Whitelisted project files. /p/ is the share viewer's prefix; the live
        # editor's prototype iframes load /source/… and /design-systems/…
        # directly (resolved relative to /s/<tok>/live/) — serve both through
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
        """th_live=<token> cookie set when the editor index was served — scopes
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
        # Real-editor root-absolute writes (guest mode is read-only) → no-op.
        if _LIVE is not None and not parsed.path.startswith("/s/"):
            tok = self._live_cookie()
            if tok and _LIVE.handle_rooted_post(self, tok, parsed.path):
                return
        rec, sub = self._route()
        if rec is None:
            return
        # Live Session routes (/s/<token>/live*) — delegated to live.py.
        if _LIVE is not None and sub.startswith("/live/"):
            if _LIVE.handle_post(self, rec, sub):
                return
        root = self._project_root(rec)
        if root is None:
            return self._send_json(500, {"error": "project unavailable"})
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
            m = re.match(r"^/api/comments/([cr]-[a-f0-9]+)/(reply|status|delete)$", sub)
            if m:
                cid, op = m.group(1), m.group(2)
                if op == "reply":
                    author = self._require_author(rec, body)
                    reply = comment_reply(root, cid, text=body.get("text"), author=author)
                    _notify_comments_changed(rec.get("project"), rec.get("prototype"))
                    return self._send_json(200, {"ok": True, "reply": reply})
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
    port. Idempotent — repeated calls return the existing port."""
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
# 5. Status summary — what GET /__shares returns per record
# ═════════════════════════════════════════════════════════════════════════

def share_summary(rec):
    """Record + live status + comment counts, ready for the UI."""
    out = dict(rec)
    out.pop("token", None)   # editor uses shareUrl below; token stays server-side-ish
    st = tunnel_status(rec)
    out["status"] = st["status"]
    out["pid"]    = st["pid"]
    out["error"]  = st["error"]
    url = st["url"] or (rec.get("lastUrl") if st["status"] == "running" else "")
    # While running, the canonical link is <tunnel-url>/s/<token>/.
    out["shareUrl"] = (url.rstrip("/") + "/s/" + rec.get("token", "") + "/") if url else ""
    out["localUrl"] = (f"http://127.0.0.1:{GATE_PORT}/s/{rec.get('token','')}/"
                       if GATE_PORT else "")
    out["urlChanged"] = bool(rec.get("prevUrl")) and rec.get("prevUrl") != rec.get("lastUrl")
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

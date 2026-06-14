"""Live Session — host-authoritative multiplayer over the share gate.

The realtime sibling of share mode (editor/shares.py). Where shares.py exposes a
prototype for *view + comment*, live.py exposes the host's living project for
*co-editing*: guests join through the SAME cloudflared tunnel + gate, get live
cursors, claim per-element leases, co-edit the workflow canvas, and trigger the
HOST's agent. There is exactly one source of truth (the host's tree) and one
agent (the host's daemon).

Design of record: docs/features/live-session.md.

Architecture (mirrors shares.py's daemon-side ownership):

  SESSIONS   — in-memory, per share. Volatile by design: a session is presence +
               leases + guest tokens + a set of SSE waiters. Nothing here is
               persisted — close the daemon and sessions are gone (the doc's
               "session dies with the host's laptop" property).

  GATE WIRING — shares.py owns the single gate listener. live.py registers itself
               via shares.register_live(); the GateHandler delegates any
               /s/<token>/live* route to handle_gate_get/post here. No second
               server, no import cycle (live imports shares; shares late-binds
               live).

  BRIDGE     — the daemon (serve.py) broadcasts workflow/asset changes per
               project_id over its own SSE channel; serve.py also calls
               notify_project_changed() here so live guests see the host's edits
               (and each other's, since guest ops route back through the daemon's
               normal broadcast). live.py never writes workflow.json directly —
               it calls the apply_node_op / dispatch_run callbacks serve.py wired
               at init(), so every write goes through the daemon's locked,
               broadcasting save path.

serve.py wiring (see "live session" section there):
     init(...)                              once at boot
     shares.register_live(GATE)             once at boot
     notify_project_changed(pid, ev, data)  from _broadcast_workflow_change /
                                            _broadcast_asset_change
"""

import json
import re
import secrets
import threading
import time
import urllib.parse

import shares as _shares     # read share records (token→share, share→project)
import git_ops as _git        # git/GitHub backbone for fork + PR + device-flow OAuth

# ── Module config (set once by init()) ──────────────────────────────────────

INSTALL_ROOT = None             # where editor/live/* client assets live
_RESOLVE_PROJECT_ROOT = None    # fn(project_id) -> abs path (raises ValueError)
_READ_WORKFLOW = None           # fn(project_root) -> dict (sanitized workflow)
_APPLY_NODE_OP = None           # fn(project_id, op, author) -> dict | raises
_DISPATCH_RUN = None            # fn(project_id, node_id, author) -> {runId} | raises
DAEMON_PORT = None              # main daemon port — proxied (read-only) so guests run the REAL editor

LEASE_TTL_S      = 30.0         # a lease auto-expires this long after last touch
PARTICIPANT_TTL_S = 35.0       # a participant goes stale this long after last beat
PRESENCE_MIN_INTERVAL_S = 0.03 # server-side floor on per-guest presence rate

TOKEN_OK = re.compile(r"^[a-f0-9]{32}$")
NAME_SAFE_FILE = re.compile(r"^[A-Za-z0-9._-]+$")
ROLES = ("editor", "viewer")
# Lease targets: node:<id> | wb:<id> | file:<rel>
TARGET_OK = re.compile(r"^(node|wb|file):[A-Za-z0-9_./-]{1,200}$")


def init(install_root, resolve_project_root, read_workflow,
         apply_node_op, dispatch_run, daemon_port=None):
    """Called once from serve.py before any other function here."""
    global INSTALL_ROOT, _RESOLVE_PROJECT_ROOT, _READ_WORKFLOW
    global _APPLY_NODE_OP, _DISPATCH_RUN, DAEMON_PORT
    INSTALL_ROOT = install_root
    _RESOLVE_PROJECT_ROOT = resolve_project_root
    _READ_WORKFLOW = read_workflow
    _APPLY_NODE_OP = apply_node_op
    _DISPATCH_RUN = dispatch_run
    DAEMON_PORT = daemon_port


def _now():
    return time.time()


import os as _os
_CANON_CACHE = {}

def _canon(project_id):
    """Normalize a project id to basename(project_root) so the daemon's
    broadcast id (keyed by basename) and a session's share-project field match
    even in single-project / workspace modes. Cached; resolve failures fall
    back to the raw id."""
    if not project_id:
        return ""
    hit = _CANON_CACHE.get(project_id)
    if hit is not None:
        return hit
    val = project_id
    try:
        root = _RESOLVE_PROJECT_ROOT(project_id)
        val = _os.path.basename(root.rstrip("/")) or project_id
    except Exception:
        pass
    _CANON_CACHE[project_id] = val
    return val


# ═════════════════════════════════════════════════════════════════════════
# 1. Session state — in-memory, per share
# ═════════════════════════════════════════════════════════════════════════

class _Waiter:
    """Per-SSE-connection waiter: a wake signal + an ordered queue of pending
    (event_type, data) tuples. Same shape as serve.py's WorkflowWaiter."""
    __slots__ = ("_signal", "_pending", "_lock")

    def __init__(self):
        self._signal = threading.Event()
        self._pending = []
        self._lock = threading.Lock()

    def push(self, event_type, data):
        with self._lock:
            self._pending.append((event_type, data))
        self._signal.set()

    def wait(self, timeout=25.0):
        fired = self._signal.wait(timeout=timeout)
        if fired:
            self._signal.clear()
        return fired

    def drain(self):
        with self._lock:
            out = self._pending[:]
            self._pending.clear()
            return out


class _Session:
    """One live session, keyed by share_id. All fields guarded by `lock`
    except the waiter set ops (which take the lock too). Volatile — never
    persisted."""
    __slots__ = ("share_id", "project_id", "active", "participants",
                 "leases", "tokens", "waiters", "lock", "_last_presence",
                 "_writes", "credits")

    def __init__(self, share_id, project_id):
        self.share_id = share_id
        self.project_id = project_id
        self.active = False
        self.participants = {}   # guestId -> {name,email,color,role,github,lastSeen,cursor,selection}
        self.leases = {}         # target -> {holder(guestId), holderName, expiresAt, kind}
        self.tokens = {}         # token -> guestId
        self.waiters = set()
        self.lock = threading.Lock()
        self._last_presence = {} # guestId -> ts (rate floor)
        self._writes = {}        # guestId -> [recent write timestamps] (rate cap)
        self.credits = {}        # "Name <github>" -> True  (guests who triggered work; drained at commit)


_SESSIONS = {}                   # share_id -> _Session
_SESSIONS_LOCK = threading.Lock()

# Palette for participant cursors — assigned round-robin on join.
_COLORS = ["#F5172A", "#2D7FF9", "#16A34A", "#9333EA", "#EA580C",
           "#0891B2", "#DB2777", "#CA8A04", "#4F46E5", "#0D9488"]


def _session(share_id, project_id=None):
    with _SESSIONS_LOCK:
        s = _SESSIONS.get(share_id)
        if s is None:
            if project_id is None:
                return None
            s = _Session(share_id, project_id)
            _SESSIONS[share_id] = s
        return s


def session_start(share_id):
    """Host intent: open a live session for this share. Idempotent."""
    rec = _shares.share_get(share_id)
    if rec is None:
        raise ValueError(f"unknown share: {share_id}")
    s = _session(share_id, rec.get("project") or "")
    with s.lock:
        s.active = True
    return True


def session_stop(share_id):
    """End the session: revoke all guest tokens, drop participants, signal
    every waiter so its SSE loop closes. The /live routes then 404 for new
    joins until restarted."""
    with _SESSIONS_LOCK:
        s = _SESSIONS.get(share_id)
    if s is None:
        return False
    with s.lock:
        s.active = False
        s.participants.clear()
        s.leases.clear()
        s.tokens.clear()
        waiters = list(s.waiters)
    for w in waiters:
        w.push("session-ended", {})
    return True


def session_active(share_id):
    with _SESSIONS_LOCK:
        s = _SESSIONS.get(share_id)
    return bool(s and s.active)


def session_summary(share_id):
    """For the host UI: is it live, who's connected."""
    with _SESSIONS_LOCK:
        s = _SESSIONS.get(share_id)
    if s is None:
        return {"active": False, "participants": []}
    with s.lock:
        _reap(s)
        return {
            "active": s.active,
            "participants": [
                {"guestId": g, "name": p["name"], "color": p["color"],
                 "role": p["role"], "github": p.get("github") or ""}
                for g, p in s.participants.items()
            ],
        }


# ── reaping stale participants + leases (called under s.lock) ───────────────

def _reap(s):
    now = _now()
    dead = [g for g, p in s.participants.items()
            if now - p.get("lastSeen", 0) > PARTICIPANT_TTL_S]
    for g in dead:
        s.participants.pop(g, None)
        # drop their tokens + leases
        for tok in [t for t, gid in s.tokens.items() if gid == g]:
            s.tokens.pop(tok, None)
        for tgt in [t for t, l in s.leases.items() if l.get("holder") == g]:
            s.leases.pop(tgt, None)
    expired = [t for t, l in s.leases.items() if now > l.get("expiresAt", 0)]
    for t in expired:
        s.leases.pop(t, None)
    return bool(dead or expired)


def _roster(s):
    return [{"guestId": g, "name": p["name"], "color": p["color"],
             "role": p["role"], "github": p.get("github") or "",
             "cursor": p.get("cursor"), "selection": p.get("selection")}
            for g, p in s.participants.items()]


def _leases_public(s):
    return [{"target": t, "holder": l["holder"], "holderName": l.get("holderName", ""),
             "expiresAt": l["expiresAt"]} for t, l in s.leases.items()]


# ═════════════════════════════════════════════════════════════════════════
# 2. Broadcast — fan out to this session's SSE waiters
# ═════════════════════════════════════════════════════════════════════════

def broadcast(share_id, event_type, data):
    with _SESSIONS_LOCK:
        s = _SESSIONS.get(share_id)
    if s is None:
        return
    with s.lock:
        waiters = list(s.waiters)
    for w in waiters:
        try:
            w.push(event_type, data)
        except Exception:
            pass


def notify_project_changed(project_id, event_type, data):
    """Bridge from serve.py's _broadcast_workflow_change / _broadcast_asset_change.
    Fan the daemon's per-project event out to every live session on that
    project so guests see the host's (and each other's) committed edits."""
    if not project_id:
        return
    canon = _canon(project_id)
    with _SESSIONS_LOCK:
        targets = [s for s in _SESSIONS.values()
                   if s.active and _canon(s.project_id) == canon]
    for s in targets:
        with s.lock:
            waiters = list(s.waiters)
        for w in waiters:
            try:
                w.push(event_type, data or {})
            except Exception:
                pass


# ═════════════════════════════════════════════════════════════════════════
# 3. Identity — join + token auth
# ═════════════════════════════════════════════════════════════════════════

def _clip(v, n):
    return v[:n] if isinstance(v, str) else ""


def join(rec, name, email, github=None, client_id=None):
    """Issue a guest a session token. Always needs a display name; the share's
    email gate additionally needs a plausible email (same policy as comments).

    `client_id` is a stable per-browser id (localStorage) — when present, a
    refresh REUSES the same participant instead of spawning a duplicate user
    (the old one would otherwise linger until the TTL reap)."""
    share_id = rec.get("id")
    s = _session(share_id, rec.get("project") or "")
    if not s.active:
        raise PermissionError("this session is not live")
    name = _clip(name, 80).strip()
    if not name:
        raise PermissionError("a display name is required to join")
    email = _clip(email, 120).strip().lower()
    if rec.get("emailGate") and not _shares.EMAIL_OK.match(email or ""):
        raise PermissionError("this session requires an email address to join")
    role = rec.get("roleDefault") if rec.get("roleDefault") in ROLES else "editor"
    client_id = _clip(client_id, 64).strip()
    with s.lock:
        guest_id = None
        # Reuse an existing participant for this browser (refresh-stable).
        if client_id:
            for gid, p in s.participants.items():
                if p.get("clientId") == client_id:
                    guest_id = gid
                    break
        if guest_id is None:
            guest_id = "g-" + secrets.token_hex(4)
            color = _COLORS[len(s.participants) % len(_COLORS)]
            s.participants[guest_id] = {
                "name": name, "email": email, "color": color, "role": role,
                "github": _clip(github, 80).strip() or "", "lastSeen": _now(),
                "cursor": None, "selection": None, "clientId": client_id,
            }
        else:
            p = s.participants[guest_id]
            p["name"] = name; p["lastSeen"] = _now()
            if email: p["email"] = email
            color = p["color"]; role = p["role"]
        token = secrets.token_hex(16)
        s.tokens[token] = guest_id
        roster = _roster(s)
    broadcast(share_id, "roster", {"participants": roster})
    return {"guestId": guest_id, "token": token, "role": role,
            "color": color, "participants": roster}


def _auth(s, token):
    """Resolve a guest token to its participant, refreshing lastSeen. Raises
    PermissionError if unknown/revoked."""
    if not token or not TOKEN_OK.match(token):
        raise PermissionError("missing or malformed session token")
    with s.lock:
        guest_id = s.tokens.get(token)
        if guest_id is None or guest_id not in s.participants:
            raise PermissionError("session token unknown or revoked")
        p = s.participants[guest_id]
        p["lastSeen"] = _now()
        return guest_id, p


def _require_editor(p):
    if p.get("role") != "editor":
        raise PermissionError("viewer role cannot edit — ask the host for editor access")


WRITE_RATE_LIMIT = 80           # max mutating ops / guest / second (generous: a
                                # 50ms drag stream is 20/s; this only catches abuse)

def _rate_guard(s, guest_id):
    now = _now()
    with s.lock:
        log = s._writes.setdefault(guest_id, [])
        cutoff = now - 1.0
        while log and log[0] < cutoff:
            log.pop(0)
        if len(log) >= WRITE_RATE_LIMIT:
            raise PermissionError("too many requests — slow down")
        log.append(now)


def _credit_line(p):
    """Co-authored-by line for a guest. Uses their GitHub handle when known so
    the trailer attaches to a real account; falls back to name + noreply."""
    name = p.get("name") or "guest"
    gh = (p.get("github") or "").strip().lstrip("@")
    if gh:
        return f"{name} <{gh}@users.noreply.github.com>"
    email = (p.get("email") or "").strip()
    return f"{name} <{email or 'guest@woven.local'}>"


def take_credits(share_id):
    """Drain + return the set of Co-authored-by lines accrued since the last
    commit (phase 5). Clears them so the next commit starts fresh."""
    with _SESSIONS_LOCK:
        s = _SESSIONS.get(share_id)
    if s is None:
        return []
    with s.lock:
        lines = sorted(s.credits.keys())
        s.credits.clear()
    return lines


def kick(share_id, guest_id):
    """Host action: revoke a guest. Their next write 403s, presence drops."""
    with _SESSIONS_LOCK:
        s = _SESSIONS.get(share_id)
    if s is None:
        return False
    with s.lock:
        s.participants.pop(guest_id, None)
        for tok in [t for t, g in s.tokens.items() if g == guest_id]:
            s.tokens.pop(tok, None)
        for tgt in [t for t, l in s.leases.items() if l.get("holder") == guest_id]:
            s.leases.pop(tgt, None)
        roster = _roster(s)
    broadcast(share_id, "kicked", {"guestId": guest_id})
    broadcast(share_id, "roster", {"participants": roster})
    return True


def set_role(share_id, guest_id, role):
    if role not in ROLES:
        raise ValueError(f"invalid role: {role!r}")
    with _SESSIONS_LOCK:
        s = _SESSIONS.get(share_id)
    if s is None:
        return False
    with s.lock:
        p = s.participants.get(guest_id)
        if p is None:
            return False
        p["role"] = role
        # losing editor drops their leases
        if role != "editor":
            for tgt in [t for t, l in s.leases.items() if l.get("holder") == guest_id]:
                s.leases.pop(tgt, None)
        roster = _roster(s)
    broadcast(share_id, "roster", {"participants": roster})
    return True


# ═════════════════════════════════════════════════════════════════════════
# 4. Presence — ephemeral cursors, never persisted
# ═════════════════════════════════════════════════════════════════════════

def presence(s, token, cursor, selection):
    guest_id, p = _auth(s, token)
    now = _now()
    with s.lock:
        last = s._last_presence.get(guest_id, 0)
        if now - last < PRESENCE_MIN_INTERVAL_S:
            return  # rate floor — drop silently
        s._last_presence[guest_id] = now
        if isinstance(cursor, dict):
            p["cursor"] = {"x": _num(cursor.get("x")), "y": _num(cursor.get("y")),
                           "page": _clip(cursor.get("page"), 200)}
        if selection is not None:
            p["selection"] = _clip(selection, 200) or None
        color = p["color"]; name = p["name"]
    broadcast(s.share_id, "presence", {
        "guestId": guest_id, "name": name, "color": color,
        "cursor": p["cursor"], "selection": p["selection"],
    })


def _num(v):
    try:
        return float(v)
    except Exception:
        return 0.0


# ═════════════════════════════════════════════════════════════════════════
# 5. Leases — per-element locks, server-enforced
# ═════════════════════════════════════════════════════════════════════════

def lease_acquire(s, token, target):
    guest_id, p = _auth(s, token)
    _require_editor(p)
    _rate_guard(s, guest_id)
    if not isinstance(target, str) or not TARGET_OK.match(target):
        raise ValueError("invalid lease target")
    now = _now()
    with s.lock:
        cur = s.leases.get(target)
        if cur and cur.get("holder") != guest_id and now <= cur.get("expiresAt", 0):
            return {"ok": False, "held": True, "holder": cur["holder"],
                    "holderName": cur.get("holderName", "")}
        s.leases[target] = {"holder": guest_id, "holderName": p["name"],
                            "expiresAt": now + LEASE_TTL_S, "kind": target.split(":", 1)[0]}
        leases = _leases_public(s)
    broadcast(s.share_id, "lock", {"leases": leases})
    return {"ok": True, "expiresAt": now + LEASE_TTL_S}


def lease_release(s, token, target):
    guest_id, p = _auth(s, token)
    with s.lock:
        cur = s.leases.get(target)
        if cur and cur.get("holder") == guest_id:
            s.leases.pop(target, None)
        leases = _leases_public(s)
    broadcast(s.share_id, "lock", {"leases": leases})
    return {"ok": True}


def lease_heartbeat(s, token, targets):
    guest_id, p = _auth(s, token)
    now = _now()
    if not isinstance(targets, list):
        targets = []
    with s.lock:
        for t in targets:
            cur = s.leases.get(t)
            if cur and cur.get("holder") == guest_id:
                cur["expiresAt"] = now + LEASE_TTL_S
    return {"ok": True}


def _holds_lease(s, guest_id, target):
    now = _now()
    cur = s.leases.get(target)
    return bool(cur and cur.get("holder") == guest_id and now <= cur.get("expiresAt", 0))


# ═════════════════════════════════════════════════════════════════════════
# 6. Canvas ops — lease-checked, routed through the daemon's locked save
# ═════════════════════════════════════════════════════════════════════════

def apply_op(s, token, op):
    """A guest mutates the host's workflow (move/edit a node, move a wb item).
    Lease-checked here, then handed to the daemon's apply_node_op callback,
    which writes under the per-project lock and fires the normal broadcast
    (so host + every guest converge)."""
    guest_id, p = _auth(s, token)
    _require_editor(p)
    _rate_guard(s, guest_id)
    if not isinstance(op, dict):
        raise ValueError("op must be an object")
    target = op.get("target")
    if not isinstance(target, str) or not TARGET_OK.match(target):
        raise ValueError("op.target invalid")
    # Moves are cosmetic layout (last-writer-wins per the doc) and don't need a
    # lease; content edits DO. opKind == "move" is the only lease-free op.
    op_kind = op.get("op")
    if op_kind != "move" and not _holds_lease(s, guest_id, target):
        raise PermissionError(f"acquire a lease on {target} before editing it")
    author = {"name": p["name"], "email": p.get("email") or "",
              "github": p.get("github") or "", "guestId": guest_id}
    result = _APPLY_NODE_OP(s.project_id, op, author)
    # Credit content edits (not bare moves) on the next host commit.
    if op_kind != "move":
        with s.lock:
            s.credits[_credit_line(p)] = True
    # No explicit broadcast here — apply_node_op → daemon broadcast → bridge.
    return {"ok": True, "result": result}


# ═════════════════════════════════════════════════════════════════════════
# 7. Run trigger — fire the HOST's agent on a node
# ═════════════════════════════════════════════════════════════════════════

def trigger_run(s, token, node_id):
    guest_id, p = _auth(s, token)
    _require_editor(p)
    _rate_guard(s, guest_id)
    if not isinstance(node_id, str) or not re.match(r"^[A-Za-z0-9_.-]{1,80}$", node_id):
        raise ValueError("invalid node id")
    author = {"name": p["name"], "email": p.get("email") or "",
              "github": p.get("github") or "", "guestId": guest_id}
    # Credit this guest on the next host commit (Co-authored-by, phase 5).
    with s.lock:
        s.credits[_credit_line(p)] = True
    # Lease the node for the run so no one edits it mid-run; the completion
    # hook clears it (serve.py calls lease_release_agent on finish).
    now = _now()
    with s.lock:
        s.leases["node:" + node_id] = {
            "holder": "agent", "holderName": f"agent (via {p['name']})",
            "expiresAt": now + 600.0, "kind": "agent"}
        leases = _leases_public(s)
    broadcast(s.share_id, "lock", {"leases": leases})
    try:
        result = _DISPATCH_RUN(s.project_id, node_id, author)
    except Exception:
        # release the agent lease if dispatch failed
        with s.lock:
            cur = s.leases.get("node:" + node_id)
            if cur and cur.get("holder") == "agent":
                s.leases.pop("node:" + node_id, None)
            leases = _leases_public(s)
        broadcast(s.share_id, "lock", {"leases": leases})
        raise
    return {"ok": True, "run": result}


# ═════════════════════════════════════════════════════════════════════════
# 7b. GitHub — device-flow OAuth + fork + PR (guest "take it home" path)
# ═════════════════════════════════════════════════════════════════════════
# The guest authenticates IN the collab client via GitHub Device Flow (no
# redirect URI — works through a churning quick-tunnel hostname). The token is
# held SERVER-SIDE on the participant record and never sent to the browser; the
# gate performs fork + PR on the guest's behalf under their identity.

def github_device_start(s, token):
    guest_id, p = _auth(s, token)
    out = _git.device_start()
    with s.lock:
        p["_ghDevice"] = out.get("device_code")
    return {"user_code": out.get("user_code"),
            "verification_uri": out.get("verification_uri"),
            "interval": out.get("interval", 5), "expires_in": out.get("expires_in", 900)}


def github_device_poll(s, token):
    guest_id, p = _auth(s, token)
    dc = p.get("_ghDevice")
    if not dc:
        raise ValueError("start the device flow first")
    out = _git.device_poll(dc)
    if out.get("access_token"):
        tok = out["access_token"]
        try:
            u = _git.gh_user(tok)
        except Exception:
            u = {"login": ""}
        with s.lock:
            p["ghToken"] = tok
            p["github"] = u.get("login") or ""
            p.pop("_ghDevice", None)
            roster = _roster(s)
        broadcast(s.share_id, "roster", {"participants": roster})
        return {"status": "ok", "login": u.get("login") or "", "avatar": u.get("avatar") or ""}
    err = out.get("error")
    if err in ("authorization_pending", "slow_down"):
        return {"status": "pending", "slowDown": err == "slow_down"}
    return {"status": "error", "error": out.get("error_description") or err or "unknown"}


def _project_remote(rec):
    root = _proot(rec)
    if root is None:
        raise RuntimeError("project unavailable")
    st = _git.status(root)
    remote = st.get("remote")
    if not remote:
        raise RuntimeError("this project isn't connected to GitHub yet — ask the host to connect it")
    owner, repo = _git.parse_owner_repo(remote)
    if not owner:
        raise RuntimeError("could not parse the GitHub repo from the remote URL")
    return owner, repo, st


def github_fork(s, rec, token):
    guest_id, p = _auth(s, token)
    if not p.get("ghToken"):
        raise PermissionError("connect your GitHub account first")
    owner, repo, _st = _project_remote(rec)
    return _git.fork(p["ghToken"], owner, repo)


def github_pr(s, rec, token, body):
    guest_id, p = _auth(s, token)
    if not p.get("ghToken"):
        raise PermissionError("connect your GitHub account first")
    owner, repo, st = _project_remote(rec)
    head = (body or {}).get("head")
    if not head:
        raise ValueError("head branch required (forkOwner:branch)")
    title = ((body or {}).get("title") or "Live session changes")[:200]
    prbody = ((body or {}).get("body") or "")[:5000]
    base = (body or {}).get("base") or st.get("branch") or "main"
    return _git.open_pr(p["ghToken"], owner, repo, head, title, prbody, base)


# ═════════════════════════════════════════════════════════════════════════
# 7c. Host-side presence — so the HOST (in their own editor, on the daemon)
# sees guests' cursors and broadcasts their own. The host editor loads
# /__live_cursors.js (injected by serve.py) which talks to the daemon endpoints
# below; no guest token (the host is trusted daemon-side).
# ═════════════════════════════════════════════════════════════════════════

HOST_GID = "host"

def _active_sessions_for_project(project_id):
    canon = _canon(project_id)
    with _SESSIONS_LOCK:
        return [s for s in _SESSIONS.values() if s.active and _canon(s.project_id) == canon]

def project_has_live_session(project_id):
    return bool(_active_sessions_for_project(project_id))

def _ensure_host(s):
    p = s.participants.get(HOST_GID)
    if p is None:
        p = {"name": "Host", "color": "#111827", "role": "editor", "github": "",
             "lastSeen": _now(), "cursor": None, "selection": None}
        s.participants[HOST_GID] = p
    return p

def host_presence(project_id, cursor):
    for s in _active_sessions_for_project(project_id):
        with s.lock:
            p = _ensure_host(s)
            p["lastSeen"] = _now()
            if isinstance(cursor, dict):
                p["cursor"] = {"x": _num(cursor.get("x")), "y": _num(cursor.get("y")),
                               "page": _clip(cursor.get("page"), 200)}
            name, color, cur = p["name"], p["color"], p["cursor"]
        broadcast(s.share_id, "presence",
                  {"guestId": HOST_GID, "name": name, "color": color, "cursor": cur, "selection": None})
    return {"ok": True}

def host_events_stream(h, project_id):
    """Daemon-side SSE for the host editor: streams presence/lock/roster of the
    project's live session. No token (host is trusted)."""
    sessions = _active_sessions_for_project(project_id)
    if not sessions:
        return _json(h, 409, {"error": "no live session"})
    s = sessions[0]
    h.close_connection = True
    h.send_response(200)
    h.send_header("Content-Type", "text/event-stream; charset=utf-8")
    h.send_header("Cache-Control", "no-store")
    h.send_header("Connection", "close")
    h.send_header("X-Accel-Buffering", "no")
    h.send_header("Transfer-Encoding", "chunked")  # stream through cloudflared
    h.end_headers()
    _sse_pad(h)  # fill proxy buffer so events start flowing over a tunnel
    waiter = _Waiter()
    with s.lock:
        s.waiters.add(waiter)
        _ensure_host(s)
        roster = _roster(s); leases = _leases_public(s)
    try:
        _sse_write(h, "live-connected", {"guestId": HOST_GID})
        _sse_write(h, "roster", {"participants": roster})
        _sse_write(h, "lock", {"leases": leases})
        while True:
            fired = waiter.wait(timeout=25)
            with s.lock:
                hp = s.participants.get(HOST_GID)
                if hp is not None:
                    hp["lastSeen"] = _now()
                still = s.active
            if not still:
                _sse_write(h, "session-ended", {}); return True
            if fired:
                for et, ed in waiter.drain():
                    if not _sse_write(h, et, ed):
                        return True
            else:
                try:
                    _sse_chunk(h, b": heartbeat\n\n")
                except Exception:
                    return True
    finally:
        with s.lock:
            s.waiters.discard(waiter)


def release_agent_lease(project_id, node_id):
    """Called by serve.py's node-finish hook: drop the agent lease so guests
    can edit the node again."""
    canon = _canon(project_id)
    with _SESSIONS_LOCK:
        targets = [s for s in _SESSIONS.values() if _canon(s.project_id) == canon]
    for s in targets:
        changed = False
        with s.lock:
            cur = s.leases.get("node:" + node_id)
            if cur and cur.get("holder") == "agent":
                s.leases.pop("node:" + node_id, None)
                changed = True
            leases = _leases_public(s)
        if changed:
            broadcast(s.share_id, "lock", {"leases": leases})


# ═════════════════════════════════════════════════════════════════════════
# 8. Gate routing — delegated from shares.GateHandler for /s/<token>/live*
# ═════════════════════════════════════════════════════════════════════════
# shares.py calls GATE.handle_get(handler, rec, sub) / handle_post(...) where
# `sub` already has the "/live" prefix (e.g. "/live", "/live/api/presence").
# Returns True if it handled the request (replied), False to let the gate fall
# through to its own 404.

# ── Serve the REAL editor through the gate (Phase A — read-only) ─────────────
# So guests render with the actual WorkflowCanvas + node components + styles.css
# (zero interpretation). Static editor files come straight from disk; project-
# scoped / daemon-generated resources are PROXIED to the local daemon, GET-only,
# with project FORCED to the share's project (the client cannot widen scope).
# Writes are refused. This deliberately widens the gate to a read-proxy — scoped
# to one project + a read whitelist.

# Editor files served verbatim from <install>/editor/.
_EDITOR_STATIC_FILES = {
    "app.js", "styles.css", "landing-shaders.js", "index.html",
}
_EDITOR_STATIC_DIR_PREFIXES = ("prompts/",)
# Root-absolute daemon GET paths a guest may read. Everything else 404s.
# Deliberately EXCLUDES writes, chat/run transcripts, project/share/git
# management, export — reads the canvas needs only.
_PROXY_READ_PREFIXES = (
    "/__workflow", "/__ds_bootstrap", "/__source", "/__asset",
    "/__preview", "/__layout", "/__starred_prototypes", "/__media",
    "/__local_status", "/__fonts", "/__global_fonts",
)

def _proxy_read_ok(path):
    return any(path == p or path.startswith(p) for p in _PROXY_READ_PREFIXES)

def _share_for_token(token):
    if not token or not _shares.TOKEN_OK.match(token):
        return None
    return _shares.share_get_by_token(token)

def _editor_dir():
    return _os.path.join(INSTALL_ROOT, "editor")

def _serve_editor_static(h, rel):
    rel = rel.lstrip("/")
    ok = rel in _EDITOR_STATIC_FILES or any(rel.startswith(p) for p in _EDITOR_STATIC_DIR_PREFIXES)
    if not ok or ".." in rel.split("/") or rel.startswith("."):
        return _json(h, 404, {"error": "not found"})
    path = _os.path.realpath(_os.path.join(_editor_dir(), rel))
    if not path.startswith(_os.path.realpath(_editor_dir()) + _os.sep):
        return _json(h, 404, {"error": "not found"})
    if not _os.path.isfile(path):
        return _json(h, 404, {"error": "not found"})
    ctype = ("application/javascript; charset=utf-8" if path.endswith(".js")
             else "text/css; charset=utf-8" if path.endswith(".css")
             else "text/html; charset=utf-8" if path.endswith(".html")
             else "application/octet-stream")
    with open(path, "rb") as f:
        data = f.read()
    h.send_response(200)
    h.send_header("Content-Type", ctype)
    h.send_header("Content-Length", str(len(data)))
    h.send_header("Cache-Control", "no-store")
    h.end_headers()
    try: h.wfile.write(data)
    except Exception: pass
    return True

# Guest chrome lockdown — injected into the served editor so guests can't reach
# host-only affordances: Projects nav (leave to other projects), Settings/Exports
# (API keys!), and the node-creation rail/library. They keep the canvas, zoom,
# pan, and can co-edit existing nodes (which now sync). Tighten/loosen here.
_GUEST_LOCK_CSS = (
    "<style id=\"th-live-lock\">"
    # Hide ONLY the top bar (Projects nav / Settings / Exports live there).
    # Collapse it IN FLOW (not display:none) so its grid row stays and the
    # canvas still fills. The left node rail + editing tools STAY so guests can
    # build collaboratively.
    ".workflow-bar{visibility:hidden!important;height:0!important;min-height:0!important;"
    "padding:0!important;border:0!important;overflow:hidden!important}"
    # The bar lives in row 1 of .workflow-root's grid (~44px reserved); zero it
    # so there's no empty band where the bar used to be.
    ".workflow-root{grid-template-rows:0 minmax(0,1fr)!important}"
    "</style>"
).encode("utf-8")
# Injected before </body> so live cursors mount on the real canvas.
_GUEST_CURSORS_TAG = b'<script src="cursors.js" defer></script>'

def _live_cookie_header(h, token):
    """th_live cookie. Adds Secure when behind the HTTPS tunnel (Cloudflare sets
    X-Forwarded-Proto: https) — some browsers drop a non-Secure SameSite cookie
    on HTTPS, which would 404 the editor's root-absolute /app.js etc. → white."""
    proto = (h.headers.get("X-Forwarded-Proto") or "").lower()
    secure = "; Secure" if proto == "https" else ""
    return f"th_live={token}; Path=/; SameSite=Lax{secure}"


def _serve_editor_index(h, token):
    """Serve the real editor index.html + the th_live cookie that scopes its
    root-absolute requests to this share, with the guest chrome-lockdown CSS
    injected."""
    path = _os.path.join(_editor_dir(), "index.html")
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError:
        return _json(h, 404, {"error": "editor index not found"})
    # inject the lockdown stylesheet (</head>) + the live-cursors overlay (</body>)
    if b"</head>" in data:
        data = data.replace(b"</head>", _GUEST_LOCK_CSS + b"</head>", 1)
    if b"</body>" in data:
        data = data.replace(b"</body>", _GUEST_CURSORS_TAG + b"</body>", 1)
    h.send_response(200)
    h.send_header("Content-Type", "text/html; charset=utf-8")
    h.send_header("Content-Length", str(len(data)))
    h.send_header("Cache-Control", "no-store")
    h.send_header("Set-Cookie", _live_cookie_header(h, token))
    h.end_headers()
    try:
        h.wfile.write(data)
    except Exception:
        pass
    return True


def _proxy_daemon_read(h, path, query, project):
    """GET <daemon>/<path>?<query+project> and stream it back. Streams SSE.
    project is FORCED — any client-supplied project is overridden."""
    import urllib.request as _ur
    if DAEMON_PORT is None:
        return _json(h, 502, {"error": "daemon unavailable"})
    q = dict(urllib.parse.parse_qsl(query or ""))
    q["project"] = project
    url = f"http://127.0.0.1:{DAEMON_PORT}{path}?{urllib.parse.urlencode(q)}"
    import urllib.error as _ue
    try:
        req = _ur.Request(url, method="GET")
        acc = h.headers.get("Accept")
        if acc: req.add_header("Accept", acc)
        resp = _ur.urlopen(req, timeout=60)
    except _ue.HTTPError as e:
        # Forward the daemon's real status + body (e.g. a 404 layout.js stays a
        # 404, which the editor handles with onerror — not a scary 502).
        body = b""
        try: body = e.read()
        except Exception: pass
        h.send_response(e.code)
        h.send_header("Content-Type", e.headers.get("Content-Type", "application/json") if e.headers else "application/json")
        h.send_header("Content-Length", str(len(body)))
        h.send_header("Cache-Control", "no-store")
        h.end_headers()
        try: h.wfile.write(body)
        except Exception: pass
        return True
    except Exception as e:
        return _json(h, 502, {"error": f"proxy failed: {e}"})
    ctype = resp.headers.get("Content-Type", "application/octet-stream")
    if "text/event-stream" in ctype:
        # LONG-POLL — Cloudflare quick tunnels buffer a streaming body until the
        # connection CLOSES (proven: 0 bytes over 19s of a held SSE). So we don't
        # hold: forward daemon events until the FIRST real change (or a ~20s
        # idle cap), then CLOSE so the proxy/edge flushes. The browser's
        # EventSource auto-reconnects for the next poll. Latency ≈ RTT on a
        # change; on localhost it behaves the same, just with a reconnect per
        # change. The editor refetches /__workflow on each `*-changed` event.
        import time as _t
        h.close_connection = True
        h.send_response(getattr(resp, "status", 200))
        h.send_header("Content-Type", ctype)
        h.send_header("Cache-Control", "no-store")
        h.send_header("Connection", "close")
        h.send_header("X-Accel-Buffering", "no")
        h.end_headers()
        try: h.wfile.write(b"retry: 250\n\n")  # fast EventSource reconnect between polls
        except Exception: pass
        start = _t.monotonic()
        try:
            while _t.monotonic() - start < 20:
                line = resp.readline()
                if not line:
                    break
                try:
                    h.wfile.write(line)
                except Exception:
                    break
                if line.startswith(b"event:") and b"changed" in line:
                    break  # a real change — close so Cloudflare flushes it
            try: h.wfile.flush()
            except Exception: pass
        except Exception:
            pass
        try: resp.close()
        except Exception: pass
        return True
    body = resp.read()
    h.send_response(getattr(resp, "status", 200))
    h.send_header("Content-Type", ctype)
    h.send_header("Content-Length", str(len(body)))
    h.send_header("Cache-Control", resp.headers.get("Cache-Control", "no-store"))
    h.end_headers()
    try: h.wfile.write(body)
    except Exception: pass
    return True

def _serve_project_file(h, rec, rel):
    """Serve a whitelisted prototype/design-system file (read-only) — same
    realpath-contained, extension-checked logic the share viewer's /p/ uses.
    Powers the real editor's prototype iframes (which load /source/… directly)."""
    import mimetypes
    root = _proot(rec)
    if root is None:
        return _json(h, 500, {"error": "project unavailable"})
    rel = rel.split("?")[0].split("#")[0].strip("/")
    if not rel or ".." in rel.split("/") or rel.startswith("."):
        return _json(h, 404, {"error": "not found"})
    if not _shares._gate_project_paths_ok(rec, rel):
        return _json(h, 404, {"error": "not found"})
    abs_path = _os.path.realpath(_os.path.join(root, rel))
    rr = _os.path.realpath(root)
    if not (abs_path == rr or abs_path.startswith(rr + _os.sep)):
        return _json(h, 404, {"error": "not found"})
    if _os.path.isdir(abs_path):
        abs_path = _os.path.join(abs_path, "index.html")
    base = _os.path.basename(abs_path)
    ext = _os.path.splitext(base)[1].lower()
    if base.startswith(".") or ext not in _shares._GATE_SERVE_EXTS:
        return _json(h, 404, {"error": "not found"})
    if not _os.path.isfile(abs_path):
        return _json(h, 404, {"error": "not found"})
    ctype = mimetypes.guess_type(abs_path)[0] or "application/octet-stream"
    if ctype.startswith("text/") or ctype in ("application/javascript", "application/json", "image/svg+xml"):
        ctype += "; charset=utf-8"
    with open(abs_path, "rb") as f:
        body = f.read()
    h.send_response(200)
    h.send_header("Content-Type", ctype)
    h.send_header("Content-Length", str(len(body)))
    h.send_header("Cache-Control", "no-store")
    h.end_headers()
    try: h.wfile.write(body)
    except Exception: pass
    return True


def _rooted_get(h, token, path, query):
    """Root-absolute requests from the real editor (e.g. /app.js, /__workflow,
    /source/…), scoped by the th_live cookie. Called from shares.GateHandler
    when a th_live cookie is present and the path isn't a /s/<token>/ route."""
    rec = _share_for_token(token)
    if rec is None:
        return _json(h, 404, {"error": "unknown or revoked share"})
    project = rec.get("project") or ""
    rel = path.lstrip("/")
    # editor static (app.js, styles.css, prompts/*, landing-shaders.js)
    if rel in _EDITOR_STATIC_FILES or any(rel.startswith(p) for p in _EDITOR_STATIC_DIR_PREFIXES):
        return _serve_editor_static(h, rel)
    # prototype + design-system files — the editor's iframes load these
    if rel.startswith("source/") or rel.startswith("design-systems/"):
        return _serve_project_file(h, rec, rel)
    # project data files (data.js, <slug>.layout.js) → proxy to /editor/<file>
    if rel == "data.js" or re.match(r"^[A-Za-z0-9_.-]{1,80}\.layout\.js$", rel):
        return _proxy_daemon_read(h, "/editor/" + rel, query, project)
    # whitelisted daemon reads
    if path.startswith("/__") and _proxy_read_ok(path):
        return _proxy_daemon_read(h, path, query, project)
    return _json(h, 404, {"error": "not found"})

# Writes a guest's real editor may make → PROXIED to the host daemon so edits
# (node moves, content, runs, layout) land on the HOST's tree and sync to
# everyone. project FORCED. Everything else (file writes, project/share/git
# management, export) is refused.
_PROXY_WRITE_PREFIXES = ("/__workflow", "/__layout")

def _proxy_write_ok(path):
    return any(path == p or path.startswith(p) for p in _PROXY_WRITE_PREFIXES)

def _drain(h):
    try:
        n = int(h.headers.get("Content-Length") or 0)
        return h.rfile.read(n) if n > 0 else b""
    except Exception:
        return b""

def _proxy_daemon_write(h, path, project):
    """Forward a POST body to the daemon, project FORCED. Returns its response."""
    import urllib.request as _ur, urllib.error as _ue
    if DAEMON_PORT is None:
        _drain(h); return _json(h, 502, {"error": "daemon unavailable"})
    body = _drain(h)
    url = f"http://127.0.0.1:{DAEMON_PORT}{path}?project={urllib.parse.quote(project)}"
    req = _ur.Request(url, data=body, method="POST")
    ct = h.headers.get("Content-Type")
    if ct: req.add_header("Content-Type", ct)
    try:
        resp = _ur.urlopen(req, timeout=60)
        out, status = resp.read(), getattr(resp, "status", 200)
        rct = resp.headers.get("Content-Type", "application/json")
    except _ue.HTTPError as e:
        out, status = (e.read() if e else b""), (e.code if e else 500)
        rct = (e.headers.get("Content-Type", "application/json") if e and e.headers else "application/json")
    except Exception as e:
        return _json(h, 502, {"error": f"proxy write failed: {e}"})
    h.send_response(status)
    h.send_header("Content-Type", rct)
    h.send_header("Content-Length", str(len(out)))
    h.send_header("Cache-Control", "no-store")
    h.end_headers()
    try: h.wfile.write(out)
    except Exception: pass
    return True

def _rooted_post(h, token, path):
    """Writes from the guest's real editor. Whitelisted workflow/layout writes
    are PROXIED to the host daemon (so edits sync); everything else is drained
    + no-op'd so the editor doesn't error-spam."""
    rec = _share_for_token(token)
    if rec is None:
        _drain(h); return _json(h, 404, {"error": "unknown share"})
    s = _session(rec.get("id"), rec.get("project") or "")
    if not s.active:
        _drain(h); return _json(h, 409, {"error": "session not live"})
    if path.startswith("/__") and _proxy_write_ok(path):
        return _proxy_daemon_write(h, path, rec.get("project") or "")
    _drain(h)
    return _json(h, 200, {"ok": True, "readOnly": True})


class _LiveGate:
    # Root-absolute requests from the real editor, scoped by the th_live cookie
    # (called from shares.GateHandler before its /s/<tok>/ routing).
    def handle_rooted(self, h, token, path, query):
        return _rooted_get(h, token, path, query)

    def handle_rooted_post(self, h, token, path):
        return _rooted_post(h, token, path)

    def handle_get(self, h, rec, sub):
        share_id = rec.get("id")
        proj = rec.get("project") or ""
        s = _session(share_id, proj)
        # /live → /live/
        if sub == "/live":
            h.send_response(301)
            h.send_header("Location", urllib.parse.urlparse(h.path).path + "/")
            h.send_header("Content-Length", "0")
            h.end_headers()
            return True
        # ── The REAL editor (Phase A) ────────────────────────────────────
        # /live/ serves the actual editor index.html (workflow mode, the
        # share's project FORCED), sets the th_live cookie so its root-absolute
        # requests can be scoped, and is served read-only. Relative editor
        # assets resolve under /live/.
        if sub == "/live/":
            if not s.active:
                return _json(h, 409, {"error": "session not live"})
            parsed = urllib.parse.urlparse(h.path)
            qs = dict(urllib.parse.parse_qsl(parsed.query))
            if qs.get("project") != proj or qs.get("view") != "workflow":
                h.send_response(302)
                h.send_header("Location", parsed.path + "?" +
                              urllib.parse.urlencode({"project": proj, "view": "workflow"}))
                h.send_header("Set-Cookie", _live_cookie_header(h, rec.get('token')))
                h.send_header("Content-Length", "0")
                h.end_headers()
                return True
            return _serve_editor_index(h, rec.get("token"))
        if sub == "/live/cursors.js":
            return _serve_client(h, "cursors.js")   # editor/live/cursors.js
        if sub in ("/live/app.js", "/live/styles.css", "/live/landing-shaders.js") \
                or sub.startswith("/live/prompts/"):
            return _serve_editor_static(h, sub[len("/live/"):])
        m = re.match(r"^/live/(data\.js|[A-Za-z0-9_.-]{1,80}\.layout\.js)$", sub)
        if m:
            if not s.active:
                return _json(h, 409, {"error": "session not live"})
            # The daemon serves per-project editor files under /editor/.
            return _proxy_daemon_read(h, "/editor/" + m.group(1),
                                      urllib.parse.urlparse(h.path).query, proj)
        # ── Collaboration API (overlay) ──────────────────────────────────
        if not s.active:
            return _json(h, 409, {"error": "session not live"})
        if sub == "/live/api/meta":
            return _json(h, 200, {
                "label": rec.get("label") or "", "prototype": rec.get("prototype") or "",
                "emailGate": bool(rec.get("emailGate")),
                "entry": f"p/source/{rec.get('prototype')}/index.html",
                "repoConnected": bool((rec.get("repo") or {}).get("remote")),
                "githubConfigured": _git.oauth_configured(),
            })
        if sub == "/live/api/workflow":
            root = _proot(rec)
            if root is None:
                return _json(h, 500, {"error": "project unavailable"})
            try:
                wf = _READ_WORKFLOW(root)
            except Exception as e:
                return _json(h, 500, {"error": f"workflow unavailable: {e}"})
            return _json(h, 200, wf)
        if sub == "/live/api/roster":
            with s.lock:
                _reap(s)
                return _json(h, 200, {"participants": _roster(s),
                                      "leases": _leases_public(s)})
        if sub == "/live/events":
            return _events_stream(h, s)
        return _json(h, 404, {"error": "not found"})

    def handle_post(self, h, rec, sub):
        share_id = rec.get("id")
        s = _session(share_id, rec.get("project") or "")
        if not s.active:
            return _json(h, 409, {"error": "session not live"})
        try:
            body = _read_json(h)
        except ValueError as e:
            return _json(h, 400, {"error": str(e)})
        token = h.headers.get("X-Live-Token") or body.get("token") or ""
        try:
            if sub == "/live/api/join":
                out = join(rec, body.get("name"), body.get("email"), body.get("github"),
                           client_id=body.get("clientId"))
                return _json(h, 200, out)
            if sub == "/live/api/presence":
                presence(s, token, body.get("cursor"), body.get("selection"))
                return _json(h, 200, {"ok": True})
            if sub == "/live/api/lease/acquire":
                return _json(h, 200, lease_acquire(s, token, body.get("target")))
            if sub == "/live/api/lease/release":
                return _json(h, 200, lease_release(s, token, body.get("target")))
            if sub == "/live/api/lease/heartbeat":
                return _json(h, 200, lease_heartbeat(s, token, body.get("targets")))
            if sub == "/live/api/op":
                return _json(h, 200, apply_op(s, token, body.get("op")))
            if sub == "/live/api/run":
                return _json(h, 200, trigger_run(s, token, body.get("nodeId")))
            if sub == "/live/api/github/device/start":
                return _json(h, 200, github_device_start(s, token))
            if sub == "/live/api/github/device/poll":
                return _json(h, 200, github_device_poll(s, token))
            if sub == "/live/api/github/fork":
                return _json(h, 200, github_fork(s, rec, token))
            if sub == "/live/api/github/pr":
                return _json(h, 200, github_pr(s, rec, token, body))
            if sub == "/live/api/leave":
                guest_id, _p = _auth(s, token)
                kick(share_id, guest_id)
                return _json(h, 200, {"ok": True})
        except PermissionError as e:
            return _json(h, 403, {"error": str(e)})
        except ValueError as e:
            return _json(h, 400, {"error": str(e)})
        except Exception as e:
            return _json(h, 500, {"error": f"internal error: {e}"})
        return _json(h, 404, {"error": "not found"})


GATE = _LiveGate()


# ── gate helpers (operate on the shares GateHandler instance `h`) ───────────

def _json(h, code, payload):
    body = json.dumps(payload).encode("utf-8")
    h.send_response(code)
    h.send_header("Content-Type", "application/json; charset=utf-8")
    h.send_header("Content-Length", str(len(body)))
    h.send_header("Cache-Control", "no-store")
    h.end_headers()
    try:
        h.wfile.write(body)
    except Exception:
        pass
    return True


def _read_json(h, max_bytes=128 * 1024):
    try:
        n = int(h.headers.get("Content-Length") or 0)
    except ValueError:
        n = 0
    if n <= 0 or n > max_bytes:
        raise ValueError("body required (and must be under 128KB)")
    raw = h.rfile.read(n)
    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception:
        raise ValueError("invalid JSON body")
    if not isinstance(data, dict):
        raise ValueError("body must be an object")
    return data


def _proot(rec):
    try:
        return _RESOLVE_PROJECT_ROOT(rec.get("project") or "")
    except Exception:
        return None


def _serve_client(h, name):
    import os
    if not NAME_SAFE_FILE.match(name):
        return _json(h, 404, {"error": "not found"})
    path = os.path.join(INSTALL_ROOT, "editor", "live", name)
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError:
        return _json(h, 404, {"error": "not found"})
    ctype = ("text/html; charset=utf-8" if name.endswith(".html")
             else "application/javascript; charset=utf-8" if name.endswith(".js")
             else "text/css; charset=utf-8" if name.endswith(".css")
             else "application/octet-stream")
    h.send_response(200)
    h.send_header("Content-Type", ctype)
    h.send_header("Content-Length", str(len(data)))
    h.send_header("Cache-Control", "no-store")
    h.end_headers()
    try:
        h.wfile.write(data)
    except Exception:
        pass
    return True


def _events_stream(h, s):
    """SSE for one guest. EventSource can't set headers, so the guest token
    arrives as ?lt=<token>. Mirrors serve.py's _workflow_events loop."""
    parsed = urllib.parse.urlparse(h.path)
    qs = urllib.parse.parse_qs(parsed.query)
    token = (qs.get("lt") or [""])[0]
    try:
        guest_id, _p = _auth(s, token)
    except PermissionError as e:
        return _json(h, 403, {"error": str(e)})
    # SSE holds the socket open for the session's life; tell the keep-alive
    # handler to close it when we return rather than re-reading a dead socket
    # (avoids a spurious traceback in the gate console on client disconnect).
    # LONG-POLL (same reason as the workflow stream: Cloudflare quick tunnels
    # buffer a held SSE body until close). Each connection forwards the snapshot
    # + any cursor/lock events for a short window, then CLOSES so the edge
    # flushes the batch; the browser's EventSource reconnects. ~1.2s window =
    # cursors update within ~1.2s over a tunnel (instant on localhost) without a
    # reconnect-per-cursor-move storm.
    import time as _t
    h.close_connection = True
    h.send_response(200)
    h.send_header("Content-Type", "text/event-stream; charset=utf-8")
    h.send_header("Cache-Control", "no-store")
    h.send_header("Connection", "close")
    h.send_header("X-Accel-Buffering", "no")
    h.end_headers()
    def _raw(evt, data):
        try:
            h.wfile.write(("event: %s\ndata: %s\n\n" % (
                evt, json.dumps(data or {}, separators=(",", ":")))).encode("utf-8"))
            return True
        except Exception:
            return False
    waiter = _Waiter()
    with s.lock:
        s.waiters.add(waiter)
        roster = _roster(s)
        leases = _leases_public(s)
    try:
        try: h.wfile.write(b"retry: 250\n\n")  # fast EventSource reconnect between polls
        except Exception: pass
        _raw("live-connected", {"guestId": guest_id})
        _raw("roster", {"participants": roster})
        _raw("lock", {"leases": leases})
        start = _t.monotonic()
        while _t.monotonic() - start < 1.2:
            waiter.wait(timeout=max(0.05, 1.2 - (_t.monotonic() - start)))
            with s.lock:
                p = s.participants.get(guest_id)
                if p is not None:
                    p["lastSeen"] = _now()
                still_in = p is not None and s.active
            if not still_in:
                _raw("session-ended", {})
                break
            for evt_type, evt_data in waiter.drain():
                _raw(evt_type, evt_data)
        try: h.wfile.flush()
        except Exception: pass
    finally:
        with s.lock:
            s.waiters.discard(waiter)
    return True


def _sse_chunk(h, payload):
    """Write `payload` as ONE HTTP chunk (hex-length + CRLF framing) and flush.
    Chunked transfer-encoding is what makes cloudflared (and other proxies)
    stream each SSE event immediately instead of buffering a read-until-close
    body — without this, host→guest mirror + cursors never arrive over a tunnel."""
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    h.wfile.write(f"{len(payload):X}\r\n".encode("ascii") + payload + b"\r\n")
    h.wfile.flush()

def _sse_chunk_end(h):
    try:
        h.wfile.write(b"0\r\n\r\n"); h.wfile.flush()
    except Exception:
        pass

# Cloudflare (and other proxies) buffer a streaming response body until ~2KB has
# accumulated before they start flushing to the client. Without this, the first
# SSE events sit in the proxy's buffer and never arrive over a tunnel. An initial
# padding comment fills that buffer so the stream starts flowing immediately.
_SSE_PADDING = (":" + " " * 2049 + "\n\n")
def _sse_pad(h):
    try:
        _sse_chunk(h, _SSE_PADDING)
    except Exception:
        pass

def _sse_write(h, evt_type, data):
    try:
        payload = json.dumps(data or {}, separators=(",", ":"))
        _sse_chunk(h, f"event: {evt_type}\ndata: {payload}\n\n")
        return True
    except Exception:
        return False

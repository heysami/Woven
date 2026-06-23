"""User Testing mode - record a testee's prototype session (DOM via rrweb,
cursor, voice, gaze), review the integrated recording, and process many
sessions into insight notes.

The second SHARING surface (sibling of shares.py). It deliberately reuses the
same daemon-side shape:

  1. REGISTRY  - usertesting.json at the WORKSPACE root (sibling of shares.json
     and workspace.json). One record per study SESSION:
       { id, project, prototype, label, createdAt, config{…},
         cohorts:[ { id, name, createdAt,
                     participants:[ { id, name, email,
                                      testeeToken, reviewerToken,
                                      status, createdAt, startedAt,
                                      finishedAt, t0 } ] } ] }
     The registry is workspace-level (NOT per-project) for the SAME reason
     shares.json is: the public gate resolves a participant TOKEN without
     knowing which project it belongs to, so a single-file scan
     (resolve_token) has to see every session. Each session carries its own
     `project` + `prototype`, exactly like a share record.

  2. ARTIFACTS - the heavy per-participant recording bytes live PER-PROJECT on
     disk under <project_root>/usertesting/<sessionId>/<participantId>/:
         meta.json        status / device / t0(epoch ms) / durations
         rrweb.jsonl      rrweb events, one JSON per line, append-chunked
         cursor.jsonl     {t,x,y,type}            (t relative to t0, ms)
         gaze.jsonl       {t,x,y,conf}            (t relative to t0, ms)
         audio.webm       MediaRecorder opus, append-chunked
         transcript.json  {segments:[{t0,t1,text}], full, engine}
         answers.json     {answers:[{questionId, value}], rating}
         markers.json     reviewer timing {startAt, endAt, flows:[{id,startAt,endAt}]}
     Mirrors shares.py's per-project comments store; written by the testee
     through the gate AND by the editor/reviewer, all funnelled through the
     functions here under one lock.

  3. GATE      - shares.py's GateHandler grows two new token-scoped route
     families that resolve through resolve_token() here:
         /t/<token>/   testee recorder  (append-recording only)
         /r/<token>/   reviewer replay  (read + markers write only)
     served over the SAME cloudflared tunnel(s) as shares. No new network
     surface; the security boundary is unchanged.

serve.py wiring:
     init(...)   once at boot (injects workspace dir, install root, the
                 project-root resolver, and an optional change callback).

RECORDING FORMAT CONTRACT (pinned here so the testee producer and the reviewer
consumer agree): every per-stream timestamp `t` is MILLISECONDS relative to
meta.t0 (the epoch-ms instant recording started). rrweb events keep their own
native `timestamp` (epoch ms) and are NOT rebased - the reviewer aligns them by
subtracting t0. Audio is one continuous webm; its play head maps to t0+offset.
"""
from __future__ import annotations  # keep annotations 3.9-safe (daemon runs system py)

import json
import os
import re
import secrets
import threading
import time

# ── Module config (set once by init()) ──────────────────────────────────────

WORKSPACE_DIR = None          # where usertesting.json lives
INSTALL_ROOT  = None          # where editor/usertesting/* live
_RESOLVE_PROJECT_ROOT = None  # fn(project_id:str) -> abs path (raises ValueError)
_ON_CHANGED = None            # fn(project_id:str, session_id:str) | None

_REGISTRY_LOCK = threading.Lock()
_ARTIFACT_LOCK = threading.Lock()

TOKEN_OK       = re.compile(r"^[a-f0-9]{32}$")
SESSION_ID_OK  = re.compile(r"^uts-[a-f0-9]{8,16}$")
COHORT_ID_OK   = re.compile(r"^coh-[a-f0-9]{8,16}$")
PARTICIPANT_ID_OK = re.compile(r"^p-[a-f0-9]{8,16}$")
EMAIL_OK       = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_SAFE_SEG      = re.compile(r"^[A-Za-z0-9._-]+$")

# Participant lifecycle. invited -> recording (testee opened + started) ->
# complete (finalize posted) -> processed (rolled into an insights table).
PARTICIPANT_STATUSES = ("invited", "recording", "complete", "processed")

# Recording streams the gate accepts on /t/<token>/api/chunk?stream=…
STREAM_RRWEB  = "rrweb"
STREAM_CURSOR = "cursor"
STREAM_GAZE   = "gaze"
STREAM_AUDIO  = "audio"
TEXT_STREAMS   = (STREAM_RRWEB, STREAM_CURSOR, STREAM_GAZE)  # jsonl, appended as text
BINARY_STREAMS = (STREAM_AUDIO,)                             # webm, appended as bytes
_STREAM_FILE = {
    STREAM_RRWEB:  "rrweb.jsonl",
    STREAM_CURSOR: "cursor.jsonl",
    STREAM_GAZE:   "gaze.jsonl",
    STREAM_AUDIO:  "audio.webm",
}

# Question placement vocabulary. "start"/"end"/"general" or "flow:<flowId>".
_QUESTION_KINDS = ("text", "choice", "rating", "boolean")


def init(workspace_dir, install_root, resolve_project_root, on_changed=None):
    """Called once from serve.py before any other function here."""
    global WORKSPACE_DIR, INSTALL_ROOT, _RESOLVE_PROJECT_ROOT, _ON_CHANGED
    WORKSPACE_DIR = workspace_dir
    INSTALL_ROOT  = install_root
    _RESOLVE_PROJECT_ROOT = resolve_project_root
    _ON_CHANGED = on_changed


def _now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())


def _notify(project_id, session_id):
    if _ON_CHANGED is not None:
        try:
            _ON_CHANGED(project_id, session_id)
        except Exception:
            pass


# ═════════════════════════════════════════════════════════════════════════
# 1. Registry - usertesting.json (workspace level)
# ═════════════════════════════════════════════════════════════════════════

def _registry_path():
    root = WORKSPACE_DIR or INSTALL_ROOT or "."
    return os.path.join(root, "usertesting.json")


def registry_load():
    p = _registry_path()
    if not os.path.isfile(p):
        return {"sessions": []}
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f) or {}
    except Exception:
        return {"sessions": []}
    if not isinstance(data, dict):
        return {"sessions": []}
    data.setdefault("sessions", [])
    if not isinstance(data["sessions"], list):
        data["sessions"] = []
    return data


def _registry_save(data):
    p = _registry_path()
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, p)


def sessions_list(project=None):
    """All session records, optionally filtered to one project."""
    out = []
    for s in registry_load().get("sessions", []):
        if not isinstance(s, dict):
            continue
        if project is not None and s.get("project") != project:
            continue
        out.append(s)
    return out


def session_get(session_id):
    for s in registry_load().get("sessions", []):
        if isinstance(s, dict) and s.get("id") == session_id:
            return s
    return None


def _default_config():
    return {
        "flows":   [],   # [{id, name, tasks:[str]}]
        "questions": [], # [{id, at, kind, prompt, choices?, min?, max?}]
        "rating":  {"enabled": True, "min": 1, "max": 5, "label": "Overall experience"},
        "recording": {"rrweb": True, "cursor": True, "audio": True, "gaze": True},
    }


def session_create(project, prototype, label=None, config=None):
    """Create a study session for (project, prototype). Unlike shares this is
    NOT idempotent per prototype - a team can run several distinct studies on
    the same prototype, so each create mints a new session."""
    with _REGISTRY_LOCK:
        data = registry_load()
        cfg = _default_config()
        if isinstance(config, dict):
            cfg.update({k: v for k, v in config.items() if k in cfg})
        rec = {
            "id":        "uts-" + secrets.token_hex(6),
            "project":   project,
            "prototype": prototype,
            "label":     (label or "").strip() or f"{prototype} study",
            "createdAt": _now_iso(),
            "config":    cfg,
            "cohorts":   [],
        }
        data["sessions"].append(rec)
        _registry_save(data)
    _notify(project, rec["id"])
    return rec


def session_update(session_id, patch):
    """Shallow-merge top-level fields (label, config) onto a session."""
    allowed = ("label", "config", "prototype")
    with _REGISTRY_LOCK:
        data = registry_load()
        for s in data["sessions"]:
            if s.get("id") == session_id:
                for k, v in patch.items():
                    if k in allowed:
                        s[k] = v
                _registry_save(data)
                _notify(s.get("project"), session_id)
                return s
    return None


def session_delete(session_id):
    """Remove a session from the registry. Leaves on-disk artifacts in place
    (the caller may purge <project>/usertesting/<sessionId>/ separately)."""
    with _REGISTRY_LOCK:
        data = registry_load()
        rec = next((s for s in data["sessions"] if s.get("id") == session_id), None)
        before = len(data["sessions"])
        data["sessions"] = [s for s in data["sessions"] if s.get("id") != session_id]
        if len(data["sessions"]) != before:
            _registry_save(data)
            if rec is not None:
                _notify(rec.get("project"), session_id)
            return True
    return False


# ── Cohorts ──────────────────────────────────────────────────────────────

def cohort_add(session_id, name=None):
    with _REGISTRY_LOCK:
        data = registry_load()
        for s in data["sessions"]:
            if s.get("id") == session_id:
                coh = {
                    "id":        "coh-" + secrets.token_hex(5),
                    "name":      (name or "").strip() or "Cohort",
                    "createdAt": _now_iso(),
                    "participants": [],
                }
                s.setdefault("cohorts", []).append(coh)
                _registry_save(data)
                _notify(s.get("project"), session_id)
                return coh
    return None


def cohort_update(session_id, cohort_id, patch):
    with _REGISTRY_LOCK:
        data = registry_load()
        for s in data["sessions"]:
            if s.get("id") != session_id:
                continue
            for coh in s.get("cohorts", []):
                if coh.get("id") == cohort_id:
                    if "name" in patch:
                        coh["name"] = (patch["name"] or "").strip() or coh["name"]
                    _registry_save(data)
                    _notify(s.get("project"), session_id)
                    return coh
    return None


def cohort_delete(session_id, cohort_id):
    with _REGISTRY_LOCK:
        data = registry_load()
        for s in data["sessions"]:
            if s.get("id") != session_id:
                continue
            before = len(s.get("cohorts", []))
            s["cohorts"] = [c for c in s.get("cohorts", []) if c.get("id") != cohort_id]
            if len(s["cohorts"]) != before:
                _registry_save(data)
                _notify(s.get("project"), session_id)
                return True
    return False


# ── Participants ───────────────────────────────────────────────────────────

def participant_add(session_id, cohort_id, name=None, email=None):
    """Add a participant to a cohort and mint their two access tokens."""
    with _REGISTRY_LOCK:
        data = registry_load()
        for s in data["sessions"]:
            if s.get("id") != session_id:
                continue
            for coh in s.get("cohorts", []):
                if coh.get("id") != cohort_id:
                    continue
                p = {
                    "id":            "p-" + secrets.token_hex(5),
                    "name":          (name or "").strip() or "Participant",
                    "email":         (email or "").strip(),
                    "testeeToken":   secrets.token_hex(16),
                    "reviewerToken": secrets.token_hex(16),
                    "status":        "invited",
                    "createdAt":     _now_iso(),
                    "startedAt":     "",
                    "finishedAt":    "",
                    "t0":            0,
                }
                coh.setdefault("participants", []).append(p)
                _registry_save(data)
                _notify(s.get("project"), session_id)
                return p
    return None


def participant_update(session_id, participant_id, patch):
    """Shallow-merge selected participant fields. Token fields are immutable."""
    allowed = ("name", "email", "status", "startedAt", "finishedAt", "t0")
    with _REGISTRY_LOCK:
        data = registry_load()
        for s in data["sessions"]:
            if s.get("id") != session_id:
                continue
            for coh in s.get("cohorts", []):
                for p in coh.get("participants", []):
                    if p.get("id") == participant_id:
                        for k, v in patch.items():
                            if k in allowed:
                                p[k] = v
                        _registry_save(data)
                        _notify(s.get("project"), session_id)
                        return p
    return None


def participant_delete(session_id, participant_id):
    with _REGISTRY_LOCK:
        data = registry_load()
        for s in data["sessions"]:
            if s.get("id") != session_id:
                continue
            for coh in s.get("cohorts", []):
                before = len(coh.get("participants", []))
                coh["participants"] = [p for p in coh.get("participants", [])
                                       if p.get("id") != participant_id]
                if len(coh.get("participants", [])) != before:
                    _registry_save(data)
                    _notify(s.get("project"), session_id)
                    return True
    return False


def participant_find(session_id, participant_id):
    """Return (session, cohort, participant) or (None, None, None)."""
    s = session_get(session_id)
    if s is None:
        return None, None, None
    for coh in s.get("cohorts", []):
        for p in coh.get("participants", []):
            if p.get("id") == participant_id:
                return s, coh, p
    return s, None, None


# ── Token resolution (the gate's entry point) ──────────────────────────────

def resolve_token(token):
    """Map a participant access token to its context. Returns a dict
        { session, cohort, participant, role }
    where role is "testee" or "reviewer", or None if the token is unknown.
    O(participants) single-file scan, exactly like share_get_by_token."""
    if not token or not TOKEN_OK.match(token):
        return None
    for s in registry_load().get("sessions", []):
        if not isinstance(s, dict):
            continue
        for coh in s.get("cohorts", []):
            for p in coh.get("participants", []):
                if p.get("testeeToken") == token:
                    return {"session": s, "cohort": coh, "participant": p, "role": "testee"}
                if p.get("reviewerToken") == token:
                    return {"session": s, "cohort": coh, "participant": p, "role": "reviewer"}
    return None


# ═════════════════════════════════════════════════════════════════════════
# 2. Per-project artifacts on disk
# ═════════════════════════════════════════════════════════════════════════

def project_root_for(session):
    """Resolve the session's project to an absolute root, or None."""
    if _RESOLVE_PROJECT_ROOT is None:
        return None
    try:
        return _RESOLVE_PROJECT_ROOT(session.get("project") or "")
    except Exception:
        return None


def participant_dir(session, participant_id, *, create=False):
    """<project_root>/usertesting/<sessionId>/<participantId>/ . Returns the
    absolute path, or None if the project can't be resolved or the ids look
    unsafe."""
    sid = session.get("id") or ""
    if not (SESSION_ID_OK.match(sid) and PARTICIPANT_ID_OK.match(participant_id or "")):
        return None
    root = project_root_for(session)
    if root is None:
        return None
    d = os.path.join(root, "usertesting", sid, participant_id)
    if create:
        try:
            os.makedirs(d, exist_ok=True)
        except OSError:
            return None
    return d


def stream_path(session, participant_id, stream, *, create=False):
    fname = _STREAM_FILE.get(stream)
    if not fname:
        return None
    d = participant_dir(session, participant_id, create=create)
    if d is None:
        return None
    return os.path.join(d, fname)


def append_stream(session, participant_id, stream, payload):
    """Append a recording chunk. Text streams (rrweb/cursor/gaze) take a str
    (already newline-delimited JSON) or bytes; the audio stream takes raw
    bytes. Append-only so a session uploads incrementally and survives a
    dropped connection mid-test. Returns the new file size, or None on error."""
    path = stream_path(session, participant_id, stream, create=True)
    if path is None:
        return None
    if stream in TEXT_STREAMS:
        if isinstance(payload, str):
            data = payload.encode("utf-8")
        elif isinstance(payload, (bytes, bytearray)):
            data = bytes(payload)
        else:
            return None
        # Guarantee a trailing newline so concatenated chunks stay line-valid.
        if data and not data.endswith(b"\n"):
            data += b"\n"
    else:
        if not isinstance(payload, (bytes, bytearray)):
            return None
        data = bytes(payload)
    with _ARTIFACT_LOCK:
        try:
            with open(path, "ab") as f:
                f.write(data)
            return os.path.getsize(path)
        except OSError:
            return None


def read_jsonl(session, participant_id, stream, *, limit=None):
    """Parse a jsonl stream into a list of objects. Skips malformed lines.
    `limit` caps the count (most-recent-N is the caller's job)."""
    path = stream_path(session, participant_id, stream)
    if path is None or not os.path.isfile(path):
        return []
    out = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except Exception:
                    continue
                if limit is not None and len(out) >= limit:
                    break
    except OSError:
        return out
    return out


# ── Sidecar JSON docs (meta / answers / markers / transcript) ──────────────

_SIDECARS = ("meta", "answers", "markers", "transcript")


def _sidecar_path(session, participant_id, name, *, create=False):
    if name not in _SIDECARS:
        return None
    d = participant_dir(session, participant_id, create=create)
    if d is None:
        return None
    return os.path.join(d, name + ".json")


def sidecar_read(session, participant_id, name, default=None):
    path = _sidecar_path(session, participant_id, name)
    if path is None or not os.path.isfile(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def sidecar_write(session, participant_id, name, obj):
    """Atomically write a sidecar JSON doc. Returns True on success."""
    path = _sidecar_path(session, participant_id, name, create=True)
    if path is None:
        return False
    with _ARTIFACT_LOCK:
        try:
            tmp = path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(obj, f, indent=2)
            os.replace(tmp, path)
            return True
        except OSError:
            return False


# ═════════════════════════════════════════════════════════════════════════
# 3. Lifecycle helpers used by the gate + editor
# ═════════════════════════════════════════════════════════════════════════

def begin_recording(session_id, participant_id, t0_ms, device=None):
    """Testee pressed Start: stamp t0, flip status to recording, seed meta."""
    s, _coh, p = participant_find(session_id, participant_id)
    if p is None:
        return None
    participant_update(session_id, participant_id, {
        "status": "recording", "startedAt": _now_iso(), "t0": int(t0_ms or 0),
    })
    meta = {
        "sessionId": session_id, "participantId": participant_id,
        "t0": int(t0_ms or 0), "startedAt": _now_iso(),
        "device": device or {}, "status": "recording",
        "finishedAt": "", "durationMs": 0,
    }
    sidecar_write(s, participant_id, "meta", meta)
    return meta


def finalize_recording(session_id, participant_id, duration_ms=None):
    """Testee finished: flip status to complete, stamp meta. Transcription is
    kicked separately by the daemon (it owns whisper/cloud)."""
    s, _coh, p = participant_find(session_id, participant_id)
    if p is None:
        return None
    participant_update(session_id, participant_id, {
        "status": "complete", "finishedAt": _now_iso(),
    })
    meta = sidecar_read(s, participant_id, "meta", {}) or {}
    meta["status"] = "complete"
    meta["finishedAt"] = _now_iso()
    if duration_ms is not None:
        try:
            meta["durationMs"] = int(duration_ms)
        except (TypeError, ValueError):
            pass
    sidecar_write(s, participant_id, "meta", meta)
    return meta


def participant_summary(session, cohort, p):
    """Compact participant view for the editor panel (no tokens leaked except
    as link-builder inputs the caller decides to expose)."""
    return {
        "id":         p.get("id"),
        "name":       p.get("name"),
        "email":      p.get("email"),
        "status":     p.get("status"),
        "createdAt":  p.get("createdAt"),
        "startedAt":  p.get("startedAt"),
        "finishedAt": p.get("finishedAt"),
        "t0":         p.get("t0"),
        "cohortId":   cohort.get("id") if cohort else None,
        # tokens are needed by the editor to build the two links - this is the
        # owner's own editor surface (main daemon, not the public gate), so it
        # is the one place tokens are handed out.
        "testeeToken":   p.get("testeeToken"),
        "reviewerToken": p.get("reviewerToken"),
    }


def session_summary(session):
    """Session + cohort/participant rollup for the editor."""
    cohorts = []
    counts = {"invited": 0, "recording": 0, "complete": 0, "processed": 0}
    for coh in session.get("cohorts", []):
        parts = []
        for p in coh.get("participants", []):
            parts.append(participant_summary(session, coh, p))
            st = p.get("status")
            if st in counts:
                counts[st] += 1
        cohorts.append({
            "id": coh.get("id"), "name": coh.get("name"),
            "createdAt": coh.get("createdAt"), "participants": parts,
        })
    return {
        "id":        session.get("id"),
        "project":   session.get("project"),
        "prototype": session.get("prototype"),
        "label":     session.get("label"),
        "createdAt": session.get("createdAt"),
        "config":    session.get("config") or _default_config(),
        "cohorts":   cohorts,
        "counts":    counts,
    }

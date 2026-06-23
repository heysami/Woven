"""User Testing gate delegate - the public, token-scoped HTTP surface for the
testee recorder (/t/<token>/) and the reviewer replay (/r/<token>/).

Mirrors live.py: a self-contained GATE object that shares.py's GateHandler
delegates to (register_usertesting(GATE) at boot). It imports `shares` for the
shared prototype-file serving helper without a cycle (shares never imports this
module - it only holds the late-bound _UT reference). All storage goes through
`usertesting` (the pure registry/artifact module).

Security: exactly two route families, each scoped to one participant token.
  /t/<token>/   role must be "testee"   - append-recording + answers/finalize
  /r/<token>/   role must be "reviewer" - read streams + write markers
Anything else 404s. No path here can reach the main daemon.
"""
from __future__ import annotations

import json
import os
import re
import threading
import urllib.parse

import shares as _shares
import usertesting as _ut

_NAME_SAFE = re.compile(r"^[A-Za-z0-9._-]+$")

# Upload caps. Each chunk POST stays well under the gate's comfort zone; the
# testee slices long streams into many of these.
_CHUNK_MAX   = 16 * 1024 * 1024
_JSON_MAX    = 1 * 1024 * 1024

# Hook the daemon wires (WS6) so finalize can kick a background transcription.
# fn(session_dict, participant_id) -> None. Unset -> finalize still succeeds.
_ON_FINALIZE = None


def register_on_finalize(fn):
    global _ON_FINALIZE
    _ON_FINALIZE = fn


def _assets_dir():
    # editor/usertesting/ alongside editor/share/ (served by the gate).
    return os.path.join(_ut.INSTALL_ROOT or ".", "editor", "usertesting")


def _send_local(handler, *relparts):
    base = os.path.realpath(_assets_dir())
    abs_path = os.path.realpath(os.path.join(base, *relparts))
    if abs_path != base and not abs_path.startswith(base + os.sep):
        return handler._send_json(404, {"error": "not found"})
    if not os.path.isfile(abs_path):
        return handler._send_json(404, {"error": "not found"})
    return handler._send_file(abs_path, cache=False)


def _send_vendor(handler, sub_after_vendor):
    name = os.path.basename(sub_after_vendor)
    if not name or not _NAME_SAFE.match(name):
        return handler._send_json(404, {"error": "not found"})
    return _send_local(handler, "vendor", name)


def _read_raw_body(handler, cap):
    try:
        n = int(handler.headers.get("Content-Length") or 0)
    except ValueError:
        n = 0
    if n <= 0 or n > cap:
        return None
    return handler.rfile.read(n)


def _query(handler):
    return urllib.parse.parse_qs(urllib.parse.urlparse(handler.path).query)


def _send_audio(handler, path):
    """Serve audio.webm with single-range support so the reviewer can SEEK
    (Chrome requires 206/Range for media currentTime jumps). Reads only the
    requested slice; audio is small enough to hold in memory."""
    try:
        size = os.path.getsize(path)
    except OSError:
        return handler._send_json(404, {"error": "no audio"})
    start, end, is_range = 0, size - 1, False
    rng = handler.headers.get("Range")
    if rng:
        m = re.match(r"bytes=(\d*)-(\d*)\s*$", rng.strip())
        if m:
            g1, g2 = m.group(1), m.group(2)
            if g1 == "" and g2 != "":
                start = max(0, size - int(g2)); end = size - 1
            else:
                start = int(g1) if g1 else 0
                end = int(g2) if g2 else size - 1
            end = min(end, size - 1)
            if start > end or start >= size:
                handler.send_response(416)
                handler.send_header("Content-Range", "bytes */%d" % size)
                handler.send_header("Content-Length", "0")
                handler.end_headers()
                return
            is_range = True
    length = end - start + 1
    try:
        with open(path, "rb") as f:
            f.seek(start)
            data = f.read(length)
    except OSError:
        return handler._send_json(500, {"error": "read failed"})
    handler.send_response(206 if is_range else 200)
    handler.send_header("Content-Type", "audio/webm")
    handler.send_header("Accept-Ranges", "bytes")
    handler.send_header("Content-Length", str(len(data)))
    if is_range:
        handler.send_header("Content-Range", "bytes %d-%d/%d" % (start, end, size))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    try:
        handler.wfile.write(data)
    except Exception:
        pass


def _redirect_slash(handler):
    handler.send_response(301)
    handler.send_header("Location", handler.path + "/")
    handler.send_header("Content-Length", "0")
    handler.end_headers()


class _UTGate:
    # ── GET ────────────────────────────────────────────────────────────
    def handle_get(self, handler, role, token, sub):
        ctx = self._resolve(handler, role, token)
        if ctx is None:
            return True  # already replied (404)
        session, participant = ctx["session"], ctx["participant"]
        pid = participant.get("id")
        if sub == "":
            _redirect_slash(handler); return True
        if role == "t":
            return self._testee_get(handler, session, participant, pid, sub)
        return self._reviewer_get(handler, session, participant, pid, sub)

    def _testee_get(self, handler, session, participant, pid, sub):
        if sub == "/":
            _send_local(handler, "testee.html"); return True
        if sub in ("/testee.js", "/testee.css"):
            _send_local(handler, sub.lstrip("/")); return True
        if sub.startswith("/vendor/"):
            _send_vendor(handler, sub); return True
        if sub == "/api/meta":
            cfg = session.get("config") or {}
            slug = session.get("prototype") or ""
            handler._send_json(200, {
                "sessionLabel": session.get("label") or "",
                "prototype":    slug,
                "entry":        "p/source/%s/index.html" % slug,
                "config":       cfg,
                "participant":  {"id": pid, "name": participant.get("name")},
                "status":       participant.get("status"),
            })
            return True
        # Prototype + design-system files for the iframe.
        root = _ut.project_root_for(session)
        if root is None:
            handler._send_json(500, {"error": "project unavailable"}); return True
        if _shares.gate_serve_project_file(handler, root, session.get("prototype"), sub):
            return True
        handler._send_json(404, {"error": "not found"}); return True

    def _reviewer_get(self, handler, session, participant, pid, sub):
        if sub == "/":
            _send_local(handler, "reviewer.html"); return True
        if sub in ("/reviewer.js", "/reviewer.css"):
            _send_local(handler, sub.lstrip("/")); return True
        if sub.startswith("/vendor/"):
            _send_vendor(handler, sub); return True
        if sub == "/api/meta":
            cfg = session.get("config") or {}
            handler._send_json(200, {
                "sessionLabel": session.get("label") or "",
                "prototype":    session.get("prototype") or "",
                "config":       cfg,
                "participant":  {"id": pid, "name": participant.get("name")},
                "meta":         _ut.sidecar_read(session, pid, "meta", {}) or {},
                "answers":      _ut.sidecar_read(session, pid, "answers", None),
                "markers":      _ut.sidecar_read(session, pid, "markers", None),
                "transcript":   _ut.sidecar_read(session, pid, "transcript", None),
            })
            return True
        if sub == "/api/stream":
            name = (_query(handler).get("name") or [""])[0]
            if name in (_ut.STREAM_RRWEB, _ut.STREAM_CURSOR, _ut.STREAM_GAZE):
                handler._send_json(200, _ut.read_jsonl(session, pid, name))
                return True
            if name == _ut.STREAM_AUDIO:
                path = _ut.stream_path(session, pid, _ut.STREAM_AUDIO)
                if not path or not os.path.isfile(path):
                    handler._send_json(404, {"error": "no audio"}); return True
                _send_audio(handler, path); return True
            handler._send_json(400, {"error": "unknown stream"}); return True
        handler._send_json(404, {"error": "not found"}); return True

    # ── POST ───────────────────────────────────────────────────────────
    def handle_post(self, handler, role, token, sub):
        ctx = self._resolve(handler, role, token)
        if ctx is None:
            return True
        session, participant = ctx["session"], ctx["participant"]
        pid = participant.get("id")
        sid = session.get("id")
        if role == "t":
            return self._testee_post(handler, session, sid, pid, sub)
        return self._reviewer_post(handler, session, sid, pid, sub)

    def _testee_post(self, handler, session, sid, pid, sub):
        if sub == "/api/begin":
            body = self._json(handler, _JSON_MAX)
            if body is None:
                return True
            meta = _ut.begin_recording(sid, pid, body.get("t0"), body.get("device"))
            handler._send_json(200, {"ok": True, "meta": meta}); return True
        if sub == "/api/chunk":
            params = _query(handler)
            stream = (params.get("stream") or [""])[0]
            if stream not in _ut.TEXT_STREAMS and stream not in _ut.BINARY_STREAMS:
                handler._send_json(400, {"error": "unknown stream"}); return True
            raw = _read_raw_body(handler, _CHUNK_MAX)
            if raw is None:
                handler._send_json(400, {"error": "empty or oversized chunk (max 16MB)"}); return True
            size = _ut.append_stream(session, pid, stream, raw)
            if size is None:
                handler._send_json(500, {"error": "append failed"}); return True
            handler._send_json(200, {"ok": True, "size": size}); return True
        if sub == "/api/answers":
            body = self._json(handler, _JSON_MAX)
            if body is None:
                return True
            _ut.sidecar_write(session, pid, "answers", {
                "answers": body.get("answers") or [],
                "rating":  body.get("rating"),
            })
            handler._send_json(200, {"ok": True}); return True
        if sub == "/api/finalize":
            body = self._json(handler, _JSON_MAX) or {}
            _ut.finalize_recording(sid, pid, body.get("durationMs"))
            if _ON_FINALIZE is not None:
                threading.Thread(
                    target=_ON_FINALIZE, args=(session, pid), daemon=True,
                    name="ut-transcribe-%s" % pid).start()
            handler._send_json(200, {"ok": True}); return True
        handler._send_json(404, {"error": "not found"}); return True

    def _reviewer_post(self, handler, session, sid, pid, sub):
        if sub == "/api/markers":
            body = self._json(handler, _JSON_MAX)
            if body is None:
                return True
            _ut.sidecar_write(session, pid, "markers", {
                "startAt": body.get("startAt"),
                "endAt":   body.get("endAt"),
                "flows":   body.get("flows") or [],
            })
            handler._send_json(200, {"ok": True}); return True
        handler._send_json(404, {"error": "not found"}); return True

    # ── helpers ─────────────────────────────────────────────────────────
    def _resolve(self, handler, role, token):
        ctx = _ut.resolve_token(token)
        if ctx is None:
            handler._send_json(404, {"error": "unknown or revoked link"})
            return None
        want = "testee" if role == "t" else "reviewer"
        if ctx.get("role") != want:
            handler._send_json(404, {"error": "wrong link for this action"})
            return None
        return ctx

    def _json(self, handler, cap):
        try:
            return handler._read_json_body(max_bytes=cap)
        except ValueError as e:
            handler._send_json(400, {"error": str(e)})
            return None


GATE = _UTGate()

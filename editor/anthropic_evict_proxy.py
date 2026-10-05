#!/usr/bin/env python3
"""Transparent Anthropic API proxy that evicts stale screenshots from history.

WHY
---
Browser-MCP screenshots are returned as `image` blocks inside `tool_result`s.
The Claude Code CLI keeps the FULL conversation locally and re-sends every
turn, so a screenshot taken at turn 50 is re-read on every later turn. In one
demo-inhouse thread that was 154M cache-read tokens (~$77); the worst was
646M (~$411), 91% of it images. The agent only ever needs the LATEST shot.

WHAT
----
Sit between the CLI and api.anthropic.com (the CLI is pointed here via
ANTHROPIC_BASE_URL). On every /v1/messages request we keep the last
EVICT_KEEP_IMAGES TOOL-RESULT image blocks (browser screenshots / tool outputs)
and replace older ones with a tiny text stub. USER-UPLOADED images (top-level
image blocks in a message) are NEVER touched, however many the user sends.
Responses (including SSE streams) pass through untouched.

TWO TRAPS THIS HANDLES
----------------------
1. FAIL-OPEN. Any error in rewriting forwards the ORIGINAL body unchanged. A
   bug here must never break an agent spawn.
2. CACHE-STABLE. Prompt caching is a prefix match, so a per-turn mutation in
   the middle of history would convert cheap cache_reads (0.1x) into expensive
   cache_creation (1.25-2x). The stub is a BYTE-CONSTANT string and eviction is
   deterministic, so the CLI's (always-identical) full history rewrites to the
   same evicted prefix every turn. An image only changes bytes ONCE, the turn
   it ages out of the keep-window — bounded, near-the-end churn, never per-turn.

WIRE-IN
-------
  1. Launch:  python3 editor/anthropic_evict_proxy.py        (PORT via env)
  2. In the spawned CLI's env (serve.py `_guest_cli_env`):
        env["ANTHROPIC_BASE_URL"] = "http://127.0.0.1:%d" % EVICT_PROXY_PORT
  Test on ONE manual spawn before wiring it for all spawns.

CONFIG (env)
------------
  EVICT_PROXY_PORT    listen port (default 8787)
  EVICT_KEEP_IMAGES   how many most-recent images to keep (default 10)
  EVICT_UPSTREAM_HOST upstream host (default api.anthropic.com)

CACHE KEEP-ALIVE
----------------
The prompt cache lives upstream and expires an hour after its last read,
whether or not the CLI process is still alive. serve.py gives each spawn its
own base URL, `<proxy>/r/<runId>`, so the proxy knows which run a request
belongs to and remembers that run's latest main-thread request. keepalive()
re-sends it with `max_tokens: 0`: billed as a cache read, it restarts the
hour without generating anything. serve.py decides WHEN (idle chat threads,
for a few hours after their last real request); this file only knows HOW.
"""
from __future__ import annotations

import atexit
import gzip
import hashlib
import http.client
import json
import os
import re
import shutil
import sys
import tempfile
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

KEEP_IMAGES = int(os.environ.get("EVICT_KEEP_IMAGES", "10"))
LISTEN_PORT = int(os.environ.get("EVICT_PROXY_PORT", "8787"))
UPSTREAM_TIMEOUT = 600  # long turns stream for minutes; don't kill mid-response


def _parse_upstream(url):
    """Parse a base URL (or bare host) into (scheme, host, port). The proxy
    FORWARDS here - it's whatever ANTHROPIC_BASE_URL pointed at before we
    inserted ourselves (the default API, or a real gateway), so chaining works
    in every case instead of us having to skip when a base URL is already set."""
    if not url:
        url = "https://api.anthropic.com"
    if "://" not in url:
        url = "https://" + url
    u = urllib.parse.urlsplit(url)
    scheme = u.scheme or "https"
    host = u.hostname or "api.anthropic.com"
    port = u.port or (443 if scheme == "https" else 80)
    return (scheme, host, port)


# Upstream the proxy forwards to. Defaults to the real API; start_in_background()
# overrides it with the caller's actual ANTHROPIC_BASE_URL so a gateway chains.
UPSTREAM = _parse_upstream(os.environ.get("EVICT_UPSTREAM"))

# BYTE-CONSTANT — never put a counter/timestamp/id in here or the cache thrashes.
STUB_TEXT = "[screenshot evicted to conserve context; re-capture if needed]"

# Request headers we must NOT forward verbatim (we recompute or drop them).
_DROP_REQ = {
    "host", "content-length", "accept-encoding", "content-encoding",
    "connection", "keep-alive", "proxy-connection", "transfer-encoding",
    "te", "upgrade",
}
# Response headers we strip (we re-frame the body as chunked, identity).
_DROP_RESP = {
    "content-length", "transfer-encoding", "content-encoding", "connection",
    "keep-alive",
}


def _evict_images(payload: dict, keep_last: int) -> int:
    """Evict already-READ images; keep just-arrived and recent ones.

    Same rule for uploads and screenshots - the axis is read-state, not source.
    An image is KEPT if either: (1) it's in the request's LAST message - it just
    arrived and the agent is about to read it for the first time, so a fresh
    batch of N uploads/screenshots survives this turn; or (2) it's among the last
    `keep_last` images overall (a small recency buffer). Every older image -
    upload or tool_result screenshot - has been read in a prior turn and is
    replaced with a text stub.

    Deterministic + order-preserving, so the CLI's repeated full-history sends
    rewrite to a byte-stable prefix and don't thrash the prompt cache. Returns
    count evicted.
    """
    msgs = payload.get("messages")
    if not isinstance(msgs, list) or not msgs:
        return 0
    last = len(msgs) - 1

    images = []        # (container_list, index) in positional order
    protected = set()  # (id(container), index) for images in the LAST message

    def scan(content, is_last):
        if not isinstance(content, list):
            return
        for i, block in enumerate(content):
            if not isinstance(block, dict):
                continue
            t = block.get("type")
            if t == "image":  # user upload or inline image
                images.append((content, i))
                if is_last:
                    protected.add((id(content), i))
            elif t == "tool_result":  # browser screenshot / tool output
                tc = block.get("content")
                if isinstance(tc, list):
                    for j, sub in enumerate(tc):
                        if isinstance(sub, dict) and sub.get("type") == "image":
                            images.append((tc, j))
                            if is_last:
                                protected.add((id(tc), j))

    for mi, msg in enumerate(msgs):
        if isinstance(msg, dict):
            scan(msg.get("content"), mi == last)

    keep = set(protected)  # never evict unread (just-arrived) images
    if keep_last > 0:
        for c, i in images[-keep_last:]:
            keep.add((id(c), i))

    n = 0
    for c, i in images:
        if (id(c), i) in keep:
            continue
        c[i] = {"type": "text", "text": STUB_TEXT}
        n += 1
    return n


def _rewrite_body_ex(raw: bytes, content_encoding: str):
    """Return (new_bytes, evicted_count, sent_json). `sent_json` is the
    uncompressed JSON upstream receives (None when the body is not a Messages
    request) - what a keep-alive must replay. Fail-open: on any trouble return
    raw."""
    try:
        data = gzip.decompress(raw) if content_encoding == "gzip" else raw
        payload = json.loads(data)
        if not isinstance(payload, dict) or "messages" not in payload:
            return raw, 0, None  # not a Messages request — pass through
        n = _evict_images(payload, KEEP_IMAGES)
        if n == 0:
            return raw, 0, data
        # Re-serialize compactly + deterministically (stable bytes => stable cache).
        new = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        return new, n, new
    except Exception:
        return raw, 0, None  # FAIL-OPEN


def _rewrite_body(raw: bytes, content_encoding: str):
    """Return (new_bytes, evicted_count). Fail-open: on any trouble return raw."""
    new, n, _sent = _rewrite_body_ex(raw, content_encoding)
    return new, n


# ── cache keep-alive ─────────────────────────────────────────────────────────
# runId -> {key: entry}. One entry per (model, system prompt), so a run's own
# subagents and side calls don't overwrite its main conversation; keepalive()
# replays the entry with the most messages. Bodies live on disk (a long
# thread's request is megabytes, and the point of all this is less memory);
# only the small header dict stays in memory, so credentials never touch disk.
_RUN_PREFIX_RE = re.compile(r"^/r/([A-Za-z0-9_-]{1,64})(/.*)$")
_KA_LOCK = threading.Lock()
_KA: dict = {}
_KA_DIR = None
_KA_MAX_KEYS = 4
# The keep-alive request must not stream; everything else goes as recorded.
_KA_DROP_HEADERS = {"accept", "content-length"}


def _split_run_path(path: str):
    """'/r/<runId>/v1/messages?x' -> ('<runId>', '/v1/messages?x');
    any other path -> (None, path)."""
    m = _RUN_PREFIX_RE.match(path or "")
    if not m:
        return None, path
    return m.group(1), m.group(2)


def _ka_dir() -> str:
    global _KA_DIR
    if _KA_DIR is None:
        _KA_DIR = tempfile.mkdtemp(prefix="woven-keepalive-")   # 0700
        atexit.register(shutil.rmtree, _KA_DIR, True)
    return _KA_DIR


def _ka_record(run_id: str, path: str, headers: dict, sent_json: bytes) -> None:
    """Remember the request a keep-alive for `run_id` would replay. Best-effort:
    a failure here only means no keep-alive, never a broken request."""
    try:
        if path.split("?", 1)[0] != "/v1/messages":
            return                       # count_tokens, batches: nothing to keep warm
        payload = json.loads(sent_json)
        msgs = payload.get("messages")
        if not isinstance(msgs, list) or not msgs or payload.get("max_tokens") == 0:
            return
        key = hashlib.sha1((str(payload.get("model")) + "\0" +
                            json.dumps(payload.get("system"), sort_keys=True))
                           .encode("utf-8")).hexdigest()[:16]
        file = os.path.join(_ka_dir(), "%s-%s.json" % (run_id, key))
        tmp = file + ".tmp"
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "wb") as f:
            f.write(sent_json)
        os.replace(tmp, file)
        now = time.time()
        keep = {k: v for k, v in headers.items() if k.lower() not in _KA_DROP_HEADERS}
        with _KA_LOCK:
            entries = _KA.setdefault(run_id, {})
            entries[key] = {"file": file, "path": path, "headers": keep,
                            "nmsg": len(msgs), "real_at": now, "touched_at": now,
                            "dead": False}
            while len(entries) > _KA_MAX_KEYS:
                oldest = min(entries, key=lambda k: entries[k]["real_at"])
                gone = entries.pop(oldest)
                if gone["file"] != file:
                    try: os.remove(gone["file"])
                    except OSError: pass
    except Exception:
        pass


def _ka_main(run_id: str):
    """The entry keepalive() would replay for `run_id` (a copy), or None."""
    with _KA_LOCK:
        live = [e for e in (_KA.get(run_id) or {}).values() if not e["dead"]]
        if not live:
            return None
        return dict(max(live, key=lambda e: (e["nmsg"], e["real_at"])))


def keepalive_status(run_id: str):
    """{realAt, touchedAt} for the run's main conversation, or None when
    nothing replayable was recorded. realAt = last request the CLI itself
    sent; touchedAt = last time anything (CLI or keep-alive) read the cache."""
    e = _ka_main(run_id)
    if e is None:
        return None
    return {"realAt": e["real_at"], "touchedAt": e["touched_at"], "messages": e["nmsg"]}


def keepalive(run_id: str, timeout: float = 120.0):
    """Re-send the run's main request with max_tokens 0 so the upstream prompt
    cache counts a read and restarts its TTL. Returns {ok, status, usage} or
    None when there is nothing to replay. A request shape the API rejects
    with max_tokens 0 (or any other 4xx) retires the entry - no retry loop
    against an error."""
    e = _ka_main(run_id)
    if e is None:
        return None

    def _retire():
        with _KA_LOCK:
            for cur in (_KA.get(run_id) or {}).values():
                if cur["file"] == e["file"]:
                    cur["dead"] = True

    try:
        with open(e["file"], "rb") as f:
            payload = json.loads(f.read())
    except Exception:
        _retire()
        return None
    # max_tokens 0 is rejected with these; the CLI's normal adaptive-thinking
    # request has none of them.
    if ((payload.get("thinking") or {}).get("type") == "enabled"
            or (payload.get("output_config") or {}).get("format")
            or (payload.get("tool_choice") or {}).get("type") in ("any", "tool")):
        _retire()
        return {"ok": False, "status": None, "usage": None, "reason": "unsupported"}
    payload["max_tokens"] = 0
    payload.pop("stream", None)
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    headers = dict(e["headers"])
    headers["Accept"] = "application/json"
    headers["Accept-Encoding"] = "identity"
    headers["Content-Length"] = str(len(body))
    started = time.time()
    scheme, uhost, uport = UPSTREAM
    try:
        if scheme == "https":
            conn = http.client.HTTPSConnection(uhost, uport, timeout=timeout)
        else:
            conn = http.client.HTTPConnection(uhost, uport, timeout=timeout)
        conn.request("POST", e["path"], body=body, headers=headers)
        resp = conn.getresponse()
        data = resp.read()
        conn.close()
    except Exception as err:
        return {"ok": False, "status": None, "usage": None, "reason": str(err)[:200]}
    usage = None
    try:
        usage = json.loads(data).get("usage")
    except Exception:
        pass
    if resp.status == 200:
        with _KA_LOCK:
            for cur in (_KA.get(run_id) or {}).values():
                if cur["file"] == e["file"]:
                    cur["touched_at"] = max(cur["touched_at"], started)
    elif 400 <= resp.status < 500 and resp.status not in (408, 409, 429):
        _retire()
    return {"ok": resp.status == 200, "status": resp.status, "usage": usage,
            "reason": None if resp.status == 200 else data[:300].decode("utf-8", "replace")}


def keepalive_runs() -> list:
    """Run ids with something recorded."""
    with _KA_LOCK:
        return list(_KA)


def keepalive_forget(run_id: str) -> None:
    """Drop everything recorded for `run_id` (thread deleted, window over)."""
    with _KA_LOCK:
        entries = _KA.pop(run_id, None) or {}
    for e in entries.values():
        try: os.remove(e["file"])
        except OSError: pass


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):  # quiet; daemon captures its own logs
        pass

    def _proxy(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(length) if length else b""

            # serve.py points each spawn at <proxy>/r/<runId>; upstream never
            # sees that prefix.
            run_id, path = _split_run_path(self.path)

            # Rewrite only Messages POSTs; everything else passes through.
            evicted = 0
            sent_json = None
            if self.command == "POST" and body:
                enc = (self.headers.get("Content-Encoding") or "").lower()
                body, evicted, sent_json = _rewrite_body_ex(body, enc)

            # Build upstream headers: copy, drop hop-by-hop, force identity,
            # recompute length (and clear content-encoding since we decompressed).
            up_headers = {}
            for k in self.headers.keys():
                if k.lower() in _DROP_REQ:
                    continue
                up_headers[k] = self.headers[k]
            up_headers["Content-Length"] = str(len(body))
            up_headers["Accept-Encoding"] = "identity"  # avoid gzip relay complexity
            if run_id and sent_json is not None:
                _ka_record(run_id, path, up_headers, sent_json)

            scheme, uhost, uport = UPSTREAM
            if scheme == "https":
                conn = http.client.HTTPSConnection(uhost, uport, timeout=UPSTREAM_TIMEOUT)
            else:
                conn = http.client.HTTPConnection(uhost, uport, timeout=UPSTREAM_TIMEOUT)
            conn.request(self.command, path, body=body or None, headers=up_headers)
            resp = conn.getresponse()

            # Relay status + headers, then stream the body back as chunked so SSE
            # tokens reach the CLI as they arrive (read1 = data-as-available).
            self.send_response(resp.status)
            for k, v in resp.getheaders():
                if k.lower() in _DROP_RESP:
                    continue
                self.send_header(k, v)
            self.send_header("Transfer-Encoding", "chunked")
            if evicted:
                self.send_header("X-Evicted-Images", str(evicted))
            self.end_headers()

            while True:
                chunk = resp.read1(65536)
                if not chunk:
                    break
                self.wfile.write(b"%X\r\n" % len(chunk) + chunk + b"\r\n")
                self.wfile.flush()
            self.wfile.write(b"0\r\n\r\n")
            self.wfile.flush()
            conn.close()
        except BrokenPipeError:
            pass  # client (CLI) hung up mid-stream
        except Exception as e:
            try:
                self.send_error(502, "evict-proxy upstream error: %s" % e)
            except Exception:
                pass

    do_GET = do_POST = do_PUT = do_DELETE = do_PATCH = _proxy


def start_in_background(upstream=None):
    """Start the proxy on an ephemeral localhost port in a daemon thread.

    Called once from serve.py. `upstream` is the real ANTHROPIC_BASE_URL the CLI
    would otherwise hit (the default API, or a gateway); the proxy forwards
    there, so we can always route through it instead of skipping when a base URL
    is already set. Returns the proxy's base URL to set as the child's
    ANTHROPIC_BASE_URL. The thread is a daemon thread, so it dies with the daemon
    - nothing for the user to launch or supervise. Returns None on failure
    (caller then leaves ANTHROPIC_BASE_URL as-is - fail-open).
    """
    global UPSTREAM
    try:
        if upstream:
            UPSTREAM = _parse_upstream(upstream)
        srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)  # 0 => free port
        port = srv.server_address[1]
        threading.Thread(target=srv.serve_forever, daemon=True,
                         name="anthropic-evict-proxy").start()
        return "http://127.0.0.1:%d" % port
    except Exception:
        return None


def main():
    srv = ThreadingHTTPServer(("127.0.0.1", LISTEN_PORT), Handler)
    sys.stderr.write(
        "anthropic-evict-proxy on http://127.0.0.1:%d -> %s://%s:%d "
        "(keep last %d image%s)\n"
        % (LISTEN_PORT, UPSTREAM[0], UPSTREAM[1], UPSTREAM[2], KEEP_IMAGES,
           "" if KEEP_IMAGES == 1 else "s")
    )
    sys.stderr.flush()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()


if __name__ == "__main__":
    main()

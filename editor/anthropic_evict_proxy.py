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
  EVICT_KEEP_IMAGES   how many most-recent images to keep (default 2)
  EVICT_UPSTREAM_HOST upstream host (default api.anthropic.com)
"""
from __future__ import annotations

import gzip
import http.client
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

KEEP_IMAGES = int(os.environ.get("EVICT_KEEP_IMAGES", "2"))
UPSTREAM_HOST = os.environ.get("EVICT_UPSTREAM_HOST", "api.anthropic.com")
LISTEN_PORT = int(os.environ.get("EVICT_PROXY_PORT", "8787"))
UPSTREAM_TIMEOUT = 600  # long turns stream for minutes; don't kill mid-response

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
    """Replace all but the last `keep_last` TOOL-RESULT image blocks with a stub.

    Only images inside tool_results (screenshots / tool outputs) are eligible;
    user-uploaded image blocks in a message are left alone. Deterministic +
    order-preserving so the rewritten prefix is byte-stable across the CLI's
    repeated full-history sends. Returns count evicted.
    """
    images = []  # list of (container_list, index) in positional order

    def scan(content):
        # ONLY tool_result images (browser screenshots / tool outputs) are
        # evictable. A top-level `image` block in a message is a USER UPLOAD -
        # deliberate input the agent needs - and is NEVER touched, no matter how
        # many the user sends.
        if not isinstance(content, list):
            return
        for block in content:
            if not isinstance(block, dict) or block.get("type") != "tool_result":
                continue
            tc = block.get("content")
            if isinstance(tc, list):
                for j, sub in enumerate(tc):
                    if isinstance(sub, dict) and sub.get("type") == "image":
                        images.append((tc, j))

    msgs = payload.get("messages")
    if not isinstance(msgs, list):
        return 0
    for msg in msgs:
        if isinstance(msg, dict):
            scan(msg.get("content"))

    evict = images if keep_last <= 0 else images[:-keep_last]
    for container, idx in evict:
        container[idx] = {"type": "text", "text": STUB_TEXT}
    return len(evict)


def _rewrite_body(raw: bytes, content_encoding: str):
    """Return (new_bytes, evicted_count). Fail-open: on any trouble return raw."""
    try:
        data = gzip.decompress(raw) if content_encoding == "gzip" else raw
        payload = json.loads(data)
        if not isinstance(payload, dict) or "messages" not in payload:
            return raw, 0  # not a Messages request — pass through
        n = _evict_images(payload, KEEP_IMAGES)
        if n == 0:
            return raw, 0
        # Re-serialize compactly + deterministically (stable bytes => stable cache).
        new = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        return new, n
    except Exception:
        return raw, 0  # FAIL-OPEN


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):  # quiet; daemon captures its own logs
        pass

    def _proxy(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(length) if length else b""

            # Rewrite only Messages POSTs; everything else passes through.
            evicted = 0
            if self.command == "POST" and body:
                enc = (self.headers.get("Content-Encoding") or "").lower()
                body, evicted = _rewrite_body(body, enc)

            # Build upstream headers: copy, drop hop-by-hop, force identity,
            # recompute length (and clear content-encoding since we decompressed).
            up_headers = {}
            for k in self.headers.keys():
                if k.lower() in _DROP_REQ:
                    continue
                up_headers[k] = self.headers[k]
            up_headers["Content-Length"] = str(len(body))
            up_headers["Accept-Encoding"] = "identity"  # avoid gzip relay complexity

            conn = http.client.HTTPSConnection(UPSTREAM_HOST, timeout=UPSTREAM_TIMEOUT)
            conn.request(self.command, self.path, body=body or None, headers=up_headers)
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


def start_in_background():
    """Start the proxy on an ephemeral localhost port in a daemon thread.

    Called once from serve.py at boot. Returns the base URL to put in the
    spawned CLI's env (ANTHROPIC_BASE_URL). The thread is a daemon thread, so
    it dies with the daemon — nothing for the user to launch or supervise.
    Returns None on failure (caller then just doesn't set ANTHROPIC_BASE_URL,
    so spawns fall back to talking to the API directly — fail-open).
    """
    try:
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
        "anthropic-evict-proxy on http://127.0.0.1:%d -> https://%s "
        "(keep last %d image%s)\n"
        % (LISTEN_PORT, UPSTREAM_HOST, KEEP_IMAGES, "" if KEEP_IMAGES == 1 else "s")
    )
    sys.stderr.flush()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()


if __name__ == "__main__":
    main()

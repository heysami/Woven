"""Regression test for the live-mirror SSE long-poll proxy.

Bug: _proxy_daemon_read broke out of the forward loop the instant it saw the
`event: ...changed` LINE — before forwarding the event's `data:` line and the
terminating blank line. A real browser EventSource only fires an event once it
receives the complete frame (ending in a blank line), so the guest never got
`workflow-changed`, never refetched /__workflow, and the canvas never mirrored.
curl showed the `event:` line so the earlier check looked green — this test
asserts the WHOLE frame is forwarded, which is what EventSource actually needs.
"""
import os, sys, io, json, time, threading, http.server, socketserver

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, "editor"))

import live


class _FakeDaemon(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):  # silence
        pass

    def do_GET(self):
        # Emit the EXACT frame format serve.py's /__workflow/events uses:
        #   one hello, a heartbeat-ish pause, then a real change frame.
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(b"event: workflow-events-connected\ndata: {}\n\n")
        self.wfile.flush()
        time.sleep(0.15)
        self.wfile.write(b"event: workflow-changed\ndata: {}\n\n")
        self.wfile.flush()
        # keep the connection open a beat so the proxy decides when to close
        time.sleep(2.0)


class _MockHandler:
    """Minimal stand-in for the BaseHTTPRequestHandler the proxy writes to."""
    def __init__(self):
        self.headers = {}
        self.wfile = io.BytesIO()
        self.close_connection = False
        self._status = None
        self._sent_headers = {}

    # headers.get(...) is what the proxy calls
    class _H(dict):
        def get(self, k, default=None):
            return dict.get(self, k, default)

    def send_response(self, code):
        self._status = code

    def send_header(self, k, v):
        self._sent_headers[k] = v

    def end_headers(self):
        pass


def main():
    # Stand up the fake daemon on an ephemeral port.
    srv = socketserver.TCPServer(("127.0.0.1", 0), _FakeDaemon)
    srv.allow_reuse_address = True
    port = srv.server_address[1]
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    try:
        live.DAEMON_PORT = port
        h = _MockHandler()
        h.headers = _MockHandler._H({"Accept": "text/event-stream"})
        # Drive the proxy against the fake daemon's /__workflow/events.
        ok = live._proxy_daemon_read(h, "/__workflow/events", "", "proj")
        out = h.wfile.getvalue()

        assert ok is True, "proxy did not return True"
        assert b"event: workflow-changed" in out, f"no change event forwarded:\n{out!r}"
        # THE regression assertion: the change event must be COMPLETE — the
        # data line AND the terminating blank line must follow the event line,
        # otherwise EventSource never fires it.
        idx = out.index(b"event: workflow-changed")
        tail = out[idx:]
        assert b"data: {}" in tail, f"data line dropped (incomplete frame):\n{out!r}"
        assert tail.split(b"data: {}", 1)[1].startswith(b"\n\n"), \
            f"terminating blank line dropped — EventSource won't fire:\n{out!r}"
        print("test_live_mirror_sse: ALL PASS  (complete workflow-changed frame forwarded)")
    finally:
        srv.shutdown()
        srv.server_close()


if __name__ == "__main__":
    main()

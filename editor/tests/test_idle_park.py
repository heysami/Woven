"""Idle park + prompt-cache keep-alive. No CLI or model calls: a fake `claude`
speaks stream-json over real pipes, and a fake upstream stands in for the API."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import anthropic_evict_proxy as proxy
import serve


def _idle_run(**over):
    state = SimpleNamespace(
        run_id="r1", agent_id="claude", proc=None, workflow_node_id=None,
        parent_run_id=None, kind="freeform", session_id="sess-1", done=False,
        turn_done=True, stop_reason=None, is_live=True, msg_queue=[],
        _queue_draining=False, _compact_inflight=False, _compact_pending=None,
        updated_at=0.0, started_at=0.0, title="t", lock=threading.Lock(),
        events=[], jobs={}, project_root="/fixture/p")
    for k, v in over.items():
        setattr(state, k, v)
    return state


class ParkRuleTests(unittest.TestCase):
    NOW = 10_000.0

    def parkable(self, **over):
        with patch.object(serve, "_pending_run_jobs", return_value=[]):
            return serve._parkable(_idle_run(**over), self.NOW)

    def test_idle_chat_thread_parks(self):
        self.assertTrue(self.parkable())

    def test_only_resumable_threads_park(self):
        self.assertFalse(self.parkable(agent_id="codex"))
        self.assertFalse(self.parkable(kind="node-agent"))
        self.assertFalse(self.parkable(workflow_node_id="n1"))
        self.assertFalse(self.parkable(kind="planner:visual"))
        self.assertFalse(self.parkable(parent_run_id="p"))
        self.assertFalse(self.parkable(session_id=None))

    def test_nothing_owed_and_really_idle(self):
        self.assertFalse(self.parkable(turn_done=False))
        self.assertFalse(self.parkable(done=True))
        self.assertFalse(self.parkable(stop_reason="user-stop"))
        self.assertFalse(self.parkable(is_live=False))
        self.assertFalse(self.parkable(msg_queue=[{"id": "q"}]))
        self.assertFalse(self.parkable(_queue_draining=True))
        self.assertFalse(self.parkable(_compact_inflight=True))
        self.assertFalse(self.parkable(updated_at=self.NOW - serve.PARK_AFTER_S + 5))
        with patch.object(serve, "_pending_run_jobs", return_value=[{"jobId": "c"}]):
            self.assertFalse(serve._parkable(_idle_run(), self.NOW))

    def test_queue_never_writes_into_a_parking_process(self):
        state = _idle_run(stop_reason="parked", msg_queue=[{"id": "q", "text": "x"}])
        self.assertFalse(serve._queue_deliverable(state, "stdin"))


def _usage_event(h1=0, m5=0, read=0):
    return {"type": "agent", "data": {"type": "usage", "usage": {
        "cache_read_input_tokens": read,
        "cache_creation": {"ephemeral_1h_input_tokens": h1, "ephemeral_5m_input_tokens": m5}}}}


class FakeProxy:
    def __init__(self, status, result=None):
        self.status, self.result = status, result
        self.pings, self.forgot = [], []

    def keepalive_status(self, rid):
        return self.status

    def keepalive(self, rid):
        self.pings.append(rid)
        return self.result

    def keepalive_forget(self, rid):
        self.forgot.append(rid)


class KeepaliveRuleTests(unittest.TestCase):
    NOW = 100_000.0

    def run_rule(self, state, status, result=None):
        fake = FakeProxy(status, result)
        serve._keepalive_maybe(state, self.NOW, fake)
        return fake

    def due(self, **over):
        return {"realAt": self.NOW - 3600, "touchedAt": self.NOW - serve.KEEPALIVE_EVERY_S, **over}

    def ok(self, read, write):
        return {"ok": True, "status": 200,
                "usage": {"cache_read_input_tokens": read, "cache_creation_input_tokens": write}}

    def test_parked_thread_on_1h_cache_gets_pinged(self):
        state = _idle_run(stop_reason="parked", done=True, events=[_usage_event(h1=500)])
        fake = self.run_rule(state, self.due(), self.ok(260_000, 0))
        self.assertEqual(fake.pings, ["r1"])
        self.assertEqual(fake.forgot, [])

    def test_idle_live_thread_gets_pinged_too(self):
        state = _idle_run(events=[_usage_event(h1=500)])
        self.assertEqual(self.run_rule(state, self.due(), self.ok(1, 0)).pings, ["r1"])

    def test_not_due_yet(self):
        state = _idle_run(events=[_usage_event(h1=500)])
        fake = self.run_rule(state, self.due(touchedAt=self.NOW - 60))
        self.assertEqual(fake.pings, [])

    def test_window_over_forgets(self):
        state = _idle_run(events=[_usage_event(h1=500)])
        fake = self.run_rule(state, self.due(realAt=self.NOW - serve.KEEPALIVE_WINDOW_S))
        self.assertEqual((fake.pings, fake.forgot), ([], ["r1"]))

    def test_five_minute_cache_is_never_pinged(self):
        state = _idle_run(events=[_usage_event(h1=500), _usage_event(m5=500)])
        fake = self.run_rule(state, self.due())
        self.assertEqual((fake.pings, fake.forgot), ([], ["r1"]))

    def test_a_ping_that_wrote_stops_further_pings(self):
        state = _idle_run(events=[_usage_event(h1=500)])
        fake = self.run_rule(state, self.due(), self.ok(0, 260_000))
        self.assertEqual((fake.pings, fake.forgot), (["r1"], ["r1"]))

    def test_busy_or_stopped_threads_are_left_alone(self):
        for over in ({"turn_done": False}, {"stop_reason": "user-stop", "done": True},
                     {"msg_queue": [{"id": "q"}]}, {"kind": "node-agent"}):
            state = _idle_run(events=[_usage_event(h1=500)], **over)
            self.assertEqual(self.run_rule(state, self.due()).pings, [], over)


class _Upstream(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    seen = []
    status = 200

    def log_message(self, *a):
        pass

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        type(self).seen.append((self.path, dict(self.headers), json.loads(body)))
        out = json.dumps({"content": [], "usage": {"cache_read_input_tokens": 1234,
                                                   "cache_creation_input_tokens": 0}}).encode()
        self.send_response(type(self).status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)


class ProxyKeepaliveTests(unittest.TestCase):
    def setUp(self):
        _Upstream.seen, _Upstream.status = [], 200
        self.up = ThreadingHTTPServer(("127.0.0.1", 0), _Upstream)
        threading.Thread(target=self.up.serve_forever, daemon=True).start()
        self.addCleanup(self.up.shutdown)
        self.addCleanup(self.up.server_close)
        patcher = patch.object(proxy, "UPSTREAM", ("http", "127.0.0.1", self.up.server_address[1]))
        patcher.start()
        self.addCleanup(patcher.stop)
        for rid in proxy.keepalive_runs():
            proxy.keepalive_forget(rid)

    def body(self, n, system="SYS", **extra):
        msgs = [{"role": "user", "content": "m%d" % i} for i in range(n)]
        return json.dumps({"model": "claude-opus-5-5", "system": system, "messages": msgs,
                           "max_tokens": 64000, "stream": True,
                           "thinking": {"type": "adaptive"}, **extra}).encode()

    def test_run_prefix_is_split_off(self):
        self.assertEqual(proxy._split_run_path("/r/abc_1/v1/messages?beta=true"),
                         ("abc_1", "/v1/messages?beta=true"))
        self.assertEqual(proxy._split_run_path("/v1/messages"), (None, "/v1/messages"))

    def test_replays_main_thread_with_max_tokens_zero(self):
        hdr = {"Authorization": "Bearer tok", "anthropic-beta": "x", "Accept": "text/event-stream"}
        proxy._ka_record("run1", "/v1/messages?beta=true", hdr, self.body(40))
        proxy._ka_record("run1", "/v1/messages?beta=true", hdr, self.body(3, system="SUBAGENT"))
        proxy._ka_record("run1", "/v1/messages/count_tokens", hdr, self.body(99))
        before = proxy.keepalive_status("run1")
        self.assertEqual(before["messages"], 40)
        time.sleep(0.01)
        res = proxy.keepalive("run1")
        self.assertTrue(res["ok"])
        self.assertEqual(res["usage"]["cache_read_input_tokens"], 1234)
        path, headers, sent = _Upstream.seen[-1]
        self.assertEqual(path, "/v1/messages?beta=true")
        self.assertEqual(sent["max_tokens"], 0)
        self.assertNotIn("stream", sent)
        self.assertEqual(len(sent["messages"]), 40)
        self.assertEqual(sent["system"], "SYS")
        self.assertEqual(headers.get("Authorization"), "Bearer tok")
        self.assertEqual(headers.get("anthropic-beta"), "x")
        self.assertEqual(headers.get("Accept"), "application/json")
        after = proxy.keepalive_status("run1")
        self.assertGreater(after["touchedAt"], before["touchedAt"])
        self.assertEqual(after["realAt"], before["realAt"])

    def test_rejected_replay_retires_the_entry(self):
        proxy._ka_record("run2", "/v1/messages", {}, self.body(5))
        _Upstream.status = 400
        self.assertFalse(proxy.keepalive("run2")["ok"])
        self.assertIsNone(proxy.keepalive_status("run2"))
        self.assertIsNone(proxy.keepalive("run2"))

    def test_shapes_max_tokens_zero_rejects_are_never_sent(self):
        proxy._ka_record("run3", "/v1/messages", {}, self.body(5, thinking={"type": "enabled", "budget_tokens": 2048}))
        self.assertEqual(proxy.keepalive("run3")["reason"], "unsupported")
        self.assertEqual(_Upstream.seen, [])

    def test_forget_removes_the_body_file(self):
        proxy._ka_record("run4", "/v1/messages", {}, self.body(5))
        files = [e["file"] for e in proxy._KA["run4"].values()]
        proxy.keepalive_forget("run4")
        self.assertFalse(any(os.path.exists(f) for f in files))
        self.assertNotIn("run4", proxy.keepalive_runs())

    def test_handler_records_per_run_and_strips_prefix(self):
        url = proxy.start_in_background("http://127.0.0.1:%d" % self.up.server_address[1])
        import http.client
        host, port = url.rsplit(":", 1)
        conn = http.client.HTTPConnection("127.0.0.1", int(port), timeout=10)
        conn.request("POST", "/r/run5/v1/messages?beta=true", body=self.body(7),
                     headers={"Content-Type": "application/json", "Authorization": "Bearer t"})
        conn.getresponse().read()
        conn.close()
        self.assertEqual(_Upstream.seen[-1][0], "/v1/messages?beta=true")
        self.assertEqual(proxy.keepalive_status("run5")["messages"], 7)


FAKE_CLAUDE = textwrap.dedent("""
    import json, sys
    argv_log = sys.argv[1]
    with open(argv_log, "a") as f:
        f.write(json.dumps(sys.argv[2:]) + "\\n")
    sid = "11111111-2222-3333-4444-555555555555"
    def out(o):
        sys.stdout.write(json.dumps(o) + "\\n"); sys.stdout.flush()
    out({"type": "system", "subtype": "init", "session_id": sid, "tools": [], "model": "m"})
    for line in sys.stdin:
        out({"type": "assistant", "session_id": sid, "message": {
            "role": "assistant", "content": [{"type": "text", "text": "ok"}],
            "usage": {"input_tokens": 2, "output_tokens": 1,
                      "cache_read_input_tokens": 1000, "cache_creation_input_tokens": 10,
                      "cache_creation": {"ephemeral_1h_input_tokens": 10,
                                         "ephemeral_5m_input_tokens": 0}}}})
        out({"type": "result", "subtype": "success", "is_error": False,
             "result": "ok", "session_id": sid})
""")


def _wait(pred, timeout=10.0):
    end = time.time() + timeout
    while time.time() < end:
        if pred():
            return True
        time.sleep(0.05)
    return False


class ParkResumeEndToEndTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = os.path.join(self.tmp.name, "proj")
        for d in ("source", "editor", "workflow"):
            os.makedirs(os.path.join(self.root, d))
        self.fake = os.path.join(self.tmp.name, "fake_claude.py")
        with open(self.fake, "w") as f:
            f.write(FAKE_CLAUDE)
        self.argv_log = os.path.join(self.tmp.name, "argv.jsonl")

    def spawn(self, *args, **kw):
        kw.pop("bufsize", None)
        return subprocess.Popen([sys.executable, self.fake, self.argv_log, *args], **kw)

    def start_run(self):
        proc = self.spawn(stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, start_new_session=True)
        state = serve.RunState("e2e0000000000001", proc, "claude", "main", "freeform", "chat",
                               project_id="p", project_root=self.root)
        state.bin_path = "/fake/claude"
        state.permission_mode = "bypassPermissions"
        serve.RUNS[state.run_id] = state
        self.addCleanup(serve.RUNS.pop, state.run_id, None)
        self.addCleanup(lambda: state.proc and state.proc.poll() is None and state.proc.kill())
        threading.Thread(target=serve._drain_stdout, args=(state,), daemon=True).start()
        threading.Thread(target=serve._drain_stderr, args=(state,), daemon=True).start()
        proc.stdin.write(serve._claude_user_frame("hi"))
        proc.stdin.flush()
        self.assertTrue(_wait(lambda: state.turn_done and state.session_id))
        return state

    def handler(self, body):
        h = object.__new__(serve.H)
        h.path = "/__run/x?project=p"
        h._reply = lambda status, value: (status, value)
        h._read_json_body = lambda **kw: body
        return h

    def test_park_then_reply_resumes_the_same_session(self):
        state = self.start_run()
        old = state.proc
        state.updated_at = time.time() - serve.PARK_AFTER_S - 1
        with patch.object(serve, "_EVICT_BASE_URL", None):
            serve._idle_watch_round([state], time.time())
        self.assertEqual(state.stop_reason, "parked")

        # A reply racing the park is turned away, never written into the
        # dying process, and points the client at /resume.
        status, reply = self.handler({"text": "next"})._run_user_message(state.run_id)
        self.assertEqual(status, 409)
        self.assertTrue(reply.get("needsResume"))
        self.assertIsNotNone(old.poll())

        self.assertTrue(state.exit_settled.wait(10))
        self.assertTrue(state.done)
        self.assertEqual(state.exit_code, 0)
        end = [e for e in state.events if e["type"] == "end"][-1]["data"]
        self.assertEqual(end["stopReason"], "parked")

        spawn = lambda agent_id, argv, **kw: self.spawn(*argv[1:], **kw)
        with patch.object(serve, "_spawn_runtime_process", side_effect=spawn), \
             patch.object(serve, "_ensure_harness_settings", return_value=None), \
             patch.object(serve, "_mcp_config_spawn_args", return_value=[]), \
             patch.object(serve, "_agents_plugin_spawn_args", return_value=[]), \
             patch.object(serve, "_chat_system_prompt", return_value="SYS"), \
             patch.object(serve, "_agent_model_spawn_args", return_value=[]), \
             patch.object(serve, "_build_child_env", return_value=dict(os.environ)):
            status, reply = self.handler({"text": "next"})._run_resume(state.run_id)
        self.assertEqual(status, 200, reply)
        self.assertTrue(_wait(lambda: state.turns_completed >= 2 or
                              (state.turn_done and state.proc is not old)))
        self.assertTrue(_wait(lambda: state.turn_done))
        self.assertFalse(state.done)
        self.assertIsNone(state.stop_reason)
        self.assertIsNotNone(state.history_pending_id)
        self.assertFalse(state._resume_probe)
        with open(self.argv_log) as f:
            resumed_argv = json.loads(f.read().splitlines()[-1])
        i = resumed_argv.index("--resume")
        self.assertEqual(resumed_argv[i + 1], state.session_id)
        self.assertIn("SYS", resumed_argv)
        # The old drain is long settled; nothing may finish() the new process.
        time.sleep(0.3)
        self.assertFalse(state.done)
        serve._kill_run_tree(state)
        self.assertTrue(state.exit_settled.wait(10))

    def test_resume_waits_for_the_old_drain_to_settle(self):
        state = self.start_run()
        old = state.proc
        state.updated_at = time.time() - serve.PARK_AFTER_S - 1
        with patch.object(serve, "_EVICT_BASE_URL", None):
            serve._idle_watch_round([state], time.time())
        real_pending = serve._pending_run_jobs
        drain_thread = []

        def slow_pending(s):
            # Hold the OLD drain in its finally-block, before finish().
            if threading.current_thread() is not threading.main_thread():
                drain_thread.append(1)
                time.sleep(1.0)
            return real_pending(s)

        spawn = lambda agent_id, argv, **kw: self.spawn(*argv[1:], **kw)
        with patch.object(serve, "_pending_run_jobs", side_effect=slow_pending), \
             patch.object(serve, "_spawn_runtime_process", side_effect=spawn), \
             patch.object(serve, "_ensure_harness_settings", return_value=None), \
             patch.object(serve, "_mcp_config_spawn_args", return_value=[]), \
             patch.object(serve, "_agents_plugin_spawn_args", return_value=[]), \
             patch.object(serve, "_chat_system_prompt", return_value="SYS"), \
             patch.object(serve, "_agent_model_spawn_args", return_value=[]), \
             patch.object(serve, "_build_child_env", return_value=dict(os.environ)):
            self.assertTrue(_wait(lambda: old.poll() is not None))
            self.assertFalse(state.exit_settled.is_set())   # drain still finishing
            status, reply = self.handler({"text": "next"})._run_resume(state.run_id)
            self.assertEqual(status, 200, reply)
            self.assertTrue(drain_thread)
            self.assertIsNot(state.proc, old)
            self.assertTrue(_wait(lambda: state.turn_done))
        time.sleep(1.5)     # longer than the old drain's hold above
        self.assertFalse(state.done, "the old drain finished the resumed process")
        self.assertTrue(state.proc.poll() is None)
        serve._kill_run_tree(state)
        self.assertTrue(state.exit_settled.wait(10))

    def test_drain_marks_exit_settled_only_after_exit_handling(self):
        state = self.start_run()
        self.assertFalse(state.exit_settled.is_set())
        state.stop_reason = "user-stop"
        serve._kill_run_tree(state)
        self.assertTrue(state.exit_settled.wait(10))
        self.assertTrue(state.done)


if __name__ == "__main__":
    unittest.main()

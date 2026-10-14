"""Per-message chat modes: Normal / Plan / Triage, switchable inside one thread.

The mode rides on each user message instead of the system prompt, so the user
can triage a request, plan it and build it in ONE thread. The agent receives
the mode's rules folded into the message; the thread echoes the user's own
words, stamped with the mode, and that stamp is the thread's current mode.

Run: python3 -m unittest discover -s editor/tests -p test_chat_modes.py -v
"""
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

EDITOR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EDITOR))
import plan_split
import serve
from kinds import capabilities as caps

DASHES = ("—", "–")


def fake_state(guards=None, modes=()):
    state = SimpleNamespace(run_id="r1", lock=threading.Lock(), events=[],
                            guards=guards or {"visual": True, "dsGuard": True, "reqQa": False, "plan": False},
                            done=False, stop_reason=None, turn_done=True, msg_queue=[])
    def append(kind, data):
        state.events.append({"seq": len(state.events), "type": kind, "data": data})
    state.append = append
    for m in modes:
        append("user_message", {"text": "earlier", "mode": m} if m else {"text": "earlier"})
    return state


class ModeTextTests(unittest.TestCase):
    def test_triage_folds_its_rules_in_ahead_of_the_users_words(self):
        out = caps.chat_mode_message("triage", "normal", "Remove the due date")
        self.assertIn("TRIAGE - report only", out)
        self.assertTrue(out.endswith("===== THE USER'S MESSAGE =====\nRemove the due date"))
        for must in ("[Overridden - ignore]", "[Stale - ignore]", "[In effect]", "__chat_search",
                     "git log", "not technical", "ONE complete sentence", "BEFORE and AFTER",
                     "You change NOTHING", "Needs your call"):
            self.assertIn(must, out)

    def test_plan_is_the_thread_stub_reframed_for_one_message(self):
        out = caps.chat_mode_message("plan", "triage", "x")
        self.assertIn('(the user picked "Plan" mode for this message)', out)
        self.assertIn("Before you BUILD anything asked for in this message,", out)
        self.assertNotIn('ON for this thread', out)
        # same rules as the spawn-time stub: everything after its header line
        self.assertIn(caps.PLAN_MODE_STUB.split("\n", 4)[4], out)

    def test_normal_is_untouched_unless_it_follows_another_mode(self):
        self.assertEqual(caps.chat_mode_message("normal", "normal", "go"), "go")
        self.assertEqual(caps.chat_mode_message(None, None, "go"), "go")
        back = caps.chat_mode_message("normal", "triage", "go")
        self.assertTrue(back.startswith("[Woven mode for THIS message: NORMAL. The user switched back from Triage"))
        self.assertTrue(back.endswith("go"))

    def test_no_dashes_in_any_mode_text(self):
        for text in (caps.TRIAGE_MODE_MESSAGE, caps.PLAN_MODE_MESSAGE, caps.NORMAL_MODE_RETURN, caps._MODE_LEAD):
            for d in DASHES:
                self.assertNotIn(d, text)

    def test_unknown_mode_names_are_ignored(self):
        self.assertIsNone(caps.normalize_chat_mode("yolo"))
        self.assertEqual(caps.normalize_chat_mode(" Triage "), "triage")


class ThreadModeTests(unittest.TestCase):
    def test_latest_stamped_message_is_the_threads_mode(self):
        self.assertEqual(serve._thread_chat_mode(fake_state(modes=("triage", "plan", None))), "plan")
        self.assertEqual(serve._thread_chat_mode(fake_state()), "normal")

    def test_old_plan_thread_reads_as_plan_until_switched(self):
        legacy = fake_state(guards={"plan": True}, modes=(None,))
        self.assertEqual(serve._thread_chat_mode(legacy), "plan")
        legacy.append("user_message", {"text": "go", "mode": "normal"})
        self.assertEqual(serve._thread_chat_mode(legacy), "normal")

    def test_a_message_without_a_mode_keeps_the_threads(self):
        # a card answer, a daemon nudge: no `mode` on the body
        send, mode = serve._mode_send(fake_state(modes=("triage",)), "[decision:x] a", None)
        self.assertEqual(mode, "triage")
        self.assertIn("TRIAGE - report only", send)

    def test_switching_mid_thread(self):
        st = fake_state(modes=("triage",))
        send, mode = serve._mode_send(st, "now build it", "normal")
        self.assertEqual(mode, "normal")
        self.assertIn("switched back from Triage", send)


class DeliveryTests(unittest.TestCase):
    def test_user_message_sends_the_rules_and_echoes_the_words(self):
        st = fake_state(modes=("normal",))
        sink = io.BytesIO()
        st.proc = SimpleNamespace(stdin=sink)
        got = {}
        fake = SimpleNamespace(_read_json_body=lambda max_bytes=0: {"text": "Drop the due date", "mode": "triage"},
                               _reply=lambda code, body: got.update(code=code, **body))
        st.is_live = True
        with patch.dict(serve.RUNS, {"r1": st}, clear=True):
            serve.H._run_user_message(fake, "r1")
        self.assertEqual(got["code"], 200)
        frame = json.loads(sink.getvalue().decode("utf-8"))
        sent = frame["message"]["content"][0]["text"]
        self.assertIn("TRIAGE - report only", sent)
        self.assertTrue(sent.endswith("Drop the due date"))
        self.assertEqual(st.events[-1]["data"], {"text": "Drop the due date", "mode": "triage"})

    def test_enqueue_keeps_the_mode_it_was_typed_in(self):
        st = fake_state()
        st.msg_queue = []
        got = {}
        fake = SimpleNamespace(_read_json_body=lambda max_bytes=0: {"text": "later", "mode": "plan"},
                               _reply=lambda code, body: got.update(body),
                               _run_queue_state=lambda rid: st)
        with patch.object(serve, "_queue_persist", lambda s: None), \
             patch.object(serve, "_queue_drain_maybe", lambda s, mode="stdin": None):
            serve.H._run_enqueue(fake, "r1")
        self.assertEqual(got["entry"]["mode"], "plan")


class RoleTests(unittest.TestCase):
    def test_role_follows_the_latest_mode(self):
        self.assertEqual(plan_split.thread_role({"plan": False}, None, None, "triage"), {"role": "triage"})
        self.assertEqual(plan_split.thread_role({"plan": True}, None, None, "normal"), None)
        self.assertEqual(plan_split.thread_role({"plan": True}, None, None), {"role": "plan"})

    def test_runs_list_role_is_read_off_the_latest_message(self):
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root)
        os.makedirs(os.path.join(root, "editor"))
        base = {"runId": "t1", "branch": "main", "agentId": "claude", "kind": "freeform",
                "title": "triage me", "startedAt": 1000.0}
        lines = [dict(base, seq=0, type="status", ts=1000.0, data={"label": "spawned", "guards": {"plan": False}}),
                 dict(base, seq=1, type="user_message", ts=1001.0, data={"text": "a", "mode": "triage"})]
        with open(os.path.join(root, "editor", "chat.jsonl"), "w") as f:
            f.write("\n".join(json.dumps(l) for l in lines) + "\n")
        got = {}
        fake = SimpleNamespace(_reply=lambda code, body: got.update(body))
        with patch.object(serve, "resolve_project_root", lambda qs: root), \
             patch.dict(serve.RUNS, {}, clear=True):
            serve.H._runs_list(fake, {"project": ["p"]})
        row = next(r for r in got["runs"] if r["runId"] == "t1")
        self.assertEqual(row["planRole"], {"role": "triage"})
        self.assertNotIn("_roleSpawn", row)


if __name__ == "__main__":
    unittest.main()

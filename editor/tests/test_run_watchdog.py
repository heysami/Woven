"""Watchdog regressions for active child runs. No CLI or model calls."""
import io
from pathlib import Path
import sys
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import serve


def run(rid, parent=None, project="/fixture/lulu", turn_done=False):
    state = SimpleNamespace(run_id=rid, parent_run_id=parent, project_root=project,
        project_id=project, done=False, process_running=True, is_live=True,
        turn_done=turn_done, jobs={}, lock=threading.Lock(), events=[],
        workflow_node_id=rid, kind="node-agent", title=rid)
    def append(kind, data):
        state.events.append({"seq": len(state.events), "type": kind, "data": data})
    state.append = append
    return state


class WatchdogTests(unittest.TestCase):
    def test_active_research_does_not_stall_quiet_qa_or_main(self):
        main = run("main", turn_done=True)
        qa = run("qa", parent="main", turn_done=True)
        research = run("research", parent="qa")
        states = [main, qa, research]
        seen = {"qa": [-1, 0, False]}
        with patch.dict(serve.RUNS, {s.run_id: s for s in states}, clear=True), \
             patch.object(serve, "_stall_tell_parent") as tell:
            for now in range(0, 3601, 300):
                research.append("agent", {"type": "tool_result"})
                serve._stall_watch_round(states, seen, now)
        tell.assert_not_called()
        self.assertEqual(set(seen), {"research"})
        self.assertFalse(main.events)
        self.assertFalse(qa.events)

    def test_silent_child_warns_once_and_real_progress_rearms(self):
        qa, child = run("qa", turn_done=True), run("child", parent="qa")
        states, seen = [qa, child], {}
        with patch.dict(serve.RUNS, {s.run_id: s for s in states}, clear=True), \
             patch.object(serve, "_stall_tell_parent") as tell:
            for now in [0, 899, 900, 1800]:
                serve._stall_watch_round(states, seen, now)
            tell.assert_called_once_with(child, 15)
            child.append("agent", {"type": "tool_result"})
            serve._stall_watch_round(states, seen, 1801)
            serve._stall_watch_round(states, seen, 2701)
            self.assertEqual(tell.call_count, 2)

    def test_finished_child_returns_parent_to_monitoring_with_fresh_timer(self):
        parent, child = run("parent"), run("child", parent="parent")
        states, seen = [parent, child], {"parent": [-1, 0, False]}
        with patch.object(serve, "_stall_tell_parent") as tell:
            serve._stall_watch_round(states, seen, 1000)
            child.done = True
            serve._stall_watch_round(states, seen, 2000)
            tell.assert_not_called()
            serve._stall_watch_round(states, seen, 2900)
            tell.assert_called_once_with(parent, 15)

    def test_other_project_cannot_suppress_parent_warning(self):
        parent = run("parent")
        unrelated = run("other", parent="parent", project="/fixture/other")
        states, seen = [parent, unrelated], {}
        with patch.object(serve, "_stall_tell_parent") as tell:
            serve._stall_watch_round(states, seen, 0)
            unrelated.append("agent", {"type": "tool_result"})
            serve._stall_watch_round(states, seen, 900)
            tell.assert_called_once_with(parent, 15)

    def test_idle_chat_is_not_a_stall_but_pending_native_work_is_watched(self):
        idle = run("idle", turn_done=True)
        waiting = run("waiting", turn_done=True)
        waiting.jobs["native"] = {"jobId": "native", "source": "native", "status": "running"}
        states, seen = [idle, waiting], {}
        with patch.dict(serve.RUNS, {s.run_id: s for s in states}, clear=True), \
             patch.object(serve, "_stall_tell_parent") as tell:
            serve._stall_watch_round(states, seen, 0)
            serve._stall_watch_round(states, seen, 900)
            tell.assert_called_once_with(waiting, 15)

    def test_parent_notice_requests_investigation_without_ordering_stop(self):
        parent, child = run("parent"), run("child", parent="parent")
        parent.proc = SimpleNamespace(stdin=io.BytesIO())
        with patch.dict(serve.RUNS, {s.run_id: s for s in [parent, child]}, clear=True):
            serve._stall_tell_parent(child, 15)
            text = parent.events[-1]["data"]["text"]
            self.assertIn("Check its pending jobs, child runs, and saved outputs", text)
            self.assertIn("Do not stop an active worker or skip required QA", text)
            self.assertNotIn("polling will never resolve", text)
            parent.project_root = "/fixture/other"
            self.assertIsNone(serve._stall_find_parent(child))


if __name__ == "__main__":
    unittest.main()

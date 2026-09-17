"""Regression cases from the CLI/model portability audit. No paid model calls."""
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import model_routing as models
import mcp_routing as mcp
import run_jobs
import runtime_drivers as drivers
import serve
import review_evidence
import contract_writer
import helper_jobs
from concurrent.futures import ThreadPoolExecutor


class ModelRoutingTests(unittest.TestCase):
    def test_api_string_results_are_not_discarded(self):
        with patch.object(serve, "_resolve_provider_key", return_value="fixture"), patch.object(serve, "_openai_chat", return_value="expected response"):
            self.assertEqual(serve.H._llm_dispatch(None, {"provider": "openai", "model": "gpt-6-astra"}, "hello"), "expected response")

    def test_exact_ids_and_future_models_are_preserved(self):
        for runtime, model in [("claude", "claude-opus-4-6"), ("claude", "claude-fable-5"),
                               ("codex", "gpt-6-astra"), ("opencode", "google/future-model")]:
            self.assertEqual(models.spawn_model(runtime, model), ["--model", model])

    def test_economy_and_registered_models_do_not_depend_on_prefixes(self):
        cfg = {"economyModels": {"codex": "small"}, "modelCatalog": [
            {"id": "small", "runtime": "codex", "model": "my-new-model", "efforts": ["low"]}]}
        result = models.resolve("fast", "codex", "gpt-6-astra", cfg, role="summary")
        self.assertEqual((result["runtime"], result["model"], result["isolation"]), ("codex", "my-new-model", "text-only"))
        self.assertEqual(models.resolve("opencode:local/cheaper", "claude")["runtime"], "opencode")

    def test_inheritance_preserves_default_and_runtime(self):
        result = models.resolve("inherit", "opencode", None)
        self.assertEqual((result["runtime"], result["model"]), ("opencode", None))
        self.assertEqual(models.resolve("fast", "opencode")["runtime"], "opencode")
        with self.assertRaises(ValueError):
            models.spawn_model("claude", "gpt-6-astra")
        changed_catalog = {"modelCatalog": [{"id": "native-id", "runtime": "claude", "model": "other"}]}
        self.assertEqual(models.resolve("inherit", "codex", "native-id", changed_catalog)["model"], "native-id")
        self.assertEqual(models.resolve("inherit", "codex", "native-id", changed_catalog)["runtime"], "codex")
        with patch.object(serve, "_compact_config", return_value=changed_catalog):
            self.assertEqual(serve._agent_model_spawn_args("codex", {}, "native-id", resolved=True), ["--model", "native-id"])

    def test_catalog_rejects_bad_shapes_not_unknown_models(self):
        self.assertTrue(models.valid_model("vendor/custom-model-v9"))
        for value in ("--model", "hi\n--tools", "$(cmd)", ""):
            self.assertFalse(models.valid_model(value))
        with self.assertRaises(ValueError):
            models.validate_catalog([{"id": "new", "model": "new", "runtime": "made-up"}])


class JobTests(unittest.TestCase):
    def test_launch_ack_does_not_complete_background_worker(self):
        jobs = {}
        for event in [run_jobs.observe({}, {"type": "tool_use", "name": "Agent", "id": "tool", "input": {}}, "claude"),
                      run_jobs.claude_job({"subtype": "task_started", "task_id": "task", "tool_use_id": "tool"})]:
            run_jobs.reduce_job(jobs, event)
        ack = run_jobs.observe(jobs, {"type": "tool_result", "toolUseId": "tool", "content": "Launched agent"}, "claude")
        run_jobs.reduce_job(jobs, ack)
        self.assertEqual(len(run_jobs.pending(jobs)), 1)
        run_jobs.reduce_job(jobs, run_jobs.claude_job({"subtype": "task_notification", "task_id": "task", "status": "completed"}))
        self.assertFalse(run_jobs.pending(jobs))
        run_jobs.reduce_job(jobs, run_jobs.claude_job({"subtype": "task_progress", "task_id": "task"}))
        self.assertFalse(run_jobs.pending(jobs))

    def test_multiple_receivers_of_one_tool_remain_distinct(self):
        jobs = {}
        for identity in ("child-a", "child-b"):
            run_jobs.reduce_job(jobs, {"type": "job", "jobId": identity, "toolUseId": "wait-call", "status": "running"})
        self.assertEqual(len(jobs), 2)

    def test_foreground_claude_result_finishes_even_with_agent_id(self):
        jobs = {}
        run_jobs.reduce_job(jobs, run_jobs.observe(jobs, {"type": "tool_use", "id": "call", "name": "Agent", "input": {}}, "claude"))
        run_jobs.reduce_job(jobs, run_jobs.claude_job({"subtype": "task_started", "task_id": "child", "tool_use_id": "call"}))
        run_jobs.reduce_job(jobs, run_jobs.observe(jobs, {"type": "tool_result", "toolUseId": "call", "content": "Finished the review. agentId: child"}, "claude"))
        self.assertFalse(run_jobs.pending(jobs))

    def test_new_turn_reopens_child_but_old_completion_does_not_finish_it(self):
        jobs = {}
        for event in [
            {"type": "job", "jobId": "child", "attemptId": "one", "status": "completed"},
            {"type": "job", "jobId": "child", "attemptId": "two", "status": "running", "restart": True},
            {"type": "job", "jobId": "child", "attemptId": "one", "status": "completed"},
        ]:
            run_jobs.reduce_job(jobs, event)
        self.assertEqual(jobs["child"]["status"], "running")
        self.assertEqual(jobs["child"]["attemptId"], "two")
        run_jobs.reduce_job(jobs, {"type": "job", "jobId": "child", "attemptId": "two", "status": "completed"})
        run_jobs.reduce_job(jobs, {"type": "job", "jobId": "child", "status": "stopped", "resourceClosed": True})
        self.assertEqual(jobs["child"]["status"], "completed")

    def test_late_tool_identity_keeps_completed_child_state(self):
        jobs = {"child": {"jobId": "child", "status": "completed"},
                "call": {"jobId": "call", "toolUseId": "call", "status": "pending"}}
        run_jobs.reduce_job(jobs, {"type": "job", "jobId": "child", "toolUseId": "call", "status": "running"})
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs["child"]["status"], "completed")

    def test_opencode_metadata_arrives_before_tool_result(self):
        events = serve._OpenCodeStreamParser().feed({"type": "tool", "part": {"type": "tool", "tool": "task", "callID": "call",
            "state": {"status": "completed", "output": "Acknowledged", "metadata": {"background": True, "sessionId": "child"}}}})
        jobs = {}
        for event in events:
            derived = run_jobs.observe(jobs, event, "opencode")
            run_jobs.reduce_job(jobs, event)
            if derived:
                run_jobs.reduce_job(jobs, derived)
        self.assertEqual(jobs["child"]["status"], "running")

    def test_late_child_completion_settles_parent_once(self):
        with tempfile.TemporaryDirectory() as root:
            state = serve.RunState("p", Mock(poll=Mock(return_value=None)), "codex", "main", "node-agent", "test", project_root=root)
            state.workflow_node_id, state.turn_done = "node", True
            state.events = [{"type": "agent", "data": {"type": "status", "label": "done"}}]
            state.jobs["c"] = {"jobId": "c", "status": "running"}
            with patch.object(serve, "RUNS", {"p": state}), patch.object(serve, "_kill_run_tree") as kill, patch.object(serve, "_fire_node_completion_hook") as complete, patch.object(serve, "_chat_jsonl_append"):
                serve._settle_run_jobs(state)
                complete.assert_not_called()
                state.append("agent", {"type": "job", "jobId": "c", "status": "completed"})
                state.append("agent", {"type": "job", "jobId": "c", "status": "completed"})
                complete.assert_called_once_with(state, exit_code=0, error_detail=None)
                kill.assert_called_once_with(state)

    def test_native_frames_and_child_attribution_survive(self):
        for subtype in ("task_started", "task_updated", "task_notification"):
            result = serve._normalize_frame("claude", {"type": "system", "subtype": subtype, "task_id": "child"})
            self.assertEqual(result[0]["type"], "job")
        events = serve._normalize_frame("claude", {"type": "assistant", "parent_tool_use_id": "parent",
            "message": {"content": [{"type": "text", "text": "child text"}]}})
        self.assertEqual(events[0]["parentToolUseId"], "parent")

    def test_compaction_waits_for_native_children_after_parent_done(self):
        with tempfile.TemporaryDirectory() as root:
            state = serve.RunState("test", Mock(poll=Mock(return_value=None)), "claude", "main", "freeform", "test", project_root=root)
            state.turn_done = True
            state.jobs["child"] = {"jobId": "child", "status": "running"}
            with patch.object(serve, "RUNS", {}), patch.object(serve, "_kill_run_tree") as kill:
                result = serve._compact_commit(state, "summary", 100000, "manual", 2)
                self.assertTrue(result["deferred"])
                kill.assert_not_called()

    def test_stop_signals_process_without_stdin_and_logical_children(self):
        with tempfile.TemporaryDirectory() as root:
            proc = Mock(stdin=None, poll=Mock(return_value=None))
            parent = serve.RunState("p", proc, "codex", "main", "freeform", "test", project_root=root)
            child = serve.RunState("c", proc, "codex", "main", "node-agent", "test", project_root=root)
            child.parent_run_id = "p"
            handler = SimpleNamespace(_reply=lambda code, body: (code, body))
            with patch.object(serve, "RUNS", {"p": parent, "c": child}), patch.object(serve, "_kill_run_tree") as kill, patch.object(serve, "_chat_jsonl_append"):
                code, result = serve.H._run_stop(handler, "p")
                self.assertEqual(code, 200)
                self.assertNotIn("wasGhost", result)
                self.assertIn(child, [c.args[0] for c in kill.call_args_list])


class MCPTests(unittest.TestCase):
    def test_remote_and_timeout_units(self):
        spec = {"url": "https://example.test/mcp", "headers": {"X-Test": "value"}, "startupTimeoutMs": 15000}
        self.assertEqual(mcp.translate(spec, "codex")["startup_timeout_sec"], 15)
        self.assertEqual(mcp.translate(spec, "opencode")["timeout"], 15000)
        self.assertEqual(mcp.translate(spec, "codex")["http_headers"], {"X-Test": "value"})
        secret_spec = {"url": "https://example.test/mcp", "envHeaders": {"X-Key": "MY_KEY"}, "bearerTokenEnvVar": "MY_TOKEN"}
        translated = mcp.translate(secret_spec, "opencode")
        self.assertEqual(translated["headers"], {"X-Key": "{env:MY_KEY}", "Authorization": "Bearer {env:MY_TOKEN}"})
        self.assertFalse(translated["oauth"])

    def test_jsonc_keeps_url_strings_and_removes_comments(self):
        value = mcp.jsonc_loads('{// comment\n"url":"https://host/a//b", /* x */ "items":[1,],}')
        self.assertEqual(value, {"url": "https://host/a//b", "items": [1]})

    def test_unsupported_transport_is_explicit(self):
        with self.assertRaises(ValueError):
            mcp.translate({"url": "https://example.test/sse", "type": "sse"}, "codex")


class DriverReplayTests(unittest.TestCase):
    def codex(self):
        driver = drivers.CodexDriver.__new__(drivers.CodexDriver)
        drivers.ProcessDriver.__init__(driver)
        driver.session_id, driver.model, driver.streamed = "root", "gpt-6-astra", set()
        driver.completed_turns = set()
        driver.emit = Mock()
        return driver

    def test_codex_turn_steering_and_ambiguous_delivery(self):
        driver = self.codex()
        driver.turn_id = "turn1"
        driver.request = Mock(side_effect=TimeoutError("unknown"))
        with self.assertRaises(TimeoutError):
            driver.send_user("adjust")
        self.assertEqual(driver.request.call_count, 1)
        self.assertEqual(driver.request.call_args.args[0], "turn/steer")
        self.assertEqual(driver.request.call_args.args[1]["expectedTurnId"], "turn1")

    def test_codex_parent_done_does_not_finish_native_child(self):
        driver = self.codex()
        driver.notification("item/completed", {"threadId": "root", "item": {"type": "collabAgentToolCall", "id": "spawn",
            "tool": "spawnAgent", "receiverThreadIds": ["child"], "agentsStates": {"child": {"status": "running"}}}})
        driver.notification("turn/completed", {"threadId": "root", "turn": {"id": "parent-turn", "status": "completed"}})
        self.assertEqual(driver.children, {"child": "spawn"})
        driver.notification("turn/completed", {"threadId": "child", "turn": {"status": "completed"}})
        self.assertEqual(driver.emit.call_args.args[0]["jobId"], "child")

    def test_codex_text_never_parsed_as_tools(self):
        driver = self.codex()
        driver.notification("item/agentMessage/delta", {"threadId": "root", "itemId": "m", "delta": "search\nexec\ncodex"})
        self.assertEqual(driver.emit.call_args.args[0]["type"], "text_delta")
        driver.notification("item/completed", {"threadId": "root", "item": {"type": "agentMessage", "id": "m", "text": "search\nexec\ncodex"}})
        self.assertEqual(driver.emit.call_count, 1)

    def test_opencode_busy_is_queue_not_steer(self):
        driver = drivers.OpenCodeDriver.__new__(drivers.OpenCodeDriver)
        drivers.ProcessDriver.__init__(driver)
        driver.turn_id = "busy"
        driver.request = Mock()
        with self.assertRaisesRegex(RuntimeError, "queue"):
            driver.send_user("later")
        driver.request.assert_not_called()

    def test_opencode_initial_idle_is_not_completion(self):
        driver = drivers.OpenCodeDriver.__new__(drivers.OpenCodeDriver)
        drivers.ProcessDriver.__init__(driver)
        driver.session_id, driver.busy_sessions = "root", set()
        driver.emit = Mock()
        driver.notification({"type": "session.status", "properties": {"sessionID": "root", "status": {"type": "idle"}}})
        driver.emit.assert_not_called()
        driver.notification({"type": "session.status", "properties": {"sessionID": "root", "status": {"type": "busy"}}})
        driver.notification({"type": "session.status", "properties": {"sessionID": "root", "status": {"type": "idle"}}})
        self.assertEqual(driver.emit.call_args.args[0]["label"], "done")


class EvidenceTests(unittest.TestCase):
    def test_missing_vision_is_not_visual_pass(self):
        report = review_evidence.attach({"verdict": "pass", "judge": {"available": False}}, "red sphere", "abc", "abc")
        self.assertEqual(report["renderVerdict"], "pass")
        self.assertEqual(report["verdict"], "inconclusive")
        self.assertEqual(report["visualReview"]["status"], "unavailable")

    def test_edit_during_review_invalidates_result(self):
        report = review_evidence.attach({"verdict": "pass", "judge": {"available": True, "ok": True}}, "red sphere", "abc", "def")
        self.assertEqual(report["verdict"], "stale")

    def test_concurrent_writer_prepare_calls_share_one_completion(self):
        with tempfile.TemporaryDirectory() as root:
            body = {"orchestrator": "simulation-orchestrator", "draft": {"description": "Quiet paper"},
                    "outputPath": "workflow/contract.json", "prosePaths": ["/description"]}
            complete = Mock(return_value='{"edits":[]}')
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda _: contract_writer.prepare(root, body, "gpt-6-astra", complete), range(2)))
            self.assertEqual(complete.call_count, 1)
            self.assertEqual(sum(r["reused"] for r in results), 1)


class HelperTests(unittest.TestCase):
    def test_stop_before_registration_cannot_launch_helper(self):
        with patch.object(helper_jobs.subprocess, "Popen") as spawn:
            with self.assertRaises(helper_jobs.Cancelled):
                with helper_jobs.execution("late", "parent", "codex", cancelled=lambda: True):
                    helper_jobs.run(["should-not-run"])
            spawn.assert_not_called()

    def test_queued_helper_cancellation_releases_registration(self):
        with helper_jobs.execution("active", "one", "codex", limit=1):
            ready = threading.Event()
            def cancellation():
                ready.set()
                return False
            def queued():
                with self.assertRaises(helper_jobs.Cancelled):
                    with helper_jobs.execution("queued", "two", "codex", limit=1, cancelled=cancellation):
                        self.fail("queued helper acquired the occupied slot")
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(queued)
                self.assertTrue(ready.wait(2))
                helper_jobs.cancel("two")
                future.result(timeout=2)
        self.assertFalse(helper_jobs._JOBS)
        self.assertEqual(helper_jobs._ACTIVE["codex"], 0)


if __name__ == "__main__":
    unittest.main()

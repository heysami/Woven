"""Context cost and continuity regressions. No model calls or user projects.

Run: python3 -m unittest discover -s editor/tests -p test_context_policy.py -v
"""
import json
from pathlib import Path
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import context_policy as policy
import serve
from kinds import capabilities as caps


def event(seq, kind, **data):
    return {"seq": seq, "type": kind, "data": data}


class ContextPolicyTests(unittest.TestCase):
    def test_replay_preserves_early_constraints_and_summary(self):
        events = [event(0, "agent", type="compact", summary="Approved copper palette", coveredThrough=-1),
                  event(1, "user_message", text="Only edit source/atlas. Budget is $20."),
                  event(2, "agent", type="text_delta", delta="x" * 100000),
                  event(3, "user_message", text="Keep the nav fixed.")]
        text = policy.transcript(events, detail_budget=100)
        self.assertIn("Approved copper palette", text)
        self.assertIn("Budget is $20", text)
        self.assertIn("Keep the nav fixed", text)
        self.assertIn("observations omitted", text)

    def test_compaction_covers_snapshot_not_commit_time(self):
        events = [event(0, "user_message", text="Build atlas"),
                  event(1, "agent", type="text_delta", delta="Built the shell."),
                  event(2, "user_message", text="New constraint during summary"),
                  event(3, "agent", type="compact", summary="Shell built", coveredThrough=1)]
        self.assertEqual(policy.transcript(events),
                         "[CURRENT WORKING STATE]\nShell built\n\nUSER: New constraint during summary")

    def test_legacy_compaction(self):
        events = [event(0, "user_message", text="old"),
                  event(1, "agent", type="compact", summary="state"),
                  event(2, "user_message", text="new")]
        self.assertNotIn("USER: old", policy.transcript(events))
        self.assertIn("USER: new", policy.transcript(events))

    def test_file_bodies_shrink_but_paths_errors_and_decisions_survive(self):
        events = [event(0, "agent", type="tool_use", name="Write",
                        input={"file_path": "source/atlas/index.html", "content": "x" * 80000}),
                  event(1, "agent", type="tool_result", content="Validation failed", isError=True),
                  event(2, "agent", type="text_delta", delta="Keep the approved irregular grid.")]
        text = policy.transcript(events, detail_budget=None)
        self.assertLess(len(text), 1000)
        self.assertIn("source/atlas/index.html", text)
        self.assertIn("ERROR", text)
        self.assertIn("approved irregular grid", text)

    def test_stream_fragments_are_not_split_into_words(self):
        self.assertEqual(policy.transcript([event(0, "agent", type="text_delta", delta="hel"),
                                          event(1, "agent", type="text_delta", delta="lo")]), "ASSISTANT: hello")

    def test_deferred_commit_keeps_coverage(self):
        state = SimpleNamespace(proc=SimpleNamespace(poll=lambda: None), turn_done=False)
        result = serve._compact_commit(state, "summary", 10000, "test", 12)
        self.assertTrue(result["deferred"])
        self.assertEqual(state._compact_pending["coveredThrough"], 12)

    def test_summary_uses_fast_model_and_failure_does_not_fallback(self):
        state = SimpleNamespace(agent_id="codex", model="gpt-5.6-sol")
        with patch.object(serve, "_compact_config", return_value={"summaryModel": "fast"}), \
             patch.object(serve, "_assistant_agent_complete", return_value="state") as complete:
            self.assertEqual(serve._compact_summarize("transcript", state), "state")
            self.assertEqual(complete.call_args.kwargs["model"], "gpt-5.6-luna")
            self.assertEqual(complete.call_args.kwargs["reasoning"], "low")
        with patch.object(serve, "_compact_config", return_value={"summaryModel": "inherit"}), \
             patch.object(serve, "_assistant_agent_complete", side_effect=RuntimeError("offline")), \
             patch.object(serve, "_ut_llm_text") as fallback:
            with self.assertRaisesRegex(RuntimeError, "offline"):
                serve._compact_summarize("transcript", state)
            fallback.assert_not_called()

    def test_delegation_inherits_same_project_only(self):
        state = SimpleNamespace(run_id="parent", project_root="/fixture/a", prototype="atlas",
                                guards={"dsGuard": False, "visual": False, "reqQa": True})
        with patch.dict(serve.RUNS, {"parent": state}, clear=True):
            inherited = serve._delegated_context("/fixture/a", {"parent": "parent"}, {})
            self.assertEqual(inherited["prototype"], "atlas")
            self.assertFalse(inherited["guards"]["dsGuard"])
            other = serve._delegated_context("/fixture/b", {"parent": "parent"}, {})
            self.assertIsNone(other["parent"])
            self.assertIsNone(other["prototype"])

    def test_planner_profiles(self):
        self.assertEqual(policy.planner_tier("art-director-orchestrator"), "setup")
        self.assertEqual(policy.planner_tier("craft-lens"), "leaf")
        self.assertEqual(policy.planner_tier("s3d-subsystem-author"), "leaf")

    def test_planner_launch_uses_leaf_checks_and_subagent_model(self):
        handler = SimpleNamespace(
            _read_json_body=lambda **kwargs: {"type": "craft-lens", "brief": "Check atlas", "parent": "parent"},
            _reply=lambda status, body: (status, body))
        parent = SimpleNamespace(run_id="parent", project_root="/fixture", prototype="atlas",
                                 guards={"dsGuard": False, "visual": False})
        with patch.dict(serve.RUNS, {"parent": parent}, clear=True), \
             patch.object(serve, "resolve_project_root", return_value="/fixture"), \
             patch.object(serve, "detect_agent_bin", side_effect=lambda name: "/mock/codex" if name == "codex" else None), \
             patch.object(serve, "_agent_default_runtime", return_value="codex"), \
             patch.object(serve, "_subagent_override_model_for_node", return_value="gpt-5.6-luna"), \
             patch.object(serve, "_codex_mcp_spawn_args", return_value=[]), \
             patch.object(serve, "_mcp_servers_from_config", return_value={}), \
             patch.object(serve, "_build_child_env", return_value={}), \
             patch.object(caps, "capabilities_preamble", return_value="CAPS") as preamble, \
             patch.object(serve.subprocess, "Popen", side_effect=RuntimeError("captured, no spawn")) as spawn:
            status, _ = serve.H._dispatch_planner(handler, {})
            self.assertEqual(status, 500)
            self.assertEqual(preamble.call_args.kwargs["tier"], "leaf")
            self.assertEqual(preamble.call_args.kwargs["prototype"], "atlas")
            self.assertFalse(preamble.call_args.kwargs["guards"]["dsGuard"])
            self.assertIn("gpt-5.6-luna", spawn.call_args.args[0])
            self.assertEqual(spawn.call_args.kwargs["env"]["TH_VISUAL_GUARD"], "0")

    def test_handoff_cache_and_late_messages(self):
        events = [event(0, "user_message", text="Approved copper. Only atlas.")]
        state = SimpleNamespace(events=events, lock=threading.Lock(), run_id="fixture", is_live=False,
                                branch="atlas", prototype="atlas", tier="scoped", model="chosen",
                                guards={"dsGuard": False}, agent_id="codex", title="Atlas")
        state.append = lambda kind, data: events.append({"seq": len(events), "type": kind, "data": data})
        handler = SimpleNamespace(_read_json_body=lambda: {}, _reply=lambda code, body: (code, body))
        with patch.dict(serve.RUNS, {"fixture": state}, clear=True), \
             patch.object(serve, "_compact_summarize", return_value="Working state") as summary:
            for _ in range(2):
                code, result = serve.H._run_handoff(handler, "fixture", {})
                self.assertEqual(code, 200)
                self.assertEqual(result["context"]["prototype"], "atlas")
            self.assertEqual(summary.call_count, 1)
            state.append("user_message", {"text": "Use serif type"})
            def summarize(*args):
                state.append("user_message", {"text": "Also keep reduced motion"})
                return "New working state"
            summary.side_effect = summarize
            _, result = serve.H._run_handoff(handler, "fixture", {})
            self.assertIn("Also keep reduced motion", result["summary"])
            self.assertEqual(summary.call_count, 2)

    def test_planner_rehydrate_retains_profile_and_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "editor").mkdir()
            record = {"runId": "fixture-rehydrate", "branch": "planner", "agentId": "codex",
                      "kind": "planner:craft-lens", "title": "Craft", "startedAt": 1000,
                      "seq": 0, "type": "status", "data": {"label": "planner-dispatched",
                      "tier": "leaf", "prototype": "atlas", "guards": {"dsGuard": False},
                      "model": "gpt-5.6-luna"}}
            (Path(tmp) / "editor" / "chat.jsonl").write_text(json.dumps(record) + "\n")
            with patch.dict(serve.RUNS, {}, clear=True):
                state = serve._rehydrate_run_from_jsonl("fixture-rehydrate", tmp)
                self.assertEqual(state.tier, "leaf")
                self.assertEqual(state.prototype, "atlas")
                self.assertFalse(state.guards["dsGuard"])
                self.assertEqual(state.model, "gpt-5.6-luna")

    def test_summary_inherit_and_fast_defaults(self):
        self.assertEqual(policy.summary_model("claude"), "claude-haiku-4-5")
        self.assertEqual(policy.summary_model("codex", "inherit", "gpt-5.6-sol"), "gpt-5.6-sol")

    def test_claude_summary_has_no_tools_and_haiku_has_no_effort_flag(self):
        with patch.object(serve, "detect_agent_bin", return_value="/mock/claude"), \
             patch.object(serve, "_guest_cli_env", return_value={}), \
             patch.object(serve.subprocess, "run", return_value=SimpleNamespace(
                 returncode=0, stdout="state", stderr="")) as run:
            serve._assistant_agent_complete("summary", "transcript", model="claude-haiku-4-5",
                                            tools="none", reasoning="low")
            args = run.call_args.args[0]
            self.assertEqual(args[args.index("--tools") + 1], "")
            self.assertIn("--strict-mcp-config", args)
            self.assertIn("--system-prompt", args)
            self.assertNotIn("--append-system-prompt", args)
            self.assertEqual(args[args.index("--setting-sources") + 1], "")
            self.assertNotIn("--effort", args)

    def test_invalid_summary_does_not_replace_history(self):
        with patch.object(serve, "_compact_config", return_value={"summaryModel": "fast"}), \
             patch.object(serve, "_assistant_agent_complete", return_value="<function_calls>Read</function_calls>"):
            with self.assertRaisesRegex(RuntimeError, "original conversation retained"):
                serve._compact_summarize("USER: Preserve 3D", SimpleNamespace(agent_id="claude", model=None))

    def test_summary_does_not_promote_reported_checks_to_verification(self):
        with patch.object(serve, "_compact_config", return_value={"summaryModel": "fast"}), \
             patch.object(serve, "_assistant_agent_complete", return_value="**Verified state:**\nNav passes, per assistant."):
            result = serve._compact_summarize("ASSISTANT: Nav passes", SimpleNamespace(agent_id="claude", model=None))
            self.assertEqual(result, "**Reported state:**\nNav passes, per assistant.")

    def test_codex_summary_low_effort_and_cli_default(self):
        with patch.object(serve, "_codex_cli_complete", return_value="state") as complete:
            serve._assistant_agent_complete("summary", "transcript", model="codex-default",
                                            tools="none", reasoning="low")
            self.assertIsNone(complete.call_args.kwargs["model"])
            self.assertIn('model_reasoning_effort="low"', complete.call_args.kwargs["extra_args"])
            self.assertIn("--skip-git-repo-check", complete.call_args.kwargs["extra_args"])
            self.assertIn("--ephemeral", complete.call_args.kwargs["extra_args"])

    def test_ds_full_embed_is_toggle_controlled_in_every_tier(self):
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(caps, "_live_provider_availability", return_value=[]), \
             patch.object(serve, "_default_providers_get", return_value={}), \
             patch.object(serve, "_orchestrator_models_get", return_value={}), \
             patch.object(serve, "_subagent_models_get", return_value={}):
            ds = Path(tmp) / "design-systems" / "fixture"
            ds.mkdir(parents=True)
            catalog = "CATALOG_START\n" + "Usage rule.\n" * 4000 + "CATALOG_END"
            (ds / "DESIGN.md").write_text(catalog)
            (ds / "styles.css").write_text(":root { --ink: #111; }")
            for tier in ("setup", "normal", "scoped", "leaf", "full", "slim"):
                with self.subTest(tier=tier):
                    on = caps.capabilities_preamble(tmp, tier=tier, prototype="atlas", guards={"dsGuard": True})
                    off = caps.capabilities_preamble(tmp, tier=tier, prototype="atlas", guards={"dsGuard": False})
                    self.assertEqual(on.count(catalog), 1)
                    self.assertNotIn("CATALOG_START", off)
                    self.assertIn("Description and handoff discipline", off)
            normal = caps.capabilities_preamble(tmp, tier="normal", guards={"dsGuard": False})
            setup = caps.capabilities_preamble(tmp, tier="setup", guards={"dsGuard": False})
            self.assertLess(len(normal), len(setup) / 2)


if __name__ == "__main__":
    unittest.main()

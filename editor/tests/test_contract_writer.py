"""Writer routing, review boundaries, fidelity, and all-orchestrator coverage."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import contract_writer as writer
import context_artifacts as artifacts
import serve
from test_context_artifacts import draft as art_draft, handler


class ContractWriterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = {**serve.COMPACT_DEFAULTS, "contractWriterOverrides": {}}
        self.body = {"orchestrator": "simulation-orchestrator",
                     "draft": {"description": "Soft paper. Paper stays matte. Never glossy. Settle in 200ms.",
                               "constraints": ["No scoring"], "palette": {"hex": "#92806a"},
                               "approvedExceptions": "Allow neon only in the chart."},
                     "outputPath": "workflow/simulation-contract.json", "prosePaths": ["/description"]}
        self.response = json.dumps({"edits": [{"path": "/description", "text": "Matte soft paper, never glossy; settle in 200ms."}]})

    def call(self, action, body, complete=None, runtime="codex"):
        with patch.object(serve, "resolve_project_root", return_value=str(self.root)), \
             patch.object(serve, "_compact_config", return_value=self.config), \
             patch.object(serve, "_agent_default_runtime", return_value=runtime), \
             patch.object(serve, "_agent_default_model", return_value="gpt-6-astra"), \
             patch.object(serve, "_orch_override_model_for_node", return_value=""), \
             patch.object(serve, "_subagent_override_model_for_node", return_value=""), \
             patch.object(serve, "_assistant_agent_complete", side_effect=complete or (lambda *a, **kw: self.response)):
            return serve.H._context_writer(handler(body), "/__context/writer/" + action, {"project": ["fixture"]})

    def test_global_per_orchestrator_and_inherit_models_are_independent(self):
        for runtime, expected in (("codex", "gpt-5.6-luna"), ("claude", "claude-haiku-4-5")):
            calls = []
            code, result = self.call("prepare", self.body, lambda *a, **kw: calls.append(kw) or self.response, runtime)
            self.assertEqual(code, 200)
            self.assertEqual(result["model"], expected)
            self.assertEqual(calls[0]["tools"], "none")
            self.assertEqual(calls[0]["reasoning"], "low")
        self.config["contractWriterModel"] = "claude-sonnet-4-6"
        self.config["contractWriterOverrides"] = {"simulation-orchestrator": "gpt-5.6-terra"}
        self.assertEqual(self.call("prepare", self.body)[1]["model"], "gpt-5.6-terra")
        other = {**self.body, "orchestrator": "art-director-orchestrator"}
        self.assertEqual(self.call("prepare", other)[1]["model"], "claude-sonnet-4-6")
        self.config["contractWriterOverrides"]["simulation-orchestrator"] = "inherit"
        self.assertEqual(self.call("prepare", self.body)[1]["model"], "gpt-6-astra")

    def test_review_required_and_only_accepted_prose_changes(self):
        code, receipt = self.call("prepare", self.body)
        self.assertEqual(code, 200)
        output = self.root / self.body["outputPath"]
        self.assertFalse(output.exists())
        self.assertTrue((self.root / receipt["decisionsPath"]).is_file())
        self.assertEqual(self.call("publish", receipt)[0], 400)
        self.assertEqual(self.call("publish", {**receipt, "acceptedPaths": ["/palette"]})[0], 400)
        code, result = self.call("publish", {**receipt, "acceptedPaths": ["/description"]})
        self.assertEqual(code, 200)
        actual = json.loads(output.read_text())
        for key in ("constraints", "palette", "approvedExceptions"):
            self.assertEqual(actual[key], self.body["draft"][key])
        self.assertEqual(actual["description"], "Matte soft paper, never glossy; settle in 200ms.")
        self.assertEqual(result["sha256"], artifacts.digest(actual))

    def test_rejected_edits_keep_original_and_repeated_prepare_reuses_review(self):
        _, receipt = self.call("prepare", self.body)
        def forbidden(*a, **kw):
            self.fail("identical prepare must reuse the saved writer review")
        self.assertTrue(self.call("prepare", self.body, forbidden)[1]["reused"])
        self.assertEqual(self.call("publish", {**receipt, "acceptedPaths": []})[0], 200)
        self.assertEqual(json.loads((self.root / self.body["outputPath"]).read_text()), self.body["draft"])

    def test_invalid_changes_and_failed_model_keep_decisions_without_publishing(self):
        for changed in ({"path": "/palette/hex", "text": "#ffffff"},
                        {"path": "/description", "text": "Matte paper."},
                        {"path": "/description", "text": ""}):
            response = json.dumps({"edits": [changed]})
            self.assertEqual(self.call("prepare", self.body, lambda *a, **kw: response)[0], 400)
        def failed(*a, **kw):
            raise RuntimeError("offline")
        self.assertEqual(self.call("prepare", self.body, failed)[0], 502)
        self.assertFalse((self.root / self.body["outputPath"]).exists())
        self.assertTrue(list(self.root.glob("workflow/writing/*/decisions.json")))
        protected = {**self.body, "prosePaths": ["/approvedExceptions"]}
        self.assertEqual(self.call("prepare", protected)[0], 400)

    def test_saved_source_review_and_output_revisions_are_checked(self):
        source = self.root / "decisions.json"
        source.write_text(json.dumps(self.body["draft"]))
        body = {**self.body, "draftPath": "decisions.json"}
        _, receipt = self.call("prepare", body)
        self.assertEqual(self.call("publish", {**receipt, "reviewHash": "stale", "acceptedPaths": []})[0], 400)
        source.write_text(json.dumps({**self.body["draft"], "constraints": ["New constraint"]}))
        self.assertEqual(self.call("publish", {**receipt, "acceptedPaths": []})[0], 400)
        source.write_text(json.dumps(self.body["draft"]))
        output = self.root / self.body["outputPath"]
        output.write_text('{"newer":"decision"}')
        self.assertEqual(self.call("publish", {**receipt, "acceptedPaths": []})[0], 409)
        self.assertEqual(json.loads(output.read_text()), {"newer": "decision"})

    def test_text_briefs_and_json_pointer_array_fields(self):
        body = {**self.body, "format": "text", "draft": self.body["draft"]["description"],
                "outputPath": "workflow/brief.md", "prosePaths": ["/text"]}
        response = self.response.replace('/description', '/text')
        _, receipt = self.call("prepare", body, lambda *a, **kw: response)
        self.assertEqual(self.call("publish", {**receipt, "acceptedPaths": ["/text"]})[0], 200)
        self.assertEqual((self.root / body["outputPath"]).read_text(), "Matte soft paper, never glossy; settle in 200ms.")
        original = {"workers": [{"brief": "Some long brief"}]}
        self.assertEqual(writer.descriptions(original, ["/workers/0/brief"]), {"/workers/0/brief": "Some long brief"})
        actual = writer.apply_review(original, [{"path": "/workers/0/brief", "before": "Some long brief", "text": "Brief"}], ["/workers/0/brief"])
        self.assertEqual(actual["workers"][0]["brief"], "Brief")

    def test_project_paths_and_foreign_parent_are_rejected(self):
        self.assertEqual(self.call("prepare", {**self.body, "outputPath": "../elsewhere.json"})[0], 400)
        self.assertEqual(self.call("prepare", {**self.body, "draftPath": "../elsewhere.json"})[0], 400)
        parent = SimpleNamespace(project_root="/unrelated/project")
        with patch.dict(serve.RUNS, {"foreign": parent}):
            self.assertEqual(self.call("prepare", {**self.body, "parent": "foreign"})[0], 400)

    def test_art_direction_uses_same_writer_and_existing_contract_validation(self):
        original = art_draft()
        body = {"orchestrator": "art-director-orchestrator", "draft": original,
                "outputPath": "workflow/art-direction-contract.json", "prosePaths": ["/voice/audience"]}
        _, receipt = self.call("prepare", body, lambda *a, **kw: '{"edits":[]}')
        self.assertEqual(self.call("publish", {**receipt, "acceptedPaths": []})[0], 400)
        plate = self.root / original["platePath"]; plate.parent.mkdir(exist_ok=True); plate.write_bytes(b"fixture")
        self.assertEqual(self.call("publish", {**receipt, "acceptedPaths": []})[0], 200)
        result = json.loads((self.root / body["outputPath"]).read_text())
        self.assertIn("bindingRules", result)
        self.assertEqual(result["approvedExceptions"], original["approvedExceptions"])

    def test_settings_patch_and_clear_override_preserve_other_choices(self):
        self.assertTrue(writer.valid_model("o3"))
        self.assertTrue(writer.valid_model("o4-mini"))
        with patch.object(serve, "COMPACT_CONFIG_PATH", str(self.root / "settings.json")):
            def save(body):
                return serve.H._compact_config_set(handler(body))
            self.assertEqual(save({"contractWriterModel": "gpt-5.6-luna"})[0], 200)
            save({"contractWriterOverrides": {"simulation-orchestrator": "inherit"}})
            save({"contractWriterOverrides": {"art-director-orchestrator": "claude-haiku-4-5"}})
            save({"contractWriterOverrides": {"simulation-orchestrator": None}})
            self.assertEqual(serve._compact_config()["contractWriterOverrides"], {"art-director-orchestrator": "claude-haiku-4-5"})
            self.assertEqual(serve._compact_config()["contractWriterModel"], "gpt-5.6-luna")
            for body in ({"contractWriterModel": "--bad-flag"}, {"contractWriterOverrides": {"../bad": "fast"}},
                         {"contractWriterOverrides": {"simulation-orchestrator": 9}}):
                self.assertEqual(save(body)[0], 400)

    def test_all_orchestrators_and_codex_mirrors_use_shared_writer(self):
        root = Path(serve.INSTALL_ROOT)
        spec = importlib.util.spec_from_file_location("writer_agent_sync", root / "scripts/sync-codex-agents.py")
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        playbooks = list((root / ".claude/agents").glob("*-orchestrator.md"))
        self.assertGreater(len(playbooks), 0)
        for path in playbooks:
            self.assertIn("docs/agents/contract-writer.md", path.read_text())
            self.assertEqual((root / ".codex/agents" / (path.stem + ".toml")).read_text(), module.render_toml(*module.parse_md(path)))


if __name__ == "__main__":
    unittest.main()

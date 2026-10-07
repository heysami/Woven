"""Agent catalog deduplication. No model calls or user configuration changes."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agent_catalog import plugin_spawn_args


class AgentCatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.plugin = self.root / "plugin"
        (self.plugin / ".claude-plugin").mkdir(parents=True)
        (self.plugin / ".claude-plugin/plugin.json").write_text(
            json.dumps({"name": "woven", "version": "1.0.0"}))
        self.agents = self.root / ".claude/agents"
        self.agents.mkdir(parents=True)
        (self.plugin / "agents").symlink_to(self.agents, target_is_directory=True)

    def agent(self, filename, name, description="Draw one asset."):
        path = self.agents / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"---\nname: {name}\ndescription: {description}\ntools: Read\n---\nKeep the full playbook.\n")
        return path

    def test_filters_only_bare_plugin_aliases_and_preserves_playbooks(self):
        path = self.agent("worker.md", "worker")
        before = path.read_bytes()
        unrelated = self.root / "user-agent.md"
        unrelated.write_text("---\nname: personal-agent\ndescription: Custom\n---\n")
        self.assertEqual(plugin_spawn_args(self.plugin), [
            "--plugin-dir", str(self.plugin), "--disallowedTools=Agent(worker)"])
        self.assertEqual(path.read_bytes(), before)

    def test_uses_declared_names_and_includes_nested_long_definitions(self):
        self.agent("different-filename.md", "'alpha'")
        self.agent("nested/beta.md", '"beta"', "Long description. " * 300)
        self.agent("duplicate.md", "alpha")
        self.assertEqual(plugin_spawn_args(self.plugin)[-1],
                         "--disallowedTools=Agent(alpha),Agent(beta)")

    def test_skips_docs_malformed_and_rule_syntax(self):
        (self.agents / "ORCHESTRATORS.md").write_text("# Documentation\nname: not-an-agent\n")
        (self.agents / "missing-description.md").write_text("---\nname: incomplete\n---\n")
        self.agent("namespace.md", "woven:worker")
        self.agent("injection.md", "worker),Agent(*)")
        self.assertEqual(plugin_spawn_args(self.plugin), ["--plugin-dir", str(self.plugin)])

    def test_missing_plugin_never_denies_bare_agents(self):
        self.assertEqual(plugin_spawn_args(None), [])
        self.assertEqual(plugin_spawn_args(self.root / "missing"), [])

    def test_invalid_manifest_does_not_hide_fallback_agents(self):
        self.agent("worker.md", "worker")
        path = self.plugin / ".claude-plugin/plugin.json"
        for body in ["broken", "[]", "{}"]:
            with self.subTest(body=body):
                path.write_text(body)
                self.assertEqual(plugin_spawn_args(self.plugin), ["--plugin-dir", str(self.plugin)])

    def test_missing_agents_directory(self):
        (self.plugin / "agents").unlink()
        self.assertEqual(plugin_spawn_args(self.plugin), ["--plugin-dir", str(self.plugin)])


if __name__ == "__main__":
    unittest.main()

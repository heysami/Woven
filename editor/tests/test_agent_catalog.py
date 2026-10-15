"""Agent catalog deduplication. No model calls or user configuration changes."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agent_catalog import declared_model, model_settings, plugin_spawn_args, with_models


class PluginFixture(unittest.TestCase):
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


class AgentCatalogTests(PluginFixture):
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


class WovenModelTests(PluginFixture):
    """`woven-model:` resolved into a derived plugin copy carrying `model:`."""

    def checker(self, model_line="woven-model: fast\n"):
        path = self.agents / "checker.md"
        path.write_text("---\nname: checker\ndescription: Check.\ntools: Read\n" + model_line + "---\nPlaybook.\n")
        return path

    def test_declared_model_reads_only_frontmatter(self):
        self.assertEqual(declared_model("---\nname: a\nwoven-model: 'fast'\n---\nbody"), "fast")
        self.assertEqual(declared_model("---\nname: a\n---\nwoven-model: fast\n"), "")
        self.assertEqual(declared_model(None), "")

    def test_model_settings_lists_declaring_agents(self):
        self.checker()
        self.agent("worker.md", "worker")
        self.assertEqual(model_settings(self.plugin), {"checker.md": "fast"})
        self.assertEqual(model_settings(None), {})

    def test_with_models_copies_only_listed_agents(self):
        source = self.checker("woven-model: fast\nmodel: opus\n")
        worker = self.agent("nested/worker.md", "worker")
        cache = self.root / "cache"
        derived = Path(with_models(self.plugin, {"checker.md": "claude-haiku-4-5"}, cache))
        self.assertEqual(derived.parent, cache)
        copy = (derived / "agents/checker.md").read_text()
        self.assertTrue(copy.startswith("---\nname: checker\n"))
        self.assertIn("\nmodel: claude-haiku-4-5\n---\nPlaybook.\n", copy)
        self.assertNotIn("model: opus", copy)
        self.assertEqual(source.read_text().count("model: opus"), 1)
        self.assertEqual(os.readlink(derived / "agents/nested/worker.md"), str(worker.resolve()))
        self.assertEqual(plugin_spawn_args(derived), [
            "--plugin-dir", str(derived), "--disallowedTools=Agent(checker),Agent(worker)"])

    def test_with_models_resyncs_edits_and_removed_agents(self):
        source = self.checker()
        gone = self.agent("gone.md", "gone")
        derived = Path(with_models(self.plugin, {"checker.md": "m1"}, self.root / "cache"))
        source.write_text(source.read_text().replace("Playbook.", "Edited."))
        gone.unlink()
        again = Path(with_models(self.plugin, {"checker.md": "m1"}, self.root / "cache"))
        self.assertEqual(again, derived)
        self.assertIn("Edited.", (derived / "agents/checker.md").read_text())
        self.assertFalse((derived / "agents/gone.md").exists())
        other = with_models(self.plugin, {"checker.md": "m2"}, self.root / "cache")
        self.assertNotEqual(other, str(derived))

    def test_no_models_or_unwritable_cache_keeps_the_plugin(self):
        self.checker()
        self.assertEqual(with_models(self.plugin, {}, self.root / "cache"), self.plugin)
        blocker = self.root / "blocked"
        blocker.write_text("a file, not a directory")
        self.assertEqual(with_models(self.plugin, {"checker.md": "m"}, blocker), self.plugin)


if __name__ == "__main__":
    unittest.main()

"""opencode spawn flags and managed config. No CLI or model calls."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import serve


class OpencodeAutoTests(unittest.TestCase):
    def spawned_argv(self, argv, supports=True, mode=None):
        with patch.object(serve, "_mcp_servers_from_config", return_value={}), \
             patch.object(serve, "_opencode_run_supports_auto", return_value=supports), \
             patch.object(serve.subprocess, "Popen") as popen, \
             patch.object(serve, "_compact_config", return_value={"runtimeDrivers": {}}):
            serve._spawn_runtime_process("opencode", list(argv), driver_mode=mode, env={})
        return popen.call_args.args[0]

    def test_run_spawns_get_auto_right_after_run(self):
        argv = self.spawned_argv(["/bin/opencode", "run", "--format", "json", "--model", "a/b", "hi"])
        self.assertEqual(argv[:3], ["/bin/opencode", "run", "--auto"])
        self.assertEqual(argv[-1], "hi")

    def test_not_added_when_the_cli_lacks_it(self):
        argv = self.spawned_argv(["/bin/opencode", "run", "--format", "json", "hi"], supports=False)
        self.assertNotIn("--auto", argv)

    def test_never_duplicated(self):
        argv = self.spawned_argv(["/bin/opencode", "run", "--auto", "--format", "json", "hi"])
        self.assertEqual(argv.count("--auto"), 1)

    def test_probe_reads_the_help_text(self):
        help_text = ("      --interactive  run in direct mode\n"
                     "      --auto         auto-approve permissions that are not explicitly denied\n")
        done = type("R", (), {"stdout": help_text, "stderr": "", "returncode": 0})()
        with patch.object(serve.subprocess, "run", return_value=done), \
             patch.dict(serve._OPENCODE_AUTO_PROBE, {}, clear=True):
            self.assertTrue(serve._opencode_run_supports_auto("/fake/oc-new"))
        done.stdout = "      --autoload  something else\n"
        with patch.object(serve.subprocess, "run", return_value=done), \
             patch.dict(serve._OPENCODE_AUTO_PROBE, {}, clear=True):
            self.assertFalse(serve._opencode_run_supports_auto("/fake/oc-old"))


class OpencodeAnthropicCacheTests(unittest.TestCase):
    def test_each_listed_model_gets_the_1h_cache_option(self):
        cfg = {"mcp": {}}
        serve._opencode_apply_anthropic_cache(cfg, ["claude-opus-5-5", "claude-haiku-4-5"])
        models = cfg["provider"]["anthropic"]["models"]
        self.assertEqual(set(models), {"claude-opus-5-5", "claude-haiku-4-5"})
        for entry in models.values():
            self.assertEqual(entry["options"]["cacheControl"], {"type": "ephemeral", "ttl": "1h"})
        self.assertNotIn("options", cfg["provider"]["anthropic"])   # provider-wide never reaches requests

    def test_user_settings_survive(self):
        cfg = {"provider": {
            "anthropic": {"options": {"baseURL": "https://gw/v1"},
                          "models": {"claude-opus-5-5": {"name": "Mine", "options": {
                              "cacheControl": {"type": "ephemeral", "ttl": "5m"}, "effort": "high"}}}},
            "zai": {"options": {"apiKey": "k"}}}}
        serve._opencode_apply_anthropic_cache(cfg, ["claude-opus-5-5", "claude-sonnet-5-5"])
        prov = cfg["provider"]
        mine = prov["anthropic"]["models"]["claude-opus-5-5"]
        self.assertEqual(mine["options"]["cacheControl"]["ttl"], "5m")      # the user's choice wins
        self.assertEqual((mine["name"], mine["options"]["effort"]), ("Mine", "high"))
        self.assertEqual(prov["anthropic"]["models"]["claude-sonnet-5-5"]["options"]["cacheControl"]["ttl"], "1h")
        self.assertEqual(prov["anthropic"]["options"], {"baseURL": "https://gw/v1"})
        self.assertEqual(prov["zai"], {"options": {"apiKey": "k"}})

    def test_no_anthropic_provider_means_no_entries(self):
        cfg = {"mcp": {}}
        serve._opencode_apply_anthropic_cache(cfg, [])
        self.assertNotIn("provider", cfg)

    def test_model_list_parses_the_cli_output(self):
        out = "\x1b[1manthropic/claude-opus-5-5\x1b[0m\nanthropic/claude-haiku-4-5-20251001\nnoise line\n"
        done = type("R", (), {"stdout": out, "stderr": "", "returncode": 0})()
        with patch.object(serve, "detect_agent_bin", return_value="/fake/opencode"), \
             patch.object(serve.subprocess, "run", return_value=done), \
             patch.dict(serve._OPENCODE_ANTHROPIC_MODELS, {}, clear=True):
            self.assertEqual(serve._opencode_anthropic_models(),
                             ["claude-opus-5-5", "claude-haiku-4-5-20251001"])
        failed = type("R", (), {"stdout": "", "stderr": "Provider not found: anthropic", "returncode": 1})()
        with patch.object(serve, "detect_agent_bin", return_value="/fake/opencode2"), \
             patch.object(serve.subprocess, "run", return_value=failed), \
             patch.dict(serve._OPENCODE_ANTHROPIC_MODELS, {}, clear=True):
            self.assertEqual(serve._opencode_anthropic_models(), [])


if __name__ == "__main__":
    unittest.main()

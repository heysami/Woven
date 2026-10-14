"""Per-thread typed judgment: a chat can turn the text or the image judge on or
off for itself (guards judgeText / judgeImage), and every place that applies
the global switch applies the thread's choice instead. Absent = follow
Settings, so callers that pass nothing behave as before."""
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

EDITOR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EDITOR))
import serve
import typed_judge
from kinds import capabilities as caps


class _Configured:
    """Settings + a Cloudflare key in throwaway config files; no network."""

    def __init__(self, compact):
        self.compact = compact

    def __enter__(self):
        self.saved = (typed_judge.MEDIA_CONFIG_PATH, typed_judge.COMPACT_CONFIG_PATH)
        self.env = {k: os.environ.pop(k) for k in list(typed_judge.ENV_KEYS.values())
                    + list(typed_judge.ENDPOINT_ENV.values()) + ["TH_JUDGE_TEXT", "TH_JUDGE_IMAGE"]
                    if k in os.environ}
        self.tmp = tempfile.TemporaryDirectory()
        typed_judge.MEDIA_CONFIG_PATH = os.path.join(self.tmp.name, "m.json")
        typed_judge.COMPACT_CONFIG_PATH = os.path.join(self.tmp.name, "c.json")
        Path(typed_judge.MEDIA_CONFIG_PATH).write_text(
            json.dumps({"cloudflare": {"api_key": "cf", "account_id": "a"}}))
        Path(typed_judge.COMPACT_CONFIG_PATH).write_text(json.dumps(self.compact))
        return self

    def __exit__(self, *exc):
        typed_judge.MEDIA_CONFIG_PATH, typed_judge.COMPACT_CONFIG_PATH = self.saved
        os.environ.update(self.env)
        self.tmp.cleanup()


class ThreadJudgeTests(unittest.TestCase):
    def test_absent_follows_settings(self):
        g = caps.normalize_guards({"visual": False})
        self.assertIsNone(g["judgeText"])
        self.assertIsNone(g["judgeImage"])
        g = caps.normalize_guards({"judgeText": False, "judgeImage": "yes"})
        self.assertIs(g["judgeText"], False)
        self.assertIsNone(g["judgeImage"])
        self.assertIsNone(serve._normalize_chat_guards(None)["judgeText"])

    def test_preamble_block_follows_the_thread(self):
        with _Configured({"jevJudge": False, "typedJudgeVisual": False}):
            self.assertIsNone(caps._typed_judgment_state())
            self.assertEqual(caps._typed_judgment_state({"text": True, "image": None}),
                             {"text": "Cloudflare Clef Flash", "image": None})
        with _Configured({"jevJudge": True, "typedJudgeVisual": True}):
            self.assertIsNone(caps._typed_judgment_state({"text": False, "image": False}))
            self.assertEqual(caps._typed_judgment_state({"text": False, "image": None}),
                             {"text": None, "image": "Cloudflare Clef"})
            with tempfile.TemporaryDirectory() as tmp:
                off = caps.capabilities_preamble(tmp, tier="normal",
                                                 guards={"judgeText": False, "judgeImage": False})
                on = caps.capabilities_preamble(tmp, tier="normal", guards={})
            self.assertNotIn("Typed judgment is available", off)
            self.assertIn("Typed judgment is available", on)
            self.assertIn("run=$TH_RUN_ID", on)

    def test_endpoints_apply_the_calling_thread(self):
        state = SimpleNamespace(guards={"judgeText": False, "judgeImage": True}, lock=threading.Lock())
        with patch.object(serve, "_compact_config",
                          return_value={"jevJudge": True, "typedJudgeVisual": False}), \
             patch.dict(serve.RUNS, {"r1": state}, clear=True):
            cfg = serve._judge_config({"run": ["r1"]})
            self.assertFalse(cfg["jevJudge"])
            self.assertTrue(cfg["typedJudgeVisual"])
            self.assertTrue(serve._judge_config(None, "r1")["typedJudgeVisual"])
            # No run named, or one the daemon does not know: Settings.
            self.assertTrue(serve._judge_config({})["jevJudge"])
            self.assertTrue(serve._judge_config({"run": ["gone"]})["jevJudge"])

    def test_agent_env_carries_only_an_explicit_choice(self):
        env = serve._apply_guard_env({"TH_JUDGE_IMAGE": "1"}, {"judgeText": False, "judgeImage": None})
        self.assertEqual(env.get("TH_JUDGE_TEXT"), "0")
        self.assertNotIn("TH_JUDGE_IMAGE", env)
        with _Configured({"jevJudge": True}):
            self.assertTrue(typed_judge.enabled("text"))
            with patch.dict(os.environ, {"TH_JUDGE_TEXT": "0", "TH_JUDGE_IMAGE": "1"}):
                self.assertFalse(typed_judge.enabled("text"))
                self.assertTrue(typed_judge.enabled("image"))

    def test_children_inherit_the_choice(self):
        parent = SimpleNamespace(run_id="p", project_root="/fixture/a", prototype="main",
                                 guards={"judgeText": False, "judgeImage": True}, lock=threading.Lock())
        with patch.dict(serve.RUNS, {"p": parent}, clear=True):
            child = serve._delegated_context("/fixture/a", {"parent": "p"}, {})["guards"]
        self.assertIs(child["judgeText"], False)
        self.assertIs(child["judgeImage"], True)


if __name__ == "__main__":
    unittest.main()

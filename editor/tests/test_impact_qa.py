"""Impact QA: the opt-in check that looks for OTHER screens and flows a change
broke (docs/agents/impact-qa.md). Off by default, rides only the interactive
tiers, never inherited by a child run its parent waits on, and never fixes
anything without asking the user."""
from pathlib import Path
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

EDITOR = Path(__file__).resolve().parents[1]
REPO = EDITOR.parent
sys.path.insert(0, str(EDITOR))
import run_jobs
import serve
from kinds import capabilities as caps

HEADER = "### IMPACT QA - mandatory gate"


class ImpactQaTests(unittest.TestCase):
    def test_off_unless_asked(self):
        self.assertFalse(caps.normalize_guards(None)["impactQa"])
        self.assertFalse(caps.normalize_guards({"visual": False})["impactQa"])
        self.assertTrue(caps.normalize_guards({"impactQa": True})["impactQa"])
        self.assertFalse(serve._normalize_chat_guards(None)["impactQa"])

    def test_rides_the_interactive_tiers_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            for tier in ("normal", "scoped", "setup"):
                on = caps.capabilities_preamble(tmp, tier=tier, prototype="main", guards={"impactQa": True})
                off = caps.capabilities_preamble(tmp, tier=tier, prototype="main", guards={"impactQa": False})
                self.assertEqual(on.count(HEADER), 1, tier)
                self.assertNotIn(HEADER, off, tier)
            leaf = caps.capabilities_preamble(tmp, tier="leaf", guards={"impactQa": True})
            self.assertNotIn(HEADER, leaf)

    def test_stub_asks_before_any_fix(self):
        stub = caps.IMPACT_QA_STUB
        self.assertIn("docs/agents/impact-qa.md", stub)
        self.assertIn("Never apply an impact fix on your own", stub)
        self.assertIn('multiSelect="true"', stub)
        self.assertIn('id="impact-qa"', stub)
        self.assertNotIn("—", stub)
        self.assertNotIn("–", stub)
        spec = (REPO / "docs" / "agents" / "impact-qa.md").read_text()
        self.assertIn("You do NOT edit anything", spec)
        self.assertIn("IMPACT-QA <CLEAN|FINDINGS|SKIPPED>", spec)
        self.assertNotIn("—", spec)
        self.assertNotIn("–", spec)

    def test_children_the_parent_waits_on_do_not_inherit_it(self):
        parent = SimpleNamespace(run_id="parent", project_root="/fixture/a", prototype="main",
                                 guards={"visual": True, "dsGuard": True, "reqQa": True, "impactQa": True},
                                 lock=threading.Lock())
        with patch.dict(serve.RUNS, {"parent": parent}, clear=True):
            child = serve._delegated_context("/fixture/a", {"parent": "parent"}, {})["guards"]
        self.assertFalse(child["impactQa"])
        self.assertTrue(child["reqQa"])
        # A plan-split thread is a thread the user works in: it keeps the check.
        self.assertTrue(serve._delegated_guards(parent.guards)["impactQa"])

    def test_dispatch_counts_as_a_qa_check(self):
        event = {"type": "tool_use", "id": "call", "name": "Agent",
                 "input": {"subagent_type": "general-purpose",
                           "prompt": "Read /x/docs/agents/impact-qa.md and execute it."}}
        self.assertEqual(run_jobs.observe({}, event, "claude")["qaCheck"], "impact QA")


if __name__ == "__main__":
    unittest.main()

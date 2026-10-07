"""The normal-tier build thread must carry the synchronous-dispatch rule.

Regression for the medival build (2026-09-18): since build threads stopped
flipping to the setup tier, the normal preamble was their only drive
contract, and it never said orchestrators run inside the turn. The thread
backgrounded every orchestrator and ended its turn, so the chat read as the
build stopping for 15-30 minutes at a time.

Run: python3 -m unittest discover -s editor/tests -p test_normal_tier_drive.py -v
"""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kinds import capabilities as caps


class NormalTierDriveTests(unittest.TestCase):
    def test_normal_tier_says_orchestrators_run_synchronously(self):
        with tempfile.TemporaryDirectory() as tmp:
            normal = caps.capabilities_preamble(tmp, tier="normal", guards={"dsGuard": False})
        self.assertIn("Orchestrators run INSIDE your turn", normal)
        self.assertIn("`run_in_background: false`", normal)
        self.assertIn("gate card the user must answer", normal)
        # The rule lives in the Role A drive mechanics, next to the node-run rule.
        self.assertLess(normal.find("Orchestrators run INSIDE your turn"),
                        normal.find("Builders run as NODE RUNS"))
        self.assertNotIn("—", normal)
        self.assertNotIn("–", normal)


if __name__ == "__main__":
    unittest.main()

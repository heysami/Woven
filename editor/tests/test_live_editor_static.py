"""The live-share gate must serve every local script the editor page loads."""
from pathlib import Path
import re
import sys
import unittest

EDITOR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EDITOR))
import live


class LiveEditorStaticTests(unittest.TestCase):
    def test_every_local_index_script_is_served_to_guests(self):
        html = (EDITOR / "index.html").read_text(encoding="utf-8")
        # Static tags only: data.js / <slug>.layout.js are written by
        # document.write() and proxied per project by their own gate route.
        local = [src for src in re.findall(r'<script src="([A-Za-z0-9_./-]+)"', html)]
        self.assertIn("kinds/logic_nodes.js", local)
        for src in local:
            served = (src in live._EDITOR_STATIC_FILES
                      or any(src.startswith(p) for p in live._EDITOR_STATIC_DIR_PREFIXES))
            self.assertTrue(served, src + " would 404 for a live-share guest")


if __name__ == "__main__":
    unittest.main()

"""Concurrent visual saves must not silently overwrite a newer revision."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import edit_store


class EditStoreTests(unittest.TestCase):
    def test_only_one_save_from_a_shared_revision_can_commit(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "page.html"
            path.write_text("<h1>Before</h1>")
            expected = edit_store.read(path)["version"]

            def save(label):
                try:
                    return edit_store.write(path, label, expected)
                except edit_store.Conflict:
                    return None

            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(save, ["First", "Second"]))
            self.assertEqual(sum(result is not None for result in results), 1)
            self.assertIn(path.read_text(), ["First", "Second"])
            self.assertEqual(list(Path(directory).glob(".woven-edit-*")), [])

    def test_external_change_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "page.html"
            path.write_text("Before")
            expected = edit_store.read(path)["version"]
            path.write_text("Agent update")
            with self.assertRaises(edit_store.Conflict):
                edit_store.write(path, "Visual update", expected)
            self.assertEqual(path.read_text(), "Agent update")


if __name__ == "__main__":
    unittest.main()

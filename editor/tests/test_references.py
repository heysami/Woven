"""Project references: the per-project store of sources of truth, and how the
list rides on chat messages.

The rule under test: a chat thread is told the current list with its first
message and again only when the list changes, except Plan and Triage, which
get it on every message. A list that empties is announced once. Node runs and
planners never get it.

Run: python3 -m unittest discover -s editor/tests -p test_references.py -v
"""
import os
from pathlib import Path
import shutil
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest

EDITOR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EDITOR))
import references
import serve

DASHES = ("—", "–")


def fake_state(root, kind="freeform"):
    state = SimpleNamespace(run_id="r1", lock=threading.Lock(), events=[], project_root=root, kind=kind,
                            guards={"visual": True, "dsGuard": True, "reqQa": False},
                            done=False, stop_reason=None, turn_done=True, msg_queue=[])

    def append(k, data):
        state.events.append({"seq": len(state.events), "type": k, "data": data})
    state.append = append
    return state


def say(state, text, mode="normal"):
    """One composer message: what the agent receives, echoed like the daemon does."""
    send, fields = serve._mode_send(state, text, mode)
    state.append("user_message", serve._user_echo(text, mode=fields))
    return send, fields


class Store(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="refs-test-")
        os.makedirs(os.path.join(self.root, "docs", "spec"))
        Path(self.root, "docs", "dictionary.csv").write_text("field,type\n")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_links_and_paths_classify(self):
        self.assertEqual(references.classify(self.root, "https://docs.google.com/x"), ("link", "https://docs.google.com/x"))
        # The user's own example: a link typed without its scheme.
        self.assertEqual(references.classify(self.root, "drive.google.com/xxx/xx/data-dictionary"),
                         ("link", "https://drive.google.com/xxx/xx/data-dictionary"))
        self.assertEqual(references.classify(self.root, "./docs/spec/"), ("path", "docs/spec"))
        # A file name looks like a host; it exists, so it is a path.
        self.assertEqual(references.classify(self.root, "docs/dictionary.csv"), ("path", "docs/dictionary.csv"))
        self.assertEqual(references.classify(self.root, os.path.join(self.root, "docs")), ("path", "docs"))
        for bad in ("", "../outside", "ftp://x/y", "/etc/passwd", "https://a b"):
            with self.assertRaises(ValueError, msg=bad):
                references.classify(self.root, bad)

    def test_upsert_delete_move(self):
        a, _ = references.upsert(self.root, {"name": " Data  dictionary ", "location": "docs/dictionary.csv",
                                             "note": "field names and types"})
        self.assertTrue(references.ID_RE.match(a["id"]))
        self.assertEqual(a["name"], "Data dictionary")
        b, rows = references.upsert(self.root, {"name": "Spec", "location": "https://notion.so/spec"})
        self.assertEqual([r["name"] for r in rows], ["Data dictionary", "Spec"])
        with self.assertRaises(ValueError):
            references.upsert(self.root, {"name": "data dictionary", "location": "docs/spec"})
        edited, rows = references.upsert(self.root, dict(a, location="docs/spec"))
        self.assertEqual(edited["createdAt"], a["createdAt"])
        self.assertEqual(len(rows), 2)
        self.assertEqual([r["name"] for r in references.move(self.root, b["id"], -1)], ["Spec", "Data dictionary"])
        kinds = {r["name"]: r["kind"] for r in references.listing(self.root)}
        self.assertEqual(kinds, {"Spec": "link", "Data dictionary": "folder"})
        self.assertEqual([r["name"] for r in references.delete(self.root, b["id"])], ["Data dictionary"])

    def test_text_and_block_carry_no_dashes(self):
        references.upsert(self.root, {"name": "Dictionary", "location": "docs/dictionary.csv", "note": "fields"})
        references.upsert(self.root, {"name": "Gone", "location": "docs/later"})
        rows = references.load(self.root)
        text = references.text_listing(self.root) + references.agent_block(self.root, rows) + references.agent_block(self.root, [])
        self.assertIn("docs/dictionary.csv (project file) - source of truth for: fields", text)
        self.assertIn("docs/later (project path, NOT FOUND right now)", text)
        for d in DASHES:
            self.assertNotIn(d, text)


class Riding(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="refs-ride-")
        references.upsert(self.root, {"name": "Dictionary", "location": "https://drive.google.com/d/1"})

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_told_once_then_on_change(self):
        st = fake_state(self.root)
        send, fields = say(st, "build the form")
        self.assertIn("Woven project REFERENCES", send)
        self.assertIn("https://drive.google.com/d/1", send)
        self.assertEqual(fields["refs"], references.digest(references.load(self.root)))
        send, fields = say(st, "now the list")
        self.assertNotIn("REFERENCES", send)
        self.assertNotIn("refs", fields)
        references.upsert(self.root, {"name": "Spec", "location": "https://notion.so/spec"})
        send, _ = say(st, "and the detail page")
        self.assertIn("https://notion.so/spec", send)
        send, _ = say(st, "next")
        self.assertNotIn("REFERENCES", send)

    def test_plan_and_triage_every_message(self):
        st = fake_state(self.root)
        for mode in ("triage", "triage", "plan", "normal"):
            send, _ = say(st, "x", mode)
            if mode == "normal":
                self.assertNotIn("REFERENCES", send)
            else:
                self.assertIn("REFERENCES", send, mode)

    def test_emptied_list_announced_once(self):
        st = fake_state(self.root)
        say(st, "first")
        for r in references.load(self.root):
            references.delete(self.root, r["id"])
        send, fields = say(st, "second")
        self.assertIn("removed every reference", send)
        self.assertEqual(fields["refs"], "")
        send, _ = say(st, "third", "triage")
        self.assertNotIn("reference", send.split("===== THE USER'S MESSAGE =====")[-1])

    def test_no_references_no_block(self):
        empty = tempfile.mkdtemp(prefix="refs-none-")
        try:
            send, fields = say(fake_state(empty), "hello", "triage")
            self.assertNotIn("Woven project", send)
            self.assertNotIn("refs", fields)
        finally:
            shutil.rmtree(empty, ignore_errors=True)

    def test_node_runs_never_get_it(self):
        send, fields = say(fake_state(self.root, kind="node-agent"), "run it")
        self.assertNotIn("REFERENCES", send)
        self.assertNotIn("refs", fields)


if __name__ == "__main__":
    unittest.main()

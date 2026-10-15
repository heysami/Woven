"""Simulated personas: the per-project store, the critique armed on a message,
the knowledge a persona may read, and the planner / persona answer parsers.

The isolation rule under test: a persona knows only its profile, the documents
granted to it and what it is shown. Code is never part of that, not even
inside a granted folder.

Run: python3 -m unittest discover -s editor/tests -p test_personas.py -v
"""
import json
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
import personas
import serve

DASHES = ("—", "–")


def fake_state(root, echoes=()):
    state = SimpleNamespace(run_id="r1", lock=threading.Lock(), events=[], project_root=root,
                            guards={"visual": True, "dsGuard": True, "reqQa": False},
                            done=False, stop_reason=None, turn_done=True, msg_queue=[])

    def append(kind, data):
        state.events.append({"seq": len(state.events), "type": kind, "data": data})
    state.append = append
    for e in echoes:
        append("user_message", dict({"text": "earlier"}, **e))
    return state


class PersonaStore(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="personas-test-")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_profile_is_one_markdown_text(self):
        text = "# Maya R.\nFirst-year student, works part time\n\n## Goals\n- rent money fast\n\nDevice: phone"
        rec, rows = personas.upsert(self.root, {"profile": text,
                                                "knowledge": ["./docs/a.md", "../escape", "docs/a.md", "/abs/x"]})
        self.assertTrue(personas.ID_RE.match(rec["id"]))
        self.assertEqual(rec["name"], "Maya R.")
        self.assertEqual(rec["role"], "First-year student, works part time")
        self.assertEqual(rec["device"], "mobile")
        self.assertEqual(rec["profile"], text)
        self.assertEqual(rec["knowledge"], ["docs/a.md", "abs/x"])
        rec2, rows = personas.upsert(self.root, dict(rec, profile=text.replace("Device: phone", "Device: laptop")))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rec2["device"], "desktop")
        self.assertEqual(rec2["createdAt"], rec["createdAt"])
        self.assertIn("rent money fast", personas.persona_system(rec2))
        self.assertEqual(personas.delete(self.root, rec["id"]), [])

    def test_untouched_skeleton_never_reaches_the_persona(self):
        text = ("# Ana\n\n## Who they are\n- Night-shift nurse\n\n## About\n- \n\n## Goals\n- \n\n"
                "## In their words\n> \n\n## Using the product\nComfort with tech: low\nDevice: phone\n")
        rec, _ = personas.upsert(self.root, {"profile": text})
        self.assertEqual(rec["profile"], text.strip())          # the box keeps its structure
        self.assertEqual(rec["role"], "Night-shift nurse")
        self.assertEqual(rec["device"], "mobile")
        clean = personas.profile_clean(rec["profile"])
        self.assertEqual(clean, "# Ana\n\n## Who they are\n- Night-shift nurse\n\n"
                                "## Using the product\nComfort with tech: low\nDevice: phone")
        self.assertIn(clean, personas.persona_system(rec))
        skeleton_only = personas.upsert(self.root, {"profile": "# Lee\n\n## Goals\n- \n\nDevice: computer"})[0]
        self.assertEqual(skeleton_only["role"], "")

    def test_name_required(self):
        with self.assertRaises(ValueError):
            personas.upsert(self.root, {"profile": "   \n  "})

    def test_first_form_records_still_load(self):
        personas._write(self.root, [{"id": "p_old1", "name": "Tom K.", "role": "Mature student",
                                     "goals": "- finish", "device": "mobile", "quote": "Keep it simple"}])
        row = personas.load(self.root)[0]
        self.assertTrue(row["profile"].startswith("# Tom K.\nMature student"))
        self.assertIn("Device: phone", row["profile"])
        self.assertIn('> "Keep it simple"', row["profile"])

    def test_taste_images_belong_to_their_persona(self):
        pid = "p_abcd1234"
        kept = personas.save_taste(self.root, pid, b"\x89PNG fake", "png")
        dropped = personas.save_taste(self.root, pid, b"\x89PNG fake", "png")
        self.assertTrue(kept.startswith("personas/taste/p_abcd1234-"))
        with self.assertRaises(ValueError):
            personas.save_taste(self.root, pid, b"x", "svg+xml")
        rec, _ = personas.upsert(self.root, {"id": pid, "profile": "# Ana",
                                             "taste": [kept, "personas/taste/p_other-1.png", "docs/x.png"]})
        self.assertEqual(rec["taste"], [kept])                 # only its own uploads
        self.assertTrue(os.path.isfile(os.path.join(self.root, kept)))
        self.assertFalse(os.path.isfile(os.path.join(self.root, dropped)))   # removed on save
        personas.delete(self.root, pid)
        self.assertFalse(os.path.isfile(os.path.join(self.root, kept)))      # goes with the persona

    def test_draft_is_markdown(self):
        out = personas.parse_draft("```markdown\n# Lee\nNurse \u2014 nights\n```")
        self.assertEqual(out["profile"], "# Lee\nNurse - nights")


class CriticOnMessage(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="personas-test-")
        self.maya, _ = personas.upsert(self.root, {"name": "Maya", "role": "Student"})
        self.raj, _ = personas.upsert(self.root, {"name": "Raj"})

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_norm_critic(self):
        self.assertIsNone(personas.norm_critic(None))
        self.assertEqual(personas.norm_critic({"personas": []}), {})
        self.assertEqual(personas.norm_critic({"personas": ["bad", self.maya["id"]], "how": "x"}),
                         {"personas": [self.maya["id"]], "how": "text"})

    def test_armed_message_carries_the_request_and_stamps_the_echo(self):
        state = fake_state(self.root)
        send, fields = serve._mode_send(state, "make the form shorter", "normal",
                                        {"personas": [self.maya["id"], "p_gone0"], "how": "simulate"})
        self.assertTrue(send.startswith("make the form shorter"))
        self.assertIn("/__critic/run", send)
        self.assertIn("Maya", send)
        self.assertIn('"how": "simulate"', send)
        self.assertNotIn("p_gone0", send)            # a deleted persona drops out
        self.assertEqual(fields["critic"]["personas"], [self.maya["id"], "p_gone0"])
        for d in DASHES:
            self.assertNotIn(d, send)

    def test_message_without_critic_keeps_the_threads(self):
        state = fake_state(self.root, [{"critic": {"personas": [self.raj["id"]], "how": "text"}}])
        send, fields = serve._mode_send(state, "[decision:x] a - A", None)
        self.assertIn("/__critic/run", send)
        self.assertNotIn("critic", fields)           # inherited, not re-stamped

    def test_switched_off(self):
        state = fake_state(self.root, [{"critic": {"personas": [self.raj["id"]], "how": "text"}}])
        send, fields = serve._mode_send(state, "next", None, {"personas": []})
        self.assertNotIn("/__critic/run", send)
        self.assertEqual(fields["critic"], {})
        state.append("user_message", {"text": "next", **fields})
        send, _ = serve._mode_send(state, "after", None)
        self.assertNotIn("/__critic/run", send)


class Knowledge(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="personas-test-")
        os.makedirs(os.path.join(self.root, "research", "deep"))
        for rel, body in (("research/interviews.md", "They hate long forms."),
                          ("research/deep/notes.txt", "Phone first."),
                          ("research/app.js", "secret()"),
                          ("research/page.html", "<div>code</div>")):
            with open(os.path.join(self.root, rel), "w") as f:
                f.write(body)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_documents_only_never_code(self):
        text, images, notes = personas.knowledge_bundle(self.root, ["research", "../outside"])
        self.assertIn("They hate long forms.", text)
        self.assertIn("Phone first.", text)
        self.assertNotIn("secret()", text)
        self.assertNotIn("<div>", text)
        self.assertNotIn("research/", text)          # titles never leak the project's paths
        self.assertTrue(any("code file" in n for n in notes))
        self.assertEqual(images, [])


class Parsers(unittest.TestCase):
    def test_plan(self):
        text = 'Sure:\n```json\n{"summary": ["Shorter form"], "tasks": [{"goal": "Apply", "do": "click", "target": "Apply now", "lookFor": "fields"}]}\n```'
        summary, tasks = personas.parse_plan(text, ["P1", "P2"], True)
        self.assertEqual(summary, ["Shorter form"])
        self.assertEqual(tasks[0]["do"], "open")      # the session always starts on the start screen
        self.assertEqual(tasks[0]["page"], "P1")
        self.assertEqual(tasks[1]["target"], "Apply now")
        summary, tasks = personas.parse_plan(text, [], False)
        self.assertEqual(tasks, [])

    def test_critique(self):
        out = personas.parse_critique(json.dumps({
            "steps": [{"n": 1, "feel": "stuck", "thought": "Where is it?"}, {"n": 9, "thought": "x"}],
            "verdict": "Too long\u2014really.",
            "suggestions": [{"title": "Cut a field", "why": "No time", "priority": "high", "step": 1},
                            {"title": "", "why": "dropped"}]}), 2)
        self.assertEqual([s["n"] for s in out["steps"]], [1])
        self.assertEqual(out["verdict"], "Too long - really.")
        self.assertEqual(len(out["suggestions"]), 1)
        with self.assertRaises(ValueError):
            personas.parse_critique("no json here", 2)

    def test_digest_names_who_and_priority(self):
        report = {"id": "c_0123456789", "how": "simulate", "status": "done",
                  "tasks": [{"goal": "Apply", "do": "click", "target": "Apply"}],
                  "walks": {"desktop": {"device": "desktop", "steps": [{"n": 1, "ok": False, "error": 'could not find "Apply"'}]}},
                  "personas": [{"name": "Maya", "role": "Student", "status": "done", "verdict": "Lost.",
                                "suggestions": [{"title": "Show Apply", "why": "I could not find it", "priority": "high", "step": 1}]}]}
        text = personas.digest(report)
        self.assertIn("Maya (Student) - Lost.", text)
        self.assertIn("[high] Show Apply", text)
        self.assertIn('Step 1 could not be done on desktop', text)
        for d in DASHES:
            self.assertNotIn(d, text)


if __name__ == "__main__":
    unittest.main()

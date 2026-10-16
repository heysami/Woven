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

    def test_taste_uploads_belong_to_their_persona(self):
        pid = "p_abcd1234"
        kept = personas.save_taste(self.root, pid, b"\x89PNG fake", "png")
        dropped = personas.save_taste(self.root, pid, b"\x89PNG fake", "png")
        self.assertTrue(kept.startswith("personas/taste/p_abcd1234-"))
        with self.assertRaises(ValueError):
            personas.save_taste(self.root, pid, b"x", "svg+xml")
        rec, _ = personas.upsert(self.root, {"id": pid, "profile": "# Ana",
                                             "taste": [kept, "personas/taste/p_other-1.png", "docs/x.png",
                                                       "ref:r_abcd1234", "ref:bad", "../out.png"]})
        # Its own uploads, project paths and references; never another
        # persona's uploads (that persona's delete sweeps them).
        self.assertEqual(rec["taste"], [kept, "docs/x.png", "ref:r_abcd1234"])
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

    def test_references_are_read_fresh(self):
        import references
        folder, _ = references.upsert(self.root, {"name": "Interview folder", "location": "research/deep"})
        link, _ = references.upsert(self.root, {"name": "Market study", "location": "https://example.com/study"})
        gone = "ref:r_dead0000"
        entries = ["ref:" + folder["id"], "ref:" + link["id"], gone]
        # A critique run opens each link once and hands the result over.
        text, images, notes = personas.knowledge_bundle(
            self.root, entries, {"https://example.com/study": {"text": "Most buy on a phone."}})
        self.assertIn("Phone first.", text)
        self.assertIn("#### Market study\nMost buy on a phone.", text)   # titled by the reference's name
        self.assertNotIn("example.com", text)
        self.assertTrue(any("removed" in n for n in notes))
        # An edited reference moves every persona using it.
        references.upsert(self.root, dict(folder, location="research/interviews.md"))
        text, _, _ = personas.knowledge_bundle(self.root, entries[:1])
        self.assertIn("They hate long forms.", text)
        self.assertNotIn("Phone first.", text)
        # A link that cannot be opened is a note, never an invented document.
        _, _, notes = personas.knowledge_bundle(
            self.root, entries[1:2], {"https://example.com/study": {"error": "it needs a sign-in"}})
        self.assertEqual(notes, ["Market study: it needs a sign-in"])

    def test_taste_from_folders_files_and_links(self):
        import references
        shots = os.path.join(self.root, "moodboard")
        os.makedirs(shots)
        for name in ("a.png", "b.jpg", "c.js"):
            with open(os.path.join(shots, name), "wb") as f:
                f.write(b"x")
        site, _ = references.upsert(self.root, {"name": "A site they love", "location": "https://example.com"})
        shot = os.path.join(self.root, "shot.jpg")
        p = {"taste": ["moodboard", "research/interviews.md", "ref:" + site["id"]]}
        images, notes = personas.taste_images(self.root, p, {"https://example.com": {"image": shot}})
        self.assertEqual([os.path.basename(i) for i in images], ["a.png", "b.jpg", "shot.jpg"])
        self.assertTrue(any("not an image" in n for n in notes))

    def test_page_text(self):
        parser = personas._PageText()
        parser.feed("<html><head><title>T</title><script>var x</script></head><body><h1>Guide</h1>"
                    "<p>Compare &amp; save</p><style>.a{}</style><div>More</div></body></html>")
        self.assertEqual(parser.text(), "Guide\n\nCompare & save\n\nMore")
        self.assertEqual(personas._export_url("https://docs.google.com/spreadsheets/d/Ab-1/edit#gid=7"),
                         "https://docs.google.com/spreadsheets/d/Ab-1/export?format=csv&gid=7")


class Parsers(unittest.TestCase):
    def test_plan(self):
        text = ('Sure:\n```json\n{"summary": ["Shorter form"], "personas": ["p_aaaa", "p_zzzz"], "journeys": ['
                '{"title": "New application", "personas": ["p_aaaa"], "tasks": [{"goal": "Apply", "do": "click", "target": "Apply now"}]},'
                '{"title": "Saved draft", "personas": ["p_bbbb"], "tasks": [{"goal": "Edit", "do": "open", "page": "P2"}]},'
                '{"title": "Empty", "personas": ["p_aaaa"], "tasks": []}]}\n```')
        plan = personas.parse_plan(text, ["P1", "P2"], True, ["p_aaaa", "p_bbbb", "p_cccc"])
        self.assertEqual(plan["summary"], ["Shorter form"])
        self.assertEqual(plan["personas"], ["p_aaaa", "p_bbbb"])   # unknown id dropped, a journey's taker joins
        self.assertEqual([f["title"] for f in plan["flows"]], ["New application", "Saved draft"])
        first = plan["flows"][0]["tasks"]
        self.assertEqual(first[0]["do"], "open")                   # a journey always starts on a screen
        self.assertEqual(first[0]["page"], "P1")
        self.assertEqual(first[1]["target"], "Apply now")
        self.assertEqual(plan["flows"][1]["tasks"][0]["page"], "P2")
        self.assertEqual(personas.parse_plan(text, [], False, ["p_aaaa"])["flows"], [])

    def test_plan_first_form_and_no_one_touched(self):
        old = '{"summary": ["Shorter form"], "tasks": [{"goal": "Apply", "do": "click", "target": "Apply"}]}'
        plan = personas.parse_plan(old, ["P1"], True, ["p_aaaa", "p_bbbb"])
        self.assertEqual(plan["personas"], ["p_aaaa", "p_bbbb"])
        self.assertEqual(len(plan["flows"]), 1)
        self.assertEqual(plan["flows"][0]["personas"], ["p_aaaa", "p_bbbb"])
        none = personas.parse_plan('{"summary": ["x"], "personas": [], "journeys": []}', ["P1"], True, ["p_aaaa"])
        self.assertEqual((none["personas"], none["flows"]), ([], []))

    def test_critique(self):
        out = personas.parse_critique(json.dumps({
            "journeys": [{"journey": "f1", "steps": [{"n": 1, "feel": "stuck", "thought": "Where is it?"}, {"n": 9, "thought": "x"}]},
                         {"journey": "f9", "steps": [{"n": 1}]}],
            "verdict": "Too long—really.",
            "suggestions": [{"title": "Cut a field", "why": "No time", "priority": "high", "journey": "f2", "step": 3},
                            {"title": "Say why", "journey": "nope", "step": 1},
                            {"title": "", "why": "dropped"}]}), {"f1": 2, "f2": 3})
        self.assertEqual(list(out["journeys"]), ["f1"])
        self.assertEqual([s["n"] for s in out["journeys"]["f1"]], [1])
        self.assertEqual(out["verdict"], "Too long - really.")
        self.assertEqual([(s["journey"], s["step"]) for s in out["suggestions"]], [("f2", 3), (None, None)])
        one = personas.parse_critique('{"steps": [{"n": 1, "feel": "fine", "thought": "ok"}], "suggestions": [{"title": "A", "step": 1}]}', {"f4": 1})
        self.assertEqual(one["journeys"]["f4"][0]["thought"], "ok")      # the first answer form, one journey
        self.assertEqual(one["suggestions"][0]["journey"], "f4")
        with self.assertRaises(ValueError):
            personas.parse_critique("no json here", {"f1": 2})

    def test_changes(self):
        self.assertEqual(personas.norm_changes({"change": "Shorter form", "pages": "app"}, True),
                         [{"change": "Shorter form", "pages": ["app"], "flow": ""}])
        got = personas.norm_changes({"pages": ["app"], "changes": [{"change": "A"}, {"change": "B", "pages": ["app/b.html"], "flow": "x"}, {"change": " "}]}, True)
        self.assertEqual([(c["change"], c["pages"]) for c in got], [("A", ["app"]), ("B", ["app/b.html"])])
        with self.assertRaises(ValueError):
            personas.norm_changes({"changes": [{"change": "A"}]}, True)        # simulate needs pages
        with self.assertRaises(ValueError):
            personas.norm_changes({"changes": []}, False)

    def test_shot_names(self):
        root = tempfile.mkdtemp(prefix="personas-test-")
        try:
            d = os.path.join(personas.critiques_dir(root), "c_0123456789", "f2")
            os.makedirs(d)
            open(os.path.join(d, "mobile-3.jpg"), "wb").close()
            self.assertTrue(personas.shot_path(root, "c_0123456789", "f2/mobile-3.jpg"))
            self.assertIsNone(personas.shot_path(root, "c_0123456789", "../f2/mobile-3.jpg"))
            self.assertIsNone(personas.shot_path(root, "c_0123456789", "f2/../../x.jpg"))
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_digest_groups_by_change(self):
        report = {"id": "c_0123456789", "how": "simulate", "status": "done",
                  "personas": [{"id": "p_m", "name": "Maya", "role": "Student"}, {"id": "p_o", "name": "Omar"}],
                  "changes": [{"id": "t1", "title": "Guardian option on the form", "personas": ["p_m"]}],
                  "flows": [{"id": "f1", "change": "t1", "title": "New application", "personas": ["p_m"],
                             "tasks": [{"do": "open"}, {"do": "click", "target": "Apply"}],
                             "walks": {"desktop": {"device": "desktop", "steps": [{"n": 2, "ok": False, "error": 'could not find "Apply"'}]}}}],
                  "reviews": [{"change": "t1", "persona": "p_m", "status": "done", "verdict": "Lost.",
                               "suggestions": [{"title": "Show Apply", "why": "I could not find it", "priority": "high", "journey": "f1", "step": 2}]}]}
        text = personas.digest(report)
        self.assertIn("Change 1: Guardian option on the form", text)
        self.assertIn("Maya (Student) - Lost.", text)
        self.assertIn("[high] Show Apply: I could not find it (journey f1, step 2)", text)
        self.assertIn("step 2 could not be done on desktop", text)
        self.assertIn("Not affected: Omar", text)
        for d in DASHES:
            self.assertNotIn(d, text)


class CritiqueJob(unittest.TestCase):
    """A whole critique with fake models and a fake browser: two changes,
    each touching different personas, one persona meeting a change through
    two journeys, a phone user walked on a phone, a deep-thinking persona on
    the thread's model."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="personas-test-")
        self.maya, _ = personas.upsert(self.root, {"profile": "# Maya\nNew student"})
        self.raj, _ = personas.upsert(self.root, {"profile": "# Raj\nEnrolled student\nDevice: phone"})
        self.omar, _ = personas.upsert(self.root, {"profile": "# Omar\nFinancial aid officer", "deep": True})
        self.calls = {"fast": [], "cheap": [], "deep": []}

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def walker(self, args):
        cmd, out, device = args[0], args[args.index("--out") + 1], args[args.index("--device") + 1]
        with open(args[args.index("--plan") + 1]) as f:
            plan = json.load(f)
        if cmd == "survey":
            doc = {"pages": [{"key": p["key"], "title": "Form", "inventory": [{"role": "button", "name": "Apply"}]} for p in plan["pages"]]}
            with open(os.path.join(out, "survey.json"), "w") as f:
                json.dump(doc, f)
            return {}
        steps = []
        for i, _t in enumerate(plan["tasks"]):
            name = "%s-%d.jpg" % (device, i + 1)
            open(os.path.join(out, name), "wb").close()
            steps.append({"n": i + 1, "ok": True, "shot": name})
        with open(os.path.join(out, "walk-%s.json" % device), "w") as f:
            json.dump({"device": device, "steps": steps}, f)
        return {}

    def fast(self, system, blocks):
        self.calls["fast"].append(blocks)
        task = [{"goal": "Apply", "do": "click", "target": "Apply"}]
        if "guardian" in blocks[0]["text"]:
            return json.dumps({"summary": ["A guardian option on the form"], "personas": [self.maya["id"], self.raj["id"]],
                               "journeys": [{"title": "New application", "personas": [self.maya["id"]], "tasks": task},
                                            {"title": "Edit a saved draft", "personas": [self.maya["id"], self.raj["id"]], "tasks": task}]})
        return json.dumps({"summary": ["Statuses read Awaiting review"], "personas": [self.omar["id"]],
                           "journeys": [{"title": "Review the queue", "personas": [self.omar["id"]], "tasks": task}]})

    def persona(self, kind):
        def call(system, content):
            text = "\n".join(c.get("text", "") for c in content if c["type"] == "text")
            jids = [j for j in ("f1", "f2", "f3") if "### Journey %s:" % j in text]
            self.calls[kind].append((system.split("## Your profile")[1][:120], jids, sum(c["type"] == "image" for c in content)))
            return json.dumps({"journeys": [{"journey": j, "steps": [{"n": 2, "feel": "unsure", "thought": "Hm"}]} for j in jids],
                               "verdict": "Fine.", "suggestions": [{"title": "Label it", "priority": "low", "journey": jids[0], "step": 2}]})
        return call

    def test_changes_personas_and_journeys(self):
        events = []
        deps = {"fast_complete": self.fast, "persona_complete": self.persona("cheap"), "deep_complete": self.persona("deep"),
                "resolve_page": lambda raw: "http://x/" + raw, "emit": events.append, "walker": self.walker}
        req = {"how": "simulate", "models": {"cheap": "haiku", "deep": "opus"},
               "changes": personas.norm_changes({"changes": [{"change": "Added a guardian option", "pages": ["app"]},
                                                              {"change": "Renamed the pending status", "pages": ["app/queue.html"]}]}, True)}
        cid = personas.start(self.root, "proj", "r1", [self.maya, self.raj, self.omar], req, deps)
        personas.wait(cid, 20)
        rep = personas.get_report(self.root, cid)
        self.assertEqual(rep["status"], "done", rep.get("error"))
        self.assertEqual([c["personas"] for c in rep["changes"]], [[self.maya["id"], self.raj["id"]], [self.omar["id"]]])
        self.assertEqual([(f["id"], f["change"]) for f in rep["flows"]], [("f1", "t1"), ("f2", "t1"), ("f3", "t2")])
        self.assertEqual(sorted(rep["flows"][1]["walks"]), ["desktop", "mobile"])        # Raj is on a phone
        self.assertEqual(rep["flows"][1]["walks"]["mobile"]["steps"][0]["shot"], "f2/mobile-1.jpg")
        self.assertTrue(personas.shot_path(self.root, cid, "f2/mobile-1.jpg"))
        by = {(r["change"], r["persona"]): r for r in rep["reviews"]}
        self.assertEqual(sorted(by), sorted([("t1", self.maya["id"]), ("t1", self.raj["id"]), ("t2", self.omar["id"])]))
        self.assertEqual(sorted(by[("t1", self.maya["id"])]["journeys"]), ["f1", "f2"])   # two journeys, one review
        self.assertEqual(sorted(by[("t1", self.raj["id"])]["journeys"]), ["f2"])
        who = lambda kind: sorted(n for c in self.calls[kind] for n in ("Maya", "Raj", "Omar") if "# " + n in c[0])
        self.assertEqual(who("cheap"), ["Maya", "Raj"])
        self.assertEqual(who("deep"), ["Omar"])
        self.assertEqual({p["name"]: (p["deep"], p["model"], p["status"]) for p in rep["personas"]},
                         {"Maya": (False, "haiku", "done"), "Raj": (False, "haiku", "done"), "Omar": (True, "opus", "done")})
        self.assertIn("Not affected: Omar", personas.digest(rep))
        self.assertEqual(events[-1]["status"], "done")

    def test_orphaned_running_report_reads_as_stopped(self):
        rep = {"id": "c_00000000aa", "status": "running", "stage": "walking", "personas": []}
        personas.save_report(self.root, rep)
        got = personas.get_report(self.root, "c_00000000aa")
        self.assertEqual((got["status"], got["stage"]), ("error", "done"))


if __name__ == "__main__":
    unittest.main()

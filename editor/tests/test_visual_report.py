"""editor/visual_report.py and the record visual_qa keeps of each judge call.

A Visual QA run that asks typed visual checks has to be inspectable after the
fact: which questions were asked, about which screenshot or crop, what the
judge answered and how sure it was. These tests pin that record (the images
saved are the bytes the judge receives), the saved report, and the decisions
recorded on it.
"""

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

EDITOR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EDITOR))
sys.path.insert(0, str(EDITOR / "tools" / "qa"))

import typed_judge  # noqa: E402
import visual_qa  # noqa: E402
import visual_report  # noqa: E402


def _png(rgb, size):
    return typed_judge.solid_png(rgb, size=size)


class CallRecord(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="vr-")
        self.shot = Path(self.tmp) / "typed_page.png"
        self.shot.write_bytes(_png((30, 120, 200), 200))
        self.report = {"idleFrames": [], "interactions": [],
                       "typedPass": {"settled": {"path": str(self.shot),
                                                 "boxes": {"#menu": {"x": 20, "y": 30, "width": 60,
                                                                     "height": 40}}},
                                     "ds": {"off": [{"selector": "#bar", "source": "<style> .bar",
                                                     "count": 1, "skin": ["border"]}],
                                            "comps": []}}}

    def _run(self, answers):
        checks, rejected = visual_qa.parse_checks([
            {"id": "menu", "shape": "shows", "x": "a dropdown menu", "at": "page", "selector": "#menu",
             "source": "screen criteria: visual-checks.json"},
            {"id": "title", "shape": "shows", "x": "the heading Account", "at": "page"},
            {"id": "gone", "shape": "shows", "x": "a toast", "at": "page", "selector": "#toast"},
            {"id": "vague", "statement": "The page renders correctly.", "at": "page"},
        ])
        self.report["typedPass"]["settled"]["boxes"]["#toast"] = None

        def judge(state, questions, **kw):
            return {"answers": {q: answers[q] for q in questions}, "provider": "clef", "model": "m",
                    "thresholds": typed_judge.thresholds("frame_check", "clef")}
        return visual_qa.run_visual_checks(copy.deepcopy(self.report), checks, rejected, "shadow", 200, judge)

    def test_each_call_keeps_its_question_ids_state_and_images_as_sent(self):
        block = self._run({"menu": {"noul": 0.02}, "title": {"noul": 0.97}})
        self.assertEqual(len(block["calls"]), 2)
        crop_call = next(c for c in block["calls"] if c["questions"] == ["menu"])
        (img,) = crop_call["images"]
        self.assertTrue(img["path"].endswith("sent_%02d_1.png" % crop_call["n"]))
        data = Path(img["path"]).read_bytes()
        self.assertEqual((img["width"], img["height"]), typed_judge.image_size(data, "png"))
        self.assertEqual(img["box"], {"x": 20, "y": 30, "width": 60, "height": 40})
        self.assertEqual(img["capture"], str(self.shot))
        page_call = next(c for c in block["calls"] if c["questions"] == ["title"])
        self.assertEqual(page_call["images"][0]["path"], str(self.shot),
                         "a frame sent unchanged is its own capture file")
        self.assertIn("A screenshot of a web page", page_call["state"])
        self.assertEqual(block["pageShot"], str(self.shot))
        self.assertEqual(block["dsFound"]["offSystem"][0]["selector"], "#bar")
        rows = {r["id"]: r for r in block["checks"]}
        self.assertEqual(rows["menu"]["call"], crop_call["n"])
        self.assertNotIn("call", rows["gone"], "a check with nothing to crop is never sent")

    def test_a_one_colour_image_is_measured(self):
        if not visual_qa._PIL_OK:
            self.skipTest("Pillow not installed")
        block = self._run({"menu": {"noul": 0.5}, "title": {"noul": 0.5}})
        self.assertGreaterEqual(block["calls"][0]["images"][0]["oneColour"], 0.99)

    def test_save_copies_only_the_run_images(self):
        block = self._run({"menu": {"noul": 0.02}, "title": {"noul": 0.97}})
        root = Path(self.tmp) / "reports"
        rid = visual_report.save({"typedChecks": block, "verdict": "pass", "page": "a.html",
                                  "casesSummary": {"pass": 3, "total": 3}}, self.tmp,
                                 project="p", root=str(root))
        data = visual_report.load(rid, str(root))
        names = sorted(p.name for p in (root / rid).iterdir())
        self.assertIn("report.json", names)
        self.assertIn("typed_page.png", names)
        self.assertEqual(data["sizes"]["typed_page.png"], [200, 200])
        for call in data["typedChecks"]["calls"]:
            for im in call["images"]:
                self.assertNotIn("path", im, "no temp path leaks into the saved report")
                self.assertTrue(visual_report.file_path(rid, im["file"], str(root)))
        self.assertIsNone(visual_report.file_path(rid, "../report.json", str(root)))
        self.assertIsNone(visual_report.load("../etc", str(root)))

        text = visual_report.text_table(data)
        self.assertTrue(text.startswith("SURE NO  menu"), "the sure no comes first")
        self.assertIn("NOT ASKED  gone", text)
        self.assertEqual(visual_report.summary_line(data["typedChecks"]),
                         "1 sure no, 1 sure yes, 1 not asked")

    def test_a_decision_on_a_check_is_kept_on_its_row(self):
        block = self._run({"menu": {"noul": 0.02}, "title": {"noul": 0.97}})
        for r in block["checks"]:
            if r["status"] == "answered":
                r["logId"] = "log-" + r["id"]
        root = Path(self.tmp) / "labels"
        rid = visual_report.save({"typedChecks": block}, self.tmp, root=str(root))
        row = visual_report.label(rid, "menu", True, "the menu is open below Account", root=str(root))
        self.assertEqual(row["escalation"]["passed"], True)
        self.assertEqual(row["escalation"]["agrees"], False, "the judge said no; it is there")
        saved = visual_report.load(rid, str(root))
        menu = next(r for r in saved["typedChecks"]["checks"] if r["id"] == "menu")
        self.assertEqual(menu["escalation"]["note"], "the menu is open below Account")
        self.assertEqual(menu["logId"], "log-menu")
        self.assertIsNone(visual_report.label(rid, "nope", True, root=str(root)))
        with self.assertRaises(ValueError):
            visual_report.label(rid, "menu", "maybe", root=str(root))

    def test_a_choice_decision_must_be_one_of_its_options(self):
        checks, _rj = visual_qa.parse_checks([{"id": "orig", "shape": "which", "list": "ds_origin",
                                               "x": "the element", "expect": "layout", "at": "page"}])

        def judge(state, questions, **kw):
            return {"answers": {"orig": {"choice": "ds-copy", "confidence": 0.95,
                                         "probabilities": {"ds-copy": 0.95, "layout": 0.05}}},
                    "provider": "clef", "model": "m",
                    "thresholds": typed_judge.thresholds("frame_check", "clef")}
        block = visual_qa.run_visual_checks(copy.deepcopy(self.report), checks, [], "shadow", 200, judge)
        root = Path(self.tmp) / "choice"
        rid = visual_report.save({"typedChecks": block}, self.tmp, root=str(root))
        with self.assertRaises(ValueError):
            visual_report.label(rid, "orig", "sideways", root=str(root))
        row = visual_report.label(rid, "orig", "layout", root=str(root))
        self.assertEqual((row["escalation"]["passed"], row["escalation"]["agrees"]), (True, False))

    def test_a_quota_refusal_stops_the_asking_and_says_why(self):
        asked = []

        def judge(state, questions, **kw):
            asked.append(list(questions))
            raise typed_judge.JudgeError(
                "clef request failed: http 429 you have used up your daily free allocation of 10,000 neurons",
                status=429)
        checks, rejected = visual_qa.parse_checks([
            {"id": "a%d" % i, "shape": "shows", "x": "a heading %d" % i, "at": "page",
             "selector": "#menu"} if i % 2 else
            {"id": "a%d" % i, "shape": "shows", "x": "a heading %d" % i, "at": "page"} for i in range(2)])
        block = visual_qa.run_visual_checks(copy.deepcopy(self.report), checks, rejected, "shadow", 200, judge)
        self.assertEqual(len(asked), 1, "after one refusal the other call is not sent")
        self.assertIn("daily free allowance", block["refused"])
        self.assertIn("refused the rest", block["message"])
        self.assertTrue(all(r["status"] == "unavailable" for r in block["checks"]))

    def test_a_run_that_asked_nothing_saves_nothing(self):
        self.assertIsNone(visual_report.save({"typedChecks": {"checks": [], "rejected": []}}, self.tmp,
                                             root=str(Path(self.tmp) / "r")))
        self.assertIsNone(visual_report.save({}, self.tmp, root=str(Path(self.tmp) / "r")))

    def test_old_reports_are_pruned(self):
        root = Path(self.tmp) / "prune"
        for i in range(5):
            (root / ("20261013-0000%02d-abcdef" % i)).mkdir(parents=True)
        visual_report.prune(str(root), keep=2)
        self.assertEqual(sorted(p.name for p in root.iterdir()),
                         ["20261013-000003-abcdef", "20261013-000004-abcdef"])


if __name__ == "__main__":
    unittest.main()

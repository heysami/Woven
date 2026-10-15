"""editor/visual_checks.py - literal checks built from shapes and stored fields.

No model writes a question at check time: every question is a fixed shape
filled from a value Woven already stores, so a check is one fast classifier
call. These tests pin the shapes, the field table, and the grading.
"""

import json
from pathlib import Path
import sys
import unittest

EDITOR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EDITOR))

import typed_judge  # noqa: E402
import visual_checks as vc  # noqa: E402

TH = {"low": 0.6, "high": 0.9, "noul": 0.5}


class Shapes(unittest.TestCase):

    def test_each_shape_builds_one_literal_question(self):
        self.assertEqual(vc.question({"shape": "shows", "x": "a red delivery van"}),
                         ({"type": "noul", "instructions": "The image shows a red delivery van."}, 1))
        self.assertEqual(vc.question({"shape": "changed", "x": "an open menu"})[0]["instructions"],
                         "Image 2 shows an open menu that image 1 does not.")
        self.assertEqual(vc.question({"shape": "same_as", "x": "character"})[1], 2)
        q, n = vc.question({"shape": "which", "x": "the subject", "list": "direction"})
        self.assertEqual((q["type"], n), ("choice", 1))
        self.assertEqual(set(q["criteria"]), set(vc.LISTS["direction"]))

    def test_control_kind_and_label_place_are_closed_choices(self):
        # The two facts a plan's wireframe commits for an added entry: a Yes/No
        # radio pair and an On/Off switch both answer yes or no, only the look
        # tells them apart.
        q, n = vc.question({"shape": "which", "list": "control_kind",
                            "x": "the control on the row 'Funds A Laptop'"})
        self.assertEqual((q["type"], n), ("choice", 1))
        self.assertTrue({"switch", "radio", "checkbox", "dropdown", "text"} <= set(q["criteria"]))
        q, _ = vc.question({"shape": "which", "list": "label_place", "x": "the entry 'Funds A Laptop'"})
        self.assertEqual(set(q["criteria"]), {"same_line", "label_above", "label_after"})

    def test_a_pair_branches_on_its_style_scores(self):
        sys.path.insert(0, str(EDITOR / "tools" / "qa"))
        import visual_qa
        def answers(**dims):
            out = {"p": {"noul": 0.9}}
            for d in visual_qa.PAIR_DIMS:
                out["p__" + d] = {"noul": dims.get(d, 0.1)}
            return out
        v = visual_qa.pair_verdict(answers(border=0.85, shape=0.92), "p")
        self.assertEqual((v["answer"], v["passed"], v["band"]), ("differs in border, shape", False, "act"))
        v = visual_qa.pair_verdict(answers(words=0.97, icon=0.9), "p")
        self.assertEqual((v["answer"], v["passed"], v["band"]), ("same style (its icon, words differ)", True, "act"),
                         "content differs by design: the gallery shows sample content")
        v = visual_qa.pair_verdict(answers(colour=0.6), "p")
        self.assertEqual((v["answer"], v["passed"], v["band"]), ("unclear: colour", None, "escalate"))

    def test_vague_or_counting_values_are_refused(self):
        for bad in ({"shape": "shows", "x": "the effect working as expected"},
                    {"shape": "shows", "x": "how many cards"},
                    {"shape": "which", "x": "the toggle"},                 # no list
                    {"shape": "nope", "x": "a van"},
                    {"statement": "The page renders correctly."}):
            with self.assertRaises(ValueError, msg=bad):
                vc.question(bad)

    def test_a_literal_statement_is_still_accepted(self):
        q, n = vc.question({"statement": "The correct answer is highlighted."})
        self.assertEqual((q["instructions"], n), ("The correct answer is highlighted.", 1))

    def test_option_lists_are_closed_and_described(self):
        for name, opts in vc.LISTS.items():
            self.assertGreaterEqual(len(opts), 3, name)
            self.assertTrue(all(len(v) > 10 for v in opts.values()), name)


class FromFields(unittest.TestCase):

    def test_no_field_no_check(self):
        self.assertEqual(vc.from_fields({}, 4), [])
        self.assertEqual(vc.from_fields({"facing": "", "alt": None}, 4), [])

    def test_facing_becomes_a_direction_choice_on_every_frame(self):
        (c,) = vc.from_fields({"facing": "facing down toward the camera"}, 3)
        self.assertEqual((c["shape"], c["list"]), ("which", "direction"))
        self.assertEqual(c["expect"], ["down", "toward-viewer"])
        self.assertEqual(c["frames"], [[0], [1], [2]])

    def test_a_facing_it_cannot_map_is_not_checked(self):
        self.assertEqual(vc.from_fields({"facing": "heroically"}, 2), [])

    def test_end_state_is_the_last_frame_and_same_subject_first_vs_last(self):
        checks = {c["field"]: c for c in vc.from_fields({"endState": "lying on the ground",
                                                          "sameSubject": True}, 6)}
        self.assertEqual(checks["endState"]["frames"], [[5]])
        self.assertEqual(vc.question(checks["endState"])[0]["instructions"],
                         "The subject is lying on the ground.")
        self.assertEqual(checks["sameSubject"]["frames"], [[0, 5]])

    def test_alt_text_becomes_a_shows_check(self):
        (c,) = vc.from_fields({"alt": "a barista pouring latte art"}, 1)
        self.assertEqual(vc.question(c)[0]["instructions"], "The image shows a barista pouring latte art.")

    def test_an_exact_list_value_must_be_one_of_the_options(self):
        self.assertEqual(len(vc.from_fields({"subjectPosition": "left"}, 1)), 1)
        self.assertEqual(vc.from_fields({"subjectPosition": "somewhere"}, 1), [])


class Grading(unittest.TestCase):

    def test_a_choice_passes_only_when_its_top_option_is_expected(self):
        q, _n = vc.question({"shape": "which", "x": "the subject", "list": "direction"})
        ans = {"choice": "right", "confidence": 0.95, "probabilities": {"right": 0.95, "left": 0.05}}
        self.assertEqual(vc.verdict(q, ans, TH, ["left"]),
                         {"answer": "right", "passed": False, "confidence": 0.95, "band": "act"})
        self.assertTrue(vc.verdict(q, ans, TH, ["right", "down"])["passed"])
        self.assertIsNone(vc.verdict(q, ans, TH)["passed"])
        self.assertEqual(vc.verdict(q, None, TH)["band"], "escalate")

    def test_run_flags_a_confident_miss_and_shadow_does_not(self):
        checks = vc.from_fields({"facing": "left", "endState": "kneeling"}, 3)
        images = [typed_judge.solid_png((9, 9, 9))] * 3

        def judge(state, questions, **kw):
            q = questions["c"]
            if q["type"] == "choice":
                return {"answers": {"c": {"choice": "right", "confidence": 0.97,
                                          "probabilities": {"right": 0.97, "left": 0.03}}},
                        "provider": "clef", "thresholds": TH}
            return {"answers": {"c": {"noul": 0.98}}, "provider": "clef", "thresholds": TH}

        logged = []
        flag = vc.run(checks, images, judge, "sprite", "flag", shadow_log=logged.append)
        self.assertEqual(len([r for r in flag["results"] if r["status"] == "answered"]), 4)
        self.assertEqual(len(flag["findings"]), 3, "facing is wrong on all three frames")
        self.assertEqual(len(logged), 4)
        self.assertEqual(vc.run(checks, images, judge, "sprite", "shadow")["findings"], [])

    def test_an_unavailable_judge_stops_quietly(self):
        def judge(*a, **k):
            raise typed_judge.JudgeUnavailable("none", reason="no-image-judge")
        block = vc.run(vc.from_fields({"alt": "a van"}, 1), [b"x"], judge, "asset", "flag")
        self.assertIn("unavailable", block["message"])
        self.assertEqual(block["findings"], [])


if __name__ == "__main__":
    unittest.main()

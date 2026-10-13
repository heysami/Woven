"""editor/direction_ranking.py - the design library ranked for a brief by the
text judge at thread start, shown to the user and handed to the agent.

The ranking existed only as an instruction in PROTOTYPE.md step -1, and the
documented call left out each choice's question, so the judge refused it.
"""

import os
from pathlib import Path
import sys
import tempfile
import unittest

EDITOR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EDITOR))

import direction_ranking as dr  # noqa: E402
import typed_judge  # noqa: E402

AXES = str(EDITOR.parent / "docs" / "research" / "direction-axes.jev.json")


def judge(state, questions, **kw):
    ans = {"needs_direction": {"noul": 0.66}, "is_build": {"noul": 0.95}}
    for k, q in questions.items():
        if q["type"] == "choice":
            ids = list(q["criteria"])
            ans[k] = {"choice": ids[1], "confidence": 0.6,
                      "probabilities": {ids[0]: 0.1, ids[1]: 0.8, ids[2]: 0.05}}
    return {"answers": ans, "provider": "clef", "model": "m",
            "thresholds": {"low": 0.45, "high": 0.7, "noul": 0.5}}


class Ranking(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="dr-")
        os.makedirs(os.path.join(self.root, "source", "prototype"))

    def test_it_applies_only_before_any_direction_or_page(self):
        self.assertTrue(dr.applies(self.root))
        Path(self.root, "source", "prototype", "index.html").write_text("<html></html>")
        self.assertFalse(dr.applies(self.root), "a page is built: the direction exists")
        os.remove(os.path.join(self.root, "source", "prototype", "index.html"))
        Path(self.root, "DECISION_prototype-direction.json").write_text("{}")
        self.assertFalse(dr.applies(self.root), "a direction is locked")

    def test_the_setting_off_means_nothing_runs(self):
        self.assertIsNone(dr.propose(self.root, "a pixel art ludo game", judge, AXES, enabled=False))

    def test_every_question_is_one_the_judge_accepts(self):
        qs = dr.questions(dr.load_axes(AXES))
        self.assertEqual(sorted(qs), ["aesthetic", "is_build", "needs_direction", "recipe", "shell", "style"])
        self.assertTrue(all(q.get("instructions") for q in qs.values()), "every choice carries its question")
        typed_judge.validate_questions(qs, typed_judge.provider("clef"))

    def test_the_proposal_is_shown_and_handed_to_the_agent(self):
        out = dr.propose(self.root, "a pixel art ludo game", judge, AXES, enabled=True)
        ev = out["event"]
        self.assertEqual(ev["provider"], "clef")
        self.assertEqual(ev["needsDirection"], 0.66)
        style = ev["axes"]["style"]
        self.assertEqual([t["p"] for t in style["top"]], [0.8, 0.1, 0.05], "ranked, best first")
        self.assertTrue(style["top"][0]["desc"])
        self.assertIn("ranked the design library", out["forAgent"])
        self.assertIn("do not call /__judge", out["forAgent"])
        self.assertIn("style (confidence 0.60): %s 0.80" % style["top"][0]["id"], out["forAgent"])
        self.assertEqual(len(ev["proposals"]), 3)
        self.assertIn("Do NOT compose direction options", out["forAgent"])
        self.assertIn("[decision:prototype-direction] judgeN", out["forAgent"])

    def test_only_a_new_build_that_leaves_the_direction_open_gets_proposals(self):
        def answering(is_build, needs):
            def j(state, questions, **kw):
                out = judge(state, questions, **kw)
                out["answers"].update({"is_build": {"noul": is_build}, "needs_direction": {"noul": needs}})
                return out
            return j
        self.assertIsNone(dr.propose(self.root, "how do I export?", answering(0.1, 0.9), AXES, enabled=True),
                          "not a build request")
        self.assertIsNone(dr.propose(self.root, "a brutalist site in Space Mono", answering(0.95, 0.2), AXES,
                                     enabled=True), "the brief states its direction")
        self.assertIsNotNone(dr.propose(self.root, "a ludo game", answering(0.95, 0.7), AXES, enabled=True))

    def test_three_proposals_spread_across_the_open_axis(self):
        ev = {"thresholds": {"high": 0.7}, "axes": {
            "shell": {"top": [{"id": "canvas", "label": "canvas", "p": 0.23}, {"id": "mobile", "label": "mobile", "p": 0.13}]},
            "style": {"top": [{"id": "pixel", "label": "pixel", "p": 0.8}, {"id": "flat", "label": "flat", "p": 0.03}]},
            "aesthetic": {"top": [{"id": "ps1", "label": "ps1", "p": 0.16}, {"id": "8bit", "label": "8bit", "p": 0.15},
                                  {"id": "cozy", "label": "cozy", "p": 0.14}]}}}
        props = dr.proposals(ev)
        self.assertEqual(len(props), 3)
        self.assertEqual({p["spread"] for p in props}, {"aesthetic"}, "the axis the brief leaves most open")
        self.assertEqual([p["picks"]["aesthetic"]["id"] for p in props], ["ps1", "8bit", "cozy"])
        self.assertEqual({p["picks"]["style"]["id"] for p in props}, {"pixel"}, "the implied style stays")
        self.assertEqual({p["picks"]["shell"]["id"] for p in props}, {"canvas"})

    def test_each_pick_has_its_library_preview(self):
        pv = dr.previews(str(EDITOR.parent / "PROTOTYPE.md"))
        self.assertEqual(pv.get("pixel-grid-bitmap"), "design-library/style-pixel-bitmap-ui.png",
                         "ids and file names differ: the roster line links them")
        self.assertEqual(pv.get("canvas-floating-panels"), "design-library/shell-canvas-floating-ui.png")
        self.assertGreater(len(pv), 100)

    def test_a_failure_is_shown_never_missing(self):
        def down(*a, **k):
            raise typed_judge.JudgeUnavailable("no text judge", reason="no-key")
        out = dr.propose(self.root, "a pixel art ludo game", down, AXES, enabled=True)
        self.assertIn("no text judge is set up", out["event"]["error"])
        self.assertEqual(out["forAgent"], "")


if __name__ == "__main__":
    unittest.main()

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
        self.assertIn("[decision:prototype-direction] N - <title>", out["forAgent"])
        self.assertIn(".prototype-options/%s/options.json" % ev["slug"], out["forAgent"])
        self.assertIn("lock THAT one directly", out["forAgent"])
        self.assertNotIn("run step -1 as usual", out["forAgent"])

    def test_only_a_new_build_that_leaves_the_direction_open_gets_proposals(self):
        def answering(is_build, needs):
            def j(state, questions, **kw):
                out = judge(state, questions, **kw)
                out["answers"].update({"is_build": {"noul": is_build}, "needs_direction": {"noul": needs}})
                return out
            return j
        self.assertEqual(dr.propose(self.root, "how do I export?", answering(0.1, 0.9), AXES, enabled=True),
                         {"event": None, "forAgent": ""}, "not a build request: no direction step at all")
        stated = dr.propose(self.root, "a brutalist site in Space Mono", answering(0.95, 0.03), AXES, enabled=True)
        self.assertIsNone(stated["event"], "nothing to choose, so nothing shown")
        self.assertIn("Lock the direction it states", stated["forAgent"])
        self.assertIn("do NOT compose direction options", stated["forAgent"])
        self.assertIsNotNone(dr.propose(self.root, "a ludo game", answering(0.95, 0.32), AXES, enabled=True)["event"],
                             "a brief that names only its style still gets proposals")

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

    def test_the_card_is_the_standard_direction_options_block(self):
        """Same card as the agent's step -1: label, axes, vibe, why, six
        palette tokens, display and body fonts, recoloured previews."""
        out = dr.propose(self.root, "I want to create a pixel art ludo game. Every turn you attack or move.",
                         judge, AXES, enabled=True)
        ev = out["event"]

        def fonts(state, questions, **kw):
            return {"answers": {"display": {"choice": "Press Start 2P"}, "body": {"choice": "Pixelify Sans"}},
                    "provider": "clef", "model": "m", "thresholds": {}}
        made = []

        def recolor(src, dest, tokens):
            made.append((os.path.basename(src), tokens))
            Path(dest).write_bytes(b"png")
            return True
        done = dr.card(ev, "I want to create a pixel art ludo game. Every turn you attack or move.",
                       self.root, judge=fonts, recolor=recolor)
        m = done["markup"]
        self.assertTrue(m.startswith('<direction-options id="prototype-direction"'))
        self.assertEqual(m.count("<opt "), 3)
        self.assertEqual(m.count('<opt value="1" recommended>'), 1)
        self.assertEqual(m.count("<palette>"), 3)
        self.assertIn('<display font="Press Start 2P">Pixel art ludo game</display>', m)
        self.assertIn('<body font="Pixelify Sans">Every turn you attack or move.</body>', m)
        self.assertEqual(m.count('<image axis="'), sum(len(o["picks"]) for o in done["options"]))
        self.assertIn("auto-preview · judge-ranked", m)
        self.assertTrue(made and all(len(t) == 6 for _src, t in made), "every preview recoloured into its six tokens")
        saved = Path(self.root, ".prototype-options", ev["slug"], "options.json")
        self.assertTrue(saved.is_file(), "the agent reads the option the user picked from here")
        self.assertNotIn("Sample-image references", m, "the title is the entry's own heading")

    def test_palette_tokens_read_and_stay_in_family(self):
        dmg = ["#0f380f", "#306230", "#8bac0f", "#9bbc0f"]
        bg, surface, fg, muted, border, accent = dr.palette_tokens(dmg, dmg + ["#ff004d", "#1c1c1c"])
        self.assertEqual((bg, fg), ("#9bbc0f", "#0f380f"))
        self.assertNotEqual(accent, "#ff004d", "an accent from another palette family is not used")
        pale = ["#f8f8f8", "#e058b8", "#eba0d5", "#f4dbec"]
        _bg, _s, fg2, _m, _b, _a = dr.palette_tokens(pale, pale + ["#181818"])
        self.assertEqual(fg2, "#181818", "ink too close to its ground takes the entry's darkest")

    def test_the_judge_reads_the_request_not_the_editor_context(self):
        msg = ("[Context: you're chatting from WORKFLOW MODE of the prototype editor.]\n"
               "The canvas holds two kinds of object: nodes and whiteboard items.\n\n"
               "<chat-target>\nYou are editing prototype `prototype`.\n</chat-target>\n\n"
               "make me a real time pokemon game")
        self.assertEqual(dr.brief_of(msg), "make me a real time pokemon game")
        self.assertEqual(dr.brief_of("a plain request"), "a plain request")
        seen = []

        def spy(state, questions, **kw):
            seen.append(state)
            return judge(state, questions, **kw)
        dr.propose(self.root, msg, spy, AXES, enabled=True)
        self.assertEqual(seen, ["make me a real time pokemon game"])

    def test_a_failure_is_shown_never_missing(self):
        def down(*a, **k):
            raise typed_judge.JudgeUnavailable("no text judge", reason="no-key")
        out = dr.propose(self.root, "a pixel art ludo game", down, AXES, enabled=True)
        self.assertIn("no text judge is set up", out["event"]["error"])
        self.assertIn("do NOT compose direction options", out["forAgent"],
                      "judge on: the agent never falls back to composing options")


if __name__ == "__main__":
    unittest.main()

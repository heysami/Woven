"""Auto chat mode: the typed judge picks Normal / Plan / Triage per message by
fixed rules, reading where the conversation is (editor/auto_mode.py).

Run: python3 -m unittest discover -s editor/tests -p test_auto_mode.py -v
"""
from pathlib import Path
import sys
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

EDITOR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EDITOR))
import auto_mode
import serve
import typed_judge


def yes(*ids):
    return {q: {"noul": 0.9 if q in ids else 0.1} for q in auto_mode.QUESTIONS}


class DecideTests(unittest.TestCase):
    def test_fresh_requests_follow_the_fixed_order(self):
        d = auto_mode.decide
        self.assertEqual(d(yes("question_only", "affects_other"))[0], "normal")
        self.assertEqual(d(yes("affects_other", "new_layout"))[0], "triage")
        self.assertEqual(d(yes("new_layout", "straightforward"))[0], "plan")
        self.assertEqual(d(yes("straightforward"))[0], "normal")
        self.assertEqual(d(yes())[0], "plan")          # not clearly simple

    def test_answering_a_triage_moves_the_work_on(self):
        d = lambda *ids: auto_mode.decide(yes("continues", *ids), "triage")
        self.assertEqual(d("new_layout")[0], "plan")
        self.assertEqual(d("straightforward")[0], "normal")
        self.assertEqual(d()[0], "plan")
        # the answers already settled the impact the triage was about
        self.assertEqual(d("affects_other", "straightforward")[0], "normal")

    def test_a_triage_reply_that_adds_work_is_triaged_again(self):
        mode, why = auto_mode.decide(yes("continues", "adds_scope", "affects_other"), "triage")
        self.assertEqual(mode, "triage")
        self.assertIn("adds work", why)

    def test_a_reply_to_a_plan_stays_in_plan(self):
        self.assertEqual(auto_mode.decide(yes("continues", "straightforward"), "plan")[0], "plan")
        # ...but a new request after a plan is judged afresh
        self.assertEqual(auto_mode.decide(yes("straightforward"), "plan")[0], "normal")

    def test_a_judge_that_is_off_or_fails_changes_nothing(self):
        self.assertEqual(auto_mode.classify("x", None)["mode"], "triage")
        def boom(*a, **k):
            raise typed_judge.JudgeError("quota")
        r = auto_mode.classify("x", boom)
        self.assertEqual((r["mode"], r["judge"]), ("triage", None))

    def test_classify_reports_the_judge(self):
        r = auto_mode.classify("make the button blue",
                               lambda st, qs: {"answers": yes("straightforward"), "provider": "jev"})
        self.assertEqual((r["mode"], r["judge"]), ("normal", "jev"))


class StateTests(unittest.TestCase):
    def test_subject_is_the_users_own_words(self):
        ctx = "[Context: you're chatting from WORKFLOW MODE]\nrouting rules...\n\nRemove the due date"
        self.assertEqual(auto_mode.subject(ctx), "Remove the due date")
        hand = "[CONTINUING WORK]\nsummary\n\n[CURRENT REQUEST]\nnow plan it"
        self.assertEqual(auto_mode.subject(hand), "now plan it")
        pts = '<pointed-targets>\n<t id="1"/>\n</pointed-targets>\nfix this'
        self.assertEqual(auto_mode.subject(pts), "fix this")

    def test_long_text_keeps_its_start(self):
        long = "ASK: remove the due date. " + "detail " * 2000 + "END"
        s = auto_mode.subject(long)
        self.assertLessEqual(len(s), auto_mode.SUBJECT_MAX)
        self.assertTrue(s.startswith("ASK: remove the due date."))
        self.assertTrue(s.endswith("END"))

    def test_worst_case_fits_the_smallest_judge(self):
        # Every excerpt at its cap; Clef Flash has the smallest window.
        st = auto_mode.state_for("a" * 20000, earlier="b" * 20000, last_reply="c" * 20000, prev_mode="triage")
        flash = typed_judge.provider("clef-flash")
        typed_judge.check_context(st, auto_mode.QUESTIONS, flash)        # raises if it does not fit
        typed_judge.validate_questions(auto_mode.QUESTIONS, flash)
        self.assertLess(typed_judge.estimate_tokens(st, auto_mode.QUESTIONS), 4000)

    def test_state_names_the_previous_mode_and_keeps_the_end_of_the_reply(self):
        st = auto_mode.state_for("yes, remove it", earlier="remove the due date",
                                 last_reply="report... Needs your call: keep reminders?", prev_mode="triage")
        self.assertIn("a Triage reply", st)
        self.assertIn("Needs your call: keep reminders?", st)
        self.assertTrue(st.index("Earlier request") < st.index("New message"))


def fake_state(events=(), guards=None):
    st = SimpleNamespace(run_id="r1", lock=threading.Lock(), events=[], guards=guards or {})
    for kind, data in events:
        st.events.append({"type": kind, "data": data})
    return st


class DaemonTests(unittest.TestCase):
    def setUp(self):
        self.seen = []
        def judge(state, questions):
            self.seen.append(state)
            return {"answers": self.answers, "provider": "clef-flash"}
        self.answers = yes("straightforward")
        p = patch.object(serve, "_auto_judge", lambda guards: judge)
        p.start()
        self.addCleanup(p.stop)

    def test_auto_message_runs_in_the_picked_mode_and_says_why(self):
        st = fake_state([("user_message", {"text": "earlier", "mode": "normal"})])
        send, fields = serve._mode_send(st, "make the title bold", "auto")
        self.assertEqual(fields, {"mode": "normal", "modePick": "auto",
                                  "autoWhy": "it is a small, straightforward change",
                                  "autoJudge": "clef-flash"})
        self.assertEqual(send, "make the title bold")

    def test_answering_a_triage_reads_the_report(self):
        st = fake_state([
            ("user_message", {"text": "remove the due date", "mode": "triage", "modePick": "auto"}),
            ("agent", {"type": "text_delta", "delta": "Report. Needs your call: keep reminders?"}),
            ("agent", {"type": "text_delta", "delta": " subagent noise", "sidechain": True}),
        ])
        self.answers = yes("continues", "straightforward")
        send, fields = serve._mode_send(st, "yes keep them, go", "auto")
        self.assertEqual(fields["mode"], "normal")
        self.assertIn("answers the triage", fields["autoWhy"])
        self.assertIn("a Triage reply", self.seen[-1])
        self.assertIn("keep reminders?", self.seen[-1])
        self.assertNotIn("subagent noise", self.seen[-1])
        self.assertIn("switched back from Triage", send)

    def test_a_clarifying_question_does_not_hide_the_triage(self):
        st = fake_state([
            ("user_message", {"text": "remove the due date", "mode": "triage", "modePick": "auto"}),
            ("agent", {"type": "text_delta", "delta": "Needs your call: keep reminders?"}),
            ("user_message", {"text": "what are reminders?", "mode": "normal", "modePick": "auto",
                              "autoWhy": auto_mode.QUESTION_WHY}),
            ("agent", {"type": "text_delta", "delta": "Reminders are the emails sent before..."}),
        ])
        self.answers = yes("continues", "new_layout")
        _, fields = serve._mode_send(st, "ok, drop them and add a date picker instead", "auto")
        self.assertEqual(fields["mode"], "plan")
        self.assertIn("answers the triage", fields["autoWhy"])

    def test_a_card_answer_keeps_the_mode_and_the_auto_pick(self):
        st = fake_state([("user_message", {"text": "add a filter bar", "mode": "plan", "modePick": "auto"})])
        send, fields = serve._mode_send(st, "[decision:plan-next-1] execute - Execute the plan", None)
        self.assertEqual(fields, {"mode": "plan", "modePick": "auto"})
        self.assertEqual(self.seen, [])          # never re-judged
        self.assertIn("PLAN FIRST", send)

    def test_echo_carries_the_auto_fields(self):
        d = serve._user_echo("hi", mode={"mode": "plan", "modePick": "auto", "autoWhy": "x"})
        self.assertEqual(d, {"text": "hi", "mode": "plan", "modePick": "auto", "autoWhy": "x"})
        self.assertEqual(serve._norm_mode_pick("Auto"), "auto")
        self.assertIsNone(serve._norm_chat_mode("auto"))   # never a mode a message runs in


class GateTests(unittest.TestCase):
    def test_auto_needs_typed_judgment_on_for_the_chat(self):
        off = {"jevJudge": False, "typedJudgeVisual": False}
        with patch.object(serve, "_compact_config", lambda: dict(off)):
            self.assertIsNone(serve._auto_judge({}))
            self.assertIsNotNone(serve._auto_judge({"judgeImage": True}))   # the chat's own choice
        with patch.object(serve, "_compact_config", lambda: dict(off, jevJudge=True)):
            self.assertIsNotNone(serve._auto_judge({}))
            self.assertIsNone(serve._auto_judge({"judgeText": False}))


if __name__ == "__main__":
    unittest.main()

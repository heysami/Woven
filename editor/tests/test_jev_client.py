"""editor/jev.py against a recorded response - no key, no network.

Phase 0 of docs/features/jev-integration.md. The parity suite
(test_jev_parity.py) covers the invariants and the degradation paths; this
covers the client itself: the request it builds, the limits it refuses before
spending a round trip, and the readers that turn a recorded answer into a
decision.
"""

import json
from pathlib import Path
import sys
import unittest

EDITOR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EDITOR))

import jev  # noqa: E402

FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "jev_systemone_response.json")
    .read_text(encoding="utf-8"))


class _Recorded:
    """Stands in for urlopen. Captures the request so the wire shape is asserted
    rather than assumed."""

    def __init__(self, payload=None, headers=None):
        self.payload = payload if payload is not None else FIXTURE
        self.headers = headers or {}
        self.requests = []

    def __call__(self, req, timeout=None):
        self.requests.append(req)
        body = json.dumps(self.payload).encode("utf-8")
        outer = self

        class _Resp:
            def __enter__(self_inner):
                return self_inner

            def __exit__(self_inner, *a):
                return False

            @staticmethod
            def read():
                return body

        del outer
        return _Resp()


class JevClient(unittest.TestCase):
    QUESTIONS = {
        "states_a_direction": {"type": "noul",
                               "instructions": "This request states a visual direction."},
        "shell": {"type": "choice", "criteria": {"three-column-app": "dense product UI",
                                                 "bento-grid": "asymmetric marketing cells"},
                  "instructions": "Which shell does this request imply?"},
    }

    def _ask(self, **kw):
        rec = _Recorded(kw.pop("payload", None))
        real = jev.urllib.request.urlopen
        jev.urllib.request.urlopen = rec
        try:
            return jev.ask("a dense internal tool for case officers", self.QUESTIONS,
                           api_key="k", **kw), rec
        finally:
            jev.urllib.request.urlopen = real

    def test_the_request_carries_state_model_and_questions_under_a_bearer(self):
        _answers, rec = self._ask()
        self.assertEqual(len(rec.requests), 1)
        req = rec.requests[0]
        self.assertEqual(req.full_url, jev.API_URL)
        self.assertEqual(req.get_method(), "POST")
        self.assertEqual(req.get_header("Authorization"), "Bearer k")
        sent = json.loads(req.data.decode("utf-8"))
        self.assertEqual(set(sent), {"state", "model", "questions"})
        self.assertEqual(sent["model"], jev.DEFAULT_MODEL)
        self.assertEqual(set(sent["questions"]), set(self.QUESTIONS))

    def test_answers_come_back_keyed_by_the_question_ids_sent(self):
        answers, _rec = self._ask()
        self.assertIn("shell", answers)
        self.assertIn("states_a_direction", answers)

    def test_a_noul_reads_as_a_threshold_not_a_boolean(self):
        answers, _rec = self._ask()
        a = answers["states_a_direction"]
        self.assertAlmostEqual(jev.noul_value(a), 0.08)
        self.assertFalse(jev.noul_pass(a))
        self.assertTrue(jev.noul_pass(a, threshold=0.05))

    def test_a_choice_returns_the_whole_distribution_highest_first(self):
        """The full map is the point: it is what lets a caller compose a ranked
        shortlist instead of taking a single pick."""
        ranked = jev.choice_ranked(self._ask()[0]["shell"])
        self.assertEqual([r[0] for r in ranked],
                         ["three-column-app", "two-column-app",
                          "centered-narrow-column", "bento-grid"])
        self.assertAlmostEqual(sum(p for _i, p in ranked), 1.0, places=6)
        self.assertEqual(jev.choice_ranked(self._ask()[0]["shell"], 2),
                         [("three-column-app", 0.71), ("two-column-app", 0.18)])

    def test_confidence_routes_into_the_three_bands(self):
        answers, _rec = self._ask()
        t = jev.thresholds("direction_axis")
        self.assertEqual(jev.band(jev.confidence(answers["shell"]), t["low"], t["high"]), "act")
        self.assertEqual(jev.band(jev.confidence(answers["polish"]), t["low"], t["high"]), "confirm")
        self.assertEqual(jev.band(0.1, t["low"], t["high"]), "escalate")

    def test_thresholds_scale_with_what_the_answer_can_do(self):
        """A DS role inference can promote a finding to a gating error; a
        direction rank narrows a shortlist nobody is gated by."""
        self.assertGreater(jev.thresholds("ds_role")["high"],
                           jev.thresholds("direction_axis")["high"])
        self.assertEqual(jev.thresholds("no-such-kind"), jev.thresholds("default"))

    def test_a_winner_only_response_still_reads_as_a_ranking(self):
        self.assertEqual(jev.choice_ranked({"choice": "card", "confidence": 0.8}),
                         [("card", 0.8)])

    def test_retry_after_is_honoured_before_the_backoff_guess(self):
        import urllib.error
        calls = {"n": 0}
        slept = []

        def flaky(req, timeout=None):
            calls["n"] += 1
            if calls["n"] == 1:
                raise urllib.error.HTTPError("u", 429, "slow down", {"retry-after": "7"}, None)
            return _Recorded()(req, timeout)

        real_open, real_sleep = jev.urllib.request.urlopen, jev.time.sleep
        jev.urllib.request.urlopen = flaky
        jev.time.sleep = slept.append
        try:
            answers = jev.ask("x", self.QUESTIONS, api_key="k")
        finally:
            jev.urllib.request.urlopen, jev.time.sleep = real_open, real_sleep
        self.assertEqual(slept, [7.0])
        self.assertIn("shell", answers)

    def test_the_context_estimate_refuses_an_oversized_request_locally(self):
        """Rule 6, small state. Refusing here turns a silently truncated
        judgment into a clear error before any money is spent."""
        self.assertGreater(jev.estimate_tokens("x" * 36_000, {}), 9_000)
        with self.assertRaises(ValueError) as ctx:
            jev.ask("x" * (jev.MAX_CONTEXT_TOKENS * 4), self.QUESTIONS, api_key="k")
        self.assertIn("shard", str(ctx.exception))

    def test_a_choice_over_the_option_cap_is_refused(self):
        """The aesthetics roster is the biggest thing Woven sends; the cap is
        what makes one-question-per-axis legal at all."""
        jev.validate_questions({"q": {"type": "choice", "instructions": "pick",
                                      "criteria": {str(i): "r" for i in range(jev.MAX_CHOICE_OPTIONS)}}})
        with self.assertRaises(ValueError):
            jev.validate_questions({"q": {"type": "choice", "instructions": "pick",
                                          "criteria": {str(i): "r"
                                                       for i in range(jev.MAX_CHOICE_OPTIONS + 1)}}})

    def test_enabled_and_available_are_separate_questions(self):
        """The setting alone is an intent, the key alone is a capability. Only
        the pair makes the fast path real."""
        self.assertIs(type(jev.enabled()), bool)
        self.assertFalse(jev.available(""))
        self.assertTrue(jev.available("sk-something"))


if __name__ == "__main__":
    unittest.main()

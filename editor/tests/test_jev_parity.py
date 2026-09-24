"""Parity tests for the Jev typed-judgment path (docs/features/jev-integration.md).

The four invariants in that plan are worthless as prose. These are them as
tests. Everything runs on FIXTURES and a stubbed judge - no key, no network, no
daemon - so CI exercises the Jev path on every commit.

  P1 vocabulary parity (I1, I4) - the generated direction axes and the DS
     contract can only say what their sources already say.
  P2 superset invariant (I3) - jev-on findings are a superset of jev-off ones
     and no severity ever decreases, which is what keeps "turn it off" a safe
     operation rather than a behaviour change.
  P3 decision-shape parity (I2) - the direction axes cover exactly the axes an
     option card has to fill, so both paths emit the same SHAPE of decision.
  P4 degradation - no key, 401, exhausted 429, malformed body: every consumer
     returns the non-Jev result and none raises.
  P5 no preamble divergence - the toggle changes exactly one block and nothing
     else, so the two paths cannot start building differently.
"""
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
import urllib.error

ROOT = Path(__file__).resolve().parents[2]
EDITOR = ROOT / "editor"
sys.path.insert(0, str(EDITOR))
sys.path.insert(0, str(EDITOR / "tools" / "qa"))

import jev                      # noqa: E402
import ds_contract              # noqa: E402
import ds_lint                  # noqa: E402
import kinds.capabilities as capabilities  # noqa: E402

AXES_PATH = ROOT / "docs" / "research" / "direction-axes.jev.json"
PROTOTYPE_MD = ROOT / "PROTOTYPE.md"

# Mirrors DIRECTION_AXES in scripts/build-library-indexes.py. Named here rather
# than imported so the test fails when the generator quietly stops covering a
# roster, instead of agreeing with it.
ROSTER_HEADINGS = {
    "shell":     "## Shell index",
    "style":     "## Visual styles index",
    "aesthetic": "## Aesthetics index",
    "recipe":    "## Recipes index",
}
ROSTER_ROW = re.compile(r"^-\s+\*\*(?P<id>[^*]+)\*\*")


def roster_ids(axis):
    """The ids PROTOTYPE.md itself states for one roster, parsed independently
    of the generator."""
    lines = PROTOTYPE_MD.read_text(encoding="utf-8").splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith(ROSTER_HEADINGS[axis]))
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")),
               len(lines))
    out = set()
    for raw in lines[start + 1:end]:
        m = ROSTER_ROW.match(raw.strip())
        if m:
            out.add(m.group("id").strip().strip("`"))
    return out


# ── P1 - vocabulary parity (I1, I4) ─────────────────────────────────────────

class P1VocabularyParity(unittest.TestCase):
    """If direction-axes.jev.json and PROTOTYPE.md disagree about what exists,
    the Jev path is wrong even when Jev is right. This failing means someone
    edited one source and did not re-run the generator."""

    @classmethod
    def setUpClass(cls):
        cls.axes = json.loads(AXES_PATH.read_text(encoding="utf-8"))["axes"]

    def test_every_roster_axis_is_generated(self):
        self.assertEqual(set(self.axes), set(ROSTER_HEADINGS))

    def test_id_sets_are_identical_in_both_directions(self):
        for axis in ROSTER_HEADINGS:
            criteria = set(self.axes[axis]["criteria"])
            stated = roster_ids(axis)
            # "none" is the generator's own addition on the optional axes: an
            # answer, not a roster entry.
            offered = criteria - {"none"}
            self.assertEqual(offered - stated, set(),
                             "%s: offered to the judge but not in PROTOTYPE.md" % axis)
            self.assertEqual(stated - offered, set(),
                             "%s: in PROTOTYPE.md but never offered to the judge" % axis)

    def test_none_exists_exactly_on_the_optional_axes(self):
        for axis in ("aesthetic", "recipe"):
            self.assertIn("none", self.axes[axis]["criteria"])
            self.assertTrue(self.axes[axis]["optional"])
        for axis in ("shell", "style"):
            self.assertNotIn("none", self.axes[axis]["criteria"])
            self.assertFalse(self.axes[axis]["optional"])

    def test_every_rubric_is_substantial(self):
        """A thin rubric is the same failure as a thin library index: a dropped
        field gets replaced by confident wrong inference."""
        for axis, entry in self.axes.items():
            for oid, rubric in entry["criteria"].items():
                self.assertGreaterEqual(len(rubric), 20,
                                        "%s/%s has a %d-char rubric" % (axis, oid, len(rubric)))

    def test_every_axis_is_inside_the_choice_cap(self):
        for axis, entry in self.axes.items():
            self.assertLessEqual(len(entry["criteria"]), jev.MAX_CHOICE_OPTIONS, axis)


class P1ContractParity(unittest.TestCase):
    """Every contract component must be a real DS class. The contract is derived
    from the stylesheet, so this catches a parser that starts inventing bases."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.ds = Path(self.temp.name) / "ds"
        self.ds.mkdir()
        (self.ds / "styles.css").write_text(
            ":root{--ink:#111;--pad:8px}\n"
            ".card{display:grid;gap:8px;padding:12px;background:#fff;border:1px solid #ddd}\n"
            ".card__title{font-weight:600;color:var(--ink)}\n"
            ".card__body{color:#555}\n"
            ".card--compact{padding:6px}\n"
            "button.btn{cursor:pointer;padding:6px 10px;background:#111;color:#fff}\n"
            ".btn--ghost{background:transparent;color:#111}\n"
            ".stack{display:flex;flex-direction:column;gap:4px}\n", encoding="utf-8")
        (self.ds / "DESIGN.md").write_text(
            "# DS\n\n## Catalog\n"
            "Card    .card [--compact] .card__title .card__body - bounded content surface\n"
            "Button  .btn [--ghost] - the one clickable affordance\n", encoding="utf-8")
        (self.ds / "gallery.html").write_text(
            "<div class='card'><h3 class='card__title'>A</h3><p class='card__body'>x</p></div>"
            "<div class='card'><h3 class='card__title'>B</h3></div>", encoding="utf-8")

    def test_every_component_is_a_declared_class(self):
        contract = ds_contract.build(str(self.ds))
        vocab = ds_lint.load_ds_vocab(str(self.ds))["classes"]
        for c in contract["components"]:
            self.assertIn(c["id"], vocab, "contract invented .%s" % c["id"])
            for part in list(c["requiredParts"]) + list(c["optionalParts"]) + list(c["variants"]):
                self.assertIn(part, vocab, "contract invented .%s" % part)

    def test_required_parts_come_from_observed_usage_not_from_naming(self):
        comp = {c["id"]: c for c in ds_contract.build(str(self.ds))["components"]}["card"]
        # gallery.html ships two cards; only __title is in both.
        self.assertEqual(comp["requiredParts"], ["card__title"])
        self.assertEqual(comp["optionalParts"], ["card__body"])

    def test_a_part_variant_is_not_a_base_variant(self):
        (self.ds / "styles.css").write_text(
            (self.ds / "styles.css").read_text(encoding="utf-8")
            + ".card__title--lead{font-size:20px}\n", encoding="utf-8")
        comp = {c["id"]: c for c in ds_contract.build(str(self.ds))["components"]}["card"]
        self.assertEqual(comp["variants"], ["card--compact"])
        self.assertIn("card__title--lead", comp["optionalParts"])

    def test_notforusewhen_is_never_invented(self):
        """It becomes a Choice criterion verbatim and it gates, so a synthesised
        exclusion is worse than a missing one."""
        for c in ds_contract.build(str(self.ds))["components"]:
            if "notForUseWhen" in c:
                self.assertIn(c["notForUseWhen"],
                              (self.ds / "DESIGN.md").read_text(encoding="utf-8"))


# ── P2 - superset invariant (I3) ────────────────────────────────────────────

def _recorded(choice, confidence):
    """One recorded Choice answer, in the wire shape jev.ask returns."""
    return {"choice": choice, "confidence": confidence,
            "probabilities": {choice: confidence, "page-layout-only": 1.0 - confidence}}


class P2SupersetInvariant(unittest.TestCase):
    """For the same page, jev-off findings must be a subset of jev-on findings
    by (rule, page, line), and no finding's severity may DECREASE when Jev is
    on. This is what makes turning the switch off a safe operation."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        ds = root / "design-systems" / "ds1"
        ds.mkdir(parents=True)
        (ds / "styles.css").write_text(
            ".card{display:grid;gap:8px;padding:12px;background:#fff;border:1px solid #ddd}\n"
            ".card__title{font-weight:600}\n"
            ".card--compact{padding:6px}\n", encoding="utf-8")
        (ds / "gallery.html").write_text(
            "<div class='card'><h3 class='card__title'>A</h3></div>"
            "<div class='card'><h3 class='card__title'>B</h3></div>", encoding="utf-8")
        proto = root / "source" / "main"
        proto.mkdir(parents=True)
        # .panel: defines component chrome, name does not match, structure does
        # not match -> the ambiguous residue, the ONLY thing Jev may promote.
        # .product-card: a name match -> error with or without Jev.
        (proto / "index.html").write_text(
            "<html><head><style>\n"
            ".panel{background:#fff;border:1px solid #eee;padding:16px;border-radius:8px}\n"
            ".gutter{margin-left:12px;width:40%}\n"
            "</style></head><body>\n"
            "<div class='product-card'>x</div>\n"
            "<div class='panel'><span>Quarterly total</span></div>\n"
            "<div class='gutter'>side</div>\n"
            "</body></html>", encoding="utf-8")
        self.root = str(root)

    def _run(self, jev_answer=None):
        argv = ["--project-root", self.root, "--prototype", "main", "--json"]
        real_ask, real_enabled, real_available = jev.ask, jev.enabled, jev.available
        if jev_answer is not None:
            argv.append("--jev")
            jev.ask = lambda state, questions, **kw: {q: jev_answer for q in questions}
            jev.enabled = lambda: True
            jev.available = lambda *a, **k: True
        try:
            import io
            import contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                ds_lint.main(argv)
            return json.loads(buf.getvalue())
        finally:
            jev.ask, jev.enabled, jev.available = real_ask, real_enabled, real_available

    @staticmethod
    def _keys(report):
        return {(f["rule"], f.get("page"), f.get("line")) for f in report["findings"]}

    @staticmethod
    def _worst(report):
        rank = {"info": 0, "warn": 1, "error": 2}
        worst = {}
        for f in report["findings"]:
            k = (f["rule"], f.get("page"), f.get("line"))
            worst[k] = max(worst.get(k, -1), rank[f["severity"]])
        return worst

    def test_off_findings_are_a_subset_of_on_findings(self):
        off = self._run()
        on = self._run(_recorded("card", 0.97))
        self.assertLessEqual(self._keys(off), self._keys(on))

    def test_no_severity_decreases_when_jev_is_on(self):
        off, on = self._run(), self._run(_recorded("card", 0.97))
        worst_on = self._worst(on)
        for key, sev in self._worst(off).items():
            self.assertGreaterEqual(worst_on.get(key, -1), sev, key)

    def test_a_confident_verdict_promotes_the_ambiguous_row(self):
        on = self._run(_recorded("card", 0.97))
        promoted = [f for f in on["findings"]
                    if f["rule"] == "invented-component" and f.get("matchedBy") == "jev"]
        self.assertEqual([f["classes"][0] for f in promoted], ["panel"])
        self.assertEqual(on["jev"]["promoted"], 1)

    def test_page_layout_only_declines_to_promote_but_removes_nothing(self):
        """The plan's word is "suppress"; the invariant is that nothing is ever
        removed. page-layout-only means DO NOT PROMOTE, not DELETE."""
        off = self._run()
        on = self._run(_recorded("page-layout-only", 0.99))
        self.assertEqual(on["jev"]["promoted"], 0)
        self.assertLessEqual(self._keys(off), self._keys(on))
        self.assertEqual(on["counts"]["error"], off["counts"]["error"])

    def test_low_confidence_does_not_promote(self):
        on = self._run(_recorded("card", 0.51))
        self.assertEqual(on["jev"]["promoted"], 0)

    def test_positional_only_local_css_never_reaches_the_judge(self):
        """Row 3 of the certainty table: a page-local class with purely
        positional CSS is ordinary layout and is not a candidate at all."""
        on = self._run(_recorded("card", 0.99))
        promoted = {f["classes"][0] for f in on["findings"]
                    if f.get("matchedBy") == "jev"}
        self.assertNotIn("gutter", promoted)


# ── P3 - decision-shape parity (I2) ─────────────────────────────────────────

class P3DecisionShape(unittest.TestCase):
    """Jev narrows what the agent CONSIDERS, never what it CONCLUDES. Both paths
    must be able to fill the same option card: the picks may differ, the
    structure may not."""

    @classmethod
    def setUpClass(cls):
        cls.axes = json.loads(AXES_PATH.read_text(encoding="utf-8"))["axes"]
        cls.emit = (ROOT / "prototype" / "step-neg1-emit-ui.md").read_text(encoding="utf-8")

    def test_every_axis_the_option_card_states_is_rankable(self):
        """The card's <axes> line commits shell, style and aesthetic. An axis the
        card must fill but the judge cannot rank would make the Jev path emit a
        differently-shaped decision."""
        for axis in ("shell", "style", "aesthetic"):
            self.assertIn(axis, self.axes)
            self.assertTrue(self.axes[axis]["criteria"])
        self.assertRegex(self.emit, r"<axes>Shell:.*Style:.*Aesthetic:")

    def test_the_jev_branch_is_additive_in_the_step_file(self):
        """It may add a ranking section; it may not replace the emit contract or
        the three-option shape."""
        self.assertIn("Ranking the axes with typed judgment", self.emit)
        self.assertIn("## Emit exactly this message shape", self.emit)
        for value in ('<opt value="1" recommended>', '<opt value="2">', '<opt value="3">'):
            self.assertIn(value, self.emit)

    def test_the_step_file_states_what_the_judge_cannot_see(self):
        """It ranks on roster prose and has never seen the library previews the
        user actually chooses from. A step file that omits this invites the
        agent to treat a probability as a decision."""
        section = self.emit.split("Ranking the axes with typed judgment", 1)[1]
        section = section.split("## Emit exactly this message shape", 1)[0]
        self.assertIn("-ui.png", section)
        self.assertIn("prose", section.lower())

    def test_a_recipe_short_circuit_is_still_a_composed_pick(self):
        """Every recipe names all three axes, so short-circuiting on one cannot
        produce an option card with an axis missing."""
        for rid, rubric in self.axes["recipe"]["criteria"].items():
            if rid == "none":
                continue
            self.assertIn("+", rubric, rid)


# ── P4 - degradation ────────────────────────────────────────────────────────

class _FailingOpener:
    def __init__(self, exc):
        self.exc = exc
        self.calls = 0

    def __call__(self, req, timeout=None):
        self.calls += 1
        raise self.exc


class P4Degradation(unittest.TestCase):
    """No key, 401, a 429 that exhausts retries, a malformed body. Every
    consumer returns the non-Jev result and logs; none raises. Modelled on
    run_judge in tools/qa/visual_qa.py, which already gets this right."""

    QUESTIONS = {"q": {"type": "noul", "instructions": "The state mentions a card."}}

    def test_no_key_raises_the_distinguishable_unavailable(self):
        with self.assertRaises(jev.JevUnavailable):
            jev.ask("x", self.QUESTIONS, api_key=None,
                    url="http://127.0.0.1:1/never")

    def test_401_fails_immediately_without_retrying(self):
        opener = _FailingOpener(urllib.error.HTTPError(
            "u", 401, "Unauthorized", {}, None))
        real = jev.urllib.request.urlopen
        jev.urllib.request.urlopen = opener
        try:
            with self.assertRaises(jev.JevError):
                jev.ask("x", self.QUESTIONS, api_key="k", max_retries=3)
        finally:
            jev.urllib.request.urlopen = real
        self.assertEqual(opener.calls, 1, "a caller error must not be retried")

    def test_429_retries_then_raises_a_catchable_error(self):
        opener = _FailingOpener(urllib.error.HTTPError("u", 429, "slow down", {}, None))
        real_open, real_sleep = jev.urllib.request.urlopen, jev.time.sleep
        jev.urllib.request.urlopen = opener
        jev.time.sleep = lambda _s: None
        try:
            with self.assertRaises(jev.JevError):
                jev.ask("x", self.QUESTIONS, api_key="k", max_retries=2)
        finally:
            jev.urllib.request.urlopen, jev.time.sleep = real_open, real_sleep
        self.assertEqual(opener.calls, 3)

    def test_malformed_body_is_an_error_not_a_crash(self):
        class _Resp:
            def __enter__(self_inner):
                return self_inner

            def __exit__(self_inner, *a):
                return False

            @staticmethod
            def read():
                return b'{"unexpected": true}'

        real = jev.urllib.request.urlopen
        jev.urllib.request.urlopen = lambda req, timeout=None: _Resp()
        try:
            with self.assertRaises(jev.JevError):
                jev.ask("x", self.QUESTIONS, api_key="k")
        finally:
            jev.urllib.request.urlopen = real

    def test_readers_are_total_on_garbage(self):
        for bad in (None, {}, [], "nope", {"probabilities": "nope"}, {"noul": "high"}):
            self.assertFalse(jev.noul_pass(bad))
            self.assertEqual(jev.choice_ranked(bad), [])
            self.assertIsNone(jev.confidence(bad))
        self.assertEqual(jev.band(None), "escalate")

    def test_ds_lint_jev_pass_never_raises_and_changes_nothing(self):
        findings = [{"rule": "undefined-classes", "severity": "info", "page": "p", "classes": ["x"]}]
        before = list(findings)
        real_ask, real_enabled, real_available = jev.ask, jev.enabled, jev.available
        jev.enabled, jev.available = (lambda: True), (lambda *a, **k: True)

        def boom(*a, **k):
            raise jev.JevError("network down")

        jev.ask = boom
        try:
            status = ds_lint.run_jev_pass(
                {"components": [{"id": "card", "role": "surface", "oneLine": "A bounded surface"}]},
                [{"page": "p", "class": "x", "element": {"line": 3, "tag": "div", "classes": ["x"],
                                                         "inlineStyle": "", "textSample": "hi",
                                                         "childShape": []}}],
                findings,
                ds_lint.contract_index({"components": [{"id": "card", "role": "surface"}]}))
        finally:
            jev.ask, jev.enabled, jev.available = real_ask, real_enabled, real_available
        self.assertEqual(findings, before)
        self.assertEqual(status["promoted"], 0)
        self.assertIn("network down", status["message"])

    def test_ds_lint_jev_pass_is_a_no_op_when_the_switch_is_off(self):
        real_enabled = jev.enabled
        jev.enabled = lambda: False
        try:
            status = ds_lint.run_jev_pass(
                {"components": []},
                [{"page": "p", "class": "x", "element": {"line": 1, "tag": "div", "classes": ["x"],
                                                         "inlineStyle": "", "textSample": "",
                                                         "childShape": []}}],
                [], ds_lint.contract_index({"components": []}))
        finally:
            jev.enabled = real_enabled
        self.assertFalse(status["available"])
        self.assertIn("turned off", status["message"])

    def test_question_shape_is_rejected_before_a_round_trip(self):
        for bad in (
            {"q": {"type": "choice", "criteria": {str(i): "x" * 30 for i in range(300)},
                   "instructions": "pick"}},
            {"q": {"type": "score", "criteria": ["a"], "instructions": "rate"}},
            {"q": {"type": "essay", "instructions": "write"}},
            {"q": {"type": "noul", "instructions": "  "}},
        ):
            with self.assertRaises(ValueError):
                jev.validate_questions(bad)

    def test_an_oversized_request_is_refused_rather_than_truncated(self):
        with self.assertRaises(ValueError):
            jev.ask("x" * 400_000, self.QUESTIONS, api_key="k")


# ── P5 - no preamble divergence ─────────────────────────────────────────────

class P5PreambleParity(unittest.TestCase):
    """The preamble is what every agent reads. An accidental second copy of a
    rule there, phrased for the Jev path, is how the two paths start building
    differently."""

    TIERS = ("setup", "scoped", "normal", "leaf")

    def test_the_toggle_changes_exactly_one_block(self):
        for tier in self.TIERS:
            off = capabilities.capabilities_preamble(tier=tier, jev=False)
            on = capabilities.capabilities_preamble(tier=tier, jev=True)
            self.assertEqual(on.replace(capabilities.JEV_FAST_PATH_STUB, "", 1), off,
                             "tier %s diverges beyond the one block" % tier)

    def test_the_leaf_tier_never_carries_it(self):
        """A leaf builder picks no direction and runs no requirement QA."""
        on = capabilities.capabilities_preamble(tier="leaf", jev=True)
        self.assertNotIn(capabilities.JEV_FAST_PATH_STUB, on)

    def test_the_interactive_tiers_do_carry_it(self):
        for tier in ("setup", "scoped", "normal"):
            self.assertIn(capabilities.JEV_FAST_PATH_STUB,
                          capabilities.capabilities_preamble(tier=tier, jev=True))

    def test_the_block_states_the_limits_that_make_it_safe(self):
        stub = capabilities.JEV_FAST_PATH_STUB
        for rule in ("count", "colour", "image", "ADDS", "CONSIDER"):
            self.assertIn(rule, stub, "the preamble block drops the %r rule" % rule)

    def test_the_block_is_absent_by_default_without_a_key(self):
        real_enabled, real_available = jev.enabled, jev.available
        jev.enabled, jev.available = (lambda: True), (lambda *a, **k: False)
        try:
            self.assertFalse(capabilities._jev_enabled())
        finally:
            jev.enabled, jev.available = real_enabled, real_available


if __name__ == "__main__":
    unittest.main()

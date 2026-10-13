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
  P5 no preamble divergence - the toggles change exactly one block and nothing
     else, so the two paths cannot start building differently.
  P8 typed visual checks - only literal claims tied to a capture (cropped to
     one element) are asked, vague restatements of intent are rejected, and in
     Shadow mode visual_qa's verdict, reasons, exit code and LLM verdict are
     exactly what they are with it off.
"""
import json
import os
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
import typed_judge              # noqa: E402
import ds_contract              # noqa: E402
import visual_qa                # noqa: E402
import ds_lint                  # noqa: E402
import kinds.capabilities as capabilities  # noqa: E402

AXES_PATH = ROOT / "docs" / "research" / "direction-axes.jev.json"

# Nothing in this suite may write into the user's real answer log or labels.
_LOG_DIR = tempfile.mkdtemp(prefix="jev-parity-log-")
_REAL_LOG = (typed_judge.SHADOW_LOG_PATH, typed_judge.LABELS_PATH)


def setUpModule():
    typed_judge.SHADOW_LOG_PATH = os.path.join(_LOG_DIR, "log.jsonl")
    typed_judge.LABELS_PATH = os.path.join(_LOG_DIR, "labels.json")


def tearDownModule():
    typed_judge.SHADOW_LOG_PATH, typed_judge.LABELS_PATH = _REAL_LOG
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


def _two_stage(rec, question):
    """Answer the DS judgment's two questions from one recorded verdict: stage 1
    (ds-copy / new-ui / layout) says ds-copy unless the record names layout or
    new-ui, and stage 2 (which component) answers the record's component."""
    if "ds-copy" in question["criteria"]:
        stage1 = {"page-layout-only": "layout", "layout": "layout",
                  "new-ui": "new-ui"}.get(rec["choice"], "ds-copy")
        return _recorded(stage1, rec["confidence"])
    return rec


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
            jev.ask = lambda state, questions, **kw: {q: _two_stage(jev_answer, questions[q])
                                                       for q in questions}
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


def _unit(cls, tag="div", text="", family="box", count=1):
    """One off-system unit, as ds_lint.off_system_units emits it."""
    return {"page": "p.html", "source": "<style> .%s" % cls, "selector": "." + cls,
            "skin": ["border: 1px solid <colour>", "border-radius: 12px"],
            "decls": "border:1px solid #eee;border-radius:12px;padding:16px",
            "element": {"line": 3, "tag": tag, "classes": [cls], "inlineStyle": "",
                        "textSample": text, "childShape": []},
            "count": count, "lines": [3], "classes": [cls], "family": family}


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
                [_unit("x")], findings,
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
                {"components": []}, [_unit("x")], [], ds_lint.contract_index({"components": []}))
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


# ── Off-system UI: found by styling, judged against the whole vocabulary ────

class OffSystemJudgment(unittest.TestCase):
    """The classifier guards against INVENTED components, so what it judges is
    found from what PAINTS an element, never from naming or BEM structure (an
    invented component follows neither), and each one is judged against every
    design-system component of its family, never a top-N guess. With the
    classifier off none of this runs: the linter is unchanged."""

    DS_CLASSES = {"card", "btn", "card__title"}
    CONTRACT = {"id": "ds1", "components": [
        {"id": "card", "role": "container", "name": "Card", "title": "Cards",
         "oneLine": "Card .card [--plain|--filled]",
         "description": "Groups related content and actions on one bounded surface."},
        {"id": "btn", "role": "control", "name": "Button", "oneLine": "The primary action"},
        {"id": "chip", "role": "indicator", "name": "Chip", "oneLine": "A small label"},
        {"id": "h1", "role": "text", "name": "Heading", "oneLine": "Page title"},
    ] + [{"id": "box-%d" % i, "role": "container", "oneLine": "Box %d" % i} for i in range(80)]}

    @classmethod
    def setUpClass(cls):
        cls.index = ds_lint.contract_index(cls.CONTRACT)

    def units(self, html, shared=()):
        rules = [("<style>", sel, body) for sel, body in
                 ds_lint.parse_css_rules(ds_lint.extract_style_blocks(html))]
        rules += [("site.css", sel, body) for sel, body in shared]
        return ds_lint.off_system_units("p.html", html, rules, self.DS_CLASSES, self.index)

    def test_found_by_what_paints_it_not_by_its_name(self):
        html = ("<style>.sidebar > div{background:#fff;border-radius:12px}"
                "#hero-box{box-shadow:0 2px 4px #0003}"
                ".intro p{color:#333;line-height:1.5}"
                "body{background:#fafafa}.gutter{margin-left:12px}</style>"
                "<div class='sidebar'><div>Inbox</div></div>"
                "<section id='hero-box'><h2>Hi</h2></section>"
                "<span style='border:1px solid #ccc;border-radius:999px;padding:2px 8px'>New</span>"
                "<div class='intro'><p>text</p></div><div class='gutter'>x</div>")
        got = {u["source"] for u in self.units(html)}
        self.assertEqual(got, {"<style> .sidebar > div", "<style> #hero-box", "inline style on <span>"},
                         "text-only, layout-only and page background are not UI")

    def test_the_prototypes_own_css_files_count_too(self):
        html = "<div class='promo-tile'>Sale</div>"
        got = self.units(html, shared=[(".promo-tile", "border:1px solid #ddd;border-radius:8px")])
        self.assertEqual([u["source"] for u in got], ["site.css .promo-tile"])

    def test_design_system_classes_stay_with_the_deterministic_rules(self):
        html = ("<style>.page .card{border:2px solid red}.wrap > div{background:#fff}</style>"
                "<div class='page'><div class='card'>a</div></div>"
                "<div class='wrap'><div class='card'>b</div></div>")
        self.assertEqual(self.units(html), [],
                         "a DS class in the selector, or a DS component as the element, is not invented UI")

    def test_one_question_per_styling_source_however_many_elements_it_paints(self):
        html = "<style>.row{border-bottom:1px solid #eee}</style>" + "".join(
            "<div class='row'>%d</div>" % i for i in range(20))
        (u,) = self.units(html)
        self.assertEqual(u["count"], 20)

    def _ask(self, units, stage1, stage2=("card", 0.97)):
        asked = []
        real = (jev.ask, jev.enabled, jev.available)
        jev.enabled, jev.available = (lambda: True), (lambda *a, **k: True)

        def fake(state, questions, **kw):
            asked.append((state, questions))
            out = {}
            for qid, q in questions.items():
                if "ds-copy" in q["criteria"]:
                    out[qid] = _recorded(stage1[0], stage1[1])
                else:
                    out[qid] = _recorded(stage2[0], stage2[1])
            return out
        jev.ask = fake
        findings = []
        try:
            status = ds_lint.run_jev_pass(self.CONTRACT, units, findings, self.index)
        finally:
            jev.ask, jev.enabled, jev.available = real
        return status, findings, asked

    def test_every_unit_is_asked_with_no_cap(self):
        units = [_unit("u%d" % i) for i in range(40)]
        status, _f, asked = self._ask(units, ("layout", 0.99))
        self.assertEqual(status["asked"], 40)
        questions = [q for _s, qs in asked for q in qs.values()]
        self.assertEqual(len(questions), 40)
        for state, qs in asked:
            self.assertIn("Card (.card)", state, "the vocabulary travels once per request, in state")
            self.assertLessEqual(len(qs), ds_lint.JUDGE_MAX_QUESTIONS_PER_REQUEST)
            for q in qs.values():
                self.assertEqual(set(q["criteria"]), {"ds-copy", "new-ui", "layout"})

    def test_which_component_is_asked_against_the_whole_family(self):
        _s, findings, asked = self._ask([_unit("promo-tile")], ("ds-copy", 0.97))
        stage2 = [q for _s2, qs in asked for q in qs.values() if "ds-copy" not in q["criteria"]]
        self.assertEqual(len(stage2), 1)
        opts = set(stage2[0]["criteria"])
        self.assertEqual(len(opts), 83, "card + chip + all 80 boxes + none-of-these, no top-N")
        self.assertNotIn("btn", opts, "a control is a different family")
        self.assertNotIn("h1", opts)
        state2 = [st for st, qs in asked if "ds-copy" not in next(iter(qs.values()))["criteria"]][0]
        self.assertEqual(state2.count("Groups related content and actions on one bounded surface."), 1,
                         "the authors' description travels once, in the state")
        self.assertEqual(stage2[0]["criteria"]["card"], "Cards (.card)", "options are short titles")
        self.assertNotIn("Groups related", json.dumps(stage2[0]["criteria"]))
        (f,) = findings
        self.assertEqual((f["rule"], f["severity"], f["component"]), ("invented-component", "error", "card"))

    def test_a_copy_whose_component_is_unclear_is_a_warning(self):
        _s, findings, _a = self._ask([_unit("promo-tile")], ("ds-copy", 0.97), ("card", 0.4))
        (f,) = findings
        self.assertEqual((f["rule"], f["severity"], f["component"]), ("invented-component", "warn", None))

    def test_new_ui_is_a_warning_and_layout_or_unsure_adds_nothing(self):
        _s, findings, _a = self._ask([_unit("meter")], ("new-ui", 0.97))
        self.assertEqual([(f["rule"], f["severity"]) for f in findings], [("off-system-component", "warn")])
        for verdict in (("layout", 0.99), ("ds-copy", 0.5), ("new-ui", 0.6)):
            self.assertEqual(self._ask([_unit("x")], verdict)[1], [], verdict)

    def test_every_answer_is_logged_and_returned(self):
        logged = []
        import typed_judge as tj
        real = tj.shadow_log
        tj.shadow_log = logged.append
        try:
            status, _f, _a = self._ask([_unit("promo-tile"), _unit("wrap")], ("ds-copy", 0.97))
        finally:
            tj.shadow_log = real
        kinds = sorted(r["kind"] for r in logged)
        self.assertEqual(kinds, ["ds_component", "ds_component", "ds_origin", "ds_origin"])
        row = [r for r in logged if r["kind"] == "ds_origin"][0]
        for key in ("source", "page", "lines", "answer", "probabilities", "confidence", "band", "context"):
            self.assertIn(key, row)
        self.assertEqual(len(status["judged"]), 2)
        self.assertEqual(status["judged"][0]["component"]["answer"], "card")

    def test_without_the_classifier_the_linter_output_is_unchanged(self):
        """--jev off: no off-system detection runs, nothing is added."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "design-systems" / "ds1").mkdir(parents=True)
            (root / "design-systems" / "ds1" / "styles.css").write_text(".card{padding:8px;border:1px solid #ddd}")
            (root / "source" / "main").mkdir(parents=True)
            (root / "source" / "main" / "index.html").write_text(
                "<style>.tile{border:1px solid #eee;border-radius:9px}</style>"
                "<div class='tile' style='box-shadow:0 1px 2px #0002'>x</div>")
            import io
            import contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                ds_lint.main(["--project-root", tmp, "--prototype", "main", "--json"])
            report = json.loads(buf.getvalue())
        self.assertNotIn("jev", report)
        self.assertFalse(any(f["rule"] in ("off-system-component",) or f.get("matchedBy") == "jev"
                             for f in report["findings"]))


# ── P5 - no preamble divergence ─────────────────────────────────────────────

class P5PreambleParity(unittest.TestCase):
    """The preamble is what every agent reads. An accidental second copy of a
    rule there, phrased for the typed path, is how the two paths start
    building differently."""

    TIERS = ("setup", "scoped", "normal", "leaf")
    STATES = ({"text": "TypeSafe Jev", "image": None},
              {"text": None, "image": "Cloudflare Clef"},
              {"text": "OpenAI Decisions", "image": "Cloudflare Clef"})

    def test_the_toggles_change_exactly_one_block(self):
        for tier in self.TIERS:
            off = capabilities.capabilities_preamble(tier=tier, jev=False)
            for state in self.STATES:
                on = capabilities.capabilities_preamble(tier=tier, jev=state)
                block = capabilities.typed_judgment_block(state)
                self.assertEqual(on.replace(block, "", 1), off,
                                 "tier %s diverges beyond the one block for %s" % (tier, state))

    def test_the_leaf_tier_never_carries_it(self):
        """A leaf builder picks no direction and runs no requirement QA."""
        for state in self.STATES:
            on = capabilities.capabilities_preamble(tier="leaf", jev=state)
            self.assertNotIn("Typed judgment is available", on)

    def test_the_interactive_tiers_do_carry_it(self):
        for tier in ("setup", "scoped", "normal"):
            self.assertIn(capabilities.JEV_FAST_PATH_STUB,
                          capabilities.capabilities_preamble(tier=tier, jev=True)
                          .replace(capabilities.typed_judgment_block(
                              capabilities._typed_judgment_state() or {"text": "TypeSafe Jev", "image": None}),
                              capabilities.JEV_FAST_PATH_STUB))
            for state in self.STATES:
                self.assertIn(capabilities.typed_judgment_block(state),
                              capabilities.capabilities_preamble(tier=tier, jev=state))

    def test_the_block_states_the_limits_that_make_it_safe(self):
        for state in self.STATES:
            stub = capabilities.typed_judgment_block(state)
            for rule in ("count", "colour", "image", "ADDS", "CONSIDER", "/__judge"):
                self.assertIn(rule, stub, "the preamble block drops the %r rule for %s" % (rule, state))

    def test_the_block_names_each_judge_and_says_what_it_covers(self):
        both = capabilities.typed_judgment_block(self.STATES[2])
        self.assertIn("text checks -> OpenAI Decisions; visual checks -> Cloudflare Clef", both)
        self.assertIn("never Read the PNG yourself", both)
        text_only = capabilities.typed_judgment_block(self.STATES[0])
        self.assertIn("visual checks -> none", text_only)
        self.assertIn("NO image input", text_only)
        image_only = capabilities.typed_judgment_block(self.STATES[1])
        self.assertIn("text checks -> none", image_only)
        self.assertNotIn("NO image input", image_only)

    def test_the_block_is_absent_without_a_judge(self):
        """Both switches on, no key anywhere: no block, because a block naming
        an endpoint that will 503 is worse than none."""
        import os
        saved = (typed_judge.MEDIA_CONFIG_PATH, typed_judge.COMPACT_CONFIG_PATH)
        env = {k: os.environ.pop(k) for k in list(typed_judge.ENV_KEYS.values())
               + list(typed_judge.ENDPOINT_ENV.values()) if k in os.environ}
        with tempfile.TemporaryDirectory() as tmp:
            typed_judge.MEDIA_CONFIG_PATH = os.path.join(tmp, "m.json")
            typed_judge.COMPACT_CONFIG_PATH = os.path.join(tmp, "c.json")
            Path(typed_judge.COMPACT_CONFIG_PATH).write_text(
                json.dumps({"jevJudge": True, "typedJudgeVisual": True}))
            try:
                self.assertFalse(capabilities._jev_enabled())
                Path(typed_judge.MEDIA_CONFIG_PATH).write_text(
                    json.dumps({"cloudflare": {"api_key": "cf", "account_id": "a"}}))
                self.assertEqual(capabilities._typed_judgment_state(),
                                 {"text": "Cloudflare Clef Flash", "image": "Cloudflare Clef"})
                Path(typed_judge.COMPACT_CONFIG_PATH).write_text(json.dumps({"jevJudge": False}))
                self.assertIsNone(capabilities._typed_judgment_state())
            finally:
                typed_judge.MEDIA_CONFIG_PATH, typed_judge.COMPACT_CONFIG_PATH = saved
                os.environ.update(env)


# ── P8 - typed visual checks: literal claims, and shadow is inert ──────────

class P8VisualChecks(unittest.TestCase):
    """The typed judge is a classifier, so it only ever gets LITERAL claims
    about the exact evidence each needs (a capture, cropped to one element).
    The --judge prose is never handed to it. Shadow records the answers and
    changes nothing: same verdict, reasons, exit code and LLM verdict, for every
    pixel verdict, every recorded LLM reply and every typed answer. Flag may
    only ADD findings."""

    PIXEL = ("pass", "static", "no-reaction", "error", "blank")
    LLM = {
        "confirms": {"available": True, "ok": True, "reasoning": "the menu opens"},
        "rejects": {"available": True, "ok": False, "reasoning": "nothing opens"},
        "inconclusive": {"available": True, "ok": None, "message": "reply was not JSON"},
        "unavailable": {"available": False, "ok": None, "message": "no LLM endpoint"},
    }
    TYPED = {"pass": 0.97, "fail": 0.03, "unsure": 0.52, "absent": None}
    CHECKS = [
        {"id": "menu_open", "statement": "A dropdown menu is open below the Account button.",
         "at": "after:click_account", "selector": "#menu"},
        {"id": "ripple", "statement": "Image 2 shows a ripple around the button that image 1 does not.",
         "at": "after:click_account", "compare": "before:click_account"},
    ]

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="p8-")
        frames = []
        for i in range(4):
            path = Path(cls.tmp) / ("f%d.png" % i)
            path.write_bytes(typed_judge.solid_png((40 * i, 80, 120), size=200))
            frames.append(str(path))
        box = {"x": 20, "y": 30, "width": 60, "height": 40}
        cls.report = {"idleFrames": [{"t": 0.0, "path": frames[0], "boxes": {"#menu": None}},
                                     {"t": 0.7, "path": frames[1], "diffFromPrev": 0.2,
                                      "boxes": {"#menu": None}}],
                      "interactions": [{"step": "click_account", "diff": 0.3,
                                        "beforePath": frames[2], "afterPath": frames[3],
                                        "beforeBoxes": {"#menu": None},
                                        "afterBoxes": {"#menu": box}}]}

    def _args(self, mode, checks=None, judge="a menu opens"):
        from types import SimpleNamespace
        return SimpleNamespace(judge=judge, typed_judge=mode, judge_project="p8",
                               viewport=(200, 200),
                               parsed_checks=visual_qa.parse_checks(checks if checks is not None
                                                                    else self.CHECKS))

    def _judge(self, kind, calls=None):
        def fn(state, questions, **kw):
            if calls is not None:
                calls.append((state, questions, kw))
            if self.TYPED[kind] is None:
                raise typed_judge.JudgeUnavailable("no image judge", reason="no-image-judge")
            self.assertEqual(kw["tier"], "image")
            qid = next(iter(questions))
            return {"answers": {qid: {"type": "noul", "noul": self.TYPED[kind]}},
                    "provider": "clef", "model": "clef",
                    "thresholds": typed_judge.thresholds("frame_check", "clef")}
        return fn

    def _run(self, pixel, llm, typed, mode, calls=None, checks=None):
        import copy
        report = copy.deepcopy(self.report)
        reasons = ["pixel reason"]
        logged = []
        judge_fn = self._judge(typed, calls)
        verdict = visual_qa.apply_frame_judges(
            report, pixel, reasons, self.tmp, self._args(mode, checks),
            llm_judge=lambda r, o, a: dict(self.LLM[llm]),
            checks_fn=lambda rep, c, rj, m, w: visual_qa.run_visual_checks(rep, c, rj, m, w, judge_fn),
            shadow_log=logged.append)
        return verdict, reasons, report, logged

    # The questions themselves ---------------------------------------------

    def test_intent_restated_is_rejected_not_asked(self):
        checks, rejected = visual_qa.parse_checks([
            {"statement": "The animation works as expected.", "at": "page"},
            {"statement": "The menu renders correctly.", "at": "page"},
            {"statement": "The effect is achieved.", "at": "page"},
            {"statement": "How many cards are shown?", "at": "page"},
            {"statement": "A menu is open.", "at": "somewhere"},
            {"statement": "A ripple appears.", "at": "after:x", "compare": "before:x"},
            {"statement": "The correct answer is highlighted.", "at": "after:submit"},
        ])
        self.assertEqual([c["statement"] for c in checks], ["The correct answer is highlighted."])
        self.assertEqual(len(rejected), 6)
        self.assertTrue(all(r["reason"] for r in rejected))

    def test_each_check_gets_only_its_own_images_cropped_to_its_element(self):
        calls = []
        _v, _r, report, _l = self._run("pass", "confirms", "pass", "shadow", calls)
        self.assertEqual(len(calls), 2, "one request per check")
        state, questions, kw = calls[0]
        self.assertEqual(list(questions), ["menu_open"])
        self.assertEqual(questions["menu_open"]["instructions"],
                         "A dropdown menu is open below the Account button.")
        self.assertEqual(len(kw["images"]), 1)
        crop = kw["images"][0]
        self.assertIsInstance(crop, bytes, "a selector check sends the CROP, not the frame")
        w, h = typed_judge.image_size(crop, "png")
        self.assertLess(w * h, 200 * 200 / 2)
        _s, q2, kw2 = calls[1]
        self.assertEqual([i["path"] for i in kw2["images"]],
                         [self.report["interactions"][0]["beforePath"],
                          self.report["interactions"][0]["afterPath"]],
                         "compare is image 1, at is image 2")
        self.assertEqual(report["typedChecks"]["summary"]["confidentPass"], 2)

    def test_page_checks_are_built_from_shapes_not_written(self):
        checks, rejected = visual_qa.parse_checks([
            {"id": "menu", "shape": "shows", "x": "a dropdown menu below the Account button",
             "at": "after:click_account", "selector": "#menu"},
            {"id": "opened", "shape": "changed", "x": "an open menu",
             "at": "after:click_account", "compare": "before:click_account"},
            {"id": "toggle", "shape": "which", "list": "control_state", "x": "the Dark mode toggle",
             "expect": "on", "at": "after:click_account"},
            {"id": "bad_expect", "shape": "which", "list": "control_state", "x": "the toggle",
             "expect": "sideways", "at": "page"},
            {"id": "needs_two", "shape": "changed", "x": "an open menu", "at": "page"},
        ])
        self.assertEqual([c["id"] for c in checks], ["menu", "opened", "toggle"])
        self.assertEqual(checks[0]["question"]["instructions"],
                         "The image shows a dropdown menu below the Account button.")
        self.assertEqual(checks[1]["question"]["instructions"],
                         "Image 2 shows an open menu that image 1 does not.")
        self.assertEqual(checks[2]["question"]["type"], "choice")
        self.assertEqual({r["id"] for r in rejected}, {"bad_expect", "needs_two"})

    def test_a_choice_check_is_graded_against_expect(self):
        import copy
        checks = [{"id": "toggle", "shape": "which", "list": "control_state", "x": "the Dark mode toggle",
                   "expect": "on", "at": "after:click_account"}]

        def judge(state, questions, **kw):
            return {"answers": {"toggle": {"choice": "off", "confidence": 0.96,
                                           "probabilities": {"off": 0.96, "on": 0.04}}},
                    "provider": "clef", "model": "clef",
                    "thresholds": typed_judge.thresholds("frame_check", "clef")}
        report = copy.deepcopy(self.report)
        args = self._args("flag", checks)
        visual_qa.apply_frame_judges(
            report, "pass", [], self.tmp, args, llm_judge=lambda r, o, a: dict(self.LLM["confirms"]),
            checks_fn=lambda rep, c, rj, m, w: visual_qa.run_visual_checks(rep, c, rj, m, w, judge),
            shadow_log=lambda e: None)
        (row,) = report["typedChecks"]["checks"]
        self.assertEqual((row["answer"], row["passed"]), ("off", False))
        self.assertIn("judge said off", report["findings"][0]["message"])

    def test_the_page_declares_image_checks_through_alt_text(self):
        class FakePage:
            def evaluate(self, js):
                return [{"alt": "a red delivery van outside a bakery", "selector": "#hero"},
                        {"alt": "Logo", "selector": "#logo"},
                        {"alt": "", "selector": "#spacer"},
                        {"alt": "a red delivery van outside a bakery", "selector": "#dup"},
                        {"alt": "a blue ceramic mug", "selector": "body > img:nth-of-type(2)"}]
        checks, rejected = visual_qa.page_declared_checks(FakePage())
        self.assertEqual([(c["x"], c["selector"]) for c in checks],
                         [("a red delivery van outside a bakery", "#hero"),
                          ("a blue ceramic mug", "body > img:nth-of-type(2)")])
        self.assertEqual(checks[0]["question"]["instructions"],
                         "The image shows a red delivery van outside a bakery.")
        self.assertTrue(all(c["declaredBy"] == "img alt" and c["at"] == "page" for c in checks))
        self.assertEqual(rejected, [])

    def test_a_missing_element_is_reported_without_a_model_call(self):
        calls = []
        checks = [{"id": "menu_idle", "statement": "A dropdown menu is open.",
                   "at": "idle:start", "selector": "#menu"}]
        _v, _r, report, _l = self._run("pass", "confirms", "pass", "flag", calls, checks)
        self.assertEqual(calls, [])
        self.assertEqual(report["typedChecks"]["checks"][0]["status"], "element-missing")
        self.assertEqual([f["check"] for f in report["findings"]], ["menu_idle"])

    def test_no_checks_means_no_typed_question(self):
        calls = []
        _v, _r, report, _l = self._run("pass", "confirms", "pass", "flag", calls, [])
        self.assertEqual(calls, [])
        self.assertNotIn("typedChecks", report)

    def test_checks_run_without_any_judge_prose(self):
        import copy
        report = copy.deepcopy(self.report)
        args = self._args("shadow")
        args.judge = None
        v = visual_qa.apply_frame_judges(
            report, "pass", [], self.tmp, args,
            checks_fn=lambda rep, c, rj, m, w: visual_qa.run_visual_checks(rep, c, rj, m, w, self._judge("pass")),
            shadow_log=lambda e: None)
        self.assertEqual(v, "pass")
        self.assertEqual(report["typedChecks"]["summary"]["confidentPass"], 2)
        self.assertNotIn("judge", report)

    # Posture ------------------------------------------------------------------

    def test_shadow_changes_nothing(self):
        for pixel in self.PIXEL:
            for llm in self.LLM:
                for typed in self.TYPED:
                    off = self._run(pixel, llm, typed, None)
                    shadow = self._run(pixel, llm, typed, "shadow")
                    case = (pixel, llm, typed)
                    self.assertEqual(shadow[0], off[0], case)
                    self.assertEqual(visual_qa.exit_code(shadow[0]), visual_qa.exit_code(off[0]), case)
                    self.assertEqual(shadow[1], off[1], case)
                    self.assertEqual(shadow[2]["judge"].get("ok"), off[2]["judge"].get("ok"), case)
                    self.assertNotIn("findings", shadow[2], case)
                    self.assertIn("typedChecks", shadow[2], case)

    def test_flag_adds_findings_and_nothing_else(self):
        for pixel in self.PIXEL:
            for llm in self.LLM:
                for typed in self.TYPED:
                    off = self._run(pixel, llm, typed, None)
                    flag = self._run(pixel, llm, typed, "flag")
                    case = (pixel, llm, typed)
                    self.assertEqual(flag[0], off[0], case)
                    self.assertEqual(flag[1], off[1], case)
                    findings = flag[2].get("findings") or []
                    self.assertEqual(len(findings), 2 if typed == "fail" else 0, case)
                    self.assertTrue(all(f["rule"] == "typed-judge" for f in findings))

    def test_answers_are_logged_unpaired_for_labelling(self):
        """The LLM frame judge answers a different question (the whole prose
        effect), so a check is never logged as agreeing or disagreeing with it."""
        _v, _r, _report, logged = self._run("pass", "confirms", "fail", "shadow")
        self.assertEqual(len(logged), 2)
        self.assertTrue(all(e["llmOk"] is None and e["kind"] == "frame_check" for e in logged))

    def test_only_a_calibrated_trust_pass_on_every_check_in_flag_mode_skips_the_llm(self):
        def trusted(state, questions, **kw):
            qid = next(iter(questions))
            th = dict(typed_judge.thresholds("frame_check", "clef"), trustPass=True)
            return {"answers": {qid: {"type": "noul", "noul": 0.99}},
                    "provider": "clef", "model": "clef", "thresholds": th}
        for mode, expect_calls in (("shadow", 1), ("flag", 0)):
            calls = []

            def llm(r, o, a):
                calls.append(1)
                return dict(self.LLM["confirms"])
            import copy
            report = copy.deepcopy(self.report)
            verdict = visual_qa.apply_frame_judges(
                report, "pass", [], self.tmp, self._args(mode), llm_judge=llm,
                checks_fn=lambda rep, c, rj, m, w: visual_qa.run_visual_checks(rep, c, rj, m, w, trusted),
                shadow_log=lambda e: None)
            self.assertEqual(len(calls), expect_calls, mode)
            self.assertEqual(verdict, "pass")


if __name__ == "__main__":
    unittest.main()

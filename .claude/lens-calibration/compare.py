#!/usr/bin/env python3
"""compare.py - lens calibration confusion-matrix reporter.

Reads each fixture's expected.json + the verdicts the 3 lenses wrote
(<lens>-verdict.json), compares verdict-vs-expected, emits a per-lens
confusion matrix and per-fixture detail.

Usage:
    python3 .claude/lens-calibration/compare.py            # default fixtures dir
    python3 .claude/lens-calibration/compare.py <dir>      # custom fixtures dir

Exit codes:
    0 - calibration clean (≥9/10 correct per lens)
    1 - calibration regressed (one or more lenses scored <9/10)
    2 - fixture or verdict file missing
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from typing import Optional


# ── Constants ─────────────────────────────────────────────────────────────

LENSES = ("craft", "aesthetic", "concept")
SHIPPABLE_THRESHOLD = 9   # min correct / 10 fixtures per lens to call clean


# ── ANSI helpers (no deps) ────────────────────────────────────────────────

class C:
    GREEN  = "\033[92m"
    RED    = "\033[91m"
    YELLOW = "\033[93m"
    DIM    = "\033[2m"
    BOLD   = "\033[1m"
    END    = "\033[0m"

def green(s):  return f"{C.GREEN}{s}{C.END}"
def red(s):    return f"{C.RED}{s}{C.END}"
def yellow(s): return f"{C.YELLOW}{s}{C.END}"
def dim(s):    return f"{C.DIM}{s}{C.END}"
def bold(s):   return f"{C.BOLD}{s}{C.END}"


# ── Core comparison logic ────────────────────────────────────────────────

def load_json(path: str) -> Optional[dict]:
    if not os.path.isfile(path):
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def evaluate_verdict(expected: dict, actual: dict) -> tuple[str, str]:
    """Return (status, note) where status ∈ {match, false-pass, false-fail, skip-ok, skip-bad, missing}.

    "missing" is reserved for "the lens didn't produce a verdict file at all"
    (regardless of what was expected - we can't tell pass-skip-or-no-run when
    the file is absent). "skip-bad" fires only when the file exists but says
    `fail`/`pass` when an n/a was expected.
    """
    exp_v = expected.get("verdict")        # "pass" | "fail" | "n/a"

    # File missing entirely - we cannot infer whether the lens ran-and-skipped
    # or simply didn't run. Report as missing in either case.
    if actual is None:
        return ("missing", "no verdict file produced")

    act_v = actual.get("verdict")
    act_skipped = bool(actual.get("skipped"))

    if exp_v == "n/a":
        # Lens was expected to skip (per its playbook's skip rules).
        # A passing-with-skipped=true verdict is the canonical "skipped" shape;
        # a plain pass is also acceptable (lens chose to score and passed).
        if act_skipped or act_v == "pass":
            return ("skip-ok", "lens skipped as expected" if act_skipped else "lens scored and passed (acceptable)")
        else:
            return ("skip-bad", f"expected skip; got verdict='{act_v}'")

    if exp_v == act_v:
        return ("match", "verdict matches expected")
    if exp_v == "pass" and act_v == "fail":
        return ("false-fail", actual.get("reason") or "lens flagged a clean fixture")
    if exp_v == "fail" and act_v == "pass":
        return ("false-pass", "lens missed a failure mode")
    return ("missing", f"unparseable: expected={exp_v!r} actual={act_v!r}")


def walk_fixtures(fixtures_dir: str) -> list[tuple[str, dict, dict]]:
    """Return a list of (fixture_id, expected_dict, verdicts_dict) tuples.

    verdicts_dict maps "craft" / "aesthetic" / "concept" → loaded verdict
    dict (or None if absent on disk).
    """
    out = []
    for entry in sorted(os.listdir(fixtures_dir)):
        fdir = os.path.join(fixtures_dir, entry)
        if not os.path.isdir(fdir):
            continue
        expected = load_json(os.path.join(fdir, "expected.json"))
        if not expected:
            print(red(f"  ⚠ missing expected.json in {entry}; skipping"), file=sys.stderr)
            continue
        verdicts = {}
        for lens in LENSES:
            verdicts[lens] = load_json(os.path.join(fdir, f"{lens}-verdict.json"))
        out.append((entry, expected, verdicts))
    return out


def compute_per_lens_summary(rows: list[tuple[str, dict, dict]]) -> dict:
    """Compute per-lens counts: {correct, false_pass, false_fail, missing, skip_ok, skip_bad}."""
    summary = {lens: defaultdict(int) for lens in LENSES}
    detail  = {lens: [] for lens in LENSES}   # list of (fixture_id, status, note)

    for fixture_id, expected, verdicts in rows:
        for lens in LENSES:
            exp_for_lens = (expected.get(lens) or {})
            # IMPORTANT: pass the verdict dict OR None directly - don't
            # substitute `{}` for None, or evaluate_verdict's missing-file
            # branch won't fire and a missing verdict gets misreported as
            # skip-bad on n/a-expected fixtures.
            act_for_lens = verdicts.get(lens)
            status, note = evaluate_verdict(exp_for_lens, act_for_lens)
            summary[lens][status] += 1
            detail[lens].append((fixture_id, status, note))

    return {"summary": summary, "detail": detail, "total": len(rows)}


# ── Report rendering ──────────────────────────────────────────────────────

def render_per_lens_summary(report: dict) -> None:
    print(bold("\nPER-LENS SUMMARY"))
    total = report["total"]
    for lens in LENSES:
        s = report["summary"][lens]
        correct = s["match"] + s["skip-ok"]   # both count as correct
        score   = f"{correct}/{total}"
        wrong   = []
        if s["false-pass"]:  wrong.append(red(f"{s['false-pass']} false-pass"))
        if s["false-fail"]:  wrong.append(red(f"{s['false-fail']} false-fail"))
        if s["skip-bad"]:    wrong.append(yellow(f"{s['skip-bad']} skip-bad"))
        if s["missing"]:     wrong.append(red(f"{s['missing']} missing"))
        score_label = green(score) if correct >= SHIPPABLE_THRESHOLD else red(score)
        wrong_label = f"  ({'; '.join(wrong)})" if wrong else green("  ✓ all correct")
        print(f"  {lens:14s}: {score_label} correct{wrong_label}")


def render_per_fixture_detail(report: dict) -> None:
    print(bold("\nPER-FIXTURE DETAIL"))
    # Build per-fixture lines
    by_fixture = defaultdict(dict)
    for lens in LENSES:
        for fixture_id, status, note in report["detail"][lens]:
            by_fixture[fixture_id][lens] = (status, note)
    for fixture_id in sorted(by_fixture):
        per_lens = by_fixture[fixture_id]
        any_wrong = any(s in ("false-pass", "false-fail", "skip-bad", "missing")
                         for s, _ in per_lens.values())
        header = red(fixture_id) if any_wrong else dim(fixture_id)
        print(f"  {header}")
        for lens in LENSES:
            status, note = per_lens.get(lens, ("missing", "no row"))
            if status == "match":
                glyph = green("✓"); label = "match"
            elif status == "skip-ok":
                glyph = green("·"); label = "skipped (ok)"
            elif status == "false-pass":
                glyph = red("✗"); label = "FALSE-PASS"
            elif status == "false-fail":
                glyph = red("✗"); label = "FALSE-FAIL"
            elif status == "skip-bad":
                glyph = yellow("?"); label = "should-have-skipped"
            else:
                glyph = red("·"); label = "MISSING VERDICT"
            print(f"    {glyph}  {lens:10s} {label:24s}  {dim(note)}")


def render_recommended_actions(report: dict) -> int:
    """Return exit code: 0 if clean, 1 if regressed, 2 if missing fixtures."""
    print(bold("\nRECOMMENDED ACTIONS"))
    any_missing = False
    any_regressed = False
    actions: list[str] = []
    for lens in LENSES:
        s = report["summary"][lens]
        if s["missing"]:
            actions.append(
                f"  • {red(lens)}: {s['missing']} fixture(s) have no verdict file - "
                f"the lens didn't run or wrote to the wrong path. Re-dispatch.")
            any_missing = True
        if s["false-pass"]:
            actions.append(
                f"  • {red(lens)}: {s['false-pass']} false-pass(es) - the lens is too "
                f"lenient. Sharpen the rubric for the failing check(s). Re-run.")
            any_regressed = True
        if s["false-fail"]:
            actions.append(
                f"  • {yellow(lens)}: {s['false-fail']} false-fail(s) - the lens is "
                f"too strict. Loosen the borderline-case wording. Re-run.")
            any_regressed = True
        if s["skip-bad"]:
            actions.append(
                f"  • {yellow(lens)}: {s['skip-bad']} skip(s) wrong - the lens should "
                f"have skipped per its rules but didn't. Check the skip-condition wording.")
            any_regressed = True

    if not actions:
        print(green("  ✓ All lenses scored ≥9/10. Calibration is shippable."))
        return 0
    for a in actions:
        print(a)
    if any_missing:
        return 2
    return 1 if any_regressed else 0


# ── Main ──────────────────────────────────────────────────────────────────

def main(argv: list[str]) -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    fixtures_dir = argv[1] if len(argv) > 1 else os.path.join(here, "fixtures")
    if not os.path.isdir(fixtures_dir):
        print(red(f"fixtures dir not found: {fixtures_dir}"), file=sys.stderr)
        return 2

    print(bold("\n═══ Lens calibration report ═══"))
    print(dim(f"  fixtures: {fixtures_dir}"))

    rows = walk_fixtures(fixtures_dir)
    if not rows:
        print(red("no fixtures found"), file=sys.stderr)
        return 2

    report = compute_per_lens_summary(rows)
    render_per_lens_summary(report)
    render_per_fixture_detail(report)
    return render_recommended_actions(report)


if __name__ == "__main__":
    sys.exit(main(sys.argv))

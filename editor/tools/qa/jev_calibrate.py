#!/usr/bin/env python3
"""jev_calibrate.py - set the Jev confidence thresholds from YOUR data, not from the docs.

docs/features/jev-integration.md Phase 4. The step that is easy to skip and
expensive to skip: schema-valid output is not the same as a correct decision.
Until this has run, every consumer sits behind the shipped pre-calibration
defaults and the posture is FLAG, NEVER BLOCK.

It is cheap here precisely because every input in the Jev integration is text -
you can re-run the whole labelled set for pennies. The rejected image path had
no cheap version of this step, which is part of why it is out.

WHAT IT NEEDS. A labelled set: real Woven cases whose right answer you already
know. Build one from ~30 prototypes with known verdicts - a DS drift you fixed,
a requirement gap you caught by hand - and write them out as:

    {"cases": [
      {"kind": "ds_role",
       "state": "<the contract, or the artefact>",
       "questions": {"q": {"type": "choice", "criteria": {...}, "instructions": "..."}},
       "expected": {"q": "card"}},
      {"kind": "requirement_item",
       "state": "<the built artefact>",
       "questions": {"q": {"type": "noul", "instructions": "<checklist item>"}},
       "expected": {"q": true}}
    ]}

`expected` is the id for a choice and a boolean for a noul. Cases are grouped by
`kind` and a threshold is fitted PER KIND - a DS role inference and a
requirement check do not deserve the same floor, and a finding that GATES
deserves a higher one than a report line.

WHAT IT FITS. For each kind, the lowest confidence floor at which PRECISION on
the acted-on verdicts reaches the target. Precision, not accuracy: a gate exists
to catch rare failures, so the number that matters is how many of its alarms are
real. Raising the floor trades recall for precision; the escalate band catches
what the floor drops, so that trade is cheap.

    python3 editor/tools/qa/jev_calibrate.py --labels cases.json [--target 0.95] [--write]

Stdlib only, Python 3.9-safe.
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
_EDITOR = os.path.dirname(os.path.dirname(_HERE))
for _p in (_HERE, _EDITOR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import jev  # noqa: E402

# Per-kind precision target. A kind whose verdict can PROMOTE a finding to
# error-severity has to clear a higher bar than one that only ranks a shortlist
# nobody is gated by. Anything not named here uses --target.
DEFAULT_TARGETS = {
    "ds_role": 0.95,           # promotes an info finding to a gating error
    "requirement_item": 0.90,  # writes a line into a report a human reads
    "direction_axis": 0.70,    # narrows a shortlist; a wrong rank costs nothing
}
# Candidate floors, coarse on purpose: fitting to three decimal places on 30
# cases is fitting to noise.
_GRID = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]


def _verdict(answer, noul_floor):
    # type: (Any, float) -> Tuple[Optional[Any], Optional[float]]
    """(what the judge said, how confident it was), normalised across types."""
    ranked = jev.choice_ranked(answer, 1)
    if ranked:
        return ranked[0][0], (jev.confidence(answer) or ranked[0][1])
    noul = jev.noul_value(answer)
    if noul is None:
        return None, None
    # A noul's own distance from the midpoint IS its confidence: 0.98 and 0.02
    # are both decisive, 0.51 is not.
    return (noul >= noul_floor), abs(noul - 0.5) * 2.0


def run_cases(cases, model=jev.DEFAULT_MODEL):
    # type: (List[Dict[str, Any]], str) -> List[Dict[str, Any]]
    """One request per case. Failures are RECORDED, never fatal: a calibration
    run that dies on case 7 of 30 has told you nothing."""
    rows = []  # type: List[Dict[str, Any]]
    for i, case in enumerate(cases):
        kind = str(case.get("kind") or "default")
        floor = jev.thresholds(kind)["noul"]
        try:
            answers = jev.ask(case["state"], case["questions"], model=model)
        except Exception as exc:
            rows.append({"case": i, "kind": kind, "error": str(exc)[:200]})
            continue
        for qid, expected in (case.get("expected") or {}).items():
            said, conf = _verdict(answers.get(qid), floor)
            rows.append({"case": i, "kind": kind, "question": qid,
                         "expected": expected, "said": said, "confidence": conf,
                         "correct": (said == expected) if said is not None else None})
    return rows


def fit(rows, targets, fallback_target):
    # type: (List[Dict[str, Any]], Dict[str, float], float) -> Dict[str, Dict[str, Any]]
    """Per kind, the lowest floor on _GRID whose precision clears the target."""
    by_kind = {}  # type: Dict[str, List[Dict[str, Any]]]
    for r in rows:
        if r.get("correct") is None:
            continue
        by_kind.setdefault(r["kind"], []).append(r)

    out = {}  # type: Dict[str, Dict[str, Any]]
    for kind, scored in sorted(by_kind.items()):
        target = targets.get(kind, fallback_target)
        curve = []
        chosen = None
        for floor in _GRID:
            acted = [r for r in scored if (r["confidence"] or 0.0) >= floor]
            if not acted:
                curve.append({"floor": floor, "acted": 0, "precision": None, "recall": 0.0})
                continue
            hits = sum(1 for r in acted if r["correct"])
            precision = hits / float(len(acted))
            curve.append({"floor": floor, "acted": len(acted),
                          "precision": round(precision, 3),
                          "recall": round(len(acted) / float(len(scored)), 3)})
            if chosen is None and precision >= target:
                chosen = floor
        # No floor reaches the target: say so rather than picking the least-bad
        # one. A threshold that was never met is a threshold nobody should trust,
        # and the honest move is to leave the kind at its conservative default.
        base = jev.thresholds(kind)
        row = {"cases": len(scored), "target": target, "curve": curve,
               "met": chosen is not None,
               "high": chosen if chosen is not None else base["high"],
               "low": round(max(0.3, (chosen if chosen is not None else base["high"]) - 0.2), 2),
               "noul": base["noul"]}
        out[kind] = row
    return out


def main(argv=None):
    # type: (Optional[List[str]]) -> int
    ap = argparse.ArgumentParser(description="Calibrate Jev confidence thresholds on your own data")
    ap.add_argument("--labels", required=True, help="labelled cases JSON (see the module docstring)")
    ap.add_argument("--target", type=float, default=0.90,
                    help="precision target for kinds not in DEFAULT_TARGETS (default 0.90)")
    ap.add_argument("--model", default=jev.DEFAULT_MODEL)
    ap.add_argument("--write", action="store_true",
                    help="write the fitted floors into tools/qa/jev_thresholds.json")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args(argv)

    if not jev.available():
        print("no typesafe api key configured - calibration needs live answers")
        return 2
    with open(args.labels, encoding="utf-8") as f:
        cases = (json.load(f) or {}).get("cases") or []
    if not cases:
        print("no cases in %s" % args.labels)
        return 2

    rows = run_cases(cases, model=args.model)
    failed = [r for r in rows if r.get("error")]
    fitted = fit(rows, DEFAULT_TARGETS, args.target)

    if args.write:
        path = jev._THRESHOLDS_PATH
        with open(path, encoding="utf-8") as f:
            table = json.load(f)
        for kind, row in fitted.items():
            if not row["met"]:
                continue  # never loosen a floor the data did not earn
            table[kind] = {"low": row["low"], "high": row["high"], "noul": row["noul"]}
        table["_calibratedAt"] = __import__("time").strftime("%Y-%m-%dT%H:%M:%SZ",
                                                             __import__("time").gmtime())
        with open(path, "w", encoding="utf-8") as f:
            json.dump(table, f, indent=2, ensure_ascii=False)
        print("wrote %s" % path)

    report = {"cases": len(cases), "answers": len(rows), "failed": len(failed),
              "kinds": fitted}
    if args.as_json:
        print(json.dumps(report, indent=2))
    else:
        print("Jev calibration - cases=%d answers=%d failed=%d"
              % (len(cases), len(rows), len(failed)))
        for kind, row in fitted.items():
            print("  %-18s n=%-3d target=%.2f  %s high=%.2f low=%.2f"
                  % (kind, row["cases"], row["target"],
                     "MET " if row["met"] else "NOT MET (kept the conservative default)",
                     row["high"], row["low"]))
            for point in row["curve"]:
                if point["precision"] is not None:
                    print("      floor %.2f  acted %-3d precision %.3f recall %.3f"
                          % (point["floor"], point["acted"], point["precision"], point["recall"]))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""jev_calibrate.py - set the typed-judgment thresholds from YOUR data, not from the docs.

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
(provider, kind) and a threshold is fitted for each pair - a DS role inference
and a requirement check do not deserve the same floor, a finding that GATES
deserves a higher one than a report line, and Clef at 0.8 does not mean Jev at
0.8. A visual case adds `"tier": "image"` and `"images": ["/abs/frame.png"]`.
Fitted bands are written under `providers[<judge id>][<kind>]`.

TRUST PASS. With --write --trust-pass, a (provider, kind) whose confident PASS
verdicts were right at least TRUST_TARGET of the time over at least
TRUST_MIN_CASES gets `trustPass: true`, which lets a confident typed PASS skip
the model call it shadows (the frame judge, for kind frame_check). This is the
ONLY writer of trustPass; the UI never sets it.

SHADOW REPORT. --shadow reads ~/.test-harness/typed-judge-shadow.jsonl (what
Shadow mode recorded next to the LLM verdict) and reports agreement per
(provider, kind) with the disagreements listed. Agreement is not accuracy: the
LLM is not ground truth. Label the disagreements into a --labels set; only that
set decides trustPass.

WHAT IT FITS. For each kind, the lowest confidence floor at which PRECISION on
the acted-on verdicts reaches the target. Precision, not accuracy: a gate exists
to catch rare failures, so the number that matters is how many of its alarms are
real. Raising the floor trades recall for precision; the escalate band catches
what the floor drops, so that trade is cheap.

    python3 editor/tools/qa/jev_calibrate.py --labels cases.json [--provider clef]
                                              [--target 0.95] [--write [--trust-pass]]
    python3 editor/tools/qa/jev_calibrate.py --shadow [--limit 40]

Stdlib only, Python 3.9-safe.
"""

import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
_EDITOR = os.path.dirname(os.path.dirname(_HERE))
for _p in (_HERE, _EDITOR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import jev  # noqa: E402
import typed_judge  # noqa: E402

# Per-kind precision target. A kind whose verdict can PROMOTE a finding to
# error-severity has to clear a higher bar than one that only ranks a shortlist
# nobody is gated by. Anything not named here uses --target.
DEFAULT_TARGETS = {
    "ds_role": 0.95,           # promotes an info finding to a gating error
    "requirement_item": 0.90,  # writes a line into a report a human reads
    "direction_axis": 0.70,    # narrows a shortlist; a wrong rank costs nothing
}
# trustPass needs this precision on confident PASS verdicts, over at least this
# many of them. Skipping a model call on a wrong PASS hides a real failure, so
# the bar is higher than any gate's.
TRUST_TARGET = 0.98
TRUST_MIN_CASES = 20
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


def run_cases(cases, model=None, provider=None, judge=None):
    # type: (List[Dict[str, Any]], Optional[str], Optional[str], Any) -> List[Dict[str, Any]]
    """One request per case, to `provider` or else whatever the case's tier
    routes to. Failures are RECORDED, never fatal: a calibration run that dies
    on case 7 of 30 has told you nothing."""
    judge = judge or typed_judge.judge
    rows = []  # type: List[Dict[str, Any]]
    for i, case in enumerate(cases):
        kind = str(case.get("kind") or "default")
        tier = case.get("tier") or ("image" if case.get("images") else "text")
        try:
            res = judge(case["state"], case["questions"], tier=tier, images=case.get("images"),
                        kind=kind, provider=provider, model=model if provider else None)
        except Exception as exc:
            rows.append({"case": i, "kind": kind, "provider": provider, "error": str(exc)[:200]})
            continue
        pid = res.get("provider") or provider or "default"
        floor = typed_judge.thresholds(kind, pid)["noul"]
        for qid, expected in (case.get("expected") or {}).items():
            said, conf = _verdict(res["answers"].get(qid), floor)
            rows.append({"case": i, "kind": kind, "provider": pid, "question": qid,
                         "expected": expected, "said": said, "confidence": conf,
                         "correct": (said == expected) if said is not None else None})
    return rows


def fit(rows, targets, fallback_target):
    # type: (List[Dict[str, Any]], Dict[str, float], float) -> Dict[Tuple[str, str], Dict[str, Any]]
    """Per (provider, kind), the lowest floor on _GRID whose precision clears
    the target, plus whether confident PASS verdicts earned trustPass."""
    by_kind = {}  # type: Dict[Tuple[str, str], List[Dict[str, Any]]]
    for r in rows:
        if r.get("correct") is None:
            continue
        by_kind.setdefault((str(r.get("provider") or "default"), r["kind"]), []).append(r)

    out = {}  # type: Dict[Tuple[str, str], Dict[str, Any]]
    for (pid, kind), scored in sorted(by_kind.items()):
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
        base = typed_judge.thresholds(kind, pid)
        high = chosen if chosen is not None else base["high"]
        passes = [r for r in scored if r["said"] is True and (r["confidence"] or 0.0) >= high]
        pass_precision = (sum(1 for r in passes if r["correct"]) / float(len(passes))
                          if passes else None)
        row = {"provider": pid, "kind": kind, "cases": len(scored), "target": target,
               "curve": curve, "met": chosen is not None,
               "high": high,
               "low": round(max(0.3, high - 0.2), 2),
               "noul": base["noul"],
               "confidentPasses": len(passes),
               "passPrecision": round(pass_precision, 3) if pass_precision is not None else None,
               "trustPass": bool(chosen is not None and pass_precision is not None
                                 and len(passes) >= TRUST_MIN_CASES
                                 and pass_precision >= TRUST_TARGET)}
        out[(pid, kind)] = row
    return out


def write_fitted(fitted, trust_pass=False, path=None):
    # type: (Dict[Tuple[str, str], Dict[str, Any]], bool, Optional[str]) -> str
    """Merge met bands into providers[<judge>][<kind>]. Never loosens a floor
    the data did not earn, and only sets trustPass when asked to."""
    path = path or typed_judge.THRESHOLDS_PATH
    with open(path, encoding="utf-8") as f:
        table = json.load(f)
    per = table.setdefault("providers", {})
    for (pid, kind), row in fitted.items():
        if not row["met"]:
            continue
        entry = {"low": row["low"], "high": row["high"], "noul": row["noul"]}
        if trust_pass and row["trustPass"]:
            entry["trustPass"] = True
        per.setdefault(pid, {})[kind] = entry
    table["_calibratedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(path, "w", encoding="utf-8") as f:
        json.dump(table, f, indent=2, ensure_ascii=False)
    return path


def shadow_report(paths=None, limit=40):
    # type: (Optional[List[str]], int) -> Dict[str, Any]
    """Agreement between the typed verdict and the LLM verdict it shadowed,
    per (provider, kind), from the Shadow-mode log. Lines with no LLM verdict
    or no typed noul are counted as skipped, not as agreement."""
    if paths is None:
        paths = [typed_judge.SHADOW_LOG_PATH + ".1", typed_judge.SHADOW_LOG_PATH]
    groups = {}  # type: Dict[Tuple[str, str], Dict[str, Any]]
    skipped = 0
    for path in paths:
        try:
            with open(path, encoding="utf-8") as f:
                lines = f.readlines()
        except OSError:
            continue
        for raw in lines:
            try:
                e = json.loads(raw)
            except ValueError:
                skipped += 1
                continue
            noul, llm_ok = e.get("noul"), e.get("llmOk")
            if not isinstance(noul, (int, float)) or not isinstance(llm_ok, bool):
                skipped += 1
                continue
            pid, kind = str(e.get("provider") or "?"), str(e.get("kind") or "default")
            typed_ok = noul >= typed_judge.thresholds(kind, pid)["noul"]
            g = groups.setdefault((pid, kind), {"provider": pid, "kind": kind, "n": 0,
                                                "agree": 0, "disagreements": []})
            g["n"] += 1
            if typed_ok == llm_ok:
                g["agree"] += 1
            elif len(g["disagreements"]) < limit:
                g["disagreements"].append({"ts": e.get("ts"), "project": e.get("project"),
                                           "noul": noul, "typedOk": typed_ok, "llmOk": llm_ok,
                                           "subject": e.get("subject")})
    for g in groups.values():
        g["agreement"] = round(g["agree"] / float(g["n"]), 3) if g["n"] else None
    return {"groups": [groups[k] for k in sorted(groups)], "skipped": skipped}


def main(argv=None):
    # type: (Optional[List[str]]) -> int
    ap = argparse.ArgumentParser(description="Calibrate typed-judgment thresholds on your own data")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--labels", help="labelled cases JSON (see the module docstring)")
    mode.add_argument("--shadow", nargs="?", const="", metavar="LOG",
                      help="report Shadow-mode agreement (default: the shadow log)")
    ap.add_argument("--provider", default=None,
                    help="judge id to calibrate (default: whatever each case routes to)")
    ap.add_argument("--target", type=float, default=0.90,
                    help="precision target for kinds not in DEFAULT_TARGETS (default 0.90)")
    ap.add_argument("--model", default=None, help="model override for a pinned --provider")
    ap.add_argument("--limit", type=int, default=40, help="disagreements listed per group")
    ap.add_argument("--write", action="store_true",
                    help="write the fitted floors into tools/qa/jev_thresholds.json")
    ap.add_argument("--trust-pass", action="store_true",
                    help="with --write, also set trustPass where the labelled set earned it")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args(argv)

    if args.shadow is not None:
        report = shadow_report([args.shadow] if args.shadow else None, args.limit)
        if args.as_json:
            print(json.dumps(report, indent=2))
            return 0
        print("Typed-judge shadow agreement (agreement is not accuracy; label the "
              "disagreements before trusting anything)")
        if not report["groups"]:
            print("  no shadow entries yet (skipped %d)" % report["skipped"])
        for g in report["groups"]:
            print("  %-12s %-16s n=%-4d agreement=%s" % (g["provider"], g["kind"], g["n"],
                                                        g["agreement"]))
            for d in g["disagreements"]:
                print("      %s %-24s noul=%.2f typed=%s llm=%s"
                      % (d.get("ts") or "-", (d.get("project") or "-")[:24], d["noul"],
                         "pass" if d["typedOk"] else "fail", "pass" if d["llmOk"] else "fail"))
        return 0

    if args.provider and typed_judge.provider(args.provider) is None:
        print("unknown judge %s (judges.json has: %s)"
              % (args.provider, ", ".join(r["id"] for r in typed_judge.providers())))
        return 2
    if not args.provider and not jev.available():
        print("no typed judge is set up - calibration needs live answers")
        return 2
    with open(args.labels, encoding="utf-8") as f:
        cases = (json.load(f) or {}).get("cases") or []
    if not cases:
        print("no cases in %s" % args.labels)
        return 2

    rows = run_cases(cases, model=args.model, provider=args.provider)
    failed = [r for r in rows if r.get("error")]
    fitted = fit(rows, DEFAULT_TARGETS, args.target)

    if args.write:
        print("wrote %s" % write_fitted(fitted, trust_pass=args.trust_pass))

    report = {"cases": len(cases), "answers": len(rows), "failed": len(failed),
              "groups": list(fitted.values())}
    if args.as_json:
        print(json.dumps(report, indent=2))
    else:
        print("Typed-judge calibration - cases=%d answers=%d failed=%d"
              % (len(cases), len(rows), len(failed)))
        for row in fitted.values():
            print("  %-12s %-18s n=%-3d target=%.2f  %s high=%.2f low=%.2f  trustPass=%s"
                  % (row["provider"], row["kind"], row["cases"], row["target"],
                     "MET " if row["met"] else "NOT MET (kept the conservative default)",
                     row["high"], row["low"], "earned" if row["trustPass"] else "no"))
            for point in row["curve"]:
                if point["precision"] is not None:
                    print("      floor %.2f  acted %-3d precision %.3f recall %.3f"
                          % (point["floor"], point["acted"], point["precision"], point["recall"]))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())

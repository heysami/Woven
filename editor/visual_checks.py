#!/usr/bin/env python3
"""visual_checks.py - literal visual checks, built from shapes and stored fields.

A typed judge is a classifier, so it is only ever asked a LITERAL claim about
the exact evidence the claim needs. Nobody writes those claims at check time:
they are built here from a handful of sentence SHAPES and fixed option LISTS,
filled with values Woven already stores (a sprite node's `facing`, an asset's
`alt` text, a storyboard's subject position). That keeps a check fast and
cheap: no model writes anything, one classifier call answers it.

  SHAPES       the sentence patterns (noul) and the one choice pattern
  LISTS        the fixed option sets a choice picks from, with their criteria
  FIELD_RULES  which stored field becomes which check - the ONE table to edit
               when a new kind of thing should be checked
  question()   one check -> the typed question to send
  verdict()    one answer -> {passed, confidence, band, answer}
  from_fields()  a node's fields -> the checks they call for (no field, no check)

Used by tools/qa/visual_qa.py (page and piece checks), the animated-sprite
gate and /__asset_generate in serve.py, and ds_lint's off-system judgment.
Plan: docs/features/typed-judgment-providers.md.

Stdlib only, Python 3.9-safe.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

# ── Shapes ──────────────────────────────────────────────────────────────────
# {x} is the one thing that varies. `images` is how many images the claim
# needs; with two, image 1 is the reference and image 2 the thing checked.
SHAPES = {
    "shows":      {"type": "noul", "images": 1, "text": "The image shows {x}."},
    "subject_is": {"type": "noul", "images": 1, "text": "The subject is {x}."},
    "intact":     {"type": "noul", "images": 1,
                   "text": "The whole {x} is visible, with nothing cut off."},
    "same_as":    {"type": "noul", "images": 2,
                   "text": "Image 2 shows the same {x} as image 1."},
    "changed":    {"type": "noul", "images": 2,
                   "text": "Image 2 shows {x} that image 1 does not."},
    "which":      {"type": "choice", "images": 1, "text": "Which of these is true of {x}?"},
}

# ── Option lists (choice) ───────────────────────────────────────────────────
LISTS = {
    "direction": {
        "left": "It faces the left edge of the image.",
        "right": "It faces the right edge of the image.",
        "up": "Seen from above, it faces the top edge of the image.",
        "down": "Seen from above, it faces the bottom edge of the image.",
        "toward-viewer": "It faces out of the image, toward the viewer.",
        "away-from-viewer": "It has its back to the viewer.",
    },
    "position": {
        "left": "It sits in the left third of the image.",
        "center": "It sits in the middle third of the image.",
        "right": "It sits in the right third of the image.",
    },
    "empty_area": {
        "left": "The left part of the image is empty enough to hold text.",
        "right": "The right part of the image is empty enough to hold text.",
        "top": "The top part of the image is empty enough to hold text.",
        "bottom": "The bottom part of the image is empty enough to hold text.",
        "none": "No part of the image is empty enough to hold text.",
    },
    "control_state": {
        "on": "It is switched on, selected or checked.",
        "off": "It is switched off, unselected or unchecked.",
        "disabled": "It is greyed out and cannot be used.",
    },
    "ds_origin": {
        "ds-copy": "It rebuilds by hand a component the design system already provides: one of "
                   "the components named in the state, under a different name or with its own "
                   "styling.",
        "new-ui": "It is a self-contained piece of UI (something a user reads or operates as one "
                  "piece) that none of the design system's components covers.",
        "layout": "It only arranges, frames or decorates other content: a wrapper, column, grid, "
                  "spacer, divider or background band, not a piece of UI on its own.",
    },
}

# ── Which stored field becomes which check ──────────────────────────────────
# One row per field. `x` fills the shape; `{value}` is the field's value.
# `expect` names how the field's value maps to the acceptable options of a
# choice. `frames` says which image of a sequence it applies to.
FIELD_RULES = [
    {"field": "facing", "shape": "which", "list": "direction", "x": "the subject",
     "expect": "direction", "frames": "each"},
    {"field": "endState", "shape": "subject_is", "x": "{value}", "frames": "last"},
    {"field": "sameSubject", "shape": "same_as", "x": "character", "frames": "first-last"},
    {"field": "alt", "shape": "shows", "x": "{value}", "frames": "each"},
    {"field": "subject", "shape": "shows", "x": "{value}", "frames": "each"},
    {"field": "cutout", "shape": "intact", "x": "{value}", "frames": "each"},
    {"field": "subjectPosition", "shape": "which", "list": "position", "x": "the main subject",
     "expect": "exact", "frames": "each"},
    {"field": "quietZone", "shape": "which", "list": "empty_area", "x": "the image",
     "expect": "exact", "frames": "each"},
]

MAX_X = 160
# Judgement phrases, not words: "The correct answer is highlighted" is a
# literal claim; "The menu works correctly" is not.
VAGUE = re.compile(r"\bas (expected|intended|designed)\b"
                   r"|\b(expected|intended|desired) (effect|behaviou?r|result|outcome|output|state)\b"
                   r"|\b(correctly|properly)\b"
                   r"|\b(works?|working|functions?)\b"
                   r"|\b(is|are|looks?|renders?|appears?) (correct|right|fine|good|ok|okay|nice)\b"
                   r"|\bachiev(e|es|ed|ing)\b", re.I)
COUNTING = re.compile(r"\b(how many|number of|count)\b", re.I)


def option_list(name):
    # type: (str) -> Dict[str, str]
    return dict(LISTS[name])


def literal_problem(text):
    # type: (str) -> Optional[str]
    """Why a claim cannot be checked, or None when it can."""
    m = VAGUE.search(text or "")
    if m:
        return ("restates intent (%r) instead of naming what is visible - say what the image "
                "shows, e.g. 'A dropdown menu is open below the Account button.'" % m.group(0))
    if COUNTING.search(text or ""):
        return "never ask a judge to count; one check per thing"
    return None


def _direction_expect(value):
    # type: (str) -> Optional[List[str]]
    """The direction options a free-text `facing` accepts. Seen-from-above and
    seen-from-the-front words overlap on purpose: 'facing down' in a top-down
    game and 'facing the camera' in a side view are the same pose to a player."""
    v = (value or "").lower()
    out = []  # type: List[str]
    if re.search(r"\bleft|west\b", v):
        out.append("left")
    if re.search(r"\bright|east\b", v):
        out.append("right")
    if re.search(r"\b(up|north|back|away|behind)\b", v):
        out += ["up", "away-from-viewer"]
    if re.search(r"\b(down|south|front|toward|towards|camera|viewer|forward)\b", v):
        out += ["down", "toward-viewer"]
    return sorted(set(out)) or None


def question(check):
    # type: (Dict[str, Any]) -> Tuple[Dict[str, Any], int]
    """One check -> (typed question, images it needs). A check is either a
    shape {shape, x, list?, criteria?} or a literal {statement, criteria?}.
    Raises ValueError with the reason a check cannot be asked."""
    if check.get("statement") is not None and not check.get("shape"):
        st = str(check["statement"]).strip()
        if not st or "\n" in st or len(st) > 240:
            raise ValueError("statement must be one sentence, at most 240 characters")
        why = literal_problem(st)
        if why:
            raise ValueError("statement " + why)
        if check.get("compare") and not re.search(r"\bimage [12]\b", st, re.I):
            raise ValueError("with compare, say which image: 'Image 2 shows ... that image 1 does not.'")
        q = {"type": "noul", "instructions": st}  # type: Dict[str, Any]
        if isinstance(check.get("criteria"), dict):
            q["criteria"] = {k: str(v)[:300] for k, v in check["criteria"].items()
                             if k in ("true", "false") and v}
        return q, 2 if check.get("compare") else 1
    shape = SHAPES.get(str(check.get("shape") or ""))
    if shape is None:
        raise ValueError("shape must be one of %s, or give a literal statement"
                         % ", ".join(sorted(SHAPES)))
    x = str(check.get("x") or "").strip()
    if not x or len(x) > MAX_X or "\n" in x:
        raise ValueError("x must be a short phrase (at most %d characters)" % MAX_X)
    why = literal_problem(x)
    if why:
        raise ValueError("x " + why)
    text = shape["text"].format(x=x)
    if shape["type"] == "choice":
        name = str(check.get("list") or "")
        if name not in LISTS:
            raise ValueError("a which check needs list: one of %s" % ", ".join(sorted(LISTS)))
        return {"type": "choice", "instructions": text, "criteria": option_list(name)}, shape["images"]
    q = {"type": "noul", "instructions": text}
    if isinstance(check.get("criteria"), dict):
        q["criteria"] = {k: str(v)[:300] for k, v in check["criteria"].items()
                         if k in ("true", "false") and v}
    return q, shape["images"]


def verdict(q, answer, th, expect=None):
    # type: (Dict[str, Any], Any, Dict[str, Any], Optional[List[str]]) -> Dict[str, Any]
    """One answer read against its thresholds: {answer, passed, confidence,
    band}. A noul passes when true; a choice passes when its top option is in
    `expect` (no expect -> passed is None, the answer is the result). Total:
    a missing answer is {passed: None, band: escalate}."""
    import typed_judge as tj
    if q.get("type") == "choice":
        ranked = tj.choice_ranked(answer, 1)
        if not ranked:
            return {"answer": None, "passed": None, "confidence": None, "band": "escalate"}
        top = ranked[0][0]
        conf = tj.confidence(answer)
        if conf is None:
            conf = ranked[0][1]
        return {"answer": top, "passed": (top in expect) if expect else None,
                "confidence": conf, "band": tj.band(conf, float(th.get("low", 0.55)),
                                                    float(th.get("high", 0.8)))}
    v = tj.noul_verdict(answer, th)
    return {"answer": v["noul"], "noul": v["noul"], "passed": v["pass"],
            "confidence": v["confidence"], "band": v["band"]}


def from_fields(fields, n_frames=1):
    # type: (Dict[str, Any], int) -> List[Dict[str, Any]]
    """The checks a node's own fields call for, each with `frames` (indexes
    into the images it applies to) and `expect`. A field that is absent,
    empty, or not checkable as written produces no check."""
    out = []  # type: List[Dict[str, Any]]
    for rule in FIELD_RULES:
        value = fields.get(rule["field"])
        if value in (None, "", False):
            continue
        value = str(value).strip() if value is not True else ""
        x = rule["x"].replace("{value}", value)
        check = {"id": "%s_check" % rule["field"], "field": rule["field"], "shape": rule["shape"],
                 "x": x}  # type: Dict[str, Any]
        if rule.get("list"):
            check["list"] = rule["list"]
        if rule.get("expect") == "direction":
            check["expect"] = _direction_expect(value)
            if not check["expect"]:
                continue  # a facing we cannot map is not a check we can grade
        elif rule.get("expect") == "exact":
            if value not in LISTS[rule["list"]]:
                continue
            check["expect"] = [value]
        try:
            question(check)
        except ValueError:
            continue
        frames = rule.get("frames", "each")
        last = max(0, n_frames - 1)
        if frames == "last":
            check["frames"] = [[last]]
        elif frames == "first-last":
            if n_frames < 2:
                continue
            check["frames"] = [[0, last]]
        else:
            check["frames"] = [[i] for i in range(n_frames)]
        out.append(check)
    return out


def run(checks, images, judge_fn, kind, mode, shadow_log=None, subject=None):
    # type: (List[Dict[str, Any]], List[Any], Any, str, Optional[str], Any, Optional[str]) -> Dict[str, Any]
    """Ask every check over the images it names (from from_fields). ALWAYS
    returns a block {mode, kind, provider, results, findings, message} and
    never raises. Flag mode adds one finding per confident failure; shadow
    only records. Every answered check is shadow-logged for labelling."""
    block = {"mode": mode, "kind": kind, "provider": None, "results": [], "findings": [],
             "message": None}  # type: Dict[str, Any]
    for c in checks:
        try:
            q, need = question(c)
        except ValueError as exc:
            block["results"].append({"id": c.get("id"), "status": "rejected", "reason": str(exc)})
            continue
        for idx in c.get("frames") or [[0]]:
            imgs = [images[i] for i in idx if 0 <= i < len(images)]
            row = {"id": c.get("id"), "frames": idx, "claim": q["instructions"],
                   "expect": c.get("expect")}  # type: Dict[str, Any]
            if len(imgs) != need:
                row["status"] = "no-capture"
                block["results"].append(row)
                continue
            state = ("An image." if need == 1 else
                     "Two images of the same subject: image 1 is the reference, image 2 is checked.")
            try:
                res = judge_fn(state, {"c": q}, tier="image", images=imgs, kind=kind)
            except Exception as exc:
                row.update(status="unavailable", message=str(exc)[:200])
                block["results"].append(row)
                if getattr(exc, "reason", None) in ("off", "no-key", "no-image-judge"):
                    block["message"] = "typed judge unavailable: %s" % exc
                    return block
                continue
            v = verdict(q, res["answers"].get("c"), res["thresholds"], c.get("expect"))
            row.update(v, status="answered" if v["band"] is not None and v["answer"] is not None
                       else "no-answer")
            block["provider"] = res.get("provider")
            block["results"].append(row)
            if shadow_log and row["status"] == "answered":
                try:
                    shadow_log({"provider": res.get("provider"), "kind": kind,
                                "noul": v.get("noul"), "answer": v["answer"], "llmOk": None,
                                "project": subject, "subject": "%s %s" % (c.get("id"), idx)})
                except Exception:
                    pass
            if mode == "flag" and v["passed"] is False and v["band"] == "act":
                block["findings"].append({
                    "rule": "typed-judge", "severity": "warn", "kind": kind, "check": c.get("id"),
                    "frames": idx, "provider": res.get("provider"),
                    "message": "%s is confidently not met on image(s) %s (judge said %s): %s"
                               % (c.get("id"), idx, v["answer"], q["instructions"])})
    answered = [r for r in block["results"] if r.get("status") == "answered"]
    block["message"] = "%d check(s) answered via %s" % (len(answered), block["provider"])
    return block

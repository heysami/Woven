"""The design library ranked for a brief by the text judge, before any agent
composes a direction.

When typed judgment for text checks is on and a project has no direction yet
(no `DECISION_prototype-direction.json`, no page built), the daemon asks the
text judge ONE request at thread start: does the brief leave the visual
direction open, and how does it rank every recipe, shell, style and
aesthetic of the design library (docs/research/direction-axes.jev.json). The
answer is shown to the user under their message (the judge is far faster
than the agent) and handed to the agent in its first message, so the step
cannot be skipped. With the setting off nothing here runs.
"""

import json
import os
import time
from typing import Any, Callable, Dict, List, Optional

import typed_judge

AXES = ("recipe", "shell", "style", "aesthetic")
TOP = 5
AXES_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "docs", "research", "direction-axes.jev.json")
NEEDS_DIRECTION = "This request leaves the visual direction unspecified."


def applies(project_root):
    # type: (str) -> bool
    """No direction yet: no direction decision, and no page built."""
    if not project_root or os.path.isfile(os.path.join(project_root, "DECISION_prototype-direction.json")):
        return False
    src = os.path.join(project_root, "source")
    try:
        protos = [d for d in os.listdir(src) if not d.startswith(".") and os.path.isdir(os.path.join(src, d))]
    except OSError:
        return True
    for d in protos:
        try:
            if any(f.endswith((".html", ".htm")) and not f.startswith(".")
                   for f in os.listdir(os.path.join(src, d))):
                return False
        except OSError:
            continue
    return True


def load_axes(path=None):
    # type: (Optional[str]) -> Dict[str, Any]
    with open(path or AXES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)["axes"]


def questions(axes):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    qs = {"needs_direction": {"type": "noul", "instructions": NEEDS_DIRECTION}}  # type: Dict[str, Any]
    for k in AXES:
        if k in axes:
            qs[k] = {"type": "choice", "instructions": axes[k]["question"], "criteria": axes[k]["criteria"]}
    return qs


def _label(option_id):
    # type: (str) -> str
    return option_id.replace("recipe-", "").replace("-", " ")


def propose(project_root, brief, judge=None, axes_path=None, enabled=None):
    # type: (str, str, Optional[Callable[..., Dict[str, Any]]], Optional[str], Optional[bool]) -> Optional[Dict[str, Any]]
    """{"event": <what the thread shows>, "forAgent": <block for the agent's
    first message>} or None when the setting is off or a direction exists.
    Never raises: a failure is an event that says why, so the proposal is
    never silently missing."""
    if enabled is None:
        try:
            enabled = bool(typed_judge.config().get("jevJudge"))
        except Exception:
            enabled = False
    if not enabled or not (brief or "").strip() or not applies(project_root):
        return None
    try:
        axes = load_axes(axes_path)
    except Exception as exc:
        return {"event": {"error": "the design library's ranking file could not be read (%s)" % exc},
                "forAgent": ""}
    t0 = time.time()
    try:
        out = (judge or typed_judge.judge)(brief.strip()[:6000], questions(axes), tier="text",
                                           kind="direction_axis")
    except typed_judge.JudgeUnavailable as exc:
        return {"event": {"error": "no text judge is set up (%s)" % exc}, "forAgent": ""}
    except Exception as exc:
        return {"event": {"error": str(exc)[:240]}, "forAgent": ""}
    ms = int((time.time() - t0) * 1000)
    answers = out.get("answers") or {}
    th = out.get("thresholds") or {}
    event = {"provider": out.get("provider"), "model": out.get("model"), "ms": ms,
             "needsDirection": typed_judge.noul_value(answers.get("needs_direction")),
             "thresholds": {k: th.get(k) for k in ("low", "high", "noul")},
             "axes": {}}  # type: Dict[str, Any]
    for k in AXES:
        if k not in axes:
            continue
        a = answers.get(k) or {}
        probs = a.get("probabilities") or {}
        ranked = sorted(probs.items(), key=lambda kv: -kv[1])[:TOP]
        event["axes"][k] = {
            "question": axes[k]["question"], "optional": bool(axes[k].get("optional")),
            "confidence": a.get("confidence"),
            "top": [{"id": i, "label": _label(i), "p": round(float(p), 4),
                     "desc": str(axes[k]["criteria"].get(i, ""))[:200]} for i, p in ranked],
        }
    return {"event": event, "forAgent": for_agent(event, out.get("provider") or "the text judge")}


def for_agent(event, provider):
    # type: (Dict[str, Any], str) -> str
    th = event.get("thresholds") or {}
    lines = ["[Woven: the typed judge (%s, %.1f s) ranked the design library for this request before you "
             "started, and the user can see this ranking. It is the ranking PROTOTYPE.md step -1 asks for "
             "(Ranking the axes with typed judgment): read it with those rules and do not call /__judge "
             "for it again." % (provider, (event.get("ms") or 0) / 1000.0),
             "brief leaves the direction open: %s (counts at %s)" % (_n(event.get("needsDirection")), _n(th.get("noul"))),
             "thresholds: low %s, high %s" % (_n(th.get("low")), _n(th.get("high")))]
    for k, ax in (event.get("axes") or {}).items():
        lines.append("%s (confidence %s): %s" % (k, _n(ax.get("confidence")),
                                                 ", ".join("%s %s" % (t["id"], _n(t["p"])) for t in ax["top"])))
    return "\n".join(lines) + "]"


def _n(v):
    # type: (Any) -> str
    return "-" if v is None else ("%.2f" % float(v))

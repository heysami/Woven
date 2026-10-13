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
import re
import time
from typing import Any, Callable, Dict, List, Optional

import typed_judge

AXES = ("recipe", "shell", "style", "aesthetic")
CORE = ("shell", "style", "aesthetic")
TOP = 5
PROPOSALS = 3
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AXES_FILE = os.path.join(_ROOT, "docs", "research", "direction-axes.jev.json")
PROTOTYPE_MD = os.path.join(_ROOT, "PROTOTYPE.md")
_ROSTER_LINK = re.compile(r"^- \*\*([^*]+)\*\*.*?\(\./design-library/([\w+.-]+)\.md\)", re.M)
NEEDS_DIRECTION = "This request leaves the visual direction unspecified."
IS_BUILD = "This request asks to build or design something new: an app, a website, a game, a page or a screen."
# A brief that names only part of its direction ("pixel art": a style, no
# aesthetic, no layout) sits around 0.5 on NEEDS_DIRECTION; one that states it
# all ("Swiss modernist, Helvetica, a 12-column grid, black and red") near
# 0.03. Proposals keep what the brief states and spread across what it leaves
# open, so only a fully stated brief skips them (Clef, 2026-10-13 samples).
NEEDS_CUT = 0.25


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
    qs = {"is_build": {"type": "noul", "instructions": IS_BUILD},
          "needs_direction": {"type": "noul", "instructions": NEEDS_DIRECTION}}  # type: Dict[str, Any]
    for k in AXES:
        if k in axes:
            qs[k] = {"type": "choice", "instructions": axes[k]["question"], "criteria": axes[k]["criteria"]}
    return qs


_PREVIEWS = None  # type: Optional[Dict[str, str]]


def previews(path=None):
    # type: (Optional[str]) -> Dict[str, str]
    """Library id -> its preview image (`design-library/<file>-ui.png`), from
    the roster lines in PROTOTYPE.md that link each id to its library file."""
    global _PREVIEWS
    if _PREVIEWS is not None and path is None:
        return _PREVIEWS
    out = {}  # type: Dict[str, str]
    try:
        with open(path or PROTOTYPE_MD, "r", encoding="utf-8") as f:
            text = f.read()
        lib = os.path.join(os.path.dirname(path or PROTOTYPE_MD), "design-library")
        for m in _ROSTER_LINK.finditer(text):
            png = m.group(2) + "-ui.png"
            if m.group(1).strip() not in out and os.path.isfile(os.path.join(lib, png)):
                out[m.group(1).strip()] = "design-library/" + png
    except OSError:
        pass
    if path is None:
        _PREVIEWS = out
    return out


def proposals(event, n=PROPOSALS):
    # type: (Dict[str, Any], int) -> List[Dict[str, Any]]
    """Three complete directions (shell + style + aesthetic) from the ranking,
    by PROTOTYPE.md step -1's own rule: an axis the brief implies (top pick at
    or over the high threshold) keeps its top pick in all three; the three
    SPREAD across the axis the brief leaves most open (aesthetic first, then
    style, then shell), taking its top picks in order."""
    axes = event.get("axes") or {}
    high = float((event.get("thresholds") or {}).get("high") or 0.7)
    core = [a for a in CORE if (axes.get(a) or {}).get("top")]
    if not core:
        return []
    open_axes = [a for a in core if axes[a]["top"][0]["p"] < high]
    spread = open_axes[-1] if open_axes else min(core, key=lambda a: axes[a]["top"][0]["p"])
    for a in ("aesthetic", "style", "shell"):
        if a in open_axes:
            spread = a
            break
    out = []
    for i, pick in enumerate(axes[spread]["top"][:n]):
        combo = {a: (pick if a == spread else axes[a]["top"][0]) for a in core}
        out.append({"spread": spread, "picks": {a: {k: t[k] for k in ("id", "label", "p", "preview") if k in t}
                                                 for a, t in combo.items()}})
    return out


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
    # The chain's first two links, from the same call: a request that is not a
    # new build, or that already states its direction, gets no proposal.
    cut = float(th.get("noul") or 0.5)
    is_build = typed_judge.noul_value(answers.get("is_build"))
    needs = typed_judge.noul_value(answers.get("needs_direction"))
    if is_build is None or needs is None or is_build < cut or needs < NEEDS_CUT:
        return None
    event = {"provider": out.get("provider"), "model": out.get("model"), "ms": ms,
             "needsDirection": needs, "isBuild": is_build,
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
            "top": [dict({"id": i, "label": _label(i), "p": round(float(p), 4),
                          "desc": str(axes[k]["criteria"].get(i, ""))[:200]},
                         **({"preview": previews()[i]} if i in previews() else {})) for i, p in ranked],
        }
    event["proposals"] = proposals(event)
    return {"event": event, "forAgent": for_agent(event, out.get("provider") or "the text judge")}


def for_agent(event, provider):
    # type: (Dict[str, Any], str) -> str
    """The block for the agent's first message. With proposals on screen the
    agent does NOT compose direction options: the judge's three are the
    options, and the user's pick arrives as a decision."""
    th = event.get("thresholds") or {}
    props = event.get("proposals") or []
    if not props:
        return ""
    lines = ["[Woven: the typed judge (%s, %.1f s) ranked the design library for this request and the user "
             "is now choosing a direction from its %d proposals, shown under their message. Do NOT compose "
             "direction options, do not run PROTOTYPE.md step -1's composing or recolouring, and do not call "
             "/__judge: reply in one short line that they can pick one of the proposals above or describe their "
             "own direction, then stop. Their pick arrives as `[decision:prototype-direction] judgeN - shell "
             "<id>, style <id>, aesthetic <id>` (already saved with those ids as its detail); continue from the "
             "direction lock: read those library files, add the palette and fonts to the decision's detail "
             "(POST /__decision/prototype-direction with the full detail) and go on to the next step. If they "
             "describe their own direction instead, run step -1 as usual." % (provider, (event.get("ms") or 0) / 1000.0,
                                                                         len(props)),
             "the proposals (they differ in %s, the axis the brief leaves most open):" % props[0]["spread"]]
    for i, pr in enumerate(props):
        lines.append("  %d. %s" % (i + 1, ", ".join("%s %s" % (a, t["id"]) for a, t in pr["picks"].items())))
    lines.append("ranking behind them (thresholds low %s, high %s):" % (_n(th.get("low")), _n(th.get("high"))))
    for k, ax in (event.get("axes") or {}).items():
        lines.append("  %s (confidence %s): %s" % (k, _n(ax.get("confidence")),
                                                   ", ".join("%s %s" % (t["id"], _n(t["p"])) for t in ax["top"])))
    return "\n".join(lines) + "]"


def _n(v):
    # type: (Any) -> str
    return "-" if v is None else ("%.2f" % float(v))

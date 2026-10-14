"""auto_mode.py - the composer's Auto chat mode: pick Normal, Plan or Triage
for ONE message with the typed judge (editor/typed_judge.py).

The user's rule (2026-10-14): the same few questions every time, read in a
fixed order, so the pick is consistent and explainable - and read in the
context of the conversation, because a reply continues what came before it.
A triage is usually followed by answers to its questions, and those answers
move the work on (to a plan, or straight to the change) unless they add new
work that needs triaging again; a reply to a plan revises the plan.

  1. It only asks a question                          -> Normal
  2. Last turn was a PLAN and this replies to it,
     adding nothing new                               -> Plan (revise / approve it)
  3. Last turn was a TRIAGE and this replies to it,
     adding nothing new (the triage is answered):
       needs a new layout or interaction              -> Plan
       is one small, straightforward change           -> Normal
       otherwise                                      -> Plan
  4. Otherwise (a new request, or a reply that adds new work):
       may affect other screens, flows or work        -> Triage
       needs a new layout or interaction              -> Plan
       is one small, straightforward change           -> Normal
       otherwise                                      -> Plan (not clearly simple)
A judge that is off, not set up or failing gives Triage: it changes nothing,
so a pick nobody could make never builds.

The judge is a classifier, so every question is one literal claim about the
chat excerpt in the state, never "is this a good idea". Stdlib only,
Python 3.9-safe.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Dict, Optional, Tuple

THRESHOLD = 0.5
# CONTEXT BUDGET. The judges have small windows (Clef Flash 24k tokens, the
# smallest in editor/judges.json), so the judge never gets the thread: only
# three bounded excerpts. Worst case about 7.5k characters, roughly 2k tokens
# with the questions (tests/test_auto_mode.py measures it against Clef Flash).
# The router also skips any judge a request does not fit (typed_judge.judge).
SUBJECT_MAX = 4000
EARLIER_MAX = 1500
# The END of the agent's last reply: where a triage asks its questions
# ("Needs your call") and a plan shows its Execute card.
REPLY_TAIL = 1800

MODE_NAMES = {"normal": "Normal", "plan": "Plan", "triage": "Triage"}

QUESTIONS = {
    "question_only": {
        "type": "noul",
        "instructions": "The new message only asks a question or asks for an explanation, and asks for nothing to be changed or built.",
    },
    "continues": {
        "type": "noul",
        "instructions": "The new message replies to the agent's last reply, for example answering its questions, confirming or correcting a choice, or asking it to go ahead.",
    },
    "adds_scope": {
        "type": "noul",
        "instructions": "The new message asks for work that neither the earlier request nor the agent's last reply covered.",
    },
    "affects_other": {
        "type": "noul",
        "instructions": "The work being asked for removes, renames, moves or changes something that other screens, steps, data or earlier work may rely on.",
        "criteria": {
            "true": "What it changes is shown, used or decided somewhere else too, or it reverses an earlier choice.",
            "false": "What it changes stands alone and nothing else uses it.",
        },
    },
    "new_layout": {
        "type": "noul",
        "instructions": "The work being asked for needs a new layout, or a new or changed interaction, on a screen.",
        "criteria": {
            "true": "It adds or rearranges sections, screens or controls, or changes how a person clicks, drags, navigates or moves through steps.",
            "false": "It keeps the layout and the way people interact with it as they are.",
        },
    },
    "straightforward": {
        "type": "noul",
        "instructions": "The work being asked for is one small, straightforward change whose result is obvious, such as a wording, colour, size or spacing tweak, or a fix to one thing.",
    },
}

FALLBACK = ("triage", "the judge could not answer, so nothing is changed")
# The reason a question-only message gets. The daemon looks PAST such a turn
# for the mode the work is in, so a clarifying question asked after a triage
# does not stop the next answer from counting as "the triage is answered".
QUESTION_WHY = "it only asks a question"


def subject(text: str) -> str:
    """The user's own words out of what the composer sent: drop the editor's
    leading [Context: ...] routing block and a leading <pointed-targets>
    block, and keep only the [CURRENT REQUEST] of a handoff."""
    t = text or ""
    i = t.find("[CURRENT REQUEST]")
    if i >= 0:
        t = t[i + len("[CURRENT REQUEST]"):]
    t = t.strip()
    if t.startswith("[Context:") and "\n\n" in t:
        t = t.split("\n\n", 1)[1]
    t = re.sub(r"^\s*<pointed-targets\b.*?</pointed-targets>\s*", "", t, flags=re.S)
    return clip(t.strip(), SUBJECT_MAX)


def clip(text: str, n: int) -> str:
    """At most n characters, keeping the START (where a request usually says
    what it wants) and the end, with the middle cut."""
    if len(text) <= n:
        return text
    head = (n * 2) // 3
    return text[:head].rstrip() + " [...] " + text[-(n - head - 7):].lstrip()


def state_for(text: str, earlier: Optional[str] = None, last_reply: Optional[str] = None,
              prev_mode: Optional[str] = None) -> str:
    """The chat excerpt the judge reads: the earlier request, the end of the
    agent's last reply (and which mode it ran in), then the new message."""
    parts = []
    prev = clip(subject(earlier or ""), EARLIER_MAX)
    if prev:
        parts.append("Earlier request: " + prev)
    reply = (last_reply or "").strip()
    if reply:
        tail = reply[-REPLY_TAIL:]
        name = MODE_NAMES.get(prev_mode or "", "")
        head = ("The agent's last reply (a %s reply%s), its end: " % (name, {
            "triage": ", a report that changed nothing",
            "plan": ", a plan waiting for approval",
        }.get(prev_mode or "", ""))) if name else "The agent's last reply, its end: "
        parts.append(head + tail)
    parts.append("New message: " + subject(text))
    parts.append("The work being asked for is the new message, read together with the earlier request when the new message continues it.")
    return "\n\n".join(parts)


def _yes(answers: Dict[str, Any], qid: str) -> bool:
    a = answers.get(qid)
    if isinstance(a, (int, float)) and not isinstance(a, bool):
        v = float(a)
    elif isinstance(a, dict) and isinstance(a.get("noul"), (int, float)):
        v = float(a["noul"])
    else:
        return False
    return v >= THRESHOLD


def decide(answers: Dict[str, Any], prev_mode: Optional[str] = None) -> Tuple[str, str]:
    """(mode, reason) from the judge's answers and the mode the last turn ran
    in, by the fixed order in the module docstring."""
    yes = lambda q: _yes(answers, q)  # noqa: E731
    if yes("question_only"):
        return "normal", QUESTION_WHY
    reply = yes("continues") and not yes("adds_scope")
    if prev_mode == "plan" and reply:
        return "plan", "it replies to the plan, so the plan is revised or approved"
    if prev_mode == "triage" and reply:
        if yes("new_layout"):
            return "plan", "it answers the triage, and the change needs a new layout or interaction"
        if yes("straightforward"):
            return "normal", "it answers the triage, and the change is small and straightforward"
        return "plan", "it answers the triage, and the change is not clearly simple"
    again = prev_mode == "triage" and yes("continues")
    if yes("affects_other"):
        return "triage", ("it adds work that may affect other screens, flows or earlier work"
                          if again else "it may affect other screens, flows or earlier work")
    if yes("new_layout"):
        return "plan", "it needs a new layout or interaction"
    if yes("straightforward"):
        return "normal", "it is a small, straightforward change"
    return "plan", "it is not clearly a small, straightforward change"


def classify(text: str, judge: Optional[Callable[..., Dict[str, Any]]],
             earlier: Optional[str] = None, last_reply: Optional[str] = None,
             prev_mode: Optional[str] = None) -> Dict[str, Any]:
    """{mode, why, judge} for one message. `judge(state, questions)` is
    typed_judge.judge bound to the daemon's keys; None means the judge is off
    for this chat. Never raises: any failure is the FALLBACK."""
    if judge is None:
        return {"mode": FALLBACK[0], "why": "typed judgment is off, so nothing is changed", "judge": None}
    try:
        res = judge(state_for(text, earlier, last_reply, prev_mode), QUESTIONS)
        mode, why = decide((res or {}).get("answers") or {}, prev_mode)
        return {"mode": mode, "why": why, "judge": (res or {}).get("provider")}
    except Exception:
        return {"mode": FALLBACK[0], "why": FALLBACK[1], "judge": None}

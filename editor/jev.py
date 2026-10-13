#!/usr/bin/env python3
"""jev.py - the typed-judgment client for TEXT checks, kept as a shim.

The real client is editor/typed_judge.py, which routes a request to whichever
judge is set up (TypeSafe Jev, Cloudflare Clef, Local Clef, OpenAI Decisions)
and always answers in System One shape. This module keeps the names the text
consumers were written against (ds_lint --jev, the calibrate tool, the
parity tests) so none of them changed when the providers multiplied:

  ask(state, questions)   -> the answers map, from the TEXT judge the user
                             picked (or Auto). Pass api_key or url and it is
                             pinned to TypeSafe Jev, as it always was.
  noul_pass / noul_value / choice_ranked / confidence / band  - readers
  thresholds(kind)        -> the band for the judge that would answer now
  enabled()               -> the "typed judgment for text checks" switch
  available()             -> a text judge is set up
  JevError / JevUnavailable

POSTURE - flag, never block (docs/features/jev-integration.md). `ask` raises
JevError and the caller catches it and carries on.

THE JAGGEDNESS RULES, encoded here rather than remembered. From
https://docs.typesafe.ai/model-jaggedness/jev-1.13 - `validate_questions`
enforces the mechanical ones and the rest are documented at their call sites:

  1. Literal reading. Jev answers the question as WRITTEN, not as meant. One
     clause per question; boundary cases go in `criteria`.
  2. No counting. "How many X" is unreliable and the error grows with the
     count. Fan out one question per item and sum in Python.
  3. No math, no date arithmetic. Extract with the model, compute in code.
  4. Colour: never. Hex values underperform English names and Jev cannot
     reliably judge whether two are near each other. Colour stays
     deterministic (ds_lint's color_to_token already does it better).
  5. No indirection. A property of a property costs accuracy. Point the
     question at the exact state field.
  6. Small state. "Large state full of irrelevant detail" is a named failure
     mode. Send the question's own context, never the whole page.
  7. It cannot generate. No fix text, no rewrite, no explanation. Claude still
     writes every report.

Stdlib only, Python 3.9-safe (the daemon's fresh-install floor).
"""

from __future__ import annotations

import os
import sys
import time  # noqa: F401 - tests patch jev.time.sleep, which is time.sleep
import urllib.request  # noqa: F401 - tests patch jev.urllib.request.urlopen
from typing import Any, Dict, Optional

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import typed_judge  # noqa: E402

# ── TypeSafe Jev service limits (https://docs.typesafe.ai/models) ───────────
API_URL = "https://api.typesafe.ai/v1/systemone"
DEFAULT_MODEL = "jev-latest"
MAX_CHOICE_OPTIONS = 255
MIN_SCORE_LEVELS, MAX_SCORE_LEVELS = 2, 10
MAX_CONTEXT_TOKENS = 64_000
QUESTION_TYPES = typed_judge.QUESTION_TYPES

# Env var / media-config provider id. Mirrors _PROVIDER_ENV_KEYS in serve.py.
PROVIDER = "typesafe"
ENV_KEY = "TH_TYPESAFE_API_KEY"
MEDIA_CONFIG_PATH = typed_judge.MEDIA_CONFIG_PATH
_THRESHOLDS_PATH = typed_judge.THRESHOLDS_PATH

JevError = typed_judge.JudgeError
JevUnavailable = typed_judge.JudgeUnavailable

# Readers, unchanged: every one is total on garbage.
noul_pass = typed_judge.noul_pass
noul_value = typed_judge.noul_value
choice_ranked = typed_judge.choice_ranked
confidence = typed_judge.confidence
band = typed_judge.band
estimate_tokens = typed_judge.estimate_tokens


def _jev_row():
    # type: () -> Dict[str, Any]
    return typed_judge.provider("jev") or {
        "id": "jev", "wire": "systemone", "config": PROVIDER, "url": API_URL,
        "model": DEFAULT_MODEL, "maxImages": 0, "maxChoiceOptions": MAX_CHOICE_OPTIONS,
        "maxScoreLevels": MAX_SCORE_LEVELS, "contextTokens": MAX_CONTEXT_TOKENS}


def resolve_key(explicit=None):
    # type: (Optional[str]) -> Optional[str]
    """The TypeSafe key: explicit, then env, then media-config.json."""
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()
    return typed_judge.default_key(PROVIDER)


def enabled():
    # type: () -> bool
    """The "typed judgment for text checks" switch (`jevJudge`). An intent;
    consumers gate on enabled() AND available()."""
    return typed_judge.enabled("text")


def available(explicit=None):
    # type: (Optional[str]) -> bool
    """A text judge is set up: an explicit key, or any judge the text router
    can reach (TypeSafe, Cloudflare, Local Clef, OpenAI)."""
    if isinstance(explicit, str) and explicit.strip():
        return True
    return typed_judge.pick("text") is not None


def validate_questions(questions):
    # type: (Dict[str, Dict[str, Any]]) -> None
    """The TypeSafe Jev limits (the strictest text caps Woven sends to)."""
    typed_judge.validate_questions(questions, _jev_row())


def ask(state, questions, model=DEFAULT_MODEL, api_key=None, timeout=45,
        max_retries=3, url=API_URL):
    # type: (Any, Dict[str, Dict[str, Any]], str, Optional[str], float, int, str) -> Dict[str, Any]
    """One typed-judgment request; returns the `answers` map keyed by the
    question ids you sent, in System One shape.

    With no api_key and the default url it goes to the TEXT judge the user
    picked (or Auto). With an api_key or a url it is pinned to TypeSafe Jev.
    Raises JevUnavailable when nothing is set up, ValueError for a request the
    judge would refuse, and JevError for anything else."""
    pinned = bool(isinstance(api_key, str) and api_key.strip()) or url != API_URL
    if pinned:
        key = resolve_key(api_key)
        if not key:
            raise JevUnavailable("no %s key configured (set %s or add %s.api_key "
                                 "to media-config.json)" % (PROVIDER, ENV_KEY, PROVIDER))
        return typed_judge.judge(state, questions, provider="jev", api_key=key, url=url,
                                 model=model or DEFAULT_MODEL, timeout=timeout,
                                 max_retries=max_retries)["answers"]
    return typed_judge.judge(state, questions, tier="text",
                             model=None if model in (None, DEFAULT_MODEL) else model,
                             timeout=timeout, max_retries=max_retries)["answers"]


def thresholds(question_kind="default", provider=None):
    # type: (str, Optional[str]) -> Dict[str, Any]
    """Calibrated {low, high, noul, trustPass} for one KIND of question, for
    `provider` or else the text judge that would answer right now."""
    if provider is None:
        try:
            provider = typed_judge.pick("text")
        except Exception:
            provider = None
    return typed_judge.thresholds(question_kind, provider)

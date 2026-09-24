#!/usr/bin/env python3
"""jev.py - typed judgment client (TypeSafe "System One" / Jev).

Jev does not generate text. It answers TYPED questions about a state you give
it and returns calibrated probabilities. One request carries one `state` and N
independent `questions`; the state is ingested once and every question is
evaluated in parallel and in isolation, so fanning out N questions over one
state costs barely more than one. That property is the whole reason Woven uses
it: a 40-item requirement checklist becomes one sub-second request instead of
40 sequential judgments inside a long subagent turn.

Used by:
  - the daemon's POST /__jev proxy (serve.py) so every runtime reaches it with
    one curl and the key never leaves the server,
  - editor/tools/qa/ds_lint.py (--jev) for the one real DS judgment,
  - the requirement-QA and direction-picking agent specs, via the proxy.

POSTURE - flag, never block. Until the calibration pass in
docs/features/jev-integration.md Phase 4 has run on real Woven data, consumers
gate on a HIGH-CONFIDENCE FAIL only and pass everything else. Every consumer
falls back to the judgment it replaced when the key is absent, the toggle is
off, or the call fails. Nothing here is load-bearing: `ask` raises JevError and
the caller is expected to catch it and carry on (see run_judge in
tools/qa/visual_qa.py for the fail-soft shape this mirrors).

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

import json
import os
import random
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

# ── Service limits (https://docs.typesafe.ai/models) ────────────────────────
API_URL = "https://api.typesafe.ai/v1/systemone"
DEFAULT_MODEL = "jev-latest"
# A Choice's criteria map. The aesthetics roster (130) is the biggest thing
# Woven sends; the cap is what makes "one question per axis" legal at all.
MAX_CHOICE_OPTIONS = 255
# A Score's ordered rubric.
MIN_SCORE_LEVELS, MAX_SCORE_LEVELS = 2, 10
# Total context: state + every question. Enforced as a CHARACTER budget at
# ~3.6 chars/token, deliberately under the real 64k-token ceiling - a cheap
# local guard that turns "silently truncated judgment" into a clear error.
MAX_CONTEXT_TOKENS = 64_000
_CHARS_PER_TOKEN = 3.6

QUESTION_TYPES = ("noul", "choice", "score")

# Env var / media-config provider id. Mirrors _PROVIDER_ENV_KEYS in serve.py.
PROVIDER = "typesafe"
ENV_KEY = "TH_TYPESAFE_API_KEY"
MEDIA_CONFIG_PATH = os.path.join(os.path.expanduser("~/.test-harness"),
                                 "media-config.json")


class JevError(RuntimeError):
    """Any failure reaching or parsing Jev. ALWAYS catchable: no consumer may
    let this escape into a build. The message is safe to log (it never carries
    the key)."""


class JevUnavailable(JevError):
    """No key configured. Distinct from a call failure so a consumer can say
    "not wired up" rather than "the judge errored"."""


def resolve_key(explicit=None):
    # type: (Optional[str]) -> Optional[str]
    """Env var first, then media-config.json - the same order as serve.py's
    _resolve_provider_key, repeated here so the CLI tools (ds_lint) work with
    no daemon running. The daemon passes its own resolved key explicitly, which
    keeps guest-key isolation intact (a guest must never fall through to the
    host's credential)."""
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()
    v = os.environ.get(ENV_KEY)
    if v and v.strip():
        return v.strip()
    try:
        with open(MEDIA_CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception:
        return None
    p = cfg.get(PROVIDER) if isinstance(cfg, dict) else None
    if isinstance(p, dict):
        k = p.get("api_key")
        if isinstance(k, str) and k.strip():
            return k.strip()
    return None


def available(explicit=None):
    # type: (Optional[str]) -> bool
    return bool(resolve_key(explicit))


# The ONE global switch, read from the same file the daemon persists it to
# (COMPACT_CONFIG_PATH in serve.py). Read straight off disk rather than through
# serve so the CLI tools (ds_lint) honour it with no daemon running and no
# import cycle. Absent file or absent key -> False, which matches
# COMPACT_DEFAULTS["jevJudge"] and keeps "off" the state that needs no config.
_COMPACT_CONFIG_PATH = os.path.join(os.path.expanduser("~/.test-harness"),
                                    "compact-config.json")


def enabled():
    # type: () -> bool
    """The user's global `jevJudge` preference. Consumers gate on
    `enabled() and available()`: the setting alone is an intent, the key alone
    is a capability, and only the pair makes the fast path real."""
    try:
        with open(_COMPACT_CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        return bool(cfg.get("jevJudge")) if isinstance(cfg, dict) else False
    except Exception:
        return False


def _state_text(state):
    # type: (Any) -> str
    """State may be a string, a JSON object, or an array of text values. We
    serialise non-strings for the size estimate only; the wire format keeps
    whatever the caller sent."""
    if isinstance(state, str):
        return state
    try:
        return json.dumps(state, ensure_ascii=False)
    except Exception:
        return str(state)


def estimate_tokens(state, questions):
    # type: (Any, Dict[str, Dict[str, Any]]) -> int
    """Rough character-based token estimate for the whole request. Rough is
    fine: it exists to catch the order-of-magnitude mistake (someone sending a
    whole page as state, rule 6) before spending a round trip on a 413."""
    chars = len(_state_text(state))
    try:
        chars += len(json.dumps(questions, ensure_ascii=False))
    except Exception:
        chars += sum(len(str(q)) for q in questions.values())
    return int(chars / _CHARS_PER_TOKEN)


def validate_questions(questions):
    # type: (Dict[str, Dict[str, Any]]) -> None
    """Enforce the mechanical jaggedness limits BEFORE spending a request.
    Raises ValueError naming the offending question id."""
    if not isinstance(questions, dict) or not questions:
        raise ValueError("questions must be a non-empty object keyed by question id")
    for qid, q in questions.items():
        if not isinstance(q, dict):
            raise ValueError("question %r must be an object" % qid)
        qtype = q.get("type")
        if qtype not in QUESTION_TYPES:
            raise ValueError("question %r: type must be one of %s"
                             % (qid, ", ".join(QUESTION_TYPES)))
        criteria = q.get("criteria")
        if qtype == "choice":
            if not isinstance(criteria, dict) or not criteria:
                raise ValueError("question %r: choice needs a criteria map "
                                 "{optionId: rubric}" % qid)
            if len(criteria) > MAX_CHOICE_OPTIONS:
                raise ValueError("question %r: choice has %d options, the cap is %d"
                                 % (qid, len(criteria), MAX_CHOICE_OPTIONS))
        elif qtype == "score":
            if not isinstance(criteria, list):
                raise ValueError("question %r: score needs an ORDERED criteria "
                                 "array of levels" % qid)
            if not (MIN_SCORE_LEVELS <= len(criteria) <= MAX_SCORE_LEVELS):
                raise ValueError("question %r: score has %d levels, allowed %d-%d"
                                 % (qid, len(criteria), MIN_SCORE_LEVELS,
                                    MAX_SCORE_LEVELS))
        elif criteria is not None and not isinstance(criteria, dict):
            raise ValueError("question %r: noul criteria must be a "
                             "{true, false} object when present" % qid)
        if not str(q.get("instructions") or "").strip():
            raise ValueError("question %r: instructions required (one clause, "
                             "read literally)" % qid)


# ── The one call ────────────────────────────────────────────────────────────

def ask(state, questions, model=DEFAULT_MODEL, api_key=None, timeout=45,
        max_retries=3, url=API_URL):
    # type: (Any, Dict[str, Dict[str, Any]], str, Optional[str], float, int, str) -> Dict[str, Any]
    """One POST to the System One endpoint. Returns the `answers` map keyed by
    the question ids you sent.

    Raises JevUnavailable when no key is configured and JevError for anything
    else. Retries 429 and 529 with exponential backoff, honouring `retry-after`
    when the response carries one; the official SDKs do this and we are not
    using one. 4xx other than 429 is a caller error and fails immediately -
    retrying a malformed request just spends the budget slower."""
    key = resolve_key(api_key)
    if not key:
        raise JevUnavailable("no %s key configured (set %s or add "
                             "%s.api_key to media-config.json)"
                             % (PROVIDER, ENV_KEY, PROVIDER))
    validate_questions(questions)
    est = estimate_tokens(state, questions)
    if est > MAX_CONTEXT_TOKENS:
        raise ValueError(
            "request is ~%dk tokens, over the %dk context budget - shard it "
            "(one request per page / per checklist chunk) rather than "
            "truncating; see jaggedness rule 6, small state"
            % (est // 1000, MAX_CONTEXT_TOKENS // 1000))

    body = json.dumps({"state": state, "model": model or DEFAULT_MODEL,
                       "questions": questions}).encode("utf-8")
    last = None  # type: Optional[str]
    for attempt in range(max(1, int(max_retries)) + 1):
        req = urllib.request.Request(
            url, method="POST", data=body,
            headers={"Authorization": "Bearer " + key,
                     "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8", "replace"))
            break
        except urllib.error.HTTPError as exc:
            try:
                detail = exc.read().decode("utf-8", "replace")[:300]
            except Exception:
                detail = ""
            last = "http %s %s" % (exc.code, detail)
            if exc.code not in (429, 529) or attempt >= max_retries:
                raise JevError("jev request failed: " + last)
            _sleep_backoff(attempt, exc.headers.get("retry-after")
                           if exc.headers else None)
        except Exception as exc:
            last = "%s: %s" % (type(exc).__name__, exc)
            if attempt >= max_retries:
                raise JevError("jev request failed: " + last)
            _sleep_backoff(attempt, None)
    else:  # pragma: no cover - the loop always breaks or raises
        raise JevError("jev request failed: " + (last or "unknown"))

    answers = payload.get("answers") if isinstance(payload, dict) else None
    if not isinstance(answers, dict):
        raise JevError("jev response has no answers object (got keys: %s)"
                       % (", ".join(sorted(payload))[:120]
                          if isinstance(payload, dict) else type(payload).__name__))
    return answers


def _sleep_backoff(attempt, retry_after):
    # type: (int, Optional[str]) -> None
    delay = None
    if retry_after:
        try:
            delay = float(retry_after)
        except (TypeError, ValueError):
            delay = None
    if delay is None:
        delay = (2.0 ** attempt) + random.random()
    time.sleep(min(delay, 30.0))


# ── Reading an answer ───────────────────────────────────────────────────────
# Every reader below is TOTAL: a missing or malformed answer yields the
# conservative value (a noul that does not pass, an empty ranking, an
# "escalate" band), never an exception. A judge that throws on a shape it did
# not expect would take a build down with it.

def noul_pass(answer, threshold=0.5):
    # type: (Any, float) -> bool
    """True when the statement is judged TRUE at or above `threshold`."""
    v = _noul_value(answer)
    return v is not None and v >= threshold


def noul_value(answer):
    # type: (Any) -> Optional[float]
    """The raw 0-1 noul, or None when the answer is missing/malformed."""
    return _noul_value(answer)


def _noul_value(answer):
    # type: (Any) -> Optional[float]
    if isinstance(answer, (int, float)) and not isinstance(answer, bool):
        return float(answer)
    if isinstance(answer, dict):
        v = answer.get("noul")
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return float(v)
    return None


def choice_ranked(answer, n=None):
    # type: (Any, Optional[int]) -> List[Tuple[str, float]]
    """The full probability distribution as [(optionId, probability), ...],
    highest first. A Choice returns the WHOLE map, not just the winner, which
    is what lets a caller compose a ranked shortlist instead of a single pick.
    Returns [] for a missing or malformed answer."""
    probs = None
    if isinstance(answer, dict):
        probs = answer.get("probabilities")
        if not isinstance(probs, dict) and isinstance(answer.get("choice"), str):
            # Winner-only response: a one-entry distribution is still a ranking.
            probs = {answer["choice"]: float(answer.get("confidence") or 1.0)}
    if not isinstance(probs, dict):
        return []
    rows = [(str(k), float(v)) for k, v in probs.items()
            if isinstance(v, (int, float)) and not isinstance(v, bool)]
    rows.sort(key=lambda kv: kv[1], reverse=True)
    return rows[:n] if n else rows


def confidence(answer):
    # type: (Any) -> Optional[float]
    if isinstance(answer, dict):
        c = answer.get("confidence")
        if isinstance(c, (int, float)) and not isinstance(c, bool):
            return float(c)
    return None


def band(conf, low=0.55, high=0.8):
    # type: (Optional[float], float, float) -> str
    """Three-band routing (https://docs.typesafe.ai/confidence).

      "act"       - confident enough to use the verdict as it stands
      "confirm"   - usable, but say so alongside the deterministic finding
      "escalate"  - hand this ONE item to Claude to read

    Thresholds are PER QUESTION TYPE, never one global number: a DS role
    inference and a requirement check do not deserve the same floor. Callers
    pass their own from tools/qa/jev_thresholds.json. A missing confidence
    escalates - an unknown is not a pass."""
    if conf is None:
        return "escalate"
    if conf >= high:
        return "act"
    if conf >= low:
        return "confirm"
    return "escalate"


# ── Thresholds, one file, loaded not remembered ─────────────────────────────
# Written by the Phase 4 calibration pass (tools/qa/jev_calibrate.py) and read
# by every consumer. Shipped values are the pre-calibration defaults: high
# enough that "flag, never block" holds.
_THRESHOLDS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "tools", "qa", "jev_thresholds.json")
_THRESHOLD_FALLBACK = {
    "default": {"low": 0.55, "high": 0.80, "noul": 0.50},
}


def thresholds(question_kind="default"):
    # type: (str) -> Dict[str, float]
    """Calibrated {low, high, noul} for one KIND of question ("ds_role",
    "requirement_item", "direction_axis", ...), falling back to "default"."""
    table = dict(_THRESHOLD_FALLBACK)
    try:
        with open(_THRESHOLDS_PATH, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        if isinstance(loaded, dict):
            for k, v in loaded.items():
                if isinstance(v, dict):
                    table[k] = v
    except Exception:
        pass
    row = table.get(question_kind) or table.get("default") or {}
    base = dict(_THRESHOLD_FALLBACK["default"])
    for k in ("low", "high", "noul"):
        v = row.get(k)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            base[k] = float(v)
    return base

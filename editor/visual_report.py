"""The Visual QA report: one saved record per /__qa/run that asked typed
visual checks.

Every judge call with its images exactly as they were sent, every question
with its answer, probabilities, confidence and band, and the decision of
whoever looked at it afterwards (the visual-qa subagent), so a "sure no" can
be found, looked at and settled. The daemon serves it as JSON and its images
as files; the Tasks panel renders it. Nothing in it is ever sent into a
thread.
"""

import copy
import json
import os
import re
import secrets
import shutil
import time
from typing import Any, Dict, List, Optional

REPORTS_DIR = os.path.expanduser("~/.test-harness/visual-qa")
KEEP = 60
CROP_PAD = 8  # visual_qa._CROP_PAD: a crop is its element's box plus this, in CSS px
ID_RE = re.compile(r"^\d{8}-\d{6}-[0-9a-f]{6}$")
FILE_RE = re.compile(r"^[\w.-]{1,160}\.(png|jpg|jpeg|webp)$")
BLANK_SHARE = 0.97


def _size(path):
    # type: (str) -> List[int]
    try:
        import typed_judge
        with open(path, "rb") as f:
            data = f.read(1 << 20)
        kind = typed_judge.sniff_image(data)
        wh = typed_judge.image_size(data, kind) if kind else None
        return [int(wh[0]), int(wh[1])] if wh else [0, 0]
    except Exception:
        return [0, 0]


def save(report, out_dir, project=None, page=None, root=None):
    # type: (Dict[str, Any], str, Optional[str], Optional[str], Optional[str]) -> Optional[str]
    """Copy one run's typed checks and the images they used out of the QA
    temp dir; returns the report id, or None when the run asked nothing."""
    block = report.get("typedChecks")
    if not isinstance(block, dict) or not (block.get("checks") or block.get("rejected")):
        return None
    root = root or REPORTS_DIR
    rid = time.strftime("%Y%m%d-%H%M%S") + "-" + secrets.token_hex(3)
    dest = os.path.join(root, rid)
    os.makedirs(dest, exist_ok=True)
    out_real = os.path.realpath(out_dir)
    names = {}  # type: Dict[str, str]
    sizes = {}  # type: Dict[str, List[int]]

    def keep(path):
        # type: (Optional[str]) -> Optional[str]
        if not path:
            return None
        real = os.path.realpath(path)
        if not real.startswith(out_real + os.sep) or not os.path.isfile(real):
            return None
        if real not in names:
            base = os.path.basename(real)
            if not FILE_RE.match(base) or base in names.values():
                base = "img_%d.png" % len(names)
            shutil.copyfile(real, os.path.join(dest, base))
            names[real] = base
            sizes[base] = _size(real)
        return names[real]

    block = copy.deepcopy(block)
    for call in block.get("calls") or []:
        for im in call.get("images") or []:
            im["file"] = keep(im.pop("path", None))
            im["captureFile"] = keep(im.pop("capture", None))
    block["pageShotFile"] = keep(block.pop("pageShot", None))
    cs = report.get("casesSummary") or {}
    data = {
        "id": rid, "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "project": project, "page": page or report.get("page"), "url": report.get("url"),
        "verdict": report.get("verdict"), "mode": report.get("mode"),
        "cases": {"pass": cs.get("pass", 0), "total": cs.get("total", 0)} if cs else None,
        "reasons": [str(r) for r in (report.get("reasons") or [])[:10]],
        "sizes": sizes, "typedChecks": block,
    }
    with open(os.path.join(dest, "report.json"), "w", encoding="utf-8") as f:
        json.dump(data, f)
    prune(root)
    return rid


def prune(root=None, keep=KEEP):
    # type: (Optional[str], int) -> None
    root = root or REPORTS_DIR
    try:
        ids = sorted(d for d in os.listdir(root) if ID_RE.match(d))
    except OSError:
        return
    for d in ids[:-keep] if len(ids) > keep else []:
        shutil.rmtree(os.path.join(root, d), ignore_errors=True)


def load(rid, root=None):
    # type: (str, Optional[str]) -> Optional[Dict[str, Any]]
    if not ID_RE.match(rid or ""):
        return None
    try:
        with open(os.path.join(root or REPORTS_DIR, rid, "report.json"), "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def label(rid, check, value, note="", root=None):
    # type: (str, str, Any, str, Optional[str]) -> Optional[Dict[str, Any]]
    """Record the right answer to one check (from whoever looked at its
    images) on its report row; returns the row, or None when the report or
    the check does not exist. `value` is true/false for a yes/no question and
    an option id for a choice. Raises ValueError for a value of the wrong kind."""
    data = load(rid, root)
    if data is None:
        return None
    rows = (data.get("typedChecks") or {}).get("checks") or []
    row = next((r for r in rows if r.get("id") == check), None)
    if row is None:
        return None
    q = row.get("question") or {}
    if q.get("type") == "choice":
        if str(value) not in (q.get("criteria") or {}):
            raise ValueError("value must be one of: %s" % ", ".join(q.get("criteria") or {}))
        value = str(value)
        passed = (value in row["expect"]) if row.get("expect") else None
        agrees = value == row.get("answer")
    else:
        if isinstance(value, str) and value.lower() in ("true", "yes", "1", "false", "no", "0"):
            value = value.lower() in ("true", "yes", "1")
        if not isinstance(value, bool):
            raise ValueError("value must be true or false for a yes/no question")
        passed = value
        agrees = None if row.get("passed") is None else value == row.get("passed")
    row["escalation"] = {"value": value, "passed": passed, "agrees": agrees, "note": note,
                         "at": time.strftime("%Y-%m-%d %H:%M:%S")}
    path = os.path.join(root or REPORTS_DIR, rid, "report.json")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp, path)
    return row


def file_path(rid, name, root=None):
    # type: (str, str, Optional[str]) -> Optional[str]
    if not ID_RE.match(rid or "") or not FILE_RE.match(name or ""):
        return None
    path = os.path.join(root or REPORTS_DIR, rid, name)
    return path if os.path.isfile(path) else None


# ── Reading a row ───────────────────────────────────────────────────────────

def outcome(row):
    # type: (Dict[str, Any]) -> str
    """sure-no / sure-yes / unsure / answered / not-asked."""
    if row.get("status") != "answered":
        return "not-asked"
    if row.get("band") != "act":
        return "unsure"
    if row.get("passed") is False:
        return "sure-no"
    if row.get("passed") is True:
        return "sure-yes"
    return "answered"


OUTCOME_LABEL = {"sure-no": "Sure no", "sure-yes": "Sure yes", "unsure": "Unsure",
                 "answered": "Answered", "not-asked": "Not asked"}
STATUS_WHY = {"no-capture": "No screenshot of that name in this run.",
              "element-missing": "The element was not on the page, so there was nothing to crop.",
              "not-visible": "The element was hidden at that moment (optional check, not a failure).",
              "unavailable": "The judge did not answer.",
              "no-answer": "The judge answered without a usable value."}


def summary_line(block):
    # type: (Dict[str, Any]) -> str
    rows = block.get("checks") or []
    counts = {}  # type: Dict[str, int]
    for r in rows:
        k = outcome(r)
        counts[k] = counts.get(k, 0) + 1
    parts = ["%d %s" % (counts[k], OUTCOME_LABEL[k].lower())
             for k in ("sure-no", "sure-yes", "unsure", "answered", "not-asked") if counts.get(k)]
    return ", ".join(parts) or "no checks"


def _fmt(v, nd=2):
    # type: (Any, int) -> str
    if v is None:
        return "-"
    try:
        return ("%." + str(nd) + "f") % float(v)
    except (TypeError, ValueError):
        return str(v)


def answer_text(row):
    # type: (Dict[str, Any]) -> str
    q = row.get("question") or {}
    if q.get("type") == "choice":
        return str(row.get("answer")) if row.get("answer") is not None else "-"
    n = row.get("noul")
    if n is None:
        return "-"
    # A noul is "yes" at its kind's threshold, which is what `passed` records.
    return "%s (true %s)" % ("yes" if row.get("passed") else "no", _fmt(n, 3))


def text_table(data):
    # type: (Dict[str, Any]) -> str
    """The same report as plain text, for the task's Result pane."""
    block = data.get("typedChecks") or {}
    lines = []
    calls = {c.get("n"): c for c in block.get("calls") or []}
    order = {"sure-no": 0, "unsure": 1, "answered": 2, "sure-yes": 3, "not-asked": 4}
    for r in sorted(block.get("checks") or [], key=lambda r: order.get(outcome(r), 9)):
        call = calls.get(r.get("call")) or {}
        imgs = "; ".join(i.get("label") or "" for i in call.get("images") or []) or ", ".join(r.get("images") or [])
        o = outcome(r)
        lines.append("%s  %s" % (OUTCOME_LABEL[o].upper(), r.get("id")))
        lines.append("  question: %s" % ((r.get("question") or {}).get("instructions") or r.get("claim") or ""))
        if r.get("expect"):
            lines.append("  expected: %s" % ", ".join(r["expect"]))
        if o == "not-asked":
            lines.append("  why: %s" % (r.get("message") or STATUS_WHY.get(r.get("status"), r.get("status"))))
        else:
            lines.append("  answer: %s  confidence: %s  band: %s" % (answer_text(r), _fmt(r.get("confidence")),
                                                                       r.get("band")))
            if r.get("probabilities"):
                lines.append("  probabilities: %s" % ", ".join(
                    "%s %s" % (k, _fmt(v)) for k, v in sorted(r["probabilities"].items(), key=lambda kv: -kv[1])))
        lines.append("  image: %s" % imgs)
        lines.append("  source: %s" % (r.get("source") or "screen criteria"))
    for rj in block.get("rejected") or []:
        lines.append("REJECTED  %s: %s (%s)" % (rj.get("id") or rj.get("index"), rj.get("statement") or "",
                                                 rj.get("reason")))
    return "\n".join(lines)

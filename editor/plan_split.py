"""Plan-mode split groups: who claims what, and the plan check once they finish.

Answering a plan gate with "split" makes the APP open one real thread per plan
item (app.js spawnPlanSplitRuns). Those threads start at the same moment in
the SAME working tree. On suss-cal (2026-09-29) one split thread saw its
sibling's edit in `git status`, took it for its own subagent's stray, and ran
`git checkout -- admin-nav.js`, wiping the sibling's work; nothing ever
compared the finished work with the plan.

So a split is a GROUP:
  - each item CLAIMS what it writes: a whole file (`path`) or a region of a
    shared file (`path#region`). Parallelism is decided by region, not file:
    unrelated changes to different parts of one big file are the normal case
    for a split (suss-cal 2026-09-30: seven unrelated changes to one form were
    merged into ONE thread because they "share two files");
  - each thread is told its siblings' claims (`sibling_block`);
  - the daemon records the group on every thread (`RunState.split`, persisted
    on the spawned event) and snapshots the approved plan onto item 0;
  - when every thread has finished or been stopped, the daemon opens a
    SEPARATE plan-check thread (`check_brief`). Not the planning thread: that
    one may be stopped, and the user stopping it must stay stopped.

Pure functions only: serve.py owns RUNS and spawning, this owns the shapes and
the words. Python 3.9-safe (the daemon runs 3.9).
"""
import re
from typing import List, Optional, Tuple

MAX_ITEMS = 4
MAX_OWNS = 40
REPORT_CHARS = 1500
BRIEF_CHARS = 6000
PLAN_CHARS = 15000
ASK_CHARS = 3000
SIBLING_MARK = "\n\n---\nPARALLEL THREADS"
# Typed go-aheads in the planning thread are commands, not asks.
_APPROVALS = {"split", "split it", "yes", "go", "yes go", "go ahead", "do it", "ok", "okay"}

_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,120}$")


def _clean_path(p) -> Optional[str]:
    """A project-relative path, or None when it is not one we will trust."""
    if not isinstance(p, str):
        return None
    p = p.strip().replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    if not p or len(p) > 300 or p.startswith("/") or ".." in p.split("/"):
        return None
    return p


def _clean_claim(c) -> Optional[str]:
    """`path` or `path#region`, normalised; None when unusable."""
    if not isinstance(c, str):
        return None
    path, sep, region = c.partition("#")
    path = _clean_path(path)
    if not path:
        return None
    region = " ".join(region.split())[:120]
    return path + "#" + region if sep and region else path


def claim_parts(claim: str) -> Tuple[str, Optional[str]]:
    path, sep, region = claim.partition("#")
    return path, (region.strip().lower() if sep and region.strip() else None)


def normalize(raw, parent_run_id) -> Optional[dict]:
    """Validate the `split` object the app posts with each split thread.

    Returns {"id", "parent", "index", "items": [{"title", "owns"}]} or None.
    `parent` comes from the daemon's own resolution of the parent run, never
    from the body, so a group can only ever report back to a real thread."""
    if not isinstance(raw, dict) or not parent_run_id:
        return None
    sid = raw.get("id")
    if not isinstance(sid, str) or not _ID_RE.match(sid):
        return None
    items_raw = raw.get("items")
    if not isinstance(items_raw, list) or not items_raw:
        return None
    items = []
    for it in items_raw[:MAX_ITEMS]:
        if not isinstance(it, dict):
            return None
        title = str(it.get("title") or "Plan item").strip()[:60] or "Plan item"
        owns = []
        raw_owns = it.get("owns") if isinstance(it.get("owns"), list) else []
        for c in raw_owns[:MAX_OWNS]:
            c = _clean_claim(c)
            if c and c not in owns:
                owns.append(c)
        items.append({"title": title, "owns": owns})
    idx = raw.get("index")
    if not isinstance(idx, int) or isinstance(idx, bool) or not (0 <= idx < len(items)):
        return None
    return {"id": sid, "parent": str(parent_run_id), "index": idx, "items": items}


def overlaps(items: List[dict]) -> List[dict]:
    """Claims two items cannot both hold: the same file whole in two items, a
    whole file in one and a region of it in another, or the same region
    named twice. Different regions of one file are fine. [{"path", "titles"}]"""
    whole, regions = {}, {}
    for it in items:
        t = it.get("title") or "Plan item"
        for c in it.get("owns") or []:
            path, region = claim_parts(c)
            if region is None:
                whole.setdefault(path, []).append(t)
            else:
                regions.setdefault((path, region), []).append(t)
    out = []
    for path, ts in whole.items():
        others = [x for (p, _), rs in regions.items() if p == path for x in rs]
        if len(ts) > 1 or others:
            out.append({"path": path, "titles": ts + others})
    for (path, region), ts in regions.items():
        if len(ts) > 1 and path not in whole:
            out.append({"path": path + "#" + region, "titles": ts})
    return out


def _owns_line(owns: List[str]) -> str:
    return ", ".join(owns) if owns else "(not declared - see the brief)"


def sibling_block(split: dict) -> str:
    """Appended to a split thread's brief, so it knows it is not alone."""
    items = split["items"]
    me = split["index"]
    lines = [
        SIBLING_MARK.lstrip("\n") + " - read this before you run git or edit a shared file.",
        "You are item %d of %d split from one plan. The other items run AT THE SAME TIME, "
        "in this SAME working tree. `path#region` means only that part of a shared file:"
        % (me + 1, len(items)),
    ]
    for i, it in enumerate(items):
        if i != me:
            lines.append('  - item %d "%s" claims: %s' % (i + 1, it["title"], _owns_line(it["owns"])))
    lines += [
        "You claim: %s" % _owns_line(items[me]["owns"]),
        "- In a file you share with a sibling, change ONLY your regions: re-read the lines "
        "right before each edit, use a targeted replacement (Edit, or an exact-string "
        "replace), and never rewrite, reformat or re-save the whole file. A whole-file write "
        "from an earlier read erases whatever a sibling changed since.",
        "- `git status` and `git diff` show EVERY thread's uncommitted work. A change you did "
        "not make is a sibling's work in progress: leave it alone.",
        "- Never discard changes (`git checkout`, `git restore`, `git stash`, "
        "`git reset --hard`, `git clean`): they wipe every thread's edits in that path. To "
        "undo your own edit, edit it back.",
        "- If your item needs a change in a sibling's claim, say so in your report instead of "
        "making it: a plan-check thread runs after every item finishes and picks it up.",
        "- A subagent you dispatch (ds-guardian, visual-verifier) works in this same tree. If "
        "it reports touching something outside your claims, report that; never revert it.",
    ]
    return "\n\n" + "\n".join(lines)


def thread_role(guards, split, split_check) -> Optional[dict]:
    """What a thread is in the plan/split flow, for the runs list and the
    thread header: the PLANNING thread (plan mode armed at spawn), one SPLIT
    item, or the PLAN CHECK opened after a split settles. None otherwise.
    Read off the spawn record, so it holds for historical runs too."""
    if isinstance(split, dict) and isinstance(split.get("items"), list):
        return {"role": "split", "index": split.get("index", 0), "count": len(split["items"]),
                "parent": split.get("parent"), "group": split.get("id")}
    if isinstance(split_check, dict):
        return {"role": "check", "parent": split_check.get("parent"), "group": split_check.get("group")}
    if isinstance(guards, dict) and guards.get("plan"):
        return {"role": "plan"}
    return None


def strip_sibling_block(text: str) -> str:
    i = (text or "").find(SIBLING_MARK)
    return text[:i] if i >= 0 else (text or "")


def group_ready(split: dict, members: List[dict]) -> bool:
    """True once every item has a thread and every thread is SETTLED: finished
    a turn, or stopped by the user. A thread that is mid-turn (including a
    user follow-up) holds the check back, so it never races live edits.
    `members` rows: {"index", "settled"}."""
    n = len(split.get("items") or [])
    if n == 0 or not members:
        return False
    have = {m.get("index") for m in members}
    if not all(i in have for i in range(n)):
        return False
    return all(m.get("settled") for m in members)


def worth_checking(members: List[dict]) -> bool:
    """A group the user stopped entirely has nothing to check."""
    return any(not m.get("stopped") for m in members)


def _user_words(text: str) -> str:
    """The user's own words from a chat message: the app wraps the first one
    in routing context, and the user's text follows the last context tag."""
    text = text or ""
    cut = max((text.rfind(tag) + len(tag) for tag in ("</chat-target>", "</selected-nodes>")
               if text.rfind(tag) >= 0), default=0)
    text = text[cut:].strip()
    return text if len(text) <= ASK_CHARS else "[...] " + text[-ASK_CHARS:]


def plan_snapshot(events: List[dict]) -> dict:
    """The approved plan + the user's asks, read off the planning thread's
    events at the moment the split opens. {"plan": str, "asks": [str]}.

    The plan is the latest assistant turn that carried a plan gate card and
    has real body (a re-emitted bare card after a typed "split" does not)."""
    turns, cur, asks = [], [], []
    for e in events or []:
        d = e.get("data") if isinstance(e.get("data"), dict) else {}
        if e.get("type") == "user_message":
            turns.append("".join(cur))
            cur = []
            t = d.get("text") or ""
            if (t and not t.startswith(("[decision:", "[split-reconcile]", "[watchdog]"))
                    and re.sub(r"[^a-z ]", "", t.lower()).strip() not in _APPROVALS):
                asks.append(_user_words(t))
        elif d.get("type") == "text_delta":
            cur.append(d.get("delta") or "")
        elif d.get("type") == "text" and isinstance(d.get("text"), str):
            cur.append(d["text"])
    turns.append("".join(cur))
    carded = [t for t in turns if 'id="plan-next' in t]
    plan = next((t for t in reversed(carded) if len(t) >= 800), carded[-1] if carded else "")
    if len(plan) > PLAN_CHARS:
        plan = plan[:PLAN_CHARS] + " [...]"
    return {"plan": plan, "asks": [a for a in asks if a][-6:]}


def _cap(text: str, n: int) -> str:
    text = (text or "").strip()
    return text if len(text) <= n else text[:n] + " [...]"


def check_brief(split: dict, members: List[dict], snapshot: Optional[dict]) -> str:
    """The first message of the plan-check thread the daemon opens once the
    group settles. Self-contained: this thread saw neither the plan nor any of
    the work. `members` rows: {"index", "runId", "status", "stopped", "brief",
    "report"}."""
    snapshot = snapshot or {}
    by_index = {}
    for m in members:
        by_index.setdefault(m.get("index"), m)
    n = len(split["items"])
    out = [
        "PLAN CHECK. The user approved a plan and it was split into %d threads that ran at "
        "the same time in this working tree. You built none of it. Check what is on disk "
        "NOW against the plan, fix what is missing or was overwritten, and report. Do not "
        "re-plan and do not wait for the user: do it in this turn." % n,
        "",
    ]
    if snapshot.get("asks"):
        out.append("WHAT THE USER ASKED (their own words, in order):")
        out += ["<<<", "\n---\n".join(snapshot["asks"]), ">>>", ""]
    if snapshot.get("plan"):
        out += ["THE PLAN THEY APPROVED:", "<<<", snapshot["plan"].strip(), ">>>", ""]
    out.append("THE ITEMS:")
    for i in range(n):
        it = split["items"][i]
        m = by_index.get(i) or {}
        out.append('%d. "%s" - thread %s - %s' % (
            i + 1, it["title"], m.get("runId") or "?",
            "STOPPED by the user" if m.get("stopped") else (m.get("status") or "done")))
        out.append("   claims: %s" % _owns_line(it["owns"]))
        if m.get("stopped"):
            out.append("   The user stopped this thread. Do NOT check it and do NOT build it; "
                       "list it as STOPPED.")
            continue
        out.append("   its brief: <<<\n%s\n>>>" % _cap(strip_sibling_block(m.get("brief") or ""), BRIEF_CHARS))
        out.append("   its closing report: <<<\n%s\n>>>" % (_cap(m.get("report") or "", REPORT_CHARS) or "(none)"))
    out += [
        "",
        "HOW TO CHECK. A report that says done is a claim; the files are the evidence.",
        "1. For each item that was not stopped, open what it claims and confirm every UI, "
        "Logic and Copy row of its brief is on disk NOW.",
        "2. A row that was built and is gone was overwritten by another thread: that is "
        "UNDONE, not MISSING. The thread's report and the file tell them apart.",
        "3. Check coverage too: anything the user asked for that no item carried is MISSING.",
        "4. One verdict per item: DONE, MISSING (never built), UNDONE (built, then "
        "overwritten) or DRIFT (built differently from the plan).",
        "5. Re-apply MISSING and UNDONE rows yourself with targeted edits, touching only "
        "those rows. DRIFT, or anything that needs a judgment call, goes to the user as a "
        "decision card: never silently rebuild it to match the plan.",
        "6. Never run `git checkout`, `git restore`, `git stash`, `git reset --hard` or "
        "`git clean`. Changes in `git status` that belong to no item are other threads' "
        "work; leave them.",
        "7. Run any subagent in the foreground (run_in_background: false) and do not end "
        "this turn before the verdicts are written.",
        "Finish with one line per item: its title, its verdict, and what you fixed.",
    ]
    return "\n".join(out)

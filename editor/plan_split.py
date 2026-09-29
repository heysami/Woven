"""Plan-mode split groups: who owns what, and the plan check once they finish.

Answering a plan gate with "split" makes the APP open one real thread per plan
item (app.js spawnPlanSplitRuns). Those threads start at the same moment in
the SAME working tree, and before this module nothing connected them: the
daemon kept no record that they belonged together, no thread knew which files
its siblings were writing, and nothing ever compared the finished work with
the plan. On suss-cal (2026-09-29) one split thread saw its sibling's edit in
`git status`, took it for its own subagent's stray, and ran
`git checkout -- admin-nav.js`, wiping the sibling's work. Nothing noticed
until the user did.

So a split is now a GROUP:
  - each thread is told who its siblings are and which files each one owns
    (`sibling_block`, appended to its brief at spawn);
  - the daemon records the group on every thread (`RunState.split`, persisted
    on the spawned event so it survives a restart);
  - when the last thread in the group finishes its turn, the daemon queues a
    `[split-reconcile]` message on the planning thread (`reconcile_message`),
    which checks every item against the plan on disk and re-applies what was
    missed or overwritten.

Pure functions only: serve.py owns RUNS and the queue, this owns the shapes and
the words. Python 3.9-safe (the daemon runs 3.9).
"""
import re
from typing import List, Optional

MAX_ITEMS = 4
MAX_OWNS = 40
REPORT_CHARS = 1500

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
        for p in raw_owns[:MAX_OWNS]:
            c = _clean_path(p)
            if c and c not in owns:
                owns.append(c)
        items.append({"title": title, "owns": owns})
    idx = raw.get("index")
    if not isinstance(idx, int) or isinstance(idx, bool) or not (0 <= idx < len(items)):
        return None
    return {"id": sid, "parent": str(parent_run_id), "index": idx, "items": items}


def _owns_line(owns: List[str]) -> str:
    return ", ".join(owns) if owns else "(not declared - see the brief)"


def sibling_block(split: dict) -> str:
    """Appended to a split thread's brief, so it knows it is not alone."""
    items = split["items"]
    me = split["index"]
    others = [(i, it) for i, it in enumerate(items) if i != me]
    lines = [
        "",
        "",
        "---",
        "PARALLEL THREADS - read this before you run git or touch a file you do not own.",
        "You are item %d of %d split from one plan. The other items run AT THE SAME TIME, "
        "in this SAME working tree:" % (me + 1, len(items)),
    ]
    for i, it in others:
        lines.append('  - item %d "%s" owns: %s' % (i + 1, it["title"], _owns_line(it["owns"])))
    lines += [
        "You own: %s" % _owns_line(items[me]["owns"]),
        "- `git status` and `git diff` show EVERY thread's uncommitted work, not only yours. "
        "A changed file you did not change is another thread's work in progress: leave it "
        "alone. Mention it in your report only if it blocks you.",
        "- Never discard changes: no `git checkout`, `git restore`, `git stash`, "
        "`git reset --hard` or `git clean`. They wipe EVERY thread's edits in that path, "
        "not just yours. To undo your own edit, edit it back.",
        "- Do not write to a file another item owns. If your item needs a change there, "
        "say so in your report: the plan check that runs after every thread finishes "
        "picks it up.",
        "- A subagent you dispatch (ds-guardian, visual-verifier) works in this same tree. "
        "If it reports touching a file outside yours, report that; never revert it.",
    ]
    return "\n".join(lines)


def overlaps(items: List[dict]) -> List[dict]:
    """Files claimed by more than one item: [{"path", "titles"}]."""
    seen = {}
    for it in items:
        for p in it.get("owns") or []:
            seen.setdefault(p, []).append(it.get("title") or "Plan item")
    return [{"path": p, "titles": t} for p, t in seen.items() if len(t) > 1]


def group_ready(split: dict, members: List[dict]) -> bool:
    """True once every item in the group has a thread and every thread has
    finished a turn. `members` rows: {"index", "finished"}. A thread that is
    mid-turn again (the user replied to it) holds the check back, so the plan
    check never races a thread that is still editing."""
    n = len(split.get("items") or [])
    if n == 0 or not members:
        return False
    have = {m.get("index") for m in members}
    if not all(i in have for i in range(n)):
        return False
    return all(m.get("finished") for m in members)


def reconcile_message(split: dict, members: List[dict]) -> str:
    """The message queued on the PLANNING thread once the group is done.

    `members` rows: {"index", "title", "runId", "status", "owns", "report"}.
    Self-contained on purpose: it must work on a thread whose preamble predates
    this feature, and on any runtime."""
    by_index = {}
    for m in members:
        by_index.setdefault(m.get("index"), m)
    n = len(split["items"])
    out = [
        "[split-reconcile] All %d threads opened from your plan have finished. This is "
        "the plan check. It is part of the plan the user already approved: do NOT answer "
        "it with a new plan or a plan gate card, and do not wait for the user. Do it now, "
        "in this turn." % n,
        "",
        "Items, as the user approved them:",
    ]
    for i in range(n):
        it = split["items"][i]
        m = by_index.get(i) or {}
        report = (m.get("report") or "").strip()
        if len(report) > REPORT_CHARS:
            report = report[:REPORT_CHARS] + " [...]"
        out.append('%d. "%s" - thread %s - %s' % (
            i + 1, it["title"], m.get("runId") or "?", m.get("status") or "finished"))
        out.append("   owns: %s" % _owns_line(it["owns"]))
        out.append("   its closing report: %s" % (report or "(none)"))
    out += [
        "",
        "Check each item against the PLAN you wrote in this thread (its UI, Logic and Copy "
        "rows), not against the reports above. A report that says done is a claim.",
        "1. Open the files each item owns and confirm every one of its rows is on disk NOW.",
        "2. A row that was built and is no longer there was overwritten by another thread: "
        "that is UNDONE, not MISSING. Look for it in the thread's report and in the file.",
        "3. Give each item exactly one verdict: DONE, MISSING (a row was never built), "
        "UNDONE (built, then overwritten) or DRIFT (built differently from the plan).",
        "4. Re-apply MISSING and UNDONE rows yourself, now, touching only those rows. DRIFT, "
        "or anything that needs a judgment call, goes to the user as a decision card: do "
        "not silently rebuild it to match the plan.",
        "5. Never run `git checkout`, `git restore`, `git stash`, `git reset --hard` or "
        "`git clean`: other threads may still be working in this tree. Changes in "
        "`git status` that belong to no item are other threads' work; leave them.",
        "6. Run any subagent in the foreground (run_in_background: false) and do not end "
        "this turn before the verdicts are written.",
        "Finish with one line per item: its title, its verdict, and what you fixed.",
    ]
    return "\n".join(out)

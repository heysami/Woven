"""Plan-mode split groups: who claims what, and the plan check once they finish.

Answering a plan gate with "execute" makes the APP open one real thread per plan
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
    one may be stopped, and the user stopping it must stay stopped;
  - an item may carry WIREFRAME CHECKS: its AFTER drawings as literal
    questions for the image judge (`check_manifest` validates them). The
    split thread stores them in visual-checks.json with the selectors it
    built, and the plan check asks them, so a build that follows its brief
    but not the drawing the user approved is DRIFT (suss-cal 2026-10-15: a
    "toggle" drawn as switch rows shipped as Yes/No radios).

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
# Typed go-aheads in the planning thread are commands, not asks. "split" is
# the gate's old button word, "execute" its current one.
_APPROVALS = {"execute", "execute it", "execute the plan", "split", "split it",
              "yes", "go", "yes go", "go ahead", "do it", "ok", "okay"}

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


# ── Wireframe checks ────────────────────────────────────────────────────────
# A check is a visual_checks shape (shows, which + list + expect) or a literal
# statement, plus `page`, `where` (the tab or panel it is on and the box to
# crop, in words: the split thread turns it into a selector) and `query`. It
# may name only what the screen shows: "follows the wireframe" is the intent
# the judge cannot answer, so naming the drawing is refused.
MAX_CHECKS = 24
CHECK_SOURCE = "screen criteria: plan %s item %d"
_DRAWING_RE = re.compile(r"\b(wireframes?|drawings?|mock-?ups?|sketch(es)?|the plan|the design|"
                         r"the brief|as drawn|as planned)\b", re.I)
_CHECK_ID_RE = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")


def _check_problems(c, seen: set) -> List[str]:
    """Why one manifest check cannot be asked; [] when it can."""
    import visual_checks
    if not isinstance(c, dict):
        return ["a check is an object"]
    out = []
    cid = c.get("id")
    if not isinstance(cid, str) or not _CHECK_ID_RE.match(cid):
        out.append("id must be letters, digits, _ . - (max 64)")
    elif cid in seen:
        out.append("id %s is used twice" % cid)
    else:
        seen.add(cid)
    page = _clean_path(c.get("page"))
    if not page or not page.endswith(".html"):
        out.append("page must be the screen's .html file")
    where = c.get("where")
    if not isinstance(where, str) or not where.strip() or len(where) > 200:
        out.append("where must say in a short phrase which tab or panel the screen is on "
                   "and which box to crop")
    query = c.get("query")
    if query is not None and (not isinstance(query, str) or len(query) > 300 or "\n" in query):
        out.append("query must be a URL query such as scheme=x&v=v1")
    m = _DRAWING_RE.search(" ".join(str(c.get(k) or "") for k in ("x", "statement")))
    if m:
        out.append("names %r instead of what the screen shows: say the row, control or place "
                   "the judge must see" % m.group(0))
    if c.get("compare"):
        out.append("a wireframe check looks at one screen: drop compare")
        return out
    try:
        q, need = visual_checks.question(c)
    except ValueError as exc:
        return out + [str(exc)]
    if need != 1:
        out.append("this shape compares two images: use shows, which or a statement")
    elif q["type"] == "choice":
        exp = c.get("expect")
        exp = [exp] if isinstance(exp, str) else exp
        if not isinstance(exp, list) or not exp:
            out.append("a which check needs expect: the option the AFTER wireframe shows")
        elif not set(exp) <= set(q["criteria"]):
            out.append("expect must be options of list %s: %s"
                       % (c.get("list"), ", ".join(q["criteria"])))
    return out


def check_manifest(doc) -> List[str]:
    """Every problem with a split manifest, one line each; [] when it opens.
    The planner runs this (`plan_split.py --check`) before it shows the card."""
    if not isinstance(doc, dict) or not isinstance(doc.get("items"), list):
        return ['the manifest must be {"items": [...]}']
    items = [it for it in doc["items"] if isinstance(it, dict)]
    out = []
    if not items:
        out.append("no items")
    if len(items) > MAX_ITEMS:
        out.append("%d items, but only the first %d open" % (len(items), MAX_ITEMS))
    seen = set()  # type: set
    for i, it in enumerate(items[:MAX_ITEMS]):
        name = 'item %d "%s"' % (i + 1, str(it.get("title") or "")[:60])
        if not str(it.get("brief") or "").strip():
            out.append(name + ": no brief")
        checks = it.get("checks")
        if checks is None:
            continue
        if not isinstance(checks, list):
            out.append(name + ": checks must be a list")
            continue
        if len(checks) > MAX_CHECKS:
            out.append("%s: %d checks, at most %d" % (name, len(checks), MAX_CHECKS))
        for j, c in enumerate(checks[:MAX_CHECKS]):
            label = c.get("id") if isinstance(c, dict) and c.get("id") else "#%d" % (j + 1)
            out += ["%s, check %s: %s" % (name, label, why) for why in _check_problems(c, seen)]
    owned = [{"title": str(it.get("title") or ""),
              "owns": [x for x in (_clean_claim(o) for o in (it.get("owns") or [])) if x]}
             for it in items[:MAX_ITEMS]]
    out += ["%s is claimed by %s" % (o["path"], " and ".join('"%s"' % t for t in o["titles"]))
            for o in overlaps(owned)]
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
        "- Your brief was written by a planner that read less of the code than you will. If "
        "it names a control, helper or layout for something you add into an existing card, "
        "table, list or form, and that container's current entries are built another way, "
        "do not follow it silently: build the rest, leave that part, and end your reply "
        "with a decision card naming both ways (the neighbours' and the brief's).",
    ]
    if split.get("parent"):
        lines.append(
            "- WIREFRAME CHECKS. If your item in `plan-splits/%s.json` (items[%d], \"%s\") has "
            "`checks`, they are the plan's AFTER drawing as literal questions for the image "
            "judge. Once your build is in place, store each one in "
            "`source/<prototype>/visual-checks.json` under `pages[\"<its page>\"]` (create the "
            "file or the entry if missing, keep what is there, replace an entry with the same "
            "id). Copy `id`, `shape`, `x`, `list`, `expect` or `statement` as written, "
            "correcting only a quoted label to the text the screen renders. Add `selector`: "
            "the element its `where` names in the markup you built (the entry's own row for a "
            "control or label check; for a placement check the container the drawing puts it "
            "in, even when you built the entry outside it). When `where` needs clicks "
            "first (a tab, a slideout), the page entry becomes {\"steps\": [...], \"checks\": "
            "[...]}: add a step {\"label\", \"type\": \"click\", \"selector\"} and set `at` to "
            "`after:<label>`; otherwise `at` is `page`. Set `source` to \"%s\" and `query` to "
            "the URL query that shows that screen. Your visual-qa run then asks them. Never "
            "reword a check to fit what you built: one your build fails means the brief and "
            "the drawing disagree, so raise it with a decision card as above."
            % (split["parent"], me, items[me]["title"], CHECK_SOURCE % (split["parent"], me + 1)))
    return "\n\n" + "\n".join(lines)


def thread_role(guards, split, split_check, mode=None) -> Optional[dict]:
    """What a thread is in the plan/split flow, for the runs list and the
    thread header: one SPLIT item or the PLAN CHECK opened after a split
    settles (both fixed at spawn), else the mode its LATEST message ran in -
    a PLAN or TRIAGE thread. `mode` is that latest mode (None when no message
    carried one: a thread from before per-message modes, whose plan gate was
    armed at spawn in `guards`). None otherwise."""
    if isinstance(split, dict) and isinstance(split.get("items"), list):
        return {"role": "split", "index": split.get("index", 0), "count": len(split["items"]),
                "parent": split.get("parent"), "group": split.get("id")}
    if isinstance(split_check, dict):
        return {"role": "check", "parent": split_check.get("parent"), "group": split_check.get("group")}
    if mode is not None:
        return {"role": mode} if mode in ("plan", "triage") else None
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
    parent = split.get("parent") or "<planning run id>"
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
        "2. Then hold each item's UI against the PLAN's UI section above (its AFTER "
        "wireframes), not only against its brief: the same control, in the same place, "
        "beside the same neighbours. Built as the brief says but not as the wireframe shows "
        "is DRIFT: the user approved the wireframe, never the brief.",
        "   a. WIREFRAME CHECKS. Each item's `checks` (item N is items[N-1] in "
        "`plan-splits/%s.json`) are those drawings as literal questions. Each must be stored in "
        "`source/<prototype>/visual-checks.json` under its page with a `selector` and "
        "`source` \"%s\": store a missing one yourself (find the selector in the markup). "
        "Then, per page and query, ask them: `curl -sS -G \"$TH_DAEMON_URL/__qa/run\" "
        "--data-urlencode \"project=$TH_PROJECT_ID\" --data-urlencode \"run=$TH_RUN_ID\" "
        "--data-urlencode \"page=<slug>/<page>?<query>\" --data-urlencode \"checks=[]\"` "
        "(an empty `checks` asks the screen's stored criteria and nothing else; allow 7 "
        "minutes), then read `typedChecks.checks` from `GET "
        "$TH_DAEMON_URL/__qa/visual-report?id=<visualReport>&project=$TH_PROJECT_ID`, the "
        "rows whose `source` names this plan. `passed` false with `band` act is a sure no: "
        "DRIFT, and its decision card quotes the claim and the judge's answer. An unsure "
        "answer (`band` escalate) or `element-missing` goes to b for that check."
        % (parent, CHECK_SOURCE.replace("%d", "<N>") % parent),
        "   b. No `visualReport` in the answer means the image judge is off for this thread or "
        "not set up. Then, and for unsure checks or an item with no `checks`, read the markup "
        "that renders it, and when the code cannot settle what it looks like or where it "
        "sits, dispatch a visual-verifier with that AFTER wireframe and the checks' claims "
        "in its brief.",
        "3. A row that was built and is gone was overwritten by another thread: that is "
        "UNDONE, not MISSING. The thread's report and the file tell them apart.",
        "4. Check coverage too: anything the user asked for that no item carried is MISSING.",
        "5. One verdict per item: DONE, MISSING (never built), UNDONE (built, then "
        "overwritten), DRIFT (built differently from the plan) or WAITING (its report "
        "left a part for the user's decision; never build that part).",
        "6. Re-apply MISSING and UNDONE rows yourself with targeted edits, touching only "
        "those rows. DRIFT, or anything that needs a judgment call, goes to the user as a "
        "decision card: never silently rebuild it to match the plan.",
        "7. Never run `git checkout`, `git restore`, `git stash`, `git reset --hard` or "
        "`git clean`. Changes in `git status` that belong to no item are other threads' "
        "work; leave them.",
        "8. Run any subagent in the foreground (run_in_background: false) and do not end "
        "this turn before the verdicts are written.",
        "Finish with one line per item: its title, its verdict, and what you fixed.",
    ]
    return "\n".join(out)


if __name__ == "__main__":
    # python3 editor/plan_split.py --check plan-splits/<run id>.json
    import json
    import sys
    if len(sys.argv) != 3 or sys.argv[1] != "--check":
        print("usage: plan_split.py --check plan-splits/<run id>.json")
        sys.exit(2)
    try:
        with open(sys.argv[2], "r", encoding="utf-8") as f:
            _doc = json.load(f)
    except Exception as exc:
        print("cannot read %s: %s" % (sys.argv[2], exc))
        sys.exit(1)
    _problems = check_manifest(_doc)
    for _p in _problems:
        print("- " + _p)
    if _problems:
        sys.exit(1)
    print("OK: %d item(s), %d wireframe check(s)" % (
        len(_doc["items"]), sum(len(it.get("checks") or []) for it in _doc["items"]
                                if isinstance(it, dict))))

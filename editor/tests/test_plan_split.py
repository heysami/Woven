"""Plan-mode split groups: ownership, the git-discard guard, and the plan check.

Regression for suss-cal (2026-09-29): two threads split from one plan ran in
the same working tree with no link between them. One saw its sibling's edit in
`git status`, took it for its own subagent's stray and ran
`git checkout -- source/prototype/admin-nav.js`, wiping the sibling's work.
Nothing ever compared the finished threads with the plan.

And suss-cal (2026-09-30): seven unrelated changes to one form were merged into
ONE thread because they "share two files"; the plan check ran inside the
planning thread the user had stopped; a user-stopped duplicate triggered that
check; and a typed "split" opened a second copy of a still-running item.

Run: python3 -m unittest discover -s editor/tests -p test_plan_split.py -v
"""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

EDITOR = Path(__file__).resolve().parents[1]
REPO = EDITOR.parent
HOOK = REPO / ".claude" / "hooks" / "guard-shared-tree.py"
sys.path.insert(0, str(EDITOR))
import plan_split
import serve
from kinds import capabilities as caps

_spec = importlib.util.spec_from_file_location("guard_shared_tree", HOOK)
guard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(guard)

ITEMS = [
    {"title": "Quota utilisation screen", "owns": ["source/prototype/fa-fund.js",
                                                   "./source/prototype/fa-fund-overview.html"]},
    {"title": "Rename the sidebar entry", "owns": ["source/prototype/admin-nav.js"]},
]


def split(index, sid="plan1-abc"):
    return plan_split.normalize({"id": sid, "index": index, "items": ITEMS}, "plan1")


class NormalizeTests(unittest.TestCase):
    def test_valid_group_is_kept_with_clean_paths(self):
        s = split(1)
        self.assertEqual(s["parent"], "plan1")
        self.assertEqual(s["index"], 1)
        self.assertEqual(s["items"][0]["owns"][1], "source/prototype/fa-fund-overview.html")

    def test_parent_comes_from_the_daemon_not_the_body(self):
        s = plan_split.normalize({"id": "x", "index": 0, "items": ITEMS, "parent": "evil"}, "real")
        self.assertEqual(s["parent"], "real")

    def test_rejects_malformed(self):
        self.assertIsNone(plan_split.normalize({"id": "x", "index": 5, "items": ITEMS}, "p"))
        self.assertIsNone(plan_split.normalize({"id": "a b", "index": 0, "items": ITEMS}, "p"))
        self.assertIsNone(plan_split.normalize({"id": "x", "index": 0, "items": []}, "p"))
        self.assertIsNone(plan_split.normalize({"id": "x", "index": 0, "items": ITEMS}, None))
        self.assertIsNone(plan_split.normalize({"id": "x", "index": True, "items": ITEMS}, "p"))

    def test_region_claims_are_kept_and_cleaned(self):
        s = plan_split.normalize({"id": "x", "index": 0, "items": [
            {"title": "t", "owns": ["./form.html#  awardDueCard()   and CSS ", "form.html#"]}]}, "p")
        self.assertEqual(s["items"][0]["owns"], ["form.html#awardDueCard() and CSS", "form.html"])

    def test_escaping_paths_are_dropped(self):
        s = plan_split.normalize({"id": "x", "index": 0, "items": [
            {"title": "t", "owns": ["../other/secret.js", "/etc/passwd", "ok.js"]}]}, "p")
        self.assertEqual(s["items"][0]["owns"], ["ok.js"])


class SiblingBlockTests(unittest.TestCase):
    def test_names_siblings_and_their_claims_not_itself(self):
        text = plan_split.sibling_block(split(0))
        self.assertIn('"Rename the sidebar entry" claims: source/prototype/admin-nav.js', text)
        self.assertIn("You claim: source/prototype/fa-fund.js", text)
        self.assertNotIn('item 1 "Quota utilisation screen"', text)
        self.assertIn("git checkout", text)
        self.assertIn("never rewrite, reformat or re-save the whole file", text)
        self.assertEqual(plan_split.strip_sibling_block("brief" + text), "brief")

    def test_different_regions_of_one_file_run_in_parallel(self):
        items = [{"title": "Award date", "owns": ["form.html#awardDueCard()", "model.js#validators: award date"]},
                 {"title": "Quota copy", "owns": ["form.html#quota field", "model.js#labels: quota"]},
                 {"title": "Export", "owns": ["export.html"]}]
        self.assertEqual(plan_split.overlaps(items), [])

    def test_real_collisions_are_caught(self):
        same_whole = ITEMS + [{"title": "C", "owns": ["source/prototype/admin-nav.js"]}]
        self.assertEqual(plan_split.overlaps(same_whole)[0]["path"], "source/prototype/admin-nav.js")
        whole_and_part = [{"title": "A", "owns": ["form.html"]}, {"title": "B", "owns": ["form.html#x()"]}]
        self.assertEqual(plan_split.overlaps(whole_and_part)[0]["titles"], ["A", "B"])
        same_region = [{"title": "A", "owns": ["form.html#X()"]}, {"title": "B", "owns": ["form.html#x()"]}]
        self.assertEqual(plan_split.overlaps(same_region)[0]["path"], "form.html#x()")


PLAN_EVENTS = [
    {"type": "user_message", "data": {"text": "[Context: routing...]\n<chat-target prototype=\"p\">x</chat-target>\n\nrename award due date\nadd programme split"}},
    {"type": "agent", "data": {"type": "text_delta", "delta": "**1. UI** " + "row " * 300}},
    {"type": "agent", "data": {"type": "text_delta", "delta": '<decision-request id="plan-next-1">'}},
    {"type": "user_message", "data": {"text": "wrong text, call it Indicative First Award Date"}},
    {"type": "agent", "data": {"type": "text_delta", "delta": "**1. UI** revised " + "row " * 300 + '<decision-request id="plan-next-2">'}},
    {"type": "user_message", "data": {"text": "split"}},
    {"type": "agent", "data": {"type": "text_delta", "delta": '<decision-request id="plan-next-3">'}},
    {"type": "user_message", "data": {"text": "[decision:plan-next-3] split - Split it"}},
]


class GroupReadyTests(unittest.TestCase):
    def test_waits_for_every_item_and_every_thread(self):
        s = split(0)
        self.assertFalse(plan_split.group_ready(s, [{"index": 0, "settled": True}]))
        self.assertFalse(plan_split.group_ready(s, [{"index": 0, "settled": True},
                                                    {"index": 1, "settled": False}]))
        self.assertTrue(plan_split.group_ready(s, [{"index": 0, "settled": True},
                                                   {"index": 1, "settled": True}]))

    def test_a_fully_stopped_group_is_not_checked(self):
        self.assertFalse(plan_split.worth_checking([{"stopped": True}, {"stopped": True}]))
        self.assertTrue(plan_split.worth_checking([{"stopped": True}, {"stopped": False}]))

    def test_snapshot_takes_the_approved_plan_not_a_bare_re_emitted_card(self):
        snap = plan_split.plan_snapshot(PLAN_EVENTS)
        self.assertTrue(snap["plan"].startswith("**1. UI** revised"))
        self.assertEqual(snap["asks"][0], "rename award due date\nadd programme split")
        self.assertIn("wrong text, call it Indicative First Award Date", snap["asks"])
        self.assertFalse(any(a.startswith("[decision:") for a in snap["asks"]))

    def test_check_brief_is_self_contained_and_skips_stopped_items(self):
        rows = [{"index": 0, "runId": "a", "status": "done", "report": "x" * 5000,
                 "brief": "build the quota screen" + plan_split.sibling_block(split(0))},
                {"index": 1, "runId": "b", "status": "stopped", "stopped": True, "brief": "rename"}]
        text = plan_split.check_brief(split(0), rows, plan_split.plan_snapshot(PLAN_EVENTS))
        self.assertTrue(text.startswith("PLAN CHECK"))
        for word in ("DONE", "MISSING", "UNDONE", "DRIFT", "THE PLAN THEY APPROVED",
                     "WHAT THE USER ASKED", "build the quota screen"):
            self.assertIn(word, text)
        self.assertNotIn("PARALLEL THREADS", text)      # sibling block stripped
        self.assertIn("STOPPED by the user", text)
        self.assertIn("Do NOT check it and do NOT build it", text)
        self.assertNotIn("its brief: <<<\nrename", text)
        self.assertLess(len(text), 12000)              # a long report is truncated


class GuardHookTests(unittest.TestCase):
    BLOCKED = [
        # the exact command from the suss-cal incident
        'cd "/Users/sami/Documents/Woven IN USE/projects/suss-cal" && git checkout -- '
        'source/prototype/admin-nav.js && git status --porcelain | grep -v "^A  share/"',
        "git checkout .",
        "git -C source restore page.html",
        "git stash",
        "git stash push -m wip",
        "git reset --hard HEAD",
        "git clean -fd",
        "git switch main",
        "echo ok; git checkout HEAD -- a.js",
        "x=$(git checkout -- a.js)",
    ]
    ALLOWED = [
        "git status --porcelain",
        "git diff -- source/prototype/admin-nav.js",
        "git log --oneline -3",
        "git restore --staged a.js",
        "git stash list",
        "git reset HEAD a.js",
        "git clean -n",
        'grep -n "git checkout" notes.md',
        "python3 - <<'PY'\nprint('run git checkout -- x to undo')\nPY\necho done",
        "cat > /tmp/doc.md <<EOF\ngit reset --hard\nEOF",
    ]

    def test_blocks_discards(self):
        for cmd in self.BLOCKED:
            self.assertIsNotNone(guard.offending(cmd), cmd)

    def test_allows_reads_and_index_only(self):
        for cmd in self.ALLOWED:
            self.assertIsNone(guard.offending(cmd), cmd)

    def test_hook_process_denies_with_a_reason(self):
        payload = {"tool_name": "Bash", "tool_input": {"command": "git checkout -- a.js"}}
        out = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload),
                             capture_output=True, text=True, timeout=20).stdout
        d = json.loads(out)["hookSpecificOutput"]
        self.assertEqual(d["permissionDecision"], "deny")
        self.assertIn("other threads", d["permissionDecisionReason"])
        ok = subprocess.run([sys.executable, str(HOOK)], input="not json",
                            capture_output=True, text=True, timeout=20).stdout
        self.assertEqual(json.loads(ok), {})   # fails open


def fake_run(rid, split_obj=None, turn_done=True, turns=1, done=False, result="ok",
             brief="brief"):
    state = SimpleNamespace(run_id=rid, title=rid, split=split_obj, parent_run_id=None,
        project_root="/fixture/suss", project_id="suss", done=done, turn_done=turn_done,
        turns_completed=turns, stop_reason=None, jobs={}, lock=threading.Lock(), events=[],
        msg_queue=[], tier="scoped", prototype="prototype",
        guards={"visual": True, "dsGuard": True, "plan": True})
    def append(kind, data):
        state.events.append({"seq": len(state.events), "type": kind, "data": data})
    state.append = append
    append("user_message", {"text": brief})
    if turns:   # the CLI's result frame, as _drain_stdout records it
        append("agent", {"type": "status", "label": "done", "result": result})
    return state


class JoinTests(unittest.TestCase):
    def setUp(self):
        serve._SPLIT_JOINED.clear()
        self.parent = fake_run("plan1")
        s0 = split(0)
        s0["snapshot"] = plan_split.plan_snapshot(PLAN_EVENTS)
        self.a = fake_run("a", s0, result="quota built", brief="build the quota screen")
        self.b = fake_run("b", split(1), turn_done=False, turns=0)
        self.runs = {"plan1": self.parent, "a": self.a, "b": self.b}
        self.opened = []
        patches = [patch.dict(serve.RUNS, self.runs, clear=True),
                   patch.object(serve, "_split_open_check",
                                lambda body, pid, parent: self.opened.append((body, pid, parent)))]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def finish_b(self, result="renamed"):
        self.b.turn_done, self.b.turns_completed = True, 1
        self.b.append("agent", {"type": "status", "label": "done", "result": result})

    def test_opens_one_separate_check_thread_after_the_last_sibling(self):
        serve._split_join_maybe(self.a)
        self.assertEqual(self.opened, [])
        self.finish_b()
        serve._split_join_maybe(self.b)
        serve._split_join_maybe(self.a)          # a later turn end must not re-fire
        self.assertEqual(len(self.opened), 1)
        body, pid, parent = self.opened[0]
        self.assertEqual((pid, parent, body["parent"]), ("suss", self.parent, "plan1"))
        self.assertNotIn("split", body)          # the check is not a split member
        self.assertIn("quota built", body["prompt"])
        self.assertIn("THE PLAN THEY APPROVED", body["prompt"])
        self.assertTrue(body["title"].startswith("Plan check: "))
        self.assertEqual(self.parent.msg_queue, [])   # never queued on the planner

    def test_a_stopped_planning_thread_does_not_matter(self):
        self.parent.stop_reason, self.parent.done = "user-stop", True
        self.finish_b()
        serve._split_join_maybe(self.b)
        self.assertEqual(len(self.opened), 1)

    def test_missing_planning_thread_still_gets_a_check(self):
        del serve.RUNS["plan1"]
        self.finish_b()
        serve._split_join_maybe(self.b)
        body = self.opened[0][0]
        self.assertNotIn("parent", body)
        self.assertEqual((body["tier"], body["prototype"], body["guards"]["plan"]),
                         ("scoped", "prototype", False))

    def test_a_user_stopped_thread_settles_but_is_not_rebuilt(self):
        self.b.stop_reason, self.b.done = "user-stop", True
        serve._split_join_maybe(self.b)
        prompt = self.opened[0][0]["prompt"]
        self.assertIn('"Rename the sidebar entry" - thread b - STOPPED by the user', prompt)

    def test_a_fully_stopped_group_opens_nothing(self):
        for r in (self.a, self.b):
            r.stop_reason, r.done = "user-stop", True
        serve._split_join_maybe(self.b)
        self.assertEqual(self.opened, [])

    def test_a_restart_does_not_re_fire_a_checked_group(self):
        self.finish_b()
        self.parent.append("status", {"label": "split-check", "splitId": "plan1-abc"})
        serve._split_join_maybe(self.b)
        self.assertEqual(self.opened, [])

    def test_ordinary_runs_are_untouched(self):
        serve._split_join_maybe(fake_run("solo"))
        self.assertEqual(self.opened, [])

    def test_a_second_split_is_refused_while_the_first_is_working(self):
        busy = serve._split_busy_group("plan1", "plan1-new")
        self.assertIs(busy, self.b)                       # b is still mid-turn
        self.assertIsNone(serve._split_busy_group("plan1", "plan1-abc"))   # own group
        self.finish_b()
        self.assertIsNone(serve._split_busy_group("plan1", "plan1-new"))


class WiringTests(unittest.TestCase):
    def test_harness_registers_the_bash_guard(self):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root)
        hooks = root / ".claude" / "hooks"
        hooks.mkdir(parents=True)
        (hooks / "require-orchestrator.sh").write_text("#!/bin/sh\n")
        shutil.copy(HOOK, hooks / "guard-shared-tree.py")
        with patch.object(serve, "INSTALL_ROOT", str(root)):
            path = serve._ensure_harness_settings()
        pre = json.loads(Path(path).read_text())["hooks"]["PreToolUse"]
        bash = [h for h in pre if h["matcher"] == "Bash"]
        self.assertEqual(len(bash), 1)
        self.assertIn("guard-shared-tree.py", bash[0]["hooks"][0]["command"])

    def test_plan_stub_splits_by_region_not_by_file(self):
        stub = caps.PLAN_MODE_STUB
        self.assertIn('"owns"', stub)
        self.assertIn("path#region", stub)
        self.assertIn("SHARING A FILE IS NOT COUPLING", stub)
        self.assertNotIn("no two items write the same file", stub)
        self.assertIn("SEPARATE plan-check thread", stub)
        self.assertNotIn("[split-reconcile]", stub)


if __name__ == "__main__":
    unittest.main()

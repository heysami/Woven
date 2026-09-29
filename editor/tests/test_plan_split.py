"""Plan-mode split groups: ownership, the git-discard guard, and the plan check.

Regression for suss-cal (2026-09-29): two threads split from one plan ran in
the same working tree with no link between them. One saw its sibling's edit in
`git status`, took it for its own subagent's stray and ran
`git checkout -- source/prototype/admin-nav.js`, wiping the sibling's work.
Nothing ever compared the finished threads with the plan.

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

    def test_escaping_paths_are_dropped(self):
        s = plan_split.normalize({"id": "x", "index": 0, "items": [
            {"title": "t", "owns": ["../other/secret.js", "/etc/passwd", "ok.js"]}]}, "p")
        self.assertEqual(s["items"][0]["owns"], ["ok.js"])


class SiblingBlockTests(unittest.TestCase):
    def test_names_siblings_and_their_files_not_itself(self):
        text = plan_split.sibling_block(split(0))
        self.assertIn('"Rename the sidebar entry" owns: source/prototype/admin-nav.js', text)
        self.assertIn("You own: source/prototype/fa-fund.js", text)
        self.assertNotIn('item 1 "Quota utilisation screen"', text)
        self.assertIn("git checkout", text)
        self.assertIn("EVERY thread's uncommitted work", text)

    def test_overlaps(self):
        self.assertEqual(plan_split.overlaps(ITEMS), [])
        clash = ITEMS + [{"title": "C", "owns": ["source/prototype/admin-nav.js"]}]
        self.assertEqual(plan_split.overlaps(clash)[0]["path"], "source/prototype/admin-nav.js")


class GroupReadyTests(unittest.TestCase):
    def test_waits_for_every_item_and_every_thread(self):
        s = split(0)
        self.assertFalse(plan_split.group_ready(s, [{"index": 0, "finished": True}]))
        self.assertFalse(plan_split.group_ready(s, [{"index": 0, "finished": True},
                                                    {"index": 1, "finished": False}]))
        self.assertTrue(plan_split.group_ready(s, [{"index": 0, "finished": True},
                                                   {"index": 1, "finished": True}]))

    def test_reconcile_message_is_a_plan_check_not_a_report_relay(self):
        rows = [{"index": 0, "runId": "a", "status": "done", "report": "x" * 5000},
                {"index": 1, "runId": "b", "status": "error", "report": "renamed"}]
        text = plan_split.reconcile_message(split(0), rows)
        self.assertTrue(text.startswith("[split-reconcile]"))
        for word in ("DONE", "MISSING", "UNDONE", "DRIFT", "not against the reports"):
            self.assertIn(word, text)
        self.assertIn('"Rename the sidebar entry" - thread b - error', text)
        self.assertLess(len(text), 6000)   # a long report is truncated


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


def fake_run(rid, split_obj=None, turn_done=True, turns=1, done=False, result="ok"):
    state = SimpleNamespace(run_id=rid, title=rid, split=split_obj, parent_run_id=None,
        project_root="/fixture/suss", done=done, turn_done=turn_done, turns_completed=turns,
        stop_reason=None, jobs={}, lock=threading.Lock(), events=[], msg_queue=[])
    def append(kind, data):
        state.events.append({"seq": len(state.events), "type": kind, "data": data})
    state.append = append
    if turns:   # the CLI's result frame, as _drain_stdout records it
        append("agent", {"type": "status", "label": "done", "result": result})
    return state


class JoinTests(unittest.TestCase):
    def setUp(self):
        serve._SPLIT_JOINED.clear()
        self.parent = fake_run("plan1")
        self.a = fake_run("a", split(0), result="quota built")
        self.b = fake_run("b", split(1), turn_done=False, turns=0)
        self.runs = {"plan1": self.parent, "a": self.a, "b": self.b}
        patches = [patch.dict(serve.RUNS, self.runs, clear=True),
                   patch.object(serve, "_queue_drain_maybe"),
                   patch.object(serve, "_queue_persist")]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def test_waits_for_the_last_sibling_then_queues_one_check(self):
        serve._split_join_maybe(self.a)
        self.assertEqual(self.parent.msg_queue, [])
        self.b.turn_done, self.b.turns_completed = True, 1
        self.b.append("agent", {"type": "status", "label": "done", "result": "renamed"})
        serve._split_join_maybe(self.b)
        serve._split_join_maybe(self.a)          # a later turn end must not re-fire
        self.assertEqual(len(self.parent.msg_queue), 1)
        text = self.parent.msg_queue[0]["send"]
        self.assertIn("[split-reconcile]", text)
        self.assertIn("quota built", text)
        self.assertIn("renamed", text)
        labels = [e["data"].get("label") for e in self.parent.events]
        self.assertEqual(labels.count("split-reconcile"), 1)

    def test_a_restart_does_not_re_fire_a_checked_group(self):
        self.b.turn_done, self.b.turns_completed = True, 1
        self.parent.append("status", {"label": "split-reconcile", "splitId": "plan1-abc"})
        serve._split_join_maybe(self.b)
        self.assertEqual(self.parent.msg_queue, [])

    def test_ordinary_runs_are_untouched(self):
        serve._split_join_maybe(fake_run("solo"))
        self.assertEqual(self.parent.msg_queue, [])


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

    def test_plan_stub_asks_for_owns_and_knows_the_check(self):
        self.assertIn('"owns"', caps.PLAN_MODE_STUB)
        self.assertIn("[split-reconcile]", caps.PLAN_MODE_STUB)


if __name__ == "__main__":
    unittest.main()

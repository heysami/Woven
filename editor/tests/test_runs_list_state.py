"""Pins the runs list's server-side contract: gate pendency, the rename
sidecar, and the bulk purge.

Three claims the runs list is built on:

  1. `gatePending` means "an agent asked for a pick and nobody has answered".
     It is folded forward one event at a time (RunState.append for live runs,
     _ChatFileIndex for history) rather than rescanned per poll, and a gate tag
     split across two text_deltas must still match.
  2. Renaming a run does NOT rewrite its transcript - the new title lives in a
     runId -> title sidecar and is overlaid by every run-row reader, so it
     survives the daemon restart that drops RUNS.
  3. Deleting N runs rewrites the chat JSONL ONCE, not N times.

Run: `python3 editor/tests/test_runs_list_state.py` (no pytest required).
Exit 0 on pass, non-zero on any failure.
"""

import json
import os
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_EDITOR = os.path.dirname(_HERE)
sys.path.insert(0, _EDITOR)

import serve  # noqa: E402

FAILURES = []


def _check(cond, label):
    if cond:
        print(f"  ✓ {label}")
    else:
        FAILURES.append(label)
        print(f"  ✗ {label}")


def _feed(*events):
    """Fold (ev_type, data) pairs through the gate tracker, return pending."""
    gate = {"pending": False, "tail": ""}
    for ev_type, data in events:
        serve._gate_feed(gate, ev_type, data)
    return gate["pending"]


def _delta(text):
    return ("agent", {"type": "text_delta", "delta": text})


def test_gate_feed():
    print("test: _gate_feed folds gate pendency")
    _check(not _feed(_delta("just talking")), "plain prose is not a gate")
    _check(_feed(_delta("pick one <decision-request id='x'>")),
           "<decision-request> opens a gate")
    _check(_feed(_delta("<direction-options>")), "<direction-options> opens a gate")
    _check(_feed(_delta("<question-form>")), "<question-form> opens a gate")
    # The whole reason for the 64-char carry: streamed deltas split anywhere.
    _check(_feed(_delta("here you go <decision-"), _delta("request id='y'>")),
           "a tag split across two deltas still matches")
    _check(not _feed(_delta("<decision-request>"), ("user_message", {"text": "a"})),
           "the user's reply answers the gate")
    _check(not _feed(_delta("<question-form>"), ("tool_answer", {"toolUseId": "t"})),
           "a tool answer answers the gate")
    _check(not _feed(_delta("<decision-request>"),
                     ("agent", {"type": "compact"})),
           "a compact retires the transcript the card lived in")
    _check(_feed(_delta("<decision-request>"), ("user_message", {"text": "a"}),
                 _delta("<direction-options>")),
           "a second ask after the reply re-opens the gate")
    # status frames carry the final assistant text on some runtimes.
    _check(_feed(("agent", {"type": "status", "label": "done",
                            "result": "<decision-request id='z'>"})),
           "a status result carrying gate markup opens a gate")


def test_gate_on_runstate():
    print("test: RunState.append keeps gate_pending current")
    state = serve.RunState(run_id="a" * 16, proc=None, agent_id="claude",
                           branch="main", kind="freeform", title="t",
                           project_id="p", project_root=tempfile.gettempdir())
    _check(state.gate_pending is False, "a fresh run has no pending gate")
    state.append("agent", {"type": "text_delta", "delta": "thinking <decision-"})
    _check(state.gate_pending is False, "half a tag is not yet a gate")
    state.append("agent", {"type": "text_delta", "delta": "request id='q'>"})
    _check(state.gate_pending is True, "the completed tag opens the gate")
    _check(serve._compact_gate_pending(state) is True,
           "the compact guard reads the same flag")
    state.append("user_message", {"text": "option A"})
    _check(state.gate_pending is False, "the reply closes it")


def _make_project_root(tmp):
    root = os.path.join(tmp, "proj")
    os.makedirs(os.path.join(root, "source"), exist_ok=True)
    os.makedirs(os.path.join(root, "editor"), exist_ok=True)
    return root


def _line(run_id, seq, ev_type, data, title="orig"):
    return {"runId": run_id, "branch": "main", "agentId": "claude",
            "kind": "freeform", "title": title, "startedAt": 1000.0,
            "seq": seq, "type": ev_type, "data": data, "ts": 1000.0 + seq}


def test_history_gate_pending():
    print("test: history-only runs report gatePending too")
    with tempfile.TemporaryDirectory() as tmp:
        root = _make_project_root(tmp)
        path = os.path.join(root, "editor", "chat.jsonl")
        asked, answered = "b" * 16, "c" * 16
        with open(path, "w", encoding="utf-8") as f:
            for rec in [
                _line(asked, 0, "agent", {"type": "text_delta", "delta": "pick: <decision-"}),
                _line(asked, 1, "agent", {"type": "text_delta", "delta": "request id='g'>"}),
                _line(answered, 0, "agent", {"type": "text_delta", "delta": "<question-form>"}),
                _line(answered, 1, "user_message", {"text": "done"}),
            ]:
                f.write(json.dumps(rec) + "\n")
        metas = serve._chat_jsonl_scan_historical(root)
        _check(metas.get(asked, {}).get("gatePending") is True,
               "an unanswered ask survives the daemon restart as gatePending")
        _check(metas.get(answered, {}).get("gatePending") is False,
               "an answered ask does not")
        _check("_gateTail" not in metas.get(asked, {}),
               "the index-internal carry never leaves the index")


def test_rename_sidecar():
    print("test: rename lives in a sidecar, never in the transcript")
    with tempfile.TemporaryDirectory() as tmp:
        root = _make_project_root(tmp)
        chat = os.path.join(root, "editor", "chat.jsonl")
        run_id = "d" * 16
        with open(chat, "w", encoding="utf-8") as f:
            f.write(json.dumps(_line(run_id, 0, "agent", {"type": "text_delta",
                                                          "delta": "hi"})) + "\n")
        before = open(chat, encoding="utf-8").read()
        titles = serve._run_titles_path(root)
        serve._run_titles_set(titles, run_id, "My renamed thread")
        _check(open(chat, encoding="utf-8").read() == before,
               "the transcript is byte-for-byte untouched")
        _check(serve._run_titles_load(titles).get(run_id) == "My renamed thread",
               "the sidecar carries the new title")
        # A ghost rehydrated after a restart must come back renamed.
        with serve.RUNS_LOCK:
            serve.RUNS.clear()
        with open(chat, "a", encoding="utf-8") as f:
            f.write(json.dumps(_line(run_id, 1, "system",
                                     {"sessionId": "s1", "tag": "init"})) + "\n")
        state = serve._rehydrate_run_from_jsonl(run_id, root)
        _check(state is not None and state.title == "My renamed thread",
               "a rehydrated ghost carries the rename, not the stamped title")
        serve._run_titles_set(titles, run_id, "")
        _check(run_id not in serve._run_titles_load(titles),
               "a blank title clears the rename")
        with serve.RUNS_LOCK:
            serve.RUNS.clear()


def test_bulk_purge():
    print("test: a bulk delete rewrites the transcript once")
    with tempfile.TemporaryDirectory() as tmp:
        root = _make_project_root(tmp)
        chat = os.path.join(root, "editor", "chat.jsonl")
        a, b, keep = "e" * 16, "f" * 16, "1" * 16
        with open(chat, "w", encoding="utf-8") as f:
            for rid in (a, a, b, keep, keep, keep):
                f.write(json.dumps(_line(rid, 0, "agent", {"type": "text_delta",
                                                           "delta": "x"})) + "\n")
        purged = serve._chat_jsonl_purge_run(chat, {a, b})
        _check(purged == 3, f"all three lines of both runs purged (got {purged})")
        left = [json.loads(l)["runId"] for l in open(chat, encoding="utf-8") if l.strip()]
        _check(left == [keep] * 3, "the untouched run's lines all survive")
        # Delete means delete: no trash sibling is written. The old copy was
        # never readable back (no restore path anywhere) and grew unbounded.
        trash = os.path.join(root, "editor", ".chat-trash.jsonl")
        _check(not os.path.exists(trash), "no .chat-trash.jsonl is left behind")
        # The single-id call path must keep working unchanged.
        _check(serve._chat_jsonl_purge_run(chat, keep) == 3,
               "a single run id still purges")


def main():
    for t in (test_gate_feed, test_gate_on_runstate, test_history_gate_pending,
              test_rename_sidecar, test_bulk_purge):
        t()
    print()
    if FAILURES:
        print(f"FAILED ({len(FAILURES)}):")
        for f in FAILURES:
            print("  - " + f)
        return 1
    print("all runs-list state checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

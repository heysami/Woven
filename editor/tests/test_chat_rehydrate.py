"""Regression test for the v3.1 "unknown runId after daemon restart" bug.

Background - `RUNS` is in-memory only, so every daemon restart wipes it.
When an `/__run/<id>/*` endpoint is hit afterwards, the handler falls
through to `_rehydrate_run_from_jsonl()` to reload the run from disk.

The v3.1 migration changed the chat persistence layout from
`editor/branches/<slug>.chat.jsonl` (one file per branch) to a single flat
`editor/chat.jsonl`. The historical scanner was updated; the rehydrator
was missed. Every project created after the migration silently failed
session resume with `unknown runId`.

The fix unified layout knowledge into `_chat_jsonl_candidate_files()`.
This test pins that contract - if a future reader bypasses the helper
and forgets the flat layout (or someone removes the legacy fallback
while in-flight installs still need it), CI fails here, not in
production.

Run: `python3 editor/tests/test_chat_rehydrate.py` (no pytest required).
Exit 0 on pass, non-zero on any failure.
"""

import json
import os
import shutil
import sys
import tempfile
import traceback

# Make `import serve` resolve from editor/ when this file is run directly.
_HERE = os.path.dirname(os.path.abspath(__file__))
_EDITOR = os.path.dirname(_HERE)
sys.path.insert(0, _EDITOR)

import serve  # noqa: E402  - import after sys.path mutation; module guards top-level on __main__


FAILURES = []


def _check(cond, label):
    if cond:
        print(f"  ✓ {label}")
    else:
        FAILURES.append(label)
        print(f"  ✗ {label}")


def _make_project_root(tmpdir):
    """Mimic the on-disk shape resolve_project_root() expects.

    `_rehydrate_run_from_jsonl` doesn't check for source/, but downstream
    callers do - including this file kept honest for any future test that
    pipes the same fixture through `resolve_project_root`."""
    root = os.path.join(tmpdir, "proj")
    os.makedirs(os.path.join(root, "source"), exist_ok=True)
    os.makedirs(os.path.join(root, "editor"), exist_ok=True)
    return root


def _write_jsonl(path, records):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


def _sample_records(run_id, branch, session_id, title="t"):
    """A minimal but realistic event sequence - spawn status, an agent
    frame carrying sessionId, a user/assistant pair. Enough that the
    rehydrator can extract metadata + reconstruct events."""
    return [
        {"runId": run_id, "branch": branch, "agentId": "claude",
         "kind": "freeform", "title": title, "startedAt": 1000.0,
         "seq": 0, "type": "status",
         "data": {"label": "spawned", "agentId": "claude"}, "ts": 1000.1},
        {"runId": run_id, "branch": branch, "agentId": "claude",
         "kind": "freeform", "title": title, "startedAt": 1000.0,
         "seq": 1, "type": "system",
         "data": {"sessionId": session_id, "tag": "init"}, "ts": 1000.2},
        {"runId": run_id, "branch": branch, "agentId": "claude",
         "kind": "freeform", "title": title, "startedAt": 1000.0,
         "seq": 2, "type": "assistant",
         "data": {"text": "hello"}, "ts": 1000.3},
    ]


def _reset_runs():
    with serve.RUNS_LOCK:
        serve.RUNS.clear()


def test_flat_v31_layout():
    print("test: flat v3.1 layout (editor/chat.jsonl) rehydrates")
    with tempfile.TemporaryDirectory() as tmp:
        root = _make_project_root(tmp)
        run_id = "deadbeef00000001"
        session_id = "sess-flat-1"
        _write_jsonl(
            os.path.join(root, "editor", "chat.jsonl"),
            _sample_records(run_id, "main", session_id, title="flat-case"),
        )
        _reset_runs()

        state = serve._rehydrate_run_from_jsonl(run_id, root)
        _check(state is not None, "returns a RunState (not None)")
        if state is None:
            return
        _check(state.run_id == run_id, f"run_id matches ({state.run_id!r})")
        _check(state.session_id == session_id,
               f"session_id captured from system frame ({state.session_id!r})")
        _check(state.branch == "main",
               f"branch_slug = 'main' for flat layout (got {state.branch!r})")
        _check(state.title == "flat-case",
               f"title pulled from first record ({state.title!r})")
        _check(len(state.events) == 3,
               f"all 3 non-__finish events replayed (got {len(state.events)})")
        with serve.RUNS_LOCK:
            _check(run_id in serve.RUNS, "RunState registered in RUNS dict")


def test_legacy_branches_layout():
    print("test: legacy editor/branches/<slug>.chat.jsonl still rehydrates")
    with tempfile.TemporaryDirectory() as tmp:
        root = _make_project_root(tmp)
        run_id = "deadbeef00000002"
        session_id = "sess-legacy-1"
        _write_jsonl(
            os.path.join(root, "editor", "branches", "experimental.chat.jsonl"),
            _sample_records(run_id, "experimental", session_id, title="legacy-case"),
        )
        _reset_runs()

        state = serve._rehydrate_run_from_jsonl(run_id, root)
        _check(state is not None, "returns a RunState (not None)")
        if state is None:
            return
        _check(state.run_id == run_id, f"run_id matches ({state.run_id!r})")
        _check(state.session_id == session_id,
               f"session_id captured ({state.session_id!r})")
        _check(state.branch == "experimental",
               f"branch_slug = 'experimental' derived from filename "
               f"(got {state.branch!r})")


def test_flat_preferred_over_branches():
    print("test: flat layout wins when both layouts coexist")
    with tempfile.TemporaryDirectory() as tmp:
        root = _make_project_root(tmp)
        run_id = "deadbeef00000003"
        # Same runId in both files but with different session_ids - whichever
        # candidate is scanned first wins. Helper contract: flat first.
        _write_jsonl(
            os.path.join(root, "editor", "chat.jsonl"),
            _sample_records(run_id, "main", "sess-from-flat", title="flat-wins"),
        )
        _write_jsonl(
            os.path.join(root, "editor", "branches", "main.chat.jsonl"),
            _sample_records(run_id, "main", "sess-from-legacy", title="legacy-loses"),
        )
        _reset_runs()

        state = serve._rehydrate_run_from_jsonl(run_id, root)
        _check(state is not None, "returns a RunState")
        if state is None:
            return
        _check(state.session_id == "sess-from-flat",
               f"flat layout takes priority (session_id={state.session_id!r})")


def test_unknown_run_returns_none():
    print("test: rehydrate returns None for a runId that isn't on disk")
    with tempfile.TemporaryDirectory() as tmp:
        root = _make_project_root(tmp)
        _write_jsonl(
            os.path.join(root, "editor", "chat.jsonl"),
            _sample_records("aaaa", "main", "sess-other"),
        )
        _reset_runs()
        state = serve._rehydrate_run_from_jsonl("not-on-disk", root)
        _check(state is None, "returns None (not a fabricated RunState)")


def test_no_chat_files_returns_none():
    print("test: rehydrate returns None when no chat.jsonl exists at all")
    with tempfile.TemporaryDirectory() as tmp:
        root = _make_project_root(tmp)
        # No editor/chat.jsonl, no editor/branches/. _chat_jsonl_candidate_files
        # must return [] and rehydrate must short-circuit cleanly.
        _reset_runs()
        state = serve._rehydrate_run_from_jsonl("anything", root)
        _check(state is None, "returns None when there is nothing to scan")


def test_helper_contract_is_single_source():
    print("test: _chat_jsonl_candidate_files is the only path-knowledge helper")
    # Pin the contract: flat first, then legacy. If a future refactor changes
    # the priority order or the slug convention, downstream code that depends
    # on "branch == 'main' for flat" will silently misroute. Fail loudly here.
    with tempfile.TemporaryDirectory() as tmp:
        root = _make_project_root(tmp)
        flat_path = os.path.join(root, "editor", "chat.jsonl")
        legacy_path = os.path.join(root, "editor", "branches", "foo.chat.jsonl")
        os.makedirs(os.path.dirname(legacy_path), exist_ok=True)
        open(flat_path, "w").close()
        open(legacy_path, "w").close()

        candidates = serve._chat_jsonl_candidate_files(root)
        _check(len(candidates) == 2, f"finds both layouts (got {len(candidates)})")
        if len(candidates) >= 1:
            _check(candidates[0] == (flat_path, "main"),
                   "flat layout is first with slug='main'")
        if len(candidates) >= 2:
            _check(candidates[1] == (legacy_path, "foo"),
                   "legacy file second with slug derived from filename")


def test_historical_scanner_agrees_with_rehydrate():
    print("test: historical scanner sees the same runs the rehydrator does")
    # The original bug was drift between two readers. Pin them together:
    # whatever runIds the historical scanner reports for a project, the
    # rehydrator must also be able to load.
    with tempfile.TemporaryDirectory() as tmp:
        root = _make_project_root(tmp)
        run_id_flat = "deadbeef00000010"
        run_id_legacy = "deadbeef00000011"
        _write_jsonl(
            os.path.join(root, "editor", "chat.jsonl"),
            _sample_records(run_id_flat, "main", "sess-flat-x"),
        )
        _write_jsonl(
            os.path.join(root, "editor", "branches", "old.chat.jsonl"),
            _sample_records(run_id_legacy, "old", "sess-legacy-x"),
        )

        historical = serve._chat_jsonl_scan_historical(root)
        _check(run_id_flat in historical,
               "historical scanner finds the flat-layout run")
        _check(run_id_legacy in historical,
               "historical scanner finds the legacy-layout run")

        for rid in (run_id_flat, run_id_legacy):
            _reset_runs()
            state = serve._rehydrate_run_from_jsonl(rid, root)
            _check(state is not None,
                   f"rehydrator also finds runId reported by scanner: {rid}")


def main():
    tests = [
        test_flat_v31_layout,
        test_legacy_branches_layout,
        test_flat_preferred_over_branches,
        test_unknown_run_returns_none,
        test_no_chat_files_returns_none,
        test_helper_contract_is_single_source,
        test_historical_scanner_agrees_with_rehydrate,
    ]
    for t in tests:
        try:
            t()
        except Exception:
            FAILURES.append(f"{t.__name__} raised")
            traceback.print_exc()
        print()

    if FAILURES:
        print(f"FAIL - {len(FAILURES)} assertion(s) failed:")
        for f in FAILURES:
            print(f"  - {f}")
        sys.exit(1)
    print("PASS - chat-jsonl rehydrate contract upheld")


if __name__ == "__main__":
    main()

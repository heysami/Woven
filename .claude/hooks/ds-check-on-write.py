#!/usr/bin/env python3
"""ds-check-on-write.py - PostToolUse hook for COMPONENT design systems.

Two jobs, both silent unless the file belongs to a component DS
(design-systems/<id>/meta.json kind == "component"):

  1. A project page (source/**.html) was written or edited
       -> run editor/tools/ds/ds_check.py on it. Errors go back to the agent in
          the same turn ({"decision": "block", "reason": ...}); warnings ride as
          additionalContext. Clean pages say nothing.
  2. A DS source file (components/ patterns/ shells/ tokens/ foundations/
     themes/ services/ icons/ or meta.json) was written or edited
       -> rebuild build/ (build_ds.py) so every page picks the change up, and
          report the DS's errors the same way.

Spec: docs/features/component-ds-format.md. Registered in
serve.py:_ensure_harness_settings (matcher Write|Edit|MultiEdit). The chat's
"Checks" dropdown can drop the DS gate for one thread: serve.py stamps
TH_DS_GUARD=0 on that spawn and this hook stays silent.

NOTE: must stay a real script file reading the payload from stdin (a bash
heredoc replaces stdin and the hook would fail open). Fails open on any error:
a broken checker must never brick a session.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(os.path.dirname(os.path.dirname(HERE)), "editor", "tools", "ds")
DS_SOURCE_DIRS = ("components", "patterns", "shells", "tokens", "foundations", "themes", "services", "icons")
LIMIT = 25


def emit(errors_text, warns_text, what):
    if errors_text:
        print(json.dumps({"decision": "block",
                          "reason": "ds_check: " + what + " breaks the component design system rules. Fix these before continuing:\n" + errors_text}))
    elif warns_text:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse",
                                                 "additionalContext": "ds_check warnings for " + what + ":\n" + warns_text}}))


def ds_dir_of(path):
    """design-systems/<id>/ root containing `path`, or None."""
    parts = path.replace(os.sep, "/").split("/")
    if "design-systems" not in parts:
        return None, None
    i = len(parts) - 1 - parts[::-1].index("design-systems")
    if i + 2 > len(parts) - 1:
        return None, None
    root = "/".join(parts[:i + 2])
    sub = parts[i + 2] if len(parts) > i + 2 else ""
    return root, sub


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return
    if (os.environ.get("TH_DS_GUARD") or "").strip() == "0":
        return
    ti = payload.get("tool_input") or {}
    path = ti.get("file_path") or ti.get("path") or ""
    if not path:
        return
    if not os.path.isabs(path):
        path = os.path.join(payload.get("cwd") or os.getcwd(), path)
    path = os.path.normpath(path)
    if not os.path.isfile(path):
        return
    sys.path.insert(0, TOOLS)
    try:
        import ds_check
        import build_ds
    except Exception:
        return

    ds_root, sub = ds_dir_of(path)
    if ds_root:
        # a DS source edit: rebuild + report the DS's own problems
        if sub == "build" or sub == "_legacy" or not (sub in DS_SOURCE_DIRS or os.path.basename(path) == "meta.json"):
            return
        if not ds_check.is_component_ds(ds_root):
            return
        try:
            ds, wrote = build_ds.build(ds_root)
        except Exception:
            return
        if ds is None:
            return
        errs = [f for f in ds.findings if f.level == "error"]
        warns = [f for f in ds.findings if f.level == "warn"]
        base = os.path.dirname(os.path.dirname(ds_root))
        what = "design system '" + ds.id + "' (rebuilt build/)"
        emit(ds_check.format_text(ds, errs, root=base, limit=LIMIT, ds_note=False) if errs else "",
             ds_check.format_text(ds, warns, root=base, limit=LIMIT, ds_note=False) if warns else "", what)
        return

    norm = path.replace(os.sep, "/")
    if not norm.lower().endswith((".html", ".htm")) or "/source/" not in norm:
        return
    try:
        ds, findings = ds_check.run(pages=[path])
    except Exception:
        return
    if ds is None:
        return
    errs = [f for f in findings if f.level == "error"]
    warns = [f for f in findings if f.level == "warn"]
    root = ds_check.find_project_root(path) or os.path.dirname(path)
    emit(ds_check.format_text(ds, errs, root=root, limit=LIMIT) if errs else "",
         ds_check.format_text(ds, warns, root=root, limit=LIMIT) if warns else "",
         os.path.relpath(path, root))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass

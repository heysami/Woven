#!/usr/bin/env python3
"""ds_check.py - check pages (and the DS itself) against a component design system.

    python3 ds_check.py --page source/main/orders.html            # DS resolved from the page / project
    python3 ds_check.py --ds-dir design-systems/suss --page a.html --page b.html
    python3 ds_check.py --ds-dir design-systems/suss --ds-only     # the DS's own blocks
    add --json for machine output

Exit codes: 0 clean, 1 errors, 2 not a component design system / nothing to check.
Spec: docs/features/component-ds-format.md. Stdlib only, Python 3.9-safe.
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ds_model  # noqa: E402
from ds_page import check_page  # noqa: E402

LINK_RE = re.compile(r"""(?:href|src)\s*=\s*["']([^"']*design-systems/([\w.\-]+)/build/[^"']*)["']""")


def find_project_root(path):
    d = os.path.dirname(os.path.abspath(path))
    while True:
        if os.path.isdir(os.path.join(d, "design-systems")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def bound_ds_id(project_root, page_path=None):
    """Mirror of capabilities._resolve_ds_binding: meta.dsRef in the prototype's
    editor data file, else the only design-systems/<id>/ directory."""
    candidates = []
    if page_path:
        rel = os.path.relpath(os.path.abspath(page_path), os.path.join(project_root, "source"))
        proto = rel.split(os.sep)[0] if not rel.startswith("..") else None
        if proto:
            candidates.append(os.path.join(project_root, "editor", proto + ".data.js"))
    candidates.append(os.path.join(project_root, "editor", "data.js"))
    for p in candidates:
        if not os.path.isfile(p):
            continue
        try:
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                txt = f.read()
        except OSError:
            continue
        m = re.search(r'dsRef["\']?\s*:\s*\{[^}]*?\bid["\']?\s*:\s*["\']([A-Za-z0-9_.\-]+)["\']', txt) or \
            re.search(r'dsRef["\']?\s*:\s*["\']([A-Za-z0-9_.\-]+)["\']', txt)
        if m:
            return m.group(1)
    root = os.path.join(project_root, "design-systems")
    dirs = [d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)) and not d.startswith(".")]
    return dirs[0] if len(dirs) == 1 else None


def resolve_ds_dir(page_path):
    """A page's component DS: the one its links point at, else the project binding."""
    try:
        with open(page_path, "r", encoding="utf-8", errors="replace") as f:
            head = f.read(200000)
    except OSError:
        head = ""
    m = LINK_RE.search(head)
    if m:
        url = m.group(1).split("?")[0]
        p = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(page_path)), url))
        ds_dir = p.split(os.sep + "build" + os.sep)[0]
        if os.path.isfile(os.path.join(ds_dir, "meta.json")):
            return ds_dir
    root = find_project_root(page_path)
    if not root:
        return None
    ds_id = bound_ds_id(root, page_path)
    if not ds_id:
        return None
    d = os.path.join(root, "design-systems", ds_id)
    return d if os.path.isdir(d) else None


def is_component_ds(ds_dir):
    try:
        with open(os.path.join(ds_dir, "meta.json"), "r", encoding="utf-8") as f:
            return json.load(f).get("kind") == "component"
    except (OSError, ValueError):
        return False


_cache = {}


def load_ds(ds_dir):
    ds_dir = os.path.abspath(ds_dir)
    if ds_dir not in _cache:
        _cache[ds_dir] = ds_model.load(ds_dir)
    return _cache[ds_dir]


def run(ds_dir=None, pages=(), ds_only=False):
    """Returns (ds, findings) or (None, reason) when there is nothing to check."""
    pages = list(pages)
    if not ds_dir:
        if not pages:
            return None, "no --ds-dir and no --page"
        ds_dir = resolve_ds_dir(pages[0])
        if not ds_dir:
            return None, "could not resolve a design system for " + pages[0]
    if not is_component_ds(ds_dir):
        return None, os.path.basename(os.path.normpath(ds_dir)) + " is not a component design system (meta.kind)"
    ds = load_ds(ds_dir)
    findings = []
    if ds_only or not pages:
        findings.extend(ds.findings)
    for p in pages:
        findings.extend(check_page(ds, p))
    return ds, findings


def summarize(findings):
    counts = {"error": 0, "warn": 0, "info": 0}
    for f in findings:
        counts[f.level] = counts.get(f.level, 0) + 1
    return counts


def format_text(ds, findings, root=None, limit=None, ds_note=True):
    order = {"error": 0, "warn": 1, "info": 2}
    fs = sorted(findings, key=lambda f: (order.get(f.level, 3), f.file or "", f.line or 0))
    lines = [f.fmt(root) for f in (fs[:limit] if limit else fs)]
    if limit and len(fs) > limit:
        lines.append("... and " + str(len(fs) - limit) + " more")
    c = summarize(findings)
    lines.append("ds_check " + ds.id + ": " + str(c["error"]) + " errors, " + str(c["warn"]) + " warnings, " + str(c["info"]) + " info")
    ds_errors = sum(1 for f in ds.findings if f.level == "error")
    if ds_note and ds_errors and not any(f in ds.findings for f in findings):
        lines.append("note: the design system itself has " + str(ds_errors) + " errors (run with --ds-only)")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check pages against a component design system")
    ap.add_argument("--ds-dir")
    ap.add_argument("--page", action="append", default=[])
    ap.add_argument("--ds-only", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args(argv)
    ds, findings = run(a.ds_dir, a.page, a.ds_only)
    if ds is None:
        if a.json:
            print(json.dumps({"ok": True, "skipped": findings}))
        else:
            print("ds_check: skipped - " + findings)
        return 2
    c = summarize(findings)
    if a.json:
        print(json.dumps({"ok": c["error"] == 0, "ds": ds.id, "counts": c,
                          "findings": [f.as_dict() for f in findings]}, indent=1))
    else:
        print(format_text(ds, findings, root=os.getcwd(), limit=a.limit or None))
    return 1 if c["error"] else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""ds_lint.py - deterministic design-system drift linter for Woven prototypes.

Catches the drift class that visual QA cannot see: a page whose markup uses
valid DS vocabulary but whose local <style> block silently REDEFINES the DS's
component classes (the suss-cal failure: fa-application.html shadowing
.kv-grid / .input / .field__hint with bespoke chrome), plus hallucinated
tokens, hardcoded values that duplicate a token, and the same class forked
across sibling pages with different bodies.

Stdlib only, Python 3.9-safe (the daemon's fresh-install floor). No daemon
required - runs anywhere:

    python3 editor/tools/qa/ds_lint.py --project-root <abs path> \
        --prototype <slug> [--pages a.html,b.html] [--json] [--strict]

Exit codes: 0 = clean (no error-severity findings; warns listed but pass,
unless --strict), 1 = findings at gating severity, 2 = no design system
bound (lint not applicable - the caller should skip, not fail).

DS resolution mirrors editor/kinds/capabilities.py:_resolve_ds_binding
(meta.dsRef in editor/<prototype>.data.js else editor/data.js, falling back
to a single design-systems/<id>/ dir). Keep the two in sync.
"""

import argparse
import json
import os
import re
import sys
from typing import Dict, List, Optional, Set, Tuple

# Properties that change a component's SKIN or internal geometry. A page-local
# contextual rule on a DS class that only PLACES the component (margin, width,
# grid-area, flex, position) is normal page layout; one that touches these
# forks the component's look and is drift.
CHROME_PROPS = (
    "background", "border", "box-shadow", "padding", "gap",
    "font", "color", "border-radius", "line-height", "letter-spacing",
    "text-transform", "text-decoration", "outline", "backdrop-filter",
    "filter", "opacity", "text-shadow",
)

# Class prefixes that are JS state hooks / harness markers, not styling
# vocabulary - used in markup without a definition on purpose.
STATE_PREFIXES = ("is-", "has-", "js-", "wf-", "data-", "no-")


def _read(path):
    # type: (str) -> str
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def _strip_css_comments(css):
    # type: (str) -> str
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def parse_css_rules(css):
    # type: (str) -> List[Tuple[str, str]]
    """Flatten CSS into (selector, body) pairs, descending into @media /
    @supports / @layer blocks and skipping @keyframes bodies entirely
    (their inner selectors are frame offsets, not classes)."""
    css = _strip_css_comments(css)
    rules = []  # type: List[Tuple[str, str]]
    i, n = 0, len(css)
    while i < n:
        brace = css.find("{", i)
        if brace == -1:
            break
        selector = css[i:brace].strip()
        # Walk to the matching close brace.
        depth, j = 1, brace + 1
        while j < n and depth:
            c = css[j]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            j += 1
        body = css[brace + 1:j - 1]
        if selector.startswith("@"):
            low = selector.lower()
            if low.startswith(("@media", "@supports", "@layer", "@container")):
                rules.extend(parse_css_rules(body))
            # @keyframes / @font-face / @import etc: no class rules inside.
        elif selector:
            rules.append((selector, body))
        i = j
    return rules


def classes_in_selector(selector):
    # type: (str) -> Set[str]
    return set(re.findall(r"\.([A-Za-z_][\w-]*)", selector))


def subject_classes(selector):
    # type: (str) -> Tuple[Set[str], bool]
    """Classes of the selector's SUBJECT (last compound) and whether the
    selector has any context prefix (descendant/child combinators before it)."""
    sel = selector.split("::")[0]
    parts = re.split(r"[\s>+~]+", sel.strip())
    parts = [p for p in parts if p]
    if not parts:
        return set(), False
    subject = parts[-1]
    # Strip pseudo-classes off the compound (keep the class tokens).
    return classes_in_selector(subject), len(parts) > 1


def body_props(body):
    # type: (str) -> Set[str]
    props = set()
    for decl in body.split(";"):
        if ":" in decl:
            props.add(decl.split(":", 1)[0].strip().lower())
    return props


def has_chrome_props(body):
    # type: (str) -> List[str]
    hits = []
    for p in sorted(body_props(body)):
        for c in CHROME_PROPS:
            if p == c or p.startswith(c + "-"):
                hits.append(p)
                break
    return hits


def normalize_body(body):
    # type: (str) -> str
    decls = sorted(d.strip().lower().replace(" ", "")
                   for d in body.split(";") if d.strip())
    return ";".join(decls)


def _norm_hex(v):
    # type: (str) -> Optional[str]
    m = re.fullmatch(r"#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})", v.strip())
    if not m:
        return None
    h = m.group(1).lower()
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    return "#" + h


def resolve_ds(project_root, prototype):
    # type: (str, Optional[str]) -> Optional[Dict[str, str]]
    """Mirror of capabilities.py:_resolve_ds_binding - keep in sync."""
    ds_id = None
    candidates = []
    if prototype:
        candidates.append(os.path.join(project_root, "editor", "%s.data.js" % prototype))
    candidates.append(os.path.join(project_root, "editor", "data.js"))
    for path in candidates:
        if not os.path.isfile(path):
            continue
        try:
            txt = _read(path)
        except Exception:
            continue
        m = re.search(r'dsRef["\']?\s*:\s*\{[^}]*?\bid["\']?\s*:\s*["\']([A-Za-z0-9_.\-]+)["\']', txt)
        if not m:
            m = re.search(r'dsRef["\']?\s*:\s*["\']([A-Za-z0-9_.\-]+)["\']', txt)
        if m:
            ds_id = m.group(1)
            break
    ds_root = os.path.join(project_root, "design-systems")
    if not ds_id and os.path.isdir(ds_root):
        dirs = [d for d in os.listdir(ds_root)
                if os.path.isdir(os.path.join(ds_root, d)) and not d.startswith(".")]
        if len(dirs) == 1:
            ds_id = dirs[0]
    if not ds_id:
        return None
    ds_dir = os.path.join(ds_root, ds_id)
    if not os.path.isdir(ds_dir):
        return None
    return {"id": ds_id, "dir": ds_dir}


def load_ds_vocab(ds_dir):
    # type: (str) -> Dict[str, object]
    """Classes + tokens (+ token color values) from the DS's stylesheets."""
    css_all = ""
    for fname in ("styles.css", "all.css"):
        p = os.path.join(ds_dir, fname)
        if os.path.isfile(p):
            css_all += "\n" + _read(p)
    classes = set()  # type: Set[str]
    for sel, _body in parse_css_rules(css_all):
        classes |= classes_in_selector(sel)
    tokens = set(re.findall(r"--([\w-]+)\s*:", css_all))
    # Knob tokens: custom properties the DS only ever READS with a
    # fallback (var(--kv-cols, 4)) are legitimate vocabulary too - pages
    # set them inline to vary the component.
    tokens |= set(re.findall(r"var\(\s*--([\w-]+)", css_all))
    color_to_token = {}  # type: Dict[str, str]
    for name, val in re.findall(r"--([\w-]+)\s*:\s*([^;}]+)", css_all):
        h = _norm_hex(val)
        if h and h not in color_to_token:
            color_to_token[h] = name
    return {"classes": classes, "tokens": tokens, "color_to_token": color_to_token}


def extract_style_blocks(html):
    # type: (str) -> str
    return "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", html, re.S | re.I))


def extract_markup_classes(html):
    # type: (str) -> Set[str]
    stripped = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.S | re.I)
    stripped = re.sub(r"<script[^>]*>.*?</script>", "", stripped, flags=re.S | re.I)
    out = set()  # type: Set[str]
    for attr in re.findall(r'class\s*=\s*"([^"]*)"', stripped):
        out |= set(attr.split())
    for attr in re.findall(r"class\s*=\s*'([^']*)'", stripped):
        out |= set(attr.split())
    return {c for c in out if re.fullmatch(r"[A-Za-z_][\w-]*", c)}


def lint_page(page_path, ds_vocab, shared_classes):
    # type: (str, Dict[str, object], Set[str]) -> Tuple[List[Dict[str, object]], Dict[str, str]]
    """Lint one page. Returns (findings, local_bare_defs) where
    local_bare_defs maps class -> normalized body for the fork detector."""
    findings = []  # type: List[Dict[str, object]]
    html = _read(page_path)
    page = os.path.basename(page_path)
    css = extract_style_blocks(html)
    rules = parse_css_rules(css)
    ds_classes = ds_vocab["classes"]      # type: ignore[assignment]
    ds_tokens = ds_vocab["tokens"]        # type: ignore[assignment]
    color_to_token = ds_vocab["color_to_token"]  # type: ignore[assignment]

    local_classes = set()   # type: Set[str]
    # Local token definitions can live in the page CSS or in inline
    # style="--knob: value" attributes on elements.
    local_tokens = set(re.findall(r"--([\w-]+)\s*:", css))
    local_tokens |= set(re.findall(r"--([\w-]+)\s*:", html))
    local_bare_defs = {}    # type: Dict[str, str]

    for sel, body in rules:
        local_classes |= classes_in_selector(sel)
        if not body.strip():
            continue
        for one_sel in sel.split(","):
            one_sel = one_sel.strip()
            if not one_sel:
                continue
            subj, has_context = subject_classes(one_sel)
            # State/modifier classes (.is-*, .has-*) are shared vocabulary,
            # not components - never count them as the DS class being forked.
            subj_core = {c for c in subj if not c.startswith(STATE_PREFIXES)}
            ds_hit = sorted(subj_core & ds_classes)  # type: ignore[operator]
            # A subject that MIXES a DS class with a page-local class
            # (.fa-kv.kv-grid) is the sanctioned compose-alongside pattern -
            # treat it like a contextual rule, not a naked redefinition.
            pure_ds_subject = bool(subj_core) and not (subj_core - ds_classes)  # type: ignore[operator]
            if ds_hit:
                if not has_context and pure_ds_subject:
                    findings.append({
                        "rule": "ds-class-redefined", "severity": "error",
                        "page": page, "selector": one_sel, "classes": ds_hit,
                        "detail": "page <style> redefines DS class(es) %s at top level - "
                                  "delete the local rule; vary via the component's custom-property "
                                  "knobs or a NEW page-namespaced class composed alongside, "
                                  "never by shadowing the DS name" % ", ".join("." + c for c in ds_hit),
                    })
                else:
                    chrome = has_chrome_props(body)
                    if chrome:
                        findings.append({
                            "rule": "ds-class-restyled-in-context", "severity": "warn",
                            "page": page, "selector": one_sel, "classes": ds_hit,
                            "detail": "contextual rule changes DS component chrome (%s) - layout "
                                      "placement is fine, skin/geometry belongs to the DS"
                                      % ", ".join(chrome[:6]),
                        })
            # Track bare local definitions for the cross-page fork detector
            # (classes NOT in the DS - DS ones are already flagged above).
            if not has_context and len(subj) == 1:
                cls = next(iter(subj))
                if cls not in ds_classes:  # type: ignore[operator]
                    local_bare_defs[cls] = normalize_body(body)

    # Unknown tokens: var(--x) that neither the DS nor this page defines.
    for tok in set(re.findall(r"var\(\s*--([\w-]+)", css)):
        if tok not in ds_tokens and tok not in local_tokens:  # type: ignore[operator]
            findings.append({
                "rule": "unknown-token", "severity": "error",
                "page": page, "token": tok,
                "detail": "var(--%s) is defined neither in the DS nor in this page - "
                          "hallucinated token (renders as its fallback or invalid)" % tok,
            })

    # Hardcoded colors that duplicate a DS token value.
    for sel, body in rules:
        for lit in re.findall(r"#[0-9a-fA-F]{3,6}\b", body):
            h = _norm_hex(lit)
            tok = color_to_token.get(h) if h else None  # type: ignore[union-attr]
            if tok:
                findings.append({
                    "rule": "hardcoded-token-value", "severity": "warn",
                    "page": page, "selector": sel.strip()[:80], "value": lit,
                    "detail": "literal %s duplicates DS token --%s - use var(--%s)"
                              % (lit, tok, tok),
                })

    # Undefined classes in markup (info: often JS hooks; the guardian judges).
    defined = ds_classes | local_classes | shared_classes  # type: ignore[operator]
    unknown = sorted(
        c for c in extract_markup_classes(html)
        if c not in defined and not c.startswith(STATE_PREFIXES)
    )
    if unknown:
        findings.append({
            "rule": "undefined-classes", "severity": "info",
            "page": page, "classes": unknown[:30],
            "detail": "classes used in markup but styled nowhere (DS, page <style>, "
                      "shared css) - hallucinated vocabulary or dead hooks",
        })
    return findings, local_bare_defs


def main(argv=None):
    # type: (Optional[List[str]]) -> int
    ap = argparse.ArgumentParser(description="Woven design-system drift linter")
    ap.add_argument("--project-root", required=True)
    ap.add_argument("--prototype", default=None,
                    help="source/<slug> to lint (default: sole/first source subdir)")
    ap.add_argument("--pages", default=None,
                    help="comma-separated page filenames to lint (default: all *.html)")
    ap.add_argument("--json", action="store_true", dest="as_json")
    ap.add_argument("--strict", action="store_true",
                    help="warns also gate (exit 1)")
    args = ap.parse_args(argv)

    root = os.path.abspath(args.project_root)
    proto = args.prototype
    if not proto:
        src = os.path.join(root, "source")
        subs = sorted(d for d in (os.listdir(src) if os.path.isdir(src) else [])
                      if os.path.isdir(os.path.join(src, d)))
        proto = subs[0] if subs else None
    if not proto:
        print(json.dumps({"status": "error", "error": "no prototype found under source/"}))
        return 2

    ds = resolve_ds(root, proto)
    if not ds:
        out = {"status": "no-ds", "detail": "no design system bound - lint not applicable"}
        print(json.dumps(out) if args.as_json else out["detail"])
        return 2
    ds_vocab = load_ds_vocab(ds["dir"])

    proto_dir = os.path.join(root, "source", proto)
    shared_classes = set()  # type: Set[str]
    for f in sorted(os.listdir(proto_dir)) if os.path.isdir(proto_dir) else []:
        if f.endswith(".css"):
            for sel, _b in parse_css_rules(_read(os.path.join(proto_dir, f))):
                shared_classes |= classes_in_selector(sel)

    if args.pages:
        pages = [os.path.join(proto_dir, p.strip()) for p in args.pages.split(",") if p.strip()]
    else:
        pages = [os.path.join(proto_dir, f) for f in sorted(os.listdir(proto_dir))
                 if f.endswith(".html")]
    pages = [p for p in pages if os.path.isfile(p)]

    all_findings = []  # type: List[Dict[str, object]]
    bare_defs_by_page = {}  # type: Dict[str, Dict[str, str]]
    for p in pages:
        f, bare = lint_page(p, ds_vocab, shared_classes)
        all_findings.extend(f)
        bare_defs_by_page[os.path.basename(p)] = bare

    # Cross-page fork detector: same non-DS class defined bare in 2+ pages
    # with DIFFERENT bodies. (Identical bodies are copy-paste, still worth
    # promoting, but forks are the active drift.) Only meaningful when
    # linting the whole prototype.
    if not args.pages:
        by_class = {}  # type: Dict[str, Dict[str, str]]
        for page, defs in bare_defs_by_page.items():
            for cls, body in defs.items():
                by_class.setdefault(cls, {})[page] = body
        for cls, pages_map in sorted(by_class.items()):
            if len(pages_map) >= 2 and len(set(pages_map.values())) > 1:
                all_findings.append({
                    "rule": "cross-page-fork", "severity": "warn",
                    "classes": [cls], "pages": sorted(pages_map),
                    "detail": ".%s is defined locally in %d pages with different bodies - "
                              "unify to one body; promotion candidate for the DS"
                              % (cls, len(pages_map)),
                })

    errors = [f for f in all_findings if f["severity"] == "error"]
    warns = [f for f in all_findings if f["severity"] == "warn"]
    infos = [f for f in all_findings if f["severity"] == "info"]
    report = {
        "status": "clean" if not errors and not (args.strict and warns) else "violations",
        "ds": ds["id"], "prototype": proto,
        "pagesLinted": [os.path.basename(p) for p in pages],
        "counts": {"error": len(errors), "warn": len(warns), "info": len(infos)},
        "findings": all_findings,
    }
    if args.as_json:
        print(json.dumps(report, indent=2))
    else:
        print("DS lint - ds=%s prototype=%s pages=%d  errors=%d warns=%d infos=%d"
              % (ds["id"], proto, len(pages), len(errors), len(warns), len(infos)))
        for f in all_findings:
            loc = f.get("page") or ",".join(f.get("pages", []))  # type: ignore[arg-type]
            print("  [%s] %s %s: %s" % (f["severity"], f["rule"], loc, f["detail"]))
    return 1 if report["status"] == "violations" else 0


if __name__ == "__main__":
    sys.exit(main())

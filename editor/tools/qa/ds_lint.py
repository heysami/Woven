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
import subprocess
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


def bare_local_defs(html, ds_classes):
    # type: (str, Set[str]) -> Dict[str, str]
    """Page-local class definitions: `.foo{...}` at top level, class not in the
    DS (DS names are a separate, louder finding). The unit the fork detector
    and the git baseline both compare."""
    defs = {}  # type: Dict[str, str]
    for sel, body in parse_css_rules(extract_style_blocks(html)):
        if not body.strip():
            continue
        for one_sel in sel.split(","):
            one_sel = one_sel.strip()
            if not one_sel:
                continue
            subj, has_context = subject_classes(one_sel)
            if not has_context and len(subj) == 1:
                cls = next(iter(subj))
                if cls not in ds_classes:
                    defs[cls] = normalize_body(body)
    return defs


# ── Element inventory ───────────────────────────────────────────────────────
# The flat, deterministic list of what a page actually renders. Two consumers:
# the contract-aware rules below (is this local class really a re-hand-rolled DS
# component?) and, when --jev is on, the one real judgment - one question per
# element, built by THIS parser so nothing is ever counted by a model.
#
# Stdlib regex over the tag stream, not a DOM: we need each element's own
# classes, its inline style, a short text sample and the shape of its immediate
# children. Depth is tracked so childShape is the element's OWN children.

_VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
              "meta", "param", "source", "track", "wbr"}
_TAG = re.compile(r"<(/?)([a-zA-Z][\w-]*)([^<>]*?)(/?)>")
_CLASS_ATTR = re.compile(r'class\s*=\s*"([^"]*)"|class\s*=\s*\'([^\']*)\'')
_STYLE_ATTR = re.compile(r'style\s*=\s*"([^"]*)"|style\s*=\s*\'([^\']*)\'')


def _attr_classes(attrs):
    # type: (str) -> List[str]
    out = []
    for m in _CLASS_ATTR.finditer(attrs):
        out.extend((m.group(1) or m.group(2) or "").split())
    return [c for c in out if re.fullmatch(r"[A-Za-z_][\w-]*", c)]


def _attr_style(attrs):
    # type: (str) -> str
    m = _STYLE_ATTR.search(attrs)
    return ((m.group(1) or m.group(2)) if m else "").strip()


def element_inventory(html, max_elements=2000):
    # type: (str, int) -> List[Dict[str, object]]
    """One row per CLASSED element: {line, tag, classes, inlineStyle,
    textSample, childShape}. Unclassed elements are skipped - they carry no
    vocabulary, so there is nothing about them to judge."""
    stripped = re.sub(r"<style[^>]*>.*?</style>", lambda m: "\n" * m.group(0).count("\n"),
                      html, flags=re.S | re.I)
    stripped = re.sub(r"<script[^>]*>.*?</script>", lambda m: "\n" * m.group(0).count("\n"),
                      stripped, flags=re.S | re.I)
    rows = []   # type: List[Dict[str, object]]
    stack = []  # type: List[Tuple[int, Optional[Dict[str, object]]]]
    depth = 0
    last_end = 0
    for m in _TAG.finditer(stripped):
        text = stripped[last_end:m.start()]
        last_end = m.end()
        if text.strip():
            sample = re.sub(r"\s+", " ", text).strip()[:120]
            for d, row in stack:
                if row is not None and not row["textSample"]:
                    row["textSample"] = sample
        closing, tag, attrs, selfclose = m.group(1), m.group(2).lower(), m.group(3), m.group(4)
        if closing:
            depth -= 1
            while stack and stack[-1][0] > depth:
                stack.pop()
            continue
        classes = _attr_classes(attrs)
        empty = bool(selfclose) or tag in _VOID_TAGS
        row = None  # type: Optional[Dict[str, object]]
        if classes and len(rows) < max_elements:
            row = {"line": stripped.count("\n", 0, m.start()) + 1, "tag": tag,
                   "classes": classes, "inlineStyle": _attr_style(attrs),
                   "textSample": "", "childShape": []}
            rows.append(row)
        # Register with the nearest classed ancestor as one of ITS children.
        for d, parent in reversed(stack):
            if parent is not None:
                if len(parent["childShape"]) < 24:  # type: ignore[arg-type]
                    parent["childShape"].append(  # type: ignore[union-attr]
                        {"tag": tag, "classes": classes})
                break
        if not empty:
            stack.append((depth, row))
            depth += 1
    return rows


# ── Contract-aware matching (Phase 3b) ──────────────────────────────────────

def contract_index(contract):
    # type: (Optional[Dict[str, object]]) -> Dict[str, object]
    """Lookup tables the rules below need: component by id, every declared part
    and its SUFFIX (`card__title` -> `title`), and the set of ids whose role
    makes them a candidate for being re-hand-rolled. A `text` or `indicator`
    component is not: nobody invents `.product-caret`."""
    comps = {}          # type: Dict[str, Dict[str, object]]
    part_owner = {}     # type: Dict[str, str]
    suffix_owner = {}   # type: Dict[str, Set[str]]
    if isinstance(contract, dict):
        for c in contract.get("components") or []:  # type: ignore[union-attr]
            if not isinstance(c, dict):
                continue
            cid = str(c.get("id") or "")
            if not cid:
                continue
            comps[cid] = c
            for part in (list(c.get("requiredParts") or []) + list(c.get("optionalParts") or [])):
                part_owner[str(part)] = cid
                suffix = str(part).split("__", 1)[-1]
                suffix_owner.setdefault(suffix, set()).add(cid)
    substantial = {cid for cid, c in comps.items()
                   if c.get("role") in ("container", "surface", "overlay", "control")}
    return {"components": comps, "partOwner": part_owner,
            "suffixOwner": suffix_owner, "substantial": substantial}


def _name_match(cls, index):
    # type: (str, Dict[str, object]) -> Optional[str]
    """The contract component `cls` is a renamed copy of, by NAME. `.product-card`
    -> `card`.

    SUFFIX direction only, and only on whole hyphen/underscore tokens. Both
    restrictions are load-bearing because this row gates:
      - a substring rule would match `.scorecard` to `.card`;
      - the PREFIX direction is not the same evidence. English compounds put
        the head noun last, so `.product-card` IS a card, while `.card-foot` is
        a foot belonging to a card - page-local furniture around a DS
        component, not a second copy of it. Matching prefixes flagged every
        `.card-foot` and `.choice-rank` as an invented component, which is
        exactly the wall of false failures that gets a gate switched off."""
    comps = index["substantial"]  # type: ignore[assignment]
    tokens = [t for t in re.split(r"[-_]+", cls) if t]
    if len(tokens) < 2:
        return None  # a bare `.card` is not undefined, and a one-word class is its own thing
    best = None
    for cid in comps:  # type: ignore[union-attr]
        cid_tokens = [t for t in re.split(r"[-_]+", cid) if t]
        n = len(cid_tokens)
        if n and n < len(tokens) and tokens[-n:] == cid_tokens:
            # Longest component id wins: `.mini-section-card` is a
            # `section-card`, not a `card`.
            if best is None or n > len(re.split(r"[-_]+", best)):
                best = cid
    return best


def _structure_match(element, cls, index):
    # type: (Dict[str, object], str, Dict[str, object]) -> Optional[str]
    """The contract component this element is a copy of, by SHAPE. `.product-card`
    holding `.product-card__title` + `.product-card__body` is a `card` whatever
    it is called. Needs TWO matching part suffixes, or one that the contract
    marks REQUIRED - one optional suffix like `__title` is shared by half the
    catalogue and would fire on everything."""
    suffix_owner = index["suffixOwner"]  # type: ignore[assignment]
    comps = index["components"]          # type: ignore[assignment]
    own = set()  # type: Set[str]
    for child in element.get("childShape") or []:  # type: ignore[union-attr]
        for c in child.get("classes") or []:
            if c.startswith(cls + "__"):
                own.add(c.split("__", 1)[1])
    if not own:
        return None
    scores = {}  # type: Dict[str, int]
    for suffix in own:
        for cid in suffix_owner.get(suffix, ()):  # type: ignore[union-attr]
            if cid in index["substantial"]:       # type: ignore[operator]
                scores[cid] = scores.get(cid, 0) + 1
    for cid, hits in sorted(scores.items(), key=lambda kv: -kv[1]):
        required = {str(p).split("__", 1)[-1] for p in (comps[cid].get("requiredParts") or [])}  # type: ignore[index]
        if hits >= 2 or (required and own & required):
            return cid
    return None


def baseline_html(root, rel):
    # type: (str, str) -> Optional[str]
    """The committed text of `rel` (repo-relative-ish, resolved from `root`), or
    None when git cannot answer - not a repo, no HEAD, or the file is new. None
    means "no baseline": the caller must then claim nothing about what changed."""
    try:
        r = subprocess.run(["git", "-C", root, "show", "HEAD:./" + rel],
                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    return r.stdout.decode("utf-8", "replace")


def lint_page(page_path, ds_vocab, shared_classes, index=None):
    # type: (str, Dict[str, object], Set[str], Optional[Dict[str, object]]) -> Tuple[List[Dict[str, object]], Dict[str, str], List[Dict[str, object]]]
    """Lint one page. Returns (findings, local_bare_defs, ambiguous) where
    local_bare_defs maps class -> normalized body for the fork detector, and
    `ambiguous` is the residue the Jev pass may promote - one row per page-local
    class the contract cannot place, carrying the element that uses it."""
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
    # Bare local definitions, for the cross-page fork detector (classes NOT in
    # the DS - DS ones are already flagged above).
    local_bare_defs = bare_local_defs(html, ds_classes)  # type: Dict[str, str]

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

    # ── Contract-aware split of the hand-rolled-vocabulary class ────────────
    # Until there was a contract, every class the page invented landed in ONE
    # `undefined-classes` info bucket, because nothing could tell an invented
    # component from a legitimate page-local layout utility. That is exactly the
    # rule that should fire when a page hand-rolls `.product-card` instead of
    # using the DS's `.card`, and `info` meant it never did.
    #
    # With a contract the certainty splits four ways, and only the first two are
    # certain enough to gate:
    #   1. the class IS a contract component under another name (by name or by
    #      part structure)                                            -> error
    #   2. a local class puts component CHROME on a DS component's part -> error
    #   3. no contract match, purely positional CSS                   -> info
    #   4. no contract match, chrome props, ambiguous role            -> info,
    #      promoted to error only on a confident Jev verdict (--jev).
    # Row 4 is why 3b cannot gate on its own: without the judgment, separating
    # an invented component from real page layout is the thing nothing can do,
    # and gating it would hand keyless installs a wall of false failures. Keyless
    # is LESS COMPLETE here, never noisier.
    index = index or {"components": {}, "partOwner": {}, "suffixOwner": {}, "substantial": set()}
    inventory = element_inventory(html)
    elem_by_class = {}  # type: Dict[str, Dict[str, object]]
    for row in inventory:
        for c in row["classes"]:  # type: ignore[union-attr]
            elem_by_class.setdefault(c, row)

    defined = ds_classes | local_classes | shared_classes  # type: ignore[operator]
    markup_classes = extract_markup_classes(html)
    # Every class this PAGE invented: styled nowhere, or styled only by its own
    # <style> block. Both are page-local vocabulary; the DS shipped neither.
    page_vocab = sorted(
        c for c in (markup_classes | set(local_bare_defs))
        if c not in ds_classes and c not in shared_classes  # type: ignore[operator]
        and not c.startswith(STATE_PREFIXES)
    )

    # A class shaped `<component>--<x>` where the component IS in the contract
    # but the variant is not declared. Not an invented COMPONENT - an invented
    # VARIANT of a real one, which is a different finding with a different fix
    # (declare it in the DS, or compose with a page-namespaced class alongside).
    # Reporting it as "re-hand-rolls .btn" told the user to replace `.btn--x`
    # with `.btn`, which loses the thing the page was trying to say.
    comps_all = index["components"]  # type: ignore[assignment]
    undeclared_variants = {}  # type: Dict[str, str]
    for cls in page_vocab:
        if "--" not in cls:
            continue
        base = cls.split("--", 1)[0]
        comp = comps_all.get(base)  # type: ignore[union-attr]
        if comp and cls not in (comp.get("variants") or []):
            undeclared_variants[cls] = base
    for cls, base in sorted(undeclared_variants.items()):
        comp = comps_all[base]  # type: ignore[index]
        declared = comp.get("variants") or []
        el = elem_by_class.get(cls) or {}
        findings.append({
            "rule": "undeclared-variant", "severity": "error",
            "page": page, "classes": [cls], "component": base,
            "line": el.get("line"),
            "detail": ".%s is a variant of the design system's .%s that the design system "
                      "never declares%s - add it to the DS if the whole product needs it, "
                      "otherwise compose a page-namespaced class alongside .%s rather than "
                      "extending its variant namespace from a page"
                      % (cls, base,
                         (" (declared: " + ", ".join("." + v for v in declared[:6]) + ")")
                         if declared else "",
                         base),
        })

    # NAME evidence gates; STRUCTURE evidence does not.
    #
    # The plan this implements put both in the same deterministic row. Measured
    # against a real 26-page prototype, structure alone over-fires: a component's
    # part suffixes are generic words (`__title`, `__item`, `__logo`), so a
    # page's `.sidebar` scored as the DS's `.topnav` and `.paysteps` as its
    # `.pagination` - structurally true, semantically wrong, and an error-level
    # finding either way. Deciding whether a structurally-similar element IS the
    # component is the one real judgment, which is what 3c is for. So a structure
    # hit routes to the ambiguous bucket with its suspect recorded as context,
    # and gates only on a confident verdict. Keyless stays less complete, never
    # noisier - which is the whole reason the ambiguous row exists.
    matched = {}   # type: Dict[str, Tuple[str, str]]
    suspects = {}  # type: Dict[str, str]
    for cls in page_vocab:
        if cls in undeclared_variants:
            continue
        el = elem_by_class.get(cls)
        hit = _name_match(cls, index)
        if hit:
            matched[cls] = (hit, "name")
            continue
        if el:
            shape = _structure_match(el, cls, index)
            if shape:
                suspects[cls] = shape
    for cls, (cid, how) in sorted(matched.items()):
        comp = index["components"].get(cid, {})  # type: ignore[union-attr]
        el = elem_by_class.get(cls) or {}
        findings.append({
            "rule": "invented-component", "severity": "error",
            "page": page, "classes": [cls], "component": cid,
            "line": el.get("line"), "matchedBy": how,
            "detail": ".%s re-hand-rolls the design system's .%s (matched by %s%s) - "
                      "use .%s and vary it through its declared variants%s, never by "
                      "inventing a parallel component"
                      % (cls, cid, how,
                         "" if how == "name" else " of its inner parts",
                         cid,
                         (" (" + ", ".join("." + v for v in (comp.get("variants") or [])[:4]) + ")")
                         if comp.get("variants") else ""),
        })

    # Row 2: a page-local class that puts COMPONENT CHROME onto an element that
    # is already a DS component's part. Deterministic, and only knowable with a
    # contract - a flat set of class strings has no idea `.card__title` is a
    # part of anything.
    part_owner = index["partOwner"]  # type: ignore[assignment]
    for cls, body in sorted(local_bare_defs.items()):
        if cls in matched or not part_owner:
            continue
        chrome = has_chrome_props(body)
        if not chrome:
            continue
        el = elem_by_class.get(cls)
        if not el:
            continue
        on_parts = sorted({c for c in el["classes"] if c in part_owner})  # type: ignore[operator]
        if not on_parts:
            continue
        owner = part_owner[on_parts[0]]  # type: ignore[index]
        findings.append({
            "rule": "ds-part-chrome-forked", "severity": "error",
            "page": page, "classes": [cls], "component": owner,
            "line": el.get("line"), "parts": on_parts,
            "detail": ".%s sets component chrome (%s) on %s, which belongs to the DS's "
                      ".%s - the part's skin is the design system's; place it with layout "
                      "properties or vary the component through its knobs"
                      % (cls, ", ".join(chrome[:6]),
                         ", ".join("." + p for p in on_parts), owner),
        })

    # Rows 3 and 4: the residue. Still ONE info finding, exactly as before, so
    # the keyless verdict is unchanged for everything the contract could not
    # place. `ambiguous` carries only row 4 forward to the Jev pass.
    already = {f["classes"][0] for f in findings  # type: ignore[index]
               if f["rule"] in ("ds-part-chrome-forked", "undeclared-variant")}
    unmatched = [c for c in page_vocab if c not in matched and c not in already]
    unknown = sorted(c for c in unmatched if c not in defined)
    if unknown:
        findings.append({
            "rule": "undefined-classes", "severity": "info",
            "page": page, "classes": unknown[:30],
            "detail": "classes used in markup but styled nowhere (DS, page <style>, "
                      "shared css) - hallucinated vocabulary or dead hooks",
        })

    ambiguous = []  # type: List[Dict[str, object]]
    for cls in unmatched:
        el = elem_by_class.get(cls)
        if el is None:
            continue
        body = local_bare_defs.get(cls)
        # Row 4: the page DEFINES this class with component chrome, and the
        # contract cannot place it. Row 3 - a local class with purely positional
        # CSS - is ordinary page layout and never reaches here.
        chromed = body is not None and bool(has_chrome_props(body))
        if not chromed and cls not in suspects:
            continue
        ambiguous.append({"page": page, "class": cls, "element": el,
                          "suspect": suspects.get(cls),
                          "reason": "structure" if cls in suspects else "chrome"})
    return findings, local_bare_defs, ambiguous


# ── Phase 3c: the ONE real judgment ─────────────────────────────────────────
# After 3b, the residue is a single question: "is this page-local class an
# invented component, or legitimate page layout?" Nothing deterministic can
# answer it - that is why the rule was `info` in the first place. It is one
# Choice per element over the contract's component ids plus `page-layout-only`
# plus `unknown`, with each component's own `oneLine` (and `notForUseWhen` when
# the DS authors wrote one) as the criteria VERBATIM.
#
# Constraints this pass obeys, from the jaggedness rules:
#   - never about colour: `hardcoded-token-value` already does colour
#     deterministically, via the DS's own token values, and does it better.
#   - never counting: the fan-out is built by the parser above, one element per
#     question, always.
#   - small state: the contract plus ONE element's context, never the page.
#   - it only ADDS: a `page-layout-only` verdict does NOT delete the info
#     finding, it only declines to promote it. "Turn it off" has to stay a safe
#     operation, which means jev-off findings are always a subset of jev-on
#     ones and no severity ever drops.

_PAGE_LAYOUT_ID = "page-layout-only"
_UNKNOWN_ID = "unknown"


def _element_state(contract, row):
    # type: (Dict[str, object], Dict[str, object]) -> str
    """The state for ONE element question: the element's own context and
    nothing else. The contract travels once, in the shared preamble line."""
    el = row["element"]  # type: ignore[index]
    children = ", ".join(
        "<%s%s>" % (c.get("tag"), ("." + ".".join(c.get("classes") or [])) if c.get("classes") else "")
        for c in (el.get("childShape") or [])[:12])  # type: ignore[union-attr]
    return (
        "Page: %s (line %s)\n"
        "Element: <%s class=\"%s\">\n"
        "Inline style: %s\n"
        "Own text: %s\n"
        "Immediate children: %s\n"
        % (row["page"], el.get("line"), el.get("tag"),
           " ".join(el.get("classes") or []),  # type: ignore[arg-type]
           el.get("inlineStyle") or "(none)",
           (el.get("textSample") or "(none)"),
           children or "(none)"))


def jev_criteria(contract):
    # type: (Dict[str, object]) -> Dict[str, str]
    """The Choice criteria map. Only SUBSTANTIAL components are offered: nobody
    hand-rolls a text utility, and every extra option dilutes the distribution.
    `oneLine` and `notForUseWhen` go in verbatim - a rubric paraphrased shorter
    is the same failure as a thin library index, and sharper here because this
    one gates."""
    criteria = {}  # type: Dict[str, str]
    for c in contract.get("components") or []:  # type: ignore[union-attr]
        if not isinstance(c, dict) or c.get("role") not in ("container", "surface", "overlay", "control"):
            continue
        text = str(c.get("oneLine") or c.get("id") or "")
        if c.get("notForUseWhen"):
            text += " NOT for use when: %s" % c["notForUseWhen"]
        criteria[str(c["id"])] = text[:600]
    criteria[_PAGE_LAYOUT_ID] = (
        "This element is page layout or page-specific decoration, not an instance of any "
        "component in the design system: a wrapper that positions things, a grid or column "
        "holder, a spacer, a page-only flourish.")
    criteria[_UNKNOWN_ID] = "There is not enough here to say what this element is."
    return criteria


def run_jev_pass(contract, ambiguous, findings, index, log=None):
    # type: (Dict[str, object], List[Dict[str, object]], List[Dict[str, object]], Dict[str, object], Optional[object]) -> Dict[str, object]
    """Promote the ambiguous residue. ALWAYS returns a status dict and NEVER
    raises: an unreachable judge leaves the deterministic verdict exactly as it
    was, which is the same fail-soft posture as visual_qa.run_judge."""
    status = {"available": False, "asked": 0, "promoted": 0, "message": None}  # type: Dict[str, object]
    if not ambiguous:
        status["message"] = "nothing ambiguous to judge"
        return status
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))))))
        import jev  # noqa: E402
    except Exception as exc:
        status["message"] = "jev helper unavailable: %s" % exc
        return status
    if not jev.enabled():
        status["message"] = "typed judgment is turned off (Settings -> Context and cost)"
        return status
    if not jev.available():
        status["message"] = "no typesafe api key configured"
        return status

    criteria = jev_criteria(contract)
    if len(criteria) > jev.MAX_CHOICE_OPTIONS:
        status["message"] = ("design system declares %d substantial components, over the "
                             "%d-option cap - skipping the judgment rather than truncating "
                             "the vocabulary" % (len(criteria), jev.MAX_CHOICE_OPTIONS))
        return status
    thresholds = jev.thresholds("ds_role")

    # One request per PAGE: state must stay small, and sharding on the page
    # boundary is the shard the parser already produces.
    by_page = {}  # type: Dict[str, List[Dict[str, object]]]
    for row in ambiguous:
        by_page.setdefault(str(row["page"]), []).append(row)

    errors = []  # type: List[str]
    for page, rows in sorted(by_page.items()):
        questions = {}
        for i, row in enumerate(rows):
            questions["el_%d" % i] = {
                "type": "choice",
                "instructions": "Which of these is this element?\n\n" + _element_state(contract, row),
                "criteria": criteria,
            }
        try:
            answers = jev.ask(contract, questions)
        except Exception as exc:
            errors.append("%s: %s" % (page, exc))
            continue
        status["available"] = True
        status["asked"] = int(status["asked"]) + len(questions)
        for i, row in enumerate(rows):
            ranked = jev.choice_ranked(answers.get("el_%d" % i), 1)
            conf = jev.confidence(answers.get("el_%d" % i))
            if not ranked:
                continue
            top, prob = ranked[0]
            if top in (_PAGE_LAYOUT_ID, _UNKNOWN_ID):
                # Declines to promote. Does NOT remove the info finding: jev-off
                # findings must stay a subset of jev-on ones.
                continue
            if jev.band(conf, thresholds["low"], thresholds["high"]) != "act":
                continue
            comp = index["components"].get(top, {})  # type: ignore[union-attr]
            findings.append({
                "rule": "invented-component", "severity": "error",
                "page": page, "classes": [row["class"]], "component": top,
                "line": row["element"].get("line"), "matchedBy": "jev",  # type: ignore[union-attr]
                "confidence": conf, "probability": prob,
                "detail": ".%s defines component chrome and reads as the design system's .%s - "
                          "use .%s%s instead of a parallel page-local component"
                          % (row["class"], top, top,
                             (" with one of " + ", ".join("." + v for v in (comp.get("variants") or [])[:4]))
                             if comp.get("variants") else ""),
            })
            status["promoted"] = int(status["promoted"]) + 1
    if errors:
        status["message"] = "; ".join(errors)[:300]
    elif status["available"]:
        status["message"] = "judged %d ambiguous element(s), promoted %d" % (
            status["asked"], status["promoted"])
    return status


def main(argv=None):
    # type: (Optional[List[str]]) -> int
    ap = argparse.ArgumentParser(description="Woven design-system drift linter")
    ap.add_argument("--project-root", required=True)
    ap.add_argument("--prototype", default=None,
                    help="source/<slug> to lint (default: sole/first source subdir)")
    ap.add_argument("--pages", default=None,
                    help="comma-separated page filenames to lint (default: all *.html). "
                         "Scoped: findings come only from these pages; siblings are read "
                         "solely to spot a fork of a class THESE pages define")
    ap.add_argument("--json", action="store_true", dest="as_json")
    ap.add_argument("--strict", action="store_true",
                    help="warns also gate (exit 1)")
    ap.add_argument("--jev", action="store_true",
                    help="judge the AMBIGUOUS residue with typed judgment: page-local "
                         "classes that define component chrome and that the contract "
                         "cannot place. Needs the global setting on AND a TypeSafe key; "
                         "without either it is a silent no-op and the deterministic "
                         "verdict stands untouched. It only ever ADDS findings.")
    ap.add_argument("--write-contract", action="store_true",
                    help="also write design-systems/<id>/contract.json - a reviewable "
                         "snapshot of what the linter derived. The lint itself always "
                         "derives it live, so the file is never an input")
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
    # The component contract, DERIVED LIVE from the DS's own files on every run.
    # Never read back from contract.json: an on-disk copy goes stale the first
    # time somebody edits styles.css, and a stale contract gates pages against a
    # design system that no longer exists. Failure to derive one is not fatal -
    # the linter then behaves exactly as it did before contracts existed.
    contract = {"components": []}  # type: Dict[str, object]
    try:
        import ds_contract
        contract = ds_contract.load_or_build(ds["dir"], ds["id"])
        if args.write_contract:
            with open(os.path.join(ds["dir"], ds_contract.CONTRACT_FILENAME), "w",
                      encoding="utf-8") as f:
                json.dump(contract, f, indent=2, ensure_ascii=False)
    except Exception as exc:
        if not args.as_json:
            print("note: could not derive the DS contract (%s); "
                  "contract-aware rules are skipped" % exc)
    index = contract_index(contract)

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
    ambiguous = []  # type: List[Dict[str, object]]
    for p in pages:
        f, bare, amb = lint_page(p, ds_vocab, shared_classes, index)
        all_findings.extend(f)
        bare_defs_by_page[os.path.basename(p)] = bare
        ambiguous.extend(amb)

    # Cross-page fork detector: same non-DS class defined bare in 2+ pages
    # with DIFFERENT bodies. (Identical bodies are copy-paste, still worth
    # promoting, but forks are the active drift.)
    #
    # A SCOPED run (--pages: the post-edit guard) reports only the forks THIS
    # EDIT is responsible for. A class is in play only if its local body was
    # ADDED or CHANGED against git HEAD; siblings are then read for that class
    # alone, and their own drift is never reported. So an edit that merely USES
    # the bound DS produces no cross-page work at all, and a pre-existing fork
    # between two pages stays where it is until someone asks for an audit. No
    # baseline (untracked page, no repo, no HEAD) means no claim about what
    # changed, so the scoped fork check sits out entirely. A bare sweep (no
    # --pages) keeps the exhaustive whole-prototype report.
    edited = set(os.path.basename(p) for p in pages)
    by_class = {}  # type: Dict[str, Dict[str, str]]
    if args.pages:
        for p in pages:
            page = os.path.basename(p)
            base = baseline_html(root, os.path.relpath(p, root))
            if base is None:
                continue
            was = bare_local_defs(base, ds_vocab["classes"])  # type: ignore[arg-type]
            for cls, body in bare_defs_by_page.get(page, {}).items():
                if was.get(cls) != body:
                    by_class.setdefault(cls, {})[page] = body
    else:
        for page, defs in bare_defs_by_page.items():
            for cls, body in defs.items():
                by_class.setdefault(cls, {})[page] = body
    if args.pages and by_class:
        siblings = sorted(f for f in (os.listdir(proto_dir) if os.path.isdir(proto_dir) else [])
                          if f.endswith(".html") and f not in edited)
        for f in siblings:
            sib_bare = bare_local_defs(_read(os.path.join(proto_dir, f)),
                                       ds_vocab["classes"])  # type: ignore[arg-type]
            for cls, body in sib_bare.items():
                if cls in by_class:
                    by_class[cls][f] = body
    for cls, pages_map in sorted(by_class.items()):
        if len(pages_map) >= 2 and len(set(pages_map.values())) > 1:
            fork = {
                "rule": "cross-page-fork", "severity": "warn",
                "classes": [cls], "pages": sorted(pages_map),
                "detail": ".%s is defined locally in %d pages with different bodies%s - "
                          "unify to one body; promotion candidate for the DS"
                          % (cls, len(pages_map),
                             " (this edit forked it)" if args.pages else ""),
            }  # type: Dict[str, object]
            if args.pages:
                # Which side is YOURS - the page to fix first.
                fork["origin"] = sorted(set(pages_map) & edited)
            all_findings.append(fork)

    # The judgment runs LAST, over the residue every deterministic rule declined
    # to place, and only ever appends.
    jev_status = None  # type: Optional[Dict[str, object]]
    if args.jev:
        jev_status = run_jev_pass(contract, ambiguous, all_findings, index)

    errors = [f for f in all_findings if f["severity"] == "error"]
    warns = [f for f in all_findings if f["severity"] == "warn"]
    infos = [f for f in all_findings if f["severity"] == "info"]
    report = {
        "status": "clean" if not errors and not (args.strict and warns) else "violations",
        "ds": ds["id"], "prototype": proto,
        "pagesLinted": [os.path.basename(p) for p in pages],
        "counts": {"error": len(errors), "warn": len(warns), "info": len(infos)},
        "contract": {"components": len(contract.get("components") or []),  # type: ignore[union-attr]
                     "ambiguous": len(ambiguous)},
        "findings": all_findings,
    }
    if jev_status is not None:
        report["jev"] = jev_status
    if args.as_json:
        print(json.dumps(report, indent=2))
    else:
        print("DS lint - ds=%s prototype=%s pages=%d  errors=%d warns=%d infos=%d"
              % (ds["id"], proto, len(pages), len(errors), len(warns), len(infos)))
        for f in all_findings:
            loc = f.get("page") or ",".join(f.get("pages", []))  # type: ignore[arg-type]
            print("  [%s] %s %s: %s" % (f["severity"], f["rule"], loc, f["detail"]))
        if jev_status is not None:
            print("  typed judgment: %s" % (jev_status.get("message") or "no verdict"))
    return 1 if report["status"] == "violations" else 0


if __name__ == "__main__":
    sys.exit(main())

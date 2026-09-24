#!/usr/bin/env python3
"""ds_contract.py - derive a design system's COMPONENT CONTRACT from its own sources.

ds_lint's model of a design system is a flat set of strings: load_ds_vocab
regex-scrapes class names and `--token` names into a Set[str]. That is enough to
catch a hallucinated token, and not nearly enough to catch the drift that
actually happens - a page hand-rolling `.product-card` instead of using the DS's
`.card`, a `.card` shipped without the `.card__title` it is defined around, a
component used with a variant the DS never declared. There is no component
contract in a set of strings: no parts, no variants, no role, no intent. This
module builds one.

DERIVED, NEVER HAND-WRITTEN. Everything below is read out of the DS's own
files - styles.css / all.css for what exists, gallery.html and templates/ for
how the DS itself composes it, DESIGN.md for what the authors said it is for.
A hand-maintained contract goes stale the first time somebody edits styles.css,
so ds_lint calls build() live on every run and `contract.json` is only a
reviewable snapshot of the same function's output.

WHAT IT IS FOR. Two consumers, and they want different halves of it:
  - ds_lint (deterministic): "this page's `.product-card` matches the shape of
    the contract's `card`" is now a checkable predicate, which is what lets
    undefined-classes stop being one undifferentiated `info` bucket.
  - the Jev role judgment (`ds_lint --jev`): `oneLine` and `notForUseWhen`
    become Choice criteria VERBATIM. That is why provenance is tracked per
    field: a rubric the generator inferred is weaker evidence than one the DS
    authors wrote, and a vague rubric yields confidently wrong role inference.
    `notForUseWhen` is emitted ONLY when DESIGN.md actually states one - an
    invented exclusion is worse than a missing one, because it gates.

Stdlib only, Python 3.9-safe (the daemon's fresh-install floor).

    python3 editor/tools/qa/ds_contract.py --ds-dir <abs path> [--write] [--json]
"""

import argparse
import json
import os
import re
import sys
from typing import Dict, List, Optional, Set, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from ds_lint import (CHROME_PROPS, STATE_PREFIXES, _read, body_props,  # noqa: E402
                     classes_in_selector, parse_css_rules, subject_classes)

CONTRACT_VERSION = "1.0"
CONTRACT_FILENAME = "contract.json"

# BEM separators, and ONLY these. A hyphen is NOT a part separator: `.avatar`
# and `.avatar-stack` are two components in every DS that uses this convention,
# and treating the hyphen as structural invents a part relationship that the
# authors never declared. Under-claiming here is cheap; over-claiming gates.
PART_SEP, VARIANT_SEP = "__", "--"

# Element tags a DS attaches a class to. Used for role inference: a class the
# stylesheet only ever writes as `button.btn` is a control, whatever it is called.
_CONTROL_TAGS = ("button", "a", "input", "select", "textarea", "label", "summary")

# Typographic properties. A rule that sets ONLY these styles text, not a surface.
_TEXT_PROPS = ("font", "color", "letter-spacing", "line-height", "text-align",
               "text-transform", "text-decoration", "text-overflow", "white-space",
               "word-break", "-webkit-line-clamp")


def _is_state(cls):
    # type: (str) -> bool
    return cls.startswith(STATE_PREFIXES)


def _split_class(cls):
    # type: (str) -> Tuple[str, Optional[str], Optional[str]]
    """(base, part, variant) for one class name under BEM.

    `card__title--lead` is a variant OF THE PART, not of the card: it is
    reported as a part and never as a base variant. Listing it under both (the
    first cut did) makes `.modal` look like it has fourteen variants when it has
    four, and a Choice rubric built from that is measurably worse."""
    base, part, variant = cls, None, None
    if VARIANT_SEP in base:
        base, variant = base.split(VARIANT_SEP, 1)
    if PART_SEP in base:
        base, part = base.split(PART_SEP, 1)
        variant = None
    return base, part, variant


# ── CSS side: what the DS declares ──────────────────────────────────────────

def _load_css(ds_dir):
    # type: (str) -> str
    css = ""
    for fname in ("styles.css", "all.css"):
        p = os.path.join(ds_dir, fname)
        if os.path.isfile(p):
            css += "\n" + _read(p)
    return css


_POSITION_VALUE = re.compile(r"(?:^|;)\s*position\s*:\s*([a-z-]+)", re.I)


def _declared(css):
    # type: (str) -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]]]
    """(class -> declared property names, class -> element tags it is written on).
    Only the SUBJECT of a selector counts: `.modal .btn` declares nothing about
    `.modal`, and counting it would make every container look like a control.

    `position: fixed|absolute` is folded into the property set as the synthetic
    name `@out-of-flow`, because the VALUE is what separates a modal from a
    badge that sets `position: relative` to hang a dot off itself."""
    props = {}  # type: Dict[str, Set[str]]
    tags = {}   # type: Dict[str, Set[str]]
    for sel, body in parse_css_rules(css):
        names = body_props(body)
        pos = _POSITION_VALUE.search(";" + body)
        if pos and pos.group(1).lower() in ("fixed", "absolute", "sticky"):
            names = names | {"@out-of-flow"}
        for one in sel.split(","):
            one = one.strip()
            if not one:
                continue
            subj, _ctx = subject_classes(one)
            compound = re.split(r"[\s>+~]+", one.split("::")[0].strip())
            compound = [c for c in compound if c]
            tag = ""
            if compound:
                m = re.match(r"^([a-zA-Z][a-zA-Z0-9]*)", compound[-1])
                tag = m.group(1).lower() if m else ""
            for cls in subj:
                props.setdefault(cls, set()).update(names)
                if tag:
                    tags.setdefault(cls, set()).add(tag)
    return props, tags


ROLES = ("control", "overlay", "container", "surface", "layout", "text",
         "indicator", "unknown")


def _role(cls, props, tags, has_parts):
    # type: (str, Set[str], Set[str], bool) -> str
    """One of ROLES, from DECLARED PROPERTIES ONLY. Never from the class NAME:
    a name-based rule would just re-encode the guess the contract exists to
    replace, and would then be used to judge pages by that same guess. The
    order is deliberate - each test is a strictly narrower claim than the one
    below it, and `unknown` is a real answer, not a failure."""
    if tags & set(_CONTROL_TAGS) or "cursor" in props or "appearance" in props:
        return "control"
    if "@out-of-flow" in props and ("z-index" in props or "inset" in props):
        return "overlay"
    chrome = any(p == c or p.startswith(c + "-") for p in props for c in CHROME_PROPS)
    layoutish = {"display", "grid-template-columns", "flex-direction", "gap",
                 "grid-template-areas"} & props
    if chrome and (layoutish or has_parts):
        return "container"
    if layoutish and not chrome:
        return "layout"
    if props and not (props - set(_TEXT_PROPS) - {"margin", "margin-top", "margin-bottom",
                                                  "display", "opacity"}):
        return "text"
    if chrome:
        # A padded surface holds content; an unpadded one decorates it. The
        # split matters because "this page hand-rolled a surface the DS already
        # ships" is the drift, and a hairline rule is not a candidate for it.
        padded = any(p == "padding" or p.startswith("padding-") for p in props)
        return "surface" if padded else "indicator"
    return "unknown"


# ── Usage side: how the DS itself composes the component ────────────────────

_TAG_OPEN = re.compile(r"<([a-zA-Z][\w-]*)((?:\s+[^<>]*?)?)/?>")


def _usage_pages(ds_dir):
    # type: (str) -> List[str]
    """The DS's own kitchen sink plus its page samples - the only honest source
    for whether a part is REQUIRED. A part the DS uses in every single instance
    it ships is required; one it uses sometimes is optional. Nothing else in the
    repo gets a vote: a prototype page is the thing being judged."""
    out = []
    g = os.path.join(ds_dir, "gallery.html")
    if os.path.isfile(g):
        out.append(g)
    for sub in ("templates", "shells"):
        d = os.path.join(ds_dir, sub)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if f.endswith(".html"):
                out.append(os.path.join(d, f))
    return out


def _instances(html, base, parts):
    # type: (str, str, Set[str]) -> List[Set[str]]
    """For each element carrying `base`, the set of ITS parts appearing inside
    it. Scanned by depth on the raw tag stream rather than parsed into a tree:
    stdlib-only, and the nesting depth is all we need. Self-closing and void
    elements never open a scope."""
    void = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
            "meta", "param", "source", "track", "wbr"}
    stack = []  # type: List[Tuple[int, Set[str]]]
    found = []  # type: List[Set[str]]
    depth = 0
    pos = 0
    for m in re.finditer(r"<(/?)([a-zA-Z][\w-]*)([^<>]*?)(/?)>", html):
        closing, tag, attrs, selfclose = m.group(1), m.group(2).lower(), m.group(3), m.group(4)
        if closing:
            depth -= 1
            while stack and stack[-1][0] > depth:
                found.append(stack.pop()[1])
            continue
        classes = set()  # type: Set[str]
        for a in re.findall(r'class\s*=\s*"([^"]*)"', attrs) + re.findall(r"class\s*=\s*'([^']*)'", attrs):
            classes |= set(a.split())
        hit = classes & parts
        for _d, acc in stack:
            acc |= hit
        empty = bool(selfclose) or tag in void
        if base in classes and not empty:
            stack.append((depth, set()))
        elif base in classes and empty:
            found.append(set())
        if not empty:
            depth += 1
    while stack:
        found.append(stack.pop()[1])
    return found


# ── DESIGN.md side: what the authors said it is for ─────────────────────────

_MD_EXCLUSION = re.compile(
    r"(never use|not for|do not use|don't use|avoid (?:using )?(?:this|it)|instead use|use \.?\w[\w-]* instead)",
    re.I)


def _design_prose(ds_dir, bases):
    # type: (str, Set[str]) -> Dict[str, Dict[str, str]]
    """Per base class, the DESIGN.md line that introduces it: {name, line,
    notForUseWhen}. The catalog format varies per DS, so we do not parse a
    format - we find the line that MENTIONS `.<base>` and keep it whole. A line
    that also carries exclusion language becomes notForUseWhen; nothing is
    synthesised, so a DS whose DESIGN.md says nothing yields nothing."""
    path = os.path.join(ds_dir, "DESIGN.md")
    if not os.path.isfile(path):
        return {}
    out = {}  # type: Dict[str, Dict[str, str]]
    for raw in _read(path).splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        mentioned = {c for c in re.findall(r"\.([A-Za-z_][\w-]*)", line) if c in bases}
        for base in mentioned:
            # First mention wins: a catalog row introduces a component, later
            # mentions cross-reference it from somewhere else's row.
            if base in out:
                continue
            # The human label a catalog row puts before its first class token.
            label = line.split(".")[0].strip(" \t|-*`")
            row = {"line": re.sub(r"\s+", " ", line)[:400]}
            if label and len(label) <= 40 and not label.startswith("<"):
                row["name"] = label
            if _MD_EXCLUSION.search(line):
                row["notForUseWhen"] = row["line"]
            out[base] = row
    return out


# ── The contract ────────────────────────────────────────────────────────────

def build(ds_dir, ds_id=None):
    # type: (str, Optional[str]) -> Dict[str, object]
    """Derive the whole contract. Deterministic: same sources, same output.
    Called LIVE by ds_lint on every run, so it can never be stale."""
    css = _load_css(ds_dir)
    props_by_class, tags_by_class = _declared(css)
    all_classes = set(props_by_class) | {c for sel, _b in parse_css_rules(css)
                                         for c in classes_in_selector(sel)}

    parts_by_base = {}     # type: Dict[str, Set[str]]
    variants_by_base = {}  # type: Dict[str, Set[str]]
    for cls in all_classes:
        if _is_state(cls):
            continue
        base, part, variant = _split_class(cls)
        if part:
            parts_by_base.setdefault(base, set()).add(cls)
        if variant:
            variants_by_base.setdefault(base, set()).add(cls)

    # A base is a component only when the DS DECLARES it. `.card__title` with no
    # `.card` rule anywhere means the base is a naming convention, not a
    # component, and a contract entry for it would be a fiction the linter then
    # measures pages against.
    bases = sorted(b for b in (set(parts_by_base) | set(variants_by_base) | set(all_classes))
                   if b in all_classes and not _is_state(b)
                   and PART_SEP not in b and VARIANT_SEP not in b)

    prose = _design_prose(ds_dir, set(bases))

    # Required vs optional parts, from the DS's own pages.
    pages = _usage_pages(ds_dir)
    usage = {}  # type: Dict[str, List[Set[str]]]
    if pages:
        html_all = [(p, _read(p)) for p in pages]
        for base in bases:
            parts = parts_by_base.get(base) or set()
            if not parts:
                continue
            seen = []  # type: List[Set[str]]
            for _p, html in html_all:
                if ("\"" + base) not in html and ("'" + base) not in html and (" " + base) not in html:
                    continue
                seen.extend(_instances(html, base, parts))
            if seen:
                usage[base] = seen

    components = []  # type: List[Dict[str, object]]
    for base in bases:
        parts = sorted(parts_by_base.get(base) or [])
        variants = sorted(variants_by_base.get(base) or [])
        role = _role(base, props_by_class.get(base, set()),
                     tags_by_class.get(base, set()), bool(parts))
        instances = usage.get(base) or []
        required, optional = [], list(parts)
        if len(instances) >= 2:
            # Required = present in EVERY instance the DS itself ships. Two
            # instances is the floor: one instance makes every part it happens
            # to use look mandatory.
            required = sorted(p for p in parts if all(p in inst for inst in instances))
            optional = sorted(p for p in parts if p not in required)
        row = {
            "id": base,
            "role": role,
            "requiredParts": required,
            "optionalParts": optional,
            "variants": variants,
        }  # type: Dict[str, object]
        if parts:
            # Only meaningful where there are parts to observe. On a partless
            # component a bare 0 reads as "the DS never uses this", which is a
            # different and false claim.
            row["instancesObserved"] = len(instances)
        md = prose.get(base) or {}
        name = md.get("name")
        if name:
            row["name"] = name
        one_line, source = _one_line(base, role, parts, variants, md)
        row["oneLine"] = one_line
        row["oneLineSource"] = source
        if md.get("notForUseWhen"):
            row["notForUseWhen"] = md["notForUseWhen"]
        components.append(row)

    states = sorted(c for c in all_classes if _is_state(c))
    return {
        "version": CONTRACT_VERSION,
        "dsId": ds_id or os.path.basename(ds_dir.rstrip(os.sep)),
        "generator": "editor/tools/qa/ds_contract.py",
        "generatedFrom": sorted(os.path.basename(p) for p in
                                ([os.path.join(ds_dir, f) for f in ("styles.css", "all.css", "DESIGN.md")
                                  if os.path.isfile(os.path.join(ds_dir, f))] + pages)),
        "note": ("Derived from the design system's own files on every ds_lint run - never "
                 "hand-edit this snapshot, edit the design system. `oneLineSource` says "
                 "whether a rubric is the authors' prose or the generator's description; "
                 "`notForUseWhen` appears only where DESIGN.md states one."),
        "components": components,
        "states": states,
    }


def _one_line(base, role, parts, variants, md):
    # type: (str, str, List[str], List[str], Dict[str, str]) -> Tuple[str, str]
    """The rubric a Choice question sends VERBATIM. The authors' own line when
    there is one; otherwise a structural description that says exactly what was
    observed and claims nothing about intent. The source is recorded because a
    derived rubric is weaker evidence, and the judgment that reads it should be
    able to tell."""
    if md.get("line"):
        return md["line"], "DESIGN.md"
    bits = ["`.%s`" % base, "role %s" % role]
    if parts:
        bits.append("parts %s" % ", ".join("." + p for p in parts[:8]))
    if variants:
        bits.append("variants %s" % ", ".join("." + v for v in variants[:8]))
    return "; ".join(bits), "derived"


def load_or_build(ds_dir, ds_id=None):
    # type: (str, Optional[str]) -> Dict[str, object]
    """What every consumer calls. Always BUILDS - the on-disk contract.json is a
    reviewable snapshot, never an input. Reading it back would reintroduce the
    exact staleness this module exists to remove."""
    return build(ds_dir, ds_id)


def main(argv=None):
    # type: (Optional[List[str]]) -> int
    ap = argparse.ArgumentParser(description="Derive a design system's component contract")
    ap.add_argument("--ds-dir", required=True)
    ap.add_argument("--write", action="store_true",
                    help="write <ds-dir>/contract.json (a reviewable snapshot; "
                         "ds_lint derives it live either way)")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args(argv)

    ds_dir = os.path.abspath(args.ds_dir)
    if not os.path.isdir(ds_dir):
        print("no such design system directory: %s" % ds_dir)
        return 2
    contract = build(ds_dir)
    comps = contract["components"]  # type: ignore[index]
    if args.write:
        out = os.path.join(ds_dir, CONTRACT_FILENAME)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(contract, f, indent=2, ensure_ascii=False)
        print("wrote %s (%d components)" % (out, len(comps)))  # type: ignore[arg-type]
    if args.as_json:
        print(json.dumps(contract, indent=2, ensure_ascii=False))
    elif not args.write:
        authored = sum(1 for c in comps if c.get("oneLineSource") == "DESIGN.md")  # type: ignore[union-attr]
        excl = sum(1 for c in comps if c.get("notForUseWhen"))  # type: ignore[union-attr]
        print("DS contract - ds=%s components=%d  authored oneLine=%d  notForUseWhen=%d"
              % (contract["dsId"], len(comps), authored, excl))  # type: ignore[arg-type]
        for c in comps[:200]:  # type: ignore[index]
            print("  .%-24s %-10s req=%-2d opt=%-2d var=%-2d  %s"
                  % (c["id"], c["role"], len(c["requiredParts"]), len(c["optionalParts"]),
                     len(c["variants"]), c["oneLineSource"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Build per-library index.json files for efficient orchestrator + drawer consumption.

Output (one per library):
  docs/research/photography-library.index.json
  docs/research/illustration-library.index.json
  docs/research/material-library.index.json

Each index contains:
  - version, source path, totalEntries
  - decisionTree: {prototypeSlug: {default, alternatives[], notes}}
  - entries: {styleId|materialId: {name, category, oneLine, roleAffinity, notForUseWhen,
              antiPatternKeywords, lineRange[start,end], pairsPrototypes[]}}
"""

import json
import os
import re
from collections import OrderedDict

ROOT = "/Users/sami/Documents/Woven"
LIBS = [
    {
        "name":   "photography",
        "source": "docs/research/photography-library.md",
        "id_key": "styleId",
        "tree_section": "Style-pick decision tree",
    },
    {
        "name":   "illustration",
        "source": "docs/research/illustration-library.md",
        "id_key": "styleId",
        "tree_section": "Category × prototype decision tree",
    },
    {
        "name":   "material",
        "source": "docs/research/material-library.md",
        "id_key": "materialId",
        "tree_section": "Prototype-style decision tree",
    },
]

ENTRY_RE_TEMPLATE = r"^\-\s+{id_key}:\s+([a-z0-9][a-z0-9\-]*)\s*$"
SECTION_RE = re.compile(r"^##\s+\d+\.\s")
NAME_RE = re.compile(r"^\s*name:\s*(.+?)\s*$", re.MULTILINE)
ERA_RE = re.compile(r"^\s*era:\s*(.+?)\s*$", re.MULTILINE)
CATEGORY_RE = re.compile(r"^\s*category:\s*(.+?)\s*$", re.MULTILINE)
SUBCAT_RE = re.compile(r"^\s*subCategory:\s*(.+?)\s*$", re.MULTILINE)
ROLE_RE = re.compile(r"^\s*role:\s*(.+?)\s*$", re.MULTILINE)
FAMILY_RE = re.compile(r"^\s*family:\s*(.+?)\s*$", re.MULTILINE)
SURFACE_RE = re.compile(r"^\s*surfaceFinish:\s*(.+?)\s*$", re.MULTILINE)
NOTFORUSE_RE = re.compile(r"^\s*notForUseWhen:\s*(.+?)\s*$", re.MULTILINE)
SIG_KEY_RE = re.compile(r"^\s*visualSignatures:\s*$")
BULLET_RE = re.compile(r"^\s*\-\s+(.+?)\s*$")
NEXT_KEY_RE = re.compile(r"^\s*[a-zA-Z][a-zA-Z]+:")
AVOID_KEY_RE = re.compile(r"^\s*avoidKeywords:\s*\[(.+?)\]\s*$", re.MULTILINE)
KILLS_KEY_RE = re.compile(r"^\s*killsTheIllusion:\s*$")
PAIRS_LIST_RE = re.compile(r"prototypeStyles:\s*\[([^\]]+)\]")


def parse_entries(path, id_key):
    """Walk the library file. Return list of dicts with extracted metadata + line range."""
    entry_re = re.compile(ENTRY_RE_TEMPLATE.format(id_key=id_key), re.MULTILINE)
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    # First pass: find all entry start lines + the entry id
    starts = []
    for i, ln in enumerate(lines, start=1):
        m = entry_re.match(ln)
        if m:
            starts.append((i, m.group(1)))
    # Compute end lines (one line before the next entry, OR end of file)
    ranges = []
    for idx, (lineno, eid) in enumerate(starts):
        if idx + 1 < len(starts):
            next_lineno = starts[idx + 1][0]
            end = next_lineno - 1
        else:
            end = len(lines)
        ranges.append((lineno, end, eid))

    # Second pass: for each range, extract fields
    entries = OrderedDict()
    for start, end, eid in ranges:
        block = lines[start - 1 : end]
        body = "".join(block)

        def search(rx):
            m = rx.search(body)
            return m.group(1).strip().strip('"').strip("'") if m else None

        name = search(NAME_RE) or eid.replace("-", " ").title()
        era = search(ERA_RE)
        category = search(CATEGORY_RE)
        family = search(FAMILY_RE)
        surface = search(SURFACE_RE)
        role = search(ROLE_RE)
        not_for = search(NOTFORUSE_RE)

        # visualSignatures — first bullet becomes the oneLine
        sigs = []
        in_sigs = False
        for bln in block:
            if SIG_KEY_RE.match(bln):
                in_sigs = True
                continue
            if in_sigs:
                bm = BULLET_RE.match(bln)
                if bm:
                    sigs.append(bm.group(1).strip().strip('"').strip("'"))
                else:
                    if bln.strip() and not bln.startswith(" "):
                        break
                    if NEXT_KEY_RE.match(bln):
                        in_sigs = False
                        break

        # killsTheIllusion — first 3 items for antiPatternKeywords (used as text-match heuristics)
        kills = []
        in_kills = False
        for bln in block:
            if KILLS_KEY_RE.match(bln):
                in_kills = True
                continue
            if in_kills:
                bm = BULLET_RE.match(bln)
                if bm:
                    kills.append(bm.group(1).strip().strip('"').strip("'"))
                else:
                    if NEXT_KEY_RE.match(bln):
                        in_kills = False
                        break

        # avoidKeywords (photo + illust)
        avoid = []
        am = AVOID_KEY_RE.search(body)
        if am:
            avoid = [w.strip().strip('"').strip("'") for w in am.group(1).split(",") if w.strip()]

        # pairsWith.prototypeStyles
        pairs = []
        pm = PAIRS_LIST_RE.search(body)
        if pm:
            pairs = [p.strip().strip('"').strip("'").strip("`") for p in pm.group(1).split(",") if p.strip()]

        # Compose the one-line summary
        if sigs:
            one_line = sigs[0].rstrip(".") + "."
            if len(one_line) > 200:
                one_line = one_line[:200].rsplit(" ", 1)[0] + "…"
        elif surface and family:
            one_line = f"A {surface} {family} surface."
        else:
            one_line = f"{name} ({category or 'uncategorized'})."

        # Compose roleAffinity per library
        role_aff = []
        if id_key == "styleId":  # photo or illust
            if role:
                role_aff = [role]
            elif category:
                if "fashion" in category or "editorial" in category:
                    role_aff = ["hero", "section"]
                elif category == "product":
                    role_aff = ["product"]
                elif category == "food":
                    role_aff = ["food"]
                elif category == "documentary":
                    role_aff = ["hero", "section", "portrait"]
                elif category == "street":
                    role_aff = ["hero", "section"]
                elif category in ("conceptual", "fine-art"):
                    role_aff = ["hero", "bg"]
                elif category == "lifestyle":
                    role_aff = ["hero", "section", "portrait"]
                else:
                    role_aff = ["hero", "section"]
        else:  # material
            role_aff = []  # materials apply by selector role, not by entry-level affinity

        entry = OrderedDict()
        entry["name"] = name
        entry["category"] = category
        if family:
            entry["family"] = family
        if surface:
            entry["surfaceFinish"] = surface
        if era:
            entry["era"] = era
        entry["oneLine"] = one_line
        if role_aff:
            entry["roleAffinity"] = role_aff
        if not_for:
            entry["notForUseWhen"] = not_for
        if avoid:
            entry["antiPatternKeywords"] = avoid
        elif kills:
            entry["antiPatternKeywords"] = kills[:3]
        if pairs:
            entry["pairsPrototypes"] = pairs[:12]
        entry["lineRange"] = [start, end]

        entries[eid] = entry

    return entries


# Decision tree parser (markdown table rows)
DT_ROW_RE = re.compile(r"^\|\s*`?([a-z0-9][a-z0-9\-\./]+?)`?\s*\|\s*(.+?)\s*\|\s*(.+?)\s*(?:\|\s*(.+?)\s*)?\|\s*$")


def parse_decision_tree(path, section_title):
    """Find the decision tree section and parse table rows into a structured map.

    Match the ACTUAL `## N. <title>` heading, not TOC mentions of the title.
    """
    with open(path, encoding="utf-8") as f:
        text = f.read()
    # Locate the section by its heading pattern: line starting with `## <digit>. <title>`
    heading_re = re.compile(r"^##\s+\d+\.\s+" + re.escape(section_title), re.MULTILINE)
    m = heading_re.search(text)
    if not m:
        return {}
    start_idx = m.start()
    rest = text[start_idx:]
    # Find the NEXT `## N. ` heading after this one (skip the current one)
    next_heading_re = re.compile(r"\n##\s+\d+\.\s")
    next_m = next_heading_re.search(rest, 1)  # start at 1 to skip current heading's newline
    if next_m:
        section_text = rest[: next_m.start()]
    else:
        section_text = rest

    tree = OrderedDict()
    for line in section_text.split("\n"):
        line = line.rstrip()
        if not line.startswith("|") or not line.endswith("|"):
            continue
        # Split on | and strip outer empties
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) < 2:
            continue
        slug = parts[0].strip().strip("`").strip()
        if not slug or slug.startswith("---") or slug.startswith(":") or slug.startswith("Prototype") or slug.startswith("prototype"):
            continue
        if not re.match(r"^[a-z][a-z0-9\-/]+$", slug):
            continue
        col2 = parts[1] if len(parts) > 1 else ""
        col3 = parts[2] if len(parts) > 2 else ""
        col4 = parts[3] if len(parts) > 3 else ""

        # Parse col2 (default) — pick the first comma-separated styleId
        def first_id(s):
            s = re.sub(r"\([^)]*\)", "", s).strip()  # strip parenthetical notes
            parts = [p.strip().strip("`").strip() for p in s.split(",")]
            for p in parts:
                p = re.sub(r"\s.*$", "", p)
                if re.match(r"^[a-z][a-z0-9\-]+$", p):
                    return p
            return ""

        def all_ids(s):
            s = re.sub(r"\([^)]*\)", "", s).strip()
            parts = [p.strip().strip("`").strip() for p in s.split(",")]
            out = []
            for p in parts:
                p = re.sub(r"\s.*$", "", p)
                if re.match(r"^[a-z][a-z0-9\-]+$", p) and p not in out:
                    out.append(p)
            return out

        default = first_id(col2)
        alternatives = all_ids(col3) if col3 else []
        decoration = col4 if col4 else ""

        if default:
            row = OrderedDict()
            row["default"] = default
            if alternatives:
                row["alternatives"] = alternatives
            if decoration:
                # only stash if it looks like a styleId or short phrase
                first_dec = first_id(decoration)
                if first_dec:
                    row["decoration"] = first_dec
                else:
                    row["notes"] = decoration[:120]
            tree[slug] = row

    return tree


def main():
    for lib in LIBS:
        path = os.path.join(ROOT, lib["source"])
        if not os.path.isfile(path):
            print(f"[skip] {path} missing")
            continue

        entries = parse_entries(path, lib["id_key"])
        tree = parse_decision_tree(path, lib["tree_section"])

        out = OrderedDict()
        out["version"] = "1.0"
        out["source"] = lib["source"]
        out["library"] = lib["name"]
        out["totalEntries"] = len(entries)
        out["decisionTree"] = tree
        out["entries"] = entries

        out_path = path.replace("-library.md", "-library.index.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, ensure_ascii=False)
        size_kb = os.path.getsize(out_path) / 1024
        print(f"[{lib['name']}] {len(entries)} entries, decisionTree={len(tree)} slugs → {os.path.basename(out_path)} ({size_kb:.1f}KB)")


if __name__ == "__main__":
    main()

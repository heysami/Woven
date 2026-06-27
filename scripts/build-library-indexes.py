#!/usr/bin/env python3
"""
Build per-library index.json files by SCANNING the per-entry source files in
design-library/<prefix>-*.md (these are the source of truth).

Output (one per library):
  docs/research/photography-library.index.json
  docs/research/illustration-library.index.json
  docs/research/material-library.index.json

Each index contains:
  - version, library, totalEntries
  - decisionTree: {prototypeSlug: {default, alternatives[]}}
    (built from each entry's pairsPrototypes field - first entry to claim a
     slug is the default; subsequent entries become alternatives)
  - entries: {styleId|materialId: {name, category, family, oneLine, roleAffinity,
              notForUseWhen, pairsPrototypes, sourceFile}}
    (sourceFile is a path string the orchestrator/drawer reads at dispatch)

Per-entry files are at design-library/<prefix>-<entryId>.md with YAML
frontmatter. This script ONLY reads those - no big library file is
consulted.

(The folder was renamed from prototype/ → design-library/ in the
"Split prototype/ → design-library/" commit. Library entries live in
design-library/; skill-detail files - step-*, scene-addendum-details,
gallery-html, demo-dock, etc. - live in prototype/ and are NOT scanned
by this script.)

Run after editing any design-library/<prefix>-*.md file:
    python3 scripts/build-library-indexes.py
"""

import json
import os
import re
from collections import OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESIGN_LIBRARY_DIR = os.path.join(ROOT, "design-library")

LIBS = [
    {"prefix": "photo",    "name": "photography",  "id_key": "styleId",    "out": "docs/research/photography-library.index.json"},
    {"prefix": "illust",   "name": "illustration", "id_key": "styleId",    "out": "docs/research/illustration-library.index.json"},
    {"prefix": "material", "name": "material",     "id_key": "materialId", "out": "docs/research/material-library.index.json"},
    {"prefix": "motion",   "name": "motion-scene", "id_key": "techniqueId", "out": "docs/research/motion-scene-library.index.json"},
    {"prefix": "shader",   "name": "shader",       "id_key": "shaderId",    "out": "docs/research/shader-library.index.json"},
]


def parse_frontmatter(text):
    """Parse YAML frontmatter between leading --- ... --- markers. Returns dict."""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not m:
        return {}
    body = m.group(1)
    result = {}
    for line in body.split("\n"):
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1]
            result[key] = [x.strip().strip('"').strip("'") for x in inner.split(",") if x.strip()]
        elif val.startswith('"') and val.endswith('"'):
            result[key] = val[1:-1]
        elif val.startswith("'") and val.endswith("'"):
            result[key] = val[1:-1]
        else:
            result[key] = val
    return result


def parse_oneline_summary(text):
    """Extract the first non-empty paragraph after the H1 title."""
    text2 = re.sub(r"^---\s*\n.*?\n---\s*\n", "", text, count=1, flags=re.DOTALL)
    m = re.search(r"^#\s+.+?\n", text2, re.MULTILINE)
    if not m:
        return ""
    after = text2[m.end():]
    for chunk in after.split("\n\n"):
        chunk = chunk.strip()
        if chunk and not chunk.startswith("#") and not chunk.startswith("<!--"):
            return chunk.split("\n")[0]
    return ""


def role_affinity_from_category(prefix, category):
    """Derive roleAffinity from category for photo entries (illustration uses explicit role; materials skip)."""
    if not category:
        return []
    if prefix == "photo":
        cat = category.lower()
        if "editorial" in cat or "fashion" in cat:
            return ["hero", "section"]
        if cat == "product":
            return ["product"]
        if cat == "food":
            return ["food"]
        if cat == "documentary":
            return ["hero", "section", "portrait"]
        if cat == "street":
            return ["hero", "section"]
        if cat in ("conceptual", "fine-art"):
            return ["hero", "bg"]
        if cat == "lifestyle":
            return ["hero", "section", "portrait"]
        return ["hero", "section"]
    return []


def build_index(lib):
    prefix = lib["prefix"]
    id_key = lib["id_key"]
    entries = OrderedDict()
    decision_tree = OrderedDict()

    files = sorted(f for f in os.listdir(DESIGN_LIBRARY_DIR) if f.startswith(prefix + "-") and f.endswith(".md"))

    for fname in files:
        path = os.path.join(DESIGN_LIBRARY_DIR, fname)
        with open(path, encoding="utf-8") as f:
            text = f.read()
        fm = parse_frontmatter(text)
        eid = fm.get(id_key)
        if not eid:
            continue

        entry = OrderedDict()
        entry["name"] = fm.get("name", "")
        if fm.get("category"):
            entry["category"] = fm["category"]
        if fm.get("family"):
            entry["family"] = fm["family"]
        if fm.get("surfaceFinish"):
            entry["surfaceFinish"] = fm["surfaceFinish"]
        # shader-family stack metadata (the source/filter + blend + layer contract)
        for k in ("defaultBlend", "animated", "needsSource", "stackable"):
            if fm.get(k):
                entry[k] = fm[k]
        if fm.get("era"):
            entry["era"] = fm["era"]
        if fm.get("subCategory"):
            entry["subCategory"] = fm["subCategory"]
        if fm.get("role"):
            role_val = fm["role"]
            entry["role"] = role_val
            entry["roleAffinity"] = [role_val] if isinstance(role_val, str) else role_val
        else:
            ra = role_affinity_from_category(prefix, fm.get("category", ""))
            if ra:
                entry["roleAffinity"] = ra

        one_line = parse_oneline_summary(text)
        if one_line:
            entry["oneLine"] = one_line

        if fm.get("notForUseWhen"):
            entry["notForUseWhen"] = fm["notForUseWhen"]

        pairs = fm.get("pairsPrototypes", [])
        if pairs:
            entry["pairsPrototypes"] = pairs

        entry["sourceFile"] = f"design-library/{fname}"

        entries[eid] = entry

        for slug in pairs:
            slug = slug.strip().strip("`")
            if not slug:
                continue
            if slug not in decision_tree:
                decision_tree[slug] = OrderedDict([("default", eid), ("alternatives", [])])
            else:
                if eid != decision_tree[slug]["default"] and eid not in decision_tree[slug]["alternatives"]:
                    decision_tree[slug]["alternatives"].append(eid)

    out = OrderedDict()
    out["version"] = "2.0"
    out["library"] = lib["name"]
    out["sourceDir"] = "design-library/"
    out["totalEntries"] = len(entries)
    out["decisionTree"] = decision_tree
    out["entries"] = entries

    out_path = os.path.join(ROOT, lib["out"])
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    size_kb = os.path.getsize(out_path) / 1024
    print(f"[{lib['name']}] {len(entries)} entries, decisionTree={len(decision_tree)} slugs → {os.path.basename(out_path)} ({size_kb:.1f}KB)")


def main():
    for lib in LIBS:
        build_index(lib)
    print(f"\nIndexes regenerated by scanning {os.path.relpath(DESIGN_LIBRARY_DIR, ROOT)}/ - per-entry files are the source of truth.")


if __name__ == "__main__":
    main()

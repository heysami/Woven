#!/usr/bin/env python3
"""
Regenerate the 228 per-entry prototype detail files with FULL entry content
(not just summary). Each file becomes self-contained: title + summary + the
verbatim YAML block of that entry + pairs-with + image placeholder.

Both human-readable (Design library tab browseable card) AND orchestrator-
friendly (drawer can read the per-entry file directly instead of sed-slicing
the big library). Either way, no need to digest the 13-17K-word library.

Source of truth stays at docs/research/<name>-library.md — that's where edits
happen; this script regenerates the prototype/ detail files from it.
"""

import json
import os
import re

ROOT = "/Users/sami/Documents/Woven"
LIBS = [
    {
        "prefix": "photo",
        "source": "docs/research/photography-library.md",
        "id_key": "styleId",
        "index":  "docs/research/photography-library.index.json",
    },
    {
        "prefix": "illust",
        "source": "docs/research/illustration-library.md",
        "id_key": "styleId",
        "index":  "docs/research/illustration-library.index.json",
    },
    {
        "prefix": "material",
        "source": "docs/research/material-library.md",
        "id_key": "materialId",
        "index":  "docs/research/material-library.index.json",
    },
]
OUT = os.path.join(ROOT, "prototype")


def extract_block(lines, start, end):
    """Return the verbatim YAML block for an entry, normalized for inclusion."""
    block = lines[start - 1 : end]
    # Strip trailing blank lines + stray ``` fences
    while block and not block[-1].strip():
        block.pop()
    return "".join(block).rstrip()


def regen(lib):
    src_path = os.path.join(ROOT, lib["source"])
    idx_path = os.path.join(ROOT, lib["index"])
    if not os.path.isfile(src_path) or not os.path.isfile(idx_path):
        print(f"[skip] missing {src_path} or {idx_path}")
        return 0

    with open(src_path, encoding="utf-8") as f:
        lines = f.readlines()
    with open(idx_path, encoding="utf-8") as f:
        index = json.load(f)

    prefix = lib["prefix"]
    count = 0

    for eid, entry in index["entries"].items():
        start, end = entry["lineRange"]
        # Adjust end if it strays past file
        end = min(end, len(lines))
        yaml_block = extract_block(lines, start, end)

        name = entry.get("name") or eid.replace("-", " ").title()
        category = entry.get("category") or ""
        family = entry.get("family") or ""
        surface = entry.get("surfaceFinish") or ""
        era = entry.get("era") or ""
        oneLine = entry.get("oneLine") or ""
        pairs = entry.get("pairsPrototypes") or []
        notForUse = entry.get("notForUseWhen") or ""
        role_aff = entry.get("roleAffinity") or []

        # Build the detail file
        parts = []
        parts.append(f"# {name} ({prefix})")
        parts.append("")

        # Tag + key attributes line
        bits = [f"**Tag:** {prefix}-{eid}"]
        if era:
            bits.append(f"**Era:** {era}")
        if family:
            bits.append(f"**Family:** {family}")
        cat_display = category
        if surface and cat_display:
            cat_display = f"{cat_display} · {surface}"
        elif surface:
            cat_display = surface
        if cat_display:
            bits.append(f"**Category:** {cat_display}")
        if role_aff:
            bits.append(f"**Role affinity:** {', '.join(role_aff)}")
        parts.append("  ·  ".join(bits))
        parts.append("")

        # One-line summary
        if oneLine:
            parts.append(oneLine)
            parts.append("")

        # The full library YAML block — paste-ready for the orchestrator,
        # browseable by humans, self-contained per file.
        parts.append("## Full library entry")
        parts.append("")
        parts.append(
            "_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`"
            + lib["source"]
            + "`](../"
            + lib["source"]
            + f") then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._"
        )
        parts.append("")
        parts.append("```yaml")
        parts.append(yaml_block)
        parts.append("```")
        parts.append("")

        # Anti-patterns surfaced separately for browseable scanning
        anti = entry.get("antiPatternKeywords") or []
        if anti and prefix == "material":
            # For materials, antiPatternKeywords are "killsTheIllusion" items — meaningful prose
            parts.append("## Common implementation mistakes (avoid these)")
            parts.append("")
            for a in anti[:5]:
                parts.append(f"- {a}")
            parts.append("")

        if notForUse:
            parts.append("## When NOT to use")
            parts.append("")
            parts.append(notForUse)
            parts.append("")

        if pairs:
            parts.append("## Pairs with (prototype slugs)")
            parts.append("")
            for p in pairs[:12]:
                p = p.strip().strip("`")
                parts.append(f"- `{p}`")
            parts.append("")

        # Image placeholder for the Design library catalog UI
        parts.append("<!-- image: sample-1.png -->")
        parts.append("<!-- reason: representative reference shot of this style -->")
        parts.append("")
        parts.append("---")
        parts.append("")
        parts.append(
            f"_Indexed at line {start}–{end} of `{lib['source']}`. Full index: `{lib['index']}`._"
        )
        parts.append("")

        out_path = os.path.join(OUT, f"{prefix}-{eid}.md")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(parts))
        count += 1

    print(f"[{prefix}] regenerated {count} files from {os.path.basename(src_path)}")
    return count


def main():
    total = 0
    for lib in LIBS:
        total += regen(lib)
    print(f"\nTotal: {total} per-entry files regenerated under {OUT}")


if __name__ == "__main__":
    main()

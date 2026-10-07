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
    {"prefix": "sound",    "name": "sound",        "id_key": "registerId",  "out": "docs/research/sound-library.index.json"},
]

# Emitted into the motion-scene index only. The researcher reads the index and
# nothing else in the dispatch hot path, so the distinction between a POSITION
# VARIABLE and the TRANSPORT that produces it has to live here or it does not
# exist for the agent that needs it.
#
# Bug history: a nine-scene museum film committed binding=self, then ruled out
# all seven scroll-driven techniques with "require scroll runway - structurally
# unavailable, not rejected on taste", and shipped a wheel-advanced slideshow of
# nine separately-generated clips. Its own art-direction contract had asked for
# "descent through darkness, NOT cutting" and "not a slideshow". The scrub was
# both reachable and MORE compliant; the rule-out was an artefact of this
# metadata being missing from the index.
BINDING_MODEL = OrderedDict([
    ("summary",
     "`binding` names a technique's canonical input ADAPTER. It is not a "
     "prerequisite. A scrub is video.pause() plus currentTime = f(progress) plus "
     "a damped pursuit; it needs exactly one thing, a monotonic progress "
     "variable. WHERE that variable comes from is an adapter detail. Any "
     "transport listed in producesProgress can drive any technique whose binding "
     "is scroll-progress or pointer-x."),
    ("producesProgress", OrderedDict([
        ("scroll-progress", "Host scroll offset over a pinned runway: progress = -rect.top / (rect.height - innerHeight)."),
        ("wheel-step", "A wheel/swipe accumulator. TWO valid readings, both legitimate progress sources. (a) CONTINUOUS - map raw accumulated delta straight onto progress; no runway needed. (b) STEPPED-SCRUB - each discrete step sets a WAYPOINT target and a damped pursuit (current += (target-current)*0.06 per rAF) walks currentTime to it, so one flick reads as one authored move along a continuous timeline. Reading (b) is what a linear authored film wants, and scroll-scrub-journey already documents it when it says its waypoints 'become the page's section anchors'. A stepped input does NOT imply stepped media."),
        ("pointer-x", "Pointer position normalised across the viewport."),
        ("scroll-velocity", "Rate of change of scroll offset; drives playbackRate, not currentTime."),
        ("user-gesture", "One-shot trigger. NOT a progress source - gates a play-once or an entrance only."),
        ("hover", "Boolean. Not a progress source."),
        ("none", "Autonomous or time-driven. Not a progress source."),
    ])),
    ("invalidRuleOuts", [
        "\"requires scroll runway\" / \"no runway exists\" / \"structurally unavailable\" applied to a scroll-progress technique because the piece is binding=self. Under binding=self the wheel accumulator IS the progress source - see producesProgress['wheel-step'].",
        "\"the id starts with scroll- so it needs scroll\". Ids name the canonical adapter, not a requirement.",
        "\"category is scroll-driven and this piece does not scroll\". The same error one level up.",
    ]),
    ("validRuleOuts", [
        "The technique's own notForUseWhen clause bites - quote it verbatim.",
        "A binding art-direction contract clause forbids it - quote it verbatim. Note a clause about POINTER reactivity does not reach a wheel-driven or scroll-driven scrub; those are different inputs.",
        "The asset cannot support seeking and cannot be re-encoded - see seekability.",
    ]),
    ("seekability",
     "The one real engineering gate on any scrub, and it is ALREADY SOLVED - do "
     "not hand-roll a parallel fix. Generated-video routes return web-delivery "
     "encodes at GOP ~64, so a seek snaps to the nearest keyframe ~2.7s away and "
     "the scrub reads as broken however good the generated motion is. Keyframe "
     "density is a property of the provider's ENCODER and cannot be prompted "
     "for. The sanctioned path: pass `options.scrub: true` in the "
     "/__asset_generate request for every technique whose binding writes "
     "currentTime, then VERIFY the `scrubGop` echoed in the reply is <= 12 "
     "before composing the scene. A `scrubGop` of null means ffmpeg is missing - "
     "say so and downgrade to a non-scrub sibling rather than shipping a "
     "snapping scrub. See ms-scene-composer step 5b. For assets ALREADY on disk "
     "from an earlier run, the same fix is a local `ffmpeg -g 12` re-encode - no "
     "regeneration, no provider spend. Verify either with `ffprobe "
     "-select_streams v:0 -show_entries frame=key_frame`. If it still judders, "
     "the library's own named substitute is scroll-sequence-frames (preloaded "
     "stills drawn to a canvas)."),
])


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
        # material scope axis: object (per-element, default) | medium (whole-frame
        # process - subsumes live render slots) | both. fxStack = ordered live
        # fx-engine ids (editor/tools/_shared/fx.js) that express the material as a
        # composite stack; the drawer attaches starting params at dispatch.
        if prefix == "material":
            entry["scope"] = fm.get("scope", "object")
            if fm.get("fxStack"):
                entry["fxStack"] = fm["fxStack"]
        # shader-family stack metadata (the source/filter + blend + layer contract)
        for k in ("defaultBlend", "animated", "needsSource", "stackable"):
            if fm.get(k):
                entry[k] = fm[k]
        if fm.get("era"):
            entry["era"] = fm["era"]
        if fm.get("subCategory"):
            entry["subCategory"] = fm["subCategory"]
        # `binding` names a technique's canonical INPUT ADAPTER - never a
        # prerequisite. It MUST reach the index: the researcher reads only the
        # index in the dispatch hot path, so when this field is absent the
        # `scroll-` id prefix becomes the de-facto binding declaration and every
        # scrub technique gets ruled out as "structurally unreachable" the moment
        # the piece is not scroll-bound. See BINDING_MODEL below.
        if fm.get("binding"):
            entry["binding"] = fm["binding"]
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
    if lib["prefix"] == "motion":
        out["bindingModel"] = BINDING_MODEL
    out["decisionTree"] = decision_tree
    out["entries"] = entries

    out_path = os.path.join(ROOT, lib["out"])
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    size_kb = os.path.getsize(out_path) / 1024
    print(f"[{lib['name']}] {len(entries)} entries, decisionTree={len(decision_tree)} slugs → {os.path.basename(out_path)} ({size_kb:.1f}KB)")


# ── Direction axes, for the typed-judgment (Jev) direction picker ───────────
# Emits docs/research/direction-axes.jev.json by SCRAPING the four rosters that
# already live in PROTOTYPE.md. Nothing here is hand-written and nothing here
# is new vocabulary: if this file and PROTOTYPE.md ever disagree about what
# exists, the Jev path is wrong even when Jev is right (invariant I1 in
# docs/features/jev-integration.md, asserted by P1 in
# editor/tests/test_jev_parity.py).
#
# Shape is the Choice `criteria` map each axis question sends verbatim:
# {optionId: rubric}. The rubric is the roster's own tag block plus its own
# one-line description, because a thin rubric is the same failure as a thin
# library index - vague prose yields CONFIDENTLY WRONG inference, and here it
# steers what the user is offered.
PROTOTYPE_MD = os.path.join(ROOT, "PROTOTYPE.md")
DIRECTION_AXES_OUT = "docs/research/direction-axes.jev.json"

# Heading -> axis id, and how many of each the roster is expected to hold
# (a sanity floor, not a lock: adding an entry is normal, losing the whole
# section to a heading rename is not).
DIRECTION_AXES = [
    ("shell",     "## Shell index",         "Page structure: layout, navigation pattern, density class. Pick exactly 1."),
    ("style",     "## Visual styles index", "Surface treatment: depth grammar, decoration vocabulary, materials, type discipline. Pick exactly 1."),
    ("aesthetic", "## Aesthetics index",    "Cultural identity: era, movement, subculture. Optional - many adult-pro briefs have none."),
    ("recipe",    "## Recipes index",       "A known-good (shell + style + aesthetic) bundle. Optional short-circuit for a familiar product type."),
]
# Axes where "the brief implies none of these" is a real answer, not a failure
# to choose. Without this option Jev is forced to pick an aesthetic for a
# Bloomberg terminal.
DIRECTION_NONE_OPTION = {
    "aesthetic": "The brief implies no cultural, era or subculture layer at all - a plain professional surface. Many adult-pro briefs (Linear, Bloomberg, Aesop) sit here.",
    "recipe":    "No recipe matches this brief closely enough; compose the three axes individually instead.",
}

ROSTER_ROW = re.compile(
    r"^-\s+\*\*(?P<id>[^*]+)\*\*\s*(?:`\[(?P<tags>[^\]]*)\]`)?\s*[-=]\s*(?P<desc>.+)$")
# Trailing "→ [`file.md`](./design-library/file.md)" pointer - useful to a
# reading agent, pure noise inside a judgment rubric.
ROSTER_POINTER = re.compile(r"\s*(?:→|->)\s*\[.*$")


def parse_direction_axis(lines, start, end):
    """Rows of ONE roster section as an ordered {id: rubric} map."""
    out = OrderedDict()
    for raw in lines[start + 1:end]:
        m = ROSTER_ROW.match(raw.strip())
        if not m:
            continue
        entry_id = m.group("id").strip().strip("`")
        desc = ROSTER_POINTER.sub("", m.group("desc")).strip().rstrip(".")
        tags = (m.group("tags") or "").strip()
        rubric = f"[{tags}] {desc}" if tags else desc
        if entry_id:
            out[entry_id] = rubric
    return out


def build_direction_axes():
    """docs/research/direction-axes.jev.json - the Choice criteria for the four
    direction axes, lifted from PROTOTYPE.md's own rosters."""
    with open(PROTOTYPE_MD, encoding="utf-8") as f:
        lines = f.read().splitlines()

    found = []
    for axis, heading, _blurb in DIRECTION_AXES:
        idx = next((i for i, l in enumerate(lines) if l.startswith(heading)), None)
        if idx is None:
            raise SystemExit(
                f"[direction-axes] PROTOTYPE.md has no '{heading}' heading. The roster was "
                f"renamed or removed; fix DIRECTION_AXES rather than letting the Jev path "
                f"offer a vocabulary the prompt does not state.")
        found.append((axis, idx))
    # Sections end where the next ## heading begins, whichever it is - relying
    # on roster order would silently swallow anything inserted between them.
    axes = OrderedDict()
    for axis, idx in found:
        end = next((i for i in range(idx + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
        criteria = parse_direction_axis(lines, idx, end)
        if not criteria:
            raise SystemExit(f"[direction-axes] '{axis}' parsed to zero entries - the roster "
                             f"row format changed; update ROSTER_ROW.")
        if len(criteria) > 255:
            raise SystemExit(f"[direction-axes] '{axis}' has {len(criteria)} entries, over the "
                             f"255-option Choice cap. Split the axis before shipping it.")
        blurb = next(b for a, _h, b in DIRECTION_AXES if a == axis)
        entry = OrderedDict()
        entry["question"] = f"Which {axis} does this request imply?"
        entry["axis"] = blurb
        entry["optional"] = axis in DIRECTION_NONE_OPTION
        if axis in DIRECTION_NONE_OPTION:
            criteria["none"] = DIRECTION_NONE_OPTION[axis]
        entry["criteria"] = criteria
        axes[axis] = entry

    out = OrderedDict()
    out["version"] = "1.0"
    out["generatedFrom"] = "PROTOTYPE.md"
    out["generator"] = "scripts/build-library-indexes.py"
    out["note"] = (
        "Choice criteria for the direction-picking axes, scraped from PROTOTYPE.md's own "
        "rosters. Never hand-edit: edit PROTOTYPE.md and re-run the generator. Jev ranks on "
        "roster PROSE and cannot see the design-library/*-ui.png previews the user actually "
        "chooses from, so it narrows candidates and nothing more - the agent still composes "
        "the option cards and runs the recolour pipeline.")
    out["axes"] = axes

    out_path = os.path.join(ROOT, DIRECTION_AXES_OUT)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    counts = ", ".join(f"{a}={len(axes[a]['criteria'])}" for a in axes)
    size_kb = os.path.getsize(out_path) / 1024
    print(f"[direction-axes] {counts} -> {os.path.basename(out_path)} ({size_kb:.1f}KB)")


def main():
    for lib in LIBS:
        build_index(lib)
    build_direction_axes()
    print(f"\nIndexes regenerated by scanning {os.path.relpath(DESIGN_LIBRARY_DIR, ROOT)}/ - per-entry files are the source of truth.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""stories.py - the project's user-story sheet and its prototype location map.

Two artefacts, both per project, both plain files on disk:

  docs/user-stories.xlsx   the stories. Excel, because that is where product
                           people already keep them. Any column layout is
                           accepted; headers are matched against an alias
                           table and normalised into canonical fields. One
                           column must carry a stable ID per story.

  docs/story-map.json      the map. One row per story ID saying WHERE in the
                           prototype that story lives: which page, which
                           element, and the interaction path to reach it.
                           Rendered on the canvas by the story-map node.

The map is the thing that goes stale: the sheet gets edited in Excel, the
prototype gets rebuilt, and nobody notices the two drifted apart. `validate()`
is the mechanical half of catching that - IDs that lost their mapping, mappings
pointing at pages or elements that no longer exist, and rows whose story text
changed since the mapping was recorded. What it cannot judge (does this element
actually SATISFY the story) is left to the requirement-QA agent, which reads
this file's output as its checklist.

Python 3.9-safe, stdlib only. No em dashes anywhere.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

try:
    from . import xlsx_io  # type: ignore
except ImportError:  # loaded flat by serve.py
    import xlsx_io  # type: ignore


STORIES_REL = os.path.join("docs", "user-stories.xlsx")
MAP_REL = os.path.join("docs", "story-map.json")

# Canonical fields, in sheet order. `id` and `title` are the only ones the
# rest of the system relies on; the others ride along for context.
FIELDS = ["id", "epic", "title", "role", "want", "benefit",
          "acceptance", "priority", "status", "notes"]

FIELD_LABELS = {
    "id": "ID",
    "epic": "Epic",
    "title": "Title",
    "role": "As a",
    "want": "I want",
    "benefit": "So that",
    "acceptance": "Acceptance criteria",
    "priority": "Priority",
    "status": "Status",
    "notes": "Notes",
}

FIELD_WIDTHS = [12, 18, 44, 18, 44, 44, 60, 12, 14, 30]

# Header aliases, lowercased and stripped of punctuation before matching.
# First match wins, so keep the specific ones ahead of the generic.
_ALIASES = [
    ("id",         ["id", "story id", "user story id", "us id", "ref", "reference",
                    "key", "ticket", "ticket id", "jira", "jira id", "code", "story key"]),
    ("epic",       ["epic", "feature", "module", "area", "theme", "category",
                    "component", "capability"]),
    ("role",       ["as a", "as an", "role", "persona", "actor", "user type",
                    "user role", "who"]),
    ("want",       ["i want", "i want to", "want", "action", "need", "i need",
                    "requirement", "what"]),
    ("benefit",    ["so that", "benefit", "value", "outcome", "why", "business value",
                    "so i can"]),
    ("acceptance", ["acceptance criteria", "acceptance", "ac", "criteria",
                    "definition of done", "dod", "given when then", "gherkin"]),
    ("priority",   ["priority", "prio", "moscow", "severity", "importance", "rank"]),
    ("status",     ["status", "state", "progress", "stage"]),
    ("notes",      ["notes", "note", "comment", "comments", "remarks", "detail",
                    "details"]),
    # Deliberately last: "description"/"summary" are common titles but would
    # otherwise swallow a sheet whose real title column is named "story".
    ("title",      ["title", "user story", "story", "story title", "summary",
                    "name", "description", "story description", "requirement title"]),
]

FINDING_KINDS = {
    "duplicate-id":    "The sheet uses this ID more than once.",
    "no-id-column":    "No ID column found - IDs were generated from row order.",
    "blank-id":        "A story row has no ID.",
    "unmapped":        "Story has no row in the map.",
    "orphan-mapping":  "Map row points at an ID the sheet no longer has.",
    "missing-page":    "The mapped page does not exist in the prototype.",
    "missing-element": "The mapped element was not found on that page.",
    "no-reach":        "Map row has no interaction path.",
    "stale":           "The story text changed since this mapping was recorded.",
}

_SEVERITY = {
    "duplicate-id": "high",
    "blank-id": "high",
    "orphan-mapping": "high",
    "missing-page": "high",
    "missing-element": "high",
    "stale": "medium",
    "unmapped": "medium",
    "no-id-column": "medium",
    "no-reach": "low",
}


def _now():
    # type: () -> str
    return datetime.datetime.now().replace(microsecond=0).isoformat()


def _norm_header(s):
    # type: (Any) -> str
    s = re.sub(r"[^a-z0-9 ]+", " ", str(s or "").lower())
    return re.sub(r"\s+", " ", s).strip()


def _match_field(header):
    # type: (str) -> Optional[str]
    h = _norm_header(header)
    if not h:
        return None
    for field, names in _ALIASES:
        if h in names:
            return field
    # Loose contains-match, longest alias first so "acceptance criteria" beats "ac".
    for field, names in _ALIASES:
        for n in sorted(names, key=len, reverse=True):
            if len(n) >= 3 and n in h:
                return field
    return None


def _find_header_row(rows):
    # type: (List[List[str]]) -> Tuple[int, Dict[int, str]]
    """Best header row in the first 10, as (row index, {col index: field})."""
    best_idx, best_map, best_score = -1, {}, 0
    for r_idx, row in enumerate(rows[:10]):
        mapping = {}
        seen = set()
        for c_idx, cell in enumerate(row):
            field = _match_field(cell)
            if field and field not in seen:
                mapping[c_idx] = field
                seen.add(field)
        score = len(mapping) + (2 if "id" in seen else 0) + (1 if "title" in seen else 0)
        if score > best_score:
            best_idx, best_map, best_score = r_idx, mapping, score
    return best_idx, best_map


def story_hash(story):
    # type: (Dict[str, Any]) -> str
    """Fingerprint of the MEANING-bearing fields. Status/notes churn is ignored
    on purpose - moving a story to 'done' must not mark its mapping stale."""
    payload = " ".join(str(story.get(k) or "").strip()
                       for k in ("title", "role", "want", "benefit", "acceptance"))
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------------------
# sheet
# ---------------------------------------------------------------------------

def stories_path(project_root):
    # type: (str) -> str
    return os.path.join(project_root, STORIES_REL)


def map_path(project_root):
    # type: (str) -> str
    return os.path.join(project_root, MAP_REL)


def parse_sheet(rows, sheet_name=""):
    # type: (List[List[str]], str) -> Dict[str, Any]
    """Normalise a raw grid into canonical stories + the findings the parse
    itself produced (missing ID column, blank or duplicated IDs)."""
    hdr_idx, colmap = _find_header_row(rows)
    findings = []  # type: List[Dict[str, Any]]
    if hdr_idx < 0:
        return {"stories": [], "columns": {}, "headerRow": -1, "extraColumns": [],
                "findings": [{"kind": "no-id-column", "id": "", "severity": "high",
                              "detail": "No recognisable header row in '%s'."
                                        % (sheet_name or "sheet")}]}

    has_id = "id" in colmap.values()
    if not has_id:
        findings.append({"kind": "no-id-column", "id": "",
                         "severity": _SEVERITY["no-id-column"],
                         "detail": "Add an ID column to '%s' so mappings survive row reordering."
                                   % (sheet_name or "the sheet")})

    header_row = rows[hdr_idx]
    extra = [{"index": c, "label": str(header_row[c]).strip()}
             for c in range(len(header_row))
             if c not in colmap and str(header_row[c]).strip()]

    stories = []
    seen_ids = {}  # type: Dict[str, int]
    for r_idx in range(hdr_idx + 1, len(rows)):
        row = rows[r_idx]
        rec = {f: "" for f in FIELDS}
        for c_idx, field in colmap.items():
            if c_idx < len(row):
                rec[field] = str(row[c_idx] or "").strip()
        rec["extra"] = {e["label"]: (str(row[e["index"]] or "").strip()
                                     if e["index"] < len(row) else "")
                        for e in extra}
        if not any(str(v).strip() for k, v in rec.items() if k != "extra"):
            continue  # blank row
        if not rec["id"]:
            if has_id:
                findings.append({"kind": "blank-id", "id": "",
                                 "severity": _SEVERITY["blank-id"],
                                 "detail": "Row %d has no ID." % (r_idx + 1),
                                 "row": r_idx + 1})
            rec["id"] = "US-%03d" % (len(stories) + 1)
            rec["generatedId"] = True
        if rec["id"] in seen_ids:
            findings.append({"kind": "duplicate-id", "id": rec["id"],
                             "severity": _SEVERITY["duplicate-id"],
                             "detail": "Also used on row %d." % seen_ids[rec["id"]],
                             "row": r_idx + 1})
        else:
            seen_ids[rec["id"]] = r_idx + 1
        rec["row"] = r_idx + 1
        rec["hash"] = story_hash(rec)
        stories.append(rec)

    return {"stories": stories,
            "columns": {str(c): f for c, f in colmap.items()},
            "headerRow": hdr_idx,
            "extraColumns": [e["label"] for e in extra],
            "findings": findings}


def load_stories(project_root):
    # type: (str) -> Dict[str, Any]
    path = stories_path(project_root)
    if not os.path.isfile(path):
        return {"exists": False, "path": STORIES_REL, "stories": [], "findings": [],
                "sheet": "", "columns": {}, "extraColumns": [], "mtime": 0}
    try:
        sheets = xlsx_io.read_xlsx(path)
    except Exception as exc:  # a corrupt or non-xlsx upload
        return {"exists": True, "path": STORIES_REL, "stories": [], "sheet": "",
                "columns": {}, "extraColumns": [], "mtime": os.path.getmtime(path),
                "findings": [{"kind": "no-id-column", "id": "", "severity": "high",
                              "detail": "Could not read the workbook: %s" % exc}],
                "error": str(exc)}
    if not sheets:
        return {"exists": True, "path": STORIES_REL, "stories": [], "sheet": "",
                "columns": {}, "extraColumns": [], "mtime": os.path.getmtime(path),
                "findings": [{"kind": "no-id-column", "id": "", "severity": "high",
                              "detail": "The workbook has no sheets."}]}
    # Prefer a sheet whose name says stories; else the first that parses to rows.
    ordered = sorted(sheets, key=lambda s: 0 if re.search(
        r"stor|requirement|backlog|user", s.get("name", ""), re.I) else 1)
    parsed, chosen = None, ordered[0]
    for sh in ordered:
        p = parse_sheet(sh.get("rows") or [], sh.get("name") or "")
        if p["stories"]:
            parsed, chosen = p, sh
            break
        if parsed is None:
            parsed, chosen = p, sh
    out = {"exists": True, "path": STORIES_REL, "sheet": chosen.get("name") or "",
           "mtime": os.path.getmtime(path)}
    out.update(parsed or {})
    return out


def write_template(project_root, stories=None, sheet_name="User stories"):
    # type: (str, Optional[List[Dict[str, Any]]], str) -> str
    """Write docs/user-stories.xlsx with the canonical header. With no stories,
    seeds three example rows so the shape is obvious in Excel."""
    path = stories_path(project_root)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    rows = [[FIELD_LABELS[f] for f in FIELDS]]
    src = stories if stories else [
        {"id": "US-001", "epic": "Access", "title": "Sign in",
         "role": "returning user", "want": "sign in with my email",
         "benefit": "I can get back to my work",
         "acceptance": "Given valid credentials, when I submit, then I land on the dashboard.",
         "priority": "Must", "status": "Draft", "notes": ""},
        {"id": "US-002", "epic": "Access", "title": "Reset password",
         "role": "user who forgot a password", "want": "request a reset link",
         "benefit": "I am not locked out",
         "acceptance": "Given a known email, when I request a reset, then a link is sent.",
         "priority": "Must", "status": "Draft", "notes": ""},
        {"id": "US-003", "epic": "Dashboard", "title": "See recent activity",
         "role": "signed-in user", "want": "see what changed since my last visit",
         "benefit": "I know where to pick up",
         "acceptance": "Given activity exists, when the dashboard loads, then the newest ten items show.",
         "priority": "Should", "status": "Draft", "notes": ""},
    ]
    for s in src:
        rows.append([str(s.get(f) or "") for f in FIELDS])
    xlsx_io.write_xlsx(path, sheet_name, rows, widths=FIELD_WIDTHS)
    return path


def export_stories(project_root, stories, sheet_name="User stories"):
    # type: (str, List[Dict[str, Any]], str) -> str
    """Overwrite the sheet from a list of canonical story dicts."""
    return write_template(project_root, stories=stories, sheet_name=sheet_name)


# ---------------------------------------------------------------------------
# map
# ---------------------------------------------------------------------------

MAP_ROW_FIELDS = ["id", "screen", "page", "selector", "reach", "note",
                  "confidence", "source", "storyHash", "checkedAt"]


def empty_map(prototype=""):
    # type: (str) -> Dict[str, Any]
    return {"version": 1, "prototype": prototype or "", "updatedAt": "", "rows": []}


def load_map(project_root):
    # type: (str) -> Dict[str, Any]
    path = map_path(project_root)
    if not os.path.isfile(path):
        return empty_map()
    try:
        with open(path, "r", encoding="utf-8") as f:
            doc = json.load(f)
    except (OSError, ValueError):
        return empty_map()
    if not isinstance(doc, dict):
        return empty_map()
    rows = doc.get("rows")
    doc["rows"] = [r for r in rows if isinstance(r, dict)] if isinstance(rows, list) else []
    doc.setdefault("version", 1)
    doc.setdefault("prototype", "")
    doc.setdefault("updatedAt", "")
    return doc


def save_map(project_root, doc):
    # type: (str, Dict[str, Any]) -> str
    path = map_path(project_root)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    clean_rows = []
    for r in (doc.get("rows") or []):
        if not isinstance(r, dict):
            continue
        row = {k: (str(r.get(k) or "").strip()) for k in MAP_ROW_FIELDS}
        if not row["id"]:
            continue
        row["confidence"] = row["confidence"] or "medium"
        row["source"] = row["source"] or "manual"
        clean_rows.append(row)
    out = {"version": 1,
           "prototype": str(doc.get("prototype") or ""),
           "updatedAt": _now(),
           "rows": clean_rows}
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)
    return path


# ---------------------------------------------------------------------------
# validation
# ---------------------------------------------------------------------------

def _proto_root(project_root, prototype):
    # type: (str, str) -> str
    return os.path.join(project_root, "source", prototype or "")


def _read_page(project_root, prototype, page):
    # type: (str, str, str) -> Optional[str]
    """Page is relative to source/<prototype>/. Refuses to escape it."""
    rel = (page or "").strip().lstrip("/")
    if not rel:
        return None
    base = os.path.realpath(_proto_root(project_root, prototype))
    full = os.path.realpath(os.path.join(base, rel))
    if not (full == base or full.startswith(base + os.sep)):
        return None
    if not os.path.isfile(full):
        return None
    try:
        with open(full, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return None


_SEL_TOKEN = re.compile(r"""
    \#(?P<id>[A-Za-z0-9_-]+)
  | \.(?P<cls>[A-Za-z0-9_-]+)
  | \[(?P<attr>[A-Za-z0-9_:-]+)(?:[~|^$*]?=(?P<val>"[^"]*"|'[^']*'|[^\]]*))?\]
  | (?P<tag>^[A-Za-z][A-Za-z0-9]*)
""", re.X)


def selector_misses(html, selector):
    # type: (str, str) -> List[str]
    """Which parts of a CSS-ish selector are absent from the page's markup.

    Deliberately textual, not a real matcher: it answers "does this page still
    contain the id / class / attribute / tag this mapping names", which is the
    drift we can catch without a browser. A selector whose every token appears
    is reported as present even if the nesting changed - a false negative we
    accept, because the alternative is a false alarm on every DOM reshuffle.

    A selector wrapped in quotes, or prefixed `text:`, is checked as literal
    visible text instead.
    """
    sel = (selector or "").strip()
    if not sel:
        return []
    quoted = len(sel) > 1 and sel[0] in ("'", '"') and sel[-1] == sel[0]
    if sel.lower().startswith("text:") or quoted:
        needle = (sel[5:] if sel.lower().startswith("text:") else sel[1:-1]).strip()
        return [] if (needle and needle.lower() in html.lower()) else [sel]

    misses = []
    for part in re.split(r"\s*[>+~]\s*|\s+", sel):
        part = part.strip()
        if not part or part == "*":
            continue
        part = re.sub(r"::?[A-Za-z-]+(\([^)]*\))?", "", part)  # drop pseudo bits
        for m in _SEL_TOKEN.finditer(part):
            if m.group("id"):
                if not re.search(r'id\s*=\s*["\']%s["\']' % re.escape(m.group("id")), html):
                    misses.append("#" + m.group("id"))
            elif m.group("cls"):
                cls = m.group("cls")
                if not re.search(r'class\s*=\s*["\'][^"\']*\b%s\b' % re.escape(cls), html):
                    misses.append("." + cls)
            elif m.group("attr"):
                attr, val = m.group("attr"), (m.group("val") or "").strip("\"'")
                pat = (r'%s\s*=\s*["\'][^"\']*%s' % (re.escape(attr), re.escape(val))) if val \
                    else re.escape(attr)
                if not re.search(pat, html):
                    misses.append("[" + attr + ("=" + val if val else "") + "]")
            elif m.group("tag"):
                if not re.search(r"<%s\b" % re.escape(m.group("tag")), html, re.I):
                    misses.append(m.group("tag"))
    return misses


def validate(project_root, prototype="", stories_doc=None, map_doc=None):
    # type: (str, str, Optional[Dict[str, Any]], Optional[Dict[str, Any]]) -> Dict[str, Any]
    """Mechanical cross-check of sheet against map against prototype."""
    sd = stories_doc if stories_doc is not None else load_stories(project_root)
    md = map_doc if map_doc is not None else load_map(project_root)
    proto = prototype or md.get("prototype") or ""

    findings = list(sd.get("findings") or [])
    stories = sd.get("stories") or []
    by_id = {}  # type: Dict[str, Dict[str, Any]]
    for s in stories:
        by_id.setdefault(str(s.get("id") or ""), s)

    rows = md.get("rows") or []
    mapped_ids = set()
    page_cache = {}  # type: Dict[str, Optional[str]]

    for row in rows:
        sid = str(row.get("id") or "").strip()
        if not sid:
            continue
        mapped_ids.add(sid)
        story = by_id.get(sid)
        if story is None:
            findings.append({"kind": "orphan-mapping", "id": sid,
                             "severity": _SEVERITY["orphan-mapping"],
                             "detail": "No story with this ID in %s." % STORIES_REL})
            continue

        page = str(row.get("page") or "").strip()
        html = None
        if page:
            if page not in page_cache:
                page_cache[page] = _read_page(project_root, proto, page)
            html = page_cache[page]
            if html is None:
                findings.append({"kind": "missing-page", "id": sid,
                                 "severity": _SEVERITY["missing-page"],
                                 "detail": "source/%s/%s is not there." % (proto, page),
                                 "page": page})
        selector = str(row.get("selector") or "").strip()
        if selector and html is not None:
            misses = selector_misses(html, selector)
            if misses:
                findings.append({"kind": "missing-element", "id": sid,
                                 "severity": _SEVERITY["missing-element"],
                                 "detail": "Not on %s: %s" % (page, ", ".join(misses)),
                                 "page": page, "selector": selector})
        if not str(row.get("reach") or "").strip():
            findings.append({"kind": "no-reach", "id": sid, "severity": _SEVERITY["no-reach"],
                             "detail": "No interaction path recorded."})
        recorded = str(row.get("storyHash") or "").strip()
        if recorded and recorded != story.get("hash"):
            findings.append({"kind": "stale", "id": sid, "severity": _SEVERITY["stale"],
                             "detail": "Story text changed since this row was mapped."})

    for s in stories:
        sid = str(s.get("id") or "")
        if sid and sid not in mapped_ids:
            findings.append({"kind": "unmapped", "id": sid, "severity": _SEVERITY["unmapped"],
                             "detail": "No location recorded for this story."})

    counts = {}  # type: Dict[str, int]
    for f in findings:
        counts[f["kind"]] = counts.get(f["kind"], 0) + 1
    by_story = {}  # type: Dict[str, List[Dict[str, Any]]]
    for f in findings:
        if f.get("id"):
            by_story.setdefault(f["id"], []).append(f)

    return {
        "ok": not any(f.get("severity") == "high" for f in findings),
        "checkedAt": _now(),
        "prototype": proto,
        "storyCount": len(stories),
        "mappedCount": len(mapped_ids & set(by_id.keys())),
        "findings": findings,
        "counts": counts,
        "byStory": by_story,
    }


def rows_for_display(project_root, prototype="", validation=None):
    # type: (str, str, Optional[Dict[str, Any]]) -> Dict[str, Any]
    """Everything the story-map canvas node needs in one shot: the joined
    story+mapping rows in sheet order, plus per-row findings."""
    sd = load_stories(project_root)
    md = load_map(project_root)
    proto = prototype or md.get("prototype") or ""
    val = validation if validation is not None else validate(project_root, proto, sd, md)

    by_map = {}
    for r in (md.get("rows") or []):
        sid = str(r.get("id") or "").strip()
        if sid:
            by_map.setdefault(sid, r)

    out = []
    for s in (sd.get("stories") or []):
        sid = str(s.get("id") or "")
        m = by_map.pop(sid, None) or {}
        out.append({
            "id": sid,
            "title": s.get("title") or "",
            "epic": s.get("epic") or "",
            "role": s.get("role") or "",
            "want": s.get("want") or "",
            "benefit": s.get("benefit") or "",
            "acceptance": s.get("acceptance") or "",
            "status": s.get("status") or "",
            "priority": s.get("priority") or "",
            "row": s.get("row") or 0,
            "screen": m.get("screen") or "",
            "page": m.get("page") or "",
            "selector": m.get("selector") or "",
            "reach": m.get("reach") or "",
            "note": m.get("note") or "",
            "confidence": m.get("confidence") or "",
            "source": m.get("source") or "",
            "storyHash": m.get("storyHash") or "",
            "mapped": bool(m),
            "findings": val.get("byStory", {}).get(sid, []),
        })
    # Orphan map rows still have to be visible, or the user cannot delete them.
    for sid, m in by_map.items():
        out.append({
            "id": sid, "title": "", "epic": "", "role": "", "want": "", "benefit": "",
            "acceptance": "", "status": "", "priority": "", "row": 0,
            "screen": m.get("screen") or "", "page": m.get("page") or "",
            "selector": m.get("selector") or "", "reach": m.get("reach") or "",
            "note": m.get("note") or "", "confidence": m.get("confidence") or "",
            "source": m.get("source") or "", "storyHash": m.get("storyHash") or "",
            "mapped": True, "orphan": True,
            "findings": val.get("byStory", {}).get(sid, []),
        })

    return {
        "stories": {"exists": sd.get("exists", False), "path": STORIES_REL,
                    "sheet": sd.get("sheet", ""), "mtime": sd.get("mtime", 0),
                    "count": len(sd.get("stories") or []),
                    "extraColumns": sd.get("extraColumns") or []},
        "map": {"path": MAP_REL, "prototype": proto,
                "updatedAt": md.get("updatedAt", ""),
                "count": len(md.get("rows") or [])},
        "rows": out,
        "validation": val,
    }

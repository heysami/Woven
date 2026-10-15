"""Project references - the sources of truth a project's agents read first.

The user lists, per project, the documents that are authoritative for the
work: a link (a data dictionary in Google Drive, a spec in Notion, a Figma
file) or a path inside the project (one file, or a whole folder). They are
edited from the References tab of the Preview file panel and stored in
<project>/references.json, which syncs with the project like personas.json.

Two ways they reach an agent:

  1. STANDING - every chat thread is told the current list (serve.py
     _refs_send): with its first message, again whenever the list changes,
     and with every Plan or Triage message, the two modes that lean on
     history hardest. The block makes the agent open a reference FRESH
     instead of trusting memory, an earlier thread or an older copy, which is
     the stale-information failure this exists to stop.
  2. NAMED - `>>name` in the composer drops a chip, and the client spells out
     name -> location for that one message (app.js composeWithAttachments).

Nothing here fetches a link. Opening it is the agent's job, with whatever tool
can (and saying so when it cannot), so a reference is always read as it is
today rather than as it was when someone last copied it.
"""
from __future__ import annotations  # keep annotations 3.9-safe (daemon runs system py)

import hashlib
import json
import os
import re
import secrets
import threading
import time

_LOCK = threading.Lock()

ID_RE = re.compile(r"^r_[a-z0-9]{4,24}$")
STORE_NAME = "references.json"
MAX_REFS = 40
NAME_CAP = 80
LOCATION_CAP = 2000
NOTE_CAP = 600

_SCHEME_RE = re.compile(r"^[a-z][a-z0-9+.-]*://", re.I)
# "drive.google.com/drive/folders/x" typed without a scheme. A bare file name
# ("data.csv") also looks like a host, so only a host FOLLOWED by a path, or
# one starting www., counts - and only when no such path exists in the project.
_HOSTISH_RE = re.compile(r"^(www\.)?[a-z0-9-]+(\.[a-z0-9-]+)*\.[a-z]{2,}(:\d+)?(/|$)", re.I)


def store_path(root):
    return os.path.join(root, STORE_NAME)


def load(root):
    try:
        with open(store_path(root), "r", encoding="utf-8") as f:
            doc = json.load(f)
    except (OSError, ValueError):
        return []
    rows = doc.get("references") if isinstance(doc, dict) else None
    return [r for r in (rows or []) if isinstance(r, dict) and ID_RE.match(str(r.get("id") or ""))
            and isinstance(r.get("name"), str) and isinstance(r.get("location"), str)]


def _write(root, rows):
    path = store_path(root)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"version": 1, "references": rows}, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)


def _clean_rel(p):
    """A project-relative path, or None when it escapes the project."""
    p = p.strip().replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    p = p.lstrip("/")
    if not p or p == ".." or p.startswith("../") or "/../" in p or p.endswith("/.."):
        return None
    return p.rstrip("/") or None


def classify(root, location):
    """("link", url) or ("path", project-relative path). Raises ValueError."""
    loc = (location or "").strip()
    if not loc:
        raise ValueError("a reference needs a link or a project path")
    if len(loc) > LOCATION_CAP:
        raise ValueError("that location is too long")
    if _SCHEME_RE.match(loc):
        if not re.match(r"^https?://", loc, re.I):
            raise ValueError("links must start with http:// or https://")
        if re.search(r"\s", loc):
            raise ValueError("a link cannot contain spaces")
        return "link", loc
    rel = _clean_rel(loc)
    if root and os.path.isabs(loc):
        # An absolute path that points inside the project becomes relative;
        # anything outside it is not part of the project, so it is refused.
        try:
            rp = os.path.relpath(os.path.realpath(loc), os.path.realpath(root))
        except ValueError:
            rp = ".."
        if rp == ".." or rp.startswith(".." + os.sep):
            raise ValueError("only paths inside the project can be references; share anything else as a link")
        rel = _clean_rel(rp.replace(os.sep, "/"))
    if rel and root and os.path.exists(os.path.join(root, rel)):
        return "path", rel
    if _HOSTISH_RE.match(loc) and ("/" in loc or loc.lower().startswith("www.")) and not re.search(r"\s", loc):
        return "link", "https://" + loc
    if not rel:
        raise ValueError("that path is outside the project")
    return "path", rel


def normalize(root, raw, prev=None):
    """A reference record from the panel's form, validated. Raises ValueError."""
    if not isinstance(raw, dict):
        raise ValueError("reference must be an object")
    name = raw.get("name")
    name = re.sub(r"\s+", " ", name).strip()[:NAME_CAP] if isinstance(name, str) else ""
    if not name:
        raise ValueError("a reference needs a name")
    _, location = classify(root, raw.get("location") if isinstance(raw.get("location"), str) else "")
    note = raw.get("note")
    note = note.strip()[:NOTE_CAP] if isinstance(note, str) else ""
    rid = raw.get("id")
    now = int(time.time() * 1000)
    return {
        "id": rid if isinstance(rid, str) and ID_RE.match(rid) else "r_" + secrets.token_hex(4),
        "name": name,
        "location": location,
        "note": note,
        "createdAt": (prev or {}).get("createdAt") or now,
        "updatedAt": now,
    }


def upsert(root, raw):
    with _LOCK:
        rows = load(root)
        prev = next((r for r in rows if r.get("id") == (raw or {}).get("id")), None)
        rec = normalize(root, raw, prev)
        clash = next((r for r in rows if r["id"] != rec["id"] and r["name"].lower() == rec["name"].lower()), None)
        if clash:
            raise ValueError('another reference is already called "%s"' % clash["name"])
        if prev:
            rows = [rec if r.get("id") == rec["id"] else r for r in rows]
        else:
            if len(rows) >= MAX_REFS:
                raise ValueError("at most %d references per project" % MAX_REFS)
            rows.append(rec)
        _write(root, rows)
        return rec, rows


def delete(root, rid):
    with _LOCK:
        rows = [r for r in load(root) if r.get("id") != rid]
        _write(root, rows)
        return rows


def move(root, rid, delta):
    """Shift one reference up (-1) or down (+1); the order is the order the
    agent reads the list in, so the most important goes first."""
    with _LOCK:
        rows = load(root)
        i = next((k for k, r in enumerate(rows) if r.get("id") == rid), -1)
        j = i + (1 if delta > 0 else -1)
        if i < 0 or j < 0 or j >= len(rows):
            return rows
        rows[i], rows[j] = rows[j], rows[i]
        _write(root, rows)
        return rows


def kind_of(root, location):
    """link | file | folder | missing - computed, never stored: a folder the
    user names before creating it is still a valid reference."""
    if re.match(r"^https?://", location or "", re.I):
        return "link"
    full = os.path.join(root, location)
    if os.path.isdir(full):
        return "folder"
    if os.path.isfile(full):
        return "file"
    return "missing"


def listing(root):
    """The panel's view: every record plus its computed kind."""
    return [dict(r, kind=kind_of(root, r["location"])) for r in load(root)]


def digest(rows) -> str:
    """Changes whenever what an agent is told changes (name, place, note,
    order) - the per-thread "already told" stamp compares this."""
    if not rows:
        return ""
    raw = json.dumps([[r.get("name"), r.get("location"), r.get("note") or ""] for r in rows], ensure_ascii=False)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10]


def _line(root, r):
    kind = kind_of(root, r["location"]) if root else ("link" if r["location"].startswith("http") else "file")
    where = r["location"] + {"folder": " (project folder)", "file": " (project file)",
                             "missing": " (project path, NOT FOUND right now)"}.get(kind, "")
    return "- %s: %s%s" % (r["name"], where, (" - source of truth for: " + r["note"]) if r.get("note") else "")


def text_listing(root, rows=None):
    """GET /__references?format=text - the list as an agent reads it."""
    rows = load(root) if rows is None else rows
    if not rows:
        return "This project has no references set."
    return "Project references (sources of truth, most important first):\n" + "\n".join(_line(root, r) for r in rows)


# The rules ride WITH the list so a thread that only ever saw the block (an
# old preamble, a codex runtime) still knows what to do with it.
_RULES = (
    "How to use them: when what you are working on touches what a reference covers, open that reference FRESH "
    "before you rely on anything else (fetch a link, read the project file or folder now), never from memory, an "
    "earlier conversation or an older copy in the project. Where a reference disagrees with an earlier decision, "
    "an older file or your own assumption, the reference wins; when the disagreement looks deliberate (the user "
    "decided otherwise later), name both sides and ask instead of picking. A link you cannot open (sign-in wall, "
    "error): say so and ask the user for access or an export, and never fall back to a stale copy without saying "
    "so (Google Docs and Sheets shared by link often open at .../export?format=txt or .../export?format=csv). "
    "Say which reference you used, and name the references a subagent or a QA check needs in its brief. "
    "The current list, any time: curl -s \"$TH_DAEMON_URL/__references?project=$TH_PROJECT_ID&format=text\""
)


def agent_block(root, rows) -> str:
    """Appended to a chat message (serve.py _refs_send). An empty list after a
    non-empty one says the earlier list is void."""
    if not rows:
        return ("\n\n---\n[Woven project references: the user removed every reference from this project. The "
                "list given earlier in this thread no longer applies.]")
    return ("\n\n---\n[Woven project REFERENCES - the sources of truth the user set for this project, most "
            "important first. This list replaces any list given earlier in this thread.\n"
            + "\n".join(_line(root, r) for r in rows) + "\n" + _RULES + "]")

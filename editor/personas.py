"""Simulated personas - research-based user profiles that critique the work.

Two halves:

  1. STORE - <project>/personas/personas.json, one record per persona, synced
     with the project (it is research, not machine-local state). Edited from
     the Personas panel on the workflow rail (canvas and preview).

  2. CRITIQUE - the composer's critic picker arms a critique for a message.
     When the agent finishes that work it POSTs /__critic/run with what
     changed (in a user's words) and the pages to open. This module then:
       - asks a FAST model for a short user-research plan (a task table),
       - walks that plan in a real browser (tools/qa/persona_walk.py),
         screenshotting every step, once per device the personas use,
       - runs every persona as an ISOLATED one-shot with NO tools: its prompt
         carries only its profile, the documents the user granted it, the
         plain-language summary and (simulate) the step screenshots. A
         persona never sees code, file names or the agent's transcript.
     The report lives under <project>/personas/critiques/<id>/ (gitignored)
     and is streamed to the chat thread as a `persona_critique` event the
     card renders; the agent gets a text digest to turn into suggestions.

serve.py injects the model calls, the page resolver and the event sink
(see run_critique's `deps`), so this module stays free of daemon state.
"""
from __future__ import annotations  # keep annotations 3.9-safe (daemon runs system py)

import hashlib
import json
import os
import re
import secrets
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser

import references as _references

_LOCK = threading.Lock()

ID_RE = re.compile(r"^p_[a-z0-9]{4,24}$")
CRITIQUE_ID_RE = re.compile(r"^c_[a-f0-9]{10}$")
HOWS = ("text", "simulate")
DEVICES = ("desktop", "mobile")

# The profile is ONE free markdown text. Only two things are read out of it:
# the name (its first line) and the device (a "Device: phone" line makes a
# simulation use a phone screen). Everything else goes to the persona as is.
PROFILE_CAP = 20000
MAX_PERSONAS = 40
MAX_KNOWLEDGE = 24

# Taste: images of apps, styles and products the persona likes or feels at
# home with. Uploaded into personas/taste/ (synced with the project), each
# file prefixed with its persona's id so a delete can take its files along,
# or picked like What they know: project images and folders, and references.
TASTE_DIR = "personas/taste"
TASTE_EXTS = {"png": "png", "jpeg": "jpg", "jpg": "jpg", "webp": "webp", "gif": "gif"}
TASTE_BYTES = 5 * 1024 * 1024
MAX_TASTE = 8

# Granted knowledge: documents only. A persona never reads code, so markup,
# scripts and styles are refused even inside a granted folder.
DOC_EXTS = {"md", "markdown", "txt", "csv", "tsv", "json", "yaml", "yml"}
IMAGE_EXTS = {"png", "jpg", "jpeg", "webp", "gif"}
CODE_EXTS = {"html", "htm", "js", "mjs", "cjs", "ts", "tsx", "jsx", "css", "scss",
             "less", "py", "sh", "rb", "go", "rs", "java", "swift", "kt", "vue",
             "svelte", "php", "glsl", "frag", "vert", "wgsl", "svg", "xml"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".history", ".trash", "critiques",
             "_attachments", "workflow"}
KNOW_FILE_CAP = 12000
KNOW_TOTAL_CAP = 40000
KNOW_IMAGES = 4
KNOW_IMAGE_BYTES = 3 * 1024 * 1024

# An entry of What they know or Taste is a project path, or "ref:<id>": one of
# the project's references (editor/references.py), looked up when it is read,
# so a reference can be an online location and an edit to it reaches every
# persona using it. Personas have no tools: the daemon opens a link for them.
REF_RE = re.compile(r"^ref:(r_[a-z0-9]{4,24})$")
LINK_BYTES = 3 * 1024 * 1024
LINK_TIMEOUT = 20
LINK_WORKERS = 4

MAX_PAGES = 4
MAX_TASKS = 8
MAX_SUGGESTIONS = 5
PERSONA_WORKERS = 4


# ── store ─────────────────────────────────────────────────────────────────

def store_dir(root):
    return os.path.join(root, "personas")


def store_path(root):
    return os.path.join(store_dir(root), "personas.json")


def critiques_dir(root):
    return os.path.join(store_dir(root), "critiques")


def load(root):
    try:
        with open(store_path(root), "r", encoding="utf-8") as f:
            doc = json.load(f)
    except (OSError, ValueError):
        return []
    rows = doc.get("personas") if isinstance(doc, dict) else None
    out = []
    for p in rows or []:
        if isinstance(p, dict) and ID_RE.match(str(p.get("id") or "")):
            if not isinstance(p.get("profile"), str) or not p["profile"].strip():
                p = dict(p, profile=_legacy_profile(p))
            out.append(p)
    return out


_LEGACY = (("demographics", "About"), ("goals", "Goals"), ("frustrations", "Frustrations"),
           ("behaviours", "Habits and context"))


def _legacy_profile(raw):
    """A persona saved by the first, field-by-field form, as one markdown text."""
    def txt(k):
        v = raw.get(k)
        return v.strip() if isinstance(v, str) else ""
    lines = ["# " + txt("name")] if txt("name") else []
    if txt("role"):
        lines.append(txt("role"))
    for key, head in _LEGACY:
        if txt(key):
            lines += ["", "## " + head, txt(key)]
    tail = []
    if raw.get("techComfort") in ("low", "medium", "high"):
        tail.append("Comfort with tech: " + raw["techComfort"])
    if raw.get("device") == "mobile":
        tail.append("Device: phone")
    if tail:
        lines += [""] + tail
    if txt("quote"):
        lines += ["", '> "%s"' % txt("quote").strip('"')]
    return "\n".join(lines)


_DEVICE_RE = re.compile(r"^[ \t>*-]*device\s*:\s*(.+)$", re.I | re.M)


def profile_name(text):
    """The persona's name: the profile's first line, heading marks dropped."""
    for line in (text or "").splitlines():
        t = line.strip().lstrip("#").strip().strip("*_").strip()
        if t:
            return t[:80]
    return ""


_META_RE = re.compile(r"^\s*(?:device|comfort with tech)\s*:", re.I)
_EMPTY_LINE_RE = re.compile(r"^\s*[-*>]?\s*$")
_HEADING_RE = re.compile(r"^\s*#{1,6}\s")


def profile_summary(text):
    """Who they are, in one line, for list rows and the critique card: the
    first written line after the name (empty skeleton bullets skipped)."""
    lines = [l.strip() for l in (text or "").splitlines() if l.strip()]
    for t in lines[1:]:
        if t.startswith("#") or t.startswith(">") or _META_RE.match(t):
            continue
        t = re.sub(r"^[-*]\s*", "", t).strip("*_ ")
        if re.search(r"\w", t):
            return t[:120]
    return ""


def profile_clean(text):
    """The profile as the persona reads it: the editor's skeleton bullets and
    headings that were left empty are dropped."""
    lines = [l for l in (text or "").splitlines() if not (l.strip() and _EMPTY_LINE_RE.match(l))]
    out = []
    for i, line in enumerate(lines):
        if _HEADING_RE.match(line) and i > 0:
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j >= len(lines) or _HEADING_RE.match(lines[j]):
                continue
        out.append(line)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()


def profile_device(text):
    m = _DEVICE_RE.search(text or "")
    return "mobile" if m and re.search(r"\b(phone|mobile|iphone|android|smartphone)\b", m.group(1), re.I) else "desktop"


def _write(root, rows):
    os.makedirs(store_dir(root), exist_ok=True)
    path = store_path(root)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"version": 1, "personas": rows}, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)


def _clean_rel(p):
    """A project-relative path the user granted, or None."""
    if not isinstance(p, str):
        return None
    p = p.strip().replace("\\", "/").lstrip("/")
    while p.startswith("./"):
        p = p[2:]
    if not p or p.startswith("..") or "/../" in p or len(p) > 400:
        return None
    return p.rstrip("/") or None


def _clean_entry(p):
    """A granted entry: "ref:<id>" as is, otherwise a project path, or None."""
    if isinstance(p, str) and p.strip().startswith("ref:"):
        return p.strip() if REF_RE.match(p.strip()) else None
    return _clean_rel(p)


def normalize(raw, prev=None):
    """A persona record from the panel, validated. Raises ValueError."""
    if not isinstance(raw, dict):
        raise ValueError("persona must be an object")
    text = raw.get("profile") if isinstance(raw.get("profile"), str) else ""
    if not text.strip():
        text = _legacy_profile(raw)
    text = _DASH_RE.sub(" - ", text).strip()[:PROFILE_CAP]
    name = profile_name(text)
    if not name:
        raise ValueError("start the profile with the persona's name on the first line")
    pid = raw.get("id")
    pid = pid if isinstance(pid, str) and ID_RE.match(pid) else "p_" + secrets.token_hex(4)
    out = {"id": pid, "name": name, "role": profile_summary(text), "device": profile_device(text),
           "profile": text}
    know = []
    for p in raw.get("knowledge") or []:
        c = _clean_entry(p)
        if c and c not in know:
            know.append(c)
    out["knowledge"] = know[:MAX_KNOWLEDGE]
    # Another persona's uploads are not grantable: its delete sweeps them.
    taste = []
    for p in raw.get("taste") or []:
        c = _clean_entry(p)
        if c and (not c.startswith(TASTE_DIR + "/") or c.startswith(TASTE_DIR + "/" + pid + "-")) and c not in taste:
            taste.append(c)
    out["taste"] = taste[:MAX_TASTE]
    now = int(time.time() * 1000)
    out["createdAt"] = (prev or {}).get("createdAt") or now
    out["updatedAt"] = now
    return out


def upsert(root, raw):
    with _LOCK:
        rows = load(root)
        prev = next((p for p in rows if p.get("id") == (raw or {}).get("id")), None)
        rec = normalize(raw, prev)
        if prev:
            rows = [rec if p.get("id") == rec["id"] else p for p in rows]
        else:
            if len(rows) >= MAX_PERSONAS:
                raise ValueError("at most %d personas per project" % MAX_PERSONAS)
            rows.append(rec)
        _write(root, rows)
        _sweep_taste(root, rows)
        return rec, rows


def delete(root, pid):
    with _LOCK:
        rows = [p for p in load(root) if p.get("id") != pid]
        _write(root, rows)
        _sweep_taste(root, rows, gone=pid)
        return rows


def save_taste(root, pid, data, mime_ext):
    """Store one taste image for a persona (saved or about to be). Returns its
    project-relative path."""
    if not ID_RE.match(pid or ""):
        raise ValueError("id must be a persona id")
    ext = TASTE_EXTS.get((mime_ext or "").lower())
    if not ext:
        raise ValueError("taste images must be png, jpg, webp or gif")
    if not data or len(data) > TASTE_BYTES:
        raise ValueError("a taste image must be under 5 MB")
    d = os.path.join(root, TASTE_DIR)
    os.makedirs(d, exist_ok=True)
    name = "%s-%s.%s" % (pid, secrets.token_hex(4), ext)
    with open(os.path.join(d, name), "wb") as f:
        f.write(data)
    return TASTE_DIR + "/" + name


def _sweep_taste(root, rows, gone=None):
    """Drop taste images nothing points at: a removed image of a saved persona
    at once, a deleted persona's all, and a day-old upload from an editor that
    was never saved."""
    d = os.path.join(root, TASTE_DIR)
    try:
        names = os.listdir(d)
    except OSError:
        return
    kept = {t for p in rows for t in (p.get("taste") or [])}
    ids = {p.get("id") for p in rows}
    now = time.time()
    for name in names:
        pid = name.split("-", 1)[0]
        rel = TASTE_DIR + "/" + name
        if rel in kept:
            continue
        path = os.path.join(d, name)
        try:
            stale = now - os.path.getmtime(path) > 86400
        except OSError:
            continue
        if pid == gone or pid in ids or stale:
            try:
                os.remove(path)
            except OSError:
                pass


# ── the critique request riding on a message ──────────────────────────────

def norm_critic(raw):
    """{personas: [ids], how} from a composer send, or None when unarmed.
    An object with no personas is an explicit "off" and normalises to {}."""
    if not isinstance(raw, dict):
        return None
    ids = []
    for p in raw.get("personas") or []:
        if isinstance(p, str) and ID_RE.match(p) and p not in ids:
            ids.append(p)
    if not ids:
        return {}
    return {"personas": ids[:8], "how": raw.get("how") if raw.get("how") in HOWS else "text"}


def critic_message(critic, names):
    """The block appended to a message the user armed a critique on."""
    ids = json.dumps(critic["personas"])
    who = ", ".join(names) or "the selected personas"
    sim = critic["how"] == "simulate"
    body = {"personas": critic["personas"], "how": critic["how"],
            "change": "<what changed, in a user's words>"}
    if sim:
        body["pages"] = ["<prototype>/<page>.html"]
        body["flow"] = "<the steps a user takes, by on-screen labels>"
    lines = [
        "",
        "",
        "---",
        "### Persona critique is armed for this message (the user ticked %s in the composer, %s)"
        % (who, "simulated on the pages" if sim else "as text"),
        "When the work this message asks for is DONE and changed something a person using the product would see or do, "
        "ask these simulated personas to critique it. Skip it when nothing a user would notice changed (an answer, a plan, "
        "a triage, a failed attempt) and say in one line that it was skipped and why.",
        "",
        "Start it with one call (it runs every persona in isolation; each call waits at most 100 seconds for them):",
        "curl -s -m 120 -X POST \"$TH_DAEMON_URL/__critic/run?project=$TH_PROJECT_ID&run=$TH_RUN_ID\" "
        "-H 'Content-Type: application/json' --data-binary @- <<'JSON'",
        json.dumps(body),
        "JSON",
        "- personas = %s and how = \"%s\": exactly these, the user picked them." % (ids, critic["how"]),
        "- change: what changed, in the words of someone USING the product: what they now see, can do, and where. "
        "Never name code, files, selectors, components, settings keys or how it is built. The personas never see code.",
    ]
    if sim:
        lines += [
            "- pages: the page(s) a user opens to meet the change, start page first (at most %d), as a prototype "
            "slug or a path under source/, a query allowed: \"my-app\", \"my-app/settings.html?tab=billing\"." % MAX_PAGES,
            "- flow: one line, the path from the start page to the change, by on-screen labels.",
        ]
    lines += [
        "While the reply says \"status\": \"running\", call curl -s -m 120 \"$TH_DAEMON_URL/__critic/<id>?project=$TH_PROJECT_ID&wait=100&format=text\" "
        "again with its id; a simulation usually takes two to five minutes.",
        "",
        "Then end your reply with the personas' SUGGESTIONS: one bullet each, merged where two personas raise the same "
        "thing, each naming who raised it and how important it is. They are suggestions only: change NOTHING because of "
        "them and put no question card on them; the user decides what to do next. The full critique (screens, steps, "
        "reactions) already shows in the thread as a card, so do not retell it.",
    ]
    return "\n".join(lines)


# ── granted knowledge ─────────────────────────────────────────────────────

def _ext(path):
    return path.rsplit(".", 1)[-1].lower() if "." in os.path.basename(path) else ""


def resolve_entries(root, entries):
    """What each entry points at now, with the name the persona sees:
    {"path": rel} | {"link": url} | {"missing": why}. References are read
    fresh from references.json on every call."""
    refs, out = None, []
    for raw in entries or []:
        c = _clean_entry(raw)
        if not c:
            continue
        m = REF_RE.match(c)
        if not m:
            out.append({"path": c, "name": c})
            continue
        if refs is None:
            refs = {r["id"]: r for r in _references.load(root)}
        r = refs.get(m.group(1))
        if not r:
            out.append({"missing": "a reference that was removed", "name": "a removed reference"})
        elif re.match(r"^https?://", r["location"], re.I):
            out.append({"link": r["location"], "name": r["name"]})
        else:
            out.append({"path": r["location"], "name": r["name"]})
    return out


def _export_url(url):
    """A shared Google Doc, Sheet or Slides link, as its plain export: the
    viewer page itself is a script shell with no readable text."""
    m = re.match(r"^https://docs\.google\.com/(document|spreadsheets|presentation)/d/([\w-]+)", url)
    if not m:
        return url
    kind, did = m.groups()
    if kind == "spreadsheets":
        g = re.search(r"[#&?]gid=(\d+)", url)
        return "https://docs.google.com/spreadsheets/d/%s/export?format=csv%s" % (did, "&gid=" + g.group(1) if g else "")
    return "https://docs.google.com/%s/d/%s/export?format=txt" % (kind, did)


class _PageText(HTMLParser):
    """The readable text of a web page: no scripts, styles or markup."""
    SKIP = {"script", "style", "noscript", "svg", "template", "head"}
    BLOCK = {"p", "div", "br", "li", "tr", "td", "th", "h1", "h2", "h3", "h4", "h5", "h6", "section",
             "article", "header", "footer", "main", "nav", "aside", "blockquote", "pre", "dt", "dd", "figcaption"}

    def __init__(self):
        HTMLParser.__init__(self, convert_charrefs=True)
        self.parts, self.title, self._skip, self._in_title = [], "", 0, False

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self._in_title = True
        elif tag in self.SKIP:
            self._skip += 1
        if tag in self.BLOCK:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag in self.SKIP and self._skip:
            self._skip -= 1
        if tag in self.BLOCK:
            self.parts.append("\n")

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        elif not self._skip:
            self.parts.append(data)

    def text(self):
        lines = [re.sub(r"[ \t\r\f\v]+", " ", l).strip() for l in "".join(self.parts).split("\n")]
        return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


_SIGNIN_RE = re.compile(r"^https?://(accounts\.google\.com|login\.microsoftonline\.com|[^/]+/(login|signin|sign-in|sign_in|auth)\b)", re.I)
_LINK_HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                               "(KHTML, like Gecko) Chrome/126.0 Safari/537.36",
                 "Accept": "text/html,text/plain,text/csv,application/json,image/*;q=0.9,*/*;q=0.5"}


def fetch_link(url, scratch):
    """Open a reference link as a signed-out visitor, fresh (never from an
    older copy). {"text": ...} for a document or page, {"image": path} for an
    image (saved under scratch), {"error": why} otherwise."""
    try:
        req = urllib.request.Request(_export_url(url), headers=_LINK_HEADERS)
        with urllib.request.urlopen(req, timeout=LINK_TIMEOUT) as r:
            final = r.geturl() or url
            ctype = (r.headers.get_content_type() or "").lower()
            charset = r.headers.get_content_charset() or "utf-8"
            data = r.read(LINK_BYTES + 1)
    except urllib.error.HTTPError as e:
        return {"error": "could not open it (HTTP %d)%s" % (
            e.code, ": it may need a sign-in, share it publicly" if e.code in (401, 403) else "")}
    except Exception as e:
        return {"error": "could not open it (%s)" % str(getattr(e, "reason", None) or e)[:120]}
    if _SIGNIN_RE.match(final):
        return {"error": "it needs a sign-in: share it publicly or add a copy to the project"}
    if ctype.startswith("image/"):
        ext = TASTE_EXTS.get(ctype.split("/", 1)[1])
        if not ext:
            return {"error": "a %s image, only png, jpg, webp or gif are read" % ctype.split("/", 1)[1]}
        if len(data) > KNOW_IMAGE_BYTES:
            return {"error": "the image is over 3 MB"}
        os.makedirs(scratch, exist_ok=True)
        path = os.path.join(scratch, "link-%s.%s" % (hashlib.sha1(url.encode("utf-8")).hexdigest()[:12], ext))
        with open(path, "wb") as f:
            f.write(data)
        return {"image": path}
    if ctype in ("text/javascript", "application/javascript", "text/css") or (
            ctype != "text/html" and _ext(final.split("?", 1)[0]) in CODE_EXTS):
        return {"error": "it is code, which personas never read"}
    if not (ctype.startswith("text/") or ctype in ("application/json", "application/xhtml+xml")):
        return {"error": "a %s file: personas read web pages, text documents and images" % (ctype or "unknown")}
    body = data[:LINK_BYTES].decode(charset, errors="replace")
    if ctype in ("text/html", "application/xhtml+xml"):
        p = _PageText()
        try:
            p.feed(body)
            p.close()
        except Exception:
            pass
        body = p.text()
    body = body.strip()
    if not body:
        return {"error": "the page has no readable text"}
    return {"text": body}


def knowledge_bundle(root, entries, links=None, scratch=None):
    """(text, image_paths, notes) for what a persona was granted: project
    files and folders, and references, whose links are opened fresh (`links`
    holds the ones a critique run already opened). Documents only; code is
    refused even inside a granted folder."""
    root_real = os.path.realpath(root)
    files, linked, notes = [], [], []
    for ent in resolve_entries(root, entries):
        if "missing" in ent:
            notes.append("%s, skipped" % ent["missing"])
            continue
        if "link" in ent:
            linked.append(ent)
            continue
        c = ent["path"]
        absolute = os.path.realpath(os.path.join(root, c))
        if absolute != root_real and not absolute.startswith(root_real + os.sep):
            notes.append("%s: outside the project, skipped" % c)
            continue
        if os.path.isdir(absolute):
            found = 0
            for dirpath, dirnames, filenames in os.walk(absolute):
                dirnames[:] = sorted(d for d in dirnames if not d.startswith(".") and d not in SKIP_DIRS)
                for name in sorted(filenames):
                    if name.startswith("."):
                        continue
                    files.append(os.path.join(dirpath, name))
                    found += 1
                    if found > 200:
                        break
                if found > 200:
                    notes.append("%s: more than 200 files, the rest skipped" % c)
                    break
        elif os.path.isfile(absolute):
            files.append(absolute)
        else:
            notes.append("%s: not found" % c)
    text_parts, images, used = [], [], 0
    code_skipped = 0

    def add_text(title, chunk):
        nonlocal used
        cut = len(chunk) > KNOW_FILE_CAP
        chunk = chunk[:min(KNOW_FILE_CAP, KNOW_TOTAL_CAP - used)]
        used += len(chunk)
        text_parts.append("#### %s\n%s%s" % (title, chunk, "\n[... cut short]" if cut else ""))

    for path in files:
        ext = _ext(path)
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        if ext in CODE_EXTS:
            code_skipped += 1
            continue
        if ext in IMAGE_EXTS:
            try:
                if len(images) < KNOW_IMAGES and os.path.getsize(path) <= KNOW_IMAGE_BYTES:
                    images.append(path)
                else:
                    notes.append("%s: image skipped (limit %d images, 3 MB each)" % (rel, KNOW_IMAGES))
            except OSError:
                pass
            continue
        if ext not in DOC_EXTS:
            notes.append("%s: not a document type the personas read, skipped" % rel)
            continue
        if used >= KNOW_TOTAL_CAP:
            notes.append("%s: skipped, the knowledge budget is spent" % rel)
            continue
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                chunk = f.read(KNOW_FILE_CAP + 1)
        except OSError:
            continue
        # The title is the document's own name, never its folder path: a path
        # tells the persona how the project is built.
        add_text(os.path.splitext(os.path.basename(path))[0].replace("-", " ").replace("_", " "), chunk)
    for ent in linked:
        got = (links or {}).get(ent["link"])
        if got is None:
            got = fetch_link(ent["link"], scratch or os.path.join(critiques_dir(root), "_links"))
        if got.get("error"):
            notes.append("%s: %s" % (ent["name"], got["error"]))
        elif got.get("image"):
            if len(images) < KNOW_IMAGES:
                images.append(got["image"])
            else:
                notes.append("%s: image skipped (limit %d images)" % (ent["name"], KNOW_IMAGES))
        elif used >= KNOW_TOTAL_CAP:
            notes.append("%s: skipped, the knowledge budget is spent" % ent["name"])
        else:
            # A reference is titled by its own name, never its address.
            add_text(ent["name"], got.get("text") or "")
    if code_skipped:
        notes.append("%d code file%s in granted folders skipped (personas never read code)"
                     % (code_skipped, "" if code_skipped == 1 else "s"))
    return "\n\n".join(text_parts), images, notes


def fetch_links(root, persona_rows, scratch, walker):
    """Open every link the chosen personas use, once per critique run, so
    two personas sharing a reference cost one fetch. What they know reads a
    link as text; Taste keeps an image link as it is and screenshots any
    other page, since how it LOOKS is the point. Returns (know, taste), each
    {url: fetch_link result}."""
    know, taste = [], []
    for p in persona_rows:
        for key, acc in (("knowledge", know), ("taste", taste)):
            for ent in resolve_entries(root, p.get(key)):
                if "link" in ent and ent["link"] not in acc:
                    acc.append(ent["link"])
    if not know and not taste:
        return {}, {}
    both = know + [u for u in taste if u not in know]
    with ThreadPoolExecutor(max_workers=min(LINK_WORKERS, len(both))) as ex:
        got = dict(zip(both, ex.map(lambda u: fetch_link(u, scratch), both)))
    know_res = {u: got[u] for u in know}
    taste_res, pages = {}, []
    for u in taste:
        if got[u].get("image"):
            taste_res[u] = got[u]
        elif "sign-in" in (got[u].get("error") or ""):
            taste_res[u] = got[u]
        else:
            pages.append({"key": "T%d" % (len(pages) + 1), "url": u})
    if pages:
        shots_dir = os.path.join(scratch, "taste")
        os.makedirs(shots_dir, exist_ok=True)
        plan = os.path.join(shots_dir, "pages.json")
        with open(plan, "w", encoding="utf-8") as f:
            json.dump({"pages": pages}, f)
        res = walker(["survey", "--plan", plan, "--out", shots_dir, "--device", "desktop"]) or {}
        try:
            with open(os.path.join(shots_dir, "survey.json"), "r", encoding="utf-8") as f:
                shot_pages = {sp.get("key"): sp for sp in (json.load(f).get("pages") or [])}
        except (OSError, ValueError):
            shot_pages = {}
        for pg in pages:
            sp = shot_pages.get(pg["key"]) or {}
            shot = os.path.join(shots_dir, sp.get("shot") or "")
            if sp.get("shot") and os.path.isfile(shot):
                taste_res[pg["url"]] = {"image": shot}
            else:
                taste_res[pg["url"]] = {"error": "could not take a picture of the page (%s)" % _short(
                    sp.get("error") or res.get("error") or "the browser opened nothing", 120)}
    return know_res, taste_res


# ── prompts ───────────────────────────────────────────────────────────────

PLANNER_SYSTEM = """You plan a short usability session for user research. You answer with ONE JSON object and nothing else: no prose, no code fence.

Words: plain words a person using the product would use. Never mention code, files, pages' file names, selectors, classes, components, settings keys or how anything is built. Every field is a short phrase, at most 12 words. No paragraphs.

JSON shape:
{"summary": ["<what changed, as a user sees it>"],
 "tasks": [{"goal": "<what the participant tries to do>", "do": "open|click|fill|select|press|scroll|look", "page": "<page key, for open>", "target": "<exact visible label>", "value": "<text to type, option to pick, or key>", "lookFor": "<what to notice>"}]}

summary: 1 to 3 items.
tasks (only when asked to plan tasks): 2 to %d items, in order, the shortest path a real participant takes to meet the change and judge it. The first task is "open" on the start page.
- "target" is copied exactly from the page's list of labels. Labels marked (appears later) are not on screen at first: they show up after an earlier step, such as a button that reveals a form.
- Act the way a person does: click the on-screen button rather than pressing a key; for "select", "value" is one of the listed options, copied exactly; type realistic values.
- "goal" uses the screen's own words and adds no facts the page does not state.
- "look" (no target) stops to judge a screen; "scroll" moves down a long screen.""" % MAX_TASKS

PERSONA_RULES = """You are a simulated participant in a usability study. Stay in character: think, feel, judge and word things the way this person would, with their goals, frustrations, habits and comfort with technology.

What you know is ONLY:
- your profile below,
- the documents under "What you know" (when there are any),
- what you are shown in this session: the description of what changed and, when there are screens, the screens.
You have never seen how the product is built and you never think about code, files or implementation. If something is not in your profile, your documents or on screen, you do not know it: say so rather than invent it."""

PERSONA_OUTPUT = """Answer with ONE JSON object and nothing else (no prose, no code fence):
{"steps": [{"n": <step number>, "feel": "fine|unsure|stuck|pleased", "thought": "<your first-person reaction, one sentence>"}],
 "verdict": "<one sentence, in your voice>",
 "suggestions": [{"title": "<short imperative>", "why": "<one sentence, tied to who you are>", "priority": "high|medium|low", "step": <step number or null>}]}
"steps" has one entry per step shown (empty when there are no steps). At most %d suggestions, most important first; each one concrete enough to act on. Only suggest what this person would actually care about.""" % MAX_SUGGESTIONS

def persona_system(p):
    text = profile_clean(p.get("profile") or _legacy_profile(p))
    device = p.get("device") or profile_device(text)
    return "\n".join([PERSONA_RULES, "", "## Your profile", "You are the person this profile describes.", "",
                      text, "", "## Device you are using", "a phone" if device == "mobile" else "a computer"])


def taste_images(root, p, links=None):
    """(image paths, notes): the persona's taste, at most MAX_TASTE images -
    uploads, project images, the images inside a project folder, and
    references (`links` holds what fetch_links made of a link: the image, or
    a screenshot of the page)."""
    root_real = os.path.realpath(root)
    out, notes = [], []

    def add(path):
        if path not in out:
            out.append(path)

    for ent in resolve_entries(root, p.get("taste")):
        if len(out) >= MAX_TASTE:
            notes.append("taste: more than %d images, the rest skipped" % MAX_TASTE)
            break
        if "missing" in ent:
            notes.append("taste: %s, skipped" % ent["missing"])
            continue
        if "link" in ent:
            got = (links or {}).get(ent["link"]) or {"error": "not opened"}
            if got.get("image"):
                add(got["image"])
            else:
                notes.append("taste, %s: %s" % (ent["name"], got.get("error") or "no picture of it"))
            continue
        absolute = os.path.realpath(os.path.join(root, ent["path"]))
        if absolute != root_real and not absolute.startswith(root_real + os.sep):
            notes.append("taste, %s: outside the project, skipped" % ent["path"])
        elif os.path.isdir(absolute):
            for dirpath, dirnames, filenames in os.walk(absolute):
                dirnames[:] = sorted(d for d in dirnames if not d.startswith(".") and d not in SKIP_DIRS)
                for name in sorted(filenames):
                    if len(out) >= MAX_TASTE:
                        break
                    path = os.path.join(dirpath, name)
                    try:
                        if _ext(name) in IMAGE_EXTS and not name.startswith(".") and os.path.getsize(path) <= TASTE_BYTES:
                            add(path)
                    except OSError:
                        pass
                if len(out) >= MAX_TASTE:
                    break
        elif os.path.isfile(absolute):
            if _ext(absolute) in IMAGE_EXTS:
                add(absolute)
            else:
                notes.append("taste, %s: not an image, skipped" % ent["name"])
        else:
            notes.append("taste, %s: not found" % ent["name"])
    return out[:MAX_TASTE], notes


def strip_json(text):
    """The first JSON object in a model reply, parsed, or None."""
    if not isinstance(text, str):
        return None
    t = text.strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t)
    start = t.find("{")
    if start < 0:
        return None
    depth, in_str, esc = 0, False, False
    for i in range(start, len(t)):
        ch = t[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    v = json.loads(t[start:i + 1])
                    return v if isinstance(v, dict) else None
                except ValueError:
                    return None
    return None


_DASH_RE = re.compile(r"\s*[\u2013\u2014]\s*")


def _short(v, n=160):
    """A model-written field, trimmed, with no em or en dash (house rule)."""
    return _DASH_RE.sub(" - ", v).strip()[:n] if isinstance(v, str) else ""


def parse_plan(text, page_keys, simulate):
    doc = strip_json(text) or {}
    summary = [_short(s, 200) for s in (doc.get("summary") or []) if _short(s)][:3]
    tasks = []
    if simulate:
        for t in (doc.get("tasks") or [])[:MAX_TASKS]:
            if not isinstance(t, dict):
                continue
            do = t.get("do") if t.get("do") in ("open", "click", "fill", "select", "press", "scroll", "look") else "look"
            task = {"goal": _short(t.get("goal"), 120), "do": do,
                    "target": _short(t.get("target"), 100), "value": _short(t.get("value"), 120),
                    "lookFor": _short(t.get("lookFor"), 120)}
            if do == "open":
                task["page"] = t.get("page") if t.get("page") in page_keys else (page_keys[0] if page_keys else "")
            tasks.append(task)
        if page_keys and (not tasks or tasks[0]["do"] != "open"):
            tasks.insert(0, {"goal": "Arrive on the start screen", "do": "open", "page": page_keys[0],
                             "target": "", "value": "", "lookFor": "first impression"})
        tasks = tasks[:MAX_TASKS]
    return summary, tasks


def parse_critique(text, n_steps):
    doc = strip_json(text)
    if not doc:
        raise ValueError("the persona did not answer in the expected form")
    steps = []
    for s in doc.get("steps") or []:
        if isinstance(s, dict) and isinstance(s.get("n"), int) and 1 <= s["n"] <= max(n_steps, 0):
            steps.append({"n": s["n"],
                          "feel": s.get("feel") if s.get("feel") in ("fine", "unsure", "stuck", "pleased") else "fine",
                          "thought": _short(s.get("thought"), 300)})
    sugg = []
    for s in (doc.get("suggestions") or [])[:MAX_SUGGESTIONS]:
        if isinstance(s, dict) and _short(s.get("title")):
            step = s.get("step") if isinstance(s.get("step"), int) and 1 <= s["step"] <= max(n_steps, 0) else None
            sugg.append({"title": _short(s.get("title"), 140), "why": _short(s.get("why"), 300),
                         "priority": s.get("priority") if s.get("priority") in ("high", "medium", "low") else "medium",
                         "step": step})
    return {"steps": steps, "verdict": _short(doc.get("verdict"), 300), "suggestions": sugg}


def action_line(t):
    do = t.get("do")
    if do == "open":
        return "Open the start screen" if t.get("page") in ("P1", "", None) else "Open screen " + str(t.get("page"))[1:]
    if do == "click":
        return 'Click "%s"' % t.get("target")
    if do == "fill":
        return 'Type "%s" into "%s"' % (t.get("value"), t.get("target"))
    if do == "select":
        return 'Choose "%s" in "%s"' % (t.get("value"), t.get("target"))
    if do == "press":
        return "Press " + (t.get("value") or "Enter")
    if do == "scroll":
        return "Scroll down" + ((' to "%s"' % t["target"]) if t.get("target") else "")
    return "Look at the screen"


# ── the critique job ──────────────────────────────────────────────────────

_JOBS = {}          # id -> {"report": dict, "done": Event, "root": str}
_JOBS_LOCK = threading.Lock()


def _report_path(root, cid):
    return os.path.join(critiques_dir(root), cid, "report.json")


def save_report(root, report):
    d = os.path.join(critiques_dir(root), report["id"])
    os.makedirs(d, exist_ok=True)
    tmp = os.path.join(d, "report.json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1, ensure_ascii=False)
    os.replace(tmp, os.path.join(d, "report.json"))


def get_report(root, cid):
    if not CRITIQUE_ID_RE.match(cid or ""):
        return None
    with _JOBS_LOCK:
        job = _JOBS.get(cid)
    if job and job["root"] == root:
        return json.loads(json.dumps(job["report"]))
    try:
        with open(_report_path(root, cid), "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def wait(cid, seconds):
    with _JOBS_LOCK:
        job = _JOBS.get(cid)
    if job:
        job["done"].wait(max(0.0, min(float(seconds), 590.0)))


def shot_path(root, cid, name):
    if not CRITIQUE_ID_RE.match(cid or "") or not re.match(r"^[a-z]+-\d{1,2}\.jpg$|^survey-P\d\.jpg$", name or ""):
        return None
    p = os.path.join(critiques_dir(root), cid, name)
    return p if os.path.isfile(p) else None


def digest(report):
    """The text the calling agent receives: suggestions to relay, no images."""
    if report.get("status") not in ("done", "error"):
        return ('PERSONA CRITIQUE %s: "status": "running" (%s). Poll again.'
                % (report.get("id"), report.get("stage") or "working"))
    lines = ["PERSONA CRITIQUE %s (%s) - suggestions only, change nothing on their account."
             % (report["id"], "simulated on the pages" if report.get("how") == "simulate" else "as text")]
    if report.get("status") == "error":
        lines.append("FAILED: " + (report.get("error") or "unknown error"))
    if report.get("tasks"):
        lines.append("Tasks: " + "; ".join("%d. %s" % (i + 1, t.get("goal") or action_line(t))
                                            for i, t in enumerate(report["tasks"])))
    for walk in (report.get("walks") or {}).values():
        stuck = [s for s in walk.get("steps") or [] if not s.get("ok")]
        for s in stuck:
            lines.append("Step %d could not be done on %s: %s" % (s["n"], walk.get("device"), s.get("error") or "failed"))
    for p in report.get("personas") or []:
        head = "%s%s" % (p.get("name"), (" (" + p["role"] + ")") if p.get("role") else "")
        if p.get("status") != "done":
            lines.append("%s: no critique (%s)" % (head, p.get("error") or p.get("status")))
            continue
        lines.append("%s - %s" % (head, p.get("verdict") or "no verdict"))
        for s in p.get("suggestions") or []:
            lines.append("  - [%s] %s: %s%s" % (s.get("priority"), s.get("title"), s.get("why"),
                                               (" (step %d)" % s["step"]) if s.get("step") else ""))
    lines.append('The thread already shows the full critique as a card: relay the suggestions as a short merged list, '
                 'naming who raised each.')
    return "\n".join(lines)


def start(root, project_id, run_id, persona_rows, req, deps):
    """Create the job and run it on a thread. Returns the report id."""
    cid = "c_" + secrets.token_hex(5)
    report = {
        "id": cid, "project": project_id, "run": run_id, "createdAt": int(time.time() * 1000),
        "how": req["how"], "status": "running", "stage": "planning",
        "summary": [], "tasks": [], "walks": {}, "notes": [],
        "personas": [{"id": p["id"], "name": p.get("name"), "role": p.get("role"),
                      "device": p.get("device") or "desktop", "status": "waiting"} for p in persona_rows],
    }
    job = {"report": report, "done": threading.Event(), "root": root}
    with _JOBS_LOCK:
        _JOBS[cid] = job
    save_report(root, report)
    threading.Thread(target=_run, args=(job, persona_rows, req, deps), daemon=True,
                     name="persona-critique-" + cid).start()
    return cid


def _update(job, deps, **fields):
    with _JOBS_LOCK:
        job["report"].update(fields)
        snap = json.loads(json.dumps(job["report"]))
    try:
        save_report(job["root"], snap)
    except OSError:
        pass
    emit = deps.get("emit")
    if emit:
        try:
            emit({"type": "persona_critique", "id": snap["id"], "status": snap["status"],
                  "stage": snap.get("stage"), "how": snap.get("how"),
                  "personas": [{"name": p.get("name"), "status": p.get("status")} for p in snap["personas"]]})
        except Exception:
            pass


def _set_persona(job, pid, **fields):
    with _JOBS_LOCK:
        for p in job["report"]["personas"]:
            if p["id"] == pid:
                p.update(fields)


def _walk(job, deps, out_dir, pages, tasks, device):
    plan_path = os.path.join(out_dir, "plan-%s.json" % device)
    with open(plan_path, "w", encoding="utf-8") as f:
        json.dump({"pages": pages, "tasks": tasks}, f)
    res = deps["walker"](["walk", "--plan", plan_path, "--out", out_dir, "--device", device])
    try:
        with open(os.path.join(out_dir, "walk-%s.json" % device), "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"device": device, "steps": [], "error": (res or {}).get("error") or "the browser walk produced nothing"}


def _run(job, persona_rows, req, deps):
    started = time.time()
    root = job["root"]
    report = job["report"]
    out_dir = os.path.join(critiques_dir(root), report["id"])
    simulate = req["how"] == "simulate"
    try:
        _update(job, deps, stage="planning")
        # 1. Resolve and survey the pages (simulate only).
        pages, survey = [], {}
        if simulate:
            for i, raw in enumerate(req.get("pages") or []):
                try:
                    pages.append({"key": "P%d" % (i + 1), "url": deps["resolve_page"](raw)})
                except Exception as e:
                    report["notes"].append("page %r: %s" % (raw, e))
            if not pages:
                raise RuntimeError("no page to open: pass pages (a prototype slug or a path under source/)")
            pages_path = os.path.join(out_dir, "pages.json")
            with open(pages_path, "w", encoding="utf-8") as f:
                json.dump({"pages": pages}, f)
            res = deps["walker"](["survey", "--plan", pages_path, "--out", out_dir, "--device", "desktop"])
            try:
                with open(os.path.join(out_dir, "survey.json"), "r", encoding="utf-8") as f:
                    survey = json.load(f)
            except (OSError, ValueError):
                raise RuntimeError("could not open the pages in a browser: %s" % ((res or {}).get("error") or "no survey"))
        # 2. The fast planner: the change in a user's words (+ the task table).
        blocks = [{"type": "text", "text": "What the builder says changed (it may use technical words; translate them):\n"
                   + (req.get("change") or "")}]
        if simulate:
            if req.get("flow"):
                blocks.append({"type": "text", "text": "The path a user takes, as the builder describes it: " + req["flow"]})
            for sp in survey.get("pages") or []:
                inv = "\n".join("- %s: %s%s%s" % (it.get("role"), it.get("name"),
                                                   (" (options: " + ", ".join(it["options"]) + ")") if it.get("options") else "",
                                                   " (appears later)" if it.get("later") else "")
                                for it in (sp.get("inventory") or [])[:80])
                blocks.append({"type": "text", "text": "Page %s%s. Visible labels:\n%s" % (
                    sp.get("key"), (' "' + sp["title"] + '"') if sp.get("title") else "", inv or "(none found)")})
                shot = os.path.join(out_dir, sp.get("shot") or "")
                if sp.get("shot") and os.path.isfile(shot):
                    blocks.append({"type": "image", "path": shot})
            blocks.append({"type": "text", "text": "Plan the tasks (start page is P1). Answer with the JSON object only."})
        else:
            blocks.append({"type": "text", "text": "Write only the summary (no tasks). Answer with the JSON object only."})
        plan_text = deps["fast_complete"](PLANNER_SYSTEM, blocks)
        summary, tasks = parse_plan(plan_text, [p["key"] for p in pages], simulate)
        if not summary:
            summary = [_short(req.get("change"), 200)] if not simulate else ["(the planner wrote no summary)"]
        if simulate and len(tasks) < 1:
            raise RuntimeError("the planner returned no tasks")
        _update(job, deps, summary=summary, tasks=tasks, stage="walking" if simulate else "critiquing")
        # 3. Walk the plan once per device the chosen personas use.
        walks = {}
        if simulate:
            devices = sorted({p.get("device") or "desktop" for p in persona_rows})
            with ThreadPoolExecutor(max_workers=len(devices)) as ex:
                futs = {d: ex.submit(_walk, job, deps, out_dir, pages, tasks, d) for d in devices}
                for d, fut in futs.items():
                    walks[d] = fut.result()
            _update(job, deps, walks=walks, stage="critiquing")
        # 4. Every persona, isolated and in parallel. Links among their
        # references are opened first, once for all of them.
        links_dir = os.path.join(out_dir, "links")
        know_links, taste_links = fetch_links(root, persona_rows, links_dir, deps["walker"])

        def one(p):
            _set_persona(job, p["id"], status="running")
            _update(job, deps)
            try:
                know_text, know_images, know_notes = knowledge_bundle(root, p.get("knowledge"), know_links, links_dir)
                content = []
                if know_text or know_images:
                    content.append({"type": "text", "text": "## What you know\n" + (know_text or "(images only)")})
                    for img in know_images:
                        content.append({"type": "image", "path": img})
                taste, taste_notes = taste_images(root, p, taste_links)
                know_notes = know_notes + taste_notes
                if taste:
                    content.append({"type": "text", "text": "## Your taste\nThese images show apps, styles and "
                                    "products you like and feel at home with. They shape what feels right or off "
                                    "to you; you do not talk about them as pictures, you simply have this taste."})
                    for img in taste:
                        content.append({"type": "image", "path": img})
                content.append({"type": "text", "text": "## What changed in the product\n"
                                + "\n".join("- " + s for s in summary)})
                steps = []
                if simulate:
                    walk = walks.get(p.get("device") or "desktop") or {}
                    steps = walk.get("steps") or []
                    # What to look for stays with the team (it is the card's
                    # table): a moderator never tells the participant what
                    # they are supposed to notice.
                    content.append({"type": "text", "text": "## Your session\nYou try the product yourself, step by step. "
                                    "Each step says what you set out to do and what happened, then shows the screen you saw."})
                    by_n = {s.get("n"): s for s in steps}
                    for i, t in enumerate(tasks):
                        n = i + 1
                        s = by_n.get(n) or {}
                        did = action_line(t)
                        result = "done" if s.get("ok") else ("you could not: " + (s.get("error") or "nothing happened"))
                        content.append({"type": "text", "text": "### Step %d - %s\nYou: %s. Result: %s." % (
                            n, t.get("goal") or did, did, result)})
                        shot = os.path.join(out_dir, s.get("shot") or "")
                        if s.get("shot") and os.path.isfile(shot):
                            content.append({"type": "image", "path": shot})
                else:
                    content.append({"type": "text", "text": "There are no screens to try: judge the change from its description."})
                content.append({"type": "text", "text": PERSONA_OUTPUT})
                text = deps["persona_complete"](persona_system(p), content)
                out = parse_critique(text, len(tasks) if simulate else 0)
                _set_persona(job, p["id"], status="done", notes=know_notes, **out)
            except Exception as e:
                _set_persona(job, p["id"], status="error", error=str(e)[:300])
            _update(job, deps)
        with ThreadPoolExecutor(max_workers=min(PERSONA_WORKERS, max(1, len(persona_rows)))) as ex:
            list(ex.map(one, persona_rows))
        ok = any(p.get("status") == "done" for p in report["personas"])
        _update(job, deps, status="done" if ok else "error", stage="done",
                error=None if ok else "no persona answered",
                durationMs=int((time.time() - started) * 1000))
    except Exception as e:
        _update(job, deps, status="error", stage="done", error=str(e)[:400],
                durationMs=int((time.time() - started) * 1000))
    finally:
        job["done"].set()
        # Keep finished jobs reachable from disk only.
        def _forget():
            time.sleep(600)
            with _JOBS_LOCK:
                _JOBS.pop(report["id"], None)
        threading.Thread(target=_forget, daemon=True).start()


# ── research draft (fills the profile form from granted documents) ────────

DRAFT_SYSTEM = """You turn research into one user persona for a product team. Answer with the persona as markdown and nothing else: no code fence, no preamble.
- First line: "# " and a realistic first name and last initial.
- Second line: who they are, in one line.
- Then short "## " sections with "- " bullets: About, Goals, Frustrations, Habits and context.
- Then the lines "Comfort with tech: low|medium|high" and "Device: phone|computer".
- Last: one line they might say, as "> ".
Use only what the research supports; where it is silent, leave the section out rather than invent. Plain words, short lines, no paragraphs."""


def draft_blocks(root, paths, notes_text, hint, scratch=None):
    """The draft call's blocks; a linked image lands in `scratch`, which the
    caller removes once the call is done."""
    know_text, images, notes = knowledge_bundle(root, paths, None, scratch)
    blocks = []
    if hint:
        blocks.append({"type": "text", "text": "The team's current draft (keep what the research does not contradict):\n" + hint})
    if notes_text:
        blocks.append({"type": "text", "text": "Research notes pasted by the team:\n" + notes_text[:KNOW_TOTAL_CAP]})
    if know_text:
        blocks.append({"type": "text", "text": "Research documents:\n" + know_text})
    for img in images:
        blocks.append({"type": "image", "path": img})
    blocks.append({"type": "text", "text": "Answer with the persona in markdown only."})
    return blocks, notes, bool(know_text or images or notes_text)


def parse_draft(text):
    t = (text or "").strip()
    t = re.sub(r"^```(?:markdown|md)?\s*|\s*```$", "", t).strip()
    return {"profile": _DASH_RE.sub(" - ", t)[:PROFILE_CAP]}


# ── walker subprocess (tools/qa/persona_walk.py) ──────────────────────────

def run_walker(install_root, args, timeout=240):
    tool = os.path.join(install_root, "editor", "tools", "qa", "persona_walk.py")
    if not os.path.isfile(tool):
        return {"error": "persona_walk.py is missing"}
    try:
        r = subprocess.run([sys.executable, tool] + list(args), capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"error": "the browser walk timed out"}
    if r.returncode != 0:
        return {"error": (r.stderr or "exit %d" % r.returncode).strip()[-400:]}
    return {}

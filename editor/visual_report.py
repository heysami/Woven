"""The Visual QA report: one page per /__qa/run that asked typed visual checks.

Every judge call with its images exactly as they were sent, every question
with its answer, probabilities, confidence and band, and each screenshot with
the crop boxes drawn on it, so a "sure no" can be found and looked at. The
daemon saves the run here and serves the page and its images; nothing in it
is ever sent into a thread (a thread gets one line and the link).
"""

import copy
import html
import json
import os
import re
import secrets
import shutil
import time
import urllib.parse
from typing import Any, Dict, List, Optional

REPORTS_DIR = os.path.expanduser("~/.test-harness/visual-qa")
KEEP = 60
CROP_PAD = 8  # visual_qa._CROP_PAD: a crop is its element's box plus this, in CSS px
ID_RE = re.compile(r"^\d{8}-\d{6}-[0-9a-f]{6}$")
FILE_RE = re.compile(r"^[\w.-]{1,160}\.(png|jpg|jpeg|webp)$")
BLANK_SHARE = 0.97


def _size(path):
    # type: (str) -> List[int]
    try:
        import typed_judge
        with open(path, "rb") as f:
            data = f.read(1 << 20)
        kind = typed_judge.sniff_image(data)
        wh = typed_judge.image_size(data, kind) if kind else None
        return [int(wh[0]), int(wh[1])] if wh else [0, 0]
    except Exception:
        return [0, 0]


def save(report, out_dir, project=None, page=None, root=None):
    # type: (Dict[str, Any], str, Optional[str], Optional[str], Optional[str]) -> Optional[str]
    """Copy one run's typed checks and the images they used out of the QA
    temp dir; returns the report id, or None when the run asked nothing."""
    block = report.get("typedChecks")
    if not isinstance(block, dict) or not (block.get("checks") or block.get("rejected")):
        return None
    root = root or REPORTS_DIR
    rid = time.strftime("%Y%m%d-%H%M%S") + "-" + secrets.token_hex(3)
    dest = os.path.join(root, rid)
    os.makedirs(dest, exist_ok=True)
    out_real = os.path.realpath(out_dir)
    names = {}  # type: Dict[str, str]
    sizes = {}  # type: Dict[str, List[int]]

    def keep(path):
        # type: (Optional[str]) -> Optional[str]
        if not path:
            return None
        real = os.path.realpath(path)
        if not real.startswith(out_real + os.sep) or not os.path.isfile(real):
            return None
        if real not in names:
            base = os.path.basename(real)
            if not FILE_RE.match(base) or base in names.values():
                base = "img_%d.png" % len(names)
            shutil.copyfile(real, os.path.join(dest, base))
            names[real] = base
            sizes[base] = _size(real)
        return names[real]

    block = copy.deepcopy(block)
    for call in block.get("calls") or []:
        for im in call.get("images") or []:
            im["file"] = keep(im.pop("path", None))
            im["captureFile"] = keep(im.pop("capture", None))
    block["pageShotFile"] = keep(block.pop("pageShot", None))
    cs = report.get("casesSummary") or {}
    data = {
        "id": rid, "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "project": project, "page": page or report.get("page"), "url": report.get("url"),
        "verdict": report.get("verdict"), "mode": report.get("mode"),
        "cases": {"pass": cs.get("pass", 0), "total": cs.get("total", 0)} if cs else None,
        "reasons": [str(r) for r in (report.get("reasons") or [])[:10]],
        "sizes": sizes, "typedChecks": block,
    }
    with open(os.path.join(dest, "report.json"), "w", encoding="utf-8") as f:
        json.dump(data, f)
    prune(root)
    return rid


def prune(root=None, keep=KEEP):
    # type: (Optional[str], int) -> None
    root = root or REPORTS_DIR
    try:
        ids = sorted(d for d in os.listdir(root) if ID_RE.match(d))
    except OSError:
        return
    for d in ids[:-keep] if len(ids) > keep else []:
        shutil.rmtree(os.path.join(root, d), ignore_errors=True)


def load(rid, root=None):
    # type: (str, Optional[str]) -> Optional[Dict[str, Any]]
    if not ID_RE.match(rid or ""):
        return None
    try:
        with open(os.path.join(root or REPORTS_DIR, rid, "report.json"), "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def file_path(rid, name, root=None):
    # type: (str, str, Optional[str]) -> Optional[str]
    if not ID_RE.match(rid or "") or not FILE_RE.match(name or ""):
        return None
    path = os.path.join(root or REPORTS_DIR, rid, name)
    return path if os.path.isfile(path) else None


# ── Reading a row ───────────────────────────────────────────────────────────

def outcome(row):
    # type: (Dict[str, Any]) -> str
    """sure-no / sure-yes / unsure / answered / not-asked."""
    if row.get("status") != "answered":
        return "not-asked"
    if row.get("band") != "act":
        return "unsure"
    if row.get("passed") is False:
        return "sure-no"
    if row.get("passed") is True:
        return "sure-yes"
    return "answered"


OUTCOME_LABEL = {"sure-no": "Sure no", "sure-yes": "Sure yes", "unsure": "Unsure",
                 "answered": "Answered", "not-asked": "Not asked"}
STATUS_WHY = {"no-capture": "No screenshot of that name in this run.",
              "element-missing": "The element was not on the page, so there was nothing to crop.",
              "not-visible": "The element was hidden at that moment (optional check, not a failure).",
              "unavailable": "The judge did not answer.",
              "no-answer": "The judge answered without a usable value."}


def summary_line(block):
    # type: (Dict[str, Any]) -> str
    rows = block.get("checks") or []
    counts = {}  # type: Dict[str, int]
    for r in rows:
        k = outcome(r)
        counts[k] = counts.get(k, 0) + 1
    parts = ["%d %s" % (counts[k], OUTCOME_LABEL[k].lower())
             for k in ("sure-no", "sure-yes", "unsure", "answered", "not-asked") if counts.get(k)]
    return ", ".join(parts) or "no checks"


def _fmt(v, nd=2):
    # type: (Any, int) -> str
    if v is None:
        return "-"
    try:
        return ("%." + str(nd) + "f") % float(v)
    except (TypeError, ValueError):
        return str(v)


def answer_text(row):
    # type: (Dict[str, Any]) -> str
    q = row.get("question") or {}
    if q.get("type") == "choice":
        return str(row.get("answer")) if row.get("answer") is not None else "-"
    n = row.get("noul")
    if n is None:
        return "-"
    # A noul is "yes" at its kind's threshold, which is what `passed` records.
    return "%s (true %s)" % ("yes" if row.get("passed") else "no", _fmt(n, 3))


def text_table(data):
    # type: (Dict[str, Any]) -> str
    """The same report as plain text, for the task's Result pane."""
    block = data.get("typedChecks") or {}
    lines = []
    calls = {c.get("n"): c for c in block.get("calls") or []}
    order = {"sure-no": 0, "unsure": 1, "answered": 2, "sure-yes": 3, "not-asked": 4}
    for r in sorted(block.get("checks") or [], key=lambda r: order.get(outcome(r), 9)):
        call = calls.get(r.get("call")) or {}
        imgs = "; ".join(i.get("label") or "" for i in call.get("images") or []) or ", ".join(r.get("images") or [])
        o = outcome(r)
        lines.append("%s  %s" % (OUTCOME_LABEL[o].upper(), r.get("id")))
        lines.append("  question: %s" % ((r.get("question") or {}).get("instructions") or r.get("claim") or ""))
        if r.get("expect"):
            lines.append("  expected: %s" % ", ".join(r["expect"]))
        if o == "not-asked":
            lines.append("  why: %s" % (r.get("message") or STATUS_WHY.get(r.get("status"), r.get("status"))))
        else:
            lines.append("  answer: %s  confidence: %s  band: %s" % (answer_text(r), _fmt(r.get("confidence")),
                                                                       r.get("band")))
            if r.get("probabilities"):
                lines.append("  probabilities: %s" % ", ".join(
                    "%s %s" % (k, _fmt(v)) for k, v in sorted(r["probabilities"].items(), key=lambda kv: -kv[1])))
        lines.append("  image: %s" % imgs)
        lines.append("  source: %s" % (r.get("source") or "screen criteria"))
    for rj in block.get("rejected") or []:
        lines.append("REJECTED  %s: %s (%s)" % (rj.get("id") or rj.get("index"), rj.get("statement") or "",
                                                 rj.get("reason")))
    return "\n".join(lines)


# ── The page ────────────────────────────────────────────────────────────────

_CSS = """
:root{--bg:#f7f7f5;--panel:#fff;--ink:#1d1d1b;--mute:#6b6b66;--line:#e2e1dc;--no:#b3261e;--yes:#2e7d32;--unsure:#8a6d00;--box:#e8590c}
@media (prefers-color-scheme: dark){:root{--bg:#161615;--panel:#1f1f1d;--ink:#ecebe6;--mute:#9b9a94;--line:#33332f;--no:#ff8a80;--yes:#81c784;--unsure:#e0c060;--box:#ff922b}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
main{max-width:1180px;margin:0 auto;padding:20px 16px 60px;overflow-wrap:break-word}
h1{font-size:18px;margin:0 0 4px}h2{font-size:15px;margin:28px 0 8px}h3{font-size:14px;margin:0}
.meta{color:var(--mute);font-size:12.5px}
.filters{display:flex;flex-wrap:wrap;gap:6px;margin:14px 0 4px}
.filters button{font:inherit;font-size:12.5px;background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:4px;padding:4px 10px;cursor:pointer}
.filters button[aria-pressed=true]{border-color:var(--ink)}
.note{color:var(--mute);font-size:12.5px;margin:6px 0 0}
.card{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:12px;margin:10px 0}
.card-h{display:flex;gap:10px;align-items:baseline;flex-wrap:wrap;margin-bottom:8px}
.sent{display:flex;gap:10px;flex-wrap:wrap;margin:6px 0}
.sent figure{margin:0;max-width:min(340px,100%)}
.sent img{display:block;max-width:100%;max-height:260px;min-width:48px;image-rendering:pixelated;border:1px solid var(--line);background:repeating-conic-gradient(#0001 0 25%,#0000 0 50%) 0/12px 12px}
figcaption{font-size:12px;color:var(--mute);margin-top:3px}
.warn{color:var(--no);font-size:12px}
pre{white-space:pre-wrap;font:12px/1.4 ui-monospace,Menlo,monospace;background:var(--bg);border:1px solid var(--line);border-radius:4px;padding:6px 8px;margin:6px 0}
.tw{overflow-x:auto}table{width:100%;min-width:720px;border-collapse:collapse;font-size:13px}td .meta{overflow-wrap:anywhere}
th,td{text-align:left;vertical-align:top;padding:6px 8px;border-top:1px solid var(--line)}
th{font-weight:600;color:var(--mute);font-size:12px}
td.o{white-space:nowrap;font-weight:600}
tr[data-o=sure-no] td.o{color:var(--no)}tr[data-o=sure-yes] td.o{color:var(--yes)}tr[data-o=unsure] td.o{color:var(--unsure)}
.opts{font-size:12px;color:var(--mute)}.opts b{color:var(--ink)}
.shot{position:relative;display:inline-block;max-width:100%}
.shot img{display:block;max-width:100%;border:1px solid var(--line)}
.shot .bx{position:absolute;border:2px solid var(--box);pointer-events:none}
.shot .bx span{position:absolute;left:-2px;top:-17px;background:var(--box);color:#fff;font-size:11px;line-height:15px;padding:0 4px;white-space:nowrap}.shot .bx.in span{left:0;top:0}@media (max-width:600px){.shot .bx{border-width:1px}.shot .bx span{font-size:9px;line-height:11px;padding:0 2px;top:-12px;left:-1px}.shot .bx.in span{top:0;left:0}}
.shotwrap{border:1px solid var(--line);border-radius:4px}
a{color:inherit}
.hidden{display:none}
"""

_JS = """
document.querySelectorAll('.filters button').forEach(b => b.addEventListener('click', () => {
  const want = b.dataset.f;
  document.querySelectorAll('.filters button').forEach(x => x.setAttribute('aria-pressed', x === b));
  document.querySelectorAll('tr[data-o]').forEach(tr => tr.classList.toggle('hidden', want !== 'all' && tr.dataset.o !== want));
  document.querySelectorAll('.card[data-call]').forEach(c => {
    const any = c.querySelector('tr[data-o]:not(.hidden)');
    c.classList.toggle('hidden', want !== 'all' && !any);
  });
  document.querySelectorAll('section[data-sec=rows]').forEach(sec =>
    sec.classList.toggle('hidden', want !== 'all' && !sec.querySelector('tr[data-o]:not(.hidden)')));
  document.querySelectorAll('section[data-sec=sureno]').forEach(sec =>
    sec.classList.toggle('hidden', want !== 'all' && want !== 'sure-no'));
}));
"""


def _e(v):
    # type: (Any) -> str
    return html.escape("" if v is None else str(v), quote=True)


def render(data, file_url):
    # type: (Dict[str, Any], Any) -> str
    """The report page. `file_url(name)` is the URL of one saved image."""
    block = data.get("typedChecks") or {}
    rows = block.get("checks") or []
    calls = block.get("calls") or []
    sizes = data.get("sizes") or {}
    counts = {}  # type: Dict[str, int]
    for r in rows:
        counts[outcome(r)] = counts.get(outcome(r), 0) + 1
    th = next((c.get("thresholds") for c in calls if c.get("thresholds")), None) or {}
    out = []  # type: List[str]
    w = out.append
    w("<!doctype html><html lang=en><head><meta charset=utf-8>"
      "<meta name=viewport content='width=device-width,initial-scale=1'>")
    w("<title>Visual QA report</title><style>%s</style></head><body><main>" % _CSS)
    w("<h1>Visual QA · %s</h1>" % _e(data.get("page")))
    bits = [_e(data.get("created"))]
    if data.get("project"):
        bits.append("project " + _e(data["project"]))
    if block.get("provider"):
        bits.append("judge " + _e(block["provider"]) + (" (" + _e(block.get("model")) + ")" if block.get("model") else ""))
    bits.append(("Shadow mode: answers are recorded only" if block.get("mode") == "shadow"
                 else "Flag mode: a sure no becomes a QA finding") if block.get("mode") else "")
    qa = "QA verdict " + _e(data.get("verdict"))
    if data.get("cases"):
        qa += " (%d/%d cases)" % (data["cases"]["pass"], data["cases"]["total"])
    bits.append(qa)
    w("<div class=meta>%s</div>" % " · ".join(b for b in bits if b))
    if data.get("url"):
        w("<div class=meta>%s</div>" % _e(data["url"]))
    w("<p class=note>%d question(s) in %d judge call(s). A call is one screenshot or crop with every "
      "question about it. An answer is <b>sure</b> when its confidence reaches %s; below that it is "
      "unsure and nothing acts on it. For a yes/no question, <i>true 0.011</i> is the judge's "
      "probability that the sentence is true, and confidence is how decisive that is (0.011 is a decisive no). "
      "None of this changes the QA verdict above.</p>"
      % (len(rows), len(calls), _fmt(th.get("high", 0.9))))
    w("<div class=filters role=group aria-label='Show'>")
    w("<button data-f=all aria-pressed=true>All (%d)</button>" % len(rows))
    for k in ("sure-no", "unsure", "sure-yes", "answered", "not-asked"):
        if counts.get(k):
            w("<button data-f=%s aria-pressed=false>%s (%d)</button>" % (k, OUTCOME_LABEL[k], counts[k]))
    w("</div>")

    # Sure no first: what failed, on which image, in one place.
    sure_no = [r for r in rows if outcome(r) == "sure-no"]
    if sure_no:
        w("<section data-sec=sureno><h2>Sure no</h2>")
        for r in sure_no:
            call = next((c for c in calls if c.get("n") == r.get("call")), {})
            w("<div class=card><div class=card-h><h3>%s</h3><span class=meta>confidence %s · "
              "<a href='#call-%s'>call %s</a></span></div>"
              % (_e(r.get("id")), _fmt(r.get("confidence")), _e(r.get("call")), _e(r.get("call"))))
            w("<div>%s</div>" % _e((r.get("question") or {}).get("instructions") or r.get("claim")))
            w("<div class=meta>judge said %s%s · %s</div>" % (
                _e(answer_text(r)), (" · expected " + _e(", ".join(r["expect"]))) if r.get("expect") else "",
                _e(r.get("source") or "screen criteria")))
            w(_sent(call, file_url))
            w("</div>")
        w("</section>")

    w("<section data-sec=rows><h2>Judge calls</h2>")
    for call in calls:
        w("<div class=card id='call-%s' data-call=%s><div class=card-h><h3>Call %s</h3>"
          "<span class=meta>%d question(s)%s%s</span></div>"
          % (_e(call.get("n")), _e(call.get("n")), _e(call.get("n")), len(call.get("questions") or []),
             (" · %.1f s" % (call["ms"] / 1000.0)) if call.get("ms") is not None else "",
             (" · " + _e(call.get("provider"))) if call.get("provider") else ""))
        w(_sent(call, file_url))
        w("<div class=meta>Text sent with the image(s):</div><pre>%s</pre>" % _e(call.get("state")))
        if call.get("error"):
            w("<div class=warn>The call failed: %s</div>" % _e(call["error"]))
        w(_table([r for r in rows if r.get("call") == call.get("n")]))
        w("</div>")
    w("</section>")

    not_asked = [r for r in rows if outcome(r) == "not-asked" and r.get("call") is None]
    if not_asked:
        w("<section data-sec=rows><h2>Not asked</h2><div class=card data-call=none>")
        w(_table(not_asked))
        w("</div></section>")
    if block.get("rejected"):
        w("<h2>Criteria refused before asking</h2><div class=card><table><tr><th>Check</th>"
          "<th>Written as</th><th>Why</th></tr>")
        for rj in block["rejected"]:
            w("<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (_e(rj.get("id") or rj.get("index")),
                                                              _e(rj.get("statement")), _e(rj.get("reason"))))
        w("</table></div>")

    # Every screenshot the calls cropped from, with the crop boxes drawn.
    shots = []  # type: List[str]
    for call in calls:
        for im in call.get("images") or []:
            if im.get("captureFile") and im["captureFile"] not in shots:
                shots.append(im["captureFile"])
    if block.get("pageShotFile") and block["pageShotFile"] not in shots:
        shots.insert(0, block["pageShotFile"])
    if shots:
        w("<h2>Screenshots</h2><p class=note>Each box is a crop the judge was shown, numbered by its call "
          "(the box includes the %d px padding around the element).</p>" % CROP_PAD)
    for name in shots:
        wh = sizes.get(name) or [0, 0]
        boxes = []
        for call in calls:
            for im in call.get("images") or []:
                if im.get("captureFile") == name and im.get("box") and wh[0] and wh[1]:
                    boxes.append((call.get("n"), im))
        w("<div class=card><div class=meta>%s · %d x %d px</div><div class=shotwrap><div class=shot>"
          "<img src='%s' alt=''>" % (_e(name), wh[0], wh[1], _e(file_url(name))))
        for n, im in boxes:
            b, vw = im["box"], float(im.get("viewportW") or wh[0])
            scale = wh[0] / vw if vw else 1.0
            # The crop's own rectangle (visual_qa._crop): box plus padding,
            # clamped to the image on every side.
            l = max(0.0, (b["x"] - CROP_PAD) * scale)
            t = max(0.0, (b["y"] - CROP_PAD) * scale)
            r = min(float(wh[0]), (b["x"] + b["width"] + CROP_PAD) * scale)
            btm = min(float(wh[1]), (b["y"] + b["height"] + CROP_PAD) * scale)
            if r <= l or btm <= t:
                continue
            w("<div class='bx%s' style='left:%.3f%%;top:%.3f%%;width:%.3f%%;height:%.3f%%'><span>%s</span></div>"
              % (" in" if t < 24 * scale else "", l / wh[0] * 100, t / wh[1] * 100,
                 (r - l) / wh[0] * 100, (btm - t) / wh[1] * 100, _e(n)))
        w("</div></div></div>")

    found = block.get("dsFound")
    if found:
        w("<h2>Found on the rendered page</h2><div class=card>")
        w("<div class=meta>Design-system components on screen (each compared with the gallery render):</div>")
        w("<pre>%s</pre>" % _e("\n".join("%s  .%s%s%s  at %s" % (
            c.get("title"), c.get("cls"), "".join("." + v for v in c.get("variant") or []),
            " (%s)" % ", ".join(c["state"]) if c.get("state") else "", c.get("selector"))
            for c in found.get("components") or []) or "none"))
        w("<div class=meta>Styled outside the design system (each asked ds-copy / new-ui / layout):</div>")
        w("<pre>%s</pre>" % _e("\n".join("%s  from %s  (%s)" % (u.get("selector"), u.get("source"),
                                                              ", ".join(u.get("skin") or []))
                                         for u in found.get("offSystem") or []) or "none"))
        w("</div>")
    w("<script>%s</script></main></body></html>" % _JS)
    return "".join(out)


def _bytes(n):
    # type: (int) -> str
    return "%d B" % n if n < 1024 else "%.1f KB" % (n / 1024.0) if n < 1 << 20 else "%.1f MB" % (n / 1048576.0)


def _sent(call, file_url):
    # type: (Dict[str, Any], Any) -> str
    parts = ["<div class=sent>"]
    for i, im in enumerate(call.get("images") or []):
        cap = "image %d: %s" % (i + 1, im.get("label") or "")
        if im.get("width"):
            cap += " · %d x %d px · %s" % (im["width"], im["height"], _bytes(im.get("bytes") or 0))
        warn = ""
        if im.get("error"):
            warn = "<div class=warn>Could not read this image: %s</div>" % _e(im["error"])
        elif (im.get("oneColour") or 0) >= BLANK_SHARE:
            warn = ("<div class=warn>%d%% of this image is one colour: the screenshot or crop may be "
                    "empty.</div>" % int(round(im["oneColour"] * 100)))
        src = _e(file_url(im["file"])) if im.get("file") else ""
        parts.append("<figure>%s<figcaption>%s</figcaption>%s</figure>" % (
            ("<a href='%s' target=_blank rel=noopener><img src='%s' alt=''></a>" % (src, src)) if src else "",
            _e(cap), warn))
    parts.append("</div>")
    return "".join(parts)


def _table(rows):
    # type: (List[Dict[str, Any]]) -> str
    order = {"sure-no": 0, "unsure": 1, "answered": 2, "sure-yes": 3, "not-asked": 4}
    out = ["<div class=tw><table><tr><th>Result</th><th>Check</th><th>Question</th><th>Answer</th>"
           "<th>Confidence</th><th>Source</th></tr>"]
    for r in sorted(rows, key=lambda r: order.get(outcome(r), 9)):
        o = outcome(r)
        q = r.get("question") or {}
        qtext = _e(q.get("instructions") or r.get("claim") or r.get("statement") or r.get("x"))
        if q.get("type") == "choice":
            probs = r.get("probabilities") or {}
            exp = set(r.get("expect") or [])
            opts = []
            for k in (q.get("criteria") or {}):
                label = _e(k) + (" " + _fmt(probs[k]) if k in probs else "")
                opts.append("<b>%s</b>" % label if k in exp else label)
            qtext += "<div class=opts>options: %s%s</div>" % (
                " · ".join(opts), " (bold = expected)" if exp else "")
        if o == "not-asked":
            ans = _e(r.get("message") or STATUS_WHY.get(r.get("status"), r.get("status")))
            conf = "-"
        else:
            ans = _e(answer_text(r))
            conf = "%s (%s)" % (_fmt(r.get("confidence")), _e(r.get("band")))
        out.append("<tr data-o=%s><td class=o>%s</td><td>%s%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
                   % (o, OUTCOME_LABEL[o], _e(r.get("id")),
                      ("<div class=meta>" + _e(r["selector"]) + "</div>") if r.get("selector") else "",
                      qtext, ans, conf, _e(r.get("source") or "screen criteria")))
    out.append("</table></div>")
    return "".join(out)


def page_url(rid):
    # type: (str) -> str
    return "/__qa/visual-report?id=" + urllib.parse.quote(rid)


def file_url(rid):
    # type: (str) -> Any
    return lambda name: ("/__qa/visual-report/file?id=%s&f=%s"
                         % (urllib.parse.quote(rid), urllib.parse.quote(name)))

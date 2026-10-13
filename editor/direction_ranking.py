"""The design library ranked for a brief by the text judge, before any agent
composes a direction.

When typed judgment for text checks is on and a project has no direction yet
(no `DECISION_prototype-direction.json`, no page built), the daemon asks the
text judge ONE request at thread start: does the brief leave the visual
direction open, and how does it rank every recipe, shell, style and
aesthetic of the design library (docs/research/direction-axes.jev.json). The
answer is shown to the user under their message (the judge is far faster
than the agent) and handed to the agent in its first message, so the step
cannot be skipped. With the setting off nothing here runs.
"""

import json
import os
import re
import time
from typing import Any, Callable, Dict, List, Optional

import typed_judge

AXES = ("recipe", "shell", "style", "aesthetic")
CORE = ("shell", "style", "aesthetic")
TOP = 5
PROPOSALS = 3
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AXES_FILE = os.path.join(_ROOT, "docs", "research", "direction-axes.jev.json")
PROTOTYPE_MD = os.path.join(_ROOT, "PROTOTYPE.md")
_ROSTER_LINK = re.compile(r"^- \*\*([^*]+)\*\*.*?\(\./design-library/([\w+.-]+)\.md\)", re.M)
NEEDS_DIRECTION = "This request leaves the visual direction unspecified."
IS_BUILD = "This request asks to build or design something new: an app, a website, a game, a page or a screen."
# A brief that names only part of its direction ("pixel art": a style, no
# aesthetic, no layout) sits around 0.5 on NEEDS_DIRECTION; one that states it
# all ("Swiss modernist, Helvetica, a 12-column grid, black and red") near
# 0.03. Proposals keep what the brief states and spread across what it leaves
# open, so only a fully stated brief skips them (Clef, 2026-10-13 samples).
NEEDS_CUT = 0.25


def applies(project_root):
    # type: (str) -> bool
    """No direction yet: no direction decision, and no page built."""
    if not project_root or os.path.isfile(os.path.join(project_root, "DECISION_prototype-direction.json")):
        return False
    src = os.path.join(project_root, "source")
    try:
        protos = [d for d in os.listdir(src) if not d.startswith(".") and os.path.isdir(os.path.join(src, d))]
    except OSError:
        return True
    for d in protos:
        try:
            if any(f.endswith((".html", ".htm")) and not f.startswith(".")
                   for f in os.listdir(os.path.join(src, d))):
                return False
        except OSError:
            continue
    return True


_CONTEXT = re.compile(r"^\[Context: you're chatting from (?:WORKFLOW|EDITOR) MODE[^\n]*(?:\n(?!\n)[^\n]*)*\n\n")
_BLOCK = re.compile(r"^\s*<(selected-nodes|whiteboard|selected-frame|chat-target)\b[\s\S]*?</\1>\s*")


def brief_of(message):
    # type: (str) -> str
    """The user's own words from a first message: the editor prefixes its
    context ("[Context: you're chatting from WORKFLOW MODE ...]" and blocks
    like <chat-target>), which is not the request. Mirrors the chat's own
    stripChatPreamble."""
    s = (message or "").lstrip()
    m = _CONTEXT.match(s)
    if m:
        s = s[m.end():]
    prev = None
    while prev != s:
        prev = s
        s = _BLOCK.sub("", s, count=1)
    return s.strip()


def load_axes(path=None):
    # type: (Optional[str]) -> Dict[str, Any]
    with open(path or AXES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)["axes"]


def questions(axes):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    qs = {"is_build": {"type": "noul", "instructions": IS_BUILD},
          "needs_direction": {"type": "noul", "instructions": NEEDS_DIRECTION}}  # type: Dict[str, Any]
    for k in AXES:
        if k in axes:
            qs[k] = {"type": "choice", "instructions": axes[k]["question"], "criteria": axes[k]["criteria"]}
    return qs


_PREVIEWS = None  # type: Optional[Dict[str, str]]


def previews(path=None):
    # type: (Optional[str]) -> Dict[str, str]
    """Library id -> its preview image (`design-library/<file>-ui.png`), from
    the roster lines in PROTOTYPE.md that link each id to its library file."""
    global _PREVIEWS
    if _PREVIEWS is not None and path is None:
        return _PREVIEWS
    out = {}  # type: Dict[str, str]
    try:
        with open(path or PROTOTYPE_MD, "r", encoding="utf-8") as f:
            text = f.read()
        lib = os.path.join(os.path.dirname(path or PROTOTYPE_MD), "design-library")
        for m in _ROSTER_LINK.finditer(text):
            png = m.group(2) + "-ui.png"
            if m.group(1).strip() not in out and os.path.isfile(os.path.join(lib, png)):
                out[m.group(1).strip()] = "design-library/" + png
    except OSError:
        pass
    if path is None:
        _PREVIEWS = out
    return out


def proposals(event, n=PROPOSALS):
    # type: (Dict[str, Any], int) -> List[Dict[str, Any]]
    """Three complete directions (shell + style + aesthetic) from the ranking,
    by PROTOTYPE.md step -1's own rule: an axis the brief implies (top pick at
    or over the high threshold) keeps its top pick in all three; the three
    SPREAD across the axis the brief leaves most open (aesthetic first, then
    style, then shell), taking its top picks in order."""
    axes = event.get("axes") or {}
    high = float((event.get("thresholds") or {}).get("high") or 0.7)
    core = [a for a in CORE if (axes.get(a) or {}).get("top")]
    if not core:
        return []
    open_axes = [a for a in core if axes[a]["top"][0]["p"] < high]
    spread = open_axes[-1] if open_axes else min(core, key=lambda a: axes[a]["top"][0]["p"])
    for a in ("aesthetic", "style", "shell"):
        if a in open_axes:
            spread = a
            break
    out = []
    for i, pick in enumerate(axes[spread]["top"][:n]):
        combo = {a: (pick if a == spread else axes[a]["top"][0]) for a in core}
        out.append({"spread": spread, "picks": {a: {k: t[k] for k in ("id", "label", "p", "preview") if k in t}
                                                 for a, t in combo.items()}})
    return out


def _label(option_id):
    # type: (str) -> str
    return option_id.replace("recipe-", "").replace("-", " ")


def propose(project_root, brief, judge=None, axes_path=None, enabled=None):
    # type: (str, str, Optional[Callable[..., Dict[str, Any]]], Optional[str], Optional[bool]) -> Optional[Dict[str, Any]]
    """{"event": <what the thread shows, or None>, "forAgent": <block for the
    agent's first message>}, or None when the setting is off or a direction
    exists. With the setting on the agent never composes direction options:
    proposals are shown and it waits for the pick; a brief that states its
    direction is locked as stated; a request that is no new build gets
    nothing. Never raises: a failure is shown and the agent told why."""
    if enabled is None:
        try:
            enabled = bool(typed_judge.config().get("jevJudge"))
        except Exception:
            enabled = False
    brief = brief_of(brief)
    if not enabled or not brief or not applies(project_root):
        return None
    try:
        axes = load_axes(axes_path)
    except Exception as exc:
        return _failed("the design library's ranking file could not be read (%s)" % exc)
    t0 = time.time()
    try:
        out = (judge or typed_judge.judge)(brief.strip()[:6000], questions(axes), tier="text",
                                           kind="direction_axis")
    except typed_judge.JudgeUnavailable as exc:
        return _failed("no text judge is set up (%s)" % exc)
    except Exception as exc:
        return _failed(str(exc)[:240])
    ms = int((time.time() - t0) * 1000)
    answers = out.get("answers") or {}
    th = out.get("thresholds") or {}
    # The chain's first two links, from the same call: a request that is not a
    # new build needs no direction; one that states its whole direction gets
    # it locked as stated. Neither shows proposals.
    cut = float(th.get("noul") or 0.5)
    is_build = typed_judge.noul_value(answers.get("is_build"))
    needs = typed_judge.noul_value(answers.get("needs_direction"))
    if is_build is None or is_build < cut:
        return {"event": None, "forAgent": ""}
    if needs is None or needs < NEEDS_CUT:
        return _stated(needs or 0.0, out.get("provider") or "the text judge")
    event = {"provider": out.get("provider"), "model": out.get("model"), "ms": ms,
             "needsDirection": needs, "isBuild": is_build,
             "thresholds": {k: th.get(k) for k in ("low", "high", "noul")},
             "axes": {}}  # type: Dict[str, Any]
    for k in AXES:
        if k not in axes:
            continue
        a = answers.get(k) or {}
        probs = a.get("probabilities") or {}
        ranked = sorted(probs.items(), key=lambda kv: -kv[1])[:TOP]
        event["axes"][k] = {
            "question": axes[k]["question"], "optional": bool(axes[k].get("optional")),
            "confidence": a.get("confidence"),
            "top": [dict({"id": i, "label": _label(i), "p": round(float(p), 4),
                          "desc": str(axes[k]["criteria"].get(i, ""))[:200]},
                         **({"preview": previews()[i]} if i in previews() else {})) for i, p in ranked],
        }
    event["proposals"] = proposals(event)
    event["slug"] = "%d-judge-%s" % (int(time.time()), os.urandom(2).hex())
    return {"event": event, "forAgent": for_agent(event, out.get("provider") or "the text judge")}


# With the judge on, the agent never composes direction options (PROTOTYPE.md
# step -1): every path below locks a direction or waits for the user's pick.
LOCK = ("To lock a direction: map it to library ids (shell, style, aesthetic: from the ranking when one is given, else "
        "PROTOTYPE.md's rosters), read those library files for palette and fonts, POST "
        "/__decision/prototype-direction with values, labels and the full detail, and go on to the next step.")


def _block(text):
    # type: (str) -> str
    return "[Woven: typed judgment is on, so do NOT compose direction options, do not run PROTOTYPE.md " \
           "step -1's composing or recolouring, and do not call /__judge. " + text + " " + LOCK + "]"


def _stated(needs, provider):
    # type: (float, str) -> Dict[str, Any]
    return {"event": None, "forAgent": _block(
        "The typed judge (%s) read this request as a new build that already states its direction "
        "(leaves it open: %s). Lock the direction it states." % (provider, _n(needs)))}


def _failed(error):
    # type: (str) -> Dict[str, Any]
    return {"event": {"error": error}, "forAgent": _block(
        "The judge could not rank the library (%s). If the request states a direction, lock it; if it "
        "states none, ask the user in one line to describe the look they want, then stop." % error)}


def for_agent(event, provider):
    # type: (Dict[str, Any], str) -> str
    """The block for the agent's first message. With proposals on screen the
    agent does NOT compose direction options: the judge's three are the
    options, and the user's pick arrives as a decision."""
    th = event.get("thresholds") or {}
    props = event.get("proposals") or []
    if not props:
        return ""
    lines = ["[Woven: the typed judge (%s, %.1f s) ranked the design library for this request and the user "
             "is now choosing a direction from its %d proposals, shown under their message. Do NOT compose "
             "direction options, do not run PROTOTYPE.md step -1's composing or recolouring, and do not call "
             "/__judge: reply in one short line that they can pick one of the proposals above or describe their "
             "own direction, then stop. Their pick arrives as `[decision:prototype-direction] N - <title>`; "
             "option N's shell, style, aesthetic, palette and fonts (exactly what the card showed) are in "
             "`.prototype-options/%s/options.json`. Continue from the direction lock: POST "
             "/__decision/prototype-direction with that option as the full detail and go on to the next "
             "step. If they "
             "describe their own direction instead, lock THAT one directly (%s); never compose options."
             % (provider, (event.get("ms") or 0) / 1000.0, len(props), event.get("slug", ""), LOCK),
             "the proposals (they differ in %s, the axis the brief leaves most open):" % props[0]["spread"]]
    for i, pr in enumerate(props):
        lines.append("  %d. %s" % (i + 1, ", ".join("%s %s" % (a, t["id"]) for a, t in pr["picks"].items())))
    lines.append("ranking behind them (thresholds low %s, high %s):" % (_n(th.get("low")), _n(th.get("high"))))
    for k, ax in (event.get("axes") or {}).items():
        lines.append("  %s (confidence %s): %s" % (k, _n(ax.get("confidence")),
                                                   ", ".join("%s %s" % (t["id"], _n(t["p"])) for t in ax["top"])))
    return "\n".join(lines) + "]"


def _n(v):
    # type: (Any) -> str
    return "-" if v is None else ("%.2f" % float(v))


# ── The card: the judge's proposals as the same <direction-options> the agent
# emits, so the user sees the same card (palette chips, type samples in the
# real Google font, library previews recoloured into each option's palette).

LIBRARY = os.path.join(_ROOT, "design-library")
RECOLOR = os.path.join(_ROOT, "scripts", "prototype-recolor.py")
_HEX = re.compile(r"#[0-9a-fA-F]{6}\b")
NEUTRAL = ["#fafafa", "#ffffff", "#1a1a1a", "#6b6b6b", "#e5e5e5", "#3b5bdb"]

# The families the judge picks display and body type from, each with what it
# reads as (Google Fonts, so the chat can load them).
FONTS = {
    "Inter": "neutral modern sans for interfaces and body text",
    "DM Sans": "friendly geometric sans, soft and modern",
    "Manrope": "clean modern sans with a slight warmth",
    "Space Grotesk": "techy grotesque with quirky details",
    "IBM Plex Sans": "engineered corporate sans",
    "Work Sans": "plain grotesque, newsy and neutral",
    "Archivo": "compact grotesque, sturdy",
    "Archivo Black": "heavy black display grotesque",
    "Bebas Neue": "tall condensed all-caps display",
    "Anton": "heavy condensed poster display",
    "Syne": "expressive art-school display sans",
    "Unbounded": "wide rounded futuristic display",
    "Nunito": "rounded soft sans for friendly, cozy UI",
    "Fredoka": "bubbly rounded display for playful, kid-friendly looks",
    "EB Garamond": "classic book serif, literary",
    "Cormorant Garamond": "elegant high-contrast serif, luxurious",
    "Playfair Display": "high-contrast editorial display serif",
    "Fraunces": "soft warm old-style display serif",
    "DM Serif Display": "bold contrasty display serif",
    "Libre Baskerville": "traditional reading serif",
    "Source Serif 4": "modern reading serif for long text",
    "Cinzel": "Roman inscription capitals, classical and heraldic",
    "Uncial Antiqua": "medieval uncial script, fantasy",
    "MedievalSharp": "medieval fantasy display",
    "Pirata One": "blackletter-flavoured dark fantasy display",
    "UnifrakturMaguntia": "Gothic blackletter",
    "Press Start 2P": "NES / arcade 8-bit bitmap capitals",
    "Silkscreen": "tiny crisp pixel UI caps",
    "VT323": "terminal bitmap, CRT console",
    "Pixelify Sans": "modern readable pixel font for indie games",
    "DotGothic16": "Japanese-console dot-matrix pixel type",
    "Jersey 10": "chunky arcade pixel display",
    "JetBrains Mono": "developer monospace",
    "IBM Plex Mono": "typewriter-like engineered monospace",
    "Space Mono": "retro-futurist monospace",
    "Caveat": "casual handwriting",
    "Patrick Hand": "neat marker handwriting",
}


def library_file(option_id, suffix):
    # type: (str, str) -> Optional[str]
    """The library file for an axis id (`-ui.png` preview or `.md` entry)."""
    pv = previews().get(option_id)
    if not pv:
        return None
    path = os.path.join(_ROOT, pv[:-len("-ui.png")] + suffix)
    return path if os.path.isfile(path) else None


def _section(md_text, heading):
    # type: (str, str) -> str
    m = re.search(r"^## %s[^\n]*\n(.*?)(?=^## |\Z)" % re.escape(heading), md_text, re.S | re.M)
    return m.group(1).strip() if m else ""


def all_hexes(md_text):
    # type: (str) -> List[str]
    seen = []  # type: List[str]
    for h in _HEX.findall(_section(md_text, "Palette anchor")):
        if h.lower() not in seen:
            seen.append(h.lower())
    return seen


def palette_hexes(md_text):
    # type: (str) -> List[str]
    """The palette an entry's "Palette anchor" names: the first line that is a
    whole family (4+ swatches) when it lists several families, else every
    swatch in the section, in order."""
    sec = _section(md_text, "Palette anchor")
    for line in sec.splitlines():
        found = _HEX.findall(line)
        if len(found) >= 4:
            return [h.lower() for h in found]
    seen = []  # type: List[str]
    for h in _HEX.findall(sec):
        if h.lower() not in seen:
            seen.append(h.lower())
    return seen


def _oklab(hexcode):
    # type: (str) -> List[float]
    def lin(c):
        # type: (float) -> float
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(int(hexcode[i:i + 2], 16)) for i in (1, 3, 5))
    l_ = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3.0)
    m_ = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3.0)
    s_ = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3.0)
    L = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
    a = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    bb = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_
    return [L, (a * a + bb * bb) ** 0.5]


def _mix(h1, h2, t):
    # type: (str, str, float) -> str
    c1 = [int(h1[i:i + 2], 16) for i in (1, 3, 5)]
    c2 = [int(h2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join("%02x" % int(round(a + (b - a) * t)) for a, b in zip(c1, c2))


def palette_tokens(hexes, every=None):
    # type: (List[str], Optional[List[str]]) -> List[str]
    """The six tokens a direction card shows (bg, surface, fg, muted, border,
    accent) from a library palette: the lightest swatch is the ground, the
    darkest the ink (darkened until it reads on the ground), and the accent
    the most saturated swatch anywhere in the entry's palette (`every`);
    surface, muted and border step between ground and ink."""
    if len(hexes) < 2:
        return list(NEUTRAL)
    every = [h for h in (every or []) if h] or list(hexes)
    lab = {h: _oklab(h) for h in set(hexes) | set(every)}
    bg = max(hexes, key=lambda h: lab[h][0])
    fg = min(hexes, key=lambda h: lab[h][0])
    if lab[bg][0] - lab[fg][0] < 0.35:
        # Not enough contrast inside the family: take the entry's darkest ink,
        # else darken toward black.
        darkest = min(every, key=lambda h: lab[h][0])
        fg = darkest if lab[bg][0] - lab[darkest][0] >= 0.35 else _mix(fg, "#000000", 0.7)
        lab[fg] = _oklab(fg)
    # The accent stays inside the family when the family has colour at all
    # (entries like 8-bit say never mix palette families).
    own = [h for h in hexes if h not in (bg, fg) and lab[h][1] >= 0.08]
    rest = own or [h for h in every if h not in (bg, fg)]
    accent = max(rest, key=lambda h: lab[h][1]) if rest else _mix(fg, "#3b5bdb", 0.6)
    near = [h for h in hexes + every if h not in (bg, fg, accent) and abs(lab[h][0] - lab[bg][0]) < 0.12
            and lab[h][1] < 0.06]
    surface = near[0] if near else _mix(bg, fg, 0.05)
    return [bg, surface, fg, _mix(bg, fg, 0.55), _mix(bg, fg, 0.18), accent]


def _title(md_text):
    # type: (str) -> str
    """An entry's own H1 (after its front matter), without the axis suffix."""
    body = re.sub(r"\A---\n.*?\n---\n", "", md_text, flags=re.S)
    m = re.search(r"^# (.+)$", body, re.M)
    return re.sub(r"\s*\((aesthetic|style|shell)\)\s*$", "", m.group(1)).strip() if m else ""


def _brief_strings(brief):
    # type: (str) -> List[str]
    """A display line and a body line taken from the brief itself."""
    text = re.sub(r"\s+", " ", brief).strip()
    first = re.split(r"(?<=[.!?])\s", text)[0]
    subject = re.sub(r"^(i\s+(want|would like|need)\s+(to\s+)?)?(create|build|make|design)\s+(an?\s+|the\s+)?",
                     "", first, flags=re.I)
    head = re.split(r"\s+(?:that|which|with|where|for)\s+|[,;:]", subject)[0].strip()
    head = " ".join(head.split()[:7]).rstrip(".!?") or "Your new prototype"
    sentences = re.split(r"(?<=[.!?])\s", text)
    body = sentences[1] if len(sentences) > 1 and len(sentences[1]) > 20 else subject
    body = body[:1].upper() + body[1:]
    body = body if len(body) <= 160 else body[:157].rsplit(" ", 1)[0] + "..."
    return [head[:1].upper() + head[1:], body]


def _pick_fonts(pr, md_text, judge):
    # type: (Dict[str, Any], str, Any) -> List[str]
    """Display and body family for one proposal, chosen by the text judge
    from FONTS against the aesthetic's own description. Inter when it fails."""
    state = "A visual direction for an interface. Aesthetic: %s. %s Style: %s." % (
        pr["picks"].get("aesthetic", {}).get("label", ""),
        (_section(md_text, "Cultural identity") + " " + _section(md_text, "Failure mode"))[:1400],
        pr["picks"].get("style", {}).get("label", ""))
    qs = {"display": {"type": "choice", "instructions": "Which font family suits this direction's headings?",
                      "criteria": dict(FONTS)},
          "body": {"type": "choice", "instructions": "Which font family suits this direction's body text, "
                                                      "readable at small sizes?", "criteria": dict(FONTS)}}
    try:
        out = judge(state, qs, tier="text", kind="direction_axis")
        pick = lambda k: (out["answers"].get(k) or {}).get("choice") or "Inter"
        return [pick("display"), pick("body")]
    except Exception:
        return ["Inter", "Inter"]


def _esc(text):
    # type: (Any) -> str
    return (str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def card(event, brief, project_root, judge=None, recolor=None):
    # type: (Dict[str, Any], str, str, Any, Any) -> Dict[str, Any]
    """The judge's proposals as a `<direction-options>` block (the card the
    agent's step -1 emits), with palette, fonts and recoloured previews.
    Returns the event with `markup` and per-option `options`, or with
    `error`. Never raises."""
    from concurrent.futures import ThreadPoolExecutor
    judge = judge or typed_judge.judge
    props = event.get("proposals") or []
    if not props:
        return dict(event, error="the judge made no proposals")
    slug = event.get("slug") or "%d-judge-%s" % (int(time.time()), os.urandom(2).hex())
    out_dir = os.path.join(project_root, ".prototype-options", slug)
    os.makedirs(out_dir, exist_ok=True)
    head, body = _brief_strings(brief)
    mds = []
    for pr in props:
        path = library_file(pr["picks"].get("aesthetic", {}).get("id", ""), ".md")
        try:
            mds.append(open(path, "r", encoding="utf-8").read() if path else "")
        except OSError:
            mds.append("")
    with ThreadPoolExecutor(max_workers=3) as pool:
        fonts = list(pool.map(lambda i: _pick_fonts(props[i], mds[i], judge), range(len(props))))
    options = []
    jobs = []
    for n, (pr, md) in enumerate(zip(props, mds)):
        tokens = palette_tokens(palette_hexes(md), all_hexes(md))
        opt = {"value": str(n + 1), "picks": pr["picks"], "palette": tokens, "fonts": fonts[n],
               "title": _title(md) or pr["picks"].get("aesthetic", {}).get("label", "Direction"),
               "images": []}
        for axis in ("aesthetic", "style", "shell"):
            t = pr["picks"].get(axis)
            src = library_file(t["id"], "-ui.png") if t else None
            if src:
                dest = os.path.join(out_dir, "option-%d-%s.png" % (n + 1, axis))
                opt["images"].append({"axis": axis, "id": t["id"], "src": src, "dest": dest})
                jobs.append((src, dest, tokens))
        options.append(opt)

    def run(job):
        # type: (Any) -> bool
        src, dest, tokens = job
        try:
            if recolor:
                return bool(recolor(src, dest, tokens))
            import subprocess
            import sys
            done = subprocess.run([sys.executable, RECOLOR, src, dest, "--tokens", ",".join(tokens)],
                                  capture_output=True, timeout=60)
            return done.returncode == 0 and os.path.isfile(dest)
        except Exception:
            return False
    with ThreadPoolExecutor(max_workers=6) as pool:
        ok = dict(zip([j[1] for j in jobs], pool.map(run, jobs)))
    lines = ['<direction-options id="prototype-direction" prompt="Pick a direction - proposed by the typed judge '
             '(%s) from the design library: palette, typography and a recoloured library preview per option">'
             % _esc(event.get("provider") or "text judge")]
    for n, opt in enumerate(options):
        pk = opt["picks"]
        adesc = next((t.get("desc", "") for t in event["axes"].get("aesthetic", {}).get("top", [])
                      if t["id"] == pk.get("aesthetic", {}).get("id")), "")
        tags = re.match(r"^\[([^\]]*)\]\s*(.*)$", adesc or "")
        vibe = (tags.group(1).split("·")[1].strip() if tags and "·" in tags.group(1) else "")
        why = tags.group(2) if tags else adesc
        recoloured = 0
        lines.append('  <opt value="%d"%s>' % (n + 1, " recommended" if n == 0 else ""))
        lines.append("    <label>%s</label>" % _esc(opt["title"]))
        lines.append("    <axes>Shell: %s · Style: %s · Aesthetic: %s</axes>" % tuple(
            _esc(pk.get(a, {}).get("id", "(none)")) for a in ("shell", "style", "aesthetic")))
        if vibe:
            lines.append("    <vibe>%s</vibe>" % _esc(vibe))
        if why:
            lines.append("    <why>%s</why>" % _esc(why))
        lines.append("    <palette>%s</palette>" % ",".join(opt["palette"]))
        lines.append('    <display font="%s">%s</display>' % (_esc(opt["fonts"][0]), _esc(head)))
        lines.append('    <body font="%s">%s</body>' % (_esc(opt["fonts"][1]), _esc(body)))
        for im in opt["images"]:
            if ok.get(im["dest"]):
                src = os.path.relpath(im["dest"], project_root).replace(os.sep, "/")
                recoloured += 1
            else:
                src = "/" + os.path.relpath(im["src"], _ROOT).replace(os.sep, "/")
            lines.append('    <image axis="%s" src="%s" alt="%s · %s"/>' % (
                im["axis"], _esc(src), im["axis"].capitalize(), _esc(im["id"])))
        lines.append("    <badge>auto-preview · judge-ranked · %d axes recoloured from design-library/</badge>"
                     % recoloured if recoloured else
                     "    <badge>colours illustrative - original library reference shown</badge>")
        lines.append("  </opt>")
    lines.append("</direction-options>")
    summary = [{"value": o["value"], "title": o["title"], "palette": o["palette"],
                "fonts": {"display": o["fonts"][0], "body": o["fonts"][1]},
                "picks": {a: t.get("id") for a, t in o["picks"].items()}} for o in options]
    try:
        with open(os.path.join(out_dir, "options.json"), "w", encoding="utf-8") as f:
            json.dump({"options": summary}, f, indent=1)
    except OSError:
        pass
    return dict(event, markup="\n".join(lines), options=summary)

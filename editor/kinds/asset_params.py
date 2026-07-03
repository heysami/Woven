"""editor/kinds/asset_params.py - extract tunable parameters from generated assets.

The host's "auto-expose controls" feature reads what an asset's source ACTUALLY
contains and surfaces the numbers/colors a user would want to tune - instead of
each generator pipeline having to declare a contract (which always leaves gaps).

This module is the BRAIN: given JS/HTML source, it returns the tunable literals -
the init-constants and uniform defaults a designer would reach for - while
EXCLUDING the noise (per-frame-driven values, loop math, and every number baked
inside GLSL shader strings).

Two correctness pillars:

  1. Only NAME-BOUND literals are captured: `const NAME = 0.9`, `KEY: 0.27`
     (object property), `const uX = { value: 1.0 }` (uniform). Bare numbers in
     expressions (`0.012 * dt`, `dt > 0.1`) are never bound to a fresh name, so
     they are ignored - which also drops loop math automatically.

  2. Strings, comments, and TEMPLATE LITERALS are blanked before matching, so the
     huge GLSL bodies (full of numbers) contribute nothing. Hex-color strings are
     the one exception - they are kept so `new THREE.Color('#2f8fb0')` is seen.

  Per-frame exclusion: a uniform `const uX = { value: N }` is dropped when `uX.value`
  is assigned/mutated anywhere else (`uTime.value = t`, `uOrcaUV.value.set(...)`),
  and a plain `const NAME = N` is dropped when `NAME` is reassigned later. So a
  driven uniform (uTime/uDecay/uOrcaSpeed) is excluded while a tunable one
  (uCausticStrength, never reassigned) is kept.

Pure stdlib, 3.9-safe (future annotations), unit-testable offline like
shader_compile.py. No daemon/network/three.js dependency.
"""
from __future__ import annotations

import re
from typing import Dict, List, Tuple

_HEX_RE = re.compile(r"^#[0-9a-fA-F]{3,8}$")


def _blank_noncode(s: str) -> str:
    """Return a copy of `s` with comments, template literals and non-hex strings
    replaced by spaces (newlines preserved), so offsets still map 1:1 to the
    original. Hex-color string literals are KEPT verbatim (we want them)."""
    out = list(s)
    n = len(s)

    def blank(a: int, b: int) -> None:
        for k in range(a, b):
            if out[k] != "\n":
                out[k] = " "

    i = 0
    while i < n:
        c = s[i]
        # line comment
        if c == "/" and i + 1 < n and s[i + 1] == "/":
            j = s.find("\n", i)
            j = n if j < 0 else j
            blank(i, j)
            i = j
            continue
        # block comment
        if c == "/" and i + 1 < n and s[i + 1] == "*":
            j = s.find("*/", i + 2)
            j = n if j < 0 else j + 2
            blank(i, j)
            i = j
            continue
        # template literal - blank wholesale (GLSL lives here). ${} not parsed;
        # the generated shaders don't interpolate JS literals into knobs.
        if c == "`":
            j = i + 1
            while j < n:
                if s[j] == "\\":
                    j += 2
                    continue
                if s[j] == "`":
                    break
                j += 1
            end = min(n, j + 1)
            blank(i, end)
            i = end
            continue
        # quoted string - keep iff it is exactly a hex color, else blank
        if c == "'" or c == '"':
            q = c
            j = i + 1
            while j < n:
                if s[j] == "\\":
                    j += 2
                    continue
                if s[j] == q:
                    break
                j += 1
            content = s[i + 1 : j]
            end = min(n, j + 1)
            if not _HEX_RE.match(content):
                blank(i, end)
            i = end
            continue
        i += 1
    return "".join(out)


def _pretty(name: str) -> str:
    """`uCausticStrength` -> "Caustic Strength"; `COLOR_TOP` -> "Color Top";
    `clearcoatRoughness` -> "Clearcoat Roughness"."""
    n = name
    # strip a single leading lowercase `u` used as the uniform convention
    if len(n) > 1 and n[0] == "u" and n[1].isupper():
        n = n[1:]
    n = n.replace("_", " ")
    # split camelCase
    n = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", n)
    words = [w for w in re.split(r"\s+", n) if w]
    if not words:
        return name
    # Title-case each word (folds ALL_CAPS like COLOR_TOP -> "Color Top").
    return " ".join(w[:1].upper() + w[1:].lower() for w in words)


def _num_meta(num_str: str) -> Tuple[str, float, Dict[str, float]]:
    """Return (type, value, bounds) for a numeric literal string."""
    v = float(num_str)
    is_int = "." not in num_str and "e" not in num_str.lower()
    if 0.0 <= v <= 1.0 and not (is_int and v not in (0.0, 1.0)):
        return "range", v, {"min": 0.0, "max": 1.0, "step": 0.01}
    if is_int:
        hi = max(10.0, abs(v) * 4)
        lo = 0.0 if v >= 0 else -hi
        return "int", v, {"min": lo, "max": hi, "step": 1.0}
    mag = abs(v)
    hi = max(1.0, mag * 4)
    lo = 0.0 if v >= 0 else -hi
    step = round((hi - lo) / 100.0, 6) or 0.01
    return "range", v, {"min": lo, "max": hi, "step": step}


# A name-bound literal: `const|let|var NAME = <num|Color>` OR `NAME: <num|Color>`
# (object property) OR a uniform `const NAME = { value: <num|Color> }`.
# The trailing lookahead requires the number to be the COMPLETE initializer
# (next non-space char is a terminator), so `const x = 0.25 * f(...)` - a computed
# value, not a constant - is NOT captured.
_VALUE_END = r"(?=\s*(?:[;,)\]}]|\n|$))"
_DECL_NUM = re.compile(
    r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(-?\d+\.?\d*(?:e-?\d+)?)" + _VALUE_END
)
_DECL_COLOR = re.compile(
    r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*new\s+THREE\.Color\(\s*['\"](#[0-9a-fA-F]{3,8})['\"]"
)
_DECL_UNIFORM = re.compile(
    r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*\{\s*value\s*:\s*([^,}]+?)\s*[},]"
)
_PROP_NUM = re.compile(r"\b([A-Za-z_$][\w$]*)\s*:\s*(-?\d+\.?\d*(?:e-?\d+)?)" + _VALUE_END)

# A plain `const NAME = <num>` is a module knob only when NAME reads as a CONSTANT
# (UPPER_SNAKE) or a uniform (`uX`). A lowercase camel local (`tuck`, `beat`) is an
# internal, not a knob. Object-property numbers (`roughness:`) are exempt - those
# are config keys and intentionally tunable regardless of case.
_CONST_NAME = re.compile(r"^(?:[A-Z][A-Z0-9_]*|u[A-Z]\w*)$")
_PROP_COLOR = re.compile(
    r"\b([A-Za-z_$][\w$]*)\s*:\s*new\s+THREE\.Color\(\s*['\"](#[0-9a-fA-F]{3,8})['\"]"
)

# Pick the "default" number out of a uniform value expression. For a ternary
# `reduced ? 0.55 : 1.0` we take the LAST number (the non-reduced/default branch).
_NUM_IN = re.compile(r"-?\d+\.?\d*(?:e-?\d+)?")

# Property keys that are bookkeeping, not user-tunable knobs.
_SKIP_KEYS = {
    "value", "min", "max", "step", "width", "height", "count", "length",
    "format", "type", "wrapS", "wrapT", "minFilter", "magFilter",
    "depthBuffer", "stencilBuffer", "depthTest", "depthWrite", "key", "id",
}

# Common loop/temp/math identifiers that are never meaningful user knobs even
# when bound to a literal (e.g. `const k = 2.02`, `let dt = ...`, `const ao`).
_SKIP_NAMES = {
    "i", "j", "k", "m", "n", "x", "y", "z", "t", "u", "v", "f", "d", "e",
    "p", "q", "r", "s", "w", "h", "a", "b", "c", "g", "o", "l",
    "dt", "dx", "dy", "dz", "ao", "uv", "px", "py", "idx", "tmp", "len",
    "lastt", "now", "pi", "tau", "eps",
}

# Function names whose bodies run every frame - literals declared inside them are
# animation internals, not knobs. We exclude any param whose span lands in one.
_PERFRAME_FNS = ("onFrame", "render", "tick", "update", "step", "animate",
                 "onTick", "loop", "frame", "draw")


def _brace_match(s: str, open_idx: int) -> int:
    """Index just past the `}` matching the `{` at `open_idx` (or len on EOF)."""
    depth = 0
    n = len(s)
    i = open_idx
    while i < n:
        ch = s[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return n


def _perframe_ranges(cleaned: str) -> List[Tuple[int, int]]:
    """Char ranges of per-frame function bodies (already comment/string-blanked)."""
    ranges: List[Tuple[int, int]] = []
    name_alt = "|".join(_PERFRAME_FNS)
    # `function onFrame(...) {`, `onFrame(...) {` (method), `onFrame = (...) => {`
    pat = re.compile(r"\b(?:" + name_alt + r")\b\s*(?:=\s*)?(?:function\b[^\n(]*)?\([^)]*\)\s*(?:=>\s*)?\{")
    for m in pat.finditer(cleaned):
        brace = cleaned.find("{", m.end() - 1)
        if brace >= 0:
            ranges.append((brace, _brace_match(cleaned, brace)))
    return ranges


def _assigned_elsewhere(cleaned: str, name: str) -> bool:
    """True if `name` is reassigned beyond its single declaration - plain `=`,
    or a compound/increment mutation (`+=`, `-=`, `++`, `--`, …)."""
    nm = re.escape(name)
    # increment/compound mutations are unambiguous reassignments
    if re.search(r"\b" + nm + r"\s*(?:\+\+|--|[+\-*/%]=)", cleaned):
        return True
    if re.search(r"(?:\+\+|--)\s*" + nm + r"\b", cleaned):
        return True
    # plain `name =` (not ==, <=, >=, !=, =>); declaration is one such match
    hits = re.findall(r"(?<![=!<>+\-*/%])\b" + nm + r"\s*=(?![=>])", cleaned)
    return len(hits) > 1


def _value_mutated(cleaned: str, name: str) -> bool:
    """True if `name.value` is assigned or mutated (.set/.copy/.lerp/...)."""
    pat = re.compile(
        r"\b" + re.escape(name) + r"\.value\s*(?:=(?![=>])|\.(?:set|copy|lerp|add|sub|addScalar|multiplyScalar|setScalar|setHex|setRGB)\b)"
    )
    return bool(pat.search(cleaned))


def scan_source(text: str, group: str = "") -> List[dict]:
    """Extract tunable params from one JS/HTML source string.

    Returns a list of param dicts:
      { id, name, label, group, type, value, span:[start,end], **bounds }
    `span` is the [start,end) of the literal in the ORIGINAL text (rewrite target).
    """
    cleaned = _blank_noncode(text)
    perframe = _perframe_ranges(cleaned)
    params: List[dict] = []
    seen: set = set()

    def _in_perframe(pos: int) -> bool:
        return any(a <= pos < b for (a, b) in perframe)

    def add(name: str, type_: str, value, span: Tuple[int, int], bounds=None, default_str=None):
        if name in seen or name in _SKIP_KEYS:
            return
        if name.startswith("_"):
            return  # leading-underscore = internal (e.g. _frozenT, _camPos)
        if name.lower() in _SKIP_NAMES or len(name) <= 2:
            return  # loop/temp identifiers are never knobs
        if _in_perframe(span[0]):
            return  # literal declared inside a per-frame function body
        seen.add(name)
        p = {
            "id": (group + ":" if group else "") + name,
            "name": name,
            "label": _pretty(name),
            "group": group or "Controls",
            "type": type_,
            "value": value,
            "span": [span[0], span[1]],
        }
        if bounds:
            p.update(bounds)
        params.append(p)

    # 1. uniform declarations `const uX = { value: <expr> }`
    for m in _DECL_UNIFORM.finditer(cleaned):
        name, expr = m.group(1), m.group(2)
        if _value_mutated(cleaned, name):
            continue  # per-frame driven -> skip
        nums = _NUM_IN.findall(expr)
        if not nums:
            continue  # value is a Vector2/Color identifier/etc. - not a scalar
        num_str = nums[-1]  # ternary default = last branch
        # locate the chosen number's span within the original (search the expr region)
        start = text.find(num_str, m.start(2), m.end(2))
        if start < 0:
            start = m.start(2)
        type_, value, bounds = _num_meta(num_str)
        add(name, type_, value, (start, start + len(num_str)), bounds)

    # 2. plain numeric consts `const NAME = 0.9` - only CONSTANT-style names
    for m in _DECL_NUM.finditer(cleaned):
        name, num_str = m.group(1), m.group(2)
        if not _CONST_NAME.match(name):
            continue  # lowercase local, not a module knob
        if _assigned_elsewhere(cleaned, name):
            continue
        type_, value, bounds = _num_meta(num_str)
        add(name, type_, value, (m.start(2), m.end(2)), bounds)

    # 3. color consts `const COLOR_TOP = new THREE.Color('#..')`
    for m in _DECL_COLOR.finditer(cleaned):
        name, hex_ = m.group(1), m.group(2)
        add(name, "color", hex_, (m.start(2), m.end(2)))

    # 4. object-property numbers `roughness: 0.27`
    for m in _PROP_NUM.finditer(cleaned):
        name, num_str = m.group(1), m.group(2)
        if name in _SKIP_KEYS:
            continue
        type_, value, bounds = _num_meta(num_str)
        add(name, type_, value, (m.start(2), m.end(2)), bounds)

    # 5. object-property colors `color: new THREE.Color('#..')`
    for m in _PROP_COLOR.finditer(cleaned):
        name, hex_ = m.group(1), m.group(2)
        add(name, "color", hex_, (m.start(2), m.end(2)))

    return params


def scan_files(files: List[Tuple[str, str]]) -> List[dict]:
    """Scan multiple (path, text) sources. `group` is derived from each filename
    (e.g. `subsystems/liquid-shader-water.js` -> "water"). The `file` key is added
    so the daemon knows which file to rewrite. Names are de-duped across files
    (first file wins) so a uniform shared via runtime isn't shown twice."""
    out: List[dict] = []
    seen_names: set = set()
    for path, text in files:
        group = _group_for(path)
        for p in scan_source(text, group):
            if p["name"] in seen_names:
                continue
            seen_names.add(p["name"])
            p["file"] = path
            out.append(p)
    return out


def _group_for(path: str) -> str:
    base = path.rsplit("/", 1)[-1]
    base = re.sub(r"\.(js|html|mjs)$", "", base)
    # `liquid-shader-water` -> "water"; `hero-orca` -> "hero"; `runtime` -> "Scene"
    if base in ("runtime", "index"):
        return "Scene"
    last = re.split(r"[-_]", base)[-1]
    return last[:1].upper() + last[1:] if last else "Controls"


def rewrite_literal(text: str, span: Tuple[int, int], new_value, type_: str) -> str:
    """Replace the literal at `span` with `new_value` and return the new source.
    For colors the replacement is the hex (the surrounding quotes stay). For
    numbers it is the stringified number."""
    start, end = span[0], span[1]
    if type_ == "color":
        rep = str(new_value)
        if not rep.startswith("#"):
            rep = "#" + rep
    else:
        f = float(new_value)
        rep = str(int(f)) if (type_ == "int" and f == int(f)) else _fmt_num(f)
    return text[:start] + rep + text[end:]


def _fmt_num(f: float) -> str:
    s = ("%.4f" % f).rstrip("0").rstrip(".")
    return s if s not in ("", "-") else "0"

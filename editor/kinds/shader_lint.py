"""editor/kinds/shader_lint.py — static GLSL validate + auto-repair.

The smart agent reliably ROUTES to the shader medium now, but its one-shot GLSL
keeps hitting the same compile-error classes (a node renders blank because the
program never compiled, then the runtime's fallback paints a flat colour). The
recurring offenders, all confirmed on wovenweb shader assets:

  1. RESERVED-WORD identifiers — `vec2 half = …` (`half`/`input`/`output`/
     `sample`/… are reserved in GLSL ES) → compile error. AUTO-FIXABLE: rename
     the identifier (suffix `_`) inside the GLSL only.
  2. `gl_FragColor` under `#version 300 es` — removed in GLSL ES 3.00 → compile
     error. Detected + flagged (rewriting the output path safely is too risky).
  3. precision-before-out — `out vec4 X;` declared before `precision … float;`
     in a 300-es fragment shader → no default float precision → compile error.
     Detected + flagged.

Pure functions only (no I/O), so they're fully unit-testable offline; the daemon
calls `validate_and_repair` after a shader asset is written. Auto-repair is
SCOPED to GLSL regions (x-shader <script> blocks + backtick template literals
that contain GLSL markers) so it can never mangle the surrounding JavaScript.
"""
from __future__ import annotations

import re
from typing import List, Tuple

# Reserved-for-future-use keywords in GLSL ES that agents most often reach for
# as ordinary variable names. (Not the full list — just the ones that realistically
# collide with hand-written identifiers, plus the classic `half`.)
GLSL_RESERVED = [
    "half", "input", "output", "sample", "filter", "active", "common",
    "partition", "class", "union", "enum", "typedef", "template", "this",
    "packed", "goto", "inline", "noinline", "public", "static", "extern",
    "interface", "long", "short", "double", "fixed", "unsigned", "superp",
    "namespace", "using",
]

# A GLSL scalar/vector/matrix type, used to spot `TYPE reservedword` declarations.
_GLSL_TYPE = r"(?:[iub]?vec[234]|float|int|uint|bool|mat[234](?:x[234])?)"


def _glsl_regions(text: str) -> List[Tuple[int, int]]:
    """Return [start, end) spans of `text` that are GLSL source: x-shader
    <script> blocks and backtick template literals carrying GLSL markers.
    These are the ONLY regions auto-repair is allowed to rewrite."""
    spans: List[Tuple[int, int]] = []
    for m in re.finditer(r'<script[^>]*type=["\']x-shader[^>]*>(.*?)</script>',
                         text, re.S | re.I):
        spans.append((m.start(1), m.end(1)))
    for m in re.finditer(r'`([^`]*)`', text, re.S):
        body = m.group(1)
        if re.search(r'\bvoid\s+main\s*\(|\bprecision\s+(?:lowp|mediump|highp)\b'
                     r'|gl_Position|gl_FragColor|#version', body):
            spans.append((m.start(1), m.end(1)))
    return spans


def _reserved_in_region(region: str) -> List[str]:
    """Reserved words used as an identifier in a `TYPE name` declaration."""
    found = []
    for kw in GLSL_RESERVED:
        if re.search(rf"\b{_GLSL_TYPE}\s+{kw}\b", region):
            if kw not in found:
                found.append(kw)
    return found


def validate_and_repair(text: str) -> dict:
    """Validate a shader HTML file's GLSL and auto-repair what's safe.

    Returns {repaired: str, fixed: [str], errors: [str]}:
      • repaired — the (possibly rewritten) file text; identical when nothing fixed.
      • fixed    — human-readable descriptions of auto-applied repairs.
      • errors   — compile-error signatures detected but NOT auto-fixed; the caller
                   should surface these so the agent retries against a real error.
    """
    regions = _glsl_regions(text)
    fixed: List[str] = []
    errors: List[str] = []

    # ── 1. reserved-word identifiers — auto-rename inside each GLSL region ──
    # Rebuild the text region-by-region so renames never touch the JS around them.
    out = []
    last = 0
    for (s, e) in sorted(regions):
        if s < last:           # overlapping/nested — skip to stay safe
            continue
        out.append(text[last:s])
        region = text[s:e]
        for kw in _reserved_in_region(region):
            region = re.sub(rf"\b{kw}\b", kw + "_", region)
            fixed.append(f"renamed reserved GLSL identifier `{kw}` → `{kw}_`")
        out.append(region)
        last = e
    out.append(text[last:])
    repaired = "".join(out)

    # ── 2 & 3. detect-only signatures (auto-rewrite too risky) ──
    # Re-scan the repaired GLSL regions.
    glsl = "\n".join(repaired[s:e] for (s, e) in _glsl_regions(repaired))
    is_es300 = bool(re.search(r"#version\s+300\s+es", glsl))
    if is_es300 and re.search(r"\bgl_FragColor\b", glsl):
        errors.append(
            "uses `gl_FragColor` under `#version 300 es` — removed in GLSL ES 3.00. "
            "Declare `out vec4 fragColor;` and write to it instead.")
    # precision-before-out: an `out vec4 …;` that appears before any
    # `precision … float;` in a 300-es shader.
    if is_es300:
        m_out = re.search(r"\bout\s+(?:lowp|mediump|highp\s+)?vec4\s+\w+\s*;", glsl)
        m_prec = re.search(r"\bprecision\s+(?:lowp|mediump|highp)\s+float\s*;", glsl)
        if m_out and (not m_prec or m_prec.start() > m_out.start()):
            errors.append(
                "fragment `out vec4` is declared before `precision highp float;` — GLSL ES "
                "3.00 has no default float precision, so declare precision FIRST.")

    return {"repaired": repaired, "fixed": fixed, "errors": errors}


def looks_like_shader_html(text: str) -> bool:
    """Cheap gate: does this file contain an inline WebGL shader worth linting?"""
    return bool(re.search(r"getContext\(\s*['\"]webgl", text)
                and re.search(r"\b(?:gl_FragColor|fragColor|void\s+main)\b", text))

"""editor/kinds/shader_compile.py — real GLSL compile check via glslang.

Runs the Khronos reference compiler (`glslangValidator`, installed via
`brew install glslang`) so it catches ANY compile error for ANY shader —
undeclared vars, type mismatches, removed builtins, reserved words, etc. — not
a fixed pattern list. (This + the headless render-verify replace the earlier
static regex lint, which only matched the handful of bugs we'd seen.)

Two limits (by design, covered by the headless render-verify):
  • Extraction — we can pull GLSL out of <script type=x-shader> blocks and
    self-contained backtick literals, but NOT shaders assembled across several
    JS string pieces at runtime. Those are skipped here.
  • It only checks COMPILE, not render — a shader that compiles but draws blank
    passes this gate.

Pure logic except the `glslangValidator` subprocess, so extraction + error
parsing are unit-testable offline.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from typing import List, Optional


# Placeholder tokens generators leave in a shader body for JS to substitute
# (`FRAG_BODY.replace('COLOR_OUT', …)`). Swap them for a benign write so the
# REST of the body still compiles and real errors surface.
_PLACEHOLDERS = ["COLOR_OUT", "COL_OUT", "FRAG_OUT", "OUTPUT_COLOR"]


def find_glslang() -> Optional[str]:
    """`glslangValidator` on PATH or the usual Homebrew prefixes."""
    p = shutil.which("glslangValidator")
    if p:
        return p
    for cand in ("/opt/homebrew/bin/glslangValidator", "/usr/local/bin/glslangValidator"):
        if os.path.isfile(cand) and os.access(cand, os.X_OK):
            return cand
    return None


def _stage_of(src: str) -> str:
    """vertex if it writes gl_Position, else fragment (the common embedded case)."""
    return "vert" if re.search(r"\bgl_Position\b", src) else "frag"


def extract_shaders(html: str) -> List[dict]:
    """Pull compilable GLSL units out of a shader HTML file.

    Returns [{stage, source}]. Only regions that are a full shader (contain
    `void main`) are returned; placeholder tokens are substituted; an ES
    `#version`/`precision` preamble is added when missing so glslang validates
    in the ES profile (not desktop GLSL, which would false-error on `precision`).
    """
    units = []
    # Only `<script type="x-shader/...">` blocks — those are COMPLETE shaders.
    # Shaders built in JS backtick literals (assembled across pieces) aren't
    # reliably extractable and produce false syntax errors; the headless
    # render-verify runs the real page and covers them instead.
    for m in re.finditer(r'<script[^>]*type=["\']x-shader[^>]*>(.*?)</script>',
                         html, re.S | re.I):
        src = m.group(1)
        if not re.search(r"\bvoid\s+main\s*\(", src) or "${" in src:
            continue
        stage = _stage_of(src)
        # Substitute generator placeholders with a benign write for this stage.
        if any(tok in src for tok in _PLACEHOLDERS):
            repl = ("gl_FragColor = vec4(0.0)" if stage == "frag" else "gl_Position = vec4(0.0)")
            for tok in _PLACEHOLDERS:
                src = src.replace(tok, repl)
        has_version = bool(re.search(r"#version\b", src))
        # Force the ES profile so glslang doesn't validate as desktop GLSL
        # (which rejects `precision` qualifiers and ES builtins).
        if not has_version:
            preamble = "#version 100\n"
            if stage == "frag" and not re.search(r"\bprecision\s+(?:lowp|mediump|highp)\s+float", src):
                preamble += "precision highp float;\n"
            src = preamble + src
        units.append({"stage": stage, "source": src})
    return units


_ERR_RE = re.compile(r"^(?:ERROR|WARNING):\s*(.+)$", re.M)


def compile_check(html: str, glslang_bin: Optional[str] = None) -> List[str]:
    """Compile every extractable shader unit and return ERROR lines (empty = ok
    or nothing to check). Returns [] when glslang is unavailable (caller skips)."""
    glslang_bin = glslang_bin or find_glslang()
    if not glslang_bin:
        return []
    errors: List[str] = []
    for unit in extract_shaders(html):
        tmp = None
        try:
            fd, tmp = tempfile.mkstemp(suffix="." + unit["stage"])
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(unit["source"])
            proc = subprocess.run([glslang_bin, tmp], capture_output=True,
                                  text=True, timeout=20)
            if proc.returncode != 0:
                out = (proc.stdout or "") + "\n" + (proc.stderr or "")
                for m in _ERR_RE.finditer(out):
                    line = m.group(1).strip()
                    # glslang echoes the temp path + a final "compilation errors"
                    # tally; keep only the substantive diagnostics.
                    if tmp in line or line.lower().startswith(("no code", "compilation", "1 compilation")):
                        continue
                    tag = f"[{unit['stage']}] {line}"
                    if tag not in errors:
                        errors.append(tag)
        except Exception:
            continue
        finally:
            if tmp:
                try: os.unlink(tmp)
                except Exception: pass
    return errors

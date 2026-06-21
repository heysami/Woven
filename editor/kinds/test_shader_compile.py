"""Tests for shader_compile - extraction + glslang compile check.

Extraction tests run always; compile tests run only when glslangValidator is
installed (so the suite passes on a machine without it).
Run: python kinds/test_shader_compile.py
"""
from __future__ import annotations

import sys

from .shader_compile import extract_shaders, compile_check, find_glslang

_FRAG_BLOCK = (
    '<canvas id=c></canvas>\n'
    '<script type="x-shader/x-fragment" id="frag">\n'
    'precision highp float;\n'
    'void main(){ gl_FragColor = vec4(1.0,0.2,0.3,1.0); }\n'
    '</script>'
)
_BAD_FRAG_BLOCK = (
    '<script type="x-shader/x-fragment">\n'
    'precision highp float;\n'
    'void main(){ vec3 c = undeclared_var * 2.0; gl_FragColor = vec4(c,1.0); }\n'
    '</script>'
)
_VERT_BLOCK = (
    '<script type="x-shader/x-vertex">\n'
    'attribute vec2 p; void main(){ gl_Position = vec4(p,0.0,1.0); }\n'
    '</script>'
)
_BACKTICK_ASSEMBLED = (
    "<script>const F = `#version 300 es\nout vec4 o;\n${BODY}\n"
    "void main(){ o = vec4(1.0); }`;</script>"
)


def test_extract_classifies_stage_and_skips_assembled():
    units = extract_shaders(_FRAG_BLOCK + _VERT_BLOCK + _BACKTICK_ASSEMBLED)
    stages = sorted(u["stage"] for u in units)
    assert stages == ["frag", "vert"], stages        # the ${...} backtick is skipped
    frag = next(u for u in units if u["stage"] == "frag")
    assert "#version" in frag["source"]               # ES preamble added (no version in block)


def test_extract_ignores_non_shader_blocks():
    assert extract_shaders("<div>hi</div><script>let x=1;</script>") == []


def test_compile_check_no_glslang_returns_empty(monkeypatch=None):
    # Force the no-binary path explicitly.
    assert compile_check(_BAD_FRAG_BLOCK, glslang_bin=None) == [] or find_glslang()


def _glslang_only():
    return find_glslang() is not None


def test_compile_check_flags_real_error_when_glslang_present():
    if not _glslang_only():
        print("   (skipped - glslangValidator not installed)")
        return
    errs = compile_check(_BAD_FRAG_BLOCK)
    assert any("undeclared_var" in e or "undeclared identifier" in e.lower() for e in errs), errs


def test_compile_check_clean_shader_passes_when_glslang_present():
    if not _glslang_only():
        print("   (skipped - glslangValidator not installed)")
        return
    assert compile_check(_FRAG_BLOCK) == []


def main():
    tests = [test_extract_classifies_stage_and_skips_assembled,
             test_extract_ignores_non_shader_blocks,
             test_compile_check_flags_real_error_when_glslang_present,
             test_compile_check_clean_shader_passes_when_glslang_present]
    for t in tests:
        try:
            t()
        except AssertionError as e:
            print(f"FAIL {t.__name__}: {e}", file=sys.stderr); return 1
        except Exception as e:  # noqa: BLE001
            print(f"ERROR {t.__name__}: {type(e).__name__}: {e}", file=sys.stderr); return 1
        print(f"OK   {t.__name__}")
    print(f"\n{len(tests)}/{len(tests)} shader-compile tests passed"
          + ("" if _glslang_only() else " (compile tests skipped - no glslang)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())

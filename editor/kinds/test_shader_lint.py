"""Unit tests for shader_lint — the static GLSL validate/auto-repair pass.

Fixtures mirror the exact compile-error classes seen on wovenweb shader assets.
Run: python kinds/test_shader_lint.py
"""
from __future__ import annotations

import sys

from .shader_lint import validate_and_repair, looks_like_shader_html


def test_reserved_word_half_autofixed_in_glsl_only():
    """`half` (reserved) declared in a GLSL template literal gets renamed —
    but an identically-named JS variable OUTSIDE the GLSL must NOT change."""
    text = (
        "<canvas id=gl></canvas><script>\n"
        "let input = 5;\n"                       # JS var named like a reserved word
        "const FRAG = `#version 300 es\n"
        "precision highp float;\n"
        "out vec4 fragColor;\n"
        "void main(){ vec2 half = vec2(0.3,0.1); fragColor = vec4(half,0.0,1.0); }`;\n"
        "</script>"
    )
    r = validate_and_repair(text)
    assert any("half" in f for f in r["fixed"]), r
    # GLSL `half` renamed everywhere inside the literal
    assert "vec2 half_" in r["repaired"]
    assert "vec4(half_,0.0,1.0)" in r["repaired"]
    assert "vec2 half " not in r["repaired"]
    # JS `input` untouched (it's outside any GLSL region, not a TYPE decl anyway)
    assert "let input = 5;" in r["repaired"]


def test_gl_fragcolor_under_300_flagged():
    text = (
        "<script>const F = `#version 300 es\nprecision highp float;\n"
        "void main(){ gl_FragColor = vec4(1.0); }`;</script>"
    )
    r = validate_and_repair(text)
    assert any("gl_FragColor" in e for e in r["errors"]), r
    # not auto-fixed
    assert not r["fixed"]


def test_precision_after_out_autofixed():
    text = (
        "<script>const F = `#version 300 es\nout vec4 fragColor;\n"
        "void main(){ fragColor = vec4(1.0); }`;</script>"
    )
    r = validate_and_repair(text)
    assert any("precision" in f for f in r["fixed"]), r
    # precision now precedes the out declaration
    assert r["repaired"].index("precision highp float;") < r["repaired"].index("out vec4 fragColor;")
    # and it no longer trips the error path
    assert not r["errors"], r


def test_dual_path_webgl1_and_webgl2_not_flagged():
    """A file that ships BOTH a WebGL1 variant (gl_FragColor, no #version) and a
    WebGL2 variant (#version 300 es, out vec4) in SEPARATE literals is correct —
    must NOT be flagged (the cross-region false-positive regression)."""
    text = (
        "<script>\n"
        "const FRAG2 = `#version 300 es\nprecision highp float;\nout vec4 fragColor;\n"
        "void main(){ fragColor = vec4(1.0); }`;\n"
        "const FRAG1 = `precision highp float;\nvoid main(){ gl_FragColor = vec4(1.0); }`;\n"
        "const gl = c.getContext('webgl2');</script>"
    )
    r = validate_and_repair(text)
    assert not r["errors"], r
    assert not r["fixed"], r


def test_clean_shader_untouched():
    text = (
        "<script>const F = `#version 300 es\nprecision highp float;\n"
        "out vec4 fragColor;\nvoid main(){ vec2 sz = vec2(0.3); fragColor = vec4(sz,0.0,1.0); }`;"
        "\nconst gl = c.getContext('webgl2');</script>"
    )
    r = validate_and_repair(text)
    assert not r["fixed"] and not r["errors"], r
    assert r["repaired"] == text


def test_looks_like_shader_html():
    assert looks_like_shader_html(
        "x=getContext('webgl2'); ... void main(){}")
    assert not looks_like_shader_html("<div>just html</div>")


def main():
    tests = [test_reserved_word_half_autofixed_in_glsl_only,
             test_gl_fragcolor_under_300_flagged,
             test_precision_after_out_autofixed,
             test_dual_path_webgl1_and_webgl2_not_flagged,
             test_clean_shader_untouched,
             test_looks_like_shader_html]
    for t in tests:
        try:
            t()
        except AssertionError as e:
            print(f"FAIL {t.__name__}: {e}", file=sys.stderr); return 1
        except Exception as e:  # noqa: BLE001
            print(f"ERROR {t.__name__}: {type(e).__name__}: {e}", file=sys.stderr); return 1
        print(f"OK   {t.__name__}")
    print(f"\n{len(tests)}/{len(tests)} shader-lint tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

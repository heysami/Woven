"""Routing-pattern smoke test for the v3.0 asset-versioning endpoints.

Validates that every URL we promise in docs/features/asset-versioning.md §7.2
matches one of the regex patterns in serve.py's do_POST / do_DELETE. Doesn't
spin up an HTTP server — just exercises the regex set.

Run: python kinds/test_routing.py
"""
from __future__ import annotations

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SERVE = os.path.join(os.path.dirname(HERE), "serve.py")


def extract_regexes(method_def_name: str) -> list:
    """Pull every `re.match(r"...", parsed.path)` literal out of the given
    method body so we can replay them against canned URLs.
    """
    text = open(SERVE, encoding="utf-8").read()
    # Find the method body.
    pat = re.compile(rf"^    def {method_def_name}\(self\):\n(.+?)(?=^    def )",
                     re.S | re.M)
    m = pat.search(text)
    if not m:
        raise RuntimeError(f"could not find method {method_def_name}")
    body = m.group(1)
    # Capture re.match(r"..."...) literals (raw strings).
    out = []
    for m2 in re.finditer(r're\.match\(\s*(rf?"[^"]+")\s*,\s*parsed\.path\s*\)', body):
        out.append(m2.group(1))
    return out


def render_pattern(literal: str) -> str:
    """Eval the f-string portion of the regex literal in a stub scope so
    rf-string substitution (_NID, _VID) resolves the same way serve.py does."""
    _NID = r"[A-Za-z0-9_.-]{1,80}"
    _VID = r"[A-Za-z0-9_-]{1,64}"
    return eval(literal, {"_NID": _NID, "_VID": _VID})


URLS_POST = [
    # Version-level
    ("/__workflow/node/bs_html_1/version/branch", True),
    ("/__workflow/node/bs_html_1/version/01HXYZAB123/revert", True),
    ("/__workflow/node/bs_html_1/version/01HXYZAB123/pin", True),
    ("/__workflow/node/bs_html_1/version/01HXYZAB123/label", True),
    ("/__workflow/node/bs_html_1/version/01HXYZAB123/thumb", True),
    # Composition-level
    ("/__workflow/node/bs_html_1/version/01HXYZAB123/composition", True),
    ("/__workflow/node/bs_html_1/version/01HXYZAB123/composition/01CDEF456/switch", True),
    ("/__workflow/node/bs_html_1/version/01HXYZAB123/composition/01CDEF456/pin", True),
    ("/__workflow/node/bs_html_1/version/01HXYZAB123/composition/01CDEF456/label", True),
    ("/__workflow/node/bs_html_1/version/01HXYZAB123/composition/01CDEF456/thumb", True),
    # Size
    ("/__workflow/node/bs_html_1/size", True),
    # Negative cases
    ("/__workflow/node/bs_html_1/composition/01CDEF456/switch", False),  # missing version
    ("/__workflow/node/bs_html_1/version/", False),
    ("/__bogus/path", False),
]

URLS_DELETE = [
    ("/__workflow/node/bs_html_1/version/01HXYZAB123", True),
    ("/__workflow/node/bs_html_1/version/01HXYZAB123/composition/01CDEF456", True),
    ("/__workflow/node/bs_html_1/version/01HXYZAB123/composition", False),  # missing cid
]


def matches_any(url: str, patterns: list) -> bool:
    for p in patterns:
        if re.match(p, url):
            return True
    return False


def test_post_routes():
    raw_patterns = extract_regexes("do_POST")
    versioning_patterns = []
    for raw in raw_patterns:
        try:
            rendered = render_pattern(raw)
        except Exception:
            continue
        if "version" in rendered or "size$" in rendered:
            versioning_patterns.append(rendered)
    assert len(versioning_patterns) >= 11, \
        f"expected ≥11 versioning POST routes, found {len(versioning_patterns)}"

    failures = []
    for url, should_match in URLS_POST:
        actual = matches_any(url, versioning_patterns)
        if actual != should_match:
            failures.append(f"  {url} expected={should_match} got={actual}")
    if failures:
        raise AssertionError("URL routing mismatches:\n" + "\n".join(failures))


def test_delete_routes():
    raw_patterns = extract_regexes("do_DELETE")
    patterns = [render_pattern(r) for r in raw_patterns]
    assert len(patterns) >= 2, f"expected ≥2 DELETE routes, found {len(patterns)}"

    failures = []
    for url, should_match in URLS_DELETE:
        actual = matches_any(url, patterns)
        if actual != should_match:
            failures.append(f"  {url} expected={should_match} got={actual}")
    if failures:
        raise AssertionError("DELETE routing mismatches:\n" + "\n".join(failures))


def main():
    tests = [test_post_routes, test_delete_routes]
    for t in tests:
        try:
            t()
        except AssertionError as e:
            print(f"FAIL {t.__name__}: {e}", file=sys.stderr); return 1
        except Exception as e:
            print(f"ERROR {t.__name__}: {type(e).__name__}: {e}", file=sys.stderr); return 1
        print(f"OK   {t.__name__}")
    print(f"\n{len(tests)}/{len(tests)} routing tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

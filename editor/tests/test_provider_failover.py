"""Contract test for provider failover on availability failures.

Background - a build generating a nine-scene film ran the fal balance to zero
mid-run and stopped dead, with a Higgsfield key wired, idle, and perfectly able
to render the remaining clips. `/__asset_generate` turned the 402 into a flat
502 and no caller had anywhere to go. The only fallback that existed
(`_VIDEO_T2V_PROVIDER_FALLBACK`) is a CAPABILITY fallback that fires before the
call, and its single entry is fal - so it could only ever fall back TO fal.

What is worth pinning here is the DECISION, not the HTTP: which failures are
worth rerouting, and which provider the ladder picks next. Both are easy to
regress silently - a widened status set that starts rerouting content refusals
burns a second provider's credit to reproduce the same error, and a ladder that
stops filtering on capability sends prompt-only video to an image-to-video-only
provider that can only raise "needs a start frame".

No transport is touched and no key is required: the classifier takes an
exception, and the ladder takes the dispatch registry plus the model catalog.
Nothing here spends credits or makes a network call.

Run: `python3 editor/tests/test_provider_failover.py` (no pytest required).
Exit 0 on pass, non-zero on any failure.
"""

import io
import os
import sys
import traceback
import urllib.error

# Make `import serve` resolve from editor/ when this file is run directly.
_HERE = os.path.dirname(os.path.abspath(__file__))
_EDITOR = os.path.dirname(_HERE)
sys.path.insert(0, _EDITOR)

import serve  # noqa: E402  - import after sys.path mutation

FAILURES = []


def check(name, cond, detail=""):
    if cond:
        print("  ok   " + name)
    else:
        print("  FAIL " + name + (("  -> " + detail) if detail else ""))
        FAILURES.append(name)


def _http(code, body):
    return urllib.error.HTTPError("http://x", code, "err", {},
                                  io.BytesIO(body.encode("utf-8")))


def _wire(*providers):
    """Pretend exactly these providers have a live key."""
    keyed = set(providers)
    serve._resolve_provider_key = lambda pid: ("key-" + pid) if pid in keyed else None


def test_classifier_reroutes_availability():
    """Out of credit / quota / rate limit are worth trying elsewhere."""
    print("classifier - availability failures reroute")
    cases = [
        ("fal exhausted balance (403 + wording)",
         _http(403, '{"detail":"Exhausted balance. Please top up."}')),
        ("payment required (402)", _http(402, '{"detail":"payment required"}')),
        ("rate limited (429)", _http(429, '{"detail":"Too Many Requests"}')),
        ("insufficient credits inside a queue RuntimeError",
         RuntimeError("fal queue: request FAILED: insufficient credits")),
        ("quota wording on a 500", _http(500, '{"error":"monthly quota exceeded"}')),
    ]
    for name, exc in cases:
        check(name, serve._availability_failure_reason(exc) is not None)


def test_classifier_holds_request_failures():
    """A bad request fails identically everywhere - rerouting it would just
    bill a second provider to reproduce the same error."""
    print("classifier - request/content failures do NOT reroute")
    cases = [
        ("malformed prompt (400)", _http(400, '{"detail":"prompt too long"}')),
        ("aspect validation (422)",
         _http(422, '{"detail":[{"msg":"Input should be 16:9 or 9:16"}]}')),
        ("content refusal in a queue RuntimeError",
         RuntimeError("fal queue: request FAILED: flagged as nsfw")),
        ("plain 404", _http(404, '{"detail":"model not found"}')),
    ]
    for name, exc in cases:
        check(name, serve._availability_failure_reason(exc) is None)


def test_video_ladder_finds_higgsfield():
    """The exact case that stalled the film: fal dies on an i2v video request
    and Higgsfield DoP is keyed."""
    print("ladder - video with a start frame")
    _wire("fal", "higgsfield")
    lad = serve._failover_ladder(
        "video-gen", "fal", "fal-ai/kling-video/v3/pro/image-to-video", "k", "i2v")
    check("caller's own pick is entry 0, untouched",
          lad[0][0] == "fal" and lad[0][1] == "fal-ai/kling-video/v3/pro/image-to-video")
    check("higgsfield is the next candidate", any(p == "higgsfield" for p, _m, _k in lad),
          detail=repr([(p, m) for p, m, _ in lad]))
    hf = [(p, m) for p, m, _ in lad if p == "higgsfield"]
    check("and it carries a real DoP model id, not a blank",
          bool(hf and hf[0][1]), detail=repr(hf))


def test_prompt_only_video_skips_i2v_only_provider():
    """Higgsfield DoP is image-to-video ONLY. Rerouting a prompt-only request
    onto it just raises 'needs a start frame' - the capability filter is what
    stops that, so pin it."""
    print("ladder - prompt-only video")
    _wire("fal", "higgsfield")
    lad = serve._failover_ladder("video-gen", "fal", "fal-ai/veo3.1", "k", "t2v")
    check("higgsfield is NOT a candidate without a start frame",
          all(p != "higgsfield" for p, _m, _k in lad),
          detail=repr([(p, m) for p, m, _ in lad]))


def test_ladder_only_offers_keyed_providers():
    print("ladder - unkeyed providers are never candidates")
    _wire("fal")
    lad = serve._failover_ladder("video-gen", "fal", "fal-ai/veo3.1", "k", "t2v")
    check("no key anywhere else leaves the ladder at just the caller's pick",
          len(lad) == 1, detail=repr([(p, m) for p, m, _ in lad]))


def test_ladder_derives_from_dispatch_registry():
    """The ladder is built from _GENERATE_DISPATCH / _TRANSFORM_DISPATCH so a
    newly wired provider becomes a failover target with no table to update -
    and a provider with no renderer for the skill never appears."""
    print("ladder - derived from the dispatch registry")
    _wire("openai", "fal", "bfl", "higgsfield", "elevenlabs")
    lad = serve._failover_ladder("generate-image", "openai", "gpt-image-2", "k", None)
    got = [p for p, _m, _k in lad]
    check("image ladder reaches other image providers", len(got) > 1, detail=repr(got))
    check("every candidate has a generate-image renderer",
          all(("generate-image", p) in serve._GENERATE_DISPATCH for p in got),
          detail=repr(got))
    check("elevenlabs (audio-only, no image renderer) is never offered",
          "elevenlabs" not in got, detail=repr(got))


def test_catalog_model_respects_caps():
    print("catalog - model resolution honours the requested capability")
    check("higgsfield has an i2v video model", bool(
        serve._catalog_model_for("video-gen", "higgsfield", "i2v")))
    check("higgsfield has NO t2v video model", not
          serve._catalog_model_for("video-gen", "higgsfield", "t2v"))
    check("fal resolves a t2v model", bool(
        serve._catalog_model_for("video-gen", "fal", "t2v")))
    check("unknown skill resolves to nothing rather than guessing",
          serve._catalog_model_for("not-a-skill", "fal", None) == "")


def main():
    _orig_key = serve._resolve_provider_key
    tests = [
        test_classifier_reroutes_availability,
        test_classifier_holds_request_failures,
        test_video_ladder_finds_higgsfield,
        test_prompt_only_video_skips_i2v_only_provider,
        test_ladder_only_offers_keyed_providers,
        test_ladder_derives_from_dispatch_registry,
        test_catalog_model_respects_caps,
    ]
    try:
        for t in tests:
            try:
                t()
            except Exception:
                FAILURES.append(t.__name__ + " raised")
                traceback.print_exc()
            print()
    finally:
        serve._resolve_provider_key = _orig_key

    if FAILURES:
        print("FAIL - %d assertion(s) failed:" % len(FAILURES))
        for f in FAILURES:
            print("  - " + f)
        sys.exit(1)
    print("PASS - provider failover reroutes availability failures only, "
          "and only onto providers that can actually serve the request")


if __name__ == "__main__":
    main()

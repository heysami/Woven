"""Contract test for the image providers wired in July 2026.

Background - xAI, Volcengine Ark, Black Forest Labs and Gemini each had a row
in media-models.js, a key slot in Settings, and a line in the README, but NO
entry in `_GENERATE_DISPATCH`. Every call returned
`400 no renderer for skill='generate-image' provider='bfl'`. Higgsfield was
half-wired: DoP (image->video) ran, Soul (text->image) did not, though both
ride the same key.

Each renderer talks to a different shape of API - OpenAI-style sync JSON (xai,
volcengine), submit+poll with a signed result URL (bfl, higgsfield soul), and
Gemini's interactions route with a fallback to :generateContent - so the thing
worth pinning is not "does it return bytes" but the request each one builds and
the response path each one reads. Those came from the vendors' own docs; this
file is where a doc drift or a careless refactor gets caught, since none of
these can be exercised without a paid key.

The transport is faked: `urlopen` is routed to canned payloads and
`_download_bytes` is stubbed, so this test makes no network calls and spends no
credits.

Run: `python3 editor/tests/test_image_providers.py` (no pytest required).
Exit 0 on pass, non-zero on any failure.
"""

import base64
import io
import json
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
PNG = b"\x89PNG-fake-bytes"
LONG_B64 = base64.b64encode(PNG * 40).decode()   # >256 chars, reads as image data

CALLS = []      # every request the renderer made, in order
ROUTES = {}     # url prefix -> payload dict | callable(req) -> payload | Exception


class _Resp:
    def __init__(self, payload):
        self._b = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._b

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _fake_urlopen(req, timeout=None):
    CALLS.append({
        "url":     req.full_url,
        "method":  req.method,
        "headers": dict(req.headers),
        "body":    json.loads(req.data.decode("utf-8")) if req.data else None,
    })
    for prefix, payload in ROUTES.items():
        if req.full_url.startswith(prefix):
            out = payload(req) if callable(payload) else payload
            if isinstance(out, Exception):
                raise out
            return _Resp(out)
    raise AssertionError("renderer called an unrouted URL: " + req.full_url)


def _install_fakes():
    serve.urllib.request.urlopen = _fake_urlopen
    serve._download_bytes = lambda url, timeout=None: (
        CALLS.append({"download": url}) or PNG)
    serve.time.sleep = lambda s: None       # poll loops run instantly


def _reset(routes):
    CALLS[:] = []
    ROUTES.clear()
    ROUTES.update(routes)


def check(name, cond, detail=""):
    if cond:
        print("  ok   " + name)
    else:
        print("  FAIL " + name + (("  -> " + detail) if detail else ""))
        FAILURES.append(name)


def test_dispatch_entries_exist():
    """The whole bug was a missing dispatch key, so pin the keys themselves."""
    print("dispatch table")
    for provider in ("xai", "volcengine", "bfl", "nanobanana", "higgsfield"):
        check(f"generate-image is wired for {provider}",
              ("generate-image", provider) in serve._GENERATE_DISPATCH)


def test_xai():
    print("xai")
    _reset({"https://api.x.ai/v1/images/generations":
            {"data": [{"b64_json": base64.b64encode(PNG).decode()}]}})
    out = serve._xai_generate_image("k", "a cat", "", "16:9", None)
    c = CALLS[0]
    check("posts to the documented endpoint",
          c["url"] == "https://api.x.ai/v1/images/generations", c["url"])
    check("Bearer auth", c["headers"].get("Authorization") == "Bearer k")
    check("defaults to the documented model id",
          c["body"]["model"] == "grok-imagine-image-quality", str(c["body"]))
    # The endpoint documents no size/aspect field; sending one risks a 422.
    check("sends no size/aspect field",
          not any(k in c["body"] for k in ("size", "aspect_ratio", "width")))
    check("decodes b64_json", out == PNG)


def test_volcengine():
    print("volcengine")
    _reset({"https://ark.cn-beijing.volces.com": {"data": [{"url": "https://cdn/x.png"}]}})
    out = serve._volcengine_generate_image("k", "a cat", None, "9:16", {"seed": 7})
    c = CALLS[0]
    check("Ark images endpoint", c["url"].endswith("/api/v3/images/generations"), c["url"])
    check("portrait aspect maps to a portrait size",
          c["body"]["size"] == "1440x2560", str(c["body"].get("size")))
    # A watermarked asset is not usable in a prototype.
    check("watermark off by default", c["body"]["watermark"] is False)
    check("options pass through", c["body"]["seed"] == 7)
    check("downloads data[0].url when no b64 came back",
          CALLS[-1].get("download") == "https://cdn/x.png" and out == PNG)


def test_bfl_submit_and_poll():
    print("bfl")
    state = {"polls": 0}

    def poll(req):
        state["polls"] += 1
        if state["polls"] < 2:
            return {"status": "Pending"}
        return {"status": "Ready", "result": {"sample": "https://bfl/out.png"}}

    _reset({
        "https://api.bfl.ai/v1/flux-2-pro-preview": {"id": "j1", "polling_url": "https://api.bfl.ai/poll/j1"},
        "https://api.bfl.ai/poll/j1": poll,
    })
    out = serve._bfl_generate_image("k", "a cat", "flux-2-pro-preview", "3:2", None)
    check("the model id IS the endpoint path segment",
          CALLS[0]["url"] == "https://api.bfl.ai/v1/flux-2-pro-preview", CALLS[0]["url"])
    # BFL authenticates with x-key, NOT a bearer token.
    check("x-key header, not Authorization",
          CALLS[0]["headers"].get("X-key") == "k" and "Authorization" not in CALLS[0]["headers"],
          str(CALLS[0]["headers"]))
    w, h = CALLS[0]["body"]["width"], CALLS[0]["body"]["height"]
    check("aspect maps to pixels that are multiples of 32",
          (w, h) == (1728, 1152) and w % 32 == 0 and h % 32 == 0, f"{w}x{h}")
    check("polls until Ready, then downloads result.sample",
          state["polls"] == 2 and CALLS[-1].get("download") == "https://bfl/out.png" and out == PNG)


def test_bfl_moderation_raises():
    print("bfl (moderated)")
    _reset({
        "https://api.bfl.ai/v1/flux-pro-1.1": {"id": "j2", "polling_url": "https://api.bfl.ai/poll/j2"},
        "https://api.bfl.ai/poll/j2": {"status": "Content Moderated"},
    })
    try:
        serve._bfl_generate_image("k", "x", "flux-pro-1.1", "1:1", None)
        check("a moderated job raises instead of hanging to the deadline", False)
    except RuntimeError as e:
        check("a moderated job raises instead of hanging to the deadline",
              "moderated" in str(e).lower(), str(e))


def test_gemini_primary_and_fallback():
    print("nanobanana")
    _reset({"https://generativelanguage.googleapis.com/v1beta/interactions":
            {"steps": [{"content": [{"data": LONG_B64}]}]}})
    out = serve._gemini_generate_image("k", "a cat", None, "1:1", None)
    c = CALLS[0]
    check("interactions endpoint with x-goog-api-key",
          c["url"].endswith("/v1beta/interactions") and c["headers"].get("X-goog-api-key") == "k")
    check("defaults to the documented model id",
          c["body"]["model"] == "gemini-3.1-flash-image", str(c["body"]))
    check("reads steps[].content[].data", out == PNG * 40)

    # Gemini has moved this surface before - a 404 must fall back, not fail.
    _reset({
        "https://generativelanguage.googleapis.com/v1beta/interactions":
            urllib.error.HTTPError("u", 404, "gone", {}, io.BytesIO(b"")),
        "https://generativelanguage.googleapis.com/v1beta/models/":
            {"candidates": [{"content": {"parts": [
                {"inlineData": {"mimeType": "image/png", "data": LONG_B64}}]}}]},
    })
    out = serve._gemini_generate_image("k", "a cat", "gemini-3-pro-image", "1:1", None)
    check("404 on interactions falls back to :generateContent",
          len(CALLS) == 2 and CALLS[1]["url"].endswith("/models/gemini-3-pro-image:generateContent"),
          str([c["url"] for c in CALLS]))
    check("reads inlineData.data on the fallback shape", out == PNG * 40)
    # The walker keys on "data"; a mime string sits under a sibling short key.
    check("a short string is not mistaken for image data",
          serve._gemini_extract_image_b64(
              {"mimeType": "image/png", "data": LONG_B64}) == PNG * 40)


def test_higgsfield_soul():
    print("higgsfield soul")
    _reset({
        "https://platform.higgsfield.ai/v1/text2image/soul": {"id": "s1"},
        "https://platform.higgsfield.ai/requests/s1/status":
            {"status": "completed", "jobs": [{"results": {"raw": {"url": "https://hf/out.png"}}}]},
    })
    out = serve._higgsfield_generate_image(
        "kid:secret", "a cat", "higgsfield/soul", "9:16", {"custom_reference_id": "soul-7"})
    c = CALLS[0]
    check("soul endpoint, not the DoP one", c["url"].endswith("/v1/text2image/soul"), c["url"])
    check("Key auth with the key:secret pair",
          c["headers"].get("Authorization") == "Key kid:secret")
    check("aspect maps to a documented width_and_height",
          c["body"]["input"]["width_and_height"] == "1152x2048",
          str(c["body"]["input"].get("width_and_height")))
    # "higgsfield/soul" is a routing label; the API knows no such model.
    check("the namespaced catalog id is not forwarded as a model",
          "model" not in c["body"]["input"], str(c["body"]["input"]))
    check("a Soul ID passes through for character consistency",
          c["body"]["input"]["custom_reference_id"] == "soul-7")
    check("polls status, then downloads jobs[0].results.raw.url",
          CALLS[-1].get("download") == "https://hf/out.png" and out == PNG)


def test_dop_extractor_still_works():
    """Soul shares the job-set URL extractor with DoP; DoP must not regress."""
    print("higgsfield dop (shared extractor)")
    check("video url still resolves from the job set",
          serve._higgsfield_extract_video_url(
              {"jobs": [{"results": {"raw": {"url": "https://hf/v.mp4"}}}]}) == "https://hf/v.mp4")
    try:
        serve._higgsfield_extract_video_url({}, kind="image")
        check("the error names the asset kind it was looking for", False)
    except RuntimeError as e:
        check("the error names the asset kind it was looking for", "image" in str(e), str(e))


def main():
    _install_fakes()
    tests = [
        test_dispatch_entries_exist,
        test_xai,
        test_volcengine,
        test_bfl_submit_and_poll,
        test_bfl_moderation_raises,
        test_gemini_primary_and_fallback,
        test_higgsfield_soul,
        test_dop_extractor_still_works,
    ]
    for t in tests:
        try:
            t()
        except Exception:
            FAILURES.append(f"{t.__name__} raised")
            traceback.print_exc()
        print()

    if FAILURES:
        print(f"FAIL - {len(FAILURES)} assertion(s) failed:")
        for f in FAILURES:
            print(f"  - {f}")
        sys.exit(1)
    print("PASS - image-provider request/response contracts upheld")


if __name__ == "__main__":
    main()

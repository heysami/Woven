"""editor/typed_judge.py on recorded fixtures - no key, no network, no daemon.

docs/features/typed-judgment-providers.md. Every test runs against a private
copy of judges.json, an empty media-config and an empty compact-config, so a
key on the machine running the tests can never answer for one.

  P4 degradation per provider - absent key, 401, exhausted 429 and a malformed
     body each raise a catchable JudgeError for Jev, Clef, Local Clef and OpenAI.
  P6 adapter round trip - an OpenAI Decisions reply reads exactly like the
     System One reply for the same questions.
  P7 the Jev image upgrade is one number - raising maxImages on the jev row of a
     copy of judges.json puts Jev in the image tier with no other change.
"""

import base64
import io
import json
import os
from pathlib import Path
import shutil
import struct
import sys
import tempfile
import unittest
import urllib.error

EDITOR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EDITOR))

import typed_judge as tj  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"
SYSTEMONE = json.loads((FIXTURES / "jev_systemone_response.json").read_text(encoding="utf-8"))
OPENAI = json.loads((FIXTURES / "openai_decisions_response.json").read_text(encoding="utf-8"))
CLEF_REST = json.loads((FIXTURES / "clef_rest_response.json").read_text(encoding="utf-8"))

QUESTIONS = {
    "states_a_direction": {"type": "noul", "instructions": "This request states a visual direction.",
                           "criteria": {"true": "It names a style or a mood",
                                        "false": "It only describes function"}},
    "shell": {"type": "choice", "instructions": "Which shell does this request imply?",
              "criteria": {"three-column-app": "dense product UI",
                           "two-column-app": "list and detail",
                           "centered-narrow-column": "reading surface",
                           "bento-grid": "asymmetric marketing cells"}},
    "polish": {"type": "score", "instructions": "How considered is the visual polish?",
               "criteria": ["absent: no visual intent", "thin: defaults only",
                            "adequate: consistent", "considered: deliberate choices",
                            "exceptional: distinctive and coherent"]},
    "refused": {"type": "noul", "instructions": "The request is acceptable."},
}


class _Resp:
    def __init__(self, payload):
        self.body = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return self.body


class _Opener:
    """Stands in for urlopen. `reply` is a payload, an exception, or a
    callable(request) -> payload. Every request is kept so the wire shape is
    asserted rather than assumed."""

    def __init__(self, reply):
        self.reply = reply
        self.requests = []

    def __call__(self, req, timeout=None):
        self.requests.append(req)
        r = self.reply(req) if callable(self.reply) else self.reply
        if isinstance(r, BaseException):
            raise r
        return _Resp(r)

    def body(self, i=-1):
        return json.loads(self.requests[i].data.decode("utf-8"))


class Isolated(unittest.TestCase):
    """A private judges.json / media-config / compact-config / thresholds."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="typed-judge-test-")
        self.saved = {k: getattr(tj, k) for k in ("JUDGES_PATH", "MEDIA_CONFIG_PATH",
                                                   "COMPACT_CONFIG_PATH", "THRESHOLDS_PATH",
                                                   "SHADOW_LOG_PATH", "LABELS_PATH")}
        tj.JUDGES_PATH = os.path.join(self.tmp, "judges.json")
        shutil.copy(self.saved["JUDGES_PATH"], tj.JUDGES_PATH)
        tj.THRESHOLDS_PATH = os.path.join(self.tmp, "jev_thresholds.json")
        shutil.copy(self.saved["THRESHOLDS_PATH"], tj.THRESHOLDS_PATH)
        tj.MEDIA_CONFIG_PATH = os.path.join(self.tmp, "media-config.json")
        tj.COMPACT_CONFIG_PATH = os.path.join(self.tmp, "compact-config.json")
        tj.SHADOW_LOG_PATH = os.path.join(self.tmp, "shadow.jsonl")
        tj.LABELS_PATH = os.path.join(self.tmp, "labels.json")
        self.env = {k: os.environ.pop(k) for k in
                    list(tj.ENV_KEYS.values()) + list(tj.ACCOUNT_ENV.values())
                    + list(tj.ENDPOINT_ENV.values()) if k in os.environ}
        self.real_open = tj.urllib.request.urlopen
        self.real_sleep = tj.time.sleep
        tj.time.sleep = lambda _s: None

    def tearDown(self):
        tj.urllib.request.urlopen = self.real_open
        tj.time.sleep = self.real_sleep
        for k, v in self.saved.items():
            setattr(tj, k, v)
        os.environ.update(self.env)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def media(self, cfg):
        with open(tj.MEDIA_CONFIG_PATH, "w") as f:
            json.dump(cfg, f)

    def compact(self, cfg):
        with open(tj.COMPACT_CONFIG_PATH, "w") as f:
            json.dump(cfg, f)

    def judges(self, edit):
        doc = json.loads(Path(tj.JUDGES_PATH).read_text())
        edit({r["id"]: r for r in doc["providers"]})
        Path(tj.JUDGES_PATH).write_text(json.dumps(doc))

    def opener(self, reply):
        op = _Opener(reply)
        tj.urllib.request.urlopen = op
        return op


ALL_KEYED = {"typesafe": {"api_key": "ts"},
             "cloudflare": {"api_key": "cf", "account_id": "acct-1"},
             "clef_local": {"endpoint": "http://localhost:11434/v1/systemone"},
             "openai": {"api_key": "oa"}}


def png(w=4, h=4):
    return tj.solid_png((10, 200, 10), size=w) if w == h else None


# ── Routing ─────────────────────────────────────────────────────────────────

class Routing(Isolated):

    def test_nothing_keyed_is_unavailable_with_the_reason_the_endpoint_names(self):
        self.assertIsNone(tj.pick("text"))
        with self.assertRaises(tj.JudgeUnavailable) as ctx:
            tj.judge("x", {"q": QUESTIONS["refused"]})
        self.assertEqual(ctx.exception.reason, "no-key")
        with self.assertRaises(tj.JudgeUnavailable) as ctx:
            tj.judge("x", {"q": QUESTIONS["refused"]}, tier="image", images=[png()])
        self.assertEqual(ctx.exception.reason, "no-image-judge")

    def test_auto_follows_each_tiers_rank(self):
        self.media(ALL_KEYED)
        self.assertEqual(tj.pick("text"), "jev")
        self.assertEqual(tj.pick("image"), "clef")

    def test_jev_never_answers_an_image_request_while_its_cap_is_zero(self):
        self.media({"typesafe": {"api_key": "ts"}})
        self.assertEqual(tj.pick("text"), "jev")
        self.assertIsNone(tj.pick("image"))

    def test_the_users_choice_wins_when_it_is_set_up_and_capable(self):
        self.media(ALL_KEYED)
        self.compact({"typedJudgeTextProvider": "openai", "typedJudgeImageProvider": "clef-flash"})
        self.assertEqual(tj.pick("text"), "openai")
        self.assertEqual(tj.pick("image"), "clef-flash")

    def test_a_choice_that_is_not_set_up_falls_back_to_auto(self):
        self.media({"typesafe": {"api_key": "ts"}})
        self.compact({"typedJudgeTextProvider": "openai"})
        self.assertEqual(tj.pick("text"), "jev")

    def test_cloudflare_needs_both_the_token_and_the_account_id(self):
        self.media({"cloudflare": {"api_key": "cf"}})
        self.assertIsNone(tj.pick("image"))
        self.media({"cloudflare": {"api_key": "cf", "account_id": "a"}})
        self.assertEqual(tj.pick("image"), "clef")

    def test_local_clef_is_set_up_by_a_saved_endpoint_not_by_a_default(self):
        self.assertIsNone(tj.pick("text"))
        self.media({"clef_local": {"endpoint": "http://localhost:11434/v1/systemone"}})
        self.assertEqual(tj.pick("text"), "clef-local")

    def test_a_failed_image_probe_takes_a_judge_out_of_the_image_tier_only(self):
        self.media({"cloudflare": {"api_key": "cf", "account_id": "a", "imagesVerified": False},
                    "openai": {"api_key": "oa"}})
        self.assertEqual(tj.pick("image"), "openai")
        self.assertEqual(tj.pick("text"), "clef-flash")

    def test_the_image_tier_filters_on_how_many_images_a_request_carries(self):
        self.media({"cloudflare": {"api_key": "cf", "account_id": "a"}, "openai": {"api_key": "oa"}})
        self.assertEqual(tj.pick("image", n_images=4), "clef")
        self.assertEqual(tj.pick("image", n_images=5), "openai")  # null cap: not enforced

    def test_auto_skips_a_judge_the_request_does_not_fit(self):
        """Direction picking sends ~50k tokens and a 130-option choice: Clef
        Flash (24k) and Local Clef (26 options) would refuse it, Clef takes it."""
        self.media({"cloudflare": {"api_key": "cf", "account_id": "a"},
                    "clef_local": {"endpoint": "http://localhost:11434/v1/systemone"}})
        op = self.opener(CLEF_REST)
        big = "x" * int(40_000 * 3.6)
        res = tj.judge(big, {"q": QUESTIONS["refused"]})
        self.assertEqual(res["provider"], "clef")
        many = {"q": {"type": "choice", "instructions": "pick",
                      "criteria": {"a%d" % i: "r" for i in range(130)}}}
        self.compact({"typedJudgeTextProvider": "clef-local"})
        self.assertEqual(tj.judge("brief", many)["provider"], "clef-flash")
        self.assertTrue(op.requests)

    def test_when_nothing_fits_the_limit_comes_back_as_a_400(self):
        self.media({"cloudflare": {"api_key": "cf", "account_id": "a"}})
        with self.assertRaises(ValueError):
            tj.judge("x" * int(70_000 * 3.6), {"q": QUESTIONS["refused"]})

    def test_the_daemons_resolver_is_used_instead_of_the_files(self):
        """Guest isolation: a guest with no key of their own must not fall
        through to the host's media-config key."""
        self.media(ALL_KEYED)
        self.assertEqual(tj.pick("text", resolve_key=lambda _p: None), "clef-local")

    def test_status_names_both_tiers_and_every_judge(self):
        self.media({"typesafe": {"api_key": "ts"}, "openai": {"api_key": "oa", "imagesVerified": True}})
        st = tj.status()
        self.assertEqual(st["text"], {"id": "jev", "name": "TypeSafe Jev"})
        self.assertEqual(st["image"]["id"], "openai")
        rows = {r["id"]: r for r in st["providers"]}
        self.assertEqual(set(rows), {"jev", "clef", "clef-flash", "clef-local", "openai"})
        self.assertTrue(rows["jev"]["keyed"])
        self.assertEqual(rows["jev"]["tiers"], ["text"])
        self.assertEqual(rows["openai"]["tiers"], ["text", "image"])
        self.assertTrue(rows["openai"]["imagesVerified"])
        self.assertFalse(rows["clef"]["keyed"])
        for r in st["providers"]:
            self.assertEqual(set(r), {"id", "name", "config", "keyed", "maxImages",
                                      "imagesVerified", "tiers"})


class P7JevImageUpgrade(Isolated):
    """When TypeSafe ships image input the change is ONE number in judges.json.
    Nothing else in this test differs from the one before it."""

    def test_raising_maxImages_puts_jev_in_the_image_tier(self):
        self.media({"typesafe": {"api_key": "ts"}})
        self.assertIsNone(tj.pick("image"))
        self.judges(lambda rows: rows["jev"].update(maxImages=4))
        self.assertEqual(tj.pick("image"), "jev")
        st = {r["id"]: r for r in tj.status()["providers"]}
        self.assertEqual(st["jev"]["tiers"], ["text", "image"])

    def test_it_then_sends_images_on_the_same_wire_as_text(self):
        self.media({"typesafe": {"api_key": "ts"}})
        self.judges(lambda rows: rows["jev"].update(maxImages=4))
        op = self.opener(SYSTEMONE)
        res = tj.judge("frames", {"states_a_direction": QUESTIONS["states_a_direction"]},
                       tier="image", images=[png()])
        self.assertEqual(res["provider"], "jev")
        self.assertEqual(op.requests[0].full_url, "https://api.typesafe.ai/v1/systemone")
        self.assertTrue(op.body()["images"][0].startswith("data:image/png;base64,"))

    def test_a_failed_probe_still_keeps_it_out(self):
        self.media({"typesafe": {"api_key": "ts", "imagesVerified": False}})
        self.judges(lambda rows: rows["jev"].update(maxImages=4))
        self.assertIsNone(tj.pick("image"))


# ── Wires ───────────────────────────────────────────────────────────────────

class SystemOneWire(Isolated):

    def test_clef_goes_to_the_account_url_and_is_unwrapped_from_result(self):
        self.media(ALL_KEYED)
        op = self.opener(CLEF_REST)
        q = {k: v for k, v in QUESTIONS.items() if k != "refused"}
        res = tj.judge("brief", q, provider="clef")
        req = op.requests[0]
        self.assertEqual(req.full_url, "https://api.cloudflare.com/client/v4/accounts/"
                                       "acct-1/ai/run/@cf/cloudflare/clef")
        self.assertEqual(req.get_header("Authorization"), "Bearer cf")
        self.assertEqual(op.body()["model"], "clef")
        self.assertEqual(res["answers"], SYSTEMONE["answers"])
        self.assertEqual((res["provider"], res["model"], res["tier"]), ("clef", "clef", "text"))

    def test_clef_flash_sends_its_own_model_id(self):
        self.media(ALL_KEYED)
        op = self.opener(CLEF_REST)
        tj.judge("x", {"q": QUESTIONS["refused"]}, provider="clef-flash")
        self.assertTrue(op.requests[0].full_url.endswith("/@cf/cloudflare/clef-flash"))
        self.assertEqual(op.body()["model"], "clef-flash")

    def test_local_clef_has_no_auth_and_sends_raw_base64_images(self):
        """Ollama's /v1/systemone takes raw base64 strings, not data URLs."""
        self.media(ALL_KEYED)
        op = self.opener(SYSTEMONE)
        tj.judge("x", {"q": QUESTIONS["refused"]}, provider="clef-local", tier="image",
                 images=[png()])
        req = op.requests[0]
        self.assertEqual(req.full_url, "http://localhost:11434/v1/systemone")
        self.assertIsNone(req.get_header("Authorization"))
        img = op.body()["images"][0]
        self.assertFalse(img.startswith("data:"))
        self.assertEqual(base64.b64decode(img)[:4], b"\x89PNG")

    def test_clef_sends_data_urls(self):
        self.media(ALL_KEYED)
        op = self.opener(CLEF_REST)
        tj.judge("x", {"q": QUESTIONS["refused"]}, provider="clef", tier="image", images=[png()])
        self.assertTrue(op.body()["images"][0].startswith("data:image/png;base64,"))

    def test_a_text_request_carries_no_images_field(self):
        self.media(ALL_KEYED)
        op = self.opener(SYSTEMONE)
        tj.judge("x", {"q": QUESTIONS["refused"]})
        self.assertEqual(set(op.body()), {"state", "model", "questions"})


class OpenAIWire(Isolated):

    def setUp(self):
        super().setUp()
        self.media({"openai": {"api_key": "oa"}})

    def test_the_request_is_translated_question_by_question(self):
        op = self.opener(OPENAI)
        tj.judge({"brief": "a dense tool"}, QUESTIONS, provider="openai", tier="image",
                 images=[png()])
        req = op.requests[0]
        self.assertEqual(req.full_url, "https://api.openai.com/v1/decisions")
        self.assertEqual(req.get_header("Authorization"), "Bearer oa")
        body = op.body()
        self.assertEqual(body["model"], "gpt-6-luna")
        content = body["input"][0]["content"]
        self.assertEqual(body["input"][0]["role"], "user")
        self.assertEqual(content[0]["type"], "input_text")
        self.assertEqual(json.loads(content[0]["text"]), {"brief": "a dense tool"})
        self.assertEqual(content[1]["type"], "input_image")
        self.assertTrue(content[1]["image_url"].startswith("data:image/png;base64,"))
        qs = {q["name"]: q for q in body["questions"]}
        self.assertEqual(list(qs), list(QUESTIONS))
        pred = qs["states_a_direction"]
        self.assertEqual(pred["type"], "predicate")
        self.assertIn("It names a style or a mood", pred["instructions"])
        self.assertIn("It only describes function", pred["instructions"])
        self.assertEqual(qs["shell"]["choices"][0],
                         {"value": "three-column-app", "description": "dense product UI"})
        self.assertEqual(qs["polish"]["levels"][0], {"label": "absent", "description": "no visual intent"})
        self.assertEqual(len(qs["polish"]["levels"]), 5)

    def test_a_refusal_is_dropped_so_the_reader_escalates_it(self):
        self.opener(OPENAI)
        res = tj.judge("x", QUESTIONS, provider="openai")
        self.assertNotIn("refused", res["answers"])
        v = tj.noul_verdict(res["answers"].get("refused"), tj.thresholds())
        self.assertIsNone(v["pass"])
        self.assertEqual(v["band"], "escalate")


class P6AdapterRoundTrip(Isolated):
    """The same questions, answered in each wire format, read the same."""

    def test_openai_reads_exactly_like_system_one(self):
        self.media({"openai": {"api_key": "oa"}, "typesafe": {"api_key": "ts"}})
        self.opener(OPENAI)
        via_openai = tj.judge("x", QUESTIONS, provider="openai")["answers"]
        self.opener(SYSTEMONE)
        via_systemone = tj.judge("x", QUESTIONS, provider="jev")["answers"]
        th = tj.thresholds("direction_axis")
        for qid in QUESTIONS:
            a, b = via_openai.get(qid), via_systemone.get(qid)
            self.assertEqual(tj.noul_value(a), tj.noul_value(b), qid)
            self.assertEqual(tj.noul_pass(a), tj.noul_pass(b), qid)
            self.assertEqual(tj.choice_ranked(a), tj.choice_ranked(b), qid)
            self.assertEqual(tj.confidence(a), tj.confidence(b), qid)
            self.assertEqual(tj.noul_verdict(a, th), tj.noul_verdict(b, th), qid)
        self.assertEqual(via_openai["polish"], via_systemone["polish"])
        self.assertEqual(via_openai["shell"]["choice"], "three-column-app")


# ── P4 - degradation per provider ───────────────────────────────────────────

class P4Degradation(Isolated):
    """Each judge, each failure: a catchable JudgeError, never a crash, so
    every consumer keeps the path it had before typed judgment."""

    PROVIDERS = ("jev", "clef", "clef-flash", "clef-local", "openai")
    Q = {"q": {"type": "noul", "instructions": "The state mentions a card."}}

    def test_absent_key(self):
        for pid in self.PROVIDERS:
            with self.assertRaises(tj.JudgeUnavailable, msg=pid):
                tj.judge("x", self.Q, provider=pid)

    def test_401_fails_once_without_retrying(self):
        self.media(ALL_KEYED)
        for pid in self.PROVIDERS:
            op = self.opener(urllib.error.HTTPError("u", 401, "no", {}, None))
            with self.assertRaises(tj.JudgeError, msg=pid) as ctx:
                tj.judge("x", self.Q, provider=pid)
            self.assertEqual(len(op.requests), 1, pid)
            self.assertEqual(ctx.exception.status, 401)
            self.assertNotIsInstance(ctx.exception, tj.JudgeUnavailable)

    def test_429_retries_then_raises(self):
        self.media(ALL_KEYED)
        for pid in self.PROVIDERS:
            op = self.opener(urllib.error.HTTPError("u", 429, "slow", {}, None))
            with self.assertRaises(tj.JudgeError, msg=pid):
                tj.judge("x", self.Q, provider=pid, max_retries=2)
            self.assertEqual(len(op.requests), 3, pid)

    def test_malformed_body(self):
        self.media(ALL_KEYED)
        for pid in self.PROVIDERS:
            self.opener({"unexpected": True, "result": {"nope": 1}})
            with self.assertRaises(tj.JudgeError, msg=pid):
                tj.judge("x", self.Q, provider=pid)

    def test_network_error(self):
        self.media(ALL_KEYED)
        for pid in self.PROVIDERS:
            self.opener(OSError("connection refused"))
            with self.assertRaises(tj.JudgeError, msg=pid):
                tj.judge("x", self.Q, provider=pid, max_retries=1)

    def test_readers_are_total_on_garbage(self):
        for bad in (None, {}, [], "nope", {"probabilities": "nope"}, {"noul": "high"}):
            self.assertFalse(tj.noul_pass(bad))
            self.assertEqual(tj.choice_ranked(bad), [])
            self.assertIsNone(tj.confidence(bad))
            self.assertIsNone(tj.noul_verdict(bad, tj.thresholds())["pass"])


# ── Limits, checked against the chosen judge ───────────────────────────────

class Limits(Isolated):

    def setUp(self):
        super().setUp()
        self.media(ALL_KEYED)
        self.opener(SYSTEMONE)

    def test_clef_takes_at_most_64_questions(self):
        many = {"q%d" % i: {"type": "noul", "instructions": "x"} for i in range(65)}
        with self.assertRaises(ValueError):
            tj.judge("x", many, provider="clef")
        tj.judge("x", many, provider="jev")  # Jev publishes no cap

    def test_clef_refuses_question_ids_it_cannot_carry(self):
        with self.assertRaises(ValueError):
            tj.judge("x", {"has space": {"type": "noul", "instructions": "x"}}, provider="clef")

    def test_local_clef_caps_choices_at_26(self):
        q = {"q": {"type": "choice", "instructions": "pick",
                   "criteria": {"o%d" % i: "r" for i in range(27)}}}
        with self.assertRaises(ValueError):
            tj.judge("x", q, provider="clef-local")
        tj.judge("x", q, provider="clef")

    def test_a_choice_needs_two_options(self):
        with self.assertRaises(ValueError):
            tj.judge("x", {"q": {"type": "choice", "instructions": "pick", "criteria": {"a": "x"}}})

    def test_image_count_over_a_published_cap(self):
        with self.assertRaises(ValueError):
            tj.judge("x", {"q": QUESTIONS["refused"]}, provider="clef", tier="image",
                     images=[png()] * 5)

    def test_tier_and_images_must_agree(self):
        with self.assertRaises(ValueError):
            tj.judge("x", {"q": QUESTIONS["refused"]}, images=[png()])
        with self.assertRaises(ValueError):
            tj.judge("x", {"q": QUESTIONS["refused"]}, tier="image")

    def test_clef_flash_budget_counts_images(self):
        state = "x" * int(23_500 * 3.6)
        tj.judge(state, {"q": QUESTIONS["refused"]}, provider="clef-flash")
        with self.assertRaises(ValueError) as ctx:
            tj.judge(state, {"q": QUESTIONS["refused"]}, provider="clef-flash", tier="image",
                     images=[png()] * 2)
        self.assertIn("shard", str(ctx.exception))


# ── Images ──────────────────────────────────────────────────────────────────

class Images(Isolated):

    def test_formats_are_sniffed_from_bytes_not_names(self):
        self.assertEqual(tj.sniff_image(tj.solid_png((1, 2, 3))), "png")
        self.assertEqual(tj.sniff_image(b"\xff\xd8\xff\xe0rest"), "jpeg")
        self.assertEqual(tj.sniff_image(b"RIFF\x00\x00\x00\x00WEBPVP8 "), "webp")
        self.assertIsNone(tj.sniff_image(b"GIF89a"))
        with self.assertRaises(ValueError):
            tj.load_image(b"GIF89a....")

    def test_header_sizes_without_pillow(self):
        self.assertEqual(tj.image_size(tj.solid_png((0, 0, 0), size=37), "png"), (37, 37))
        jpeg = (b"\xff\xd8" + b"\xff\xe0" + struct.pack(">H", 4) + b"xx"
                + b"\xff\xc0" + struct.pack(">HBHH", 11, 8, 480, 640) + b"\x03")
        self.assertEqual(tj.image_size(jpeg, "jpeg"), (640, 480))
        vp8x = b"RIFF\x00\x00\x00\x00WEBPVP8X" + b"\x00" * 8 + (1279).to_bytes(3, "little") \
            + (719).to_bytes(3, "little")
        self.assertEqual(tj.image_size(vp8x, "webp"), (1280, 720))

    def test_a_path_outside_the_roots_is_refused(self):
        inside = os.path.join(self.tmp, "proj")
        os.makedirs(inside)
        good = os.path.join(inside, "f.png")
        Path(good).write_bytes(tj.solid_png((1, 1, 1)))
        self.assertTrue(tj.load_image({"path": "f.png"}, roots=[inside]).startswith("data:image/png"))
        outside = os.path.join(self.tmp, "x.png")
        Path(outside).write_bytes(tj.solid_png((1, 1, 1)))
        for bad in (outside, "../x.png"):
            with self.assertRaises(ValueError) as ctx:
                tj.load_image({"path": bad}, roots=[inside])
            self.assertIn("outside", str(ctx.exception))

    def test_oversize_with_no_pillow_names_the_limit(self):
        big = tj.solid_png((5, 5, 5), size=8)
        real = tj.IMAGE_MAX_PIXELS
        tj.IMAGE_MAX_PIXELS = 10
        saved = sys.modules.get("PIL")
        sys.modules["PIL"] = None
        try:
            with self.assertRaises(ValueError) as ctx:
                tj.load_image(big)
            self.assertIn("MP limit", str(ctx.exception))
        finally:
            tj.IMAGE_MAX_PIXELS = real
            if saved is None:
                sys.modules.pop("PIL", None)
            else:
                sys.modules["PIL"] = saved

    def test_oversize_is_downscaled_when_pillow_is_there(self):
        try:
            import PIL  # noqa: F401
        except Exception:
            self.skipTest("Pillow not installed")
        real = tj.IMAGE_MAX_PIXELS
        tj.IMAGE_MAX_PIXELS = 1000
        try:
            uri = tj.load_image(tj.solid_png((5, 5, 5), size=64))
        finally:
            tj.IMAGE_MAX_PIXELS = real
        from PIL import Image
        img = Image.open(io.BytesIO(base64.b64decode(uri.split(",", 1)[1])))
        self.assertLessEqual(img.width * img.height, 1000)


# ── The key-row probe ───────────────────────────────────────────────────────

class Probe(Isolated):

    def _reply_by_colour(self, red_noul, blue_noul):
        def reply(req):
            body = json.loads(req.data.decode("utf-8"))
            if not body.get("images"):
                return {"answers": {"t": {"type": "noul", "noul": 0.97}}}
            raw = body["images"][0].split(",", 1)[-1]
            data = base64.b64decode(raw)
            import zlib
            idat = data.index(b"IDAT")
            px = zlib.decompress(data[idat + 4:])[1:4]
            return {"result": {"answers": {"red": {"type": "noul",
                                                    "noul": red_noul if px[0] > px[2] else blue_noul}}}}
        return reply

    def test_a_judge_that_tells_red_from_blue_reads_images(self):
        self.media(ALL_KEYED)
        self.opener(self._reply_by_colour(0.96, 0.03))
        out = tj.probe("clef")
        self.assertEqual((out["text"], out["images"]), (True, True))

    def test_a_judge_that_cannot_is_text_only(self):
        self.media(ALL_KEYED)
        self.opener(self._reply_by_colour(0.6, 0.55))
        out = tj.probe("clef")
        self.assertEqual((out["text"], out["images"]), (True, False))

    def test_a_text_only_row_is_never_sent_images(self):
        self.media(ALL_KEYED)
        op = self.opener(self._reply_by_colour(0.96, 0.03))
        out = tj.probe("jev")
        self.assertEqual((out["text"], out["images"]), (True, None))
        self.assertEqual(len(op.requests), 1)

    def test_an_unverified_probe_is_not_a_failed_one(self):
        """A pinned probe must reach a judge whose earlier probe failed, or a
        fixed judge could never be re-verified."""
        cfg = dict(ALL_KEYED)
        cfg["cloudflare"] = dict(cfg["cloudflare"], imagesVerified=False)
        self.media(cfg)
        self.opener(self._reply_by_colour(0.96, 0.03))
        self.assertTrue(tj.probe("clef")["images"])

    def test_the_text_probe_failing_stops_there(self):
        self.media(ALL_KEYED)
        self.opener(urllib.error.HTTPError("u", 401, "no", {}, None))
        out = tj.probe("clef")
        self.assertEqual((out["text"], out["images"]), (False, None))
        self.assertIn("401", out["detail"])


# ── Thresholds, settings, shadow log ────────────────────────────────────────

class Thresholds(Isolated):

    def _table(self, extra):
        doc = json.loads(Path(tj.THRESHOLDS_PATH).read_text())
        doc.update(extra)
        Path(tj.THRESHOLDS_PATH).write_text(json.dumps(doc))

    def test_lookup_order_provider_kind_then_provider_default_then_kind_then_default(self):
        self._table({"providers": {"clef": {"ds_role": {"high": 0.97},
                                            "default": {"high": 0.93}}}})
        self.assertEqual(tj.thresholds("ds_role", "clef")["high"], 0.97)
        self.assertEqual(tj.thresholds("requirement_item", "clef")["high"], 0.93)
        self.assertEqual(tj.thresholds("ds_role", "jev")["high"], 0.90)
        self.assertEqual(tj.thresholds("no-such-kind", "jev")["high"], 0.80)
        self.assertEqual(tj.thresholds("ds_role")["high"], 0.90)

    def test_trust_pass_is_off_unless_the_table_says_so(self):
        self.assertFalse(tj.thresholds("frame_check", "clef")["trustPass"])
        self._table({"providers": {"clef": {"frame_check": {"high": 0.9, "trustPass": True}}}})
        self.assertTrue(tj.thresholds("frame_check", "clef")["trustPass"])
        self.assertFalse(tj.thresholds("frame_check", "openai")["trustPass"])

    def test_the_shipped_table_trusts_nothing(self):
        doc = json.loads(Path(self.saved["THRESHOLDS_PATH"]).read_text())
        doc.pop("_readme", None)
        self.assertNotIn("trustPass", json.dumps(doc))


class Settings(Isolated):

    def test_defaults_are_off_auto_auto_shadow(self):
        self.assertEqual(tj.config(), {"jevJudge": False, "typedJudgeVisual": False,
                                       "typedJudgeTextProvider": "auto",
                                       "typedJudgeImageProvider": "auto",
                                       "typedJudgeVisualMode": "shadow"})

    def test_invalid_values_fall_back_to_defaults(self):
        self.compact({"typedJudgeVisual": "yes", "typedJudgeTextProvider": "gemini",
                      "typedJudgeVisualMode": "block", "jevJudge": True})
        cfg = tj.config()
        self.assertFalse(cfg["typedJudgeVisual"])
        self.assertEqual(cfg["typedJudgeTextProvider"], "auto")
        self.assertEqual(cfg["typedJudgeVisualMode"], "shadow")
        self.assertTrue(cfg["jevJudge"])
        self.assertTrue(tj.enabled("text"))
        self.assertFalse(tj.enabled("image"))


class ShadowLog(Isolated):

    def test_appends_one_line_per_call_and_rotates_at_the_cap(self):
        real = tj.SHADOW_LOG_MAX_BYTES
        tj.SHADOW_LOG_MAX_BYTES = 200
        try:
            for i in range(10):
                tj.shadow_log({"provider": "clef", "kind": "frame_check", "noul": 0.1 * i,
                               "llmOk": True, "project": "p"})
        finally:
            tj.SHADOW_LOG_MAX_BYTES = real
        self.assertTrue(os.path.exists(tj.SHADOW_LOG_PATH + ".1"))
        lines = Path(tj.SHADOW_LOG_PATH).read_text().splitlines()
        self.assertTrue(lines)
        self.assertIn("ts", json.loads(lines[-1]))

    def test_never_raises(self):
        tj.SHADOW_LOG_PATH = "/dev/null/cannot/exist.jsonl"
        tj.shadow_log({"x": 1})


# ── Calibration: per provider, trustPass, shadow agreement ──────────────────

class Calibrate(Isolated):

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(EDITOR / "tools" / "qa"))
        import jev_calibrate
        cls.cal = jev_calibrate

    def _cases(self, n, right=True):
        return [{"kind": "frame_check", "tier": "image", "images": ["/x.png"],
                 "state": "frames", "questions": {"q": {"type": "noul", "instructions": "x"}},
                 "expected": {"q": True}} for _ in range(n)]

    def _judge(self, pid, noul):
        def fake(state, questions, **kw):
            return {"answers": {"q": {"type": "noul", "noul": noul}}, "provider": pid}
        return fake

    def test_bands_are_fitted_and_written_per_provider(self):
        rows = self.cal.run_cases(self._cases(25), judge=self._judge("clef", 0.99))
        rows += self.cal.run_cases(self._cases(5), judge=self._judge("openai", 0.99))
        fitted = self.cal.fit(rows, self.cal.DEFAULT_TARGETS, 0.9)
        self.assertEqual(set(fitted), {("clef", "frame_check"), ("openai", "frame_check")})
        self.assertTrue(fitted[("clef", "frame_check")]["trustPass"])
        self.assertFalse(fitted[("openai", "frame_check")]["trustPass"], "too few cases")
        self.cal.write_fitted(fitted, trust_pass=False)
        self.assertFalse(tj.thresholds("frame_check", "clef")["trustPass"])
        self.cal.write_fitted(fitted, trust_pass=True)
        self.assertTrue(tj.thresholds("frame_check", "clef")["trustPass"])
        self.assertFalse(tj.thresholds("frame_check", "openai")["trustPass"])
        self.assertFalse(tj.thresholds("frame_check", "jev")["trustPass"])

    def test_wrong_passes_never_earn_trust(self):
        cases = self._cases(30)
        for c in cases[:3]:
            c["expected"] = {"q": False}
        rows = self.cal.run_cases(cases, judge=self._judge("clef", 0.99))
        fitted = self.cal.fit(rows, self.cal.DEFAULT_TARGETS, 0.85)
        self.assertFalse(fitted[("clef", "frame_check")]["trustPass"])

    def test_the_answer_log_is_labelled_by_id_and_fits_per_provider(self):
        tj.LABELS_PATH = os.path.join(self.tmp, "labels.json")
        for i in range(25):
            tj.shadow_log({"kind": "ds_origin", "provider": "clef", "source": "<style> .x%d" % i,
                           "answer": "ds-copy", "confidence": 0.75 if i < 20 else 0.55,
                           "band": "confirm"})
        rows = tj.read_log()
        self.assertEqual(len(rows), 25)
        self.assertEqual(len({r["id"] for r in rows}), 25, "every row has its own id")
        rep = self.cal.log_report(rows, "ds_origin")
        self.assertEqual((rep["groups"][0]["n"], rep["groups"][0]["labelled"]), (25, 0))
        self.assertEqual(len(rep["unlabelled"]), 25)
        # The confident answers were right, the five hesitant ones wrong.
        tj.save_labels({r["id"]: ("ds-copy" if r["confidence"] > 0.6 else "layout") for r in rows})
        labelled = self.cal.log_rows_for_fit(tj.read_log())
        self.assertEqual(len(labelled), 25)
        self.assertEqual(labelled[0]["kind"], "ds_role", "DS answers fit the ds_role band")
        fitted = self.cal.fit(labelled, self.cal.DEFAULT_TARGETS, 0.9)
        self.assertTrue(fitted[("clef", "ds_role")]["met"])
        self.assertEqual(fitted[("clef", "ds_role")]["high"], 0.6,
                         "Clef's own bar sits just above its own wrong answers")

    def test_shadow_report_counts_agreement_and_lists_disagreements(self):
        for noul, llm in ((0.9, True), (0.1, False), (0.9, False), (0.2, True), (0.8, True)):
            tj.shadow_log({"provider": "clef", "kind": "frame_check", "noul": noul,
                           "llmOk": llm, "project": "p"})
        tj.shadow_log({"provider": "clef", "kind": "frame_check", "noul": None, "llmOk": True})
        rep = self.cal.shadow_report()
        self.assertEqual(rep["skipped"], 1)
        g = rep["groups"][0]
        self.assertEqual((g["provider"], g["kind"], g["n"], g["agree"]), ("clef", "frame_check", 5, 3))
        self.assertEqual(len(g["disagreements"]), 2)
        self.assertEqual(g["agreement"], 0.6)

# ── The daemon routes, driven through the real handlers ─────────────────────

class _Router:
    """urlopen stand-in that answers by URL, so one test can reach the OpenAI
    models list and the Decisions endpoint, or Clef with a red and a blue PNG."""

    def __init__(self, routes):
        self.routes = routes
        self.requests = []

    def __call__(self, req, timeout=None):
        self.requests.append(req)
        for prefix, reply in self.routes:
            if req.full_url.startswith(prefix):
                r = reply(req) if callable(reply) else reply
                if isinstance(r, BaseException):
                    raise r
                return _Resp(r)
        raise AssertionError("unexpected request to " + req.full_url)


def _colour_reply(req):
    """A judge that reads images: high on red, low on blue, sure of the sky."""
    import zlib
    body = json.loads(req.data.decode("utf-8"))
    if not body.get("images"):
        return {"result": {"answers": {"t": {"type": "noul", "noul": 0.98}}}}
    data = base64.b64decode(body["images"][0].split(",", 1)[-1])
    px = zlib.decompress(data[data.index(b"IDAT") + 4:])[1:4]
    return {"result": {"answers": {"red": {"type": "noul", "noul": 0.95 if px[0] > px[2] else 0.04}}}}


class DaemonRoutes(Isolated):

    @classmethod
    def setUpClass(cls):
        import serve  # heavy; only this class needs it
        cls.serve = serve

    def setUp(self):
        super().setUp()
        from unittest.mock import patch
        self.project = os.path.join(self.tmp, "proj")
        os.makedirs(os.path.join(self.project, "source", "main"))
        Path(self.project, "source", "main", "shot.png").write_bytes(tj.solid_png((9, 9, 9)))
        self.patches = [
            patch.object(self.serve, "MEDIA_CONFIG_PATH", tj.MEDIA_CONFIG_PATH),
            patch.object(self.serve, "MEDIA_CONFIG_DIR", self.tmp),
            patch.object(self.serve, "COMPACT_CONFIG_PATH", tj.COMPACT_CONFIG_PATH),
            patch.object(self.serve, "resolve_project_root", lambda *a, **k: self.project),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        super().tearDown()

    def handler(self, body=None):
        from types import SimpleNamespace
        data = json.dumps(body if body is not None else {}).encode("utf-8")
        return SimpleNamespace(headers={"Content-Length": str(len(data))}, rfile=io.BytesIO(data),
                               _read_json_body=lambda: body, _reply=lambda code, payload: (code, payload))

    def post_judge(self, body, alias=None):
        h = self.handler(body)
        return self.serve.H._judge_run(h, {"project": ["proj"]}, alias_tier=alias)

    def settings(self, body):
        return self.serve.H._compact_config_set(self.handler(body))

    def key_test(self, provider):
        return self.serve.H._media_config_test(self.handler(), {"provider": [provider]})

    Q = {"q": {"type": "noul", "instructions": "The page shows a card."}}

    # settings ----------------------------------------------------------------

    def test_settings_whitelist_validates_every_new_key(self):
        self.assertEqual(self.settings({"typedJudgeVisual": True})[0], 200)
        self.assertEqual(self.settings({"typedJudgeTextProvider": "clef-flash"})[0], 200)
        self.assertEqual(self.settings({"typedJudgeImageProvider": "auto"})[0], 200)
        code, cfg = self.settings({"typedJudgeVisualMode": "flag"})
        self.assertEqual(code, 200)
        for bad in ({"typedJudgeVisual": "on"}, {"typedJudgeTextProvider": "gemini"},
                    {"typedJudgeVisualMode": "block"}):
            self.assertEqual(self.settings(bad)[0], 400, bad)
        loaded = self.serve._compact_config()
        self.assertEqual((loaded["typedJudgeVisual"], loaded["typedJudgeTextProvider"],
                          loaded["typedJudgeVisualMode"]), (True, "clef-flash", "flag"))
        self.assertEqual(tj.config()["typedJudgeTextProvider"], "clef-flash")

    def test_defaults_are_off(self):
        cfg = self.serve._compact_config()
        self.assertEqual((cfg["typedJudgeVisual"], cfg["typedJudgeTextProvider"],
                          cfg["typedJudgeImageProvider"], cfg["typedJudgeVisualMode"]),
                         (False, "auto", "auto", "shadow"))

    # /__judge ----------------------------------------------------------------

    def test_off_is_a_503_with_reason_off(self):
        code, out = self.post_judge({"state": "x", "questions": self.Q})
        self.assertEqual((code, out["reason"]), (503, "off"))

    def test_on_with_nothing_set_up_is_no_key_or_no_image_judge(self):
        self.compact({"jevJudge": True, "typedJudgeVisual": True})
        self.assertEqual(self.post_judge({"state": "x", "questions": self.Q})[1]["reason"], "no-key")
        code, out = self.post_judge({"state": "x", "questions": self.Q, "tier": "image",
                                     "images": [{"path": "source/main/shot.png"}]})
        self.assertEqual((code, out["reason"]), (503, "no-image-judge"))
        self.assertIn("Cloudflare or OpenAI", out["hint"])

    def test_an_image_request_reaches_the_image_judge(self):
        self.compact({"typedJudgeVisual": True})
        self.media({"cloudflare": {"api_key": "cf", "account_id": "a"}})
        op = self.opener(CLEF_REST)
        code, out = self.post_judge({"state": "x", "questions": self.Q, "tier": "image",
                                     "kind": "visual_item",
                                     "images": [{"path": "source/main/shot.png"}]})
        self.assertEqual(code, 200, out)
        self.assertEqual((out["provider"], out["tier"]), ("clef", "image"))
        self.assertEqual(out["thresholds"]["high"], 0.90)
        self.assertEqual(len(json.loads(op.requests[0].data)["images"]), 1)

    def test_a_qa_frame_outside_the_project_is_allowed_anything_else_is_not(self):
        self.compact({"typedJudgeVisual": True})
        self.media({"cloudflare": {"api_key": "cf", "account_id": "a"}})
        self.opener(CLEF_REST)
        qa_dir = tempfile.mkdtemp(prefix="woven-qa-")
        try:
            frame = os.path.join(qa_dir, "idle_0.png")
            Path(frame).write_bytes(tj.solid_png((1, 2, 3)))
            ok = self.post_judge({"state": "x", "questions": self.Q, "tier": "image",
                                  "images": [{"path": frame}]})
            self.assertEqual(ok[0], 200, ok[1])
        finally:
            shutil.rmtree(qa_dir, ignore_errors=True)
        stray = os.path.join(self.tmp, "stray.png")
        Path(stray).write_bytes(tj.solid_png((1, 2, 3)))
        for path in (stray, "../stray.png"):
            code, out = self.post_judge({"state": "x", "questions": self.Q, "tier": "image",
                                         "images": [{"path": path}]})
            self.assertEqual(code, 400, path)
            self.assertIn("outside", out["error"])

    def test_a_node_image_resolves_to_its_asset(self):
        self.compact({"typedJudgeVisual": True})
        self.media({"cloudflare": {"api_key": "cf", "account_id": "a"}})
        self.opener(CLEF_REST)
        os.makedirs(os.path.join(self.project, "workflow"))
        Path(self.project, "workflow", "workflow.json").write_text(json.dumps(
            {"nodes": [{"id": "n1", "path": "source/main/shot.png"}, {"id": "n2"}]}))
        self.assertEqual(self.post_judge({"state": "x", "questions": self.Q, "tier": "image",
                                          "images": [{"node": "n1"}]})[0], 200)
        self.assertEqual(self.post_judge({"state": "x", "questions": self.Q, "tier": "image",
                                          "images": [{"node": "n2"}]})[0], 400)

    def test_the_jev_alias_is_the_text_tier(self):
        self.compact({"jevJudge": True})
        self.media({"typesafe": {"api_key": "ts"}})
        self.opener(SYSTEMONE)
        code, out = self.post_judge({"state": "x", "questions": self.Q, "kind": "requirement_item"},
                                    alias="text")
        self.assertEqual((code, out["provider"], out["tier"]), (200, "jev", "text"))
        self.assertEqual(out["thresholds"]["high"], 0.85)
        code, _ = self.post_judge({"state": "x", "questions": self.Q,
                                   "images": [{"path": "source/main/shot.png"}]}, alias="text")
        self.assertEqual(code, 400)

    def test_shape_and_service_4xx_are_400_outages_are_502(self):
        self.compact({"jevJudge": True})
        self.media({"openai": {"api_key": "oa"}})
        self.assertEqual(self.post_judge({"state": "x", "questions": {"q": {"type": "essay",
                                                                             "instructions": "x"}}})[0], 400)
        self.assertEqual(self.post_judge({"state": "x", "questions": self.Q, "provider": "gemini"})[0], 400)
        self.opener(urllib.error.HTTPError("u", 422, "bad", {}, None))
        self.assertEqual(self.post_judge({"state": "x", "questions": self.Q})[0], 400)
        self.opener(urllib.error.HTTPError("u", 500, "down", {}, None))
        self.assertEqual(self.post_judge({"state": "x", "questions": self.Q})[0], 502)

    def test_a_routed_request_ignores_a_model_meant_for_another_judge(self):
        """Old /__jev callers send model jev-latest; Clef refuses any model id
        but its own, so the model only applies to a pinned judge."""
        self.compact({"jevJudge": True})
        self.media({"cloudflare": {"api_key": "cf", "account_id": "a"}})
        op = self.opener(CLEF_REST)
        self.assertEqual(self.post_judge({"state": "x", "questions": self.Q,
                                          "model": "jev-latest"}, alias="text")[0], 200)
        self.assertEqual(json.loads(op.requests[0].data)["model"], "clef-flash")

    # status and key rows -----------------------------------------------------

    def test_media_config_rows_carry_fields_and_image_status(self):
        self.media({"cloudflare": {"api_key": "cf", "account_id": "acct", "imagesVerified": True},
                    "typesafe": {"api_key": "ts"}})
        code, out = self.serve.H._media_config_get(self.handler())
        rows = out["providers"]
        self.assertEqual(rows["cloudflare"]["fields"], {"account_id": "acct"})
        self.assertEqual(rows["cloudflare"]["judgeImages"], "reads")
        self.assertEqual(rows["typesafe"]["judgeImages"], "text")
        self.assertEqual(rows["openai"]["judgeImages"], "unchecked")
        self.assertFalse(rows["clef_local"]["has_key"])
        self.assertEqual(rows["clef_local"]["fields"], {"endpoint": None})
        self.assertNotIn("judgeImages", rows["fal"])

    def test_saving_a_new_account_id_forgets_what_the_last_test_proved(self):
        self.media({"cloudflare": {"api_key": "cf", "account_id": "a", "imagesVerified": True,
                                   "last_test_ok": True}})
        self.serve.H._media_config_set(self.handler({"cloudflare": {"account_id": "b"}}))
        saved = json.loads(Path(tj.MEDIA_CONFIG_PATH).read_text())["cloudflare"]
        self.assertEqual(saved["account_id"], "b")
        self.assertNotIn("imagesVerified", saved)
        self.assertEqual(saved["api_key"], "cf")

    def test_cloudflare_test_verifies_images_and_records_it(self):
        self.media({"cloudflare": {"api_key": "cf", "account_id": "a"}})
        self.opener(_colour_reply)
        code, out = self.key_test("cloudflare")
        self.assertEqual(code, 200, out)
        self.assertTrue(out["imagesVerified"])
        self.assertTrue(json.loads(Path(tj.MEDIA_CONFIG_PATH).read_text())["cloudflare"]["imagesVerified"])
        self.assertEqual(tj.pick("image"), "clef")

    def test_cloudflare_test_without_an_account_id_says_so(self):
        self.media({"cloudflare": {"api_key": "cf"}})
        code, out = self.key_test("cloudflare")
        self.assertEqual(code, 502)
        self.assertIn("account ID", out["detail"]["hint"])

    def test_typesafe_test_is_text_only_and_sends_no_image(self):
        self.media({"typesafe": {"api_key": "ts"}})
        op = self.opener({"answers": {"t": {"type": "noul", "noul": 0.97}}})
        code, out = self.key_test("typesafe")
        self.assertEqual((code, out["judge"]["images"], out["imagesVerified"]), (200, None, None))
        self.assertEqual(len(op.requests), 1)

    def test_local_clef_test_needs_no_key_and_sets_up_the_default_endpoint(self):
        op = self.opener(lambda req: {"answers": _colour_reply(req)["result"]["answers"]})
        code, out = self.key_test("clef_local")
        self.assertEqual(code, 200, out)
        self.assertEqual(op.requests[0].full_url, "http://localhost:11434/v1/systemone")
        saved = json.loads(Path(tj.MEDIA_CONFIG_PATH).read_text())["clef_local"]
        self.assertEqual(saved["endpoint"], "http://localhost:11434/v1/systemone")
        self.assertEqual(tj.pick("text"), "clef-local")

    def test_an_openai_key_never_fails_because_decisions_did(self):
        self.media({"openai": {"api_key": "oa"}})
        tj.urllib.request.urlopen = _Router([
            ("https://api.openai.com/v1/models", {"data": []}),
            ("https://api.openai.com/v1/decisions", urllib.error.HTTPError("u", 404, "no", {}, None)),
        ])
        code, out = self.key_test("openai")
        self.assertEqual(code, 200, out)
        self.assertFalse(out["judge"]["text"])
        self.assertIsNone(out["imagesVerified"])

    def test_a_pages_stored_criteria_are_its_own_plus_the_shared_ones(self):
        folder = os.path.join(self.project, "source", "main")
        path = os.path.join(folder, "visual-checks.json")
        Path(path).write_text(json.dumps({
            "checks": [{"id": "brand", "shape": "shows", "x": "the SUSS logo", "at": "page"}],
            "pages": {"apply.html": [{"id": "q1", "shape": "shows", "x": "a Yes/No question",
                                      "at": "page", "selector": "#q1"}],
                      "other.html": [{"id": "z", "shape": "shows", "x": "x y z", "at": "page"}]}}))
        got = self.serve._page_visual_checks(path, os.path.join(folder, "apply.html"))
        self.assertEqual([c["id"] for c in got], ["brand", "q1"])
        self.assertEqual([c["id"] for c in self.serve._page_visual_checks(
            path, os.path.join(folder, "none.html"))], ["brand"])
        Path(path).write_text(json.dumps({"pages": {"apply.html": {
            "steps": [{"label": "pick_yes", "type": "click", "selector": "#yes"}],
            "checks": [{"id": "f", "shape": "shows", "x": "a field", "at": "after:pick_yes"}]}}}))
        apply = os.path.join(folder, "apply.html")
        self.assertEqual([c["id"] for c in self.serve._page_visual_checks(path, apply)], ["f"])
        self.assertEqual(self.serve._page_visual_steps(path, apply)[0]["selector"], "#yes")
        self.assertEqual(self.serve._page_visual_steps(path, os.path.join(folder, "none.html")), [])
        Path(path).write_text(json.dumps([{"id": "a", "shape": "shows", "x": "x y", "at": "page"}]))
        self.assertEqual(len(self.serve._page_visual_checks(path, os.path.join(folder, "apply.html"))), 1)
        Path(path).write_text("{broken")
        self.assertEqual(self.serve._page_visual_checks(path, os.path.join(folder, "apply.html")), [])

    def test_judge_status_route(self):
        self.media({"typesafe": {"api_key": "ts"}})
        st = tj.status(resolve_key=self.serve._resolve_provider_key)
        self.assertEqual(st["text"]["id"], "jev")
        self.assertIsNone(st["image"])


if __name__ == "__main__":
    unittest.main()

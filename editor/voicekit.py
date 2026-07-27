"""Runtime voice core (dynamic TTS + STT) shared by the daemon and the share gate.

This module is the SINGLE implementation behind:
  - POST /__voice/tts            (daemon, editor/serve.py)
  - POST /__voice/stt            (daemon)
  - GET  /__voice/status|voices  (daemon)
  - POST /s/<token>/api/voice/*  (share gate, editor/shares.py GateHandler)

Design notes (v1, buffered):
  - TTS is whole-utterance: the full mp3 is generated at ElevenLabs, cached,
    and returned as audio/mpeg bytes. No streaming, no disk writes (this is
    the runtime sibling of the BAKED audio-gen skill, which writes assets to
    source/<branch>/audio/).
  - STT is batch: the recorded blob (MediaRecorder webm/opus, or Safari's
    mp4/aac - ffmpeg decodes both) is transcribed with the same engines the
    user-testing capability provisioned: local whisper.cpp first (free,
    offline), OpenAI whisper-1 as the cloud fallback.
  - Rate limiting + the TTS cache are IN-MEMORY, per daemon process, and
    reset on restart. Accepted for v1: the hosted daily-character budget is
    the real spend bound and a restart resetting it only ever errs generous.
  - serve.py owns keys, renderers and whisper helpers; init() threads them in
    so this module has zero imports from the monolith (and the gate, which
    deliberately does not import serve.py, can still call it).

Python 3.9 floor applies (fresh installs run the stock macOS python3).
"""

from __future__ import annotations

import collections
import hashlib
import json
import os
import shutil
import tempfile
import threading

# ── wiring (populated once by serve.py at boot via init()) ──────────────────

_FNS = {
    "resolve_provider_key": None,   # (provider) -> key or None
    "elevenlabs_audio": None,       # (api_key, prompt, model, aspect, options) -> bytes
    "whisper_local": None,          # (binp, ffmpeg, audio_path) -> transcript dict or None
    "whisper_cloud": None,          # (api_key, audio_path) -> transcript dict or None
    "whisper_find_bin": None,       # () -> path or None
    "whisper_status": None,         # () -> {binary, model, ready}
}


def init(resolve_provider_key, elevenlabs_audio, whisper_local, whisper_cloud,
         whisper_find_bin, whisper_status):
    _FNS["resolve_provider_key"] = resolve_provider_key
    _FNS["elevenlabs_audio"] = elevenlabs_audio
    _FNS["whisper_local"] = whisper_local
    _FNS["whisper_cloud"] = whisper_cloud
    _FNS["whisper_find_bin"] = whisper_find_bin
    _FNS["whisper_status"] = whisper_status


class VoiceKeyError(Exception):
    """No ElevenLabs key is wired (env TH_ELEVENLABS_API_KEY or media-config)."""


# ── curated voices ──────────────────────────────────────────────────────────
# ElevenLabs premade-library voices with casting notes, so prototypes and the
# share gate can validate viewer-supplied voice ids against a known-cost set.
# KEEP IN SYNC with the voice map in docs/research/sound-library.md (the
# sound-orchestrator's casting doctrine reads that file; this list is the
# machine-readable twin the /__voice/voices endpoint serves).

CURATED_VOICES = [
    {"id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel",    "character": "calm, warm, neutral American female", "castFor": "default narrator, documentary", "default": True},
    {"id": "pNInz6obpgDQGcFmaJgB", "name": "Adam",      "character": "deep, grounded male",                 "castFor": "trailers, authority"},
    {"id": "ErXwobaYiN019PkySvjV", "name": "Antoni",    "character": "well rounded, warm male",             "castFor": "product narration"},
    {"id": "AZnzlk1XvdvUeBnXmlld", "name": "Domi",      "character": "strong, confident female",            "castFor": "energetic UI, arcade callouts"},
    {"id": "MF3mGyEYCl7XYWbV9V6O", "name": "Elli",      "character": "young, emotive female",               "castFor": "character voice, playful"},
    {"id": "TxGEqnHWrfWFTfGW9XjX", "name": "Josh",      "character": "deep young male",                     "castFor": "cinematic, game protagonist"},
    {"id": "VR6AewLTigWG4xSOukaG", "name": "Arnold",    "character": "crisp, resonant male",                "castFor": "announcer, sports"},
    {"id": "XB0fDUnXU5powFXDhCwa", "name": "Charlotte", "character": "measured, luxurious female",          "castFor": "museum hush, luxury"},
]

DEFAULT_VOICE_ID = CURATED_VOICES[0]["id"]
_CURATED_IDS = set(v["id"] for v in CURATED_VOICES)


def curated_voices():
    return [dict(v) for v in CURATED_VOICES]


def is_curated_voice(voice_id):
    return voice_id in _CURATED_IDS


# ── TTS cache ───────────────────────────────────────────────────────────────
# Small shared LRU so repeated utterances (UI labels, common feedback lines,
# repeat share viewers) are instant and free. A ~5s utterance at mp3_44100_128
# is roughly 80KB, so the byte bound dominates in practice.

_TTS_CACHE = collections.OrderedDict()   # sha256 hex -> mp3 bytes
_TTS_CACHE_LOCK = threading.Lock()
_TTS_CACHE_MAX_ENTRIES = 64
_TTS_CACHE_MAX_BYTES = 20 * 1024 * 1024
_TTS_CACHE_BYTES = [0]


def _cache_key(text, voice_id, model_id, voice_settings):
    blob = "|".join([
        voice_id or "", model_id or "",
        json.dumps(voice_settings, sort_keys=True) if isinstance(voice_settings, dict) else "",
        text or "",
    ])
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _cache_get(key):
    with _TTS_CACHE_LOCK:
        data = _TTS_CACHE.get(key)
        if data is not None:
            _TTS_CACHE.move_to_end(key)
        return data


def _cache_put(key, data):
    with _TTS_CACHE_LOCK:
        old = _TTS_CACHE.pop(key, None)
        if old is not None:
            _TTS_CACHE_BYTES[0] -= len(old)
        _TTS_CACHE[key] = data
        _TTS_CACHE_BYTES[0] += len(data)
        while _TTS_CACHE and (len(_TTS_CACHE) > _TTS_CACHE_MAX_ENTRIES
                              or _TTS_CACHE_BYTES[0] > _TTS_CACHE_MAX_BYTES):
            _k, _v = _TTS_CACHE.popitem(last=False)
            _TTS_CACHE_BYTES[0] -= len(_v)


# ── rate limiter ────────────────────────────────────────────────────────────
# Sliding-window requests-per-minute per key, plus an optional daily character
# budget per budget-key. In-memory, per process (documented above).

LIMITS = {
    # Share viewers: the spend gate. rpm keyed on token+ip; the daily char
    # budget keyed on token alone so it caps the SHARE regardless of viewers.
    "hosted": {"rpm": 10, "chars_per_req": 500, "chars_per_day": 20000,
               "stt_bytes": 5 * 1024 * 1024, "stt_rpm": 6},
    # Local prototypes / editor: generous, just a runaway-loop backstop.
    "local":  {"rpm": 60, "chars_per_req": 2000, "chars_per_day": None,
               "stt_bytes": 10 * 1024 * 1024, "stt_rpm": 30},
}

_RATE_LOCK = threading.Lock()
_RATE_WINDOWS = {}    # key -> list of monotonic timestamps (last 60s)
_DAY_BUDGETS = {}     # key -> {"day": "YYYY-MM-DD", "chars": int}


def check_rate(profile, key, now, today, chars=0, budget_key=None, kind="tts"):
    """Returns (ok, retry_after_seconds, reason). `now` is a monotonic-ish
    seconds float; `today` a YYYY-MM-DD string (callers pass real time so this
    module stays clock-agnostic and easy to test)."""
    lim = LIMITS.get(profile) or LIMITS["local"]
    rpm = lim["stt_rpm"] if kind == "stt" else lim["rpm"]
    with _RATE_LOCK:
        win = _RATE_WINDOWS.setdefault(kind + ":" + key, [])
        cutoff = now - 60.0
        while win and win[0] < cutoff:
            win.pop(0)
        if len(win) >= rpm:
            return (False, max(1, int(win[0] + 60.0 - now) + 1),
                    "rate limit: %d requests per minute" % rpm)
        cap = lim.get("chars_per_day")
        if kind == "tts" and cap and budget_key:
            b = _DAY_BUDGETS.setdefault(budget_key, {"day": today, "chars": 0})
            if b["day"] != today:
                b["day"] = today
                b["chars"] = 0
            if b["chars"] + chars > cap:
                return (False, 3600, "daily voice budget for this share is used up")
            b["chars"] += chars
        win.append(now)
    return (True, 0, "")


def max_text_chars(profile):
    lim = LIMITS.get(profile) or LIMITS["local"]
    return lim["chars_per_req"]


def max_stt_bytes(profile):
    lim = LIMITS.get(profile) or LIMITS["local"]
    return lim["stt_bytes"]


# ── TTS ─────────────────────────────────────────────────────────────────────

def tts_bytes(text, voice_id=None, model_id=None, voice_settings=None):
    """Generate (or cache-hit) one utterance. Returns (mp3_bytes, cache_hit).
    Raises VoiceKeyError when no ElevenLabs key is wired; upstream HTTPError
    bubbles for the caller to map to a 502 with ElevenLabs' error body."""
    resolve = _FNS["resolve_provider_key"]
    renderer = _FNS["elevenlabs_audio"]
    if resolve is None or renderer is None:
        raise RuntimeError("voicekit is not initialised")
    vid = (voice_id or "").strip() or DEFAULT_VOICE_ID
    mid = (model_id or "").strip() or "eleven_multilingual_v2"
    key = _cache_key(text, vid, mid, voice_settings)
    cached = _cache_get(key)
    if cached is not None:
        return (cached, True)
    api_key = resolve("elevenlabs")
    if not api_key:
        raise VoiceKeyError("no ElevenLabs key configured")
    options = {"voice_id": vid, "model_id": mid}
    if isinstance(voice_settings, dict) and voice_settings:
        options["voice_settings"] = voice_settings
    data = renderer(api_key, text, "elevenlabs/tts", None, options)
    if not isinstance(data, bytes) or len(data) == 0:
        raise RuntimeError("ElevenLabs returned empty audio")
    _cache_put(key, data)
    return (data, False)


# ── STT ─────────────────────────────────────────────────────────────────────

def stt_engine():
    """"local" | "cloud" | "none" - which transcription engine would run."""
    status_fn = _FNS["whisper_status"]
    find_bin = _FNS["whisper_find_bin"]
    resolve = _FNS["resolve_provider_key"]
    try:
        st = status_fn() if callable(status_fn) else {}
    except Exception:
        st = {}
    have_ffmpeg = bool(shutil.which("ffmpeg") or os.path.isfile("/opt/homebrew/bin/ffmpeg"))
    if callable(find_bin) and find_bin() and st.get("model") and have_ffmpeg:
        return "local"
    if callable(resolve) and resolve("openai"):
        return "cloud"
    return "none"


def stt_text(audio_bytes, mime=None):
    """Transcribe one recorded blob. Returns
    {"ok": bool, "text": str, "engine": str, ["error": str]}.
    "no engine" is ok:False with engine "none" - a capability gap, not a
    request failure (callers reply 200 so the client downgrades cleanly)."""
    whisper_local = _FNS["whisper_local"]
    whisper_cloud = _FNS["whisper_cloud"]
    find_bin = _FNS["whisper_find_bin"]
    resolve = _FNS["resolve_provider_key"]
    suffix = ".webm"
    m = (mime or "").lower()
    if "mp4" in m or "aac" in m or "m4a" in m:
        suffix = ".mp4"
    elif "ogg" in m:
        suffix = ".ogg"
    elif "wav" in m:
        suffix = ".wav"
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    try:
        tmp.write(audio_bytes)
        tmp.close()
        engine = stt_engine()
        if engine == "local":
            ffmpeg = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
            try:
                res = whisper_local(find_bin(), ffmpeg, tmp.name)
                if res is not None:
                    return {"ok": True, "text": res.get("full") or "",
                            "engine": res.get("engine") or "whisper.cpp"}
            except Exception as e:
                print("[voice] local whisper failed: %s" % e, flush=True)
            engine = "cloud" if (callable(resolve) and resolve("openai")) else "none"
        if engine == "cloud":
            try:
                res = whisper_cloud(resolve("openai"), tmp.name)
                if res is not None:
                    return {"ok": True, "text": res.get("full") or "",
                            "engine": res.get("engine") or "openai/whisper-1"}
            except Exception as e:
                print("[voice] cloud whisper failed: %s" % e, flush=True)
                return {"ok": False, "text": "", "engine": "cloud",
                        "error": "transcription failed"}
        return {"ok": False, "text": "", "engine": "none",
                "error": "no transcription engine (enable User Testing to provision whisper, or add an OpenAI key)"}
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


# ── status ──────────────────────────────────────────────────────────────────

def status():
    """Capability probe for the client helper's fallback tiering."""
    resolve = _FNS["resolve_provider_key"]
    has_tts = bool(callable(resolve) and resolve("elevenlabs"))
    return {"ok": True, "tts": has_tts, "stt": stt_engine(),
            "defaultVoiceId": DEFAULT_VOICE_ID}

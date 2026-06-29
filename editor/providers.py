"""Host-side connection store for backend / database providers (Supabase first).

Mirrors the GitHub token model in git_ops.py: a provider's API token lives
OUTSIDE any repo at ~/.woven/providers/<provider>.json, mode 0600, and is NEVER
written into a project, into publish.json, or shipped to the browser. The publish
orchestrator reads it host-side so the user connects ONCE (via a Woven button)
instead of pasting a token into chat.

Provider-agnostic by design: add a new backend (Firebase, PocketBase, Neon,
Cloudflare D1, Appwrite, ...) by adding a PROVIDERS entry + a `validate` branch.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

_PROVIDERS_DIR = os.path.expanduser("~/.woven/providers")

# Registry of supported backends. The UI reads label / tokenLabel / tokenHint /
# tokenUrl to render the Connect field; `validate` proves the token works.
PROVIDERS = {
    "supabase": {
        "label": "Supabase",
        "tokenLabel": "Management API token",
        "tokenHint": "Generate at supabase.com/dashboard/account/tokens (starts with sbp_).",
        "tokenUrl": "https://supabase.com/dashboard/account/tokens",
    },
    "cloudflare": {
        "label": "Cloudflare",
        "tokenLabel": "API token",
        "tokenHint": "Create at dash.cloudflare.com/profile/api-tokens (D1 + R2 + Pages edit) for the all-Cloudflare backend.",
        "tokenUrl": "https://dash.cloudflare.com/profile/api-tokens",
    },
}


def _path(provider):
    return os.path.join(_PROVIDERS_DIR, provider + ".json")


def save(provider, token, meta=None):
    os.makedirs(_PROVIDERS_DIR, exist_ok=True)
    p = _path(provider)
    with open(p, "w", encoding="utf-8") as f:
        json.dump({"token": token, "meta": meta or {}}, f)
    try:
        os.chmod(p, 0o600)
    except OSError:
        pass


def load(provider):
    try:
        with open(_path(provider), "r", encoding="utf-8") as f:
            return json.load(f) or {}
    except Exception:
        return {}


def token(provider):
    return (load(provider) or {}).get("token") or ""


def clear(provider):
    try:
        os.remove(_path(provider))
    except OSError:
        pass


def status():
    """{provider: {label, tokenLabel, tokenHint, tokenUrl, connected, meta}} -
    NEVER includes the token itself (only label + avatar-like meta surface)."""
    out = {}
    for pid, meta in PROVIDERS.items():
        rec = load(pid)
        out[pid] = {
            "label":      meta["label"],
            "tokenLabel": meta.get("tokenLabel", "API token"),
            "tokenHint":  meta.get("tokenHint", ""),
            "tokenUrl":   meta.get("tokenUrl", ""),
            "connected":  bool(rec.get("token")),
            "meta":       rec.get("meta", {}),
        }
    return out


def validate(provider, tok):
    """Prove the token works against the provider's API. Returns (ok, meta|error)."""
    tok = (tok or "").strip()
    if not tok:
        return False, {"error": "empty token"}
    if provider == "supabase":
        return _validate_supabase(tok)
    if provider == "cloudflare":
        return _validate_cloudflare(tok)
    return False, {"error": "unknown provider: " + str(provider)}


def _sb_get(tok, path):
    """GET a Supabase Management API path. Returns (http_code, parsed_json|None).
    code 0 = could not reach Supabase at all."""
    req = urllib.request.Request(
        "https://api.supabase.com" + path,
        headers={"Authorization": "Bearer " + tok, "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            try:
                return r.status, json.loads(r.read().decode("utf-8") or "null")
            except Exception:
                return r.status, None
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception:
        return 0, None


def _validate_supabase(tok):
    """A USABLE Management token can list its own projects even when org-level
    reads are out of scope, so try /v1/projects first and fall back to
    /v1/organizations. 403 means the token is authenticated but scoped - that is
    still a real, usable token (the publish agent provisions with project-level
    calls), so accept it. Only a clear 401 (or no Supabase response) is a reject -
    do NOT block a token that actually works."""
    last = None
    for path in ("/v1/projects", "/v1/organizations"):
        code, data = _sb_get(tok, path)
        if 200 <= code < 300:
            meta = {}
            if isinstance(data, list):
                meta = {"count": len(data), "kind": path.rsplit("/", 1)[-1]}
            return True, meta
        if code == 403:
            return True, {"scope": "limited"}   # authenticated, just not org-read
        last = code
    if last == 0:
        return False, {"error": "could not reach Supabase to verify the token"}
    if last == 401:
        return False, {"error": "token rejected by Supabase - it must be a Management API token from supabase.com/dashboard/account/tokens (starts with sbp_), not a project anon/service key"}
    return False, {"error": "Supabase rejected the token (HTTP " + str(last) + ")"}


def _validate_cloudflare(tok):
    req = urllib.request.Request(
        "https://api.cloudflare.com/client/v4/user/tokens/verify",
        headers={"Authorization": "Bearer " + tok, "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            return False, {"error": "token rejected by Cloudflare (invalid or wrong scope)"}
        return False, {"error": "Cloudflare API error " + str(e.code)}
    except Exception as e:
        return False, {"error": "could not reach Cloudflare: " + str(e)}
    if not (isinstance(data, dict) and data.get("success")):
        return False, {"error": "Cloudflare rejected the token"}
    st = (data.get("result") or {}).get("status")
    if st != "active":
        return False, {"error": "token status: " + str(st)}
    return True, {"status": "active"}

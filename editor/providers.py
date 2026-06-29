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
    return False, {"error": "unknown provider: " + str(provider)}


def _validate_supabase(tok):
    req = urllib.request.Request(
        "https://api.supabase.com/v1/organizations",
        headers={"Authorization": "Bearer " + tok, "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode("utf-8") or "[]")
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            return False, {"error": "token rejected by Supabase (invalid or wrong scope)"}
        return False, {"error": "Supabase API error " + str(e.code)}
    except Exception as e:
        return False, {"error": "could not reach Supabase: " + str(e)}
    orgs = []
    if isinstance(data, list):
        for o in data:
            if isinstance(o, dict):
                nm = o.get("name") or o.get("id")
                if nm:
                    orgs.append(nm)
    return True, {"orgs": orgs}

"""Woven share broker.

Hands each Woven install its own stable Cloudflare tunnel so the public share
URL (https://<install>.getwoven.design/s/<token>/) never changes - across
daemon restarts, reboots, even network blips. The client calls /provision ONCE
on first run, saves the returned credentials locally, and from then on runs the
tunnel itself with no broker involvement.

  POST /provision    {installId}  -> {hostname, tunnelId, credentials}
  POST /heartbeat    {installId}  -> {ok}            (keeps the reaper away)
  POST /deprovision  {installId}  -> {ok}            (user opts out / cleanup)
  POST /admin/reap                -> {reaped}        (cron; X-Admin-Token gated)
  GET  /healthz                   -> {ok}

No Woven user accounts. The only abuse defense is per-IP rate limiting on
/provision + the reaper. The Cloudflare API token lives only here (env), never
in a shipped client.
"""
from __future__ import annotations

import os
import re
import time
from collections import defaultdict, deque
from typing import Optional

import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import cloudflare as cf
import store

INSTALL_RE = re.compile(r"^[a-f0-9]{32}$")     # client mints uuid4().hex
# Vanity published-site names: 3-30 chars, lowercase letters/numbers/hyphens,
# no leading/trailing hyphen. (Install-id-shaped names are excluded too.)
NAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{1,28}[a-z0-9])?$")
RESERVED_NAMES = {
    "www", "api", "app", "apps", "admin", "mail", "email", "smtp", "ftp", "ns",
    "ns1", "ns2", "cdn", "static", "assets", "share", "s", "live", "getwoven",
    "woven", "broker", "status", "help", "support", "docs", "blog", "dev", "test",
    "staging", "preview", "dashboard", "account", "login", "auth", "billing",
    "pay", "store", "shop", "id", "go", "link",
}
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")
REAP_TTL_DAYS = int(os.environ.get("REAP_TTL_DAYS", "45"))

# Per-IP sliding window. Single Render instance -> in-memory is fine; if you
# scale to >1 replica, move this to Postgres/Redis.
RATE_MAX = int(os.environ.get("PROVISION_RATE_MAX", "5"))      # provisions...
RATE_WINDOW = int(os.environ.get("PROVISION_RATE_WINDOW", "3600"))  # ...per hour per IP
_hits: dict[str, deque] = defaultdict(deque)

app = FastAPI(title="woven-broker")
_client: httpx.AsyncClient


@app.exception_handler(cf.CloudflareError)
async def _cf_error(request: Request, exc: cf.CloudflareError) -> JSONResponse:
    # Surface Cloudflare's actual complaint instead of a blank 500.
    return JSONResponse(status_code=502, content={"error": "cloudflare", "detail": str(exc)})


@app.on_event("startup")
async def _startup() -> None:
    global _client
    _client = httpx.AsyncClient(timeout=30)
    await store.init()


@app.on_event("shutdown")
async def _shutdown() -> None:
    await _client.aclose()
    await store.close()


def _client_ip(req: Request) -> str:
    # Render/Cloudflare put the real client in CF-Connecting-IP / X-Forwarded-For.
    return (req.headers.get("cf-connecting-ip")
            or (req.headers.get("x-forwarded-for", "").split(",")[0].strip())
            or (req.client.host if req.client else "?"))


def _rate_limit(ip: str) -> None:
    now = time.time()
    dq = _hits[ip]
    while dq and dq[0] < now - RATE_WINDOW:
        dq.popleft()
    if len(dq) >= RATE_MAX:
        raise HTTPException(429, "rate limit - too many provisions from this IP")
    dq.append(now)


class InstallReq(BaseModel):
    installId: str


def _validate(install_id: str) -> str:
    if not INSTALL_RE.match(install_id or ""):
        raise HTTPException(400, "installId must be 32 lowercase hex chars")
    return install_id


@app.get("/healthz")
async def healthz() -> dict:
    return {"ok": True}


@app.post("/provision")
async def provision(body: InstallReq, request: Request) -> dict:
    install_id = _validate(body.installId)
    _rate_limit(_client_ip(request))

    # Re-provision (lost creds / fresh machine reusing the id): tear down the
    # old tunnel first. The subdomain is derived from install_id, so the new
    # tunnel re-points the SAME hostname -> the user's URL is unchanged.
    existing = await store.get(install_id)
    if existing:
        try:
            await cf.delete_tunnel(_client, existing["tunnel_id"])
        except cf.CloudflareError:
            pass  # already gone / no connections - keep going

    secret = cf.new_tunnel_secret()
    tunnel_id = await cf.create_tunnel(_client, name=install_id, tunnel_secret=secret)
    hostname = await cf.upsert_dns(_client, subdomain=install_id, tunnel_id=tunnel_id)
    await store.upsert(install_id, tunnel_id, hostname)

    return {
        "hostname": hostname,
        "tunnelId": tunnel_id,
        "credentials": cf.credentials_json(tunnel_id, secret),
    }


@app.post("/heartbeat")
async def heartbeat(body: InstallReq) -> dict:
    install_id = _validate(body.installId)
    known = await store.touch(install_id)
    # known=False -> reaped or never provisioned; client should call /provision.
    return {"ok": True, "known": known}


@app.post("/deprovision")
async def deprovision(body: InstallReq) -> dict:
    install_id = _validate(body.installId)
    row = await store.get(install_id)
    if row:
        try:
            await cf.delete_tunnel(_client, row["tunnel_id"])
        except cf.CloudflareError:
            pass
        await cf.delete_dns(_client, subdomain=install_id)
        await store.delete(install_id)
    return {"ok": True}


@app.post("/admin/reap")
async def reap(x_admin_token: str = Header(default="")) -> dict:
    if not ADMIN_TOKEN or x_admin_token != ADMIN_TOKEN:
        raise HTTPException(403, "bad admin token")
    candidates = await store.stale(REAP_TTL_DAYS)
    reaped = 0
    for row in candidates:
        try:
            await cf.delete_tunnel(_client, row["tunnel_id"])
        except cf.CloudflareError:
            pass
        await cf.delete_dns(_client, subdomain=row["install_id"])
        await store.delete(row["install_id"])
        reaped += 1
    return {"reaped": reaped, "ttlDays": REAP_TTL_DAYS}


# ── Vanity published-site names (username.getwoven.design) ────────────────
# A name maps to a PUBLISHED site, not a tunnel: we point an unproxied CNAME
# <name>.getwoven.design -> <login>.github.io so GitHub Pages serves it. The
# name is owned by a GitHub login, VERIFIED at claim time by calling GitHub
# /user with the user's own token (used once, never stored) - that stops anyone
# squatting a name pointing at an account they do not control.


class NameClaimReq(BaseModel):
    name: str
    ghLogin: str
    ghToken: str
    repo: Optional[str] = None
    target: Optional[str] = None     # defaults to <ghLogin>.github.io


def _name_ok(name: str):
    """(normalized_name, None) if usable, else (None, reason)."""
    n = (name or "").strip().lower()
    if not n:
        return None, "empty"
    if not NAME_RE.match(n):
        return None, "3-30 chars: lowercase letters, numbers, hyphens; no leading/trailing hyphen"
    if n in RESERVED_NAMES or INSTALL_RE.match(n):
        return None, "reserved"
    return n, None


async def _verify_gh(login: str, token: str) -> bool:
    """True iff `token` belongs to GitHub user `login` (case-insensitive). The
    token is used ONLY here and never stored."""
    if not (login and token):
        return False
    try:
        r = await _client.get(
            "https://api.github.com/user",
            headers={"Authorization": "token " + token,
                     "Accept": "application/vnd.github+json",
                     "User-Agent": "woven-broker"},
        )
        if r.status_code != 200:
            return False
        return (r.json().get("login") or "").lower() == login.lower()
    except Exception:
        return False


@app.get("/names/check")
async def names_check(name: str = "") -> dict:
    n, why = _name_ok(name)
    if not n:
        return {"available": False, "name": (name or "").strip().lower(), "reason": why}
    row = await store.name_get(n)
    if row:
        return {"available": False, "name": n, "reason": "taken"}
    return {"available": True, "name": n}


@app.post("/names/claim")
async def names_claim(body: NameClaimReq, request: Request) -> dict:
    _rate_limit(_client_ip(request))
    n, why = _name_ok(body.name)
    if not n:
        raise HTTPException(400, "invalid name: " + (why or ""))
    login = (body.ghLogin or "").strip()
    if not login:
        raise HTTPException(400, "ghLogin required")
    if not await _verify_gh(login, body.ghToken):
        raise HTTPException(403, f"could not verify you own the GitHub account '{login}'")
    row = await store.name_get(n)
    if row and (row["gh_login"] or "").lower() != login.lower():
        raise HTTPException(409, "name already taken")
    target = (body.target or f"{login.lower()}.github.io").strip()
    fqdn = await cf.upsert_cname(_client, subdomain=n, target=target)
    await store.name_upsert(n, login, (body.repo or ""), target, fqdn)
    return {"ok": True, "name": n, "fqdn": fqdn, "target": target}


@app.post("/names/release")
async def names_release(body: NameClaimReq, request: Request) -> dict:
    n, why = _name_ok(body.name)
    if not n:
        raise HTTPException(400, "invalid name")
    row = await store.name_get(n)
    if not row:
        return {"ok": True}
    if (row["gh_login"] or "").lower() != (body.ghLogin or "").lower() \
            or not await _verify_gh(body.ghLogin, body.ghToken):
        raise HTTPException(403, "not the owner")
    await cf.delete_dns(_client, subdomain=n)
    await store.name_delete(n)
    return {"ok": True}

"""Thin async Cloudflare API client - only the calls the broker needs.

The broker holds the account-scoped API token (env CF_API_TOKEN) and is the
ONLY place it ever lives. Clients never see it. Two resources are touched:

  cfd_tunnel  - one named tunnel per Woven install. We create it with
                config_src="local" so the CLIENT owns ingress (it points the
                hostname at its own local gate port in its own config.yml).
                We generate the tunnel_secret, send it, and reconstruct the
                credentials JSON ourselves - Cloudflare never returns it.

  dns_records - one proxied CNAME  <install>.<base-domain> -> <uuid>.cfargotunnel.com
                so the stable hostname resolves to the tunnel at the edge.
"""
from __future__ import annotations

import base64
import os
import secrets

import httpx

API = "https://api.cloudflare.com/client/v4"

CF_API_TOKEN = os.environ["CF_API_TOKEN"]
CF_ACCOUNT_ID = os.environ["CF_ACCOUNT_ID"]
CF_ZONE_ID = os.environ["CF_ZONE_ID"]
BASE_DOMAIN = os.environ.get("BASE_DOMAIN", "getwoven.design")

_HEADERS = {"Authorization": f"Bearer {CF_API_TOKEN}"}


class CloudflareError(RuntimeError):
    pass


def _check(resp: httpx.Response) -> dict:
    """Cloudflare wraps everything in {success, errors, result}. Raise on
    transport errors AND on success:false (the HTTP status alone lies)."""
    try:
        body = resp.json()
    except Exception:
        resp.raise_for_status()
        raise CloudflareError(f"non-JSON response: {resp.text[:200]}")
    if not body.get("success", False):
        raise CloudflareError(str(body.get("errors") or body))
    return body.get("result") or {}


def new_tunnel_secret() -> str:
    """32 random bytes, base64 - the shared secret that ties a credentials
    file to a tunnel. We mint it; Cloudflare stores its hash."""
    return base64.b64encode(secrets.token_bytes(32)).decode()


def credentials_json(tunnel_id: str, tunnel_secret: str) -> dict:
    """The exact shape cloudflared expects in <uuid>.json. Cloudflare never
    returns this - we assemble it from what we sent + what we got back."""
    return {
        "AccountTag": CF_ACCOUNT_ID,
        "TunnelID": tunnel_id,
        "TunnelSecret": tunnel_secret,
    }


async def create_tunnel(client: httpx.AsyncClient, name: str, tunnel_secret: str) -> str:
    """POST /accounts/{acct}/cfd_tunnel -> tunnel id (UUID)."""
    r = await client.post(
        f"{API}/accounts/{CF_ACCOUNT_ID}/cfd_tunnel",
        headers=_HEADERS,
        json={"name": name, "config_src": "local", "tunnel_secret": tunnel_secret},
    )
    return _check(r)["id"]


async def delete_tunnel(client: httpx.AsyncClient, tunnel_id: str) -> None:
    """Delete a tunnel. A tunnel with live connections refuses deletion, so
    clean up connections first, then delete. Best-effort: a 404 (already gone)
    is fine."""
    await client.delete(
        f"{API}/accounts/{CF_ACCOUNT_ID}/cfd_tunnel/{tunnel_id}/connections",
        headers=_HEADERS,
    )
    r = await client.delete(
        f"{API}/accounts/{CF_ACCOUNT_ID}/cfd_tunnel/{tunnel_id}",
        headers=_HEADERS,
    )
    if r.status_code == 404:
        return
    _check(r)


async def _find_dns(client: httpx.AsyncClient, fqdn: str) -> str | None:
    r = await client.get(
        f"{API}/zones/{CF_ZONE_ID}/dns_records",
        headers=_HEADERS,
        params={"type": "CNAME", "name": fqdn},
    )
    rows = _check(r)
    return rows[0]["id"] if rows else None


async def upsert_dns(client: httpx.AsyncClient, subdomain: str, tunnel_id: str) -> str:
    """Create-or-update the proxied CNAME for this install. Idempotent: if a
    record already exists for the name we PUT over it (re-provision re-points
    the SAME hostname at the new tunnel, so the URL never changes)."""
    fqdn = f"{subdomain}.{BASE_DOMAIN}"
    content = f"{tunnel_id}.cfargotunnel.com"
    payload = {"type": "CNAME", "name": fqdn, "content": content, "proxied": True}
    existing = await _find_dns(client, fqdn)
    if existing:
        r = await client.put(
            f"{API}/zones/{CF_ZONE_ID}/dns_records/{existing}",
            headers=_HEADERS, json=payload,
        )
    else:
        r = await client.post(
            f"{API}/zones/{CF_ZONE_ID}/dns_records",
            headers=_HEADERS, json=payload,
        )
    _check(r)
    return fqdn


async def delete_dns(client: httpx.AsyncClient, subdomain: str) -> None:
    fqdn = f"{subdomain}.{BASE_DOMAIN}"
    existing = await _find_dns(client, fqdn)
    if existing:
        await client.delete(
            f"{API}/zones/{CF_ZONE_ID}/dns_records/{existing}",
            headers=_HEADERS,
        )


async def upsert_cname(client: httpx.AsyncClient, subdomain: str, target: str) -> str:
    """Create-or-update an UNPROXIED CNAME <subdomain>.<base-domain> -> target,
    for pointing a vanity name at an external host (e.g. <login>.github.io for a
    published GitHub Pages site). DNS-only (proxied=False) so GitHub Pages can
    serve its own HTTPS cert for the custom domain. Idempotent."""
    fqdn = f"{subdomain}.{BASE_DOMAIN}"
    payload = {"type": "CNAME", "name": fqdn, "content": target, "proxied": False}
    existing = await _find_dns(client, fqdn)
    if existing:
        r = await client.put(
            f"{API}/zones/{CF_ZONE_ID}/dns_records/{existing}",
            headers=_HEADERS, json=payload,
        )
    else:
        r = await client.post(
            f"{API}/zones/{CF_ZONE_ID}/dns_records",
            headers=_HEADERS, json=payload,
        )
    _check(r)
    return fqdn

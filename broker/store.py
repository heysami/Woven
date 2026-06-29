"""Postgres-backed install registry (Supabase Postgres via DATABASE_URL).

ONE table, installs. We deliberately store NO tunnel secret - re-provisioning
deletes + recreates the tunnel under the same subdomain, so a DB breach can
never leak credentials that would let someone impersonate a user's tunnel.

Columns:
  install_id  text PK  - client-generated, validated ^[a-f0-9]{32}$
  tunnel_id   text     - Cloudflare tunnel UUID we minted for it
  hostname    text     - <install_id>.<base-domain>
  created_at  timestamptz
  last_seen   timestamptz - bumped by /heartbeat; the reaper prunes by this
"""
from __future__ import annotations

import os
from typing import Optional

import asyncpg

DATABASE_URL = os.environ["DATABASE_URL"]

_pool: Optional[asyncpg.Pool] = None


async def init() -> None:
    global _pool
    _pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
    # Vanity-name registry for PUBLISHED sites (username.getwoven.design ->
    # <login>.github.io). Self-creates so a deploy needs no manual migration;
    # the installs table is assumed to already exist.
    async with _pool.acquire() as c:
        await c.execute(
            """
            CREATE TABLE IF NOT EXISTS names (
              name       text PRIMARY KEY,
              gh_login   text NOT NULL,
              repo       text,
              target     text NOT NULL,
              fqdn       text NOT NULL,
              created_at timestamptz DEFAULT now(),
              updated_at timestamptz DEFAULT now()
            )
            """
        )


async def close() -> None:
    if _pool:
        await _pool.close()


async def get(install_id: str) -> Optional[asyncpg.Record]:
    async with _pool.acquire() as c:
        return await c.fetchrow("SELECT * FROM installs WHERE install_id=$1", install_id)


async def upsert(install_id: str, tunnel_id: str, hostname: str) -> None:
    async with _pool.acquire() as c:
        await c.execute(
            """
            INSERT INTO installs (install_id, tunnel_id, hostname, created_at, last_seen)
            VALUES ($1, $2, $3, now(), now())
            ON CONFLICT (install_id) DO UPDATE
              SET tunnel_id = EXCLUDED.tunnel_id,
                  hostname  = EXCLUDED.hostname,
                  last_seen = now()
            """,
            install_id, tunnel_id, hostname,
        )


async def touch(install_id: str) -> bool:
    """Bump last_seen. Returns False if the install is unknown (client should
    re-provision)."""
    async with _pool.acquire() as c:
        row = await c.execute(
            "UPDATE installs SET last_seen=now() WHERE install_id=$1", install_id
        )
    return row.endswith("1")


async def delete(install_id: str) -> None:
    async with _pool.acquire() as c:
        await c.execute("DELETE FROM installs WHERE install_id=$1", install_id)


async def stale(ttl_days: int) -> list:
    """Installs whose last_seen is older than the TTL - reaper candidates."""
    async with _pool.acquire() as c:
        return await c.fetch(
            "SELECT install_id, tunnel_id FROM installs "
            "WHERE last_seen < now() - ($1 || ' days')::interval",
            str(ttl_days),
        )


# ── Vanity-name registry (published-site subdomains) ──────────────────────

async def name_get(name: str) -> Optional[asyncpg.Record]:
    async with _pool.acquire() as c:
        return await c.fetchrow("SELECT * FROM names WHERE name=$1", name)


async def name_upsert(name: str, gh_login: str, repo: str, target: str, fqdn: str) -> None:
    async with _pool.acquire() as c:
        await c.execute(
            """
            INSERT INTO names (name, gh_login, repo, target, fqdn, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, now(), now())
            ON CONFLICT (name) DO UPDATE
              SET gh_login = EXCLUDED.gh_login,
                  repo     = EXCLUDED.repo,
                  target   = EXCLUDED.target,
                  fqdn     = EXCLUDED.fqdn,
                  updated_at = now()
            """,
            name, gh_login, repo, target, fqdn,
        )


async def name_delete(name: str) -> None:
    async with _pool.acquire() as c:
        await c.execute("DELETE FROM names WHERE name=$1", name)

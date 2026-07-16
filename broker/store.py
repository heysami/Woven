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
        # Hosted share snapshots (R2-backed). One row per share token; the
        # actual bytes live in the bucket under s/<token>/. refreshed_at is
        # bumped by the owning install's /heartbeat so the reaper only prunes
        # snapshots whose owner has been gone for HOSTED_TTL_DAYS.
        await c.execute(
            """
            CREATE TABLE IF NOT EXISTS hosted_shares (
              token        text PRIMARY KEY,
              install_id   text NOT NULL,
              prototype    text,
              label        text,
              bytes        bigint NOT NULL DEFAULT 0,
              files        integer NOT NULL DEFAULT 0,
              created_at   timestamptz DEFAULT now(),
              uploaded_at  timestamptz DEFAULT now(),
              refreshed_at timestamptz DEFAULT now()
            )
            """
        )
        # Offline comment inbox - comments visitors leave on a HOSTED share
        # while the owner's daemon is unreachable. The share worker posts them
        # here; the owning daemon pulls + acks them into the project's own
        # comments.json when it comes back online. payload is the normalized
        # comment JSON (text/author/anchor/pin - never screenshots).
        await c.execute(
            """
            CREATE TABLE IF NOT EXISTS hosted_comments (
              id         bigserial PRIMARY KEY,
              token      text NOT NULL,
              payload    jsonb NOT NULL,
              created_at timestamptz DEFAULT now()
            )
            """
        )
        await c.execute(
            "CREATE INDEX IF NOT EXISTS hosted_comments_token ON hosted_comments (token)"
        )
        # Hosting passcodes - uploading a snapshot requires presenting one.
        # Only the sha256 HASH is stored, so neither the repo nor a DB dump
        # reveals a usable code. Managed via the /admin/passcodes endpoints
        # (plus the HOSTED_PASSCODES env fallback in main.py).
        await c.execute(
            """
            CREATE TABLE IF NOT EXISTS hosted_passcodes (
              code_hash  text PRIMARY KEY,
              label      text,
              created_at timestamptz DEFAULT now(),
              disabled   boolean NOT NULL DEFAULT false
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


# ── Hosted share snapshots ─────────────────────────────────────────────────

async def hosted_get(token: str) -> Optional[asyncpg.Record]:
    async with _pool.acquire() as c:
        return await c.fetchrow("SELECT * FROM hosted_shares WHERE token=$1", token)


async def hosted_upsert(token: str, install_id: str, prototype: str, label: str,
                        nbytes: int, files: int) -> None:
    async with _pool.acquire() as c:
        await c.execute(
            """
            INSERT INTO hosted_shares (token, install_id, prototype, label, bytes, files,
                                       created_at, uploaded_at, refreshed_at)
            VALUES ($1, $2, $3, $4, $5, $6, now(), now(), now())
            ON CONFLICT (token) DO UPDATE
              SET install_id   = EXCLUDED.install_id,
                  prototype    = EXCLUDED.prototype,
                  label        = EXCLUDED.label,
                  bytes        = EXCLUDED.bytes,
                  files        = EXCLUDED.files,
                  uploaded_at  = now(),
                  refreshed_at = now()
            """,
            token, install_id, prototype, label, nbytes, files,
        )


async def hosted_delete(token: str) -> None:
    async with _pool.acquire() as c:
        await c.execute("DELETE FROM hosted_shares WHERE token=$1", token)


async def hosted_list(install_id: str) -> list:
    async with _pool.acquire() as c:
        return await c.fetch(
            "SELECT * FROM hosted_shares WHERE install_id=$1 ORDER BY created_at", install_id
        )


async def hosted_quota_used(install_id: str, exclude_token: str = "") -> int:
    """Total hosted bytes for an install, optionally excluding one token (the
    one being re-uploaded, whose old size is about to be replaced)."""
    async with _pool.acquire() as c:
        v = await c.fetchval(
            "SELECT COALESCE(SUM(bytes),0) FROM hosted_shares "
            "WHERE install_id=$1 AND token<>$2",
            install_id, exclude_token or "",
        )
    return int(v or 0)


async def hosted_touch(install_id: str) -> None:
    """Heartbeat: the install is alive, keep its snapshots off the reaper."""
    async with _pool.acquire() as c:
        await c.execute(
            "UPDATE hosted_shares SET refreshed_at=now() WHERE install_id=$1", install_id
        )


async def hosted_stale(ttl_days: int) -> list:
    async with _pool.acquire() as c:
        return await c.fetch(
            "SELECT token, install_id FROM hosted_shares "
            "WHERE refreshed_at < now() - ($1 || ' days')::interval",
            str(ttl_days),
        )


# ── Offline comment inbox ──────────────────────────────────────────────────

async def inbox_add(token: str, payload: str) -> None:
    async with _pool.acquire() as c:
        await c.execute(
            "INSERT INTO hosted_comments (token, payload) VALUES ($1, $2::jsonb)",
            token, payload,
        )


async def inbox_count(token: str) -> int:
    async with _pool.acquire() as c:
        v = await c.fetchval("SELECT count(*) FROM hosted_comments WHERE token=$1", token)
    return int(v or 0)


async def inbox_pull(install_id: str, limit: int = 200) -> list:
    """Pending comments across every share this install hosts. Rows stay put
    until the daemon acks them (crash-safe two-phase drain)."""
    async with _pool.acquire() as c:
        return await c.fetch(
            """
            SELECT hc.id, hc.token, hc.payload::text AS payload, hc.created_at
            FROM hosted_comments hc
            JOIN hosted_shares hs ON hs.token = hc.token
            WHERE hs.install_id = $1
            ORDER BY hc.id
            LIMIT $2
            """,
            install_id, limit,
        )


async def inbox_ack(install_id: str, ids: list) -> int:
    """Delete acked rows - only ones belonging to this install's shares."""
    if not ids:
        return 0
    async with _pool.acquire() as c:
        res = await c.execute(
            """
            DELETE FROM hosted_comments hc
            USING hosted_shares hs
            WHERE hs.token = hc.token AND hs.install_id = $1 AND hc.id = ANY($2::bigint[])
            """,
            install_id, [int(i) for i in ids],
        )
    try:
        return int(res.split()[-1])
    except Exception:
        return 0


async def inbox_purge_token(token: str) -> None:
    async with _pool.acquire() as c:
        await c.execute("DELETE FROM hosted_comments WHERE token=$1", token)


async def inbox_purge_stale(ttl_days: int) -> int:
    """Reaper: drop inbox rows whose share no longer exists, or that nobody
    collected within the TTL."""
    async with _pool.acquire() as c:
        res = await c.execute(
            "DELETE FROM hosted_comments WHERE token NOT IN (SELECT token FROM hosted_shares) "
            "OR created_at < now() - ($1 || ' days')::interval",
            str(ttl_days),
        )
    try:
        return int(res.split()[-1])
    except Exception:
        return 0


# ── Hosting passcodes ──────────────────────────────────────────────────────

async def passcode_hash_valid(code_hash: str) -> bool:
    async with _pool.acquire() as c:
        row = await c.fetchrow(
            "SELECT 1 FROM hosted_passcodes WHERE code_hash=$1 AND NOT disabled",
            code_hash,
        )
    return row is not None


async def passcode_upsert(code_hash: str, label: str) -> None:
    async with _pool.acquire() as c:
        await c.execute(
            """
            INSERT INTO hosted_passcodes (code_hash, label, created_at, disabled)
            VALUES ($1, $2, now(), false)
            ON CONFLICT (code_hash) DO UPDATE
              SET label = EXCLUDED.label, disabled = false
            """,
            code_hash, label,
        )


async def passcode_disable(code_hash: str) -> None:
    async with _pool.acquire() as c:
        await c.execute(
            "UPDATE hosted_passcodes SET disabled=true WHERE code_hash=$1", code_hash
        )


async def passcode_list() -> list:
    async with _pool.acquire() as c:
        return await c.fetch(
            "SELECT code_hash, label, created_at, disabled "
            "FROM hosted_passcodes ORDER BY created_at"
        )

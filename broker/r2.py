"""Thin Cloudflare R2 client (S3-compatible API via boto3) - hosted share
snapshots only.

The broker is the ONLY place the R2 credentials live (env R2_*), exactly like
the Cloudflare API token in cloudflare.py. Clients upload a tar.gz to the
broker; the broker fans the extracted files into the bucket. The share worker
(worker/) reads the same bucket through a zero-credential R2 binding.

Key layout in the bucket:

  s/<token>/...            one hosted snapshot per share token - the exact URL
                           space the share gate serves, so the worker can map
                           https://<install>.getwoven.design/s/<token>/<sub>
                           to object s/<token>/<sub> one-to-one.
  fonts/<install>/<name>   workspace fonts, per install - DS stylesheets
                           reference /__global_fonts/<name> root-absolute, and
                           the worker resolves that against the install taken
                           from the request hostname.

boto3 calls are blocking; callers in main.py run them through
asyncio's default executor (run_blocking below keeps that in one place).
"""
from __future__ import annotations

import asyncio
import functools
import mimetypes
import os
from typing import Optional

R2_ENDPOINT          = os.environ.get("R2_ENDPOINT", "")           # https://<acct>.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID     = os.environ.get("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.environ.get("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET            = os.environ.get("R2_BUCKET", "woven-shares")

_s3 = None


def configured() -> bool:
    return bool(R2_ENDPOINT and R2_ACCESS_KEY_ID and R2_SECRET_ACCESS_KEY and R2_BUCKET)


def _client():
    """Lazy singleton - boto3 import + client construction only when hosted
    shares are actually configured, so a broker without R2 env still boots."""
    global _s3
    if _s3 is None:
        import boto3
        from botocore.config import Config
        _s3 = boto3.client(
            "s3",
            endpoint_url=R2_ENDPOINT,
            aws_access_key_id=R2_ACCESS_KEY_ID,
            aws_secret_access_key=R2_SECRET_ACCESS_KEY,
            # R2 wants path-style-ish v4 signing; region is ignored but required.
            region_name="auto",
            config=Config(s3={"addressing_style": "virtual"}, retries={"max_attempts": 3}),
        )
    return _s3


def content_type_for(name: str) -> str:
    if name.endswith("/api/meta"):          # extensionless JSON the viewer boots on
        return "application/json; charset=utf-8"
    ctype = mimetypes.guess_type(name)[0] or "application/octet-stream"
    if ctype.startswith("text/") or ctype in (
        "application/javascript", "application/json", "image/svg+xml"
    ):
        ctype += "; charset=utf-8"
    return ctype


def put_bytes(key: str, body: bytes, content_type: Optional[str] = None) -> None:
    _client().put_object(
        Bucket=R2_BUCKET, Key=key, Body=body,
        ContentType=content_type or content_type_for(key),
    )


def delete_prefix(prefix: str) -> int:
    """Delete every object under `prefix`. Returns the count removed."""
    s3 = _client()
    removed = 0
    token = None
    while True:
        kw = {"Bucket": R2_BUCKET, "Prefix": prefix, "MaxKeys": 1000}
        if token:
            kw["ContinuationToken"] = token
        page = s3.list_objects_v2(**kw)
        keys = [{"Key": o["Key"]} for o in page.get("Contents", [])]
        if keys:
            s3.delete_objects(Bucket=R2_BUCKET, Delete={"Objects": keys, "Quiet": True})
            removed += len(keys)
        if not page.get("IsTruncated"):
            return removed
        token = page.get("NextContinuationToken")


async def run_blocking(fn, *args, **kwargs):
    """Run a blocking boto3 call off the event loop."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, functools.partial(fn, *args, **kwargs))

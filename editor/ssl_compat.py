"""CA-store fallback for interpreters whose SSL trust store is empty.

Some Python installs - most commonly a python.org macOS build where the
bundled "Install Certificates.command" was never run - ship an OpenSSL whose
default trust store contains ZERO CA roots. Every https urlopen in that
interpreter then dies with CERTIFICATE_VERIFY_FAILED before the remote host
ever sees the request, which surfaced to users as nonsense like "token
rejected by GitHub". The operating system itself always has real roots;
Python just isn't looking at them. This module points the process at a real
bundle when (and only when) the interpreter's own store is empty, so a fresh
install works with whatever python3 the machine happens to resolve.
"""
from __future__ import annotations  # keep annotations 3.9-safe (daemon runs system py)

import os
import ssl

# Well-known system CA bundles, most-likely-first for Woven's install base.
_CANDIDATE_BUNDLES = (
    "/etc/ssl/cert.pem",                     # macOS (LibreSSL system bundle)
    "/etc/ssl/certs/ca-certificates.crt",    # Debian/Ubuntu
    "/etc/pki/tls/certs/ca-bundle.crt",      # Fedora/RHEL
    "/opt/homebrew/etc/openssl@3/cert.pem",  # Homebrew arm64
    "/usr/local/etc/openssl@3/cert.pem",     # Homebrew intel
)


def _find_bundle():
    try:
        import certifi
        p = certifi.where()
        if p and os.path.isfile(p):
            return p
    except Exception:
        pass
    for p in _CANDIDATE_BUNDLES:
        if os.path.isfile(p):
            return p
    return None


def ensure_default_ca():
    """Repair the process-wide default https context if the trust store is empty.

    When the interpreter's default SSL context already has CA roots, this is a
    no-op. Otherwise it rebinds ssl's default-https-context factory (which
    urllib / http.client consult on every request) to one loaded from a real
    system bundle, and exports SSL_CERT_FILE so child processes (spawned
    agents, tool scripts) inherit the same fix. Returns the bundle path used,
    or None when nothing needed fixing / no bundle exists.
    """
    try:
        stats = ssl.create_default_context().cert_store_stats()
        if stats.get("x509_ca", 0) > 0:
            return None
    except Exception:
        pass  # a context we can't even build/inspect: try the fallback
    path = _find_bundle()
    if not path:
        return None

    def _patched_context(*args, **kwargs):
        return ssl.create_default_context(cafile=path)

    ssl._create_default_https_context = _patched_context
    os.environ["SSL_CERT_FILE"] = path
    return path

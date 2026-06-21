#!/usr/bin/env bash
# Preflight: prove the daemon code runs on the OLDEST Python a fresh install
# might use. The daemon launches via `#!/usr/bin/env python3`; on stock macOS
# that resolves to /usr/bin/python3 (3.9.x), while dev machines usually have
# 3.11/3.13 where 3.10+ syntax (PEP 604 `X | None` annotations, `match`, etc.)
# silently works. This script reproduces the 3.9 import on the dev box so the
# incompatibility is caught BEFORE rsyncing editor/ to the daemon, not after.
#
# Run from anywhere:  editor/check-compat.sh
# Exit 0 = safe to sync. Non-zero = would crash a fresh-install daemon.
set -euo pipefail

# Minimum interpreter to test against. Prefer the system python (the realistic
# fresh-install floor); allow override:  PY=python3.9 editor/check-compat.sh
PY="${PY:-/usr/bin/python3}"
DIR="$(cd "$(dirname "$0")" && pwd)"

if ! command -v "$PY" >/dev/null 2>&1; then
  echo "skip: $PY not found (set PY=<python3.9-ish> to enforce the floor)"; exit 0
fi
VER="$("$PY" -c 'import sys;print("%d.%d"%sys.version_info[:2])')"
echo "checking editor/ against Python $VER ($PY)"

# 1) compile everything - catches 3.10+ SYNTAX (match statements, etc.)
"$PY" -m compileall -q "$DIR" || { echo "FAIL: syntax not valid on $VER"; exit 1; }

# 2) import every daemon module - catches RUNTIME 3.10 features (annotation
#    evaluation of PEP 604 unions is the recurring one). __main__ guard means
#    importing serve does NOT start the server.
( cd "$DIR" && for m in prompts exports shares live git_ops serve; do
    "$PY" -c "import $m" || { echo "FAIL: 'import $m' breaks on $VER"; exit 1; }
  done )

echo "OK: editor/ runs on Python $VER - safe to sync to the daemon"

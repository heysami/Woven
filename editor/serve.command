#!/usr/bin/env bash
# Double-click this file in Finder to start the editor.
# Serves the project root (so frame iframes can resolve "../source/index.html"),
# disables HTTP caching, AND accepts POST /__save so the editor can write
# edits.json straight into the repo without a Save-As dialog.
cd "$(dirname "$0")"
PORT=5731

# ── Python preflight ────────────────────────────────────────────────────────
# Find a python3 that is 3.9+ (the daemon's floor). If the only interpreter is
# too old or missing, print a plain message and keep the window open - so a
# double-click failure is legible instead of a flash of stack trace.
find_python() {
  for cand in python3 python3.13 python3.12 python3.11 python3.10 python3.9; do
    if command -v "$cand" >/dev/null 2>&1; then
      if "$cand" -c 'import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 9) else 1)' >/dev/null 2>&1; then
        echo "$cand"; return 0
      fi
    fi
  done
  return 1
}

PY="$(find_python)"
if [ -z "$PY" ]; then
  echo ""
  echo "  Woven editor needs Python 3.9 or newer, and none was found on this Mac."
  echo ""
  echo "  Install one, then double-click this file again:"
  echo "    - macOS may offer to install the Command Line Tools (which include"
  echo "      python3) the first time you run it - accept that, or:"
  echo "    - grab an installer from https://www.python.org/downloads/"
  echo "    - or, with Homebrew: brew install python@3.12"
  echo ""
  echo "  Full setup notes: README, section 1."
  echo ""
  echo "  Press Return to close this window."
  read -r _
  exit 1
fi

( sleep 0.6 && open "http://localhost:$PORT/editor/" ) &
EDITOR_PORT=$PORT exec "$PY" ./serve.py

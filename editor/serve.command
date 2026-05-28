#!/usr/bin/env bash
# Double-click this file in Finder to start the editor.
# Serves the project root (so frame iframes can resolve "../source/index.html"),
# disables HTTP caching, AND accepts POST /__save so the editor can write
# edits.json straight into the repo without a Save-As dialog.
cd "$(dirname "$0")"
PORT=5731
( sleep 0.6 && open "http://localhost:$PORT/editor/" ) &
EDITOR_PORT=$PORT exec python3 ./serve.py

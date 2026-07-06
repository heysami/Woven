// Served by the daemon for /editor/data.js and /editor/<slug>.layout.js when
// the request carries no ?project= in workspace mode (the projects landing,
// including a fresh install with zero projects). Deliberately defines nothing:
// app.js stubs window.EDITOR_DATA itself for the landing case; this file only
// exists so those unconditional index.html script tags resolve 200 instead of
// spraying 404s into a new user's console. See serve.py translate_path.

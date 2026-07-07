# Woven.app - macOS menubar app

An alternative install path for Woven. The zip flow stays exactly as-is; this
app is purely additive: it downloads the same Release zip, runs the same
daemon (`editor/serve.py`), and renders the editor in its own native window
(WKWebView) - no Terminal, no browser.

## What it does

- First launch: downloads the latest Release from GitHub
  (`heysami/Woven`) into `~/Woven/app/<tag>/` - plain, browsable files,
  identical to unpacking the zip yourself. Later launches check the release
  tag at most once per 6 hours and download only when a new tag exists.
- Runs `python3 serve.py` with the system Python (3.9+, same floor as the
  zip flow), `TH_WORKSPACE_DIR=~/Documents/Woven`, and the user's login-shell
  PATH (so the claude/codex/opencode CLIs are found even when launched from
  Finder).
- Probes port 5731 before spawning: an already-running daemon (for example
  one you started in Terminal) is attached to, never killed. A foreign
  process on the port gets a friendly error instead of an eviction.
- Editor opens in an app window. localhost pages and blob previews open as
  in-app child windows; external links (GitHub auth, docs, trycloudflare
  share URLs) open in the default browser; downloads land in `~/Downloads`.
- Quit sends SIGTERM to the daemon it spawned (serve.py then shuts down its
  agent CLI children and cloudflared tunnels). Attached daemons are left
  untouched.
- Updates never restart the daemon by themselves - the menubar shows
  "Update ready - Restart Daemon to apply" and the user picks the moment.

## Build

Requires only the Xcode Command Line Tools (Swift 6+):

    macapp/build.sh [version]

Produces `macapp/dist/Woven.app` (ad-hoc signed) and
`macapp/dist/Woven-macos.zip` for release upload.

For Developer ID signing later:

    CODESIGN_IDENTITY="Developer ID Application: ..." macapp/build.sh 1.0.0

then notarize + staple (commands are printed by the script).

## Distribution notes (until Developer ID signing lands)

- Ad-hoc signed builds downloaded from the internet are quarantined; on
  macOS 15+ users must allow the app once via System Settings > Privacy &
  Security > "Open Anyway".
- First write into `~/Documents/Woven` and the first download into
  `~/Downloads` each trigger a one-time macOS permission prompt.

## On-disk layout

    ~/Woven/app/<tag>/          unpacked release trees (newest 2 kept)
    ~/Woven/app/current         symlink to the active tag (atomic swap)
    ~/Library/Application Support/Woven/state.json
    ~/Library/Logs/Woven/daemon.log
    ~/Documents/Woven/          workspace (projects), never touched by updates

Overrides: `defaults write com.heysami.Woven EditorPort <port>` and
`defaults write com.heysami.Woven WorkspaceDir <path>`.

`macapp/` is export-ignored in `.gitattributes`, so the Release zip that the
app itself downloads does not contain the app.

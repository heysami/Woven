"""The agent browser - a signed-in Chrome that agents use to read project
references behind a login (a private Drive file, Notion, Confluence).

Agents otherwise only have anonymous WebFetch and a Chrome MCP launched
`--headless --isolated` (a fresh profile, no logins). The user picks one of
three modes in Preview > References, stored per machine in
~/.woven/agent-browser.json:

  off     no signed-in browser; a link behind a sign-in is reported unreadable
  woven   a dedicated Chrome profile Woven keeps (~/.woven/agent-browser/
          profile). The user signs in there once; Woven starts it with remote
          debugging on a free port and agents attach to it
  chrome  the user's own running Chrome (144+), after they tick "Enable
          remote debugging" at chrome://inspect/#remote-debugging. Chrome asks
          the user to allow each agent connection.

Either way agents reach it through a SEPARATE MCP server, `reference_browser`,
added only at spawn time (serve.py _mcp_servers_for_spawn): the general
`chrome` server stays isolated, so ordinary web and page testing never runs
with the user's logins. What agents may do in it (read references, nothing
else) is said in the references block (references.agent_block).

Nothing here talks CDP: status is a DevToolsActivePort file plus a TCP probe,
which never triggers Chrome's "allow remote debugging" prompt.
"""
from __future__ import annotations  # keep annotations 3.9-safe (daemon runs system py)

import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import time

MODES = ("off", "woven", "chrome")
SERVER_ID = "reference_browser"
STATE_DIR = os.path.join(os.path.expanduser("~"), ".woven")
STATE_PATH = os.path.join(STATE_DIR, "agent-browser.json")
PROFILE_DIR = os.path.join(STATE_DIR, "agent-browser", "profile")
SPAWN_CONFIG_PATH = os.path.join(STATE_DIR, "agent-browser", "mcp-config.json")
REMOTE_DEBUG_URL = "chrome://inspect/#remote-debugging"

_LOCK = threading.Lock()
_last_launch = {"t": 0.0}
_LAUNCH_GAP_S = 20.0


def load_mode() -> str:
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            m = (json.load(f) or {}).get("mode")
    except (OSError, ValueError, AttributeError):
        return "off"
    return m if m in MODES else "off"


def save_mode(mode: str) -> str:
    if mode not in MODES:
        raise ValueError("mode must be one of: " + ", ".join(MODES))
    os.makedirs(STATE_DIR, exist_ok=True)
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"mode": mode, "updatedAt": int(time.time() * 1000)}, f)
    os.replace(tmp, STATE_PATH)
    return mode


# ── where Chrome is ─────────────────────────────────────────────────────────

def chrome_binary():
    """The Chrome executable, or None. TH_AGENT_BROWSER_BIN overrides."""
    env = os.environ.get("TH_AGENT_BROWSER_BIN")
    if env and os.path.isfile(env):
        return env
    if sys.platform == "darwin":
        for base in ("/Applications", os.path.expanduser("~/Applications")):
            p = os.path.join(base, "Google Chrome.app", "Contents", "MacOS", "Google Chrome")
            if os.path.isfile(p):
                return p
        return None
    if sys.platform.startswith("win"):
        for root in (os.environ.get("PROGRAMFILES"), os.environ.get("PROGRAMFILES(X86)"), os.environ.get("LOCALAPPDATA")):
            if root:
                p = os.path.join(root, "Google", "Chrome", "Application", "chrome.exe")
                if os.path.isfile(p):
                    return p
        return None
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        p = shutil.which(name)
        if p:
            return p
    return None


def chrome_user_dir():
    """The user's own (stable channel) Chrome profile folder."""
    if sys.platform == "darwin":
        return os.path.expanduser("~/Library/Application Support/Google/Chrome")
    if sys.platform.startswith("win"):
        return os.path.join(os.environ.get("LOCALAPPDATA") or "", "Google", "Chrome", "User Data")
    return os.path.expanduser("~/.config/google-chrome")


def _active_port(user_dir):
    """The remote-debugging port Chrome published for this profile, when
    something is actually listening on it. A bare TCP connect: no CDP
    handshake, so Chrome's allow-connection prompt never fires."""
    try:
        with open(os.path.join(user_dir, "DevToolsActivePort"), "r", encoding="utf-8") as f:
            port = int((f.readline() or "").strip())
    except (OSError, ValueError):
        return None
    if not 0 < port < 65536:
        return None
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.4):
            return port
    except OSError:
        return None


def status() -> dict:
    mode = load_mode()
    return {
        "mode": mode,
        "installed": bool(chrome_binary()),
        "woven": {
            "running": _active_port(PROFILE_DIR) is not None,
            "profile": os.path.isdir(PROFILE_DIR),
        },
        "chrome": {"debugging": _active_port(chrome_user_dir()) is not None},
        "remoteDebugUrl": REMOTE_DEBUG_URL,
    }


# ── the Woven browser ───────────────────────────────────────────────────────

def launch(url=None, background=False):
    """Start (or bring forward) the Woven browser: the dedicated profile with
    remote debugging on a free port. A second launch on the same profile hands
    `url` to the running instance, which is how "open this link in it" works.
    Returns None, or an error string."""
    binary = chrome_binary()
    if not binary:
        return "Google Chrome is not installed (set TH_AGENT_BROWSER_BIN to use another Chromium)"
    os.makedirs(PROFILE_DIR, exist_ok=True)
    flags = ["--user-data-dir=" + PROFILE_DIR, "--remote-debugging-port=0",
             "--no-first-run", "--no-default-browser-check"]
    target = [url] if url else []
    try:
        if sys.platform == "darwin":
            # `open` activates (or, with -g, does not) the way a user launch
            # would; -n starts a separate instance beside the user's Chrome.
            app = binary.split("/Contents/MacOS/")[0]
            cmd = ["open", "-n"] + (["-g"] if background else []) + ["-a", app, "--args"] + flags + target
        else:
            cmd = [binary] + flags + target
        subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)
    except OSError as e:
        return "could not start Chrome: %s" % e
    _last_launch["t"] = time.time()
    return None


def ensure_running():
    """Before an agent spawn in `woven` mode: start the browser in the
    background when it is not up. Rate-limited, because one spawn asks for
    its MCP config several times and Chrome takes a moment to publish its
    port."""
    if load_mode() != "woven":
        return
    with _LOCK:
        if _active_port(PROFILE_DIR) is not None:
            return
        if time.time() - _last_launch["t"] < _LAUNCH_GAP_S:
            return
        _last_launch["t"] = time.time()   # also when the launch fails: never hammer it
        launch(background=True)


def mcp_server_spec(mode=None):
    """The `reference_browser` MCP server for the chosen mode, or None (off).
    Tools agents do not need to read a page (performance, emulation) are left
    out; reading and navigation stay."""
    mode = mode or load_mode()
    if mode not in ("woven", "chrome"):
        return None
    args = ["-y", "chrome-devtools-mcp@latest", "--autoConnect",
            "--no-usage-statistics", "--no-performance-crux",
            "--no-category-performance", "--no-category-emulation"]
    if mode == "woven":
        args += ["--userDataDir", PROFILE_DIR]
    return {"command": "npx", "args": args}


def write_spawn_config(servers: dict):
    """The claude `--mcp-config` file carrying the agent browser next to the
    configured servers. Machine-local (it names this machine's profile path),
    so it lives under ~/.woven, never in the install. Rewritten only when it
    changed. Returns its path, or None when it could not be written."""
    body = json.dumps({"mcpServers": servers}, indent=2, sort_keys=True)
    try:
        with open(SPAWN_CONFIG_PATH, "r", encoding="utf-8") as f:
            if f.read() == body:
                return SPAWN_CONFIG_PATH
    except OSError:
        pass
    try:
        os.makedirs(os.path.dirname(SPAWN_CONFIG_PATH), exist_ok=True)
        tmp = SPAWN_CONFIG_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(body)
        os.replace(tmp, SPAWN_CONFIG_PATH)
        return SPAWN_CONFIG_PATH
    except OSError:
        return None

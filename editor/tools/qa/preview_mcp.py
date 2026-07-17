#!/usr/bin/env python3
"""claude_preview MCP server - real preview tools for daemon-spawned agents.

Every builder/lens playbook in .claude/agents/ lists mcp__claude_preview__*
tools (preview_start / preview_eval / preview_screenshot / ...). Those names
come from the Claude desktop app's built-in preview pane - a server that has
never existed for the CLI agents the Woven daemon spawns, so builders sat in
20+ minute hangs on tools that were never going to answer (the vicecity /
pocket-monster build stalls). This file IS that server: a stdio MCP process
wired into .claude/mcp-config.json as "claude_preview" (the CLI rejects uppercase server names), so the playbooks'
tool lists resolve for real.

Backing: the same Playwright headless Chrome tools/qa/visual_qa.py uses,
launched with SwiftShader flags so WebGL/three.js scenes render (plain
headless Chrome reports no WebGL and every 3D self-test false-fails).

Resilience: all Playwright calls run on one worker thread behind a hard
watchdog (TOOL_TIMEOUT_S); a hung page gets its Chrome killed + relaunched
instead of wedging the serial stdin loop, and an idle reaper closes Chrome
after IDLE_SHUTDOWN_S so hung parent agents can't stockpile SwiftShader
Chromes that saturate the CPU.

Protocol: MCP over stdio - one JSON-RPC 2.0 message per line. No external
MCP SDK dependency; the daemon's fresh-install floor is Python 3.9 and this
file must import there (playwright itself is checked lazily so tools/list
still answers and the error surfaces inside the tool result, not as a dead
server).

Run standalone for a protocol smoke test:
  printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
    | python3 editor/tools/qa/preview_mcp.py
"""

import base64
import json
import os
import queue
import signal
import subprocess
import sys
import tempfile
import threading
import time
import traceback

PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "claude_preview", "version": "1.1.0"}
DEFAULT_VIEWPORT = (1280, 800)
MAX_LOG_ENTRIES = 500          # per-tab console/network ring buffer cap
ACTION_TIMEOUT_MS = 10000
SNAPSHOT_MAX_CHARS = 40000
# Hard cap per tool call. page.evaluate has NO Playwright timeout, so an eval
# against a CPU-pegged page blocks forever and, because this server answers
# stdin serially, every later call then dies at the CLI's 120s MCP timeout
# (the teamfantasy landofdawn wedge). Must stay well under 120s so the error
# reaches the agent instead of the harness timeout.
TOOL_TIMEOUT_S = int(os.environ.get("PREVIEW_MCP_TOOL_TIMEOUT_S") or 90)
# Close Chrome after this long with no tool calls. Node agents sometimes hang
# without exiting; stdin never hits EOF, and their SwiftShader Chromes pile up
# burning CPU for hours. Chrome relaunches lazily on the next call.
IDLE_SHUTDOWN_S = int(os.environ.get("PREVIEW_MCP_IDLE_SHUTDOWN_S") or 900)

SHOT_DIR = os.path.join(tempfile.gettempdir(), "woven-preview-mcp")


def log(msg):
    sys.stderr.write("[preview-mcp] %s\n" % msg)
    sys.stderr.flush()


# ---------------------------------------------------------------------------
# Browser state
# ---------------------------------------------------------------------------

class Tab(object):
    def __init__(self, tab_id, page):
        self.id = tab_id
        self.page = page
        self.console = []   # {level, text, ts}
        self.network = []   # {method, url, status, ts}


class Browser(object):
    """Lazy Playwright wrapper. One Chrome, N tabs."""

    _SEQ = [0]  # process-global so tab ids never repeat across hard resets

    def __init__(self):
        self._pw = None
        self._browser = None
        self._context = None
        self.label = None
        self.tabs = {}
        self.active = None   # tab id most recently used

    def _ensure(self):
        if self._context is not None:
            return
        from playwright.sync_api import sync_playwright  # noqa - lazy: absence must surface per-call
        self._pw = sync_playwright().start()
        # SwiftShader: software WebGL so three.js / shader self-tests render
        # under headless QA instead of hitting the no-WebGL fallback poster.
        launch_args = ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
        try:
            self._browser = self._pw.chromium.launch(
                channel="chrome", headless=True, args=launch_args)
            self.label = "chrome (channel=chrome)"
        except Exception as exc:
            log("channel=chrome launch failed (%s); trying bundled chromium" % exc)
            self._browser = self._pw.chromium.launch(headless=True, args=launch_args)
            self.label = "chromium (bundled)"
        vw, vh = DEFAULT_VIEWPORT
        self._context = self._browser.new_context(
            viewport={"width": vw, "height": vh})
        try:
            self._context.grant_permissions(["camera", "microphone"])
        except Exception:
            pass
        self._context.set_default_timeout(ACTION_TIMEOUT_MS)

    def open(self, url, width=None, height=None):
        self._ensure()
        page = self._context.new_page()
        if width and height:
            page.set_viewport_size({"width": int(width), "height": int(height)})
        Browser._SEQ[0] += 1
        tab = Tab("tab%d" % Browser._SEQ[0], page)
        self.tabs[tab.id] = tab
        self.active = tab.id

        def _on_console(msg, _tab=tab):
            try:
                _tab.console.append({"level": msg.type, "text": msg.text,
                                     "ts": time.time()})
                del _tab.console[:-MAX_LOG_ENTRIES]
            except Exception:
                pass

        def _on_page_error(err, _tab=tab):
            try:
                _tab.console.append({"level": "error", "text": str(err),
                                     "ts": time.time()})
                del _tab.console[:-MAX_LOG_ENTRIES]
            except Exception:
                pass

        def _on_response(resp, _tab=tab):
            try:
                _tab.network.append({
                    "method": resp.request.method, "url": resp.url,
                    "status": resp.status, "ts": time.time()})
                del _tab.network[:-MAX_LOG_ENTRIES]
            except Exception:
                pass

        def _on_request_failed(req, _tab=tab):
            try:
                _tab.network.append({
                    "method": req.method, "url": req.url,
                    "status": None,
                    "error": getattr(req, "failure", None) or "failed",
                    "ts": time.time()})
                del _tab.network[:-MAX_LOG_ENTRIES]
            except Exception:
                pass

        page.on("console", _on_console)
        page.on("pageerror", _on_page_error)
        page.on("response", _on_response)
        page.on("requestfailed", _on_request_failed)
        try:
            page.goto(url, wait_until="load", timeout=30000)
        except Exception:
            # failed start must not leave a zombie tab: it becomes `active`,
            # so later tabId-less evals target the broken page and hang
            self.close_tab(tab.id)
            raise
        return tab

    def tab(self, tab_id=None):
        tid = tab_id or self.active
        if not tid or tid not in self.tabs:
            raise RuntimeError(
                "no open preview tab%s - call preview_start first"
                % (" %r" % tab_id if tab_id else ""))
        self.active = tid
        return self.tabs[tid]

    def close_tab(self, tab_id=None):
        if tab_id:
            tab = self.tabs.pop(tab_id, None)
            if tab is None:
                return "tab %r was not open" % tab_id
            try:
                tab.page.close()
            except Exception:
                pass
            if self.active == tab_id:
                self.active = next(iter(self.tabs), None)
            return "closed %s" % tab_id
        # no tabId - close everything
        for tab in list(self.tabs.values()):
            try:
                tab.page.close()
            except Exception:
                pass
        self.tabs.clear()
        self.active = None
        return "closed all preview tabs"

    def is_up(self):
        return self._context is not None

    def shutdown(self):
        try:
            if self._browser is not None:
                self._browser.close()
        except Exception:
            pass
        try:
            if self._pw is not None:
                self._pw.stop()
        except Exception:
            pass
        self._pw = None
        self._browser = None
        self._context = None
        self.tabs.clear()
        self.active = None


BROWSER = Browser()


def normalise_url(url):
    """Full URLs pass through. A path starting with / is served by the
    daemon when TH_DAEMON_URL is set (so ?project stamping and daemon
    endpoints keep working); anything else is treated as a local file."""
    url = (url or "").strip()
    if "://" in url:
        return url
    daemon = (os.environ.get("TH_DAEMON_URL") or "").rstrip("/")
    if url.startswith("/") and daemon:
        return daemon + url
    return "file://" + os.path.abspath(url)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

def _text(payload):
    if not isinstance(payload, str):
        payload = json.dumps(payload, indent=2, default=str)
    return {"content": [{"type": "text", "text": payload}]}


TAB_PROP = {"type": "string",
            "description": "Tab to act on (from preview_start). Defaults to the most recently used tab."}


def tool_preview_start(args):
    url = args.get("url") or args.get("path")
    if not url:
        raise ValueError("url is required - a full http(s) URL, a daemon path "
                         "starting with / (served at $TH_DAEMON_URL), or a local file path")
    tab = BROWSER.open(normalise_url(url),
                       width=args.get("width"), height=args.get("height"))
    return _text({"tabId": tab.id, "serverId": tab.id,
                  "url": tab.page.url, "title": tab.page.title(),
                  "browser": BROWSER.label})


def tool_preview_stop(args):
    return _text(BROWSER.close_tab(args.get("tabId") or args.get("serverId")))


def tool_preview_eval(args):
    js = args.get("js") or args.get("text") or args.get("expression")
    if not js:
        raise ValueError("js is required")
    tab = BROWSER.tab(args.get("tabId"))
    try:
        result = tab.page.evaluate(js)
    except Exception:
        # statements ("const x = ...; return x") need a function wrapper;
        # async so top-level await works (evaluate awaits returned promises)
        result = tab.page.evaluate("async () => { %s }" % js)
    return _text({"result": result})


def tool_preview_console_logs(args):
    tab = BROWSER.tab(args.get("tabId"))
    entries = tab.console
    level = (args.get("level") or "").strip().lower()
    if level and level != "all":
        if level == "error":
            entries = [e for e in entries if e["level"] in ("error", "assert")]
        else:
            entries = [e for e in entries if e["level"] == level]
    search = args.get("search") or args.get("pattern")
    if search:
        entries = [e for e in entries if search in e["text"]]
    limit = int(args.get("limit") or args.get("lines") or 100)
    entries = entries[-limit:]
    return _text({"count": len(entries),
                  "entries": [{"level": e["level"], "text": e["text"][:2000]}
                              for e in entries]})


def tool_preview_network(args):
    tab = BROWSER.tab(args.get("tabId"))
    entries = tab.network
    pat = args.get("urlPattern") or args.get("search")
    if pat:
        entries = [e for e in entries if pat in e["url"]]
    limit = int(args.get("limit") or 50)
    return _text({"count": len(entries[-limit:]), "requests": entries[-limit:]})


def tool_preview_inspect(args):
    sel = args.get("selector")
    if not sel:
        raise ValueError("selector is required")
    tab = BROWSER.tab(args.get("tabId"))
    info = tab.page.evaluate(
        """(sel) => {
            const els = document.querySelectorAll(sel);
            if (!els.length) return {count: 0};
            const el = els[0];
            const cs = getComputedStyle(el);
            const r = el.getBoundingClientRect();
            return {
                count: els.length,
                tag: el.tagName.toLowerCase(),
                rect: {x: r.x, y: r.y, width: r.width, height: r.height},
                computed: {display: cs.display, visibility: cs.visibility,
                           opacity: cs.opacity, position: cs.position,
                           zIndex: cs.zIndex},
                text: (el.innerText || '').slice(0, 400),
                outerHTML: el.outerHTML.slice(0, 2000)
            };
        }""", sel)
    return _text(info)


def tool_preview_snapshot(args):
    tab = BROWSER.tab(args.get("tabId"))
    max_chars = int(args.get("max_chars") or SNAPSHOT_MAX_CHARS)
    body_text = tab.page.evaluate("() => document.body ? document.body.innerText : ''")
    return _text({"url": tab.page.url, "title": tab.page.title(),
                  "text": (body_text or "")[:max_chars]})


def tool_preview_screenshot(args):
    tab = BROWSER.tab(args.get("tabId"))
    os.makedirs(SHOT_DIR, exist_ok=True)
    path = args.get("path") or os.path.join(
        SHOT_DIR, "%s-%d.jpg" % (tab.id, int(time.time() * 1000)))
    raw = tab.page.screenshot(path=path, type="jpeg", quality=70,
                              full_page=bool(args.get("fullPage")))
    return {"content": [
        {"type": "image", "data": base64.b64encode(raw).decode("ascii"),
         "mimeType": "image/jpeg"},
        {"type": "text", "text": "saved to %s" % path},
    ]}


def tool_preview_click(args):
    sel = args.get("selector")
    if not sel:
        raise ValueError("selector is required")
    tab = BROWSER.tab(args.get("tabId"))
    tab.page.click(sel, timeout=ACTION_TIMEOUT_MS)
    return _text("clicked %s" % sel)


def tool_preview_fill(args):
    sel = args.get("selector")
    if not sel:
        raise ValueError("selector is required")
    tab = BROWSER.tab(args.get("tabId"))
    tab.page.fill(sel, str(args.get("value") or ""), timeout=ACTION_TIMEOUT_MS)
    return _text("filled %s" % sel)


def tool_preview_resize(args):
    tab = BROWSER.tab(args.get("tabId"))
    w = int(args.get("width") or DEFAULT_VIEWPORT[0])
    h = int(args.get("height") or DEFAULT_VIEWPORT[1])
    tab.page.set_viewport_size({"width": w, "height": h})
    return _text("viewport %dx%d" % (w, h))


TOOLS = [
    ("preview_start",
     "Open a page in the headless preview Chrome (WebGL-capable via SwiftShader). "
     "Pass a full http(s) URL, a daemon path starting with / (resolved against "
     "$TH_DAEMON_URL so ?project stamping works), or a local file path. "
     "Returns a tabId for the other preview_* tools.",
     {"type": "object",
      "properties": {
          "url": {"type": "string", "description": "URL, /daemon-path, or local file path to open"},
          "width": {"type": "number", "description": "viewport width (default 1280)"},
          "height": {"type": "number", "description": "viewport height (default 800)"}},
      "required": ["url"]},
     tool_preview_start),
    ("preview_stop",
     "Close one preview tab (tabId) or, with no arguments, all of them.",
     {"type": "object", "properties": {"tabId": TAB_PROP}},
     tool_preview_stop),
    ("preview_eval",
     "Evaluate JavaScript in the page and return the JSON-serialised result. "
     "Expressions evaluate directly; multi-statement code is auto-wrapped in "
     "a function, so use `return` for its result.",
     {"type": "object",
      "properties": {"js": {"type": "string", "description": "JavaScript to evaluate"},
                     "tabId": TAB_PROP},
      "required": ["js"]},
     tool_preview_eval),
    ("preview_console_logs",
     "Console output (log/info/warn/error + uncaught page errors) captured "
     "since the tab opened.",
     {"type": "object",
      "properties": {"level": {"type": "string",
                               "description": "'all' (default) or a level like 'error'"},
                     "search": {"type": "string", "description": "substring filter"},
                     "limit": {"type": "number", "description": "max entries (default 100)"},
                     "tabId": TAB_PROP}},
     tool_preview_console_logs),
    ("preview_network",
     "Network requests (method, url, status) captured since the tab opened.",
     {"type": "object",
      "properties": {"urlPattern": {"type": "string", "description": "substring filter on URL"},
                     "limit": {"type": "number", "description": "max entries (default 50)"},
                     "tabId": TAB_PROP}},
     tool_preview_network),
    ("preview_inspect",
     "Inspect the first element matching a CSS selector: match count, rect, "
     "computed display/visibility/opacity, text, trimmed outerHTML. Use this "
     "(not element.hidden) to verify visibility.",
     {"type": "object",
      "properties": {"selector": {"type": "string"}, "tabId": TAB_PROP},
      "required": ["selector"]},
     tool_preview_inspect),
    ("preview_snapshot",
     "Page snapshot: url, title and visible body text (truncated). Prefer "
     "this over a screenshot for verifying text content.",
     {"type": "object",
      "properties": {"max_chars": {"type": "number"}, "tabId": TAB_PROP}},
     tool_preview_snapshot),
    ("preview_screenshot",
     "Screenshot the tab (JPEG). Returns the image inline plus the saved "
     "file path.",
     {"type": "object",
      "properties": {"fullPage": {"type": "boolean", "description": "capture full page height"},
                     "path": {"type": "string", "description": "save path (default temp dir)"},
                     "tabId": TAB_PROP}},
     tool_preview_screenshot),
    ("preview_click",
     "Click the element matching a CSS selector.",
     {"type": "object",
      "properties": {"selector": {"type": "string"}, "tabId": TAB_PROP},
      "required": ["selector"]},
     tool_preview_click),
    ("preview_fill",
     "Fill an input/textarea/select matching a CSS selector.",
     {"type": "object",
      "properties": {"selector": {"type": "string"}, "value": {"type": "string"},
                     "tabId": TAB_PROP},
      "required": ["selector", "value"]},
     tool_preview_fill),
    ("preview_resize",
     "Resize the tab viewport.",
     {"type": "object",
      "properties": {"width": {"type": "number"}, "height": {"type": "number"},
                     "tabId": TAB_PROP},
      "required": ["width", "height"]},
     tool_preview_resize),
]

TOOL_HANDLERS = dict((name, fn) for name, _d, _s, fn in TOOLS)


# ---------------------------------------------------------------------------
# Playwright worker thread + watchdog
#
# Sync Playwright objects are bound to the thread that created them, so ONE
# worker thread owns every browser touch. The stdin loop submits jobs and
# waits with a hard timeout; on timeout it answers the agent with an error,
# SIGKILLs the Chrome/driver process tree (which unblocks the stuck call),
# and swaps in a FRESH worker thread + Browser. The old thread is abandoned,
# not reused: graceful close() hangs on the dead driver pipe, and its parked
# greenlet event loop makes sync_playwright refuse to start again on that
# thread. One hung page can no longer wedge the whole server.
# ---------------------------------------------------------------------------

class _Job(object):
    def __init__(self, fn, args):
        self.fn = fn
        self.args = args
        self.result_q = queue.Queue(maxsize=1)


_STATE = {"jobs": None}          # current worker generation's job queue
_LAST_ACTIVITY = [time.time()]   # boxed so threads share one slot


def _worker(jobs_q):
    while True:
        job = jobs_q.get()
        # bump on the worker at start AND end so an in-flight call always
        # counts as activity - the reaper's re-check runs on this same
        # thread, so it can never observe a stale clock mid-job
        _LAST_ACTIVITY[0] = time.time()
        try:
            out = ("ok", job.fn(job.args))
        except Exception as exc:
            out = ("err", exc)
        _LAST_ACTIVITY[0] = time.time()
        try:
            job.result_q.put_nowait(out)
        except Exception:
            pass  # abandoned job - the watchdog already answered for it


def _start_worker():
    jobs_q = queue.Queue()
    _STATE["jobs"] = jobs_q
    threading.Thread(target=_worker, args=(jobs_q,), daemon=True).start()


def _descendant_pids():
    """All live descendants of this process (playwright driver + Chrome tree)."""
    try:
        out = subprocess.check_output(["ps", "-axo", "pid=,ppid="],
                                      universal_newlines=True)
    except Exception:
        return []
    children = {}
    for row in out.splitlines():
        parts = row.split()
        if len(parts) != 2:
            continue
        try:
            pid, ppid = int(parts[0]), int(parts[1])
        except ValueError:
            continue
        children.setdefault(ppid, []).append(pid)
    found, frontier = [], [os.getpid()]
    while frontier:
        kids = children.get(frontier.pop(), [])
        found.extend(kids)
        frontier.extend(kids)
    return found


def _force_kill_browser_procs():
    pids = _descendant_pids()
    for pid in pids:
        try:
            os.kill(pid, signal.SIGKILL)
        except Exception:
            pass
    if pids:
        log("force-killed %d browser process(es)" % len(pids))
    # reap zombies so they don't reappear in later _descendant_pids sweeps
    try:
        while os.waitpid(-1, os.WNOHANG)[0] > 0:
            pass
    except Exception:
        pass


def _hard_reset():
    """Post-watchdog recovery: kill the browser tree and abandon the poisoned
    worker generation (thread + Browser). The next call starts fresh."""
    global BROWSER
    _force_kill_browser_procs()
    BROWSER = Browser()
    _start_worker()
    log("hard reset - fresh worker + browser generation")


def run_tool(fn, args):
    """Run a tool on the worker thread with a hard watchdog timeout."""
    _LAST_ACTIVITY[0] = time.time()
    job = _Job(fn, args)
    _STATE["jobs"].put(job)
    try:
        status, payload = job.result_q.get(timeout=TOOL_TIMEOUT_S)
    except queue.Empty:
        _hard_reset()
        raise RuntimeError(
            "preview tool hung for %ds (page unresponsive); headless Chrome "
            "was killed and relaunches on the next preview_start - all "
            "previous tabIds are gone" % TOOL_TIMEOUT_S)
    if status == "err":
        raise payload
    return payload


def _idle_close(_args):
    # re-check inside the worker: a call may have landed since the reaper woke
    if BROWSER.is_up() and time.time() - _LAST_ACTIVITY[0] >= IDLE_SHUTDOWN_S:
        BROWSER.shutdown()
        log("idle > %ds - closed headless Chrome (relaunches lazily)"
            % IDLE_SHUTDOWN_S)
    return None


def _idle_reaper():
    while True:
        time.sleep(30)
        if not BROWSER.is_up():
            continue
        if time.time() - _LAST_ACTIVITY[0] < IDLE_SHUTDOWN_S:
            continue
        job = _Job(_idle_close, None)
        _STATE["jobs"].put(job)
        try:
            job.result_q.get(timeout=TOOL_TIMEOUT_S)
        except queue.Empty:
            _hard_reset()


# ---------------------------------------------------------------------------
# JSON-RPC / MCP plumbing
# ---------------------------------------------------------------------------

def _reply(msg_id, result):
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def _error(msg_id, code, message):
    return {"jsonrpc": "2.0", "id": msg_id,
            "error": {"code": code, "message": message}}


def handle(msg):
    """Returns a response dict, or None for notifications."""
    method = msg.get("method")
    msg_id = msg.get("id")
    params = msg.get("params") or {}
    if method == "initialize":
        return _reply(msg_id, {
            "protocolVersion": params.get("protocolVersion") or PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": SERVER_INFO,
        })
    if method in ("notifications/initialized", "notifications/cancelled"):
        return None
    if method == "ping":
        return _reply(msg_id, {})
    if method == "tools/list":
        return _reply(msg_id, {"tools": [
            {"name": name, "description": desc, "inputSchema": schema}
            for name, desc, schema, _fn in TOOLS]})
    if method == "resources/list":
        return _reply(msg_id, {"resources": []})
    if method == "prompts/list":
        return _reply(msg_id, {"prompts": []})
    if method == "tools/call":
        name = params.get("name")
        fn = TOOL_HANDLERS.get(name)
        if fn is None:
            return _error(msg_id, -32602, "unknown tool %r" % name)
        try:
            result = run_tool(fn, params.get("arguments") or {})
            return _reply(msg_id, result)
        except Exception as exc:
            log("tool %s failed: %s" % (name, traceback.format_exc().strip().splitlines()[-1]))
            return _reply(msg_id, {
                "content": [{"type": "text",
                             "text": "%s: %s" % (type(exc).__name__, exc)}],
                "isError": True,
            })
    if msg_id is None:
        return None  # unknown notification - ignore
    return _error(msg_id, -32601, "method %r not found" % method)


def main():
    log("starting (pid %d)" % os.getpid())
    _start_worker()
    threading.Thread(target=_idle_reaper, daemon=True).start()
    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except Exception:
                log("skipping unparseable line: %r" % line[:200])
                continue
            resp = handle(msg)
            if resp is not None:
                sys.stdout.write(json.dumps(resp, default=str) + "\n")
                sys.stdout.flush()
    finally:
        # stdin EOF = parent CLI exited; never outlive it. Graceful close via
        # the worker (playwright is thread-bound), then force-kill leftovers.
        job = _Job(lambda _a: BROWSER.shutdown(), None)
        _STATE["jobs"].put(job)
        try:
            job.result_q.get(timeout=10)
        except queue.Empty:
            pass
        _force_kill_browser_procs()
        log("shut down")


if __name__ == "__main__":
    main()

"""Check installed CLI contracts without sending model prompts.

Usage: python3 editor/runtime_probe.py [--opencode-server]
The optional HTTP check starts a private loopback server and reads its schema;
it creates no sessions and stops the server before returning.
"""
import argparse
import base64
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import tempfile
import time
import urllib.request
import uuid


def command(args):
    result = subprocess.run(args, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise RuntimeError("CLI command failed: " + " ".join(args[:3]))
    return result.stdout + result.stderr


def require(haystack, needles, label):
    missing = [key for key in needles if key not in haystack]
    if missing:
        raise RuntimeError(label + " missing: " + ", ".join(missing))


def codex_schema(binary):
    with tempfile.TemporaryDirectory(prefix="woven-protocol-") as folder:
        command([binary, "app-server", "generate-json-schema", "--out", folder])
        root = Path(folder)
        for filename, fields in {
            "ThreadStartParams": ["cwd", "model", "sandbox", "approvalPolicy"],
            "ThreadResumeParams": ["threadId", "model"],
            "TurnStartParams": ["threadId", "input", "model"],
            "TurnSteerParams": ["threadId", "input", "expectedTurnId"],
            "TurnInterruptParams": ["threadId", "turnId"],
            "ModelListParams": ["cursor", "limit"],
        }.items():
            path = root / "v2" / (filename + ".json")
            require(json.loads(path.read_text())["properties"], fields, filename)
        require((root / "ClientRequest.json").read_text(),
            ['"' + method + '"' for method in ("initialize", "thread/start", "thread/resume", "thread/read", "turn/start", "turn/steer", "turn/interrupt", "model/list")], "Codex methods")
        require((root / "ServerNotification.json").read_text(),
            ['"' + method + '"' for method in ("turn/started", "turn/completed", "item/started", "item/completed", "item/agentMessage/delta", "thread/tokenUsage/updated")], "Codex notifications")


def opencode_schema(binary):
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    password = uuid.uuid4().hex
    env = {**os.environ, "OPENCODE_SERVER_USERNAME": "woven-probe", "OPENCODE_SERVER_PASSWORD": password}
    auth = "Basic " + base64.b64encode(("woven-probe:" + password).encode()).decode()
    def get(path):
        req = urllib.request.Request("http://127.0.0.1:%d%s" % (port, path), headers={"Authorization": auth})
        with urllib.request.urlopen(req, timeout=2) as response:
            return json.load(response)
    with tempfile.TemporaryDirectory(prefix="woven-probe-") as folder:
        proc = subprocess.Popen([binary, "serve", "--hostname", "127.0.0.1", "--port", str(port)],
            cwd=folder, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, start_new_session=True)
        try:
            until = time.monotonic() + 15
            while True:
                try:
                    get("/global/health")
                    break
                except Exception:
                    if proc.poll() is not None or time.monotonic() > until:
                        raise RuntimeError("OpenCode health check failed")
                    time.sleep(.1)
            paths = get("/doc").get("paths", {})
            for path, method in {"/event": "get", "/session": "post",
                "/session/{sessionID}/prompt_async": "post", "/session/{sessionID}/abort": "post",
                "/permission/{requestID}/reply": "post"}.items():
                require(paths, [path], "OpenCode routes")
                require(paths[path], [method], path)
        finally:
            if proc.poll() is None:
                os.killpg(proc.pid, signal.SIGTERM)
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait(timeout=5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--opencode-server", action="store_true")
    args = parser.parse_args()
    results = []
    for runtime in ("claude", "codex", "opencode"):
        binary = os.environ.get(runtime.upper() + "_BIN") or shutil.which(runtime)
        row = {"runtime": runtime, "status": "not-installed"}
        if binary:
            try:
                row["version"] = command([binary, "--version"]).strip()
                if runtime == "codex":
                    codex_schema(binary)
                    row["checked"] = "app-server schema and CLI text-isolation flags"
                    require(command([binary, "exec", "--help"]), ["--ephemeral", "--ignore-user-config"], "Codex text isolation")
                elif runtime == "claude":
                    require(command([binary, "--help"]), ["--input-format", "--output-format", "--strict-mcp-config", "--setting-sources", "--system-prompt"], "Claude flags")
                    row["checked"] = "stream-json and text-isolation CLI flags"
                else:
                    require(command([binary, "run", "--help"]), ["--pure", "--format", "--agent", "--model"], "OpenCode flags")
                    if args.opencode_server:
                        opencode_schema(binary)
                    row["checked"] = "CLI flags" + (" and HTTP schema" if args.opencode_server else " (HTTP schema not requested)")
                row["status"] = "pass"
            except Exception as error:
                row.update(status="fail", error=str(error)[:400])
        results.append(row)
    print(json.dumps({"checks": results, "modelPromptsSent": 0}, indent=2))
    return 1 if any(row["status"] == "fail" for row in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())

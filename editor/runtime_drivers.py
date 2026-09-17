"""Persistent CLI transports. No model call is retried after an ambiguous send.

Each driver owns one process and exposes a byte stream of normalized events to
the existing run reader. Legacy exec/run paths remain selectable at spawn time.
"""
import base64
import io
import json
import os
import queue
import socket
import subprocess
import threading
import time
import urllib.parse
import urllib.request
import uuid


class EventStream:
    def __init__(self):
        self.queue = queue.Queue()
        self.closed = False

    def emit(self, event):
        if not self.closed:
            self.queue.put((json.dumps({"type": "woven_event", "event": event}) + "\n").encode())

    def close(self):
        self.closed = True
        self.queue.put(None)

    def __iter__(self):
        while True:
            value = self.queue.get()
            if value is None:
                return
            yield value


class InputStream:
    closed = False

    def __init__(self, driver):
        self.driver = driver

    def write(self, raw):
        frame = json.loads(raw)
        parts = (frame.get("message") or {}).get("content") or []
        if any(p.get("type") != "text" for p in parts):
            raise ValueError("use the runtime approval channel for tool responses")
        self.driver.send_user("\n".join(p.get("text", "") for p in parts))

    def flush(self):
        pass

    def close(self):
        self.closed = True


class ProcessDriver:
    """Process ownership is independent of whether a turn is accepting input."""
    mode = ""
    steerable = False

    def __init__(self):
        self.stdout = EventStream()
        self.stdin = InputStream(self)
        self.session_id = None
        self.turn_id = None
        self.children = {}
        self.send_lock = threading.Lock()

    @property
    def pid(self):
        return self.proc.pid

    @property
    def returncode(self):
        return self.proc.returncode

    def poll(self):
        return self.proc.poll()

    def wait(self, timeout=None):
        return self.proc.wait(timeout=timeout)

    def terminate(self):
        self.proc.terminate()

    def kill(self):
        self.proc.kill()

    def send_signal(self, sig):
        self.proc.send_signal(sig)

    def emit(self, event):
        self.stdout.emit(event)

    def start(self, text):
        def work():
            try:
                self.send_user(text)
            except Exception as error:
                self.emit({"type": "error", "message": "Runtime start failed: " + str(error)[:500]})
                self.terminate()
        threading.Thread(target=work, daemon=True).start()


class CodexDriver(ProcessDriver):
    mode = "app-server"
    steerable = True

    def __init__(self, binary, config_args, cwd, env, model=None, session_id=None, discovery=False):
        super().__init__()
        self.model, self.cwd = model, cwd
        self.responses, self.response_lock, self.write_lock = {}, threading.Lock(), threading.Lock()
        self.streamed = set()
        self.completed_turns = set()
        self.proc = subprocess.Popen([binary, "app-server", *config_args], cwd=cwd, env=env,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        self.stderr = self.proc.stderr
        threading.Thread(target=self._read, daemon=True).start()
        try:
            info = self.request("initialize", {"clientInfo": {"name": "woven", "version": "1.0"},
                "capabilities": {"experimentalApi": False}})
            self._write({"method": "initialized"})
            if discovery:
                return
            params = {"cwd": cwd, "sandbox": "danger-full-access", "approvalPolicy": "never"}
            if model:
                params["model"] = model
            if session_id:
                params["threadId"] = session_id
            result = self.request("thread/resume" if session_id else "thread/start", params)
            self.session_id = result["thread"]["id"]
            self.emit({"type": "status", "label": "starting", "sessionId": self.session_id,
                "model": result.get("model"), "runtimeMode": self.mode,
                "runtimeVersion": info.get("userAgent"), "capabilities": {"steerable": True, "resume": True}})
        except Exception:
            self.terminate()
            raise

    def _write(self, packet):
        with self.write_lock:
            self.proc.stdin.write((json.dumps(packet) + "\n").encode())
            self.proc.stdin.flush()

    def request(self, method, params, timeout=30):
        key, result = uuid.uuid4().hex, queue.Queue(maxsize=1)
        with self.response_lock:
            self.responses[key] = result
        try:
            self._write({"id": key, "method": method, "params": params})
            try:
                value = result.get(timeout=timeout)
            except queue.Empty:
                raise TimeoutError(method + " timed out; delivery is unknown, no retry was sent")
            if "error" in value:
                raise RuntimeError(str(value["error"])[:600])
            return value.get("result") or {}
        finally:
            with self.response_lock:
                self.responses.pop(key, None)

    def _read(self):
        try:
            for line in self.proc.stdout:
                frame = json.loads(line)
                if "id" in frame and "method" not in frame:
                    with self.response_lock:
                        waiter = self.responses.get(frame["id"])
                    if waiter:
                        waiter.put(frame)
                elif "id" in frame:
                    # This matches the existing unattended permission mode.
                    # Content elicitation is never auto-accepted.
                    method = frame.get("method", "")
                    if method in ("item/commandExecution/requestApproval", "item/fileChange/requestApproval"):
                        self._write({"id": frame["id"], "result": {"decision": "accept"}})
                    elif method == "item/permissions/requestApproval":
                        self._write({"id": frame["id"], "result": {"permissions": {}}})
                    elif method == "mcpServer/elicitation/request":
                        self._write({"id": frame["id"], "result": {"action": "decline"}})
                        self.emit({"type": "status", "label": "MCP input required", "detail": "The server requested interactive input; this unattended run did not approve it."})
                    else:
                        self._write({"id": frame["id"], "error": {"code": -32601, "message": "Unsupported client request"}})
                        self.emit({"type": "status", "label": "unsupported-runtime-request", "detail": method})
                else:
                    self.notification(frame.get("method"), frame.get("params") or {})
        except Exception as error:
            self.emit({"type": "error", "message": "Codex event stream failed: " + str(error)[:400]})
        finally:
            with self.response_lock:
                waiters = list(self.responses.values())
            for waiter in waiters:
                try:
                    waiter.put_nowait({"error": "Codex connection closed"})
                except queue.Full:
                    pass
            self.stdout.close()

    def notification(self, method, params):
        sid = params.get("threadId")
        child = sid and self.session_id and sid != self.session_id
        item = params.get("item") or {}
        kind, identity = item.get("type"), item.get("id")
        if method in ("item/started", "item/completed") and kind == "collabAgentToolCall":
            for receiver in item.get("receiverThreadIds", []):
                self.children.setdefault(receiver, identity)
            for receiver, state in item.get("agentsStates", {}).items():
                self.children.setdefault(receiver, identity)
                status = {"pendingInit": "pending", "errored": "failed", "interrupted": "stopped",
                    "shutdown": "stopped", "notFound": "unknown"}.get(state.get("status"), state.get("status", "unknown"))
                self.emit({"type": "job", "source": "native", "runtime": "codex", "jobId": receiver,
                    "toolUseId": self.children[receiver], "status": status, "description": state.get("message"),
                    "resourceClosed": state.get("status") == "shutdown",
                    "required": True, "background": True})
        if child:
            if sid not in self.children:
                return
            if method == "turn/started":
                self.emit({"type": "job", "source": "native", "runtime": "codex", "jobId": sid,
                    "toolUseId": self.children[sid], "status": "running", "restart": True,
                    "attemptId": (params.get("turn") or {}).get("id"), "required": True})
            elif method == "turn/completed":
                status = (params.get("turn") or {}).get("status")
                self.emit({"type": "job", "source": "native", "runtime": "codex", "jobId": sid,
                    "toolUseId": self.children[sid], "status": "completed" if status == "completed" else "failed",
                    "attemptId": (params.get("turn") or {}).get("id"),
                    "required": True})
            return
        if method == "turn/started":
            self.turn_id = params["turn"]["id"]
            self.emit({"type": "status", "label": "starting", "turnId": self.turn_id})
        elif method == "turn/completed":
            turn = params.get("turn") or {}
            self.completed_turns.add(turn.get("id"))
            self.turn_id = None
            self.emit({"type": "status", "label": "done" if turn.get("status") == "completed" else "error",
                "isError": turn.get("status") != "completed", "result": turn.get("error"), "turnId": turn.get("id")})
        elif method == "item/agentMessage/delta":
            self.streamed.add(params.get("itemId"))
            self.emit({"type": "text_delta", "delta": params.get("delta", "")})
        elif method in ("item/reasoning/summaryTextDelta", "item/reasoning/textDelta"):
            self.emit({"type": "thinking_delta", "delta": params.get("delta", "")})
        elif method == "thread/tokenUsage/updated":
            token = (params.get("tokenUsage") or {}).get("last") or {}
            self.emit({"type": "usage", "usage": {"input_tokens": token.get("inputTokens"),
                "output_tokens": token.get("outputTokens"), "cached_input_tokens": token.get("cachedInputTokens")}})
        elif method in ("item/started", "item/completed"):
            completed = method == "item/completed"
            if kind == "agentMessage":
                if completed and identity not in self.streamed:
                    self.emit({"type": "text_delta", "delta": item.get("text", "")})
                return
            if kind in ("userMessage", "reasoning"):
                return
            name = {"commandExecution": "Bash", "fileChange": "Edit", "collabAgentToolCall": "Agent"}.get(kind, kind)
            inp = {"command": item.get("command")} if kind == "commandExecution" else item
            if kind == "fileChange":
                inp = {"file_path": (item.get("changes") or [{}])[0].get("path"), "changes": item.get("changes")}
            if kind == "mcpToolCall":
                name, inp = "mcp__" + item["server"] + "__" + item["tool"], item.get("arguments")
            if kind == "collabAgentToolCall":
                name = "Agent" if item.get("tool") == "spawnAgent" else item.get("tool")
                inp = {"prompt": item.get("prompt"), "description": item.get("tool"), "run_in_background": True}
            if not completed:
                self.emit({"type": "tool_use", "id": identity, "name": name, "input": inp})
            else:
                self.emit({"type": "tool_result", "toolUseId": identity,
                    "content": json.dumps(item.get("result", item.get("aggregatedOutput", item))),
                    "isError": item.get("status") in ("failed", "declined")})
        elif method and method.startswith("mcpServer/"):
            self.emit({"type": "mcp_status", "method": method, "status": params})
        elif method == "error":
            self.emit({"type": "error", "message": str(params.get("error") or params)[:600]})

    def send_user(self, text):
        with self.send_lock:
            params = {"threadId": self.session_id, "input": [{"type": "text", "text": text}]}
            if self.turn_id:
                params["expectedTurnId"] = self.turn_id
                self.request("turn/steer", params)
            else:
                if self.model:
                    params["model"] = self.model
                result = self.request("turn/start", params)
                if result["turn"].get("status") == "inProgress" and result["turn"]["id"] not in self.completed_turns:
                    self.turn_id = result["turn"]["id"]

    def interrupt(self):
        if self.turn_id:
            self.request("turn/interrupt", {"threadId": self.session_id, "turnId": self.turn_id})
        for sid in self.children:
            # The parent interruption need not stop independent child turns.
            result = self.request("thread/read", {"threadId": sid, "includeTurns": True})
            for turn in result.get("thread", {}).get("turns", []):
                if turn.get("status") == "inProgress":
                    self.request("turn/interrupt", {"threadId": sid, "turnId": turn["id"]})


class OpenCodeDriver(ProcessDriver):
    mode = "http"

    def __init__(self, binary, cwd, env, model=None, session_id=None):
        super().__init__()
        self.cwd, self.model, self.agent = cwd, model, "build"
        self.part_text, self.tools_started, self.tools_done = {}, set(), set()
        self.message_roles = {}
        self.busy_sessions = set()
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        sock.close()
        password = uuid.uuid4().hex
        env = {**env, "OPENCODE_SERVER_PASSWORD": password, "OPENCODE_SERVER_USERNAME": "woven"}
        self.auth = "Basic " + base64.b64encode(("woven:" + password).encode()).decode()
        self.base = "http://127.0.0.1:" + str(port)
        self.proc = subprocess.Popen([binary, "serve", "--hostname", "127.0.0.1", "--port", str(port)],
            cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE, start_new_session=True)
        self.stderr = self.proc.stderr
        try:
            until = time.monotonic() + 15
            while True:
                try:
                    self.request("GET", "/global/health")
                    break
                except Exception:
                    if self.poll() is not None or time.monotonic() >= until:
                        raise RuntimeError("OpenCode server did not become healthy")
                    time.sleep(.1)
            if not model:
                config = self.request("GET", "/config")
                self.model = config.get("model")
            if not self.model or "/" not in self.model:
                raise ValueError("OpenCode HTTP requires an explicit provider/model ID or a configured default")
            self.session_id = session_id or self.request("POST", "/session", {})["id"]
            self.events_ready = threading.Event()
            threading.Thread(target=self._events, daemon=True).start()
            if not self.events_ready.wait(10):
                raise RuntimeError("OpenCode event subscription failed")
            self.emit({"type": "status", "label": "starting", "sessionId": self.session_id,
                "model": self.model, "runtimeMode": self.mode, "capabilities": {"steerable": False, "resume": True}})
        except Exception:
            self.terminate()
            raise

    def request(self, method, path, body=None, stream=False):
        url = self.base + path
        if not path.startswith("/global/") and path != "/doc":
            url += ("&" if "?" in path else "?") + urllib.parse.urlencode({"directory": self.cwd})
        request = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None,
            method=method, headers={"Authorization": self.auth, "Content-Type": "application/json"})
        response = urllib.request.urlopen(request, timeout=2 if path == "/global/health" else 30)
        if stream:
            return response
        with response:
            raw = response.read()
        return json.loads(raw) if raw else {}

    def _events(self):
        try:
            with self.request("GET", "/event", stream=True) as response:
                self.events_ready.set()
                for line in response:
                    if line.startswith(b"data:"):
                        self.notification(json.loads(line[5:]))
        except Exception as error:
            if self.poll() is None:
                self.emit({"type": "error", "message": "OpenCode event connection lost: " + str(error)[:400]})
                self.terminate()
        finally:
            self.stdout.close()

    def notification(self, frame):
        kind, data = frame.get("type"), frame.get("properties") or {}
        part, info = data.get("part") or {}, data.get("info") or {}
        sid = data.get("sessionID") or part.get("sessionID") or info.get("sessionID") or info.get("id")
        if kind == "session.created" and info.get("parentID") in {self.session_id, *self.children}:
            self.children[info["id"]] = info.get("parentID")
            self.emit({"type": "job", "source": "native", "runtime": "opencode", "jobId": info["id"],
                "status": "running", "description": info.get("title"), "required": True, "background": True})
        if sid != self.session_id and sid not in self.children:
            return
        if kind == "message.updated":
            self.message_roles[info.get("id")] = info.get("role")
        elif kind == "permission.asked":
            def answer():
                try:
                    self.request("POST", "/permission/" + data["id"] + "/reply", {"reply": "once"})
                except Exception as error:
                    self.emit({"type": "error", "message": "Permission reply failed: " + str(error)[:300]})
            threading.Thread(target=answer, daemon=True).start()
        elif kind == "session.status" and (data.get("status") or {}).get("type") == "busy":
            new_turn = sid not in self.busy_sessions
            self.busy_sessions.add(sid)
            if sid == self.session_id and self.turn_id is None:
                self.turn_id = "active"
                self.emit({"type": "status", "label": "starting"})
            elif sid != self.session_id and new_turn:
                self.emit({"type": "job", "source": "native", "runtime": "opencode", "jobId": sid,
                    "status": "running", "restart": True, "required": True})
        elif kind == "session.status" and (data.get("status") or {}).get("type") == "idle" and sid in self.busy_sessions:
            self.busy_sessions.discard(sid)
            if sid == self.session_id:
                self.turn_id = None
                self.emit({"type": "status", "label": "done"})
            else:
                self.emit({"type": "job", "source": "native", "runtime": "opencode", "jobId": sid,
                    "status": "completed", "required": True})
        elif kind == "session.error":
            self.emit({"type": "job", "source": "native", "jobId": sid, "status": "failed", "required": True}) if sid != self.session_id else self.emit({"type": "status", "label": "error", "isError": True, "result": data.get("error")})
        elif kind == "message.part.updated" and sid == self.session_id:
            if self.message_roles.get(part.get("messageID")) != "assistant":
                return
            pkind, key = part.get("type"), part.get("id")
            if pkind in ("text", "reasoning"):
                text, previous = part.get("text", ""), self.part_text.get(key, "")
                self.part_text[key] = text
                delta = text[len(previous):] if text.startswith(previous) else text
                if delta:
                    self.emit({"type": "text_delta" if pkind == "text" else "thinking_delta", "delta": delta})
            elif pkind == "tool":
                call, state = part.get("callID"), part.get("state") or {}
                if call not in self.tools_started:
                    self.tools_started.add(call)
                    self.emit({"type": "tool_use", "id": call, "name": part.get("tool"), "input": state.get("input") or {}})
                if call not in self.tools_done and state.get("status") in ("completed", "error"):
                    self.tools_done.add(call)
                    metadata = state.get("metadata") or {}
                    if part.get("tool") == "task" and metadata.get("sessionId"):
                        child = metadata["sessionId"]
                        self.children[child] = self.session_id
                        self.emit({"type": "job", "source": "native", "runtime": "opencode", "jobId": child,
                            "toolUseId": call, "status": "failed" if state.get("status") == "error" else "running" if metadata.get("background") else "completed",
                            "required": True, "background": bool(metadata.get("background"))})
                    self.emit({"type": "tool_result", "toolUseId": call, "content": state.get("output") or state.get("error") or "",
                        "isError": state.get("status") == "error"})
            elif pkind == "step-finish":
                self.emit({"type": "usage", "usage": {"tokens": part.get("tokens"), "cost": part.get("cost")}})

    def send_user(self, text):
        with self.send_lock:
            if self.turn_id:
                raise RuntimeError("OpenCode does not support steering; queue this message until the turn completes")
            provider, model = self.model.split("/", 1)
            self.turn_id = "pending"
            try:
                self.request("POST", "/session/" + self.session_id + "/prompt_async",
                    {"agent": self.agent, "model": {"providerID": provider, "modelID": model},
                     "parts": [{"type": "text", "text": text}]})
            except Exception:
                # Preserve pending on ambiguous delivery to prevent duplication.
                raise

    def interrupt(self):
        for sid in [self.session_id, *self.children]:
            self.request("POST", "/session/" + sid + "/abort", {})

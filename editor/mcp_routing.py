"""Translate shared MCP definitions without conflating transport or timeout units."""
import json
import re


def jsonc_loads(text):
    # Preserve quoted strings, including URLs and escaped quotes.
    pattern = r'"(?:\\.|[^"\\])*"|//[^\n]*|/\*[\s\S]*?\*/'
    text = re.sub(pattern, lambda m: m[0] if m[0].startswith('"') else ' ', text)
    text = re.sub(r'("(?:\\.|[^"\\])*")|,(\s*[}\]])', lambda m: m[1] or m[2], text)
    return json.loads(text)


def translate(spec, runtime, env=None):
    if not isinstance(spec, dict):
        raise ValueError("MCP server definition must be an object")
    command, url = spec.get("command"), spec.get("url")
    if bool(command) == bool(url):
        raise ValueError("MCP server needs exactly one command or URL")
    if url and (not isinstance(url, str) or not url.startswith(("https://", "http://"))):
        raise ValueError("MCP URL must use HTTP or HTTPS")
    if runtime == "codex":
        out = {"command": command, "args": spec.get("args", []), "env": env or {}} if command else {"url": url}
        if url and spec.get("type") == "sse":
            raise ValueError("Codex requires Streamable HTTP; legacy SSE needs an explicit transport bridge")
        for source, dest in (("headers", "http_headers"), ("envHeaders", "env_http_headers"),
                             ("bearerTokenEnvVar", "bearer_token_env_var"),
                             ("enabledTools", "enabled_tools"), ("disabledTools", "disabled_tools")):
            if source in spec:
                out[dest] = spec[source]
        for source, dest in (("startupTimeoutMs", "startup_timeout_sec"), ("toolTimeoutMs", "tool_timeout_sec")):
            if source in spec:
                out[dest] = spec[source] / 1000
        out["required"] = bool(spec.get("required", False))
        out["enabled"] = spec.get("enabled", True)
        return out
    if runtime == "opencode":
        out = {"type": "local", "command": [command] + spec.get("args", []), "environment": env or {}} if command else {"type": "remote", "url": url}
        out["enabled"] = spec.get("enabled", True)
        if url:
            for key in ("headers", "oauth"):
                if key in spec:
                    out[key] = spec[key]
            headers = dict(out.get("headers", {}))
            for header, name in spec.get("envHeaders", {}).items():
                if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
                    raise ValueError("MCP header environment reference must be a variable name")
                headers[header] = "{env:" + name + "}"
            token_env = spec.get("bearerTokenEnvVar")
            if token_env:
                if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", token_env):
                    raise ValueError("MCP bearer environment reference must be a variable name")
                headers["Authorization"] = "Bearer {env:" + token_env + "}"
                out.setdefault("oauth", False)
            if headers:
                out["headers"] = headers
        if "startupTimeoutMs" in spec:
            out["timeout"] = spec["startupTimeoutMs"]
        if "toolTimeoutMs" in spec:
            raise ValueError("OpenCode server definitions do not support per-server toolTimeoutMs")
        if spec.get("enabledTools") or spec.get("disabledTools"):
            raise ValueError("OpenCode tool filters belong in its permission configuration, not an MCP server definition")
        return out
    raise ValueError("unknown MCP target runtime")


def toml(value):
    if isinstance(value, dict):
        return "{" + ", ".join(json.dumps(k) + " = " + toml(v) for k, v in value.items()) + "}"
    if isinstance(value, list):
        return "[" + ", ".join(toml(v) for v in value) + "]"
    return json.dumps(value)

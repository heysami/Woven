"""Expose each Woven plugin agent once without changing its playbook or scope."""
import hashlib
import json
import os
from pathlib import Path
import re

FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---(?:\s|$)", re.S)
WOVEN_MODEL = re.compile(r"^woven-model:[ \t]*([^\r\n]*?)[ \t]*$", re.M)


def declared_model(text):
    """The model setting an agent file declares with `woven-model:`, or "".

    It takes the values of the model rows in Settings > Context and cost:
    `fast` (that runtime's economy preset), `inherit`, or an exact ID. Claude
    Code ignores the key; the daemon resolves it per spawn, so Settings stays
    the one place the model is chosen.
    """
    match = FRONTMATTER.match(text or "")
    value = WOVEN_MODEL.search(match.group(1)) if match else None
    return value.group(1).strip("\"'") if value else ""


def model_settings(plugin_dir):
    """{agent file path relative to agents/: declared setting} for the plugin."""
    root = Path(plugin_dir or "") / "agents"
    out = {}
    if not plugin_dir or not root.is_dir():
        return out
    for path in sorted(root.rglob("*.md")):
        try:
            with path.open() as handle:
                setting = declared_model(handle.read(65536))
        except (OSError, UnicodeError):
            continue
        if setting:
            out[path.relative_to(root).as_posix()] = setting
    return out


def _with_model(text, model):
    match = FRONTMATTER.match(text)
    fields = re.sub(r"^model:[^\r\n]*(\r?\n|\Z)", "", match.group(1), flags=re.M).rstrip("\n")
    return text[:match.start(1)] + fields + "\nmodel: " + model + text[match.end(1):]


def _place(dest, write):
    """Replace dest atomically, so a concurrent spawn never reads a gap."""
    temp = dest.with_name(".%s.%d.tmp" % (dest.name, os.getpid()))
    if temp.is_symlink() or temp.exists():
        temp.unlink()
    write(temp)
    os.replace(temp, dest)


def with_models(plugin_dir, models, cache_root):
    """The plugin as Claude should load it, with `model:` set on some agents.

    models maps an agent file (relative to agents/) to an exact model ID. Those
    agents become copies carrying that ID; every other file is a symlink to its
    source, so playbook edits still reach spawns unchanged. The copy lives under
    cache_root, keyed by the mapping, and is re-synced on every call. With no
    models, or on any filesystem error, the plugin is returned as it is and the
    agents run on the thread's model.
    """
    source = Path(plugin_dir or "")
    if not models or not plugin_dir or not (source / "agents").is_dir():
        return plugin_dir
    key = hashlib.sha1(json.dumps([str(source.resolve()), models], sort_keys=True).encode()).hexdigest()[:12]
    root = Path(cache_root) / key
    try:
        (root / "agents").mkdir(parents=True, exist_ok=True)
        manifest = root / ".claude-plugin"
        if not manifest.is_symlink():
            _place(manifest, lambda t: t.symlink_to((source / ".claude-plugin").resolve(), target_is_directory=True))
        agents = (source / "agents").resolve()
        wanted = set()
        for path in sorted(agents.rglob("*.md")):
            rel = path.relative_to(agents).as_posix()
            dest = root / "agents" / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            wanted.add(rel)
            if rel in models:
                text = path.read_text()
                if FRONTMATTER.match(text):
                    body = _with_model(text, models[rel])
                    if dest.is_symlink() or not dest.exists() or dest.read_text() != body:
                        _place(dest, lambda t, body=body: t.write_text(body))
                    continue
            if not (dest.is_symlink() and os.readlink(dest) == str(path)):
                _place(dest, lambda t, path=path: t.symlink_to(path))
        for path in sorted((root / "agents").rglob("*.md"), reverse=True):
            if path.relative_to(root / "agents").as_posix() not in wanted:
                path.unlink()
    except (OSError, UnicodeError, ValueError):
        return plugin_dir
    return str(root)


def plugin_spawn_args(plugin_dir):
    """Keep plugin names callable and hide their bare aliases from the prompt.

    Claude discovers .claude/agents both from the project ancestry and from
    our plugin symlink. Agent(name) deny rules filter the duplicate bare names
    out of the model-visible catalog, including nested agents. Using these
    rules preserves project settings, hooks, auth, and unrelated custom agents.
    Only names from valid definitions in this plugin are filtered.
    """
    if not plugin_dir or not Path(plugin_dir).is_dir():
        return []
    root = Path(plugin_dir)
    args = ["--plugin-dir", str(root)]
    try:
        manifest = json.loads((root / ".claude-plugin/plugin.json").read_text())
        if not isinstance(manifest, dict) or not manifest.get("name"):
            return args
    except (OSError, ValueError):
        return args

    names = set()
    for path in sorted((root / "agents").rglob("*.md")):
        try:
            with path.open() as handle:
                # Descriptions can exceed 2 KB; inspect the whole frontmatter.
                text = handle.read(65536)
        except (OSError, UnicodeError):
            continue
        frontmatter = FRONTMATTER.match(text)
        if not frontmatter:
            continue
        fields = frontmatter.group(1)
        name = re.search(r"^name:[ \t]*([^\r\n]+)$", fields, re.M)
        description = re.search(r"^description:[ \t]*\S", fields, re.M)
        if not name or not description:
            continue
        value = name.group(1).strip()
        if len(value) > 1 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        # Reject rule syntax and namespaced names, which could deny the plugin
        # itself. The shipped agents all use these simple identifiers.
        if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", value):
            names.add(value)
    if names:
        # '=' keeps the variadic flag from swallowing a trailing CLI prompt.
        args.append("--disallowedTools=" + ",".join(f"Agent({name})" for name in sorted(names)))
    return args

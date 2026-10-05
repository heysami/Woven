"""Expose each Woven plugin agent once without changing its playbook or scope."""
import json
from pathlib import Path
import re


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
        frontmatter = re.match(r"\A---\s*\n(.*?)\n---(?:\s|$)", text, re.S)
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

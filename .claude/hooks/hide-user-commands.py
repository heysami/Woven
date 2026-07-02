#!/usr/bin/env python3
"""SessionStart hook: hide ALL personal ~/.claude/commands skills from THIS project only.

Claude Code has no "hide user-commands folder" setting, only hide-by-name
(skillOverrides). So we scan the folder live every session and regenerate the
off-list into .claude/settings.local.json. This adapts to whatever commands
exist on the current machine - no hardcoded names, nothing to resync by hand.
The user's global commands stay fully available in every OTHER project.
"""
import json
import os
import glob

cmd_root = os.path.expanduser("~/.claude/commands")

names = []
if os.path.isdir(cmd_root):
    # top-level single-file commands  ->  <stem>
    for f in glob.glob(os.path.join(cmd_root, "*.md")):
        names.append(os.path.splitext(os.path.basename(f))[0])
    # namespaced commands under subdirs  ->  <ns>:<stem>
    for d in [p for p in glob.glob(os.path.join(cmd_root, "*")) if os.path.isdir(p)]:
        ns = os.path.basename(d)
        for f in glob.glob(os.path.join(d, "**", "*.md"), recursive=True):
            rel = os.path.relpath(f, d)
            stem = os.path.splitext(rel)[0].replace(os.sep, ":")
            names.append(f"{ns}:{stem}")

names = sorted(set(names))

project_dir = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
settings_path = os.path.join(project_dir, ".claude", "settings.local.json")

data = {}
if os.path.exists(settings_path):
    try:
        with open(settings_path) as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, OSError):
        data = {}

# Replace wholesale so removed commands also drop off the list.
data["skillOverrides"] = {n: "off" for n in names}

os.makedirs(os.path.dirname(settings_path), exist_ok=True)
with open(settings_path, "w") as fh:
    json.dump(data, fh, indent=2)
    fh.write("\n")

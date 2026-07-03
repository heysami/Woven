#!/usr/bin/env python3
"""Regenerate .codex/agents/*.toml from the canonical .claude/agents/*.md set.

The .claude markdown files are the single source of truth for agent
contracts. The codex CLI runtime reads the same agents as TOML from
.codex/agents/, so any md edit must be mirrored or codex spawns run a
stale contract. This script makes that mirror mechanical:

    python3 scripts/sync-codex-agents.py          # regenerate all
    python3 scripts/sync-codex-agents.py --check  # exit 1 if out of sync

Mapping per agent:
    frontmatter name        -> name = "..."
    frontmatter description -> description = "..."
    md body (after ---)     -> developer_instructions (triple-quoted)
The frontmatter `tools:` line is dropped (codex manages tool access
itself). Files without a `name:` frontmatter key (e.g. ORCHESTRATORS.md)
are skipped. Orphan tomls whose md was deleted are removed.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD_DIR = os.path.join(ROOT, ".claude", "agents")
TOML_DIR = os.path.join(ROOT, ".codex", "agents")


def parse_md(path):
    """Return (name, description, body) or None when not an agent file."""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end < 0:
        return None
    front = text[4:end]
    body = text[end + len("\n---\n"):].strip("\n")
    meta = {}
    key = None
    for line in front.splitlines():
        if line[:1] in (" ", "\t") and key:
            meta[key] += " " + line.strip()
            continue
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        meta[key] = val.strip()
    name = meta.get("name")
    if not name:
        return None
    return name, meta.get("description", ""), body


def toml_escape_single(s):
    """Escape for a single-line basic string."""
    out = s.replace("\\", "\\\\").replace('"', '\\"')
    out = out.replace("\t", "\\t")
    return out


def toml_escape_multi(s):
    """Escape for a multi-line basic string (newlines stay literal)."""
    out = s.replace("\\", "\\\\")
    # Three or more consecutive quotes would close the string; escape the
    # third quote of every run. Doing it twice catches runs of 4-5.
    for _ in range(2):
        out = out.replace('"""', '""\\"')
    return out


def render_toml(name, description, body):
    return (
        'name = "%s"\n' % toml_escape_single(name)
        + 'description = "%s"\n' % toml_escape_single(description)
        + 'developer_instructions = """\n%s\n"""\n' % toml_escape_multi(body)
    )


def main():
    check_only = "--check" in sys.argv
    agents = {}
    for fname in sorted(os.listdir(MD_DIR)):
        if not fname.endswith(".md"):
            continue
        parsed = parse_md(os.path.join(MD_DIR, fname))
        if parsed is None:
            continue
        name, description, body = parsed
        agents[name] = render_toml(name, description, body)

    os.makedirs(TOML_DIR, exist_ok=True)
    stale, wrote, removed = [], [], []
    for name, content in agents.items():
        path = os.path.join(TOML_DIR, name + ".toml")
        current = None
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                current = f.read()
        if current == content:
            continue
        stale.append(name)
        if not check_only:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            wrote.append(name)
    for fname in sorted(os.listdir(TOML_DIR)):
        if not fname.endswith(".toml"):
            continue
        if fname[:-len(".toml")] not in agents:
            stale.append(fname + " (orphan)")
            if not check_only:
                os.remove(os.path.join(TOML_DIR, fname))
                removed.append(fname)

    # Round-trip verification when a strict TOML parser is available.
    try:
        import tomllib
    except ImportError:
        tomllib = None
    if tomllib and not check_only:
        for name in agents:
            with open(os.path.join(TOML_DIR, name + ".toml"), "rb") as f:
                tomllib.load(f)

    if check_only:
        if stale:
            print("OUT OF SYNC (%d): %s" % (len(stale), ", ".join(stale)))
            sys.exit(1)
        print("in sync: %d agents" % len(agents))
        return
    print("synced %d agents (%d rewritten, %d orphans removed)"
          % (len(agents), len(wrote), len(removed)))


if __name__ == "__main__":
    main()

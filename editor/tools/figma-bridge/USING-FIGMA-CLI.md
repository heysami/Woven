# Woven -> Figma via figma-cli (the agentic path)

> **End users do NOT use a terminal.** In the editor, open a prototype and click
> **Send to Figma** - the daemon runs figma-cli for you (`/__figma_cli_run`) and
> shows progress in the modal. The only manual step is having **Figma Desktop
> open** so figma-cli can connect to it (restart Figma once on the very first
> run if it can't connect). Everything below is **maintainer/agent reference**
> for how the install + integration work - not steps to hand to a user.

This is the way to get a Woven prototype into Figma as a clean, auto-layout,
component-using design. It uses [figma-cli](https://github.com/silships/figma-cli)
(MIT) - an agent-driven CLI that looks at your design, builds it with `render`,
and verifies itself by re-screenshotting (`--verify`). It is a separate tool with
its **own** Figma plugin (not the Woven Bridge plugin in this folder).

Why this and not the Woven Bridge plugin: a mechanical DOM->Figma walk can't make
the semantic decisions ("this is a Button, instance it; this is an auto-layout
column") that make a Figma file clean. figma-cli's agent makes them and verifies
the result. Woven's only job is to serve the prototype at a URL figma-cli can read.

---

## 1. Install the CLI (already done on this machine)

figma-cli is vendored at `editor/tools/figma-cli/` (gitignored - it's an external
tool) and exposed as the `figma-cli` command via `~/.local/bin/figma-cli`.

To reproduce on a fresh machine:

```bash
cd editor/tools
git clone --depth 1 https://github.com/silships/figma-cli.git figma-cli
rm -rf figma-cli/.git
cd figma-cli
npm install --no-audit --no-fund
npm rebuild sharp esbuild --foreground-scripts    # native deps recreate-url needs

# put `figma-cli` on PATH (npm link needs sudo on this box, so use a wrapper):
mkdir -p "$HOME/.local/bin"
printf '#!/bin/sh\nexec node "%s/src/index.js" "$@"\n' "$PWD" > "$HOME/.local/bin/figma-cli"
chmod +x "$HOME/.local/bin/figma-cli"

figma-cli --version    # -> 2.1.0
```

> If `recreate-url` later errors on image handling, the `sharp`/`esbuild` build
> scripts didn't run: `cd editor/tools/figma-cli && npm rebuild sharp esbuild --foreground-scripts`.

---

## 2. Connect it to Figma (one-time per session)

figma-cli drives **Figma Desktop** locally (no API key). Two modes:

### Safe Mode (recommended - no app patching)

1. In **Figma Desktop**: `Menu -> Plugins -> Development -> Import plugin from
   manifest...` and pick:
   `editor/tools/figma-cli/plugin/manifest.json`
   (this is **figma-cli's** plugin, not Woven Bridge).
2. Run it: `Menu -> Plugins -> Development -> figma-cli` (keep the window open).
3. In a terminal: `figma-cli connect --safe`
4. Check: `figma-cli daemon status` -> should show connected.

### Yolo Mode (faster, patches Figma Desktop once)

```bash
figma-cli connect          # patches Figma Desktop to expose a debug port; no plugin to keep open
```
Reversible via figma-cli; use Safe Mode if you'd rather not patch the app.

---

## 3. Rebuild a Woven prototype in Figma

Your prototype is already served by the Woven daemon, so figma-cli can recreate it
straight from the URL. Example (this project, screen `main2`, daemon on :5747):

```bash
figma-cli recreate-url "http://localhost:5747/source/main2/index.html?project=demo-inhouse" \
  --name "main2" --verify
```

- `recreate-url` is the agentic loop: it reads the live page, builds it with
  auto-layout, and `--verify` screenshots the result so it can self-correct.
- For a phone frame: add `-w 375 -h 812`.

**Finding the URL for any screen:** it's `http://<daemon-host:port>/source/<branch>/<entry>?project=<projectId>`
(+ the screen's `#hash` if it has one). The host/port/project are in your editor's
address bar; `<branch>`/`<entry>` are the prototype's folder + html file under
`projects/<projectId>/source/`. The simplest way: open the prototype on the canvas
and copy its iframe address.

### Optional: bind colors to Figma variables first

```bash
figma-cli import "/Users/sami/Documents/Woven/projects/demo-inhouse/source/main2/styles.css"
```
(`recreate-url` already reads the page's computed styles, so this is polish - it
turns the CSS custom properties into real Figma variables.)

### Driving it conversationally

figma-cli is built to be driven by Claude Code in natural language (its `CLAUDE.md`
is a "user says -> command" table). With it connected, you can just tell Claude
Code: *"use figma-cli to recreate http://localhost:5747/source/main2/index.html?project=demo-inhouse
in Figma, then tidy the auto-layout and instance any repeated components."* The
agent will run `recreate-url`, `--verify`, `instantiate`, `set autolayout`, etc.

---

## 4. Iterate / fix

```bash
figma-cli daemon status        # connection + token info
figma-cli daemon reconnect     # if Figma was restarted
figma-cli undo                 # remove what the last render/recreate created
figma-cli a11y audit           # contrast / touch targets / text size
```
Full command list: `editor/tools/figma-cli/REFERENCE.md` and `CLAUDE.md`.

---

## Relationship to the Woven Bridge plugin (this folder)

The Woven Bridge plugin + the editor's "Send to Figma" / "Tidy with agent" were an
earlier, mechanical attempt (DOM capture -> nodes). figma-cli supersedes them for
producing **clean** output. Woven Bridge still works as a raw transport if you want
it, but for real design-system-quality Figma, use figma-cli per this guide.

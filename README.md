<div align="center">
  <img src="docs/woven-social-preview.jpg?v=1" alt="Woven — built-in design orchestration and canvas" width="720" />
  <hr width="720" />
  <p>
    <img alt="required: macOS" src="https://img.shields.io/badge/required-macOS-000000?logo=apple&logoColor=white" />
    <img alt="required: Python 3.9+" src="https://img.shields.io/badge/required-Python%203.9%2B-3776AB?logo=python&logoColor=white" />
    <img alt="required: Node.js 18+" src="https://img.shields.io/badge/required-Node.js%2018%2B-339933?logo=nodedotjs&logoColor=white" />
    <img alt="required: Homebrew" src="https://img.shields.io/badge/required-Homebrew-FBB040?logo=homebrew&logoColor=white" />
    <img alt="supported: Claude · Codex · opencode" src="https://img.shields.io/badge/supported-Claude%20%C2%B7%20Codex%20%C2%B7%20opencode-8A63D2" />
  </p>
</div>

# Woven

Toss Woven an idea. Get a whole app back, drawn live on the canvas. Every illustration, every screen, every shader lands as its own node, so you can noodle on one, riff on another, branch off a weird take, or just trash the lot and try again. Freeform generation, freeform editing, pure chaos.

Each kind of visual has its own pipeline. Raster portraits get generated and cut out. Shaders stay GLSL. Vectors stay paths. Particles, Lottie, and 3D each have their own subagent. The result reads as drawn.

The output is real. Plain HTML, CSS, and JS in `source/`. Opens by double-clicking. Emails to a designer who's never heard of Woven.

You bring the agent (Claude Code, Codex, opencode, or an API key). Woven is the canvas around it.

This README walks through your first run end-to-end, from install to the Ghibli-themed Totoro feeder app at the bottom, generated from one prompt.

---

## Table of contents

1. [What you need before starting](#1-what-you-need-before-starting)
2. [Install](#2-install)
3. [Start the editor](#3-start-the-editor)
4. [Connect a model](#4-connect-a-model)
5. [Add asset-provider keys (image · video · SVG)](#5-add-asset-provider-keys-image--video--svg)
6. [Review orchestrators](#6-review-orchestrators)
7. [Local services](#7-local-services)
8. [Finish onboarding](#8-finish-onboarding)
9. [Create your first project](#9-create-your-first-project)
10. [Open the workflow and send your first prompt](#10-open-the-workflow-and-send-your-first-prompt)
11. [The final prototype](#11-the-final-prototype)

---

## 1. What you need before starting

Here's what you need before launching the editor. On first run the wizard also installs a few local tools for you automatically (see [Local services](#7-local-services)), so there's nothing to install by hand there.

| Requirement      | Minimum                                              | Why                                                                          | How to check                          |
| ---------------- | --------------------------------------------------- | ---------------------------------------------------------------------------- | ------------------------------------- |
| **macOS**        | a recent version                                     | Woven is macOS-only. The daemon, launch scripts, and setup tooling assume a Mac. | `sw_vers`                             |
| **Python**       | **3.9 or newer**                                    | The editor daemon (`serve.py` + sibling modules) is pure Python, stdlib only. 3.9 is the floor (it matches the system `python3` on a clean macOS); 3.11+ is fine and what most dev machines already have. | `python3 --version`                   |
| **A model connection** | **one of:** Claude Code CLI · Codex CLI · opencode CLI · an Anthropic / OpenAI API key | At least one way to reach a text model so the agent can run workflows. **A CLI is the required path for agentic workflows** (a pasted API key only powers single-shot "simple prompt" nodes). You'll wire this up when you [connect a model](#4-connect-a-model). | `claude --version` / `codex --version` / `opencode --version` |
| **Homebrew**     | any recent ([brew.sh](https://brew.sh))             | Package manager used to install a model CLI and other tools.                 | `brew --version`                      |
| **Node.js**      | **18 or newer** ([nodejs.org](https://nodejs.org)) | Runs the headless shader render-check the daemon installs on first launch (Playwright needs Node 18+; npm ships with Node). | `node --version`                      |

The **editor itself** has no build step; it ships as static HTML + pure-Python files (stdlib only). [Homebrew](https://brew.sh) and [Node.js](https://nodejs.org) are used by tools the daemon installs for you on first launch (background removal and a headless shader render-check), so have both ready for a complete setup.

---

## 2. Install

**[Download the latest release](https://github.com/heysami/Woven/releases/latest)** and unpack it wherever you like.

---

## 3. Start the editor

Navigate into the folder you unzipped, then:

```bash
# macOS: double-click in Finder
open editor/serve.command

# or from a terminal
python3 editor/serve.py
```

The daemon prints the URL it's listening on (default **http://localhost:5731/editor/**) and a Finder window / browser tab opens automatically.

To run with a separate workspace folder (multi-project mode), set `TH_WORKSPACE_DIR`:

```bash
TH_WORKSPACE_DIR="$HOME/my-prototypes" python3 editor/serve.py
```

---

## 4. Connect a model

On first launch the **Projects** page shows a setup card that walks you through connecting a model, adding asset keys, and reviewing orchestrators. Until a model is connected the top-right pill reads **No model configured** and the **+ New project** button stays disabled. It opens on connecting a model:

![Onboarding · connect a model](docs/screenshots/01-onboarding-step1.png)

This wires up the model the agent runs on. There are two paths, and they are **not** equivalent:

### 4a · Install a CLI (required for agents)

A **Claude Code, Codex, or opencode CLI on your `PATH` is the required backend.** The agent loop, file tools, and context compaction all live in the CLI harness, so node runs, chat, and orchestrators only work once a CLI is connected. Pick **ONE**:

```bash
# Claude Code - native installer, no npm required (recommended):
curl -fsSL https://claude.ai/install.sh | bash
claude login

# or Codex - standalone installer, no npm required:
curl -fsSL https://chatgpt.com/codex/install.sh | sh
codex login

# or opencode (multi-provider):
curl -fsSL https://opencode.ai/install | bash      # or: npm i -g opencode-ai
opencode auth login                                # then `opencode models` to pick a default
```

opencode is a multi-provider harness: it manages its own auth and default model, so after `opencode auth login` you connect any provider it supports (Anthropic, OpenAI, etc.) and Woven shells out to it for text-output runs.

In the app you can click **Install a CLI** to open the **Install a model CLI** popup (it lists the same commands); once you've run them, click **I've installed it · refresh** (or **I've already set one up · refresh**) and the status dot flips to green.

![Onboarding · install-a-CLI popup](docs/screenshots/02-onboarding-cli-picker.png)

### 4b · Paste an API key (simple prompts only)

Click **Paste an API key** to drop in an Anthropic or OpenAI key via Settings. The key is stored locally at `~/.test-harness/media-config.json` (file mode `0600`, never sent anywhere except the provider's own API).

A key on its own runs **single-shot "simple prompt" nodes** only - it does **not** enable agentic workflows. If you finish onboarding on a key alone, the top-right pill turns amber and reads **Agents disabled - no CLI** as a standing nudge to install one.

---

## 5. Add asset-provider keys (image · video · SVG)

Connecting a model only covers the **agent's text model**. To unlock image generation, video, vector SVG, audio, etc., add the relevant provider keys here:

![Onboarding · asset providers](docs/screenshots/03-onboarding-asset-providers.png)

Each row shows what the provider covers and lets you paste a key inline, no need to leave the page:

| Provider      | Covers                                                              | Where to get a key                                       |
| ------------- | ------------------------------------------------------------------- | -------------------------------------------------------- |
| **fal.ai**    | image · video · 3D · background removal · upscale (one key, many skills) | https://fal.ai/dashboard/keys                       |
| **Quiver AI** | vector SVG generation                                              | https://docs.quiver.ai/getting-started/quickstart        |
| **OpenAI**    | raster image (`gpt-image-2`) · text models                          | https://platform.openai.com/api-keys                     |
| **Anthropic** | Claude text models · vision-based describe                          | https://console.anthropic.com/settings/keys              |
| **ElevenLabs**| audio - voiceover · sound effects · music (one key, all three)      | https://elevenlabs.io/app/settings/api-keys              |
| **Meshy**     | 3D - text/image to textured `.glb`                                  | https://docs.meshy.ai/                                   |
| **Exa**       | web search for the Research assistant                               | https://dashboard.exa.ai/api-keys                        |

These are **optional**. Projects can still be created without them; you just won't be able to run the matching skill nodes (image-generate, video-gen, svg-gen, audio-gen, 3D, web-search, etc.) until the key is in place. You can always come back later via the **gear icon** in the top-right. A handful of additional providers (xAI, BFL, Recraft, Leonardo, Higgsfield, and more) are available from that same Settings panel.

---

## 6. Review orchestrators

This is an optional review step. Orchestrators dispatch whole families of subagents for richer artefacts. The editor ships **17** of them, auto-discovered from their manifests, so the list stays current as new ones land:

- **Art direction & assets** - Art Director, Visual, Photography, Illustration, Illustrative shaders, Creative visual, Material
- **Immersive & interactive** - Simulation, Narrative experience, Game experience, Interactive media, Motion Studio, Scrapbook experience
- **3D** - Scene 3D, Hero 3D
- **Polish & ship** - Interactive polish, Publish

Each row has a toggle, so you can turn off any family you don't want auto-dispatched - you can still invoke them by name later.

![Onboarding · orchestrators](docs/screenshots/03c-onboarding-orchestrators.png)

Rows whose pipeline depends on a key you haven't added under asset keys (photography and illustration need an image model; audio-bearing families need an audio key) are shown as **limited** with a short note about what's missing. Nothing here blocks project creation; if in doubt, leave the defaults and click **Next →**.

---

## 7. Local services

The **Local services** step installs a handful of on-demand tools the asset / sharing / shader pipelines depend on - background removal (rembg), share tunnels (cloudflared), and the shader lint + headless render-check (glslang + shader-verify). They install **automatically** when the step opens: each row shows live progress and flips green as it lands (the render-check pulls a Chromium, so it's the slowest - give it a minute or three).

You don't have to run anything by hand, but do glance over this step before moving on: if a row stalls or shows an error (for example shader-verify when Node.js is missing), it surfaces a hint and a manual **Install** button - fix the prerequisite, hit **Re-check**, and wait for green.

![Onboarding · local services](docs/screenshots/03b-onboarding-local-skills.png)

---

## 8. Finish onboarding

Once the required steps are satisfied, the **Done** step confirms you're set (**"All set!"** when a CLI is connected, or **"Continue without agents"** if you finished on a key alone). It also carries the optional **User testing mode** toggle. Click **Got it** to dismiss the card, and the **+ New project** button lights up.

![Onboarding · done](docs/screenshots/03d-onboarding-done.png)

---

## 9. Create your first project

Once a model is configured, the top-right warning pill disappears, the daemon + CLI chips both go green, and the **+ New project** button lights up. The header carries tabs for **Projects** (your gallery), **Shares**, and **Capabilities** (a bundled reference for the orchestrators, skills, subagents, and node kinds the editor ships with), reachable from anywhere on the landing.

![Projects landing · model configured, + New project enabled](docs/screenshots/04-projects-landing.png)

Click **+ New project** (or **+ Create your first project** in the empty state - the caret next to it also offers **From GitHub…** to clone an existing repo). The new-project modal opens:

![New project modal](docs/screenshots/05-new-project-wizard.png)

It has three things on it:

- **Project name** - type a folder-safe id (alphanumeric + `.` `_` `-`); the modal echoes the slug it will use.
- **Export folder** (optional) - where per-asset Export (the ⤓ on a selected node) drops bundles. On macOS a **Pick…** button opens Finder; you can also change this later from the **Exports** button in the workflow toolbar.
- **Start from the template design system** (toggle, off by default) - seed a tokenized component library you can recolour, round, and retype.

With the toggle **off**, click **+ Create** and you land straight on a clean workflow canvas - no scope picker, no multi-step wizard. The earlier "Blank / Quick designs / Design system / PRD only / Full guided / Custom" branching was removed; every fresh project starts blank and you tell the agent what you want from chat. Need one of the old guided runs? Just ask the agent in plain English on the next screen ("brainstorm three design directions", "write a PRD first", "do the full guided flow", …) and the orchestrator skill picks the right stages.

With the toggle **on**, the button reads **Customize →** and advances to a wider **design-system customizer** step - a live preview where you tune colour, roundness, type, and spacing before the project is created with that tokenized DS baked in.

---

## 10. Open the workflow and send your first prompt

The editor drops you into **workflow mode**. The left sidebar is the **Library** of node types (basic tools, asset generators, iterators, and more…). In the middle of the empty canvas, the editor shows a **"Your workflow is empty"** card with a composer right where you need it. No menus to open, no drawers to expand.

![Empty workflow · canvas-centered composer](docs/screenshots/07-empty-workflow.png)

Type your prompt into the composer. The agent has read/edit/bash access to your project root and will scaffold the prototype from scratch. For this walkthrough we'll use:

> `create a ghibli themed mobile app to feed totoro`

![Prompt typed in the empty-workflow composer](docs/screenshots/08-prompt-entered.png)

Press **⌘/Ctrl + Enter** (or click **Send**) and the agent gets to work, generating the design system, scaffolding pages, dispatching asset jobs, and wiring everything together as nodes on the canvas in real time.

---

## 11. The final prototype

After the run finishes (marked **Done** at 28 turns), the workflow canvas holds every step that produced the app: a column of **Generate image** nodes (one per painted asset: Totoro under the camphor tree, the pantry shelf, the ambient leaf borders, each food cutout…), with **Remove background** nodes cleaning the food sprites into transparent PNGs, all feeding the live phone-mockup of **Totoro's Wood** on the right. The chat drawer records how it was built and can be reopened to continue the same session.

![Final prototype · Totoro's Wood on the workflow canvas](docs/screenshots/09-final-prototype.png)

The chat summary shows the discipline the build followed. The palette (`#f4ece0 / #fbf6ec / #3a3128 / #8a7d6b / #e3d6c2 / #5b8c6e`), Fraunces display + Inter body, and a cream-humanist × cottagecore register were **locked from the approved art-direction plate** and held immutable through the build. The orchestrators ran in order: **art-director** (north-star plate + contract) → **illustration** (committed the Ghibli watercolor register, rejecting the 3D-mascot default) → **visual** (12 painted assets + the ambient-leaves loop) → **game-experience** (the playable feed loop) → **interactive-polish** (staggered chrome settle, watery meter rise, journal reveal). Click **▶ Run** on any node to regenerate a single asset without redoing the flow.

### What the agent generated from a single prompt

The one-line prompt, *"build a ghibli themed mobile app to feed totoro"*, produced a four-tab app — **Wood · Feed · Pantry · Journal** — with a hand-painted watercolor palette carried across every screen:

| Wood · visit Totoro | Pantry · what you've gathered | Journal · your days together |
| :---: | :---: | :---: |
| ![Wood tab](docs/screenshots/10-app-wood.png) | ![Pantry tab](docs/screenshots/11-app-pantry.png) | ![Journal tab](docs/screenshots/12-app-journal.png) |
| Totoro dozes under the great camphor tree; two meters (a **heart** at 72, an **acorn** at 48) sit above a **Feed Totoro** button, with the line "He stirs when you visit. Bring him something from the pantry." | **The Pantry** — *six days of small kindnesses.* A grid of gathered foods (**Acorns · Forest berries · Oak leaves · Brown mushroom · Dango**) with live counts and a *favorite* tag on the ones Totoro loves most. | **Journal** — a settling-in timeline that writes itself as you play: *A sprout woke up · The first acorn · A small friend came by · We waited out the rain*, each with a soft-grey soot-sprite or acorn glyph. |

The fourth tab, **Feed**, is the playable loop: drag a food from your pantry onto Totoro and his meters respond. Bottom-tab navigation, the warm-paper background, sage-green accent, and watercolor illustration style carry across every screen, all inferred from the single prompt.

---

## Troubleshooting

| Symptom                                              | Fix                                                                                                    |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| Trouble installing (a tool missing or out of date)   | Check the versions first: `python3 --version` · `node --version` · `brew --version`. Update all of them with `brew update && brew upgrade python node` (refreshes Homebrew, then Python + Node). If one is missing entirely, install it with `brew install python node`. |
| Top-right pill stays red after pasting a key         | Click the **gear icon → Test** on that provider row in Settings to verify the key.                     |
| **Claude CLI missing** chip is amber                 | `which claude`. If empty, run `curl -fsSL https://claude.ai/install.sh \| bash` then `claude login`. (Shows **Codex CLI missing** or **opencode CLI missing** if that's your preferred CLI, install via `curl -fsSL https://chatgpt.com/codex/install.sh \| sh` / `curl -fsSL https://opencode.ai/install \| bash` then its login command.) |
| **Daemon down** chip is red                          | The Python server crashed or was stopped. Re-run `python3 editor/serve.py` from the unpacked folder.   |
| Port 5731 already in use                             | Set a different port: `EDITOR_PORT=5740 python3 editor/serve.py`.                                      |
| Image / video / SVG nodes fail with "no API key"     | Open **Settings (gear)** and add the relevant provider key (see [Add asset-provider keys](#5-add-asset-provider-keys-image--video--svg)). |

---

## Where things live on disk

In multi-project mode the workspace dir (`TH_WORKSPACE_DIR`) is **separate from the editor folder** and holds only the daemon-managed data below. (If you run from the unpacked folder with no workspace dir, this same `projects/` tree lives alongside the editor's own `editor/`, `PROTOTYPE.md`, `design-library/`, etc.)

```
<workspace-dir>/
├── workspace.json                          # project registry (auto-managed)
├── shares.json                             # live-share registry (auto-managed)
├── .trash/                                 # recoverable deleted projects (Housekeeping → empty)
└── projects/
    └── <project-id>/
        ├── source/main/                    # the generated prototype HTML/CSS/JS (per branch; default "main")
        ├── editor/data.js                  # canvas state (frames, nodes, arrows)  ·  + chat.jsonl
        ├── workflow/workflow.json          # workflow graph  ·  + runs/ + views/ snapshots
        ├── design-systems/<ds-id>/         # design systems you build for this project (empty until then)
        └── .history/, .thumbnail*, …       # edit history + gallery metadata (auto-managed)

~/.test-harness/media-config.json           # your provider API keys (mode 0600, per-user)
```

(`fonts/` and `.system-chats/` also appear at the workspace root once you upload a font or use the Capabilities agent.)

That's it. You're set up.

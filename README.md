<div align="center">
  <img src="docs/woven-mark.svg" alt="Woven" width="280" />
</div>

# Woven

Toss Woven an idea. Get a whole app back, drawn live on the canvas. Every illustration, every screen, every shader lands as its own node, so you can noodle on one, riff on another, branch off a weird take, or just trash the lot and try again. Freeform generation, freeform editing, pure chaos.

Each kind of visual has its own pipeline. Raster portraits get generated and cut out. Shaders stay GLSL. Vectors stay paths. Particles, Lottie, and 3D each have their own subagent. The result reads as drawn.

The output is real. Plain HTML, CSS, and JS in `source/`. Opens by double-clicking. Emails to a designer who's never heard of Woven.

You bring the agent (Claude Code, Codex, or an API key). Woven is the canvas around it.

This README walks through your first run end-to-end, from install to the Ghibli-themed Totoro feeder app at the bottom, generated from one prompt.

---

## Table of contents

1. [What you need before starting](#1-what-you-need-before-starting)
2. [Install](#2-install)
3. [Start the editor](#3-start-the-editor)
4. [First-run onboarding: connect a model](#4-first-run-onboarding-connect-a-model)
5. [Optional · add asset-provider keys (image · video · SVG)](#5-optional--add-asset-provider-keys-image--video--svg)
6. [Required · install local skills (rembg)](#6-required--install-local-skills-rembg)
7. [Create your first project](#7-create-your-first-project)
8. [Open the workflow and send your first prompt](#8-open-the-workflow-and-send-your-first-prompt)
9. [The final prototype](#9-the-final-prototype)

---

## 1. What you need before starting

You only need four things on your machine:

| Requirement      | Why                                                                          | How to check                          |
| ---------------- | ---------------------------------------------------------------------------- | ------------------------------------- |
| **Python 3.10+** | The editor daemon (`serve.py`) is pure Python with stdlib only.              | `python3 --version`                   |
| **A modern browser** | Chrome, Edge, Safari, or Firefox (anything from the last ~2 years).      | (no command, just open it)            |
| **One of:** Claude Code CLI · Codex CLI · an Anthropic / OpenAI API key | The editor needs at least one way to reach a text model so the agent can run workflows. You'll wire this up in [Step 4](#4-first-run-onboarding-connect-a-model). | `claude --version` / `codex --version` |
| **`rembg`**      | Background-removal step in the `raster-foreground` asset pipeline (characters / mascots / isolated subjects). One-click install from the onboarding card, or `pip3 install --user rembg`. First install pulls ~170 MB of model weights. | `python3 -c "import rembg; print(rembg.__version__)"` |

You do **not** need Node, npm, Docker, or a build step. The editor ships as static HTML + a single Python file.

---

## 2. Install

```bash
# 1. Clone (or download a zip and unpack)
git clone https://github.com/heysami/Woven.git
cd Woven

# 2. (Optional) install one of the supported CLIs.
#    Pick ONE. You only need one connection path to a model.
npm install -g @anthropic-ai/claude-code   # Claude Code
# or
npm install -g @openai/codex               # Codex

# 3. Sign in once so the CLI has a session
claude login    # (if you installed Claude Code)
# or
codex login     # (if you installed Codex)
```

If you'd rather paste an API key instead of installing a CLI, skip the `npm install` step; you'll paste the key in the onboarding UI in [Step 4](#4-first-run-onboarding-connect-a-model).

---

## 3. Start the editor

From the repo root:

```bash
# macOS: double-click in Finder
open editor/serve.command

# any platform: from a terminal
python3 editor/serve.py
```

The daemon prints the URL it's listening on (default **http://localhost:5731/editor/**) and a Finder window / browser tab opens automatically.

To run with a separate workspace folder (multi-project mode), set `TH_WORKSPACE_DIR`:

```bash
TH_WORKSPACE_DIR="$HOME/my-prototypes" python3 editor/serve.py
```

---

## 4. First-run onboarding: connect a model

On the very first launch, the **Projects** page shows a setup card. The top-right pill reads **NO MODEL CONFIGURED** in red. That's your cue that nothing will run until you wire up one connection.

![Onboarding · Step 1 · required agent model](docs/screenshots/01-onboarding-step1.png)

The card has two paths, both equivalent for the agent:

### 4a · Use a CLI

Click **Install a CLI** to open the install-options dialog. The editor lists every supported binary with its install + login commands and live-detects whether each one is on your `PATH`. Once you've installed and signed in, click **I've installed it · refresh**. The dot flips to green and you're done.

![Onboarding · Step 1 · CLI picker](docs/screenshots/02-onboarding-cli-picker.png)

### 4b · Use an API key

Click **Paste an API key** to drop in an Anthropic or OpenAI key. The key is stored locally at `~/.test-harness/media-config.json` (file mode `0600`, never sent anywhere except the provider's own API).

Either path clears the **NO MODEL CONFIGURED** pill the instant it succeeds.

---

## 5. Optional · add asset-provider keys (image · video · SVG)

Step 1 only covers the **agent's text model**. To unlock image generation, video, vector SVG, audio, etc., add the relevant provider keys in **Step 2** of the onboarding card:

![Onboarding · Step 2 · asset providers](docs/screenshots/03-onboarding-asset-providers.png)

Each row shows what the provider covers and lets you paste a key inline, no need to leave the page:

| Provider     | Covers                                                              | Where to get a key                                       |
| ------------ | ------------------------------------------------------------------- | -------------------------------------------------------- |
| **fal.ai**   | image · video · 3D · background removal · upscale (one key, many skills) | https://fal.ai/dashboard/keys                       |
| **Quiver AI**| vector SVG generation                                              | https://docs.quiver.ai/getting-started/quickstart        |
| **OpenAI**   | raster image (`gpt-image-2`) · text models                          | https://platform.openai.com/api-keys                     |
| **Anthropic**| Claude text models · vision-based describe                          | https://console.anthropic.com/settings/keys              |

These are **optional**. Projects can still be created without them; you just won't be able to run the matching skill nodes (image-generate, video-gen, svg-gen, etc.) until the key is in place. You can always come back later via the **gear icon** in the top-right.

---

## 6. Required · install local skills (rembg)

The wizard's **Step 3 · Local skills** lists Python packages the daemon will install into your user site (`pip install --user`). **`rembg` is the one required entry**: it's the background-removal step in the `raster-foreground` asset pipeline (every character, mascot, or isolated subject runs through it on the way to the canvas). Skip it and foreground asset generation falls over at the cutout stage.

![Onboarding · Step 3 · Local skills (rembg)](docs/screenshots/03b-onboarding-local-skills.png)

Click **Install rembg** and give it a minute. First install pulls ~170 MB of ONNX model weights.

If you'd rather drop down to the terminal:

```bash
pip3 install --user rembg
```

Optional packages (for `particle-gl`, `3d`, etc.) can wait. Install them from the gear icon → Settings when the matching pipeline first asks for them.

---

## 7. Create your first project

Once a model is configured, the top-right warning chip disappears, the daemon + CLI chips both go green, and the **+ New project** button lights up. The header now carries two tabs — **Projects** (your gallery) and **System** (a bundled reference for the orchestrators, skills, subagents, and node kinds the editor ships with) — reachable from anywhere on the landing.

![Projects landing · model configured, + New project enabled](docs/screenshots/04-projects-landing.png)

Click **+ New project** (or **+ Create your first project** in the empty state). A single-field modal opens:

![New project modal · name only](docs/screenshots/05-new-project-wizard.png)

Type a folder-safe id (alphanumeric + `.` `_` `-`) and click **+ Create**. That's it — no scope picker, no multi-step wizard. The earlier "Blank / Quick designs / Design system / PRD only / Full guided / Custom" branching was removed; every fresh project lands on a clean workflow canvas and you tell the agent what you want from chat. Need one of the old guided runs? Just ask the agent in plain English on the next screen ("brainstorm three design directions", "write a PRD first", "do the full guided flow", …) and the orchestrator skill picks the right stages.

---

## 8. Open the workflow and send your first prompt

The editor drops you into **workflow mode**. The left sidebar is the **Library** of node types (prompt nodes, asset generators, composition tools…). In the middle of the empty canvas, the editor shows a **"Your workflow is empty"** card with a composer right where you need it. No menus to open, no drawers to expand.

![Empty workflow · canvas-centered composer](docs/screenshots/07-empty-workflow.png)

Type your prompt into the composer. The agent has read/edit/bash access to your project root and will scaffold the prototype from scratch. For this walkthrough we'll use:

> `create a ghibli themed mobile app to feed totoro`

![Prompt typed in the empty-workflow composer](docs/screenshots/08-prompt-entered.png)

Press **⌘/Ctrl + Enter** (or click **Send**) and the agent gets to work, generating the design system, scaffolding pages, dispatching asset jobs, and wiring everything together as nodes on the canvas in real time.

---

## 9. The final prototype

After the agent finishes the run, the workflow canvas fills out with every step that produced the prototype: a column of **Prompt** nodes (one per illustrated subject: Totoro himself, soot sprites, Chibi-Totoro, the Catbus…), each feeding a **Generate image** node, then a **Remove background** node that pipes the cleaned PNG into the final page rendering on the right. The chat drawer streams the agent's tool calls live (Read / Write / Bash) as it scaffolds files into `source/`. The right-most frame is the live phone-mockup of the Ghibli-themed Totoro feeder app, sitting inside the canvas alongside the assets that built it.

![Final prototype · Totoro feeder app on the workflow canvas](docs/screenshots/09-final-prototype.png)

From here you can switch to **Prototype mode** (the play icon in the toolbar) to interact with the full app outside the canvas frame, or re-run any individual asset node (right-click → Run) to regenerate a single illustration without redoing the whole flow.

### What the agent generated from a single prompt

The one-line prompt, *"create a ghibli themed mobile app to feed totoro"*, produced a four-tab app named **Mori**, with a watercolor Ghibli palette, soft-rain weather chip, and consistent illustration style across every screen:

| Glade · feed Totoro | Forage · gather food | Friends · forest companions |
| :---: | :---: | :---: |
| ![Glade tab](docs/screenshots/10-app-glade.png) | ![Forage tab](docs/screenshots/11-app-forage.png) | ![Friends tab](docs/screenshots/12-app-friends.png) |
| Totoro idles in a rainy clearing; three stat bars (**Fullness · Happiness · Trust**) drive a food picker (Acorn the favourite, Sun berry, Mushroom, Leaf roll) with live counts and a hint that O-Totoro loves acorns most. | A list of refilling foraging spots (**Camphor tree hollow · Rain meadow · Root cellar**) with painted location thumbnails and a "Resting · Back in 2h" cooldown on the cellar. Spots regrow over time. | A grid of Ghibli companions (**Chibi-Totoro · Soot sprites · Catbus · Mei**) each with a Here-now / Away presence chip; Catbus and Mei unlock as trust climbs. |

Bottom-tab navigation, the **Mori** wordmark, and the **Soft rain** weather chip carry across every screen. The agent inferred a consistent design system (cream background, sage green accent, hand-drawn icons) from the single prompt and applied it uniformly.

---

## Troubleshooting

| Symptom                                              | Fix                                                                                                    |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| Top-right pill stays red after pasting a key         | Click the **gear icon → Test** on that provider row in Settings to verify the key.                     |
| **CLI missing** chip is amber                        | `which claude`. If empty, run `npm install -g @anthropic-ai/claude-code` then `claude login`.          |
| **Daemon down** chip is red                          | The Python server crashed or was stopped. Re-run `python3 editor/serve.py` from the repo root.         |
| Port 5731 already in use                             | Set a different port: `EDITOR_PORT=5740 python3 editor/serve.py`.                                      |
| Image / video / SVG nodes fail with "no API key"     | Open **Settings (gear)** and add the relevant provider key (see [Step 5](#5-optional--add-asset-provider-keys-image--video--svg)). |

---

## Where things live on disk

```
<workspace-dir>/
├── workspace.json                  # project registry (auto-managed)
├── projects/
│   └── <project-id>/
│       ├── source/                 # the generated prototype HTML/CSS/JS lives here
│       ├── editor/data.js          # canvas state (frames, nodes, arrows)
│       └── workflow/workflow.json  # workflow graph
└── design-systems/
    └── <ds-id>/                    # reusable design systems shared across projects

~/.test-harness/media-config.json   # your provider API keys (mode 0600, per-user)
```

That's it. You're set up.

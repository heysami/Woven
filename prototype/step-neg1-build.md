---
name: step-neg1-build
description: Step -1 post-pick build pipeline — Phases A through F. Loaded ONLY after the user picks an option (numbered pick, "you pick", "lock it", "build", etc.). Locks the picked option's exact typography + palette into the build and restores the existing orchestrator-dispatch chain.
---

# Step -1 — After the user picks (Phases A → F)

Reached when the user has committed an option (clicked a button, said "option N", said "you pick" / "lock it" / "build", or named a fresh direction that's now coherent). This file is the COMPLETE post-pick build contract.

**Critical structural rule:** Step -1's stop-and-ask is the FIRST stage of the existing Woven build pipeline, not a self-contained mini-protocol that ends in "write some files." After the pick, the agent MUST execute Phases A → F below in order, integrating with the existing orchestrator fan-out documented in `AGENTS.md` and `docs/agents/subagents/`. Skipping Phase E or improvising inside Phase C is what produced studio's "picked Space Grotesk + JetBrains Mono, built Anton + Space Mono, skipped photography-orchestrator despite picking acid-design (raster-heavy)" failure.

## Phase A — Lock the contract from the picked `<opt>` (IMMUTABLE through build)

The picked option's child tags are the **immutable contract** for everything downstream. Re-read them from the emitted `<direction-options>` block (they're in your conversation history), and bind them verbatim — no improvisation:

| Picked-opt tag | Locked into | Notes |
|---|---|---|
| `<palette>#bg,#surface,#fg,#muted,#border,#accent</palette>` | `:root` CSS variables in `styles.css` | One CSS var per token. Don't invent extra tokens of different hue; derive shades via `oklch()` from THESE. |
| `<display font="X">` | `--font-display: "X", <sensible fallbacks>;` AND a Google-Fonts `<link>` in every page's `<head>` | If `X` is a system font (Times New Roman, Georgia, Arial, etc.), skip the `<link>` — the family resolves locally. |
| `<body font="X">` | `--font-body: "X", <sensible fallbacks>;` AND a `<link>` for the family (one combined Google Fonts `<link>` if both display + body are Google). | Same system-font carve-out. |
| `<axes>Shell: <shell-X> · Style: <style-Y> · Aesthetic: <aesthetic-Z></axes>` | The three detail files to Read in Phase B | These IDs identify exactly which files under `./prototype/` to inherit vocabulary from. |
| `<vibe>…</vibe>` + `<why>…</why>` + `<label>…</label>` | The genre-commit one-line comment at the top of `styles.css` (or `app.js` line 1) | Captures the WHY for downstream readers. |
| `<image src="…option-N.png"/>` | (Reference only — do NOT embed the preview PNG in `source/`; it was for the chat preview, not the build.) | Stays in `.prototype-options/` as ephemera. |

**The lock is verbatim, not "inspired by".** If the picked option has `<display font="Space Grotesk">`, the `:root` line is:

```css
--font-display: "Space Grotesk", "Helvetica Neue", Arial, sans-serif;
```

NOT `"Anton"`, NOT `"Inter"`, NOT "whatever the agent thinks fits the genre better." The user picked Space Grotesk; the build ships Space Grotesk.

Same for the palette: every hex in `<palette>` becomes a `:root` var. Don't substitute "warmer slate" for `#161616`. If you derive a hover state, do it via `oklch(from var(--accent) calc(l - 0.1) c h)` — anchored to the locked token.

## Phase B — Read the detail files for genre vocabulary

Once Phase A is locked, `Read` the three detail files identified in `<axes>`:

- `./prototype/shell-<id>.md` — layout primitives, density classes, skeleton HTML
- `./prototype/style-<id>.md` — surface treatment vocabulary, depth grammar, shape language, optical inheritance
- `./prototype/aesthetic-<id>.md` (if not "(none)") — cultural register, era cues, decoration vocabulary, named references

Plus, if a `recipe-<id>.md` was named, `Read` that too — recipes bundle all three picks with proven combinations.

**These detail files inform vocabulary, not Phase A locks.** The style detail file may suggest a default font; **the picked `<display font>` overrides that suggestion** — Phase A wins every conflict. The detail files exist to fill in the picks the Step -1 UI didn't surface (shape language, motion budget, voice register, secondary tokens, slot annotation conventions).

## Phase C — Write source per Subagent 1 conventions

Standard source-write per `docs/agents/subagents/1-source.md`:

- Token block at the TOP of `styles.css` carries Phase A's locked palette + font vars + the genre-commit comment, in that order.
- `<link rel="stylesheet" href="https://fonts.googleapis.com/css2?...">` in every page's `<head>` for the picked Google Fonts families.
- Pages link the DS stylesheet first (if a DS is present), then optional prototype overlay.
- Every visual slot is annotated for Subagent 1.V — `img-placeholder` with `data-asset-intent` for static imagery, `motion-placeholder` with `data-motion` for decorative loops (see PROTOTYPE.md → Slot annotations).
- The `data-asset-intent` and `data-motion` strings inherit the picked option's `<vibe>` + style detail file's mood. For an `acid-design` pick, slot intents read "neon-on-black acid graphics, distorted chrome, rave-flyer attitude" not "generic hero illustration".

`prototype.json` is written per the AGENTS.md schema (frames / arrows / lanes / entities) — same flow as the prior pipeline, the Step -1 ask doesn't change it.

## Phase D — Render-verify

Standard: every authored HTML opens and renders without console errors, navigation works, demo data is non-undefined. Fix any errors before Phase E. Screenshot or eval-snapshot to confirm clean state.

## Phase E — Post-build orchestrator dispatch

**Phase E is reachable ONLY after Phases A → B → C → D complete in this turn.** Orchestrators enumerate slots in *already-written source HTML*; they do not exist for pre-commit previews, +draft mockups, "show me an image" requests, or any other pre-build flow. If `source/<branch>/` has no files in it AND no Phase A lock has been written, every orchestrator listed below is **forbidden**. The agent in studio2 broke this by dispatching `visual-orchestrator` from inside the +draft loop — that's a Phase E rule violation and a category error.

After source is written and render-verified, the agent MUST walk the existing orchestrator dispatch chain — each orchestrator's gate is defined in its own manifest under `.claude/agents/<name>.manifest.json`, so the agent's job is sequencing, not gate-evaluation. Dispatch each via the `Task` tool with `subagent_type` matching the manifest's `subagentName`. Walk in this order:

1. **`photography-orchestrator`** — its manifest trigger: "fires when (a) at least one slot will resolve to raster-photo AND (b) an image-generation model is wired into the project". For the acid-design / scrapbook / editorial-warm-restraint family this almost always fires. The orchestrator picks a photo style from `docs/research/photography-library.md`, writes a `pe_photo_<slotId>` enrichment node per photographic slot. Visual-orchestrator reads these later.
2. **`illustration-orchestrator`** — same shape, for raster-foreground (illustrated subjects with transparency, mascots, vector-with-character). Fires for acid-design, corporate-memphis, kawaii, Y2K-memphis-loud, etc. Picks an illustration style from `docs/research/illustration-library.md`.
3. **`creative-visual-orchestrator`** — fires when the committed aesthetic is editorial-loud (acid-design, web-brutalism, y2k-memphis-loud, oversized-neo-grotesque, wacky-pomo, etc.). Promotes flat `<img>` slots into compositions (text-as-mask, asset-cut-into-letters, irregular-clip-path, asset-as-drop-cap). Optional but powerful for the loud register.
4. **`visual-orchestrator` (Subagent 1.V)** — **mandatory** unless `source/` has zero visual slots. Enumerates every slot, classifies the medium, scaffolds the per-asset node graph in `workflow/workflow.json`, dispatches per-asset drawers (raster-photo, raster-foreground, vector-mark, shader, particle-gl, lottie, 3d, video, motion). Reads the photo/illust enrichments from steps 1–2.
5. **`material-orchestrator`** — fires when the committed style is material-bearing per `docs/research/material-library.md` decision tree (skeuomorphism, glassmorphism, claymorphism, holographic-iridescent, neumorphism, frutiger-aero, brushed-metal, paper-grain, etc.). Adds reactive material fidelity (refraction on tilt, parallax on scroll, ripple on hover).
6. **`interactive-polish-orchestrator`** — fires when (a) a DS is present AND (b) the genre is in the restrained-register allow-list per its gate. Adds microanimations, pointer-driven effects, scroll-driven reveals, hover surprises, shader overlays.

For each orchestrator, the agent **does NOT pre-evaluate the trigger** — that's the orchestrator's own job per its manifest. The agent dispatches with the standard envelope (project slug, sourceRoot, projectRoot, genre commit line); the orchestrator reads its manifest's gate against the source and either runs or returns `runStatus:error` if its conditions don't match. The agent moves to the next orchestrator regardless.

The acid-design studio case would hit steps 1, 2, 3, 4, and likely 6 — that's the orchestrator routing that worked before Step -1 was added, and what Phase E now re-establishes.

## Phase F — Report done

After Phases A–E complete, summarise to the user: what was locked from the pick (palette + fonts + axes), which orchestrators ran (with their reported outcomes — `kept N slots, dropped M`), and what's next (typically: "click Run on the workflow canvas to generate the per-asset bitmaps", or "the polish layer is live — refresh to see microanimations").

If any phase failed (Phase B detail-file missing, Phase C render error, Phase E orchestrator dispatch error), report it explicitly — don't claim "done" when the pipeline broke partway.

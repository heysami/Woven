---
name: raster-requirements
description: The 5-step (Step 0 → Step 5) raster-asset decision tree — quick session-capability check, the user ask shape, execute-user-pick branches, archive-search push (with the per-genre-family public-archive table), project-asset parallel search, archive-search-failed report-back, and the "switch the genre, do not fake it" final fallback. Loaded only when the committed style or aesthetic's detail file shows a `**⚠ Raster required:**` marker AND drawing has not yet started. Step numbering inside this file is LOCAL to the raster decision tree — unrelated to PROTOTYPE.md's Step -1/zero/one/... workflow steps.

→ Decision lives in PROTOTYPE.md §"Raster requirements — when SVG will not deliver the genre".
---

# Raster requirements — when SVG will not deliver the genre

Some genres are raster-dependent: their decoration vocabulary is photographic textures, pressed flowers, chrome bokeh, leather grain, pixel sprites, anime portraits, or scrapbook cutouts that **cannot** be faked in SVG, CSS, or geometric primitives. Drawing them as SVG geometry produces wrong-genre output: Skeuomorphism without leather texture reads as Material; Scrapbook without raster cutouts reads as a wireframe; Frutiger Aero without bokeh reads as Aurorism.

Each detail file under `./prototype/` carries a `**⚠ Raster required:**` marker at the top when this applies. The marker names *what kind* of imagery is needed. **No marker = SVG / CSS / typography is sufficient.**

When the committed genre's detail file shows the marker, follow this decision tree **before** drawing anything:

### Step 0 — First: can you generate the assets yourself? Ask the user ONLY if you cannot

**Quick session-capability check (fast — no deep tool-search yet):**

- Does the model have NATIVE image output in this session? (Some Claude / GPT / Gemini configurations ship with it — check before assuming not.)
- Are image-gen MCPs **already loaded** (not deferred)? Glance at the available-tools list — don't `ToolSearch` deferred ones yet.
- Is a Figma MCP already loaded with a linked file that might contain assets?

**If yes to any → proceed silently. Generate or retrieve the assets and build.** Do NOT ask the user about raster — they don't need to know. This is the common case for many sessions.

**Only when no native generation route is available → ask the user before doing anything else.** Don't search archives, don't `ToolSearch`, don't burn time on a question the user can answer in 10 seconds: how would they like you to proceed?

The user may want to change their mind on the style, point you at assets you didn't know exist, set up image generation on their end (which takes their time), or pause until they've prepped. Five minutes searching Polyhaven only to discover they have a Pinterest board waiting — or worse, generating a half-broken substitute — is wasteful.

**The ask is contextual, not a fixed script.** Adapt the wording to the specific brief — its tone (kid app vs finance dashboard vs heritage museum), its specific raster need (textures vs cutouts vs anime portraits vs pixel sprites), and the archives / alternatives that are actually relevant to THIS brief.

**Shape of the ask:**

1. Surface the constraint specifically — name the picked style/aesthetic, name what kind of raster it needs (pulled from the detail file's `**⚠ Raster required:**` marker), say honestly that you can't generate in this session.
2. Offer 3-5 options adapted to THIS brief. Draw from the menu below; pick the ones that fit; word them in the brief's voice register.
3. Wait. Don't search, don't commit assets, don't start drawing.

**Menu of option types to draw from** (pick the relevant ones, name specifics relevant to THIS brief — never list all of them):

- **Change style** — name 2–3 specific raster-free alternatives that preserve THIS brief's tone (not generic options; brief-fitting ones)
- **Point me at assets** — folder path / Pinterest / Are.na / brand library / drag-drop into the thread
- **Set up image generation** — MCP / CLI / web service / paste images one at a time
- **Let me search archives** — name the SPECIFIC archives relevant to this raster need (Polyhaven for PBR textures · Wikimedia + Met Open Access + Smithsonian for botanical / heritage cutouts · NASA GIBS for atmospheric / planetary · Lospec + OpenGameArt for pixel sprites · William Morris archive for Victorian patterns · etc.) — don't list all of them, list the ones that fit
- **Wait while you prep** — for users who need time to set up their tooling first

### Step 1 — Execute the user's chosen path

Based on the user's pick:

- **(a) Change style:** loop back to the Step one selection workflow with "no-raster" as a new tag constraint. Present 3 alternative options whose styles AND aesthetics both lack the `Raster required` marker. Common substitutions: `skeuomorphism` → `restrained-hairline` OR `claymorphism` (CSS-only) · `scrapbook-*` → `editorial-magazine` OR `warm-restraint` recipes · `pixel-*` → `outline-wireframe` OR `doodle` · `frutiger-aero` → `aurorism` (mesh-gradient instead of bokeh photography).
- **(b) Provide assets:** wait for the path / URL / drag-drop. Index what they give you, build with those. Cite source per licence in HTML comments at end of file.
- **(c) Set up image-gen:** wait for their tool/MCP to come online, or for them to paste images. Use whatever route they provided. If they pasted images, save them as project assets first.
- **(d) Search archives:** proceed with Step 2.
- **(e) Wait:** acknowledge and pause. Do NOTHING until pinged again.

### Step 2 — Push hard on the harness, then archive search (only if user chose option (d))

Now go deep. `ToolSearch` for image-related MCPs (`image`, `dalle`, `imagen`, `stable diffusion`, `replicate`, `flux`, `midjourney`, `unsplash`, `pexels`). If anything loads, use it. If not, `WebFetch` + `WebSearch` to pull real images from royalty-free / public-domain sources:

| Genre family need | Public archive |
|---|---|
| Skeuomorphism textures (leather, wood, felt, brushed metal, linen, paper) | **Polyhaven Textures** (CC0), Subtle Patterns, Lost & Taken |
| Scrapbook cutouts (pressed flowers, vintage botanical, antique objects, fabric) | **Wikimedia Commons**, **Met Museum Open Access**, **Smithsonian Open Access**, Rawpixel public-domain |
| Frutiger Aero motifs (bokeh, sky, water, plants, dolphins, koi) | **Polyhaven HDRIs**, **Unsplash**, **Pexels**, Wikimedia (Vista wallpapers archive) |
| Pixel-art sprites and tilesets | **Lospec** (palettes + sprite references), **OpenGameArt** CC0, **itch.io** free asset packs, **Kenney.nl** |
| Holographic / iridescent surfaces | **Polyhaven** (iridescent / pearlescent textures), Unsplash (oil-on-water macro) |
| Chrome / Y2K / blobject 3D renders | **Sketchfab CC0** (download 3D models, render screenshots), Polyhaven, Wikimedia retro-tech |
| Photographic backdrops (Glassmorphism / Liquid Glass substrates) | **Unsplash**, **Pexels**, **Polyhaven** |
| Museum / heritage imagery (Maximalism, art-historical, Atompunk, period) | National Gallery DC, Rijksmuseum, Getty, Yale Center for British Art, Met Museum, Smithsonian — all **IIIF** |
| NASA / atomic-age / space imagery (Atompunk) | **NASA Image Gallery** (public domain), NARA, ESA |
| Pattern wallpapers (Maximalism, Victorian, William Morris) | **William Morris archive** (out of copyright), Wikimedia Commons, Met Museum |
| Vaporwave references (marble busts, palm silhouettes, plaza grids) | Wikimedia Commons (Roman / Greek sculpture), Unsplash (palm trees, malls) |
| 90s rave / Acid Design / Corporate Grunge textures | archive.org (vintage zines / flyers), Wikimedia Commons, Internet Archive image library |
| CRT / Cassette Futurism textures | Wikimedia (period hardware photography), archive.org control-panel scans |

Reference real URLs via `<img src>` — do not inline as data URIs unless under 5 KB. **Always credit the source per its licence** in a comment block at the end of the HTML.

### Step 3 — Search project assets in parallel with the archive search

Check the project tree for a reference folder, brand asset library, design system folder, screenshot folder, or moodboard the user may have already dropped without mentioning. Project assets always beat archive fetches in fidelity. If the project has them, switch to using those.

### Step 4 — Archive search failed — REPORT BACK to the user

If Step 2 + Step 3 both come up empty (or yield assets too low-fidelity to use), surface the failure with the new info — don't keep searching silently:

> *"I searched [list specific archives tried] and the project tree but couldn't find suitable assets for [specific raster need]. Three options now:*
> *(a) **Change the style** — I'll present 3 raster-free alternatives that preserve the brief's tone*
> *(b) **You still have assets / a board / image-gen** — point me at them now*
> *(c) **Switch the genre on my judgement** — I'll pick the closest non-raster recipe and explain the substitution*
>
> *Which?"*

### Step 5 — If still nothing — switch the genre, do not fake it

If the user has no images and no generation route, **do NOT silently fall back to SVG / CSS shapes.** That produces a different genre wearing the wrong genre's name — and the wrong-genre output is worse than admitting the constraint.

Instead:
- Pick a non-raster-requiring alternative from the playbook
- Name the substitution explicitly in your reply: *"Switching from Scrapbook-cottagecore to Editorial-magazine because no cutout source is available. The brief's warmth is preserved through serif typography + warm cream palette + drop-cap ornament instead of raster cutouts."*
- Build in the substituted genre cleanly, not in wrong-genre-cosplay-via-SVG mode

**Why this matters:** the failure mode of every raster-dependent genre is "AI tried to draw it with primitives and got the genre wrong." Skeuomorphism with CSS gradients reads as Material 3. Scrapbook with SVG icons reads as a wireframe. Frutiger Aero with mesh gradients reads as Aurorism. PC-98 with anti-aliased SVG reads as a generic vintage-coded landing. The substituted-genre output is genuine and shippable; the faked-genre output ships the wrong vibe under the right label.

---


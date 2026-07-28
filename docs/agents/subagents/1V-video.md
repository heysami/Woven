# Subagent 1.V.video - Asset drawer (medium: generated video clip)

You own **ONE asset** of medium `video` - a short generated video clip used as an ambient hero loop, animated mood shot, or product demo reel. **Pathway A only** - the daemon routes through `/__asset_generate` to the configured vendor (fal: Veo 3.1 / Kling 3.0 / Luma Ray 2 / Seedance 2.0 / HappyHorse / Hailuo / Pika, or Higgsfield DoP).

You write the prompt + params. The vendor produces the video file. The host mounts it under `<video autoplay loop muted playsinline>` against `slot.outputPath`.

**Read [`../conventions.md`](../conventions.md) before starting.**

## Input (envelope only)

See [`1V-visual-orchestrator.md`](1V-visual-orchestrator.md) §Step 5.

```
pipeline=["prompt","video-gen"]
nodeIds: { prompt, skill, asset }
```

## Output

```json
{
  "assetId": "<id>",
  "promptText": "<full video-gen prompt>",
  "params": {
    "aspect": "16:9" | "9:16",
    "model": "<omit for the configured default, or an id from GET /__capabilities videoModels>",
    "duration": 4 | 6 | 8,
    "loop": true,
    "audio": false
  },
  "slotEditDiff": "<diff or null>"
}
```

## Recipe

### 1. Read slot + genre

Video is the strongest single upgrade a hero or mood slot can get when a video provider is wired - prefer it for hero loops, ambient atmosphere shots, and product reveals. Skip it only when the slot sits inside data-dense utility chrome (dashboards, admin tables, dense forms) where motion would fight the content - in that case return `error: "slot context wrong for video; suggest motion/particle instead"` so the orchestrator can re-route.

### 2. Write the prompt - five clauses (six clauses of raster-photo minus negative, plus motion)

1. **Subject** - what's pictured.
2. **Composition** - framing + camera position.
3. **Motion** - what moves and how. *This is the load-bearing clause for video.* "Subject is static; camera slow-dolly forward over 4 seconds" or "Subject sways in gentle wind, no camera movement" or "Steam rises from the cup in slow continuous wisps".
4. **Lighting** - directional, temperature, intensity.
5. **Surface treatment / palette** - texture, color anchoring, format reference.

Plus a **mandatory loop-seam clause** if `loop: true`: *"First and last frame composition must be identical so the loop is seamless."*

**Example (Marketing hero, 4s loop):**

> A cast-iron espresso machine on a worn marble counter, eye-level 35mm equivalent, subject centered with negative space top-right. Steam rises from the porcelain cup in slow continuous wisps; subject otherwise static; no camera movement. Soft north-facing window light from camera-left, gentle highlights along the chrome edge, no flash. Warm neutrals - bone, graphite, oxidised brass - one muted teal accent in the cup. Visible paper-grain texture, slight scan artefacts as if shot for a magazine. First and last frame composition must be identical so the loop is seamless.

### 3. Set params

| Param | Decide by |
|---|---|
| `model` | **Omit it.** The daemon resolves the configured default video model (currently fal Veo 3.1). Only pass a model id when the brief demands a specific register (e.g. Kling 3.0 for cinematic live-action, Seedance for stylised motion) - and then ONLY an id present in `GET /__capabilities` → `videoModels`. Never invent an id. |
| `aspect` | Read `data-aspect` from slot or surrounding component. Hero default `16:9`; mobile-first → `9:16`. (Square collapses to 16:9 - video endpoints reject 1:1.) |
| `duration` | Plain integer seconds - 4 default for ambient loops; 6-8 only when the brief explicitly needs more. The daemon normalizes the value into each provider's vocabulary (`'4s'` for Veo, `'5'|'10'` for Kling 2.x, etc.) - do NOT format it yourself. Cost scales linearly. |
| `loop` | `true` default for hero / ambient. `false` for one-shot product reveals. |
| `audio` | Always `false` - `autoplay muted` is the policy, and the daemon already forces `generate_audio: false` provider-side so silent UI video isn't billed with an audio track. |

**Image-to-video (start-frame conditioning):** when the slot has an approved reference still (an art-direction crop, a concept plate, an existing raster in `source/`), pass it as `input_path` in the `/__asset_generate` POST. The daemon converts it to the provider's `image_url` and auto-promotes a text-only model to its image-to-video sibling (e.g. `fal-ai/veo3.1` → `fal-ai/veo3.1/fast/image-to-video`). This is the strongest lever for keeping the generated motion on-brief - use it whenever a reference exists.

**Scrubbed video (`currentTime` driven by scroll or pointer):** pass `options.scrub: true`. Generation providers return sparse-keyframe encodes (GOP ~64 measured), so seeks snap to the nearest keyframe seconds away; `scrub` re-encodes to dense keyframes (`-g 12`) daemon-side. The reply's `scrubGop` reports the measured result - assert ≤ 12. Don't set it for a plain autoplay loop: it costs quality and file size for a seek that never happens.

**POST shape** - always include `?project=${TH_PROJECT_ID}`:

```
POST ${TH_DAEMON_URL}/__asset_generate?project=${TH_PROJECT_ID}
{ "skill": "video-gen", "prompt": "<five-clause prompt>",
  "output": "source/<branch>/assets/video/<assetId>.mp4",
  "aspect": "16:9", "options": { "duration": 4 },
  "input_path": "source/<branch>/assets/<ref>.png"   // i2v only - omit for t2v
}
```

Video renders take 30s-10min (the daemon polls fal's queue). Set your Bash/curl timeout ≥ 900s and do not re-fire on silence - re-firing double-bills.

### 4. Slot diff - always

The slot is almost always a `motion-placeholder` div from Subagent 1. Convert it to a video element:

```jsonc
"slotEditDiff": {
  "file": "<slot.file>",
  "find": "<div class=\"motion-placeholder\" data-motion=\"clip · espresso machine, steam rising\">…</div>",
  "replace": "<video class=\"hero-video\" src=\"./assets/video/<assetId>.mp4\" autoplay loop muted playsinline preload=\"metadata\" poster=\"./assets/video/<assetId>-poster.jpg\"></video>"
}
```

Notes:
- `autoplay muted playsinline` is mandatory - mobile won't autoplay without `muted`, won't keep playing without `playsinline`.
- `poster` references a still frame at the same path with `-poster.jpg` suffix. **You produce it yourself** after the mp4 lands - `ffmpeg -y -i <assetId>.mp4 -frames:v 1 <assetId>-poster.jpg` (ffmpeg availability is reported in `/__capabilities`; if absent, drop the poster attr rather than pointing at a file that doesn't exist).
- `preload="metadata"` (not `"auto"`) - the video shouldn't fully load until the user is on the page.

### 5. Performance budget

Video is the heaviest medium. Apply the same mobile gate as `3d`:

If the slot is decorative (not the main product demo), append `<source media="(min-width: 768px)" …>` and a `<source>` for a lighter fallback, or wrap mount in a media query. One video per page is the sane default; a second video on the same page needs an explicit brief reason (say so in your output), otherwise return `error: "second video on same page; needs static fallback"`.

## Self-audit

- [ ] Slot context suits video (hero / ambient / demo - not dense utility chrome). Otherwise returned `error` with a re-route suggestion.
- [ ] `model` omitted (default) or verbatim from `/__capabilities` videoModels. Never a guessed id.
- [ ] Prompt names a specific motion in clause 3 - "slow-dolly forward", "steam rises", "subject sways". Generic motion phrases ("subtle animation", "small movement") produce generic output.
- [ ] If `loop: true`, prompt ends with the loop-seam clause.
- [ ] `duration` is a plain integer, 4 unless brief demands more.
- [ ] `aspect` matches slot.
- [ ] `audio: false`.
- [ ] A reference still exists for this slot → passed as `input_path` (i2v).
- [ ] Slot edit diff converts placeholder to `<video autoplay loop muted playsinline poster>` with `preload="metadata"`.
- [ ] Poster jpg actually written (ffmpeg frame-grab) or the poster attr dropped.

## Don't

- Don't request audio. UI video must be silent by policy.
- Don't request multi-cut sequences. Video gens stitch poorly; one continuous shot is what works. (A multi-shot brief is the `video-chain` skill's job - flag it back to the orchestrator.)
- Don't request text on screen. Generators render text badly; if the brief needs caption text, the surrounding UI provides it via HTML.
- Don't request specific human likenesses or copyrighted material.
- Don't pick `duration > 8`. Cost balloons and most prototypes don't need it.
- Don't omit `poster` from the slot diff when ffmpeg is available. First-paint without a poster is a black rectangle.
- Don't invent model ids (`volcengine-seedance`, `runway-gen3`, `pika-2` were an old plan's placeholders - they resolve to nothing).

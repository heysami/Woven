# Subagent 1.V.video — Asset drawer (medium: generated video clip)

You own **ONE asset** of medium `video` — a short generated video clip used as an ambient hero loop, animated mood shot, or product demo reel. **Pathway A only** (Volcengine, Runway, Pika, etc. — the daemon routes through `/__asset_generate` to the configured vendor).

You write the prompt + params. The vendor produces the video file. The host mounts it under `<video autoplay loop muted playsinline>` against `slot.outputPath`.

**Read [`../conventions.md`](../conventions.md) before starting.**

## Input (envelope only)

See [`1V-visual-planner.md`](1V-visual-planner.md) §Step 5.

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
    "aspect": "16:9" | "9:16" | "1:1" | "4:3",
    "model": "volcengine-seedance" | "runway-gen3" | "pika-2",
    "duration": 4 | 6 | 8,
    "loop": true,
    "audio": false
  },
  "slotEditDiff": "<diff or null>"
}
```

## Recipe

### 1. Read slot + genre

Video is heavy decoration — typically only Marketing / Bento / Consumer-products genres carry it. Return `error: "genre forbids video medium"` if mismatched.

### 2. Write the prompt — five clauses (six clauses of raster-photo minus negative, plus motion)

1. **Subject** — what's pictured.
2. **Composition** — framing + camera position.
3. **Motion** — what moves and how. *This is the load-bearing clause for video.* "Subject is static; camera slow-dolly forward over 4 seconds" or "Subject sways in gentle wind, no camera movement" or "Steam rises from the cup in slow continuous wisps".
4. **Lighting** — directional, temperature, intensity.
5. **Surface treatment / palette** — texture, color anchoring, format reference.

Plus a **mandatory loop-seam clause** if `loop: true`: *"First and last frame composition must be identical so the loop is seamless."*

**Example (Marketing hero, 4s loop):**

> A cast-iron espresso machine on a worn marble counter, eye-level 35mm equivalent, subject centered with negative space top-right. Steam rises from the porcelain cup in slow continuous wisps; subject otherwise static; no camera movement. Soft north-facing window light from camera-left, gentle highlights along the chrome edge, no flash. Warm neutrals — bone, graphite, oxidised brass — one muted teal accent in the cup. Visible paper-grain texture, slight scan artefacts as if shot for a magazine. First and last frame composition must be identical so the loop is seamless.

### 3. Set params

| Param | Decide by |
|---|---|
| `aspect` | Read `data-aspect` from slot or surrounding component. Hero default `16:9`; mobile-first → `9:16`; equal-square card → `1:1`. |
| `model` | Default `volcengine-seedance` (already wired in Open Design plan §12). Fall back to whichever is configured. |
| `duration` | 4 seconds default for ambient loops; 6–8 only when the brief explicitly needs more (a product reveal, a multi-step demo). Cost scales linearly. |
| `loop` | `true` default for hero / ambient. `false` for one-shot product reveals. |
| `audio` | Always `false` — `autoplay muted` is the policy; UI ambient video should not depend on audio. |

### 4. Slot diff — always

The slot is almost always a `motion-placeholder` div from Subagent 1. Convert it to a video element:

```jsonc
"slotEditDiff": {
  "file": "<slot.file>",
  "find": "<div class=\"motion-placeholder\" data-motion=\"clip · espresso machine, steam rising\">…</div>",
  "replace": "<video class=\"hero-video\" src=\"./assets/video/<assetId>.mp4\" autoplay loop muted playsinline preload=\"metadata\" poster=\"./assets/video/<assetId>-poster.jpg\"></video>"
}
```

Notes:
- `autoplay muted playsinline` is mandatory — mobile won't autoplay without `muted`, won't keep playing without `playsinline`.
- `poster` references a still frame at the same path with `-poster.jpg` suffix. The vendor's response typically includes a poster; the daemon writes it alongside the video.
- `preload="metadata"` (not `"auto"`) — the video shouldn't fully load until the user is on the page.

### 5. Performance budget

Video is the heaviest medium. Apply the same mobile gate as `3d`:

If the slot is decorative (not the main product demo), append `<source media="(min-width: 768px)" …>` and a `<source>` for a lighter fallback, or wrap mount in a media query. For prototype scope this is usually unnecessary — Subagent 1.V's classifier should not place video on every page; one per prototype is the realistic ceiling.

## Self-audit

- [ ] Genre allows video. Otherwise returned `error`.
- [ ] Prompt names a specific motion in clause 3 — "slow-dolly forward", "steam rises", "subject sways". Generic motion phrases ("subtle animation", "small movement") produce generic output.
- [ ] If `loop: true`, prompt ends with the loop-seam clause.
- [ ] `duration` is 4s unless brief demands more.
- [ ] `aspect` matches slot.
- [ ] `audio: false`.
- [ ] Slot edit diff converts placeholder to `<video autoplay loop muted playsinline poster>` with `preload="metadata"`.
- [ ] No two video assets on the same page (Subagent 1.V's classifier should've caught this — if the envelope hands you a second video, return `error: "second video on same page; needs static fallback"`).

## Don't

- Don't request audio. UI video must be silent by policy.
- Don't request multi-cut sequences. Video gens stitch poorly; one continuous shot is what works.
- Don't request text on screen. Generators render text badly; if the brief needs caption text, the surrounding UI provides it via HTML.
- Don't request specific human likenesses or copyrighted material.
- Don't pick `duration > 8`. Cost balloons and most prototypes don't need it.
- Don't omit `poster` from the slot diff. First-paint without a poster is a black rectangle.

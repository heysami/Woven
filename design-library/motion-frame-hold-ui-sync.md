---
techniqueId: frame-hold-ui-sync
name: Frame-hold UI sync (pause the film, play the interface)
category: composition
subCategory: video
role: product
binding: wheel-step
medium: video
pairsPrototypes: [recipe-bento-marketing, recipe-devtools-marketing, recipe-scientific-infra-marketing, recipe-ai-foundry-dark]
notForUseWhen: The video has no natural stopping poses (continuous abstract flow, atmosphere) — holds need distinct, stable frames worth annotating; or the scene's UI is a single static headline with nothing to reveal per beat — then a plain ambient loop does the job without the machinery.
---

# Frame-hold UI sync (pause the film, play the interface)

The "do something without leaving the scene" primitive: the scene's video plays to an AUTHORED hold frame and pauses; UI elements animate in synced to that exact frame (spec list, price, hotspots); the next wheel-step resumes playback to the following hold — or, past the last hold, hands the input off to the scene choreography to advance.

## Motion signature

- The scene is a sequence of hold beats: `holds: [2.0, 4.5, 7.2]` (seconds) is part of the storyboard contract, authored before generation and embedded in the prompt as distinct poses.
- On entry the video plays from t=0 and a `timeupdate` watcher pauses at the first hold (tolerance ±50ms; correct with a final `currentTime` set so the held frame is exact and repeatable).
- At each hold, that beat's UI cluster animates in: items stagger 60–90ms apart, 250ms each, translateY 12px + fade, starting ≤100ms after the pause — the deceleration of the film and the arrival of the type must read as one gesture.
- Next input: current beat's UI exits (150ms), video resumes to the next hold. Input received past the final hold is NOT consumed — it propagates to the stepper, which advances the scene. Inputs during playback-to-hold are swallowed (the travel between holds is 1–3s; it is the pacing).

## Asset generation spec

- **Resolution**: 1920×1080 minimum (2160p preferred — held frames are stared at like stills), full-bleed edge-to-edge.
- **Holds are IN the prompt**: the generation must produce distinct, fully stable poses at each beat — "the device rises and stops fully still facing front (beat 1), then rotates and stops fully still in profile (beat 2), then the casing opens and stops fully still (beat 3)". Motion-blur or residual drift on a hold frame makes the pause look like a buffering stall.
- **Composition**: the subject keeps to its storyboard third in EVERY hold pose; each beat's quiet zone must be clean because each beat's UI lands there. If beats need different UI sides, the prompt must move the subject deliberately between holds.
- **Duration**: 6–12s for 2–4 holds; 1–3s of travel between poses.
- **Negative prompt**: no text, no watermark, no letterboxing, no camera move, no scene cut, no motion blur at rest poses, no flicker.

## Interaction binding

```js
const holds = [2.0, 4.5, 7.2];           // storyboard contract, embedded in the prompt
let beat = -1, travelling = false;
function toNextHold() {
  if (travelling) return false;          // swallow input mid-travel
  if (beat >= holds.length - 1) return true;   // not consumed → stepper advances the scene
  travelling = true; hideBeatUI(beat); v.play();
  const target = holds[++beat];
  v.ontimeupdate = () => {
    if (v.currentTime >= target - 0.05) {
      v.pause(); v.currentTime = target;  // exact, repeatable held frame
      v.ontimeupdate = null; travelling = false;
      showBeatUI(beat);                   // 60–90ms stagger, 250ms items
    }
  };
  return false;                           // consumed
}
```

- Back-step mirrors forward: seek directly to the previous hold (no reverse playback — decoders hate it), 300ms crossfade over the seek, show that beat's UI.
- `muted playsinline preload="auto"`; poster = the FIRST hold frame so a pre-play scene already looks composed.

## UI composition rules

- Each beat owns ONE UI cluster (3–5 items max: label, spec rows, price, or 2–3 hotspot dots with leader lines) placed in that hold frame's quiet zone — verify against the exact held frame, not the poster.
- Hotspot dots anchor to subject features in frame fractions per hold (`{x: 0.71, y: 0.42}`); they are part of the storyboard, measured off the generated hold frame during QA.
- Persistent scene chrome (headline, beat indicator "2 / 3") never moves between beats; only beat clusters swap.

## Example asset prompt template

> Product film with authored hold poses: a brushed-titanium handheld device anchored on the right third of frame on a seamless dark ground, rises into frame and stops completely still facing front at 2 seconds, rotates smoothly and stops completely still in left profile at 4.5 seconds, casing slides open and stops completely still at 7.2 seconds, each rest pose perfectly sharp and motionless, fixed camera, constant studio lighting, left third of frame empty in every pose, edge-to-edge, photoreal, 1920x1080, 9 seconds, no text, no watermark, no letterboxing, no camera movement, no motion blur at rest poses.

## When to use

- Product walk-throughs inside a scene sequence: one object, 2–4 facets, each with its own specs.
- Pricing or feature reveals that should feel narrated, not listed.
- Any brief that says "tour the product without leaving the moment".

## When NOT to use

- More than 4 holds — the scene becomes a trapped slideshow; split into two scenes.
- Videos generated without the hold contract — retrofitting holds onto free footage lands mid-motion; regenerate.
- When no video provider is wired — degrade to N generated stills (one per hold pose, same prompt skeleton) crossfaded 400ms per beat; identical UI sync, identical input model.

## Performance notes

- One video element per scene; seeks land on keyframes — encode with `-force_key_frames` at every hold timestamp.
- Beat UI animates `transform` + `opacity` only; hotspot leader lines are SVG strokes with `stroke-dashoffset` draws (200ms).
- `prefers-reduced-motion`: skip travel playback — jump-cut directly between hold frames (instant seek, 150ms UI fade); the beat structure and content survive at full stop.

## Pairs with (prototype slugs)

- `recipe-bento-marketing`
- `recipe-devtools-marketing`
- `recipe-scientific-infra-marketing`
- `recipe-ai-foundry-dark`

<!-- image: sample-1.png -->
<!-- reason: representative reference — video paused on an authored hold frame with the beat's spec cluster synced in -->

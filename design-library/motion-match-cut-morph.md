---
techniqueId: match-cut-morph
name: Match-cut morph (the cut you never see)
category: scene-choreography
subCategory: video
role: transition
binding: wheel-step
medium: video
pairsPrototypes: [recipe-editorial-magazine, recipe-ai-foundry-dark, aesthetic-cyberpunk, style-bold-display]
notForUseWhen: Assets are generated independently per scene with no shared composition contract — the morph lives or dies on frame-matched pairs; without paired generation this is just a hard cut. Also wrong for decks longer than ~5 scenes; authoring N-1 matched seams does not scale.
images:
  - src: motion-match-cut-morph-ui.png
    reason: Motion technique UI mockup.
  - src: motion-match-cut-morph-isolated.png
    reason: Signature technique, isolated.
---

# Match-cut morph (the cut you never see)

On advance, the outgoing scene's video plays to its FINAL frame whose silhouette, position, and scale match the incoming video's FIRST frame — the two assets are generated as a composition-locked pair, so a hard cut between them reads as one object transforming into another.

## Motion signature

- Held scenes idle on an ambient loop; a wheel-step triggers the outgoing clip's "exit tail" (0.8–1.5s) which decelerates into the authored match frame.
- The cut itself is a single frame swap at the match point — no dissolve, no wipe. Any blend softens the silhouette and kills the trick.
- Incoming clip opens on its matched first frame and plays its "entry head" (0.8–1.5s) out into its own loop.
- Back-step plays the seam in reverse order: incoming clip's entry head is also generated reversed-playable (symmetric motion, no pour/shatter physics), or keep a reversed-encoded copy of the head.
- Debounce = exit tail + entry head + 200ms; one transformation at a time.

## Asset generation spec

- **Resolution**: 1920×1080 minimum, full-bleed edge-to-edge; the match frame is inspected at 100% — render the pair at the same resolution from the same prompt skeleton.
- **Composition**: write ONE composition contract sentence shared by both prompts — e.g. "a circular object 40% of frame height, centered at 62% horizontal, 50% vertical, on a near-black ground" — then vary only the subject noun. Silhouette scale within ±5%, position within ±2% of frame, or the cut reads as a jump.
- **The pair IS the deliverable**: scene N's prompt must end ON the match pose ("settles motionless as a perfect ring filling 40% of frame height at right-center"); scene N+1's prompt must START from it.
- **Negative prompt**: no text, no watermark, no letterboxing, no camera move, no scene cut, no zoom, no background change at the final frame.

## Interaction binding

```js
async function advance() {
  if (busy) return; busy = true;
  outV.currentTime = outV.duration - TAIL;       // jump to exit tail
  await outV.play();
  outV.onended = () => {
    swap(outV, inV);                              // single-frame DOM swap, no fade
    inV.currentTime = 0;
    inV.play();                                   // muted + playsinline
    setTimeout(() => { busy = false; }, 200);
  };
}
```

- Preload and pre-decode the incoming clip (`preload="auto"`, then `inV.currentTime = 0` once metadata loads) BEFORE the step — a decode stall at the match frame is fatal.
- QA gate: pixel-diff the two match frames; >3% differing pixels inside the subject's bounding box fails the pair and re-generates scene N+1.

## UI composition rules

- Both scenes in a pair share the SAME quiet zone side — the subject holds its frame position across the cut, so the UI slot is stable through the seam.
- Outgoing copy fades out during the exit tail; incoming copy enters 150–250ms AFTER the cut — the morph moment itself stays type-free so the eye is on the transformation.
- Persistent chrome only at frame edges, never near the subject's matched silhouette.

## Example asset prompt template

> Pair clip A of a match-cut: a glowing turbine ring, a circular object 40% of frame height centered at the right third of frame on a near-black seamless ground, spins slowly then decelerates and settles motionless in a perfect front-facing circle as the final frame, fixed camera, constant lighting, edge-to-edge composition, large empty left third, photoreal, 1920x1080, no text, no watermark, no letterboxing, no camera movement, no zoom. (Clip B: identical sentence with "a ringed planet" as subject, starting motionless from the same pose.)

## When to use

- Concept-bridge storytelling: turbine→planet, eye→lens, pill→moon — when the seam IS the argument.
- Short high-craft pieces (3–5 scenes) for launches, title sequences, awards-bait portfolio work.
- Briefs that say "seamless", "one continuous thought", "Kubrick cut".

## When NOT to use

- Content-led decks where scenes are interchangeable — the authoring cost buys nothing; use scene-crossfade-hold.
- Subjects without a clean silhouette (fog, crowds, particle fields) — nothing to match.
- When no video provider is wired — degrade to a paired-still version: generate both match frames as rasters and cut between them with a 250ms scale pulse (1.0 → 1.03 → 1.0) at the swap.

## Performance notes

- Encode with a keyframe ON the match frame (`-force_key_frames` at the timestamp) so the seam never lands mid-GOP.
- Two videos resident per seam maximum; release the outgoing clip 1s after the cut.
- `prefers-reduced-motion`: skip tails and heads entirely — hold each scene on its match frame and hard-cut between stills.

## Pairs with (prototype slugs)

- `recipe-editorial-magazine`
- `recipe-ai-foundry-dark`
- `aesthetic-cyberpunk`
- `style-bold-display`

<!-- image: sample-1.png -->
<!-- reason: representative reference — the matched final/first frame pair showing identical silhouette and position -->

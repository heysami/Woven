---
techniqueId: scroll-exit-handoff
name: Scroll-exit handoff (one scene's exit becomes the next scene's entrance)
category: scroll-driven
subCategory: video
role: transition
binding: scroll-trigger
medium: video
pairsPrototypes: [recipe-editorial-magazine, recipe-neo-grotesque-portfolio, recipe-aurora-marketing, style-liquid-glass, aesthetic-vaporwave]
notForUseWhen: Adjacent scenes have no visual kinship to exploit (a chart section into a testimonial wall — nothing to match on), or either neighboring scene is itself scroll-scrubbed — a pinned scrub between two triggered clips breaks the velocity chain.
---

# Scroll-exit handoff (one scene's exit becomes the next scene's entrance)

At the boundary between two full-bleed scenes, the outgoing scene's asset plays a short exit clip whose final motion — direction and velocity — is matched by the incoming scene's entrance clip, so the two scenes read as one continuous gesture instead of a cut on scroll.

## Motion signature

- Two play-once clips fired in a fixed relay: the exit triggers when the boundary reaches ~25% from the viewport bottom (`IntersectionObserver`, threshold on a sentinel), the entrance fires 200–400ms later, while the exit is still decelerating — overlap is mandatory; sequential play reads as two events.
- The match cut is the law: exit ends moving up-left at speed → entrance begins moving up-left at the same apparent speed and decays to rest. Match direction within ~15° and velocity within ~25%, or the seam shows.
- Both clips are short (1–2.5s) and end on hold frames; the entrance's hold frame is the next scene's resting layout (see scroll-entrance-video).
- Fires once per page load by default; fast scrolling past the boundary skips both clips and lands on hold frames — the handoff is a reward, never a gate.
- Scrolling back up does NOT replay in reverse — exits are one-way; the boundary shows both hold frames on return.

## Asset generation spec

- **Resolution**: both clips 1920×1080 minimum, edge-to-edge; MP4 + WebM each.
- **Composition**: the exit's FINAL frames and the entrance's FIRST frames must rhyme — shared motion vector, related silhouette or color mass at the matching screen position (e.g. exit: bottle sweeps off upper-left, leaving a teal streak; entrance: teal wave enters from lower-right along the same axis). Both scenes keep their quiet zones on the SAME side so UI never jumps sides across the seam.
- **Continuity**: each clip is one continuous motion, fixed camera, no cuts; generate the exit first, then write the entrance prompt quoting the exit's final direction, speed feel, and dominant color explicitly.
- **Duration**: 1–2.5s per clip; total boundary theater under 4s.
- **Negative prompt** (both): no text, no watermark, no letterboxing, no scene cut, no camera move, no direction change mid-clip.

## Interaction binding

```js
const io = new IntersectionObserver(([e]) => {
  if (e.isIntersecting && !boundary.dataset.fired) {
    boundary.dataset.fired = '1';
    exitVideo.play();                       // outgoing scene departs
    setTimeout(() => enterVideo.play(), 300); // incoming arrives mid-exit
    io.disconnect();
  }
}, { rootMargin: '0px 0px -25% 0px' });
io.observe(boundarySentinel);
[exitVideo, enterVideo].forEach(v => v.addEventListener('ended', () => v.pause()));
```

- Both videos `muted playsinline preload="auto"` (the boundary is known in advance — warm both within 1.5 viewports).
- Poster frames: exit's poster = its first frame (the scene at rest); entrance's poster = its LAST frame, so skip-ahead scrollers land on the settled layout.

## UI composition rules

- The outgoing scene's copy fades out 150ms BEFORE the exit fires (it should never travel with the asset); the incoming copy enters ≤120ms after the entrance settles.
- No UI may straddle the boundary — each scene's quiet zone owns its own copy, same side both scenes.
- Keep the page background identical across the boundary (sample the same hex into both prompts) — a background jump destroys the continuity the motion just bought.

## Example asset prompt template

> Exit clip — product film: an amber glass bottle on the right third of frame accelerates smoothly up and off the upper-left corner, trailing a soft amber light streak along its path, one continuous accelerating motion, fixed camera, seamless background exactly #101014, left third of frame stays empty, photoreal, 1920x1080, 2 seconds, no text, no watermark, no camera movement, no direction change. (Entrance clip: quote this exit's direction — "enters from lower-right traveling up-left at matching speed, decelerating to rest at the right third" — same background hex, same lighting.)

## When to use

- Multi-scene marketing scrollers where scene boundaries are the seams that cheapen everything else.
- Narrative sequences (ingredient → product → lifestyle) that benefit from literal visual causality.
- Briefs that say "it should flow" — this is the technique that makes flow concrete.

## When NOT to use

- Between scenes of different roles and energies (hero into pricing table) — continuity implies kinship the content doesn't have.
- Pages with more than 3 handoffs — each costs two clips; past three, the relay becomes the show and the content loses.
- When no video provider is wired — degrade to matched CSS transforms: outgoing still translates off along vector V with `easeInQuad`, incoming still enters along V with `easeOutQuad`, 250ms overlap.

## Performance notes

- Two clips per boundary, ≤4MB each; lazy-load any boundary below the second viewport at `metadata` until within 1.5 viewports.
- Pause and release both elements after `ended` (`removeAttribute('src')` is unnecessary — just ensure no loop and no rAF attached).
- `prefers-reduced-motion`: never fire either clip; both scenes show their hold frames and the boundary is an ordinary cut.

## Pairs with (prototype slugs)

- `recipe-editorial-magazine`
- `recipe-neo-grotesque-portfolio`
- `recipe-aurora-marketing`
- `style-liquid-glass`
- `aesthetic-vaporwave`

<!-- image: sample-1.png -->
<!-- reason: representative reference — the boundary mid-handoff, exit streak and entrance motion sharing one vector -->

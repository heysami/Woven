---
techniqueId: scroll-speed-ramp
name: Scroll speed-ramp (ambient loop breathes with scroll velocity)
category: scroll-driven
subCategory: video
role: background
binding: scroll-velocity
medium: video
pairsPrototypes: [recipe-ai-foundry-dark, recipe-aurora-marketing, style-holographic, aesthetic-frutiger-dark-aero, aesthetic-cyberpunk]
notForUseWhen: The background sits behind dense reading content (a background that reacts to reading-scroll punishes the reader), or the loop's motion is rhythmic/periodic — speed-ramping a visible beat sounds like a record skipping.
---

# Scroll speed-ramp (ambient loop breathes with scroll velocity)

A full-bleed ambient video loop plays continuously behind the section, and its `playbackRate` eases with scroll VELOCITY — calm at rest, rushing while the visitor scrolls fast, always relaxing back to 1.0 — the page's atmosphere responds to how hard you push it.

## Motion signature

- The loop never stops and never seeks: `autoplay muted playsinline loop` from load; scroll modulates ONLY `playbackRate` — position is untouched, so the technique is unconditionally smooth.
- Velocity sampling: `v = |scrollY - lastY| / dt` per rAF, then `rate = clamp(1 + v * 0.02, 0.75, 3.5)` — 3.5× is the perceptual ceiling before ambient motion turns to noise; Safari additionally caps silent-video rates near 4×.
- Asymmetric easing is the feel: ramp UP fast (`current += (target - current) * 0.3` per rAF, ~50ms attack) so the page answers the flick instantly; decay DOWN slow (`* 0.04`, ~1.2s release) so the rush exhales rather than snaps off.
- At rest the rate settles to exactly 1.0 — the calm state is the designed state; the ramp is seasoning.
- Optional sub-1× dip: easing the floor to 0.75 during long still pauses makes the page visibly "settle", but never pause the loop (the always-something-in-motion duty lives here).

## Asset generation spec

- **Resolution**: 1920×1080 minimum, edge-to-edge; MP4 + WebM; standard GOP is fine — this technique never seeks, so keyframe density doesn't matter (the one scroll technique where it doesn't).
- **Composition**: low-contrast, non-focal ambient motion (drifting nebula, slow smoke, particle fields, light caustics) with a quiet zone on one third for the section's UI; nothing in frame should demand the eye.
- **Continuity**: a perfect seamless loop, 8–15s, first and last frame identical; motion must be NON-PERIODIC and direction-consistent — drift, not pulse — because rate changes expose any rhythm instantly.
- **Speed-tolerance test**: the prompt must produce motion that stays attractive at 0.75× and at 3.5×; uniform drift passes, anything with a beat fails.
- **Negative prompt**: no text, no watermark, no letterboxing, no scene cut, no flicker, no rhythmic or pulsing motion, no focal subject.

## Interaction binding

```js
const v = scene.querySelector('video'); // autoplay muted playsinline loop
let lastY = scrollY, lastT = performance.now(), target = 1, current = 1;
(function tick(t) {
  const dt = Math.max(1, t - lastT);
  const vel = Math.abs(scrollY - lastY) / dt; // px per ms
  target = Math.min(3.5, Math.max(0.75, 1 + vel * 20));
  const k = target > current ? 0.3 : 0.04;    // fast attack, slow release
  current += (target - current) * k;
  v.playbackRate = current;
  lastY = scrollY; lastT = t;
  requestAnimationFrame(tick);
})(performance.now());
```

- Write `playbackRate` only when it changes by >0.01 to avoid pointless property churn.
- `muted` + `playsinline` are mandatory or autoplay is blocked and the whole technique is dead on arrival.

## UI composition rules

- All UI sits in the quiet third and stays completely static — the contrast between unmoving type and a background that surges underfoot is the entire effect.
- Foreground content must not depend on the background for contrast at ANY rate; verify legibility over the loop's busiest frame, not its average.
- Pair the ramp with at most one other velocity-reactive detail (e.g. a blur of 0–2px on the video at peak rate); two reactive layers compete, three is chaos.

## Example asset prompt template

> Seamless ambient background loop: vast slow-drifting aurora curtains in deep indigo and teal flowing steadily in one consistent direction, soft diffuse glow, no focal subject, completely non-rhythmic continuous drift that reads well at any playback speed, the left third of frame darker and quieter, loops perfectly with identical first and last frame, 1920x1080, 12 seconds, no cuts, no text, no watermark, no letterboxing, no flicker, no pulsing motion.

## When to use

- Atmospheric backgrounds on long marketing scrollers — the page feels alive without ever interrupting.
- AI / infra / "living system" briefs where responsiveness-as-texture is the brand message.
- Behind sparse hero or interstitial sections where nothing else is in motion.

## When NOT to use

- Behind body copy, docs, or data — readers scroll constantly and the surging background taxes attention.
- Stacked with scroll-scrubbed techniques in the same viewport — one scroll input driving two motion systems reads as malfunction.
- When no video provider is wired — degrade to a generated still with two layered CSS gradient/particle drifts whose `animation-duration` is swapped between 20s and 6s by the same velocity signal.

## Performance notes

- ≤8MB loop; one video element; `playbackRate` changes are free — no decode penalty, no seek, no extra paint.
- Pause the loop AND the rAF sampler when the scene leaves the viewport (`IntersectionObserver`); resume on re-entry.
- `prefers-reduced-motion`: pause the video on its poster frame and disable the sampler entirely — a speed-reactive background is exactly what that setting exists to refuse.

## Pairs with (prototype slugs)

- `recipe-ai-foundry-dark`
- `recipe-aurora-marketing`
- `style-holographic`
- `aesthetic-frutiger-dark-aero`
- `aesthetic-cyberpunk`

<!-- image: sample-1.png -->
<!-- reason: representative reference — ambient aurora loop mid-surge with static copy in the quiet third -->

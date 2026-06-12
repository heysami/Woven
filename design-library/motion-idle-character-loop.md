---
techniqueId: idle-character-loop
name: Idle character loop (the mascot is simply there)
category: ambient
subCategory: video
role: portrait
binding: none
medium: video
pairsPrototypes: [recipe-y2k-memphis-loud, recipe-neo-grotesque-portfolio, aesthetic-y2k-futurism, aesthetic-fairycore, aesthetic-cyberpunk]
notForUseWhen: The brand has no character/mascot/figure to be present (don't invent one for the technique), the character must respond to the visitor (use mouse-scrub-look or pointer-magnetic-subject), or identity consistency across the loop can't be guaranteed — a face that drifts mid-loop is worse than a static portrait.
---

# Idle character loop (the mascot is simply there)

A character, mascot, or portrait figure performs a seamless game-style idle loop — breathing, blinking, shifting weight — fully autonomous, asking nothing of the visitor; the brand has a being on the page who is simply, calmly there.

## Motion signature

- The video-game idle vocabulary, exactly: chest rises/falls on a 3–4s breath cycle, 2–4 blinks per loop at irregular spacing, one weight shift or small gesture per loop maximum. No walk cycles, no waves, no looking around — idle means content to wait.
- Seamless 6–10s loop, `autoplay muted playsinline loop`, no binding — the character was alive before the visitor scrolled there.
- Gaze direction is fixed by the prompt and never tracks: either soft-forward (presence) or angled INTO the page content (directing attention at the headline — the character becomes a layout arrow).
- Irregular blink spacing is the realism load-bearing wall: metronomic blinking reads as animatronic; the prompt asks for natural, uneven blinks.

## Asset generation spec

- **Resolution**: 1920×1080 minimum even for a portrait slot — the character gets reused at hero scale eventually; crop in CSS, not in generation.
- **Composition**: figure on one third (or the portrait slot's anchor), quiet zone opposite; if the gaze angles into the page, generate the gaze toward the quiet zone where the copy will sit.
- **Identity continuity**: same face, same outfit, same light at frame 0 and frame N — identity drift mid-loop is the disqualifying defect; loop seam on a mid-breath, eyes-open frame, never mid-blink.
- **Duration**: 6–10s; under 5s the breath cycle count gives the loop away.
- **Negative prompt**: no text, no watermark, no letterboxing, no camera move, no scene cut, no lip movement, no walking, no background motion, no identity change.

## Interaction binding

```js
const v = scene.querySelector('video');
// No input binding — lifecycle only.
new IntersectionObserver(([e]) => {
  e.isIntersecting ? v.play() : v.pause();
}, { threshold: 0.25 }).observe(scene);
```

- `muted playsinline loop preload="metadata"` (`auto` only when the slot is above the fold).
- `poster` = an eyes-open mid-breath frame, so the pre-play state is a good portrait, not a caught blink.
- Compositing fallback: when the character must sit over the page background (not in a video rectangle), use the transparent raster-sequence form — 36–60 alpha-PNG/WebP frames at 12fps flipped in a canvas/`<img>` swap; same idle vocabulary, true transparency.

## UI composition rules

- Copy in the quiet zone; if the character's gaze angles toward it, place the headline exactly on the gaze line — visitors verifiably follow a figure's gaze before reading.
- The character never overlaps interactive UI — a breathing figure behind a button makes the button feel unstable.
- One character per viewport. Two idle loops in view split presence into a waiting room.

## Example asset prompt template

> Character idle loop: a round teal robot mascot standing on the right third of frame, breathing gently with a soft 3 second chest rise and fall, blinking twice at natural uneven intervals, one small weight shift to the left mid-loop, gaze angled softly toward the left side of frame, fixed camera, locked tripod, seamless pale studio backdrop, large empty negative space on the left third, constant light, seamless loop where the final frame matches the first, 1920x1080, 8 seconds, no text, no watermark, no camera movement, no lip movement, no walking, no background motion.

## When to use

- Character-led brands — mascot products, AI assistants with a face, games, kids' education, fashion lookbook figures.
- Portrait slots (founder, artist, model) that should hold presence longer than a still.
- Briefs that say "the brand should feel like someone, not something."

## When NOT to use

- Brands with no figure — an invented mascot to justify the technique is backwards.
- When the storyboard wants acknowledgement of the visitor — idle is defined by NOT reacting; reach for mouse-scrub-look (gaze) or pointer-magnetic-subject (lean).
- When no video provider is wired — degrade to the transparent raster-sequence form above (it composites better anyway), or at minimum a 2-frame breath (two stills, same seed, crossfaded on a 4s cycle).

## Performance notes

- ≤5MB for the video form; the raster-sequence form runs 3–6MB of alpha frames — preload fully before first paint of the character, poster meanwhile.
- Pause when off-screen; a paused idle on re-entry resumes invisibly (every frame is a valid portrait).
- `prefers-reduced-motion`: the eyes-open poster frame — the character becomes a well-shot still, losing nothing structural.

## Pairs with (prototype slugs)

- `recipe-y2k-memphis-loud`
- `recipe-neo-grotesque-portfolio`
- `aesthetic-y2k-futurism`
- `aesthetic-fairycore`
- `aesthetic-cyberpunk`

<!-- image: sample-1.png -->
<!-- reason: representative reference — mascot mid-breath on the right third, gaze angled at the headline in the quiet zone -->

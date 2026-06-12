---
techniqueId: quiet-zone-headline
name: Quiet-zone headline (the asset makes room for the type)
category: composition
subCategory: video
role: hero
binding: none
medium: video
pairsPrototypes: [recipe-aurora-marketing, recipe-warm-restraint, recipe-restrained-ai-marketing, aesthetic-solarpunk, style-bold-display]
notForUseWhen: The asset is texture-only with no subject (uniform particle field, gradient wash) — there is no busy region to be quiet AGAINST, so just set type anywhere; or the headline is short enough (≤2 words) to survive on a scrim without composition help.
images:
  - src: motion-quiet-zone-headline-ui.png
    reason: Motion technique UI mockup.
  - src: motion-quiet-zone-headline-isolated.png
    reason: Signature technique, isolated.
---

# Quiet-zone headline (the asset makes room for the type)

The foundational composition contract of every motion scene: the asset is GENERATED with a deliberate low-detail, controlled-luminance region — a light sky, a fog bank, a blank wall — sized and positioned for the headline before a single frame exists, so type never fights the world it sits on (the motionsites aethera-hero pattern).

## Motion signature

- This technique is the rule the others inherit: subject mass anchored to one side, quiet zone opposite, UI in the quiet zone. It has no binding of its own (`binding: none`) — it composes WITH whatever choreography the scene uses.
- The quiet zone must stay quiet IN MOTION: ambient drift inside it (fog, cloud) is fine; subjects, highlights, or hard edges entering it at any frame is a QA failure.
- Loop motion in the zone should be the slowest thing in frame — the type reads as still because its ground barely moves.

## Asset generation spec

- **Resolution**: 1920×1080 minimum, full-bleed edge-to-edge.
- **Zone sizing**: the zone is the headline's layout box plus 10% padding, in frame fractions — a 5-word display headline at 7vw needs roughly 45% width × 30% height. Write the zone into the prompt as geography, not as an instruction ("a vast pale fog bank fills the upper-left half of frame"), because models render places, not layout directives.
- **Luminance is part of the spec**: dark type → prompt a LIGHT zone ("pale overcast sky"); light type → prompt a DARK zone ("deep shadowed wall"). Decide text color before generating, not after.
- **Negative prompt**: no text, no watermark, no letterboxing, no border, no subject in the upper-left (mirror per chosen side), no lens flare in the quiet zone.

## Interaction binding

```js
// QA recipe — luminance-check the zone ACROSS frames before the asset ships.
async function qaQuietZone(video, zone /* {x,y,w,h} fractions */, textLum /* 0..1 */) {
  const c = Object.assign(document.createElement('canvas'), { width: 192, height: 108 });
  const ctx = c.getContext('2d'); const lums = [];
  for (let t = 0; t < video.duration; t += video.duration / 12) {   // 12 samples
    video.currentTime = t; await new Promise(r => video.onseeked = r);
    ctx.drawImage(video, 0, 0, 192, 108);
    const d = ctx.getImageData(zone.x * 192, zone.y * 108, zone.w * 192, zone.h * 108).data;
    let s = 0; for (let p = 0; p < d.length; p += 4) s += 0.2126 * d[p] + 0.7152 * d[p+1] + 0.0722 * d[p+2];
    lums.push(s / (d.length / 4) / 255);
  }
  const worst = textLum > 0.5 ? Math.max(...lums) : Math.min(...lums);
  return contrastRatio(textLum, worst) >= 4.5;   // WCAG against the WORST frame
}
```

- Enforce contrast ≥4.5:1 against the worst sampled frame, not the average; a single bright gust behind dark type is the failure users notice.
- Failing assets get ONE retry with the zone description strengthened; a second failure falls back to a max-25% scrim gradient — never more, or the composition rule has failed and the asset should be regenerated.

## UI composition rules

- Subject one side → ALL UI in the quiet zone opposite: headline top of zone, supporting line beneath at 0.4–0.6× headline size, CTA at the zone's lower edge. Nothing of the UI touches the subject's half.
- Type aligns toward the subject (left zone → left-aligned, ragged-right toward the subject) so the composition reads as one diagonal.
- Never letterbox or pillarbox to create room — room is generated, not cropped.

## Example asset prompt template

> Cinematic full-bleed hero: a lone climber on a granite ridge anchored to the lower-right third of frame, a vast pale fog bank filling the upper-left half of frame as calm low-detail negative space with even light luminance for a dark headline, slow drifting fog as the only motion in that region, fixed camera, golden side light on the climber, edge-to-edge composition, photoreal, 1920x1080, 8 second seamless loop, no text, no watermark, no letterboxing, no subject in the upper-left, no lens flare.

## When to use

- Every hero scene with a headline over generated media — this is the default, not an option.
- As the composition layer under any choreography technique (stepper, crossfade, background-swap).
- Briefs where type and image must read as designed together, not type slapped on stock.

## When NOT to use

- Pure-texture grounds where everything is already quiet — skip the ceremony.
- Headlines inside matte bars or masks (letterbox-stage, video-text-mask own their own type placement).
- When no video provider is wired — the rule applies identically to a generated raster; run the same QA on the single frame.

## Performance notes

- The QA canvas runs at 192×108 — sampling 12 frames costs <50ms total and runs once at build time, never at runtime.
- `muted playsinline` autoplay for the shipped loop; poster = the frame with median zone luminance.
- `prefers-reduced-motion`: hold the poster frame — the zone passed QA on every frame, so any frame carries the type.

## Pairs with (prototype slugs)

- `recipe-aurora-marketing`
- `recipe-warm-restraint`
- `recipe-restrained-ai-marketing`
- `aesthetic-solarpunk`
- `style-bold-display`

<!-- image: sample-1.png -->
<!-- reason: representative reference — headline sitting in a generated fog-bank quiet zone opposite the subject -->

---
techniqueId: video-text-mask
name: Video text mask (the world lives inside the glyphs)
category: composition
subCategory: video
role: hero
binding: none
medium: video
pairsPrototypes: [style-oversized-neo-grotesque, style-bold-display, recipe-neo-grotesque-portfolio, recipe-brutalist-web, aesthetic-vaporwave]
notForUseWhen: The headline is long (>3 words), set in a light weight, or in a typeface with thin strokes — video through hairlines reads as noise; the technique needs ≥800-weight glyphs at ≥18vw. Also wrong when the video's CONTENT matters — viewers must recognise the subject, and the mask destroys recognisability.
---

# Video text mask (the world lives inside the glyphs)

A full-bleed video is visible ONLY through giant headline glyphs — an SVG text mask (or `mix-blend-mode` trick) over a solid page-ground — so the type becomes a window and the motion becomes texture; the video is generated FOR the glyphs: high-contrast movement, rich texture, no subject that needs to be seen whole.

## Motion signature

- `binding: none` — the scene works held; choreography techniques may swap the video behind a constant mask (pair with background-swap-fixed-ui) or wipe the whole scene.
- The motion inside the glyphs should be directional and continuous (lava creep, surf rolling, crowd flow, ink billowing) at a pace where any 2-second window shows visible travel — static texture in a mask is just a patterned fill.
- The page ground around the glyphs is SOLID and matches the page background exactly; the effect's power is that nothing exists outside the letters.
- A 6–10s seamless loop; the glyphs never animate position — the type is the still thing, the world inside it moves.

## Asset generation spec

- **Resolution**: 1920×1080 minimum — glyphs at 18–30vw sample the full frame; low-res texture shows immediately inside big counters.
- **Composition**: NO subject, no focal point, no composition in the photographic sense — prompt edge-to-edge uniform-density texture with high internal contrast (dark/light interplay ≥50% luminance swing) so strokes read against the solid ground at every point. A centered subject would be amputated by the glyph cuts.
- **Texture scale**: features should be 5–15% of frame height — finer disappears inside strokes, coarser makes single glyphs read as flat color.
- **Negative prompt**: no text, no watermark, no letterboxing, no border, no central subject, no faces, no flat low-contrast regions, no still frames.

## Interaction binding

```js
// SVG mask: white glyphs reveal, black conceals. The video never leaves the compositor.
// <svg width="0" height="0"><defs><mask id="glyphs">
//   <rect width="100%" height="100%" fill="black"/>
//   <text x="50%" y="55%" text-anchor="middle" fill="white"
//         font-size="24vw" font-weight="900">FLUX</text>
// </mask></defs></svg>
const v = scene.querySelector('video');       // muted + playsinline + loop
v.style.cssText = 'mask: url(#glyphs); -webkit-mask: url(#glyphs);';
// Fallback for engines with broken SVG-mask-on-video:
if (!CSS.supports('mask', 'url(#m)'))
  scene.classList.add('blend-mode-fallback');  // white text + mix-blend-mode: screen over video
```

- The blend-mode fallback (solid layer + `mix-blend-mode`) only works on pure-black or pure-white grounds; the SVG mask is the primary path because it works on ANY page color.
- `muted playsinline loop autoplay`; poster = a representative texture frame so the pre-play state already shows filled glyphs.

## UI composition rules

- The masked headline IS the hero — center it optically (55% vertical, not 50%) and give it the full viewport width minus 8% side margins.
- Supporting UI (kicker above, one-line dek + CTA below) sits OUTSIDE the glyphs in solid page-ground territory, set small (≤1.2vw) so nothing competes with the window.
- One masked word or two short words maximum per scene; the technique spends its entire budget on a single utterance.

## Example asset prompt template

> Abstract texture loop for a text-mask hero: molten gold and black ink folding and flowing edge-to-edge across the entire frame, uniform density with no central subject and no focal point, strong internal contrast between bright metal and deep black, texture features around one tenth of frame height, slow continuous directional flow looping seamlessly with last frame matching first, fixed camera, 1920x1080, 8 seconds, no text, no watermark, no letterboxing, no faces, no flat low-contrast regions.

## When to use

- One-word manifesto heroes: studio names, product names, campaign verbs.
- Brutalist and oversized-type directions where the typography is the design.
- When the brief says "the name should feel alive" without any product to show.

## When NOT to use

- Information-bearing video (demos, footage of the actual product) — the mask destroys it.
- Long headlines, light weights, small sizes — see notForUseWhen; below ~12vw the windows close.
- When no video provider is wired — degrade to the same SVG mask over a generated raster texture with a 30s CSS pan (`background-position` drift via transform on an oversized still, 1.15× crop).

## Performance notes

- One video element behind one mask — cheap; but the mask forces compositing of the full video even though only glyph pixels show, so keep the clip ≤8MB and 1080p (4K buys nothing through 24vw strokes).
- Pause the video when the scene leaves the viewport (`IntersectionObserver`, threshold 0.1).
- `prefers-reduced-motion`: pause on the poster frame — textured static glyphs remain a strong composition; never swap to plain solid type, which would erase the design.

## Pairs with (prototype slugs)

- `style-oversized-neo-grotesque`
- `style-bold-display`
- `recipe-neo-grotesque-portfolio`
- `recipe-brutalist-web`
- `aesthetic-vaporwave`

<!-- image: sample-1.png -->
<!-- reason: representative reference — a single 900-weight word filled with flowing molten texture on a solid ground -->

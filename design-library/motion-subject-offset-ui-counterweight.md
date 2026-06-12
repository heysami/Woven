---
techniqueId: subject-offset-ui-counterweight
name: Subject offset, UI counterweight (thirds by generation)
category: composition
subCategory: raster
role: hero
binding: none
medium: raster
pairsPrototypes: [recipe-editorial-magazine, recipe-neo-grotesque-portfolio, recipe-bento-marketing, style-oversized-neo-grotesque, aesthetic-dark-academia]
notForUseWhen: The subject is inherently centered and symmetric (a mandala, a head-on product orthographic) — forcing it to a third fights the asset; use letterbox-stage or center it and push UI to the matte. Also wrong for scenes with no UI at all — a counterweight with nothing to counter is just an off-center picture.
images:
  - src: motion-subject-offset-ui-counterweight-ui.png
    reason: Motion technique UI mockup.
  - src: motion-subject-offset-ui-counterweight-isolated.png
    reason: Signature technique, isolated.
---

# Subject offset, UI counterweight (thirds by generation)

The subject is anchored HARD to one vertical third at generation time and the UI block occupies the opposite third as a visual counterweight — image mass and type mass balance across the frame like a scale, and the storyboard decides the side per scene, alternating for rhythm.

## Motion signature

- `binding: none` — this is a composition contract for stills AND videos; it layers under any choreography.
- For video assets the offset must hold on EVERY frame: the subject may breathe, turn, or drift within its third, but its center of mass never crosses the frame's midline.
- Across a multi-scene piece, the storyboard alternates sides (R, L, R, L…) — consecutive same-side scenes read as a template; alternation reads as art direction. Break the alternation at most once per piece, deliberately, on the climax scene.

## Asset generation spec

- **Resolution**: 1920×1080 minimum, full-bleed edge-to-edge; rasters destined for slow-zoom drift should be 2560×1440 so the 1.05× scale never softens.
- **Anchor language**: prompt the position as physical fact — "anchored on the right third of frame", "occupying the left 30% of the composition", "facing into the empty space". Models obey nouns-in-places far better than layout words like "rule of thirds".
- **Gaze/orientation**: the subject faces INTO the empty third (a face looking, a vehicle pointing, a building's entrance opening that way) — facing off-frame makes the counterweight side feel abandoned.
- **The empty third is generated empty**: low detail, controlled luminance (see quiet-zone-headline for the QA recipe — it applies verbatim here).
- **Negative prompt**: no text, no watermark, no letterboxing, no border, no centered composition, no subject crossing the frame midline.

## Interaction binding

```js
// Storyboard contract: each scene declares its side; the build places UI opposite.
const scenes = [
  { asset: 's1.png', subjectSide: 'right' },   // → UI left
  { asset: 's2.mp4', subjectSide: 'left'  },   // → UI right
  { asset: 's3.png', subjectSide: 'right' },   // alternate for rhythm
];
scenes.forEach(s => {
  s.uiSide = s.subjectSide === 'right' ? 'left' : 'right';
  sceneEl(s).classList.add(`ui-${s.uiSide}`);  // grid-column placement + text-align
});
```

- The `subjectSide` field travels from storyboard → generation prompt → layout class; one source of truth, three consumers. A side mismatch anywhere in that chain is the technique failing.
- Video assets in the sequence run `muted playsinline` ambient loops; stills get a 20s 1.0 → 1.05 scale drift so no scene is dead.

## UI composition rules

- The UI block (kicker, headline, body, CTA) is one left- or right-aligned stack filling 25–35% of frame width in the empty third, vertically centered or on the lower third line — never full-width, never centered.
- Type weight balances image weight: a heavy, dark subject earns a heavier headline (700+, larger size); a wispy subject earns a lighter setting. The scale should FEEL level.
- Keep 5% frame-width clear between the UI block's inner edge and the subject's bounding box — the gutter is where the balance is visible.

## Example asset prompt template

> Editorial hero still: a marble bust in dramatic chiaroscuro anchored hard on the right third of frame, facing left into a vast empty dark-grey studio wall that fills the left two-thirds as smooth low-detail negative space for a light headline, single warm key light from the right, edge-to-edge composition, photoreal, 2560x1440, no text, no watermark, no letterboxing, no centered composition, no objects in the left two-thirds.

## When to use

- Editorial and portfolio heroes where type is a first-class design element, not a caption.
- Multi-scene pieces that need a cheap, reliable rhythm engine — alternate the side, get pacing for free.
- Both stills and videos; this is the default composition when no fancier device (mask, letterbox) is called for.

## When NOT to use

- Symmetric or centered subjects — see notForUseWhen; don't fight the asset.
- Mobile-first pieces at portrait ratios — thirds collapse at 9:16; restack to subject-upper / UI-lower and re-generate portrait crops.
- When no video provider is wired — nothing degrades; this is already the raster technique. Stills with the scale drift ARE the full implementation.

## Performance notes

- Rasters as AVIF/WebP ≤400KB at 2560w with a 1920w fallback; the drift is one CSS `transform` animation, zero script.
- Video variants ≤8MB, poster from the median frame.
- `prefers-reduced-motion`: kill the scale drift, pause loops on poster — the composition carries the scene at full stop, which is exactly the point of doing it by generation.

## Pairs with (prototype slugs)

- `recipe-editorial-magazine`
- `recipe-neo-grotesque-portfolio`
- `recipe-bento-marketing`
- `style-oversized-neo-grotesque`
- `aesthetic-dark-academia`

<!-- image: sample-1.png -->
<!-- reason: representative reference — subject hard on the right third with the type stack counterweighting the left -->

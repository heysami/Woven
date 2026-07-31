---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-jp-variety-telop-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-jp-variety-telop-isolated.png
    reason: Signature motif, isolated.
---
# Japanese variety-show telop (aesthetic)

**Tag:** broadcast caption maximalism

**Canonical references:**
- The telop (television opaque projector) caption craft of Japanese variety TV - *Gaki no Tsukai*, *London Hearts*, *Sekai no Hate Made ItteQ!*
- Golden-age burst-caption reaction graphics: うわっ! マジかよ! キターーッ!! as full-screen typography events
- Japanese YouTube thumbnail culture - the direct inheritor of telop grammar
- TV Asahi / NTV lower-third and ranking-corner graphics packages

## Cultural identity

The typography layer of Japanese variety television, promoted to a whole design language. Every exclamation is an event: thick katakana interjections wear three or four concentric stroke outlines (white ring, black ring, color ring, drop shadow), each word rotates off the baseline a few degrees in its own direction, burst bubbles and speed-line fields explode behind punchlines, and every emotion gets its own hue - yellow for surprise, pink for excitement, cyan for laughter, purple for bafflement, gray for the deadpan mutter set small and tilted. The register is loud but LEGIBLE: telop craft exists so a viewer catching three seconds mid-broadcast still gets the joke.

Against `aesthetic-jp-recruit-pop` this is the off-duty opposite: recruit-pop is a disciplined white-field token system where accents are structural; telop assigns a new color per word and a new angle per line - the anarchy is the system. Against `aesthetic-kawaii-brutalism` (chunky cute-brutal blocks and flat stickers) telop is specifically BROADCAST craft: multi-stroke bevels, speed lines, and reaction pacing, not brutalist framing.

## Palette anchor

Full-saturation signal hues, each bound to an emotion, on white or pale ground panels:
- Surprise yellow `oklch(87% 0.18 95)`
- Excitement pink `oklch(67% 0.25 355)`
- Laughter cyan `oklch(80% 0.15 220)`
- Burst lime `oklch(85% 0.25 130)`
- Fire orange `oklch(75% 0.19 55)`
- Wonder purple `oklch(65% 0.20 300)`
- Mutter gray `oklch(72% 0 0)`

Red-white-black reserved for the outline stack and panel frames. Five+ hues on screen is correct here.

## Decoration motifs

- Multi-stroke katakana display: fill + white ring + black ring + colored ring + hard shadow
- Rotated baselines: every headline tilts +6 to -12 degrees, no two the same
- Burst bubbles (spiky speech balloons) and radial speed-line fields behind key words
- Halftone dot fields and diagonal stripe wedges as panel textures
- Holographic foil fill inside the biggest interjections
- Octagonal / notched panel frames on buttons and cards, comic-sticker badges
- Ranking-corner furniture: numbered crowns, view counters, hashtag chips

**Raster required:** the holo-foil fill and the biggest multi-stroke display lockups (typography `telop-burst-lockup`). Two-ring outlines survive as stacked text-shadow; the foil sheen and hand-beveled hero words do not.

## Voice register

Pure interjection: うわっ! マジかよ! ウケるw ええ〜!? Reaction-first, body text almost absent - the vocabulary is exclamations, net slang (神, 草, ヤバイ, www), and counters (256.7万 views). Everything ends in ! or !? or trails off in ぼそっ… Never explanatory, never formal.

## Failure mode

One uniform outline color on every word = a subtitle file, not telop; the per-word color-emotion mapping is the genre. Second tell: straight baselines throughout - if nothing tilts, it is a poster, not a broadcast. Third tell: tasteful two-hue restraint; a telop screen with only two colors reads as unfinished. Fourth tell: illegibility - real telop craft never sacrifices the three-second read; if the outlines swallow the letterform, it is cosplay.

## Best for

- Video platforms, clip-compilation and ranking UIs, comedy media
- Fan communities and reaction-driven social features
- Campaign microsites for snacks, game shows, gacha events
- Any brief asking for "Japanese TV energy" or thumbnail-grade loudness

## Pairs well with

- Shells: `shell-hero-stack`, `shell-bento-grid`, `shell-mobile-app`
- Styles: `style-bold-display`, `style-ransom-glyph-mix`, `style-outline-marquee`

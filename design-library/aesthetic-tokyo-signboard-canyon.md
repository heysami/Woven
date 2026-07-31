---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-tokyo-signboard-canyon-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-tokyo-signboard-canyon-isolated.png
    reason: Signature motif, isolated.
---
# Tokyo signboard canyon (aesthetic)

**Tag:** rain-slicked mixed-sign vernacular

**Canonical references:**
- The stacked building-face sign directories of Shinjuku, Shibuya, and Dotonbori - one signboard per floor, 6F down to B1
- Omoide Yokocho and Golden Gai alley signage - lantern, brush, and neon crowded into two meters of frontage
- Japanese kanban craft: channel-letter neon, backlit acrylic panels, brush-lettered noren and chochin lanterns
- Night street photography of wet Tokyo asphalt doubling every sign in reflection

## Cultural identity

The look of a Tokyo nightlife building read from the street: a vertical canyon of stacked signboards where EVERY ROW IS A DIFFERENT REAL SIGN MEDIUM. The rooftop bar announces itself in red neon script; the shisha lounge below in purple tube caps; the jazz club in clean white channel letters; the yakiniku floor in brush-lettered vermilion with a paper lantern; the curry joint in amber backlit acrylic; the karaoke basement in blue neon with a microphone. Floor codes (6F, 5F... B1) rail the left edge, an 営業中 (open) lamp glows, and the whole stack reflects in wet asphalt below. The register is DOCUMENTARY and warm - izakaya hospitality, not dystopia; each sign is a different proprietor's taste, accumulated over decades, not one art director's system.

Differentiation: `aesthetic-cyberpunk` runs a single sci-fi register - teal/magenta holograms, dystopian mood, invented tech signage all speaking one visual language. Signboard canyon is the real city it borrowed: mixed authorship is the point, the palette is lantern-warm as often as neon-cold, and nothing is fictional - the medium diversity per row (neon vs acrylic vs brush vs LED) is the signature no sci-fi treatment reproduces.

## Palette anchor

Black wet-night ground with per-sign signal hues:
- Wet asphalt `oklch(12% 0.01 270)`
- Backlit panel white `oklch(96% 0 0)`
- Neon red `oklch(60% 0.25 27)`
- Lantern vermilion `oklch(58% 0.19 35)`
- Sign amber `oklch(83% 0.14 85)`
- Neon purple `oklch(62% 0.22 310)`
- Vending cool blue `oklch(70% 0.13 250)`

Each hue belongs to ONE sign row; the mix happens across the stack, never inside one sign.

## Decoration motifs

- Stacked full-width sign rows, each in a distinct medium: neon script, channel letters, brush kanji, backlit acrylic, LED gothic
- Floor-code rail (6F / 5F / ... / B1) as the structural index
- Red paper lantern with brush lettering; 営業中 open-lamp badges with hours
- Wet-asphalt reflection band doubling the lowest signs
- Kana furigana eyebrow over each sign's Latin or kanji main line
- Thin red hairline frames on dark panels; stamp seals tucked into sign corners

**Raster required:** the rain-slicked alley photography and the lit-sign renders (photo `wet-night-alley`, sign faces `neon-and-acrylic-sign-pack`). CSS glow approximates neon poorly; the asphalt reflection and lantern paper need pixels.

## Voice register

The building speaks as many voices: each row names its business plainly (JAZZ, SPICE CURRY, 炙り家, KARAOKE) with hours and floor. Wayfinding copy stays concise and warm - "サインが導く、今夜の一軒。" (the signs lead you to tonight's spot). Never one unified brand voice - the charm is the chorus.

## Failure mode

Setting every row in the same typeface with different colors = a themed menu, not a canyon; the MEDIUM must change per row (neon vs brush vs acrylic), not just the hue. Second tell: teal-and-magenta grading over everything - that is cyberpunk cosplay; this register keeps lantern warmth beside the neon. Third tell: clean dry backgrounds; without the wet reflection the night reads as a mockup. Fourth tell: fictional tech signage (holograms, glitch) - every sign here must be buildable by a real Tokyo sign shop.

## Best for

- Restaurant/bar directories, nightlife guides, izakaya and food-hall brands
- Music venues and multi-tenant building sites
- City guides and travel features wanting warmth, not dystopia
- Any list UI that benefits from each row having its own voice

## Pairs well with

- Shells: `shell-hero-stack`, `shell-mobile-app`, `shell-top-bar-canvas`
- Styles: `style-dense-mono-dark`, `style-bold-display`, `style-restrained-hairline`

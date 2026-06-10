---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-frutiger-chromecore-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-frutiger-chromecore-isolated.png
    reason: Signature motif, isolated.
---
# Frutiger Chromecore (aesthetic)

**Tag:** Chromecore (Motorola Razr V3, iPod nano 1st gen, Sony VAIO TX, Canon IXUS Digital ELPH, Sony Ericsson T610)

**Canonical references:**
- Motorola Razr V3 (2004) — bead-blast aluminium clamshell, engraved keypad, icy LCD
- iPod nano 1st gen (2005) — anodized stainless capsule, monochrome LCD, click-wheel precision
- Sony VAIO TX (2005) — magnesium chassis, hairline brushed grain, glacial cool palette
- Canon IXUS Digital ELPH / SD500 (2005) — pocket-cam capsule, model-number-as-decoration
- Sony Ericsson T610 (2003) — joystick + soft-keys, engineered ALL-CAPS micro labels

## Cultural identity

Chromecore is the **2003–2007 mid-decade hardware-luxury** moment — the brief window after the bubble pop and before the iPhone, when consumer electronics borrowed the language of precision tooling: bead-blasted aluminium, anodized steel, milled-edge capsule shapes, monochrome LCDs with icy backlights. It's the look of objects you wanted to hold because the surface itself was the feature. Adjacent to but distinct from Frutiger Aero — Aero is organic / wet / sky-and-bubbles; Chromecore is **industrial, cool, near-monochrome, machined**. Adjacent to Y2K Futurism but stripped of its candy hues — where Y2K celebrated translucent plastic and rainbow iridescence, Chromecore celebrates brushed steel and a single icy-blue accent.

The cultural register is **precision-machined techno-optimism**: model numbers as ornament, technical specs as poetry (`2.0" TFT · 176×220 · Li-Ion 740 mAh`), wordmarks engraved rather than printed. Less playful than Y2K, more clinical than Aero, warmer than today's restrained-hairline — there is craft and pride in the chassis itself.

## Palette anchor

Cool grayscale only, deliberately banded to read as machined steel rather than soft gradient.

- `#0E1418` near-black studio backdrop
- `#6E767C` mid-tone brushed steel
- `#B8BFC4` light brushed steel
- `#F4F6F7` highlight chrome
- `#A8C8E0` single icy-blue LCD glow (the ONLY chroma — used for active states, never as fill)
- optional `#B8D4CC` pale aqua-mint status LED

No warm metals (gold, copper, rose), no rainbow iridescence, no saturated hue, no candy Y2K pink/lime/cyan.

## Decoration motifs

- Brushed-metal grain (fine 1px directional hairlines)
- Bead-blast engraved wordmarks on a top bezel
- Capsule / pill silhouettes (hardware chassis, buttons, speaker grilles)
- Multi-dot or slot speaker grilles
- Monochrome LCD wells with subtle scanline overlay
- Engraved/milled groove lines (dark-over-light hairline pair)
- Model numbers as ornament (`V3 · TX-2P · SD500`)
- Hard bevels and chamfered edges — no blurred drop-shadows
- One icy-blue glow on active text or LED only

## Voice register

Terse engineered labels in ALL-CAPS micro: `MENU · OK · SELECT · MP3 · PLAY · 3.2 MP`. Technical units treated as feature copy: `2.0" TFT · 176×220 · Li-Ion 740 mAh`. Model numbers worn as jewellery. Sentences are short, declarative, dry — the tone of a spec sheet, not a manifesto.

## Failure mode

Rainbow holographic foil + glitter sparkles + candy-Y2K pink/cyan/lime + Orbitron 12px + airbrushed dolphin = AI Y2K cosplay. That's Holographic + Y2K Futurism, not Chromecore. Chromecore is **industrial, COOL, near-monochrome** — the only chroma is a single icy-blue LCD glow. If the page has more than two hues, or any warm metal, or any oil-slick iridescence, or any bubble/water organic Aero motif, you've drifted into the wrong subgenre. The other tell: soft blurred drop-shadows. Chromecore uses hard bevels (inset highlight + inset lowlight), never the modern blurred shadow.

## Best for

- Hardware-flavoured product pages (audio gear, cameras, peripherals)
- Retro-tech audio / video players, music libraries
- Camera / photo tools where the chassis metaphor sells precision
- Settings, control panels, "pro" surfaces for power users
- Anything that wants to project precision-machined techno-optimism without slipping into Aero's organic warmth or Y2K's candy palette

## Pairs well with

- Shells: `shell-mobile-app`, `shell-centered-column`, `shell-hero-stack`, `shell-bento-grid`, `shell-two-column-app`
- Styles: `style-skeuomorphism` (hardware chassis treatment), `style-dense-mono-dark` (LCD-well content surfaces), `style-restrained-hairline` (engraved-line discipline), `style-flat-design` (only if explicitly contrasted against the chrome chassis)

> **Raster note:** chrome / bead-blast / brushed-steel finishes require photographic raster — Razr V3, iPod nano, VAIO product renders, capsule-shaped hardware silhouettes. CSS chrome reads as Y2K Futurism instead. Follow the raster-requirements decision tree in the main playbook before drawing.

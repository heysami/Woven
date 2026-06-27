---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-pixel-nes-mario-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-pixel-nes-mario-isolated.png
    reason: Signature motif, isolated.
---
# Pixel NES / Famicom Mario era (aesthetic)

**Tag:** `aesthetic`

**Canonical references:**
- Super Mario Bros. (1985) - the codifier; sky-blue backdrop, ?-blocks, pipe-green / brick-red palette discipline
- Mega Man 2 (1988) - sharper sprite outlines, sub-palette swaps per stage, peak NES color craft
- Castlevania III (1989) - pushed the PPU; gothic palettes within the same 4-per-sprite rule
- Kid Icarus (1986) - vertical-scroll variant; lavender / pastel sub-palette range
- Super Mario Bros. 3 (1988) - late-NES maturity; tile-art finesse and HUD vocabulary

## Cultural identity

The Nintendo Entertainment System (Famicom in Japan) defined what "video game" looked like for a generation that grew up between 1985 and 1991. The aesthetic is shaped by hardware constraints - a Picture Processing Unit that drew 8×8 tiles, allowed only 4 colors per 16×16 sprite block (one shared transparent), and rendered to a 256×240 raster. The constraints became the look: chunky integer-scaled pixels, fearless primary color, and an HUD vocabulary (SCORE / TIME / 1-UP / WORLD 1-1) that crossed every genre.

This is a *console-cartridge* aesthetic, not an arcade one (that's Space Invaders / Pac-Man), and not a handheld one (that's Game Boy 2-bit mono). It belongs to the grey-rectangle controller, the CRT scanline, the cardboard box with the matte black border. It signals: childhood, score-chasing, the era before save states.

## Palette anchor

Pick ONE 4-color sub-palette per 16×16 region - never blend across regions. Era-defining anchors:

- Sky blue `#6B8CFF` (NES $22) - the Mario overworld signature
- Mario red `#E52521` / brick brown `#B53120`
- Pipe green `#00A800`
- Coin gold `#FBD000` - for highlights, never gradients
- NES greys `#7C7C7C` / `#BCBCBC` / `#FCFCFC` - castle stone 3-step ramp, no in-betweens

Underground swaps backdrop to `#000000`; castle stages use `#3F3F7F` stone on void. The discipline is what reads as NES - not the specific hues.

## Decoration motifs

- ?-block, brick, pipe, cloud, coin, 1-UP mushroom, fire flower icons
- HUD strip with monospace caps: SCORE / TIME / WORLD / LIVES
- Hard 1px black drop-shadow on all text (zero blur)
- Selective 2px black sprite outlines (Mega Man style) or no outlines (Mario style) - pick one and commit
- Nintendo dialog box: 4px white outer border + 2px black inner
- Everything snapped to an 8px grid; 16×16 attribute blocks visible if you squint

## Voice register

ALL CAPS, terse, score-screen cadence. "PRESS START", "1-UP", "WORLD 1-1", "TIME 400", "GAME OVER". No sentences. Punctuation limited to `!` and `×`. Microcopy reads like a status bar, not a paragraph.

## Failure mode

Smooth-edged "pixel" sprites rendered at fractional zoom (sub-pixel blur), Inter body text leaking into the HUD, rounded corners on a `#6B8CFF` background - AI NES cosplay. Or applying the NES 4-color rule to a mono-green brief and drifting into Game Boy territory. Or using more than 4 colors in a single 16×16 region - instantly reads as "16-bit or later," not NES.

## Best for

Nostalgia games and retro-jams, 80s / early-90s pop-culture brands, score-driven micro-apps, chiptune artist sites, indie game studio landing pages, anything where the audience grew up holding a grey rectangular controller. Also fits gamified habit / streak apps that want a console-childhood cue.

## Pairs well with

- Shells: `shell-mobile-app` (NES screen proportions translate cleanly), `shell-bento-grid` (HUD-block reading), `shell-hero-stack` (title-screen cadence), `shell-terminal-frame` (CRT framing), `shell-centered-column` (single-stage focus)
- Styles: `style-pixel-bitmap` (the canonical pairing - bitmap raster, integer scaling, stepped motion)

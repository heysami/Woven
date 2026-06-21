---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-8-bit-generic-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-8-bit-generic-isolated.png
    reason: Signature motif, isolated.
---
# 8-bit pixel generic (aesthetic)

**Tag:** `aesthetic-8-bit-generic`

**Canonical references:**
- Stardew Valley site - modern-cozy pixel commerce done with honest sprites and chunky chrome
- NES.css - the canonical web translation of NES dialog boxes and 9-slice borders
- itch.io game pages - the contemporary substrate where indie pixel branding actually lives
- Pokemon Red/Blue menus - terse ALL-CAPS labels, cursor selection, status readouts as identity
- Lospec palettes - the community-curated indexed swatches the look is built from

## Cultural identity

The aesthetic of consoles that couldn't lie about their pixels - NES (1983), Game Boy (1989), SNES (1990), PICO-8 today - extended into a 2010s indie revival (Stardew, Celeste, Undertale) and the itch.io/Lospec community that codified it as a craft. This is not "retro nostalgia"; it is a commitment to indexed palettes, integer-scaled grids, and hardware constraints as honest material. The cultural beat: hobbyist, communal, lovingly slow, suspicious of slickness. Pixels are political - they say "a human placed each one." When done right it reads as warmth and authorship; when faked it reads as a stock-asset costume.

The era never had blur, never had antialiasing, never had a 250ms ease-out. Anything smooth is a tell.

## Palette anchor

Pick ONE indexed family and stay inside it - mixing families is the fastest way to look like a pixel-sticker pack, not an artifact.

- **Game Boy DMG mono:** `#0f380f` ink, `#306230` shade, `#8bac0f` mid, `#9bbc0f` paper - 4 swatches, no exceptions
- **NES system:** `#1c1c1c` ink, `#fcfcfc` paper, `#f83800` ketchup-red, `#0078f8` cobalt-blue, `#00a800` confirm-green, `#f8b800` coin-yellow
- **PICO-8 dusk:** `#1d2b53` deep, `#7e2553` plum, `#ff004d` cherry, `#ffa300` ember, `#fff1e8` cream
- **Lospec / modern-indie:** any curated 16-or-fewer set (Endesga 32, Sweetie 16, AAP-64) used in full

Greys are stepped, never interpolated. `#888` and `oklch()` mixes are forbidden.

## Decoration motifs

- 9-slice chrome border around every panel - corners are sprite-cut, never CSS-rounded
- Selection cursor (`▶` / heart / pointing finger) instead of hover halo - moves in integer steps
- HUD readouts in the chrome: HP bars, coin counts, clock, key inventory - even on a marketing site
- Blinking 1-frame cursor on inputs (`steps(2)`, never opacity fade)
- 8-step sprite-sheet walks for any moving creature
- 2x2 dither checker where a midtone is needed - no gradients, ever
- Coin / heart / key / star pickups as the universal accent ornaments
- Pixel-perfect 1-bit borders; every element snaps to an 8px grid

Forbidden ornaments: Font Awesome icons, emoji glyphs next to sprites, photographic imagery, CSS blur filters, antialiased SVG decoration, drop-shadow with any blur radius.

## Voice register

- Menu labels: terse, ALL-CAPS - `NEW GAME` / `CONTINUE` / `OPTIONS` / `PRESS START`
- Dialog: proper-case with a leading speaker tag - `LINK: It's dangerous to go alone!`
- Exclamation marks are earned, not sprinkled
- Ellipses are three dots `...`, never the `…` glyph (era didn't have it)
- Numbers love a leading zero - `LV.07`, `x008`, `00:42`
- "QUEST", "INVENTORY", "SAVE", "LOAD" as section headers regardless of subject matter

## Failure mode

Pixel sprites sprinkled as garnish on a smooth modern layout - rounded buttons next to 16x16 floppy-disk icons; Press Start 2P used at 14px until the letters mush; `image-rendering: auto` left on so the hero blurs on retina; off-palette flat-UI accents like `#FF6B6B` coral dropped beside an NES palette; smooth 250ms fades and translate-Y hovers where the era only allowed instant or stepped flips; one lone CRT scanline overlay performing "retro" on an otherwise iOS layout; `drop-shadow: 0 4px 12px rgba(0,0,0,.2)` ghosting every sprite. The signature failure: mixing two indexed palettes in the same view, so the work reads as a sticker pack instead of a coherent artifact.

## Best for

Indie game landing pages, retro game stores, game-jam submission sites, pixel-art portfolios, chiptune and 8-bit music releases, fan wikis for NES/SNES/GB games, kid-coding learning platforms (Scratch-adjacent), Twitch overlays for retro speedrunners, and brands honestly committing to the aesthetic rather than borrowing a single sprite for flavor. Bad fit for anything that needs photographic product imagery, dense longform reading, or enterprise legitimacy.

## Pairs well with

- **Shells:** `shell-mobile-app` (phone-as-console), `shell-centered-column` (dialog-box stack), `shell-bento-grid` (inventory grid), `shell-hero-stack` (title screen + feature panels), `shell-terminal-frame` (BBS / save-room framing)
- **Styles:** `style-pixel-bitmap` (the canonical pairing), `style-terminal-mono` (for dense readouts), `style-flat-design` (only when palette and grid stay strict), `style-outline-wireframe` (low-fi development sketch mode)

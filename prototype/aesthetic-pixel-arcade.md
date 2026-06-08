# Arcade Cabinet pixel / Space Invaders era (aesthetic)

**Tag:** `aesthetic-pixel-arcade`

**Canonical references:**
- Space Invaders (Taito, 1978) — the cellophane overlay strips (red top, green bottom) over pure CRT black; the founding monochrome grammar.
- Pac-Man (Namco, 1980) — the indexed 8-swatch palette and the navy `#1717a8` playfield that defined the early-colour cabinet.
- Donkey Kong (Nintendo, 1981) — Shigeru Miyamoto's first character pixel art on a Z80; the airbrushed marquee plate above the bezel.
- Defender (Williams, 1981) — the horizontal scrolling radar HUD as an in-bezel UI vernacular.
- Galaxian (Namco, 1979) — the move from monochrome-with-cellophane to true RGB sprite colour; the Press Start 2P font lineage.

## Cultural identity

The 1978-82 arcade-cabinet era — the four-and-a-half years between Space Invaders shipping and the 1983 video-game crash. The aesthetic is hardware-constrained, not stylised: indexed palettes of 4-8 colours because the ROM and the CRT could not hold more, integer pixel grids because the sprite chips drew 8×8 and 16×16 tiles, no curves because the raster hardware could not render one, no greyscale because the framebuffer was on-or-off per channel. The cabinet itself is part of the aesthetic — the wooden bezel, the airbrushed marquee plate with bevelled-block lettering, the cellophane strips taped over the monochrome CRT to fake colour zones, the control panel reading "HI-SCORE / 1UP / CREDIT 00". This is **pre-NES, pre-console, pre-home-computer** — the public, coin-operated, standing-cabinet era. It is NOT 8-bit console (NES/Famicom 1983+), NOT synthwave (1986+ Outrun aesthetic), NOT modern cozy pixel (Stardew 2016).

## Palette anchor

Two canonical sub-palettes, never blended:

**Space Invaders monochrome + cellophane (1978-79):**
- Ink black `#000000`
- Phosphor white `#fcfcfc`
- Top cellophane strip `#d8261c` (UFO/score zone)
- Bottom cellophane strip `#1ea033` (player/bunker zone)

**Pac-Man / Galaxian indexed RGB (1980-82):**
- Paper white `#fcfcfc`
- Navy playfield `#1717a8`
- Pac-yellow `#fcc92f`
- Blinky red `#dc291e` / `#ff0200`
- Pinky pink `#e2a484`
- Clyde orange `#fb8113`
- Sky `#98cad3`

Greys are **forbidden** — the era had no greyscale ramp. Midtones come from 2×2 checkerboard dithering between two indexed colours, never from a `#7c7c7c`-style grey.

## Decoration motifs

- The **cabinet bezel as frame** — wooden surround `#3a2418` with yellow Pac-Man trim, a top marquee plate, a bottom control panel.
- **Airbrushed bevelled-block lettering** on the marquee — drop-shadow chrome, the only place display type lives.
- **Cellophane overlay strips** on monochrome playfields (Space Invaders) — red top band, green bottom band, never a flat single colour.
- **Scanlines** — 1px horizontal black stripes at ~25-50% opacity over the playfield.
- **CRT vignette** — radial darkening at the corners, faked with `radial-gradient`, never a `filter: blur()`.
- **Indexed sprite grid** — every glyph and motif aligned to an 8×8 or 16×16 cell, no sub-pixel placement.
- **In-bezel HUD vocabulary** — "HI-SCORE", "1UP", "CREDIT 00", "INSERT COIN", "READY!", "GAME OVER", "PUSH START", "EXTEND".

## Voice register

SHOUTED ALL-CAPS in the arcade vernacular. Never sentence case, never lowercase, never marketing copy. English-only (the period ROMs were ASCII-limited). The voice is the attract-mode loop and the high-score table — terse, imperative, scoring-obsessed: "INSERT COIN" / "1UP" / "HI-SCORE 050000" / "PLAYER 1 READY" / "BONUS LIFE AT 10000".

## Failure mode

Press Start 2P at 14px on a charcoal `#1a1a1a` card with `border-radius: 8px`, a soft `0 4px 12px rgba(0,0,0,0.2)` drop shadow, one lone CRT scanline overlay, a neon-pink-and-cyan synthwave grid in the background, and an antialiased SVG Pac-Man icon next to the real pixel text — that's console-era / synthwave cosplay wearing an arcade-font hat. The other tell: SVG sprites with anti-aliased edges, `border-radius` on anything, a `#7c7c7c` NES grey ramp (wrong era — that's 1983+ console palette), or smooth `cubic-bezier` motion (the era had no compositor, only stepped frame swaps).

## Best for

- Arcade revivals, coin-op museum sites, pinball nostalgia.
- Pre-1983 game-history microsites and brand throwbacks (Taito, Namco, Atari, Williams).
- Chiptune releases that genuinely sit in the 1978-82 era — not 1986+ synthwave.
- Fan tributes to Space Invaders, Pac-Man, Donkey Kong, Defender, Galaxian.
- Any product committing fully to the cabinet-as-frame metaphor — not borrowing one sprite for flavour.

## Pairs well with

- Shells: `shell-mobile-app` (portrait CRT viewport reads natively as a cabinet screen), `shell-terminal-frame` (the bezel reads as a frame), `shell-centered-column` (a single tall playfield), `shell-top-bar-canvas` (marquee strip + playfield + control panel reads as the three canonical cabinet zones).
- Styles: `style-pixel-bitmap` (the visual treatment is mandatory — integer scaling, `image-rendering: pixelated`, indexed colour, 2px hard shadows, stepped 1-2 Hz motion). The aesthetic is incompatible with `style-glassmorphism`, `style-aurorism`, `style-neumorphism`, `style-claymorphism`, `style-holographic`, `style-liquid-glass`, or any treatment that requires blur, curves, or sub-pixel rendering.

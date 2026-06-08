# Pixel-grid bitmap (style)

**Tag:** `style-pixel-bitmap`

**Canonical references:** NES.css, Pokemon R/B menus, Lospec palettes, Game Boy DMG, PICO-8.

> **Raster required:** pixel-perfect bitmap sprites at exact native resolution (8x8 / 16x16 / 32x32 tiles, NEVER anti-aliased SVG attempting pixels). Pixel art is raster by definition. Follow the raster requirements decision tree in the main playbook before drawing.

## Surface treatment

A surface drawn on an integer pixel grid with `image-rendering: pixelated` and `-webkit-font-smoothing: none`. Indexed palette, hard-stepped greys, zero curves, zero blur. Every border is a stack of hard offsets; every transition is instant or stepped. The eye reads it as a console screen, regardless of what's on screen.

### Palette

- Pick ONE indexed palette and never leave it. Declare as CSS custom properties `--c0`..`--c15`.
- 4 to 16 swatches max — no interpolation, no `color-mix`, no `oklch` ramps.
- Greys are stepped: `#fcfcfc -> #bcbcbc -> #7c7c7c -> #000000`. Never `#888`.
- Exemplars:
  - **NES**: `#fcfcfc` paper / `#7c7c7c` shade / `#000000` ink / `#f83800` action-red / `#0078f8` cobalt link / `#00a800` confirm-green / `#f8b800` coin-yellow / `#d800cc` menu-magenta.
  - **Game Boy DMG**: `#0f380f` / `#306230` / `#8bac0f` / `#9bbc0f`.
  - **PICO-8 dusk**: `#1d2b53` base.
- Midtones come from a 2x2 dither checker, never a gradient.

### Type stack

- Headers / CTAs: **Press Start 2P** — only at `8 / 16 / 24 / 32 px`, never 14 or 18.
- Body: **VT323** or **Silkscreen**.
- Dense dialog: **m5x7** or **monogram**.
- CJK falls back to a clean system sans (Hiragino, Noto). Do NOT force pixelation on Asian glyphs.

### Sizes & rhythm

- Sizes: `8 / 16 / 24 / 32 / 48 px` only. Multiples of 8. No half-steps.
- Line-height: integer pixel values, not unitless ratios. Body `16px / 16px` (1.0) or `24px / 16px` for breathing dialog. Display `1.0` — no leading on headers.
- Radius: `0px` everywhere. `border-radius` is forbidden. Cut corners come from a 1px-cut corner sprite.

### Borders & shadows

- Borders are box-shadow stacks producing the classic 2px outline + 2px hard offset:
  `box-shadow: inset 0 0 0 2px var(--ink), 2px 2px 0 var(--ink), 4px 4px 0 var(--shade);`
- Or asymmetric: `4px solid var(--ink)` plus `4px solid var(--shade)` only on bottom/right. Never uniform.
- Shadow: hard offset, no blur. `box-shadow: 4px 4px 0 #000` for panels, `2px 2px 0 #000` for buttons.
- `filter: drop-shadow(... blur)` is forbidden. Blurring a sprite breaks the grid.

### Decoration grammar

- **Mandatory**: 1px-grid alignment, blinking 1-frame cursor on inputs/selections, `image-rendering: pixelated` on every `img`/`canvas`, hard-edged selection cursor `▶` instead of hover halos.
- **Forbidden**: gradients, CSS blur, Font Awesome, emoji at body size, photo-real images, antialiased SVG icons next to pixel sprites, `border-radius`, color interpolation.

## Motion budget

- 0ms or stepped only. `transition: none` on hover — prefer JS class swap.
- Allowed: `animation: blink 1s steps(2, jump-none) infinite` for cursors; 8-step sprite-sheet walks via `animation-timing-function: steps(8)`; 16ms instant state flips.
- Forbidden: any `cubic-bezier`, `ease-in-out`, `transform: scale` tweens, opacity fades over 100ms, smooth slides.

## Failure mode

Pixel sprites sprinkled as garnish on a smooth modern layout: rounded buttons next to 16x16 floppy-disk icons; Press Start 2P used at 14px until the letters mush; `image-rendering` left as `auto` so the hero blurs on retina; off-palette flat-UI accents like `#FF6B6B` coral; smooth 250ms fades and `translate-Y` hovers where the era only had instant or stepped flips; one lone CRT scanline overlay performing "retro" on an otherwise iOS layout; `drop-shadow: 0 4px 12px rgba(0,0,0,.2)` ghosting every sprite.

## Best for

Indie game landing pages, retro game stores and jam submission sites, pixel-art portfolios, chiptune and 8-bit music releases, fan wikis for NES/SNES/GB games, kid-coding learning platforms (Scratch-adjacent), and brands honestly committing to the aesthetic rather than borrowing one sprite for flavor.

## Pairs well with

- **Shells:** `shell-mobile-app` (console handheld frame), `shell-centered-column` (single-column menu stack), `shell-terminal-frame` (chrome-as-status-bar), `shell-bento-grid` (tile inventory layouts), `shell-two-column-app` (menu + content like Pokemon R/B).
- **Aesthetics:** `aesthetic-pixel-game-boy-mono`, `aesthetic-pixel-nes-mario`, `aesthetic-pixel-snes-jrpg`, `aesthetic-pixel-ps1-tactics-ogre`, `aesthetic-pixel-modern-cozy`, `aesthetic-pixel-arcade`, `aesthetic-pc-98`, `aesthetic-8-bit-generic`.

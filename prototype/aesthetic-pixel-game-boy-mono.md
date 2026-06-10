---
# Sample-image references for the System-tab design library. Images sit
# next to this file in prototype/ and were generated via image_gen.
images:
  - src: aesthetic-pixel-game-boy-mono-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-pixel-game-boy-mono-isolated.png
    reason: Signature motif, isolated.
---
# Game Boy 2-bit mono (aesthetic)

**Tag:** `aesthetic-pixel-game-boy-mono`

**Canonical references:**
- Pokemon Red/Blue 1996 — dialog frame, menu inversion, ALLCAPS naming, 10-char limit
- Tetris 1989 — the title that shipped the DMG-01 to 35M households, defining the green
- Link's Awakening 1993 — proof the palette could carry an entire overworld
- Kirby's Dream Land 1992 — extreme legibility from 4 shades, charm from constraint
- Lospec DMG-01 palette — the modern canonical reference for the four hexes

## Cultural identity

The Game Boy was Gunpei Yokoi's bet on "lateral thinking with withered technology": a 1989 handheld with a reflective LCD, no backlight, four shades of swamp green, and a 160×144 screen. It outsold every competitor for a decade because the constraint *was* the product — you could see it in sunlight, the batteries lasted, and the games were forced to be readable at any zoom.

The aesthetic is what nostalgia for that constraint looks like now: not "8-bit" as a generic retro mood (that's NES territory — see `aesthetic-pixel-nes-mario`), but the specific *swamp-green monochrome* of the DMG-01 hardware, with the specific *ALLCAPS, exclamation-loaded, name-length-capped* voice of late-Game-Freak ROM text. It is small, terse, charming under duress. It reads as "I survived a 1996 schoolbus" or "I shipped on GB Studio in a week."

This is the indie / hobbyist / itch.io / Lospec corner of pixel culture — the one that takes the constraint seriously as a discipline, not as a Press Start 2P sticker.

## Palette anchor (DMG-01)

The locked 4-stop palette — used as discrete tokens, never interpolated; the only legal "gradient" is a 2×2 Bayer dither between two adjacent shades:

- `#9BBC0F` — paper (lightest, the background; never white)
- `#8BAC0F` — mid (substitutes for "light grey")
- `#306230` — shadow (substitutes for "dark grey")
- `#0F380F` — ink (darkest, the type)

There are no greys, no accents. Emphasis comes from inverting a tile (ink-on-paper becoming paper-on-ink) or from a 1-frame blinking cursor. Page background outside the LCD area is black — the canvas is letterboxed, never stretched.

## Decoration motifs

- The Pokemon-style double-line text frame: 2px outer + 1px gap + 1px inner
- The flashing ▼ "more text" cursor at the end of any dialog that continues
- 8×8 sprite icons aligned hard to the tile grid (item icons, party portraits, status badges)
- Scanline / dither overlay as the only acceptable "texture"
- Inset-pixel "rounded" corners faked at the 8×8 corner tile — never CSS radius
- 1px shadow tile along bottom-right of a window to fake depth — never blurred
- Screen-wipe transitions via 4-step dither cascade, never opacity

Forbidden as decoration: any curve not traced pixel-by-pixel, sub-pixel positioning, opacity below 1.0, colours outside the 4 stops, aspect ratios other than 10:9 (160:144).

## Voice register

Terse. ALLCAPS where the medium allows. Name length capped at ~10 characters (the Pokemon ROM limit was load-bearing). Exclamation marks are content, not decoration. "PIKACHU USED THUNDERBOLT!" — not "Pikachu unleashed a thunderbolt attack."

Microcopy direction: the voice of the ROM, not the voice of the manual.

## Failure mode

AI-generated "pixel art" with anti-aliased edges, five-plus unique greens, soft drop-shadows, Press Start 2P set at 12px (that font is NES-era 4-px-cap; this aesthetic is 7-px-cap), CSS gradients in place of Bayer dithering, and the LCD stretched to fill the viewport instead of integer-scaled and letterboxed. That is NES-cosplay-in-green, not Game Boy. The other tell: using #9BBC0F somewhere on a page that otherwise has a white background — the swamp green only reads as Game Boy when the whole 160×144 frame commits.

## Best for

Nostalgia-coded indie tools, retro game UIs, status/dashboard widgets where extreme constraint reads as charm, anything aimed at the GB Studio / Pico-8 / itch.io demographic, hobby trackers, small personal sites, jam game landing pages.

Bad for: anything requiring colour hierarchy, photographic content, accessible body copy at scale, or a brand that needs to feel premium rather than scrappy.

## Pairs well with

- Shells: `shell-mobile-app` (the native frame — a 160×144 LCD is essentially a tiny phone), `shell-terminal-frame` (the letterboxed-LCD-on-black reads as a terminal cousin), `shell-centered-column` (single LCD centred in dark page)
- Styles: `style-pixel-bitmap` (the canonical render), `style-terminal-mono` (when the brief leans dialog/menu over sprite)

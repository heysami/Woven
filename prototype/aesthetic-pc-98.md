---
# Sample-image references for the System-tab design library. Images sit
# next to this file in prototype/ and were generated via image_gen.
images:
  - src: aesthetic-pc-98-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-pc-98-isolated.png
    reason: Signature motif, isolated.
---
# PC-98 anime visual novel (aesthetic)

**Tag:** `PC-98 (Touhou PC-98 TH01-05, To Heart 1997, Kanon original, Princess Maker 2, World of Horror)`

> **Raster required:** anime portrait raster (16-color dithered at 640×400), authentic PC-9801 visual-novel screenshots, period dojin artwork. The portraits ARE the aesthetic — no SVG alternative. Follow the [Raster requirements](../prototype.md#raster-requirements--when-svg-will-not-deliver-the-genre) decision tree before drawing.

**Canonical references:**
- **Touhou PC-98 TH01–05 (1996–98)** — ZUN's original 640×400 shooters, the canonical Bayer-dither + #000080 menu chrome.
- **To Heart (Leaf, 1997)** — defining bishoujo visual-novel UI: double-stroke window, cream-on-navy dialogue strip.
- **Kanon (Key, 1999, original PC-98 build)** — melancholy register, mincho name plates over Gothic body.
- **Princess Maker 2 (Gainax, 1993)** — stat-amber and system-cyan UI accents on a 16-color palette.
- **World of Horror (panstasz, 2020)** — modern revival proving the aesthetic still reads as occult, not nostalgic.

## Cultural identity

The look of the NEC PC-9801/9821 era of Japanese personal computing (roughly 1985–1999), specifically the bishoujo-game and doujin-shooter subculture that lived there. A 640×400, 16-color hardware constraint that became an aesthetic in its own right: anime portraits ordered-dithered against deep navy menus, kana rendered as 16×16 bitmap Gothic, every shadow a hard 2×2 Bayer checker because the hardware couldn't blend. Revived in the 2010s–20s by World of Horror, modern doujin circles, and the Touhou preservation community — now read as occult, melancholy, and slightly forbidden rather than merely retro. Distinct from Game Boy mono pixel (no anime portraits, no Japanese typography) and from Y2K kawaii (no pastels, no cuteness — even the cute games render dark).

## Palette anchor

- `#000080` deep navy — dialogue panels, menu chrome
- `#ffeecc` cream off-white — body text, panel highlights
- `#000000` / `#ffffff` — outlines and inner-border accents
- `#ff4444` alert red, `#880000` blood shadow — saturated accents
- `#00aaaa` system cyan, `#aaaa00` menu highlight, `#ff9900` stat amber

No pastels. No pinks above `#ffaabb`. No gradients — every transition is hard-edge ordered dither.

## Decoration motifs

- **Ordered-dither checkerboard** (2×2 Bayer) for every shadow, sky, and skin-tone transition.
- **Double-stroke windows**: outer 2px white, 1px gap, inner 1px black (or inverted on dark fills) — never a single solid border.
- **Hard 1–2px translate shadows**, never blur.
- **Active-dialogue cursor glyph**: ▶ or ▼ blinking at the end of the current line.
- **Kana / box-drawing corner ornaments**: ┏ ┓ ┗ ┛, ◆ ◇ on chapter cards and menu frames.
- **DotGothic16 / MS Gothic** bitmap kana as primary type; **MS Mincho** reserved for chapter titles and character-name plates.
- **16×16 tile grid** — everything snaps to 8px or 16px, no in-between values.

## Voice register

Terse, slightly archaic Japanese-light. System messages in ALL CAPS LATIN ("LOAD", "SAVE", "AUTO", "CONFIG"). Character dialogue in sentence-case with full-width Japanese punctuation 「」。、 even in English builds. Melancholy by default; cute only ever bittersweet, never sunny.

## Failure mode

CSS `linear-gradient` skies and `box-shadow` blur instead of hard Bayer dithering. MS Gothic rendered antialiased so kana go fuzzy. Single 1px border instead of double-stroke with hard bottom-right drop. Pastel kawaii palette (pink/lilac/baby-blue) replacing the actual `#000080` + `#ff4444` + `#ffeecc` trinity. `border-radius > 0` on any dialogue box. SD-generated anime portraits with smudged faux-dither overlay instead of authentic ordered dither at hard pixel boundaries. English-only Latin type with no kana decoration anywhere on the page.

## Best for

Visual novels and dating sims. Doujin RPG / SHMUP itch.io pages. Touhou-adjacent fan projects. Occult and horror microsites in the World of Horror lineage. Retro Japanese-software emulation hubs. Archive and preservation sites for 80s–90s eroge and bishoujo games. Music release pages that want the original PC-98 source rather than the mall-Y2K vaporwave derivative.

## Pairs well with

- **Shells:** `shell-centered-column` (the canonical 640×400 letterboxed stage), `shell-two-column-app` (portrait + dialogue strip), `shell-mobile-app` (modern doujin itch.io pages), `shell-terminal-frame` (occult / World of Horror register)
- **Styles:** `style-pixel-bitmap` (mandatory — the hard-edge bitmap substrate this aesthetic lives on), `style-terminal-mono` (for system / CONFIG screens), `style-dense-mono-dark` (for stat-heavy SHMUP or RPG menus)

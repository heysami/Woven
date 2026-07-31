---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-pixel-teletext-mosaic-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-pixel-teletext-mosaic-isolated.png
    reason: Signature motif, isolated.
---
# Teletext / broadcast mosaic (aesthetic)

**Tag:** `aesthetic-pixel-teletext-mosaic`

**Canonical references:**
- BBC Ceefax (1974-2012) - the founding broadcast teletext service; page 302 sport, page 888 subtitles.
- ORACLE / Teletext Ltd on ITV - the commercial rival; Bamboozle quizzes, holiday pages in blocky sunsets.
- The World System Teletext spec (CCITT) - 40x25 character cells, 2x3 block-mosaic sixels, spacing attributes, double-height rows.
- Prestel and Minitel viewdata frames - the dial-up cousins that shared the mosaic character set.
- The teletext art revival (teletext40, Dan Farrimond) - contemporary artists proving the 2x3 cell is an illustration medium.

## Cultural identity

Broadcast-service graphics from the era when the picture WAS text: a fixed 40x25 grid of character cells, each cell either a glyph or a 2x3 block-mosaic tile, transmitted in the blanking interval of a TV signal. The aesthetic is hardware-constrained, not stylised - eight colors because the decoder had three binary channels, chunky mosaic curves because the smallest picture element was a third of a character cell, double-height headlines because the spec had a control code for it and nothing else. Everything lives on black, framed by service chrome: a page number in the corner ("P302"), a colored index bar of numbered sections, "MORE >>>" continuation arrows, dotted-rule separators, dither checkerboards faking midtones the palette cannot hold.

This is NOT `aesthetic-pixel-arcade` - no sprites, no cabinet, no score loop; teletext is a reading service, its register is the news ticker and the sports table, and its glyphs sit on a broadcast character grid, not a sprite sheet. And it is NOT `aesthetic-pc-98` - no dithered anime portraits, no Japanese home-computer palette discipline; teletext is public-service European, institutional and cheerful at once.

## Palette anchor

The eight RGB primaries, full intensity, on black - the decoder knew nothing else:
- White `oklch(100% 0 0)`
- Yellow `oklch(97% 0.21 110)`
- Cyan `oklch(91% 0.15 195)`
- Green `oklch(87% 0.29 143)`
- Red `oklch(63% 0.26 29)`
- Magenta `oklch(70% 0.32 328)`
- Blue `oklch(45% 0.31 264)`
- Black `oklch(0% 0 0)`

No tints, no midtones, no transparency. Intermediate tone is faked with checkerboard dither between two primaries. Yellow-on-blue and cyan-on-black are the canonical service pairings; green is for page numbers and prices.

## Decoration motifs

- **Block-mosaic glyphs** - display lettering and illustration built from 2x3 cell tiles, visibly gridded, corners stepped.
- **Double-height rows** - headlines occupy two character rows; body text one; nothing in between.
- **Page-number chrome** - three-digit page codes top-right, numbered section indexes with dot leaders, "100 NOW INDEX A-Z" navigation strips.
- **Full-cell color bars** - headers as solid blue bars with yellow mosaic text punched into them.
- **Dither checkerboards** - 50% checker between two primaries as the only shading device.
- **Dotted and dashed rules** - hyphen and period runs as separators, never solid hairlines.
- **Blink fields** - one blinking element per page maximum, reserved for REVEAL or breaking news.

## Voice register

Broadcast-service terse. Headlines in caps, body in caps or spec-limited mixed case, everything cut to fit 40 columns: "SPORT 200", "HOME 2-1 AWAY FT", "MORE >>>", "PRESS REVEAL". Prices, scores, and page numbers do most of the talking. Never conversational, never lowercase-casual - the register is a national service speaking to a living room.

## Failure mode

A smooth pixel font at 12px on a dark card with rounded corners and a soft glow = retro-terminal cosplay, not teletext. The tells of the real thing: everything snaps to one visible character grid, mosaic edges are stepped (never anti-aliased), the palette never leaves the eight primaries, and service chrome (page number, index bar, continuation arrow) is present. Gradients, greys, more than one blink, or freeform element placement off the cell grid all break the broadcast-decoder material logic. So does using scanlines as the main signifier - teletext reads as GRID, not as CRT.

## Best for

- News tickers, sports scores, listings, schedules - anything table-and-page shaped.
- Broadcast-nostalgia properties, TV-guide products, quiz and trivia formats (the Bamboozle lineage).
- Status boards and departure boards where the fixed grid is a feature.
- Music/label microsites wanting a public-service-broadcast register instead of a gamer one.

## Pairs well with

- Shells: `shell-terminal-frame`, `shell-centered-column`, `shell-top-bar-canvas`, `shell-mobile-app`
- Styles: `style-pixel-bitmap` (mandatory - integer scaling, stepped edges, no anti-aliasing), `style-dense-mono-dark` (tabular data discipline). Incompatible with any blur, gradient, or sub-pixel treatment.

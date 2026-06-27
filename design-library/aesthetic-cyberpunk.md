---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-cyberpunk-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-cyberpunk-isolated.png
    reason: Signature motif, isolated.
---
# Cyberpunk / Synthwave (aesthetic)

**Tag:** aesthetic-cyberpunk

**Canonical references:**
- Cyberpunk 2077 UI manual - system-default yellow + Rajdhani caps as a governing register
- Blade Runner 2049 / Territory Studio - corporate dystopia hairlines and Cyrillic/JP-glyph density
- Tron Legacy / Encom screens - single-accent cyan grid, no rainbow neon
- Cybercore CSS / Ahmod Musa glitch recipe - community canon for hairline panels and clip-path RGB split
- Ghost in the Shell SAC opening titles - telemetry-as-decoration and timecode chrome

## Cultural identity

Cyberpunk as an aesthetic is the felt surface of late-capitalist dystopia: a megacity at 3am, all signage and no sky, every interface owned by a hostile corporation that still wants you to feel cool using it. It descends from Gibson's *Neuromancer* (1984) and *Blade Runner* (1982), peaks visually with Mamoru Oshii's *Ghost in the Shell* (1995), gets re-canonized for games by *Deus Ex* (2000) and CD Projekt's *Cyberpunk 2077* (2020), and lives on the web as Cybercore CSS and glitch-art Tumblr lineage.

Synthwave is its softer twin - same neon palette and chrome typography, but nostalgic for an imagined 1984 (Miami Vice, Drive, *Stranger Things*) rather than dreading 2077. The two collapse into one aesthetic on the web because they share the same hot accents on the same near-black ground; the difference is whether the world is hopeful (synthwave) or hostile (cyberpunk).

The emotional contract is **terminal cool**: the user is a netrunner, a console cowboy, a corpo operator - never a customer. Even a banking app in this aesthetic implies you are exfiltrating funds, not budgeting.

## Palette anchor

Mood, not full tokens - see `style-` files for hex tables.

- Void ground: near-black #0A0A0F to #050505
- System-default yellow: #FCEE0A (the 2077 anchor - use sparingly, as headline or active state)
- Cyan: #00F0FF (data / interactive)
- Magenta: #FF2A6D (danger / glitch only - never a hover)
- Violet bridge: #2B1E45 (the seam between magenta and cyan; skip it and the page screams)
- Hostile red: #FF3C3C; success #05FFA1

**Rule:** pick ONE hot accent per screen. The other hues appear only as 1-character glyphs or telemetry.

## Decoration motifs

- Corner-bracket frames (L-bracket cuts at the four corners, not closed rectangles)
- Monospaced metadata rows along a panel edge - coordinates, hex IDs, timecodes, version strings
- 1px hairline dividers as `linear-gradient(transparent, accent, transparent)`
- Scanlines as a *whisper* (alpha ~0.07), never a hum
- Telemetry as ornament: live numerics, signal bars, frequency strings that don't need to mean anything
- Cyrillic / Katakana / Hangul glyphs as texture, not language
- Clip-path RGB-split glitch as a one-shot on hover or error - never a loop

**Forbidden imagery:** the pink-sun-with-perspective-grid hero (album-cover synthwave transplanted onto a UI), wireframe roads, palm-tree silhouettes, lens flares, lightning bolts, the literal word CYBER in the logo.

## Voice register

Terse military-corporate caps for *system* text: "AUTH // 0xA4F2", "INCOMING TRANSMISSION", "v2.077.4", "TRACE COMPLETE". Prose body stays plain sentence case so the caps actually carry meaning. Numeric IDs, coordinates, and timecodes are decoration as much as data. Never warm, never apologetic - the system does not say "Oops!"

## Failure mode

Every word glowing instead of one focal phrase. Magenta AND cyan at full chroma touching without the #2B1E45 violet seam to bridge them. Scanlines at alpha 0.3 so the whole page hums. Orbitron at 14px used for paragraphs (it is a caps-only display face). A perpetual glitch loop on the H1 making it unreadable. Corner brackets ⌐¬ stamped on every card so none feels focal. A stock "retro grid horizon with neon sun" hero pasted onto a productivity app with no narrative reason. Rainbow-neon hover states that turn the page into a Razer Synapse config screen.

## Best for

- Video-game launchers and companion apps
- Music releases in the synthwave / darksynth / EBM / industrial space
- AI/ML model dashboards that want a netrunner register
- Security-ops, pen-test, and red-team tools
- Hardware product pages for keyboards, mice, wearables
- Sci-fi film and series marketing sites
- Esports event pages and tournament HUDs
- Crypto / DeFi terminals that lean dystopian rather than corporate-pastel

## Pairs well with

- **Shells:** shell-three-column-app, shell-top-bar-canvas, shell-terminal-frame, shell-canvas-floating, shell-two-column-app, shell-bento-grid
- **Styles:** style-dense-mono-dark, style-oversized-neo-grotesque, style-flat-design (dark variant), style-holographic (for the synthwave-leaning end)

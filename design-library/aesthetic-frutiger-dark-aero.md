---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-frutiger-dark-aero-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-frutiger-dark-aero-isolated.png
    reason: Signature motif, isolated.
---
# Frutiger Dark Aero (aesthetic)

**Tag:** Dark Aero (Windows Vista Aero dark / Longhorn builds, Sony PSP & PS3 XrossMediaBar, original Spotify 2014 dark theme, Bloomberg Terminal, Vista-era enterprise dashboards)

**Canonical references:**
- Windows Vista Aero dark theme / Longhorn 2003-05 build screenshots - graphite chrome, single accent, gloss reserved for the focused window
- Sony PSP (2004) and PS3 (2006) XrossMediaBar - the horizontal-vertical "cross" plus the slow ambient wave behind it
- Spotify 2014 desktop (pre-flat) dark theme - green-on-graphite, one accent, humanist sans
- Bloomberg Terminal - graphite/black ground, amber as the single signal colour, dense numeric authority
- Vista-era enterprise dashboards (NOC walls, broadcast control rooms) - dark glass with one live signal as the hero

> **Raster required:** the ambient layer behind the glass (XMB wave, aurora drift, bokeh, audio waveform) must be a real raster or shader - pure CSS reads as dark Aurorism, not Aero. See the [Raster requirements](../prototype.md#raster-requirements--when-svg-will-not-deliver-the-genre) decision tree before drawing.

## Cultural identity

Dark Aero is the **after-hours** mode of Frutiger Aero - the same gloss, glass, and humanist optimism, but rendered for the den, the studio, the trading floor, the living-room console. It peaks 2004-2010 across two parallel tracks: Microsoft's Longhorn → Vista Aero dark theme on PC, and Sony's PSP/PS3 XrossMediaBar on consumer hardware. Spotify's original 2014 desktop client and Bloomberg's terminal are the surviving professional dialect.

The mood is **competent, unhurried, lived-in.** Where light Aero is a sunny morning, Dark Aero is the room dimmed for a film, the night drive with the dashboard glowing, the pro tool at 11pm. It signals craft software, hi-fi, and consumer hardware that respects the user enough to assume taste. It is the opposite of gamer-RGB: it never shouts.

The core gesture: **graphite ground, one ambient layer drifting behind, one floating glass panel in focus, exactly one neon accent.** Everything else is hairline chrome.

## Palette anchor

Graphite (never pure black) as the ground, warm off-white as text, one neon accent - picked once, used everywhere it matters.

- Graphite ground: `#0E1014` base, vignetting to `#1A1D24` at the edges
- Piano-black surfaces: `#1C1F26` with `#2A2F38` hairlines
- Warm off-white text: `#E6ECF5` (never pure `#FFFFFF`) - secondary `#8A93A6`
- Accent (pick ONE): cyan `#7DCFFF` (Vista-glow) · amber `#FFB000` (Bloomberg) · Spotify-green `#1DB954` · XMB-ice `#A8D8FF`
- Pure `#000` reserved for dense data canvases (Bloomberg pole) - not the default ground

Greys stay under ~0.012 chroma so the cool cast reads as anodised metal, not blue tint.

## Decoration motifs

- **The ambient layer** is mandatory and is what makes Dark Aero, Dark Aero: a slow XMB-style wave, an aurora gradient drifting at 0.05-0.1 Hz, soft bokeh on graphite, or a low-amplitude audio waveform behind the focused panel
- **Glass reserved for the focused element only** - one panel refracts the ambient layer; everything else is matte chrome
- **The Aero inner-light** - a 1px highlight along the top edge of the focused glass, the single hairline that says "this is the live one"
- **Horizontal-vertical "cross" navigation** acceptable (XMB lineage) - a row of categories crossed by a column of items, never a grid of equal cards
- **Single live signal as hero** - waveform, ticker, telemetry, now-playing - the ambient layer's job is to make it feel alive
- **No iconography on chrome** beyond hairline glyphs; the accent colour never touches chrome itself, only the focused signal

## Voice register

Technical, neutral, mid-register English. Labels read like a competent system reporting on itself: "Now Playing", "System Status", "Library", "Signal: 87 dBm", "Output: -3.2 dB". Numbers are unembellished and trusted. Never gamer-bro ("LOCKED IN", "ENGAGED"), never marketing-cheer ("Unleash your sound"), never lifestyle-warm ("Your evening, sorted"). The system speaks; it does not sell.

## Failure mode

Pure `#000` ground + three clashing neons (pink + cyan + lime) racing-striped across the header + glow on every icon instead of just the focused one + frosted glass over flat black with nothing behind to refract (becomes a dirty grey rectangle - the AI tell) + Orbitron / Rajdhani / Audiowide as body type + Lucide icons stroked in `#00FFFF` = **gamer-RGB cosplay**, not Dark Aero. Tasteful Dark Aero is graphite (not black) + ONE neon + gloss reserved for the focused element + humanist sans (Segoe UI / Frutiger / Inter) + a real ambient layer (wave / aurora / bokeh) behind the glass so the refraction has something to do.

## Best for

Media players, audio and video software, console dashboards, financial terminals, network operations centres, automotive cluster prototypes, hi-fi product pages, the "pro" tier of any consumer app, anything where a single live signal (waveform, ticker, telemetry, now-playing track) is the hero and the room is dimmed around it.

## Pairs well with

- Shells: `shell-canvas-floating` (the canonical fit - full-bleed ambient ground, one focused panel), `shell-top-bar-canvas` (XMB lineage with a chrome rail), `shell-three-column-app` (library / queue / now-playing for media tools), `shell-two-column-app` (chrome rail + focused canvas)
- Styles: `style-aurorism` (for the ambient drift behind the glass), `style-glassmorphism` (the focused panel itself), `style-dense-mono-dark` (when the Bloomberg pole is the brief), `style-holographic` (for the accent edge on the focused panel), `style-liquid-glass` (modern refraction reading of the same idea)

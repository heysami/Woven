---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-arcade-marquee-neon-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-arcade-marquee-neon-isolated.png
    reason: Signature motif, isolated.
---
# Arcade marquee neon (aesthetic)

**Tag:** backlit showfloor glamour

**Canonical references:**
- 80s-90s arcade cabinet marquees (After Burner, OutRun, Galaga '88) - backlit plexi plates of chrome-bevel lettering over airbrushed space.
- Cabinet side-art airbrush tradition - sunset-fade scripts, starbursts, speculars painted on vinyl.
- Movie-poster chrome logotypes (The Last Starfighter, Thief) - the display-type lineage the marquees borrowed.
- Neon arcade signage - tube-outline lettering and border runs framing the showfloor itself.

## Cultural identity

The arcade's exterior glamour - not the game on the CRT but the cabinet selling it: a backlit marquee where **chrome-bevel display lettering** (mirror-gradient faces, hard specular bites, extruded dark edges) collides with **airbrushed sunset script** (brush-lettered, hot-pink-to-orange fade, motion tails), both floating over cabinet-vinyl black flecked with starfield. On components the neon takes over: every button, card, and input wears a glowing tube outline - cyan for primary, magenta for secondary - with a soft halo bleeding onto the vinyl. Inside the cards, pixel ship sprites and phosphor score digits remind you what the marquee is advertising.

This is NOT `aesthetic-vaporwave` - no pastel irony, no statues, no melancholy; the marquee is sincere commercial hype, painted by someone paid to make quarter-droppers cross the room. And it is NOT `aesthetic-pixel-arcade` - that is the in-game sprite register of 1978-82 played on the CRT; this is the cabinet's exterior world of chrome, airbrush, and neon, where pixels appear only as quoted artwork inside the frame.

## Palette anchor

Neon signage over vinyl black:
- Aisle black `oklch(13% 0.01 270)` (#0a0b10) - matte vinyl with speckle, never pure #000
- Marquee cyan `oklch(85% 0.14 210)` (#00e6ff)
- Marquee magenta `oklch(67% 0.29 335)` (#ff3cf7)
- Sunset orange `oklch(74% 0.18 55)` (#ff8a00) fading to hot pink
- Neon purple `oklch(58% 0.25 300)` (#8a3cff)
- Arcade green `oklch(85% 0.2 160)` (#39ff9a) - credits and prices only
- Phosphor white `oklch(96% 0.01 290)`

Cyan and magenta must both be present - the two-tube storefront contrast is the signature. Halo glow is allowed and expected; this is the library's rare legitimate use of outer glow.

## Decoration motifs

- **Chrome-bevel display lettering** - mirrored gradient faces, sky/ground horizon line inside the letterforms, extruded shadows.
- **Airbrushed script** - brush-lettered secondary display in sunset fade with speed-tail strokes.
- **Neon tube outlines** - rounded-corner glowing borders on every component, halo included; active state brightens the tube.
- **Starfields** - sparse white speckle on the vinyl ground; the occasional four-point star glint.
- **Cabinet materials** - matte vinyl grain, chrome T-molding strips as dividers, speaker-grille dots.
- **Quoted game art** - pixel sprites and phosphor numerals inside cards, framed like screens within the cabinet.
- **Speedline accents** - horizontal neon dashes flanking titles, the marquee's motion shorthand.

**Raster required:** the logotypes - chrome-bevel lettering and airbrushed script cannot be faked with CSS gradients (illustration `chrome-airbrush-logotype`, in the y2k-chrome-3d lineage). Tube outlines and starfields are CSS; the marquee plate is not.

## Voice register

Attract-mode hype, all caps, quarter-economy imperative: "PLAY NOW", "INSERT COIN", "ONE MORE CREDIT CAN CHANGE EVERYTHING", "CLAIM THE HIGH SCORE". Superlatives welcome; irony forbidden. The voice is the cabinet shouting across a dark aisle.

## Failure mode

Pastel pink-and-teal with a Greek bust = vaporwave; a flat neon-outline button on pure black with no halo, no vinyl texture, and no chrome lettering = generic "gamer dark mode". The real thing needs the two display voices together (chrome bevel AND airbrush script), tube glow with visible halo, and a black that reads as material (speckled vinyl) rather than absence. One display face alone, or glow applied to body text, collapses the marquee into a Discord theme.

## Best for

- Game launches, esports events, arcade bars and retro-gaming venues.
- Drops and campaigns that want maximum showfloor hype without irony.
- Music acts and club nights in the synth-adjacent space that need signage energy.
- High-score, leaderboard, and tournament products.

## Pairs well with

- Shells: `shell-hero-stack` (the marquee IS a hero), `shell-top-bar-canvas`, `shell-mobile-app`
- Styles: `style-outline-marquee` (canonical - the tube-outline component grammar), `style-bold-display`, `style-pixel-bitmap` (quoted sprite artwork only)

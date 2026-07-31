---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-mecha-crisis-hud-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-mecha-crisis-hud-isolated.png
    reason: Signature motif, isolated.
---
# Mecha crisis HUD (aesthetic)

**Tag:** 90s anime command-center emergency

**Canonical references:**
- Neon Genesis Evangelion (Gainax, 1995) - the NERV command-room walls: orange phosphor readouts, countdown-to-impact typography, kanji alerts.
- Patlabor / Ghost in the Shell (1989-95) control-room screens - acid-green system diagnostics on black.
- Gunbuster / Macross Plus test-flight telemetry - hazard stripes and unit schematics as set dressing.
- The "MAGI deliberation" screen grammar - three-way system votes, percentage syncs, DANGER boxes.

## Cultural identity

The emergency wall of a 90s mecha-anime command center: the entire interface is in a declared state of crisis and has been for years. Phosphor orange, acid green, and alert red - colors that should never share a screen - share every screen, on absolute black, separated into hard-cornered panels with cut corners and hazard-striped borders. The hero element is a **countdown**: seven-segment digits at display scale, HR MIN SEC, always running. Headlines are kanji first with letterspaced English subtitles beneath ("非常事態 / EMERGENCY"), a bilingual formality that makes every label feel like protocol. Scanline and tech-mesh textures sit under everything; percentages (SYNC 78%, POWER 92%) climb toward thresholds nobody names.

This is NOT `aesthetic-cyberpunk` - no street, no rain, no neon commerce, no holograms; this is a military installation's interior, institutional and doomed, its palette signal-coded rather than atmospheric. And it is NOT `material-crt-phosphor` - that is a single-hue emissive screen material; this aesthetic is the multi-color ALERT SEMANTICS and hazard furniture of the room, which a build might render on phosphor but does not have to.

## Palette anchor

Signal colors at full alarm on black:
- Phosphor orange `oklch(68% 0.21 45)` (#ff5a00) - the default information color
- Acid green `oklch(86% 0.27 135)` (#39ff14) - systems nominal, secondary panels
- Alert red `oklch(58% 0.24 28)` (#ff1a1a) - DANGER, thresholds crossed
- Alarm yellow `oklch(88% 0.17 95)` (#ffd800) - caution bands
- Absolute black `oklch(0% 0 0)`

Orange carries the page; green disagrees with it; red interrupts it. No blues, no pastels, no gradients - every hue is a classification.

## Decoration motifs

- **Hazard-stripe borders** - 45-degree orange/black caution bands framing the page and critical panels.
- **Countdown as hero** - display-scale seven-segment digits with HR / MIN / SEC captions; time pressure is the layout's centerpiece.
- **Kanji alert headlines** - large kanji with letterspaced English subtitles; stamps and seals ("特務") as corner marks.
- **Cut-corner panels** - rectangles with clipped 45-degree corners and tick-marked frames, never rounded.
- **Scanline and tech-mesh textures** - fine horizontal lines and grid meshes under panel fills.
- **Threshold meters** - segmented bars filling toward red; percentage readouts pinned to unit schematics.
- **Barcode / version blocks** - "ID: CRISIS_WALL_90A VER 1.0.0" registration furniture in panel corners.

**Raster required:** the unit line-art - a mecha head or schematic rendered as single-color contour drawing (illustration `mecha-lineart-schematic`). The panels and stripes are CSS; the machine portrait is not.

## Voice register

Protocol under pressure, bilingual and absolute: "EMERGENCY", "SYSTEM ALERT", "TIME REMAINING", "危険 / DANGER". Body prose is formal operational Japanese-inflected instruction ("All systems have shifted to emergency protocol. Await orders."). Never casual, never reassuring, never marketing - the voice is a PA system in a bunker.

## Failure mode

Cyan-and-magenta neon, glassmorphic panels, or a chill dark-mode gray = cyberpunk street UI or a SaaS dashboard in costume. The tells of the real thing: orange dominates, hazard stripes exist, a countdown or threshold is the largest element, corners are cut not rounded, and kanji headlines carry English subtitles. Equally fatal: using the palette decoratively so red no longer means danger - if everything screams, add hierarchy back until only the DANGER box screams.

## Best for

- Launch pages, drops, and deadline-driven campaigns (the countdown is native).
- Ops/incident dashboards and monitoring tools that embrace the war-room register.
- Mecha and anime fan properties, game companion apps, esports team hubs.
- Any product whose story is "big machine, barely contained".

## Pairs well with

- Shells: `shell-top-bar-canvas`, `shell-bento-grid` (the crisis wall is a panel grid), `shell-hero-stack`
- Styles: `style-dense-mono-dark`, `style-micro-text-frame` (registration furniture at panel edges)

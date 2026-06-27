---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-rgb-gamer-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-rgb-gamer-isolated.png
    reason: Signature motif, isolated.
---
# RGB Gamer (aesthetic)

**Tag:** `aesthetic`

**Canonical references:**
- Razer Synapse 3 - the per-device tile rail and Chroma config as the canonical "control surface"
- ASUS ROG Armoury Crate - angular chamfers, ROG Red, telemetry-as-decoration
- NZXT CAM - calm dark shell with restrained accent, hardware-first hero
- MSI Mystic Light - the rainbow as a payload (lighting), not a typeface treatment
- Cyberpunk 2077 HUD - tracked-uppercase labels, mono numerals, the single status dot

## Cultural identity

Mid-2010s through mid-2020s PC enthusiast hardware - the moment "gamer" stopped meaning beige towers and started meaning addressable RGB on every keycap, fan blade, and DRAM stick. The aesthetic was crystallised by peripheral-maker control panels (Razer, Corsair, Logitech G, ASUS ROG, MSI) and the streamer/esports adjacent products that copied them. The shared message: this is an instrument, you are the operator, the rainbow is a tunable parameter - not the brand itself.

Crucially, the *good* version of this aesthetic treats RGB as the **brand-accent payload on a calm dark shell**. The control panel is mostly black. The lighting demo strip is where the rainbow lives. Telemetry (DPI, polling Hz, fan RPM, temps) is presented like avionics - terse, monospaced, no exclamation marks. This is the "operator" reading, not the "rave" reading.

## Palette anchor

- Ink near-black: `#07090C` base, `#14171C` surface, `#1B1F26` raised
- Hairline: `#2A2F38`
- Text: `#E6E8EC` body, `#8A93A1` muted
- Pick **ONE** saturated accent and commit:
  - Razer Green `#44D62C`
  - ROG Red `#DE272C`
  - Chroma Cyan `#00F7FF`
  - Sim-rig Amber `#FFB020`
- Rainbow only as a payload gradient on a **single** divider, progress fill, or Chroma demo strip: `#FF2D55 → #FFB020 → #44D62C → #00F7FF → #B14CFF`

## Decoration motifs

- Per-device tile rail (icon-only, one active dot)
- Inline LED status dot - single hue, slow 6s breathing on the active row only
- Chamfered hero card (one per view, never on every button)
- Tracked uppercase section labels - `+120` letter-spacing, 12px
- Mono numerals for any reading: DPI, Hz, RPM, °C, hex codes
- Optional 1px gradient border on the single hero card
- Forbidden: circuit-board SVG backgrounds, Tron grids, lens flares, hue-rotate on the page, glitch-shake on titles, emoji flames

## Voice register

Terse spec-sheet, avionics-adjacent. Verbs are `ENGAGE`, `SYNC`, `CALIBRATE`, `BIND`, `PROFILE`. Readings sit naked: `TRUE 8000 Hz · 26K DPI · OPTICAL`. No exclamation marks. Never use "gamer" as an adjective. Never "epic", "next-level", "unleash". The operator is competent; the copy respects that.

## Failure mode

Treating RGB as the visual style instead of as the brand-accent payload on a calm dark shell. The cheap version stacks: rainbow gradient text, chamfered clip-path on every button, 20px glow on every border, Orbitron + Audiowide + Press Start 2P competing in the same heading, a tiled circuit-board SVG behind everything, three accent colors on one screen, hue-rotate animation on the page background. The result reads as a 2008 modding-forum signature, not a 2024 control surface.

## Best for

- Gaming peripheral product pages and configurators (keyboards, mice, headsets)
- Custom-PC builder flows and BOM reviewers
- Esports team dashboards and stat pages
- Streamer / DJ control panels
- Sim-rig and flight-stick telemetry
- Mech-keyboard community sites
- Any product where the hardware itself is the identity

## Pairs well with

- Shells: `shell-three-column-app`, `shell-two-column-app`, `shell-top-bar-canvas`, `shell-bento-grid`, `shell-canvas-floating`
- Styles: `style-dense-mono-dark`, `style-flat-design`, `style-neubrutalism` (only if the chamfer/border instinct is dialled way down)

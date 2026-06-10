---
# Sample-image references for the System-tab design library. Images sit
# next to this file in prototype/ and were generated via image_gen.
images:
  - src: aesthetic-cassette-futurism-ui.png
    reason: Generated UI mockup committing this aesthetic's vocabulary at a usable density — palette, type tone, decoration motifs in context.
  - src: aesthetic-cassette-futurism-isolated.png
    reason: Isolated subject sample — the aesthetic's signature motif / texture / illustration treatment on a neutral background.
---
# Cassette Futurism (aesthetic)

**Tag:** Severance / Lumon MDR · Alien 1979 + MU-TH-UR · Alien: Isolation · Foundation · Berkeley Mono recreations

**Canonical references:**
- Severance / Lumon MDR — clerical dread, cyan phosphor on navy, beige plastic chassis
- Alien 1979 + MU-TH-UR — amber CRT, Semiotic Standard square pixels, "Mother" register
- Alien: Isolation (2014) — period-accurate scanline CRT recreation, chunky toggles
- Foundation (Apple TV+) — deep-time institutional UI, Berkeley Mono lineage
- IBM 5151 monochrome monitor — green phosphor, tabular data, 24h clocks

## Cultural identity

Cassette Futurism is **the future as it was imagined in 1979** — beige injection-moulded plastic, CRT phosphor, magnetic tape, dot-matrix printouts, fluorescent strip-lit offices. It assumes the future is institutional, bureaucratic, and slow: spacefaring as paperwork, AI as a courteous mainframe, dread as a clerical procedure rather than a hack. The look peaks in the Nostromo's MU-TH-UR room, the Lumon MDR floor, and the Foundation Imperial archives — all spaces where a person sits at a terminal and submits to a system that addresses them with deferential euphemism.

It is **not** cyberpunk (no neon, no rain, no street), not synthwave (no gradients, no purple), not vaporwave (no irony, no marble busts), and not generic terminal-on-web (the chassis is the point — without the beige plastic well around the screen, you've drawn a TUI, not Cassette Futurism).

## Palette anchor

Three families, all desaturated, none luminous:

- **Chassis** — `#D8D2C4` warm putty, `#B8B3A4` Steelcase grey (the injection-moulded shell around the CRT)
- **Screen well** — `#0B1F2A` Severance MDR navy, `#0A0F08` phosphor black (never pure `#000`, never white)
- **Phosphor primary** — pick ONE channel: cyan `#7FE9DE` (Lumon), amber `#FF9F1C` (Alien), or green `#33FF66` (IBM 5151). Dim variants `#994400` / `#00802B` for secondary type.
- **One accent only** — warning red `#C8321E`, used at most once per screen
- **Forbidden** — gradients, purple, neon pink, lens-flare cyan, anything that suggests post-2005

## Decoration motifs

- **Scanlines** — 1–2px repeating, 3–5% opacity, the single non-negotiable signal
- **Chassis seams** — fake injection-moulded plastic via 1px inset highlight + inset shadow
- **Corner registration ticks** and `[ LUMON ]`-style wordmark plates
- **Physical affordances** — chunky toggles, dial readouts, capacity bars made of square pixels
- **Tabular data** — padded numerals (`004 / 128`), 24h clocks, dates as `1979.06.06`
- **Semiotic Standard icons** — square-pixel pictograms (Lance Wyman lineage), or no icons at all
- **Forbidden** — emoji, drop-shadow on type, glassmorphism, lens flare, animated gradients, SVG icons with rounded strokes, "ACCESS GRANTED" hacker-movie copy

## Voice register

Clerical, deferential, slightly euphemistic. The system addresses the user as a courteous superior addressing a junior clerk:

- "Please refine the following file."
- "Compliance acknowledged."
- "Sector 4 nominal."
- "Your cooperation is appreciated."

Never the hacker-movie register ("INITIATING SEQUENCE", "ACCESS GRANTED", "HACK THE PLANET"). Numbers always padded, times always 24h, dates always period-formatted.

## Raster requirement

CRT phosphor screen captures (green/amber glow), beige plastic patina photography, period control-panel hardware shots, and scanline overlay textures are **required** — CSS-only Cassette Futurism collapses into terminal-on-web. Follow the [Raster requirements](../prototype.md#raster-requirements--when-svg-will-not-deliver-the-genre) decision tree before drawing: check image-gen MCPs, then public-domain archives, then project assets, then ask the user. If all fail, switch aesthetics rather than fake it.

## Failure mode

VT323 at 16px everywhere, full-body flicker keyframe, pure `#0F0` on `#000` with no chassis around it, 20px lime glow blurring all the type, and "INITIATING SEQUENCE" hacker copy in place of Lumon's clerical register. That's a 2014 Codepen terminal demo, not Cassette Futurism. The chassis-around-the-screen, the ONE phosphor channel (not RGB rainbow), and the deferential institutional voice are what distinguish the aesthetic from generic retro-terminal kitsch.

## Best for

- Archival and records UIs (compliance dashboards, document refinement)
- Slow industrial dashboards — refineries, HVAC, mainframe ops, nuclear control rooms
- Retro instruction manuals and in-world fictional apps for sci-fi worldbuilding
- Anything where the subject is **institutional dread**, midcentury bureaucracy, or deep-time spacefaring
- Productivity tools that want to feel weighty, slow, and consequential rather than peppy

Avoid for: consumer-friendly onboarding, anything cheerful, anything that needs to feel fast or modern, anything where users expect to be praised by the UI.

## Pairs well with

- **Shells:** `shell-terminal-frame` (the beige chassis IS the terminal frame), `shell-three-column-app` (operator console layout), `shell-top-bar-canvas` (dashboard with status strip), `shell-two-column-app` (records browser)
- **Styles:** `style-terminal-mono` (closest match — pair with chassis treatment), `style-dense-mono-dark` (Bloomberg-leaning operator console variant), `style-pixel-bitmap` (Semiotic Standard icons and capacity bars)

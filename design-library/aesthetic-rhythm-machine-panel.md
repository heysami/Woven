---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-rhythm-machine-panel-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-rhythm-machine-panel-isolated.png
    reason: Signature motif, isolated.
---
# Rhythm machine panel (aesthetic)

**Tag:** early-80s music-hardware silkscreen

**Canonical references:**
- Roland TR-808 (1980) - the color-banked sixteen-step row: red, orange, yellow, white in groups of four.
- Roland TR-909 / TB-303 - silkscreened matte panels, rubber keys, LED state dots.
- LinnDrum / Oberheim DMX - the competing grammar of gray caps and red seven-segment readouts.
- Akai MPC60 (1988) - pad-grid descendant that carried the vocabulary into hip-hop's toolkit.
- Sequential Circuits Prophet panels - the era's silkscreen typography at its most confident.

## Cultural identity

The front panel of an early-80s drum machine: a **matte black silkscreened chassis** ruled into labeled zones by thin white lines, a **sixteen-step button row** color-banked in fours (red 1-4, orange 5-8, yellow 9-12, white 13-16) with a round LED above every step, and a **seven-segment tempo readout** burning red at display scale ("128.0"). Labels are silkscreen caps printed straight onto the panel; grouping brackets underline related controls; every control is a real switch with one job. The machine's charm is total legibility - state is physical (a lit LED, a pressed key), color is positional (the bank tells you where you are in the bar), and nothing hides in a menu.

This is NOT `aesthetic-cassette-futurism` - no beige institutional plastic, no CRT terminals, no corporate computing; this is instrument hardware, black and confident, built for stage light. And it is NOT `aesthetic-analog-studio-hardware` - that is the previous generation's wood-and-ivory electromechanical console; this is its successor: silkscreen instead of engraving, LEDs instead of needles, rubber instead of bakelite.

## Palette anchor

Signal colors on matte black, straight from the 808's step banks:
- Panel black `oklch(18% 0 0)` (#1a1a1a) - matte, finely textured, never glossy
- Step red `oklch(62% 0.22 30)` (#ff3b30)
- Step orange `oklch(74% 0.18 55)` (#ff9a00)
- Step yellow `oklch(87% 0.18 95)` (#ffd600)
- Step white `oklch(96% 0 0)` (#f2f2f2)
- LED red glow `oklch(62% 0.24 28)` with halo - lit state only
- Silkscreen white `oklch(96% 0 0)` - labels and rule lines

The four-color bank sequence is the signature and must appear in order. Seven-segment readouts are always red on near-black.

## Decoration motifs

- **The sixteen-step row** - chunky rounded-rect keys in banked colors with LED dots above; the hero component for any sequence, progress, or selection UI.
- **Seven-segment readouts** - red digits with decimal points for tempo, counts, and values.
- **Silkscreen rule-lines** - thin white borders carving the panel into labeled functional zones.
- **Grouping brackets** - underbraces with captions ("1-4 RED") annotating control clusters.
- **LED state dots** - small round indicators, lit-with-halo or dead-dark, never in-between.
- **Instrument nameplates** - bold machine designations ("TR-808X") as display type.
- **Panel hardware** - corner screws, textured-metal strips, the occasional rocker switch.

## Voice register

Machine-direct imperative caps: "PLAY", "CLEAR", "TAP", "MAKE THE PATTERN. FEEL THE GROOVE." Short declaratives about function ("EVERY CONTROL HAS A PURPOSE"). Numbers are precise ("128.0", "16 STEPS", "56%"). No metaphor, no softness - the panel speaks like its own manual.

## Failure mode

A dark UI with random orange accents and rounded cards = generic music-app dark mode. The real thing requires the banked color SEQUENCE (four colors, in fours, in order), LEDs that are binary (lit or dark), silkscreen zoning lines, and seven-segment digits reserved for values. Also fatal: gloss, gradients on keys, ivory-and-walnut warmth (previous era), or wood side-panels with needle meters - that is the studio-console world, not the rhythm box.

## Best for

- Sequencers, schedulers, habit trackers - anything with steps in a cycle.
- Music-making tools, sample libraries, beat-culture and hip-hop heritage properties.
- Pattern editors and automation builders (steps = states is the native metaphor).
- Products that want tactile instrument energy: press it and it happens.

## Pairs well with

- Shells: `shell-bento-grid` (the panel is zones), `shell-two-column-app`, `shell-mobile-app`
- Styles: `style-dense-mono-dark`, `style-skeuomorphism` (kept matte and rubbery, never glossy)

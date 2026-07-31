---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-spy-dossier-typewriter-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-spy-dossier-typewriter-isolated.png
    reason: Signature motif, isolated.
---
# Spy dossier typewriter (aesthetic)

**Tag:** Cold-war case file - manila stock, typewriter display with ribbon-ink irregularity, surveillance halftones, red CLASSIFIED stamps

**Canonical references:**
- Cold-war intelligence file dressing: manila folders, carbon copies, agent-ID fields, file-tab furniture
- 1960s spy-film title sequences built from dossier props - typed credits, crosshair overlays, numbered photo grids
- Typewriter typography as display: monospace caps with ribbon-ink fill variation, trailing cursor pipe
- Surveillance photography: grainy halftone stills, subjects at distance, reticle marks
- Rubber-stamp bureaucracy: CLASSIFIED at an angle, double-boxed, over-inked

## Cultural identity

A case file you were not cleared to open: manila stock throughout, every heading typed in monospace caps with the uneven ribbon-ink fill of a real machine (some letters darker, some starved), and a trailing cursor pipe as if the typist just stopped. Surveillance halftone photos sit in numbered grids with crosshair reticles over the subject; a red CLASSIFIED stamp crosses them at an angle, over-inked and double-framed. Data lives in field rows (SUBJECT / STATUS / LOCATION / DATE); dashed rules separate sections; file tabs and paperclips organize the stack.

The defining gesture is **the typed line under surveillance**: typewriter caps + halftone photo + crosshair + red stamp, composed as evidence - the page always implies someone compiled it, and someone else should not be reading it.

Where `material-photocopy-xerox` is a SURFACE treatment (toner-crush filters you can apply to anything), spy dossier is a full world: layout furniture, photographic register, stamp system, and a bureaucratic voice - the toner is one ingredient, not the point. And unlike `recipe-newspaper-of-record` (editorial broadsheet: serif newsface, bylines, public record), the dossier is a COVERT document - typewriter not typeset, compiled not published, redacted not reported.

## Palette anchor

File-cabinet neutrals with one alarm:
- Manila `oklch(90% 0.05 95)`
- Dossier stock (darker sheet) `oklch(84% 0.05 90)`
- File gray `oklch(70% 0.02 120)`
- Carbon `oklch(35% 0.01 120)`
- Ink black `oklch(16% 0.005 90)`
- Alarm red (stamps + compromised states) `oklch(55% 0.19 25)`

Red is exclusively a stamp/alert channel. Photos are black halftone on manila - never full color, never clean grayscale.

## Decoration motifs

- Typewriter monospace display caps with ribbon-ink irregularity and a trailing cursor pipe
- Numbered surveillance-photo grids: coarse halftone stills, corner index digits, crosshair reticles
- Angled red CLASSIFIED / VOID stamps, double-boxed, over-inked with edge bleed
- Field-row data furniture: SUBJECT / STATUS / LOCATION / DATE with typed values
- Dashed and dotted rules, file tabs, paperclip and staple artifacts, redaction bars
- Registration crosshair marks in page corners

**Raster required:** the surveillance photography - grainy halftone stills of subjects and cities (raster-photo, long-lens documentary register) - plus the over-inked stamp impressions. The field rows and dashed rules are CSS; the evidence is not.

## Voice register

Filed and terse, passive where it matters: "STATUS: COMPROMISED." "Subject last observed Berlin, 12.04.64." Case-officer diction - observe, engage, extract - typed in caps for fields, sentence case for narrative notes. Never marketing warmth, never first-person enthusiasm; the document does not know you are reading it.

## Failure mode

A distressed "typewriter font" over a coffee-stained parchment texture = escape-room prop. The ink irregularity must vary per character, not repeat; the stamp must sit at a believable angle with real edge bleed, not a clean red border. Full-color photos or modern UI icons shatter the period. Green matrix glow or scanline effects drift it into hacker-terminal territory - this is paper espionage, pre-digital. Overusing red (headers, links, backgrounds) demotes the stamp from alarm to accent.

## Best for

- Mystery, thriller, and detective media - games, film promos, interactive fiction
- Investigation and research tools that suit case-file framing
- Escape rooms, ARGs, and puzzle campaigns with document props
- Editorial features on intelligence history, true crime, archives

## Pairs well with

- Shells: `shell-centered-column`, `shell-editorial-broken-grid`, `shell-two-column-app`
- Styles: `style-micro-text-frame`, `style-brutalist-raw`, `style-restrained-hairline`

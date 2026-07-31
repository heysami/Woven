---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-cdrom-multimedia-console-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-cdrom-multimedia-console-isolated.png
    reason: Signature motif, isolated.
---
# CD-ROM multimedia console (aesthetic)

**Tag:** mid-90s rendered-hardware interface

**Canonical references:**
- Myst (Cyan, 1993) - painterly pre-rendered scenes inset in machined navigation chrome.
- Microsoft Encarta 95 - the encyclopedia-as-console: media wells, transport buttons, category dials.
- The 7th Guest / Riven interface plates - deep-beveled fantasy hardware framing full-screen renders.
- Macromedia Director-era "multimedia titles" - every edutainment disc with a brushed-metal home screen.
- Kai's Power Tools / Bryce UI (Kai Krause) - the era's maximal rendered-widget philosophy.

## Cultural identity

The interface-as-machine fantasy of the CD-ROM era: the screen pretends to be a slab of rendered hardware - brushed-steel panels with visible screws and rivets, micro-vent grilles, deep bevels that read as centimeters of machined depth - and the content lives in **inset media wells**, recessed screens playing painterly scenes that glow like another world behind glass. Buttons are physical transport controls (play, eject, rewind) with travel you can almost feel; type is engraved letterspaced caps, stamped into the metal rather than printed on it. The composition is a console: chrome outside, wonder inside.

This is NOT `style-skeuomorphism` in the iOS-6 sense - no leather stitching, no paper textures, no glossy touch-candy; the material world here is industrial fantasy hardware, pre-touch, navigated by a cursor that clicks heavy switches. And it is NOT `material-brushed-aluminum` - that is one surface finish; this is a whole console grammar of wells, rivets, transport rows, and painterly inserts that happens to be milled from steel.

## Palette anchor

Cold machine neutrals holding a warm glowing insert:
- Steel `oklch(66% 0.01 240)`
- Gunmetal `oklch(48% 0.01 240)`
- Slate shadow `oklch(32% 0.01 250)`
- Teal indicator `oklch(68% 0.1 195)`
- Violet indicator `oklch(58% 0.14 300)`
- Screen glow white `oklch(96% 0.01 270)`
- Insert amber-gold `oklch(80% 0.14 85)` - the painterly scene's light spilling into the chrome

The chrome stays desaturated; all warmth and saturation belongs to what is inside the wells.

## Decoration motifs

- **Deep bevels** - multi-step edges implying real thickness; panels within panels, each seam modeled.
- **Rivets, screws, and vent grilles** - fasteners at panel corners, speaker-dot fields, ribbed intake slots.
- **Inset media wells** - recessed rounded-rect screens with an inner shadow lip, playing painterly stills or loops.
- **Transport button rows** - chunky machined play / pause / eject clusters with engraved glyphs.
- **Engraved letterspaced caps** - display type debossed into the metal with a highlight edge.
- **Indicator lamps and progress pips** - small violet/teal LED blocks, never flat UI badges.

**Raster required:** two kinds - the brushed-steel panel textures with modeled bevels (photo `machined-console-chrome`), and the painterly scenes inside the wells (photo or illustration `painterly-vista-insert`). CSS can fake a shallow bevel; it cannot fake this depth or the Myst-grade insert.

## Voice register

Machine-plate nomenclature: engraved product names ("ORBITAL"), destination labels ("ZETA PRIME"), timecodes ("07:42"). Sparse, capitalized, letterspaced. The console does not chat - it labels. Any longer prose belongs inside the media well as narration, not on the chrome.

## Failure mode

A flat gray card with a subtle gradient and a metal-texture fill = desktop-app gray, not console. The real thing needs conviction in depth: bevels with multiple steps, fasteners you can count, wells that sit visibly BELOW the panel surface, and a painterly insert that contrasts warm against cold steel. Equally fatal: making everything metal with no glowing insert (a console with nothing inside), or sliding into iOS-6 gloss with highlights and stitching - wrong decade, wrong material fantasy.

## Best for

- Media players, archives, galleries - anything with a "look into the well" content model.
- Adventure-game properties, edutainment revivals, interactive-fiction hubs.
- Museum kiosks and encyclopedia-like reference products wanting gravitas plus wonder.
- Portfolio sites presenting work as artifacts behind glass.

## Pairs well with

- Shells: `shell-top-bar-canvas`, `shell-two-column-app`, `shell-mobile-app`
- Styles: `style-skeuomorphism` (nearest kin - push it industrial, never glossy-leather), `style-dense-mono-dark` (engraved label discipline)

---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-pixel-snes-jrpg-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-pixel-snes-jrpg-isolated.png
    reason: Signature motif, isolated.
---
# Pixel SNES 16-bit JRPG (aesthetic)

**Tag:** aesthetic

**Canonical references:**
- EarthBound (1994) - warm Americana palette, deadpan microcopy, sprite charm
- Chrono Trigger (1995) - Toriyama sprite work, era-defining proportional bitmap dialog font
- Final Fantasy VI (1994) - engraved navy menu windows as the canonical UI chrome
- Secret of Mana (1993) - ring-menu and pastel field palettes
- A Link to the Past (1991) - tile-quantized world art, 16×16 icon vocabulary

## Cultural identity

The console-RPG golden age, roughly 1991-1996: cartridges, CRT televisions, Saturday-morning fluorescent kitchens, strategy-guide pages dog-eared in a Trapper Keeper. This is the aesthetic of slow turn-based progress - inventories, stats, dialog boxes, save points - rendered with the SNES's 256-colour palette and its strict 4bpp sprite budget. It is warmer and more painterly than the NES (more colours, banded ramps instead of flat fills), more constrained than the PlayStation era (no pre-rendered CGI, no transparency tricks beyond palette cycling). The mood is earnest, mildly translation-ese, optimistic in a slightly stiff way; nostalgia here is not ironic, it is sincere.

## Palette anchor

Pick from fixed 16-slot sub-palettes - never blend, never gradient, only hard bands.

- Royal navy window fill `#1028A0` with highlight `#6088E0` and shadow ridge `#080858` - the engraved Final Fantasy VI / Chrono Trigger menu chrome
- Sky band ramp `#5878D8` → `#88B0F0` → `#C8E0F8` in three hard stops, no gradient
- Grass band ramp `#387028` → `#58A038` → `#88C048`
- EarthBound warm ramp `#C87858` → `#E8A878` → `#F8D8A8`
- Accent gold `#F8C840`, HP green `#58D048`, MP magenta `#E058B8`, dialog white `#F8F8F8`
- Greys are only four steps: `#181818` / `#585858` / `#989898` / `#D8D8D8`

## Decoration motifs

- Engraved two-tone window bevel: 2px highlight top+left, 2px shadow bottom+right, optional 1px white hairline inside
- 16×16 icon vocabulary - sword, potion, heart, key, gem, scroll - drawn in 4bpp, never line icons
- Banded color ramps with visible posterization (sky, grass, water)
- Sprite drop-shadows as a separate 16×8 ellipse sprite, never CSS blur
- Palette-cycle animation on water, lava, torch flames, selected-row highlights
- Optional CRT scanline overlay (1px every 2px, ~30% opacity) and slight integer-pixel jitter on title logos
- Hard pixel edges throughout - `image-rendering: pixelated`, integer-multiple scaling only

## Voice register

Warm, slightly stiff translation-ese. All-caps menu labels (ITEM / MAGIC / EQUIP / STATUS). Exclamation-heavy NPC barks ("You found the Mythril!", "It's a secret to everybody."). Earnest, never ironic, never modern UX-writing. No "Tap to continue" - say "Press A" or "..." instead. Numbers matter: HP / MP / GP / EXP, always uppercase, always padded.

## Failure mode

Smooth bilinear "pixel-ish" art with anti-aliased edges, Inter or SF Pro for dialog, a flat `#000080` window with no engraved bevel, a CSS gradient sky instead of three hard bands - that is generic AI retro, not SNES. Equally cheap: wrong-era palette imports (NES 4-colour-per-tile flatness, Game Boy DMG green, indie-pixel lavender-and-teal) that drift into the wrong decade. The tell is always: any blur, any `border-radius`, any non-integer scaling, any emoji or Lucide icon, more than 16 colours in a single sprite.

## Best for

Turn-based or grid-based apps where progression, inventory, stats and dialog matter. Quest trackers, habit RPGs, language-learning streaks, recipe collectors, fantasy admin dashboards, dungeon-crawler todo lists, anything that wants warm 90s Saturday-morning nostalgia over slick modernism. Sincere, not ironic - works when the subject genuinely benefits from being framed as a small adventure.

## Pairs well with

- Shells: shell-mobile-app, shell-two-column-app, shell-three-column-app, shell-centered-column, shell-top-bar-canvas, shell-bento-grid
- Styles: style-pixel-bitmap, style-terminal-mono, style-flat-design

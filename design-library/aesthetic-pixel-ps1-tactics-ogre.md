---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-pixel-ps1-tactics-ogre-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-pixel-ps1-tactics-ogre-isolated.png
    reason: Signature motif, isolated.
---
# PS1 32-bit isometric pixel - Tactics Ogre era (aesthetic)

**Tag:** `aesthetic`

**Canonical references:**
- Tactics Ogre: Let Us Cling Together (1995) - gilded scroll panels over isometric tiles, the genre's Rosetta stone
- Final Fantasy Tactics (1997) - Yoshida portrait frames + parchment menus, the painterly chrome standard
- Vagrant Story (2000) - near-black void UI, oxblood + amber jewel tones
- Suikoden II (1998) - codex-feel character sheets, oldstyle figures in stat blocks
- Ogre Battle 64 (1999) - heraldic crests, Roman-capital chapter cards

## Cultural identity

The painterly-prestige end of 32-bit JRPG tactics: a medieval-codex sensibility filtered through PS1 sprite limitations. Where NES/arcade pixel is bubblegum and primary-colored, this aesthetic is jewel-toned, Romanesque, and grave - it borrows from illuminated manuscripts, heraldry, and Shakespearean theatre rather than from Saturday-morning cartoons. Peaked 1995-2000 on PS1 / Saturn / N64, defined by Akihiko Yoshida's portrait work for Quest/Square and Matsuno's writing register. The vocabulary signals: fantasy gravitas, lore-density, party-of-named-characters, hand-painted chrome, an audience that grew up with Ivalice rather than the Mushroom Kingdom.

This is "pixel" but never "8-bit" - the resolution is higher, the sprites are isometric, the chrome is painted, and the typography is Roman serif, not Press Start 2P. Confusing the two eras is the cardinal sin.

## Palette anchor

Desaturated jewel tones, never NES primaries:

- **Void / parchment** - `#0E0C14` (Vagrant Story near-black) or `#E8D9B0` (FFT vellum) as the two ground states
- **Gilded amber** - `#C9A24A` primary chrome, `#E6C36A` hot-gilt selection
- **Oxblood** - `#7A2E2E` danger / HP critical
- **Mossy green** - `#4F6B3A` confirm / terrain
- **Muted indigo** - `#3A4A6B` info / magic
- **Sepia ink** - `#3A2E22` body text on parchment

All colors sit one step below saturation max - closer to stained-glass than to Crayola.

## Decoration motifs

- Painterly pixel portrait in a gilded frame - mandatory, carries the gravitas
- Ornate corner fleurons / scroll-edge panels - never edge-to-edge chrome
- Isometric tile grid visible behind the menu chrome
- Heraldic crests, chapter cards with Roman inscriptional capitals
- Stat bars with thin gilt frame and gradient fill
- Oldstyle-figure numerals (`font-variant-numeric: oldstyle-nums`) in stat blocks
- Optional subtle CRT scanline overlay - 18% black, 1px on / 2px off
- Hard 1px drop shadow on sprites, no modern soft blur

## Voice register

Archaic-formal, Shakespearean / Matsuno-translation cadence. Title Case for class and ability names ("White Mage", "Dragoon", "Holy Knight"). Second-person archaic where it fits - "Thy party hath gained 240 EXP", "Whither shall we march?". Never casual modern UX copy ("Got it!", "Let's go!", "Oops"). Numbers spelled out only in flavor text; in stat blocks they are oldstyle figures.

## Failure mode

NES primaries (`#FF0000`, `#00FF00`) on an isometric grid + Press Start 2P bitmap font + flat rectangles labelled "Status / Menu" in Inter - this is "8-bit cosplay drift", the wrong era cosplaying as the right one. The dead giveaways: no Roman serif headers, no gilded scroll-frame, no painted portrait, rounded corners anywhere, modern soft drop-shadows, emoji. Press Start 2P specifically is forbidden - it's NES/arcade vocabulary, not PS1-Yoshida vocabulary.

## Best for

Tactical and strategy dashboards, lore-heavy character sheets, party / inventory / equipment screens, codex and bestiary surfaces, prestige fantasy briefs, anything that wants the gravitas of a medieval manuscript rather than the bubblegum of arcade 8-bit. Audiences 25+ who recognise Ivalice; products that lean on worldbuilding, named characters, or a sense of historical weight.

## Pairs well with

- **Shells:** `shell-three-column-app` (party / map / detail), `shell-two-column-app` (codex), `shell-top-bar-canvas` (battle map + status footer), `shell-bento-grid` (character sheet panels), `shell-centered-column` (chapter-card narrative)
- **Styles:** `style-pixel-bitmap` (the rendering substrate - `image-rendering: pixelated`, hard 1px shadows, no border-radius), `style-serif-warm-paper` (the parchment / Roman-serif chrome layer), `style-terminal-mono` (only as a contrasting in-world diegetic surface, sparingly)

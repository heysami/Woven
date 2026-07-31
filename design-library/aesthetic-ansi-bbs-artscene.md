---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-ansi-bbs-artscene-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-ansi-bbs-artscene-isolated.png
    reason: Signature motif, isolated.
---
# ANSI BBS artscene (aesthetic)

**Tag:** dial-up bulletin-board maximalism

**Canonical references:**
- ACiD and iCE artpacks (1990-96) - the artscene groups that turned CP437 block shading into illustration.
- Classic BBS welcome screens - winged logos, city skylines, and dragons drawn in 16-color text mode.
- TheDraw / PabloDraw - the editors whose half-block and shade-character techniques defined the look.
- Door games (Legend of the Red Dragon, TradeWars 2002) - numbered-menu chrome around ANSI art headers.
- 16colo.rs archive - the living museum of the artscene corpus.

## Cultural identity

The 2 a.m. dial-up bulletin board: an 80x25 character grid where **illustration and interface are the same medium**. Big winged logotypes, skylines, and mascots are drawn in CP437 block-shading characters (the quarter-, half-, and full-blocks, the ░▒▓ shade ramp) in the 16 ANSI colors; beneath them, the board's chrome is box-drawing frames (single and double line), numbered menu "doors" ("1) MESSAGE BASE ... 5) LOGOFF"), hotkey brackets ("[N] Next [P] Prev [Q] Quit"), and the occasional blink field on a blue bulletin bar. Everything glows against black; cyan and magenta carry the night-time register, with royal blue fills for selected rows and bulletins.

This is NOT `material-ascii-art-surface` - that is a monochrome texture treatment applied to a surface; this is a full 16-color ILLUSTRATED WORLD plus a complete interface grammar (menus, doors, hotkeys, bulletins) native to the terminal. And it is NOT `recipe-terminal-on-web` - that recipe is the modern dev-tool terminal, minimal and professional; the artscene is subcultural maximalism, where the point is showing off how much picture a character grid can hold.

## Palette anchor

The ANSI 16, on black - dim and bright pairs, used as indexed color, never mixed to new hues:
- Cyan `oklch(70% 0.12 195)` / light cyan `oklch(88% 0.13 195)` - the house color of the night board
- Magenta `oklch(55% 0.25 328)` / light magenta `oklch(75% 0.22 330)` - logo accents
- Blue `oklch(40% 0.25 264)` - selection fills, bulletin bars, blink fields
- Yellow `oklch(90% 0.18 100)`, light red `oklch(65% 0.2 25)`, light green `oklch(85% 0.25 140)` - sparingly, as signal
- Grays `oklch(70% 0 0)` / `oklch(45% 0 0)` - body text and dim chrome
- Black `oklch(0% 0 0)`

Midtones come from the ░▒▓ shade ramp and character dither, never from new colors.

## Decoration motifs

- **Block-shading illustration** - logos and scenes built from half-blocks and shade characters, visibly cellular, lovingly huge.
- **Box-drawing chrome** - single/double-line frames with ornamental corner joins; frames within frames.
- **Numbered menu doors** - "1) ... 2) ... 3)" lists as primary navigation, cursor block at the prompt.
- **Hotkey brackets** - "[N] Next" command bars as footers on every card and screen.
- **Blink fields** - royal-blue bars with starred text ("* NEW MAIL *"), the one permitted animation.
- **SysOp bulletins** - centered, bordered announcement cards with bullet ornaments.
- **The prompt cursor** - a resting block cursor after every input, always visible.

## Voice register

SysOp hospitality - courteous, slightly medieval, community-proud: "Well met, traveler.", "Choose a door from the list above.", "New mail awaits." Command language is bracketed and terse. The register is intimate broadcast: one operator talking to the few hundred people who know the number.

## Failure mode

A monospace font on a dark div with green text = generic hacker terminal, wrong scene. The real thing demands the grid (every glyph on the cell lattice), real block-shading art with multiple colors (not just text), box-drawing frames with proper joins, and the door/hotkey navigation grammar. Also fatal: anti-aliased type, more than one blink element, true-color gradients, or modern-minimal restraint - an artscene screen that is mostly empty has missed the entire point of the medium.

## Best for

- Community boards, forums, guestbooks, and webring-flavored spaces.
- Demoscene, chiptune, and retrocomputing properties.
- Text-heavy games, MUDs, interactive fiction hubs (the door-game lineage).
- Personal sites that want handmade subcultural warmth on a terminal grid.

## Pairs well with

- Shells: `shell-terminal-frame` (canonical), `shell-centered-column`, `shell-mobile-app`
- Styles: `style-pixel-bitmap` (cell-locked rendering discipline), `style-dense-mono-dark`

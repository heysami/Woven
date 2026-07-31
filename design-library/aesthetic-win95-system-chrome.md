---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-win95-system-chrome-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-win95-system-chrome-isolated.png
    reason: Signature motif, isolated.
---
# Win95 system chrome (aesthetic)

**Tag:** 90s dialog-box vernacular

**Canonical references:**
- Windows 95 / NT 4 system dialogs - the canonical C0C0C0 gray, 1px bevel grammar, MS Sans Serif at 8pt.
- InstallShield wizard sequences - Welcome / License / Serial Number / Progress, the Back-Next-Cancel ritual.
- Shareware installers and registration nags (WinZip, mIRC) - "Enter your serial number to unlock the full version."
- Netscape and WinAmp-era setup screens - 16-color dithered banner art down the wizard's left rail.
- Windows 3.1 Program Manager - the immediate ancestor: same bevels, chunkier defaults.

## Cultural identity

The system-dialog chrome of mid-90s desktop computing treated as a complete visual system, applied sincerely to a whole product. One gray rules everything; depth comes from a strict two-tone bevel: white highlight on the top and left edge, dark shadow on the bottom and right, one pixel each, no radius, no blur. Raised means clickable, sunken means editable, and a dotted focus rectangle means selected. The crown jewel is **wizard furniture**: a titled dialog, a left rail of 16-color dithered landscape art, plain instructional prose ("This wizard will install ZXQ-94 on your system. Click Next to continue."), and the eternal button row - Back, Next, Cancel - right-aligned, Next pre-focused.

This is NOT `shell-desktop-os-metaphor` - that is a layout shell (windows, taskbar, draggable chrome) that can wear any skin; this entry is the material and component grammar itself - the bevels, the gray, the wizard - usable inside any shell. And it is NOT `aesthetic-vaporwave` - vaporwave borrows a single dialog as an ironic sticker on pink gradients; here the chrome is the entire world, played straight, gray to the horizon.

## Palette anchor

- Dialog gray `oklch(80% 0 0)` (#c0c0c0) - the universal surface
- Border shadow `oklch(57% 0 0)` (#808080)
- Border highlight `oklch(100% 0 0)` (#ffffff)
- Text black `oklch(0% 0 0)`
- Accent navy `oklch(35% 0.2 264)` (#0000cc) - title bars, selection, progress fill
- Input white `oklch(100% 0 0)` - sunken field interiors

Nothing else. Any additional color arrives inside the dithered banner art, never in the chrome.

## Decoration motifs

- **Hard 1px bevels** - raised buttons (highlight top-left), sunken inputs and wells (shadow top-left), double-bevel group boxes.
- **Wizard furniture** - title bar, left-rail banner art, body prose, Back / Next / Cancel row, "< Back" and "Next >" with literal angle brackets.
- **16-color dithered banner art** - a vertical landscape painting (castle, mountains, teal sky) rendered in checkerboard dither.
- **Progress bars** - navy blocks marching through a sunken gray channel.
- **Serial-number fields** - monospaced groups with hyphens: "ZXQ94-XXXX-XXXX-XXXX".
- **Tiny pictorial icons** - 16x16 and 32x32 pixel icons with black outlines (the diskette, the hourglass, the scroll-and-pen).

**Raster required:** the dithered wizard banner art and the 16x16/32x32 pictorial icon set (pixel `wizard-banner-dither` imagery). The bevels are CSS; the left-rail painting is not.

## Voice register

Patient system prose in sentence case: "This wizard will install...", "Click Next to continue.", "Enter your serial number to unlock the full version." Labels are short nouns with colons ("Serial Number:"). Never marketing enthusiasm, never lowercase-cool - the computer is politely walking you through something.

## Failure mode

Rounded corners, soft shadows, anti-aliased type, or a hover transition = a modern UI wearing a gray costume. The tells of the real thing: bevels are exactly one pixel and unblurred, the gray is flat everywhere, focus is a dotted rectangle, buttons have angle-bracket labels, and nothing animates except the progress bar. Adding pink or cyan turns it into vaporwave pastiche; adding gloss turns it into XP - both are different worlds. The banner art must be visibly dithered, not a smooth photo.

## Best for

- Installers, onboarding flows, and multi-step forms that want the wizard ritual played straight.
- Developer tools, file utilities, settings-heavy products leaning into honest-gray functionalism.
- 90s-software nostalgia properties, retrocomputing museums, shareware-culture tributes.
- Satire that needs the registration-nag register to land.

## Pairs well with

- Shells: `shell-desktop-os-metaphor` (canonical), `shell-centered-column` (the wizard as a lone centered dialog), `shell-two-column-app`
- Styles: `style-pixel-bitmap` (icons and banner dither). Incompatible with `style-glassmorphism`, `style-claymorphism`, `style-aurorism`, or anything blurred, rounded, or glossy.

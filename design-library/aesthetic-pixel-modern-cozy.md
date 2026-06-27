---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-pixel-modern-cozy-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-pixel-modern-cozy-isolated.png
    reason: Signature motif, isolated.
---
# Pixel modern cozy (Stardew / Celeste) (aesthetic)

**Tag:** Modern cozy pixel - Stardew Valley / Celeste (Stardew Valley 2016, Celeste 2018, Hyper Light Drifter 2016, Eastward 2021, Sea of Stars 2023)

**Canonical references:**
- Stardew Valley 2016 - the warm-NPC farming archetype; top-down 16-color worldcraft
- Celeste 2018 - Madeline red `#e85a3c`, painterly mountain palette, hue-shifted shadows
- Hyper Light Drifter 2016 - pixel-locked dusk palette, parallax bands, no AA
- Eastward 2021 - modern painterly pixel with cinematic dialogue framing
- Sea of Stars 2023 - high-fidelity 32-48px sprites, day/night colour cycling

## Cultural identity

The 2010s-2020s indie pixel renaissance - pixel art reborn not as nostalgia for NES/SNES limits but as a *deliberately painterly* medium. Where 8-bit was constrained by hardware, modern cozy pixel is constrained by craft: artists pick a 16-color palette as an act of taste, hue-shift shadows because flat black is lazy, and animate at 8-12fps because every frame is hand-pixeled. The emotional register is warm, hopeful, human-scale - a JRPG town square at dusk, a farm at first light, the moment Madeline catches her breath. Cozy doesn't mean low-stakes; it means the world is rendered with care.

This aesthetic is post-Stardew (2016) - the moment when "pixel" stopped meaning "retro" and started meaning "indie auteur." The sister works (Celeste, Hyper Light, Eastward, Sea of Stars) share a refusal of both grit-realism AND sepia-nostalgia in favour of saturated, cool, painterly worlds.

## Palette anchor

- Cool nature greens - Pelican grass `#3a6a4d`, teal-shadow `#2a5a52`
- Sky / water blues - sky `#6ec1e4`, dusk `#2a3a5e`, Junimo accent `#59c9f1`
- Warm accent reds/yellows - Madeline red `#e85a3c`, lantern yellow `#ffd921`, maroon-shadow `#7a2238`
- Warm dirt-grey ramp - `#3a2e2a` → `#6b574a` → `#a89683` → `#e8dcc4` (parchment HUD), never neutral grey

Shadows are *hue-shifted*, never black. The world is *cool* and saturated, never sepia.

## Decoration motifs

- Pixel-locked sprites at 32-48px, hand-pixeled icons (never Lucide/Feather)
- Nine-slice parchment panels with 1px hard two-tone borders
- 2x2 ordered-dither gradients between sky bands - never smooth gradients
- Parallax layers, day/night colour-cycle tint, firefly/sparkle 2x2 white squares
- Dialogue strips with portrait + character name plate
- Forbidden: gaussian blur, smooth gradients, anti-aliased outlines, isometric grid, pillow-shaded rims

## Voice register

Warm, lowercase-friendly, NPC-personality. Exclamation marks allowed; em-dashes for beats. HUD labels are terse and lowercase (`stamina`, `gold`, `day 1`). Dialogue body reads like a friend telling you about their day - "Welcome to the valley!" not "USER_GREETING_01".

## Failure mode

The instant-AI-pixel tell: 32px character beside 8px HUD icon beside 4px font (pixel-size drift); m6x11 rendered at 13.5px so it antialiases; pillow-shaded rim on every sprite; warm sepia wash instead of cool Stardew greens; `border-radius: 8px` on dialogue boxes; `box-shadow: 0 4px 12px rgba(0,0,0,.2)` gaussian drop-shadow. Any one of these collapses the genre into AI-pixel cosplay.

Sepia and "retro warm filter" are the cardinal sins - this aesthetic is *cool* and saturated, not nostalgic-brown.

## Best for

- Farming / cozy-life sims and their companion apps
- JRPG-flavoured habit trackers, journals, garden / pet apps
- Indie game launchers, itch.io-adjacent storefronts
- Achievement & progression dashboards where warmth and craft beat density
- Worldbuilding / character-led products where an NPC voice fits

## Pairs well with

- Shells: shell-mobile-app, shell-two-column-app, shell-three-column-app, shell-top-bar-canvas, shell-hero-stack, shell-canvas-floating
- Styles: style-pixel-bitmap, style-flat-design (sparingly, for menu chrome)

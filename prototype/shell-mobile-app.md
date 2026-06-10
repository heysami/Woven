---
# Sample-image references for the System-tab design library. Images sit
# next to this file in prototype/ and were generated via image_gen.
images:
  - src: shell-mobile-app-ui.png
    reason: Generated UI mockup showing this shell's structural grammar — grid, density, regions, and characteristic component placement.
---
# Mobile app shell

**Tag:** `[mobile · top-bar + tab-bar · 1-col-scroll]`

## Structure

Phone-shaped centered frame on desktop preview, full-bleed on mobile. Three vertical zones:

- **Top bar** (44pt) — sticky top; back/hamburger + title + trailing action
- **Scrollable content** (1fr) — single-column list or stacked sections
- **Bottom tab bar** (49pt + safe-area-inset) — 3-5 tabs with icon + label

## Macro proportions

Phone frame: 375x812 (iPhone) or 360x800 (Android). Content padding 16-20px horizontal. Touch targets 44pt minimum. List rows 60-88px tall.

## Mandatory interactions (not optional)

- Tap-to-navigate on list rows -> detail screen via useState
- Tab swap on tab-bar tap
- Sheet present from bottom for actions
- Hold-to-press visual on buttons
- Swipe-back gesture visualized

## Forbidden

Horizontal scrollers as primary nav (chip carousels are fine). Sidebar nav (this is mobile). Multi-column content. Hover-only states.

## Best for

Mobile-native APP prototypes where the prototype shows the running product, not a marketing page.

## Pairs well with

Style: sf-pro-ios, material-m3, claymorphism, glassmorphism, neumorphism. Aesthetic: any (positivity-kawaii, cottagecore, cyberpunk).

---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: style-sf-pro-ios-ui.png
    reason: Style surface UI mockup.
  - src: style-sf-pro-ios-isolated.png
    reason: Signature surface, isolated.
---
# SF Pro / iOS system (style)

**Tag:** `iOS native feel`

**Canonical references:** Apple HIG (iOS 17+) · SF Pro / SF Pro Rounded / SF Mono · Apple Notes, Reminders, Settings · iOS Mail · Apple Music.

## Surface treatment

System surface with hairline separators, grouped rounded containers, and a precise type scale. Nothing decorative - the only ornament is the radius and the hairline.

### Color
- Background: `oklch(96% 0.002 240)` system grey, or pure white `#FFFFFF`
- Grouped container fill: `#FFFFFF` on grey background, or `oklch(97% 0.002 240)` on white
- Primary label: `#000000` / dark mode `#FFFFFF`
- Secondary label: `oklch(55% 0 0)` (~`#8E8E93`)
- Tertiary label: `oklch(70% 0 0)`
- Separator: `oklch(88% 0 0)` at 0.5px (hairline)
- Tint / accent: system blue `#007AFF` (or app-defined, single hue)
- Destructive: system red `#FF3B30`

### Type
- Family: `-apple-system, "SF Pro Text", "SF Pro Display", system-ui` - SF Pro Rounded only for playful subjects, SF Mono only for code/timers
- Scale: 13 (footnote) / 15 (subhead) / 17 (body, default) / 20 (title 3) / 22 (title 2) / 28 (title 1) / 34 (large title)
- Weights: 400 body, 600 headlines, 700 large title
- Line-height: 1.29 body, 1.2 titles
- Tracking: Apple-spec negative tracking on display sizes (-0.4px at 28pt, -0.5px at 34pt)

### Geometry
- Container radius: `10px` grouped lists, `12-14px` cards, `22px` pill buttons, full-round avatars
- Hairline: `0.5px solid` separator color - never `1px`
- Tap targets: minimum 44×44pt
- Inset list separator: starts at 16pt from leading edge of content (skips icon column)

### Decoration grammar
- Mandatory: hairline separators, grouped rounded containers, SF Symbols (or SF-Symbol-shaped icons) at consistent stroke weight
- Forbidden: drop shadows on flat content, gradients on surfaces, colored borders, multi-hue accents, custom fonts that aren't system, decorative backgrounds, "fun" emoji as UI

### Motion
- Push transition: spring `cubic-bezier(0.32, 0.72, 0, 1)` ~350ms
- Tap response: instant (no fade), with brief 100ms opacity dip to ~0.6 on press
- Modal sheet: spring from bottom, ~400ms
- Reduce-motion: cross-fade only

## Failure mode

The "Apple-ish" tell: Inter or Roboto instead of SF, `1px` borders instead of `0.5px` hairlines, drop shadows on list rows, accent color used three different ways on one screen, emoji as functional icons, square buttons where pills belong, headlines without the negative tracking.

## Best for

Mobile-first apps, settings panes, personal tools, anything that should feel native iOS without cosplaying as a marketing site. Subjects that benefit from invisible chrome and full attention on content.

## Pairs well with

- Shells: `shell-mobile-app`, `shell-two-column-app`, `shell-three-column-app`, `shell-centered-column`, `shell-top-bar-canvas`
- Aesthetics: `aesthetic-anti-design`, `aesthetic-positivity-kawaii`, `aesthetic-frutiger-eco`, `aesthetic-frutiger-tranquil-serenity`, `aesthetic-y2k-futurism` (Aqua tilt)

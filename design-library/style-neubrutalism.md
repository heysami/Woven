---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: style-neubrutalism-ui.png
    reason: Style surface UI mockup.
  - src: style-neubrutalism-isolated.png
    reason: Signature surface, isolated.
---
# Neubrutalism (saturated + borders + offset shadows) (style)

**Tag:** style

**Canonical references:** Gumroad 2021, Figma Config 2022, neobrutalism.dev, Linear Design Awards, Vercel Ship.

## Surface treatment

**Color** - Ink pure `#000000`, paper `#FFFDF5` warm or `#FFFFFF` pure. One *primary* chromatic accent committed up-front from: yellow `#FFD23F`, hot-pink `#FF6B9D`, electric-blue `#74B9FF`, lime `#BFFF00`, lilac `#C3B1E1`. At most one *secondary* accent. Three or more accents on one screen is the AI tell. Greys are forbidden in body work - only `#F4F4F0` paper-shade allowed as a soft divider. One full-bleed saturated section per page is allowed; never gradients, never patterns other than a 24px black-dot grid.

**Type stack** -
- Display: Archivo Black 800 OR Syne 800 OR Whyte Inktrap (hero, card titles, CTA labels). Two-display-face mixing is forbidden - pick one shouter.
- Structural: Space Grotesk 700 (section eyebrows, mid-size headings).
- Body: Inter 400 - "boring on purpose," kept calm so the display can shout.
- Mono: Space Mono 400/700 (price tags, code, tabular numbers).

**Sizes** - 12 / 14 / 16 / 24 / 40 / 72 / 120. The gap between body 16 and display 72 IS the genre; intermediate 28-36 hero sizes signal drift toward SaaS.

**Line-height** - Display 0.95-1.05 (crowded), body 1.5 (calm), button labels 1.1.

**Letter-spacing** - Display `-0.02em` to `-0.04em`, body 0, uppercase eyebrows `+0.06em`.

**Radius** - `0` everywhere. Cards, buttons, inputs, images, avatars. Any value above `0` quits the genre. Pills `border-radius: 9999px` are forbidden even on tags.

**Borders** - `2px solid #000` on chips/badges, `3px solid #000` default (cards, buttons, inputs, images), `4px solid #000` on hero modules and primary CTAs. Border color is always pure black, never `#222` or `oklch(20% 0 0)`.

**Shadow** - Hard-offset, zero blur, pure black:
- `--shadow-sm: 3px 3px 0 0 #000` - chips, badges
- `--shadow: 5px 5px 0 0 #000` - cards, buttons
- `--shadow-lg: 8px 8px 0 0 #000` - heroes, modals
- `--shadow-xl: 12px 12px 0 0 #000` - single hero card per page

Shadow blur > 0 is the failure mode.

**Decoration** - Sticker-style inline SVG (hand-drawn squiggles, stars, arrows, asterisks) at `stroke: 3-4px #000` placed at deliberate angles (`rotate(-8deg)`), one or two per section, often overlapping card borders. Halftone dot fills as section backgrounds acceptable. Lucide icons are forbidden (their 1.5px stroke betrays the system). Emoji as decoration acceptable only at oversized scale (96px+) treated as a graphic, never inline with text.

**Motion budget** - The press interaction only:
- Button hover: `transform: translate(-2px,-2px); box-shadow: 7px 7px 0 0 #000;` in `0.1s ease-out`
- Active state: `transform: translate(3px,3px); box-shadow: none` (the card lands flush)

Forbidden: spring physics, cubic-bezier easing curves, scroll-driven parallax, fade-in entrance animations, hover lift with diffused shadows. The press interaction is the *only* motion.

## Failure mode

Every element gets identical `5px 5px 0 0 #000` shadow → floating-card chaos with no hierarchy. Four accents on one page instead of one committed chromatic. Soft drop shadow (`0 2px 8px rgba(0,0,0,0.1)`) leaking back in. `border-radius: 8px` on "just the buttons." Lucide stroke-1.5 icons dropped in. Inter 14px doing all type work with no Archivo Black 800 display contrast (the gap IS the genre). Yellow `#FFE500` text on white failing 4.5:1. The press interaction missing, so cards look pasted rather than liftable.

**The single tell: any `box-shadow` with non-zero blur.**

## Best for

Indie creator tools, bootstrapped SaaS landing pages, design-tool marketing, dev-tool conf pages, open-source project sites, music/podcast/festival microsites, no-code platforms, GenZ DTC - anything that wants to read as "made by people, not committees." Refuse for finance, healthcare, enterprise dashboards, or any product where information density beats personality.

## Pairs well with

- Shells: shell-hero-stack, shell-bento-grid, shell-centered-column, shell-editorial-broken-grid, shell-masonry, shell-mobile-app, shell-top-bar-canvas (sidebar-shells like shell-three-column-app are a poor fit - this style lives on landing pages and dashboards-as-marketing, not in inspectors)
- Aesthetics: aesthetic-neubrutalism, aesthetic-y2k-memphis-loud, aesthetic-corporate-memphis, aesthetic-wacky-pomo, aesthetic-curly-girly, aesthetic-acid-design

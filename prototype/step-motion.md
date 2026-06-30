# Step ten - motion budget

Motion happens because *data is changing* or *the genre demands it*. Never as decoration.

Common defaults:
- Hover transitions: `0.12s` on `background`, `border-color`, `opacity`.
- State changes (selection, active): `0.15-0.2s`.
- Streaming/progress: `transition: width 0.4s ease`.
- Live signal: one ambient keyframe on a "running" indicator.

Genre overrides:
- **Marketing / portfolio**: scroll-driven entrance animations expected. `IntersectionObserver` or `animation-timeline: scroll()`.
- **Brutalist**: zero animation. No transitions, even on hover.
- **Editorial**: a single subtle parallax on hero imagery acceptable; nothing else.
- **iOS / Material**: spring-easing on state transitions, never on entrance.
- **Product UI / dashboards**: motion only for changing data. Never on entrance.
- **Scrapbook mode** (raster-collage aesthetics - vaporwave / cottagecore / Y2K / dreamcore / zine, built with `shell-scrapbook-substrate` + `style-raster-cutout`): motion is *expected and maximalist*, not budgeted away. Three moves:
  - **PNG-sequence "key visual" (the transparent-GIF substitute) - at least one per page.** Transparent animated GIFs aren't reliably generated, so a looping element is built as N rembg'd still frames (each one a `raster-foreground` generation) stitched into a CSS sprite-sheet (`steps()` `background-position` animation) or a small JS frame-swap loop. Use it for the live twitch a static collage misses: a chrome bust rotating, a glitter divider sparkling, a blinking cursor under the title, a lantern flickering. Commit the sequence intent + frame count + frame rate up front. `prefers-reduced-motion` → freeze on frame 0.
  - **Ambient drift on cutouts**: slow continuous `translate`/`rotate` keyframes (different durations per element so they never sync), plus idle wobble/twinkle, so the page reads as alive rather than a frozen paste-up.
  - **Hover-tilt + scroll-parallax** on cutouts (hand to `interactive-polish` or the scrapbook interactions pass). The register (still-with-twitches / drifting-ambient / aggressive-vaporwave) is committed by the brief; aggressive ≠ chaotic - bound it to the aesthetic's easing.

---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: recipe-jp-corporate-recruit-ui.png
    reason: Full recipe UI mockup.
  - src: recipe-jp-corporate-recruit-isolated.png
    reason: Signature scene, isolated.
---
# Japanese corporate recruit (white-pop hiring one-pager)

A `(shell + style + aesthetic + voice)` bundle for the contemporary Japanese
recruiting-site genre — the systematized, optimistic, two-accent hiring
one-pager — abstracted to be language-agnostic (any label-script/content-script
pair). Two of the surveyed reference sites (daishin-s.co.jp,
recruit.sanso-gifu.jp) ship this genre on an identical agency token framework:
it is a real, repeatable genre, not a one-off.

## Picks

- **Shell:** `hero-stack` — read `shell-hero-stack.md`. Long single page:
  hero → about → numbers → people → business → jobs/FAQ → dual CTAs, with
  alternating white/tinted section bands.
- **Style:** `flat-design` host + `style-two-register-heading` (the heading
  system IS the skeleton) + `style-micro-text-frame` or `style-outline-marquee`
  for slogan ribbons at section seams.
- **Aesthetic:** `aesthetic-jp-recruit-pop` — read its file for palette,
  modules, and failure modes.
- **Voice:** aspirational-declarative; stable section-label vocabulary
  (ABOUT / WORKS / PEOPLE / RECRUIT); verifiable numbers everywhere the
  genre allows (founded, head count, average age, projects/year).

## Signature modules (the genre checklist)

- **Hero:** photo slideshow under fixed copy, or a 6–12s vector title film
  with SKIP chip (`motion-threshold-ritual`, title-film variant)
- **"Company in numbers" stat band:** icon + display-size numeral + small
  unit, 4–8 cards in a row — load-bearing; never cut it
- **Employee interview carousel:** real-people photography, name/role
  micro-labels, swipeable
- **Business/division slider:** illustrated panels; bonus register if prev/next
  scrub the illustration animation forward/backward
- **Marquee slogan loop** at 1–2 section seams, optionally mirrored double-band
- **Dual entry CTAs:** two equal-weight application paths color-coded to the
  two accents, pinned or in a closing band

## Best for

Careers/recruiting sites, employer-brand pages, mid-size company corporate
sites, trade/manufacturing/service brand launches — "friendly + trustworthy +
organized + a bit loud."

## What distinguishes this from existing recipes

- `swiss-grid` is austere and editorial; this is warm, banded, and pop —
  but equally token-disciplined.
- `bento-marketing` celebrates the product in cells; this celebrates the
  COMPANY in modules (numbers, people, divisions).
- Western SaaS recipes lead with the product screenshot; this genre leads
  with people and proof-by-numbers.

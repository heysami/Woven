---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-jp-recruit-pop-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-jp-recruit-pop-isolated.png
    reason: Signature motif, isolated.
---
# Japanese recruit-pop corporate (aesthetic)

**Tag:** `aesthetic-jp-recruit-pop`

**Canonical references:**
- The contemporary Japanese corporate/recruiting-site vernacular (採用サイト
  canon) - agency-built recruit one-pagers for trade, manufacturing, and
  service companies (observed verbatim on daishin-s.co.jp and
  recruit.sanso-gifu.jp, both on the same agency token framework)
- Mid-size JP corporate rebrand sites (polaris-toyota.jp's service-brand
  variant; biccamera private-label promo pages)
- The genre's job-board ecosystem chrome (dual entry CTAs, herp/engage-style
  application funnels)

**NOT to be confused with:** `aesthetic-japanese-poster-layout` (the
photo-dominant editorial composition canon - quiet, Mincho-led, gallery
register). Recruit-pop is its commercial opposite: energetic, systematized,
illustration-friendly, signal-colored. Also not `aesthetic-corporate-memphis`
(Western SaaS noodle-people): recruit-pop is denser, token-disciplined, and
photography-of-real-employees-forward.

## Cultural identity

The register of the modern Japanese company persuading 22-year-olds to join:
optimistic, loud-but-orderly, deeply SYSTEMATIZED. White ground, two signal
accents (classically red + deep blue, or the company's brand pair), pill
geometry everywhere, marquee slogan loops in a second script, stats rendered
as a proud dashboard, employees photographed mid-laugh. The energy of a
school-festival poster run through a corporate design system - every loud
element sits in a token grid (radius tiers, mono ramps, sub-hue sets).

Language-agnostic core: a **white-field pop system with a strict token
skeleton** - the secondary script supplies the decorative register (slogans,
eyebrows, marquees) while the primary script does the work. Any
label-language/content-language pair reproduces it.

## Palette anchor

- Ground: white `#FFFFFF` or warm off-white `#F7F7F4`, with one pale tinted
  band color (lavender `#F4F2F5`, ice blue `#EDF9FD`) for section alternation
- Two signal accents, used structurally: e.g. red `#EC0A1B` + royal blue
  `#0042BC` (the observed canon even uses blue as BODY text color), or the
  brand's primary pair
- A disciplined mono ramp (`#F2F2F2` → `#333841`) and a 4-6 color sub-hue set
  reserved for category chips and illustration
- Optional single high-voltage CTA accent (acid yellow `#E1FF00`) - one
  element only

## Composition principles

1. **Long hero-stack with section banding.** Hero (photo slideshow or vector
   title film) → about → numbers → people → business → jobs → FAQ → dual CTAs.
   Alternating white/tinted bands chapter the scroll.
2. **Two-register headings throughout** (see `style-two-register-heading`):
   condensed eyebrow label + large heading, identical component every section.
3. **"Company in numbers" stat band:** icon + huge numeral + small unit cards
   in a row - the genre's signature module. Numerals get the display face.
4. **People carousel:** employee interview cards with real photography,
   name/role micro-labels, horizontally swipeable.
5. **Marquee slogan loops** at section seams - outline or solid micro-text
   ribbons (see `style-micro-text-frame` / `style-outline-marquee`), sometimes
   mirrored `scaleY(-1)` into double-bands.
6. **Pill geometry:** radius tokens at 3 tiers (cards ~12px, chips ~8px,
   buttons 100vmax pills). Hard corners are off-register.
7. **Dual entry CTAs** pinned or footered: two equal-weight application paths
   (e.g. graduate / mid-career), color-coded to the two accents.

## Voice register

Declarative, aspirational, second-person-inviting. Slogan lines in caps
display ("POWER YOUR VALUE."), section labels as stable vocabulary (ABOUT /
WORKS / PEOPLE / RECRUIT), body copy warm but factual (founding year, head
count, average age - the genre LOVES verifiable numbers). Never ironic, never
lowercase-defiant.

## Raster requirement

Real-people photography carries trust: employee portraits and on-site work
shots, bright and candid. Vector illustration (flat, friendly) substitutes for
process diagrams and business-domain explainers. Without either, the genre
collapses into empty banding - follow the raster decision tree before drawing.

## Failure mode

First tell: art-directing each section differently - the genre's power IS the
token repetition; per-section creativity reads as a portfolio, not a company.
Second tell: three+ accents loose on the page (accents are structural: one
per entry path, period). Third tell: stock-photo Westerners laughing at
salads - the photography must read as THIS company's actual people/site.
Fourth tell: dropping the stats band or rendering numerals in body type - the
proud-dashboard module is load-bearing. Fifth tell: dark ground (this register
is daylight; dark recruit sites are a different genre entirely).

## Best for

- Recruiting/careers sites and employer-brand one-pagers
- Mid-size company corporate sites wanting energy without chaos
- Service-brand launch pages (trades, logistics, manufacturing, retail PB)
- Any brief: "friendly + trustworthy + organized + a bit loud"

## Pairs well with

- **Shells:** `shell-hero-stack` (canonical)
- **Styles:** `style-flat-design` (host), `style-two-register-heading`,
  `style-micro-text-frame`, `style-outline-marquee`, `style-bold-display`
- **Recipes:** `recipe-jp-corporate-recruit` is this aesthetic pre-bundled

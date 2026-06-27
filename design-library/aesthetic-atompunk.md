---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-atompunk-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-atompunk-isolated.png
    reason: Signature motif, isolated.
---
# Atompunk (aesthetic)

**Tag:** Fallout Pip-Boy + RobCo terminal · NASA Worm-era brand system · Tomorrowland / 1964 World's Fair · Googie architecture · mid-century Coca-Cola atomic ads

**Canonical references:**
- **Fallout Pip-Boy / RobCo terminal** - the phosphor-CRT survival-bunker dialect; amber or green monochrome, ASCII chrome, military-civic register.
- **NASA Worm-era brand system (1975-1992)** - Danne & Blackburn's institutional Helvetica grid; hairline rules, Pantone 185 red as sole accent, zero ornament.
- **1964 New York World's Fair / Disney Tomorrowland** - chrome-and-teal optimism, Eurostile signage, starburst finials, boomerang cutouts.
- **Googie architecture (Armet & Davis, mid-century LA)** - atomic-orbit motifs, cantilever roofs, neon, the diner-coffee-shop futurism.
- **Mid-century atomic-age advertising (Coca-Cola, GE, Westinghouse, ~1955-62)** - Coca-Cola red on butter-cream, half-tone dot-screens, exclamatory ad-copy.

## Cultural identity

Atompunk is the *retro-future of 1945-1969*: the optimism (and dread) of the atomic age before Vietnam soured it. It's the aesthetic of bomb-shelter civics, Sputnik panic, Kennedy-era moonshot ambition, Cold-War civil-defense pamphlets, and tail-fin Cadillacs. Three sub-dialects share the era but never the page - pick one and commit:

- **Pip-Boy / bunker-CRT** - phosphor monochrome, survivalism, military procedural.
- **Tomorrowland / Googie** - chrome optimism, starbursts, "the future is friendly."
- **NASA-Worm / institutional** - Helvetica grid, agency calm, hairline rules, the engineer's restraint.

The Coca-Cola-atomic ad register (butter-cream + red + exclamatory copy) is a fourth note that can flavour the Tomorrowland dialect, never the Pip-Boy one.

## Palette anchor

Phosphor primaries (pick ONE per Pip-Boy page): amber `#ffb000`, sodium green `#33ff33`, Fallout-4 lime `#9eff5e`.

Atomic-ad palette: Coca-Cola red `#c72d04`, turquoise `#3ec1bf`, coral `#ff8a65`, butter-cream `#f1e4b7`, chrome `#c2c2c2`, deep-space navy `#21233a`.

NASA-Worm: Pantone 185 red `#FC3D21` as the SOLE chromatic accent on white.

Grounds: Pip-Boy `#0a1410` or amber-CRT `#1a0e00`; Tomorrowland deep plexiglass teal `#0d2a3a` or chrome silver. Never warm paper, never pure `#000`, never neutral grey `#6b7280`.

## Decoration motifs

Use ONE per page, never repeated as button-backs or bullets:

- Atomic-orbit (3 ellipses crossing at 60°).
- Googie starburst (8-spoke radial with terminal dots).
- Boomerang cutout.
- Sputnik silhouette + radio-wave arcs.
- ASCII art splash on terminal boot (Pip-Boy only).
- Vintage half-tone dot-screen over photography (Coca-Cola sub-variant only).

Period-correct chrome must be consistent: CRT bezel (Pip-Boy), chrome bar (Tomorrowland), or Helvetica hairline rule (NASA) - pick one. Never Lucide icons; a single Lucide glyph collapses the genre.

## Voice register

- **Pip-Boy** - ALL-CAPS terse military-civic: "AUTHORIZATION REQUIRED", "RAD LEVEL: NOMINAL", "EXECUTE Y/N".
- **Tomorrowland** - optimistic infinitive: "EXPLORE TOMORROW", "DESTINATION: MOON".
- **Coca-Cola-atomic** - exclamatory mid-century ad-copy: "REFRESHING! ATOMIC! NEW!"
- **NASA-Worm** - factual past-tense: "STS-1 launched April 12, 1981."

Never Slack-casual, never lowercase-defiant, never emoji.

## Failure mode

Lime-`#00ff00`-on-black VT323 with 50%-opacity scanlines and `text-shadow: 0 0 20px` bloom on every glyph, plus a Lucide gear icon in the corner = "AI Pip-Boy cosplay" reading as a broken venetian blind over a generic dashboard. Or starburst-behind-every-button + Pacifico script "Atomic!" + radial pink-to-orange gradient + clip-art Sputnik = mid-century ad-pastiche dump. Tasteful atompunk picks ONE sub-variant, uses period-correct type (Eurostile / Microgramma / Bank Gothic / VT323 - never Inter, never Pacifico), keeps phosphor bloom at 4-6px on headings only, scanlines at 4-8% opacity, and uses exactly one orbit-or-starburst motif per page. Reach for Inter, a Lucide icon, a soft drop shadow, or a 12px SaaS radius and you've quit the genre.

## Best for

Nuclear-history museums, space-agency archives, retro-gaming companion apps, mid-century-modern hospitality (motels, diners, tiki bars), sci-fi convention sites, alt-history fiction projects, defense-contractor parody, Cold-War civics simulators, vintage-soda DTC, classic-car restoration shops, bomb-shelter survivalist e-comm.

## Pairs well with

- Shells: `shell-terminal-frame` (Pip-Boy), `shell-top-bar-canvas` (Tomorrowland chrome bar), `shell-centered-column` (NASA-Worm institutional), `shell-three-column-app` (RobCo terminal data layout), `shell-bento-grid` (Coca-Cola-atomic editorial)
- Styles: `style-flat-design` (NASA-Worm hairline), `style-skeuomorphism` (Tomorrowland chrome bevel), `style-dense-mono-dark` (RobCo data screens), `style-oversized-neo-grotesque` (Eurostile display)

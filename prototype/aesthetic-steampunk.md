---
# Sample-image references for the System-tab design library. Images sit
# next to this file in prototype/ and were generated via image_gen.
images:
  - src: aesthetic-steampunk-ui.png
    reason: Generated UI mockup committing this aesthetic's vocabulary at a usable density — palette, type tone, decoration motifs in context.
  - src: aesthetic-steampunk-isolated.png
    reason: Isolated subject sample — the aesthetic's signature motif / texture / illustration treatment on a neutral background.
---
# Steampunk (aesthetic)

**Tag:** Steampunk UI (Bioshock Infinite / Columbia HUD, Frostpunk generator dashboard, Steampunk World's Fair posters, Dishonored 2 menus, Design Observer's Nakamura critique)

**Canonical references:**
- Bioshock Infinite / Columbia HUD — riveted instrument plates, brass-on-parchment chrome done with restraint
- Frostpunk generator dashboard — circular gauges as the central narrative object
- Steampunk World's Fair posters — Edwardian wood-type and double-rule letterpress lineage
- Dishonored 2 menus — engraved cartouche framing, ink-on-paper hierarchy
- Design Observer's Nakamura critique — the canonical takedown of "brass + woodgrain = Victorian"

## Cultural identity

Steampunk is the alt-history retrofuturism of a Victorian / Edwardian world that kept building on steam, brass, and analog instrumentation instead of electricity and silicon. It comes out of late-1980s sci-fi (Gibson & Sterling's *The Difference Engine*), peaked in the 2000s–2010s through Bioshock Infinite, *The Prestige*, and the Steampunk World's Fair, and matured into the considered industrial-letterpress register of Frostpunk and Dishonored 2.

The aesthetic is **engineering as ornament**: a world where the mechanism is visible, the dial is brass, the manual is letterpressed, and the engineer is a gentleman-naturalist. Not "Victorian costume" — Edwardian *industry*: ledgers, pressure gauges, almanacs, observatory logs, telegraph dispatches.

## Palette anchor

- Aged parchment `#EFE2C8` (light) / oil-darkened leather `#1F1B17` (dark) — the substrate
- Warm near-black ink `#2A201B` — body type, never pure black
- Antique brass `#B08D57` — the one chrome accent
- Coal-ember amber `#E09F3E` — reserved for alarm / critical state
- Blueprint cyan `#2F6F8F` — schematic callouts and technical overlays

All greys are **warm low-chroma** (`oklch(50% 0.015 55)`), never neutral — neutral grey is the dead giveaway of a stock UI kit pretending to be Victorian.

## Decoration motifs

The vocabulary that signals steampunk without slipping into costume:

- **Corner cartouches** — hand-drawn brass filigree at the four corners of one signature panel
- **Double-rule dividers** — the Edwardian letterpress move between sections
- **Schematic blueprint callouts** — leader-dot lines with uppercase agate labels overlaying a diagram
- **Circular pressure gauges** — the one place a `border-radius: 9999px` is earned
- **Engraved nameplates** — small-caps display type with letterpress emboss (`text-shadow` highlight + shadow)
- **Tabular oldstyle figures** — gauge readouts in tabular lining figures; flowing body in oldstyle

**The single-move rule:** pick *one* decoration motif per page. Cartouches OR rule-pairs OR schematic callouts — never all three.

**Forbidden vocabulary:** spinning gear loaders, goggles-and-tophat logos, riveted edges on form inputs, woodgrain tiled backgrounds, leather-stitching trim that isn't part of the palette, anything with "cog" or "brass" in the class name.

## Voice register

Edwardian-formal but plain. The engineer's logbook, not the LARP scroll.

- "Pressure: nominal." / "Boiler at 84%." / "Cable severed."
- "The dispatch arrived at 14:22."
- Specimens, readings, observations, dispatches.

Never: "Aetheric," "Cogworthy," "Brassmonger," "By steam and gear." No exclamation marks. The word "punk" never appears in any copy.

## Failure mode

Pinterest-steampunk / scrapbooking masquerading as design. The Nakamura formula: **brass-frame PNG on every card + woodgrain tiled background + a rotating SVG cog as the loading spinner + Algerian at every size + drop-shadow on every panel + a goggles-and-tophat logo + "Aetheric" in the copy.**

The single AI tell: any element with `animation: spin` applied to a gear glyph. The second tell: a global `filter: sepia()` instead of warm palette tokens.

## Best for

- Alt-history game UI and fictional instrument panels
- Victorian-museum, industrial-heritage, or maritime microsites
- Brewery, distillery, and apothecary brands with Edwardian provenance
- Immersive-theatre and live-event identities (Sleep No More lineage)
- Retrofuturist hardware marketing — mechanical keyboards, analog synths, brass-bodied audio gear
- TTRPG and LARP companion apps
- Observatory, almanac, and logbook-style data dashboards

## Pairs well with

- **Shells:** shell-centered-column (ledger / dispatch), shell-bento-grid (instrument panel cluster), shell-canvas-floating (single circular gauge centerpiece), shell-three-column-app (logbook + dispatch + reading pane), shell-top-bar-canvas (instrument console)
- **Styles:** style-serif-warm-paper (the natural substrate), style-dense-mono-dark (oil-darkened leather variant), style-skeuomorphism (when gauges become literal), style-restrained-hairline (when the brass is pulled back to a single rule)

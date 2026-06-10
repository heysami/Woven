---
# Sample-image references for the System-tab design library. Images sit
# next to this file in prototype/ and were generated via image_gen.
images:
  - src: aesthetic-anti-design-ui.png
    reason: Generated UI mockup committing this aesthetic's vocabulary at a usable density — palette, type tone, decoration motifs in context.
  - src: aesthetic-anti-design-isolated.png
    reason: Isolated subject sample — the aesthetic's signature motif / texture / illustration treatment on a neutral background.
---
# Anti-design (Dieter Rams orthodoxy) (aesthetic)

**Tag:** `aesthetic`

**Canonical references:**
- Vitsoe.com — the living catechism; 606 shelving sold like a tax form
- Muji.com — the Japanese translation of Rams; warm off-white, no theatre
- Braun / Das Programm archive — the source code (ET66, T3, SK4 "Snow White's Coffin")
- Lineto.com / ABCDinamo.com — type foundries that practice what Rams preached
- Naoto Fukasawa for Muji — "without thought" as a design discipline

## Cultural identity

Anti-design is the orthodoxy of "as little design as possible" — Dieter Rams' ten principles applied as moral code, not style. Its lineage runs Ulm School (1953) → Braun (1955–1995) → Vitsoe (1959–present) → Muji (1980–present) → contemporary practitioners (Jasper Morrison, Naoto Fukasawa, Konstantin Grcic). The aesthetic peaked twice: once in the 1960s–70s with Braun's domestic appliances, and again in the 2000s–10s as a corrective to Web 2.0 gloss and skeuomorphism.

It is a **daylit, Northern European, bourgeois-utilitarian** sensibility — Protestant in its restraint, Bauhaus in its lineage, but warmer than either. The reader is assumed to be literate, patient, and able to read 14px body copy without complaining. It signals: this object will outlast trends; the maker is confident enough to not shout; the catalogue is the experience.

Distinct from **Swiss modernism** (which is grid-religious and corporate) and **brutalism** (which is loud about its restraint). Anti-design is restraint that doesn't announce itself.

## Palette anchor

A warm, daylit neutral ground with **one** disciplined accent reserved for action:

- **Ground** — Braun warm white `#F0EDE5` or Muji off-white `#FAF7EB` (never pure `#FFFFFF`)
- **Text** — warm black `#1A1A18` (never `#000`)
- **Hairline** — `#C5C3BE` for rules and dividers
- **One accent**, used sparingly for actionable elements only:
  - Vitsoe orange `#D9521B`
  - Muji crimson `#7F0019`
  - Braun signal red `#C02820`
  - Function yellow `#D4B018` (status pip only)

Dark mode is heretical — the orthodoxy is daylit.

## Decoration motifs

- Generous whitespace as a positive compositional element (not absence — presence)
- Square product photography on flat ground, shadowless
- Numbered lists, footnotes, monospaced metadata
- Hairline rules as the only divider; never doubled, never colored
- Wordmark only — no logo lockup, no mascot, no illustration system
- Tabular data presented as tables, not as cards
- **Forbidden:** gradients, glows, decorative icons, emoji, drop-caps, background patterns, glass blur, neumorphism, parallax, hover-lift, fade-in-on-scroll

## Voice register

Declarative, unadorned, sentence-case. Reads like a Vitsoe inquiry email or a Muji product tag:

> "606 desk shelf. Steel, powder-coated. Made in England."
> "Cotton. Unbleached. 120 g/m²."

No exclamation marks. No "Discover" or "Unleash." No second-person hype. Metadata labels may be uppercase tracked, but body copy is lowercase or sentence-case. The product, the price, the dimensions, the material — in that order.

## Failure mode

The AI tell: pure `#FFFFFF` ground instead of Braun warm white; Inter or Geist where Akkurat or Helvetica belong; iOS-blue CTA where a single disciplined orange/crimson belongs; the accent sprayed across every icon and heading instead of reserved for one operational control per view; any `box-shadow` at all; rounded corners above 2px; hover-lift animations; a 72px display headline (which would violate "as little design as possible"); marketing voice ("Discover the perfect…") instead of catalogue voice.

The cheap version reads as Stripe-clone minimalism. The real thing reads as something a German industrial engineer signed off on.

## Best for

- Furniture catalogues and configurators
- Architecture and industrial-design portfolios
- Hi-fi and audio-equipment archives
- Stationery, writing-tools, and small-batch goods
- Slow-fashion and tailored menswear
- Public-library and museum-collection sites
- B2B documentation written for engineers
- Anything sold to people who own a Braun ET66 and would notice if you got it wrong

## Pairs well with

- **Shells:** `shell-centered-column`, `shell-two-column-app`, `shell-hero-stack` (used soberly, no hero), `shell-bento-grid` (only with hairlines, no shadows)
- **Styles:** `style-restrained-hairline`, `style-cream-humanist`, `style-oversized-neo-grotesque` (toned down), `style-flat-design`

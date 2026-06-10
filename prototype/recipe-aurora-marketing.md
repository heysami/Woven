---
# Sample-image references for the System-tab design library. Images sit
# next to this file in prototype/ and were generated via image_gen.
images:
  - src: recipe-aurora-marketing-ui.png
    reason: Generated UI mockup of this recipe end-to-end — the canonical (shell + style + aesthetic + voice) bundle rendered.
---
# Aurora marketing

A `(shell + style + voice)` bundle for **modern protocol / AI-tooling / infrastructure marketing pages** that use mesh-gradient atmosphere as the dominant brand signal.

## Picks

- **Shell:** `hero-stack` — read `shell-hero-stack.md`
- **Style:** `aurorism` — read `style-aurorism.md`
- **Aesthetic:** *(none — surface-driven brand identity)*
- **Voice:** declarative product-truth, technical confidence, no marketing exclamation. Headlines as statements ("Payments infrastructure for the internet" / "The home of onchain finance"). Sentence-case nav, lowercase brand wordmark, terse feature labels.

## Pattern

- Single hero section at first viewport — large mesh-gradient blob behind oversized neo-grotesque or geist-style headline + one-sentence sublede + primary CTA
- Mesh-gradient appears **once** at hero; body sections drop to 99% achromatic with hairline dividers
- Optional secondary mesh bloom at a closing CTA
- Live data / agate-numeric metric strip is common (TPS, TVL, uptime, requests/sec)
- 3D-rendered geometric hero object (crystal, network globe, blockchain mesh) often sits in the gradient field
- Section padding `96–160px` top/bottom (marketing rhythm)

## Best for

Layer-1 / Layer-2 protocol marketing, AI-tooling landing pages, modern developer-infrastructure SaaS, payment-rail and on-chain-finance protocols, foundation-model marketing — anywhere the brand-truth wants to read as "infrastructure, not app" but still feel atmospheric.

## What distinguishes this from existing recipes

- `bento-marketing` uses bento-grid cells with bold-display copy — this is hero-stack with aurora atmosphere.
- `linear-product-ui` is the app surface, not the marketing-for-the-app surface.
- Bloomberg dashboard is a tool, not a marketing scroll.

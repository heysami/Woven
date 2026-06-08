# Oversized neo-grotesque (style)

**Tag:** `style-oversized-neo-grotesque`

**Canonical references:** Bureau Borsche · Pentagram · Studio Dumbar · Aktiv Grotesk Extended specimens · Söhne Breit specimens

## Surface treatment

Display type is the surface. Hero-scale neo-grotesque sits on a flat ground (pure white or pure black, matched to the work's identity — never warm paper). No shadows, no radii, no chrome — the optical event is letterforms crowding the frame.

**Palette**
- Ground: `#FFFFFF` or `#000000` — pure, no warm cast
- Ink: matched to ground (`#000` on white, `#FFF` on black)
- Greys: 0-chroma greyscale only — `#111`, `#666`, `#A8A8A8`, `#E8E8E8`
- Accent: per-piece, picked from the subject's own identity; **no system-wide accent** carried across the page

**Type stack**
- Display: oversized neo-grotesque — Söhne Breit, Akzidenz-Grotesk Extended, Aktiv Grotesk Extended, GT America Extended
- Body: utilitarian sans — Söhne, Inter, Maison Neue
- Mono (labels / metadata only): GT America Mono, Maison Neue Mono
- Never: a display-sans + decorative-sans mix; never a serif anywhere

**Sizes** (px): 11 / 14 / 18 / 96 / 160 / 240 — display sizes carry the page, body is minimal connective tissue.

**Letter-spacing:** `-0.04em` on display (tight enough to crowd), `+0.04em` on uppercase labels.

**Line-height:** `0.9` on display (lines kiss), `1.4` on body.

**Radius:** `0` everywhere. No pills, no rounded tiles, no rounded inputs.

**Borders:** hairline `1px` on data tables and metadata strips only. Otherwise none.

**Shadow:** none. No drop shadow, no inner shadow, no glow.

**Gradients / blur:** none.

## Decoration grammar

- Mandatory: display type at hero scale; uppercase mono labels (`CLIENT, YEAR, DISCIPLINE`); hairline rules between metadata rows.
- Forbidden: rounded corners, drop shadows, soft pills, gradient buttons, Lucide-style icons, emoji, illustrative decoration, marketing CTAs.

## Motion budget

- Instant or `0.15s` linear cross-fades on image swaps.
- Marquee on running text is acceptable (constant velocity, never eased).
- Forbidden: `cubic-bezier` micro-interactions, hover lifts, scale-on-hover, spring physics, scroll-linked parallax. Anything that smells like a SaaS landing page.

## Failure mode

Small Lucide icons in a sidebar, soft drop shadows on tiles, an `8px` border-radius "Get in touch" CTA pill, an accent gradient swept across the index — SaaS-disguised-as-studio. Any button labelled "Learn more" or "Get started" means the surface has collapsed into marketing template.

## Best for

Design studios, fashion houses, cultural identities, sports brands, art-director portfolios, magazine masthead pages, exhibition microsites — anywhere the subject's own identity should out-shout the container.

## Pairs well with

- Shells: `shell-editorial-broken-grid`, `shell-masonry`, `shell-hero-stack`, `shell-bento-grid`, `shell-centered-column`
- Aesthetics: `aesthetic-swiss-modernist`, `aesthetic-anti-design`, `aesthetic-neubrutalism`, `aesthetic-bauhaus`, `aesthetic-constructivism`

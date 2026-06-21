---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-chinese-curated-modernist-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-chinese-curated-modernist-isolated.png
    reason: Signature motif, isolated.
---
# Chinese curated-modernist (Guizang lineage) (aesthetic)

**Tag:** `aesthetic-chinese-curated-modernist`

**Canonical references:**
- **Guizang PPT skill repository** (github.com/op7418/guizang-ppt-skill) - the canonical curated grammar that defines this aesthetic
- *Monocle* magazine editorial layouts - direct ancestor for the e-ink editorial mode
- Massimo Vignelli + Müller-Brockmann Swiss modernist tradition - direct ancestor for the structured-grid mode
- Wallpaper* Magazine sophisticated editorial spreads
- Chinese contemporary brand-book design - Bananain, Documents, NEIWAI, Songmont editorial pages
- Chinese poster-design community on Xiaohongshu / 站酷 (Zcool) that consciously rejects red-lantern / dragon clichés

**NOT to be confused with:** red-and-gold "Chinese style," dragons, qipao motifs, kung-fu typography, Beijing-Olympics ceremonial visuals. This entry is the OPPOSITE - contemporary Chinese designers reinterpreting Western modernist + magazine traditions through their own taste discipline.

## Cultural identity

This is the curated aesthetic championed by Chinese designers like **Guizang (op7418)** and his community - a contemporary Chinese visual discipline that fuses two well-defined imported traditions and constrains them rigorously. The cultural reading: this is what modern Chinese taste looks like when it consciously *refuses* the dragons-and-cinnabar cliché.

Two parallel modes coexist within this aesthetic - they're sibling lanes, not variants. Pick one per project, never mix.

**Mode A - Editorial Magazine × E-ink:** Monocle-magazine layout sensibility (long-form serif, sparse photo placement, sober color blocking) crossed with electronic-ink palette restraint. Reads as journalistic, considered, "viewpoint expression through restraint."

**Mode B - Swiss International Modernism (Chinese-curated):** Vignelli-Müller-Brockmann discipline applied with absolute fidelity - 16-column grid, zero shadows, zero gradients, zero rounded corners, hairline strokes only, extreme typographic size contrast. The Chinese curatorial signature is the **saturated single-color anchor** (one intense chromatic per layout, never a system of accents).

The Guizang grammar is famously constrained - *"constraint over customization, forbidding hex value modification to protect aesthetics."* That discipline IS the aesthetic. Loosen it and the whole register collapses.

## Palette anchor

Five named e-ink palettes (Mode A) - pick ONE per project, never customize:

- **Ink Classic:** ink `#0A0A0B`, paper `#F1EFEA`
- **Indigo Porcelain:** indigo `#0A1F3D`, porcelain `#F1F3F5`
- **Forest Ink:** forest `#1A2E1F`, cream `#F5F1E8`
- **Kraft Paper:** brown `#2A1E13`, kraft `#EEDFC7`
- **Dune:** charcoal `#1F1A14`, dune `#F0E6D2`

Four saturated chromatic anchors (Mode B) - pick ONE per project, never multiple:

- **Klein Blue IKB** `#002FA7`
- **Lemon Yellow** `#FFD500`
- **Lemon Green** `#C5E803`
- **Safety Orange** `#FF6B35`

NEVER mix modes. NEVER modify hex values. The constraint protects the aesthetic.

## Composition principles

- **Grid (Mode B):** 16-column, right angles only, hairline strokes 0.5-1px, ZERO skeuomorphism (no shadows, no gradients, no rounded corners, no blur).
- **Type:** extreme size contrast (display 96-200px → body 12-16px, no mid-sizes). Typically one Latin family + one Chinese family (Source Han Serif for editorial mode, Source Han Sans for modernist mode), absolutely no third typeface.
- **Image discipline:** images are first-class citizens locked into predefined slots at standardized aspect ratios - **21:9 primary, 16:10 secondary**. Never bespoke crop ratios. The framing IS the system.
- **Color saturation singularity (Mode B):** one chromatic per layout. Klein Blue OR Lemon Yellow OR Lemon Green OR Safety Orange - never two.
- **Restraint as the rhetoric:** the absence of decoration IS the gesture. No icons-for-decoration, no illustrated accents, no emoji.

## Voice register

Mode A: editorial, third-person, considered, slightly removed. "本期专题：城市边界" / "This issue: City boundaries."

Mode B: declarative, system-label, slightly clinical. "SECTION 04 / DATA / 2026"

Both modes: bilingual when audience is global (Chinese + English), monolingual when audience is domestic. Never warm-marketing, never lowercase-defiant, never emoji-decorated.

## Raster requirement

Both modes are photography-driven (Mode A) or photography-and-strict-geometry (Mode B). Photography must be commissioned or carefully curated. Stock images break the register instantly. Follow the [Raster requirements](../prototype.md#raster-requirements--when-svg-will-not-deliver-the-genre) decision tree before drawing.

## Failure mode

A red `#FF0000` plus gold `#FFD700` plus a dragon SVG plus a stylized 龙 character at 120px and a backdrop of distressed paper texture - this is cliché-Chinese cosplay, the exact opposite of this entry's brief. Refuse to deliver it under this tag.

Second tell: skeuomorphism in Mode B. Any shadow / gradient / rounded corner / blur breaks the Swiss-modernist contract immediately.

Third tell: multiple chromatic anchors on Mode B. Klein-Blue AND Lemon-Yellow on the same screen reads as "designer couldn't commit." The constraint is the point.

Fourth tell: Mode A and Mode B mixed on one project. They're sibling lanes - pick one per project, the whole thing or nothing.

Fifth tell: custom hex values. Guizang's grammar forbids modifying the palette. Loose hex = loose aesthetic.

## Best for

- Chinese tech / fintech sophisticated brand pages
- Cross-border premium brands wanting "considered Chinese taste, not stereotyped Chinese"
- Editorial / journalism in Chinese-language markets
- High-end product launches (consumer electronics, apparel, beauty)
- Museum / cultural-institution microsites in mainland China
- Conference / event sites where typographic and editorial discipline IS the brand
- Design-studio portfolios wanting to signal modernist-with-Chinese-restraint heritage

## Pairs well with

- **Shells:** `shell-editorial-broken-grid`, `shell-centered-column`, `shell-hero-stack`, `shell-two-column-app`, `shell-three-column-app`
- **Styles:** `style-swiss-modernist` (Mode B), `style-cream-humanist` (Mode A), `style-restrained-hairline`, `style-oversized-neo-grotesque`, `style-serif-warm-paper`

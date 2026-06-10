---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-vaporwave-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-vaporwave-isolated.png
    reason: Signature motif, isolated.
---
# Vaporwave (aesthetic)

**Tag:** Vaporwave UI (Macintosh Plus — Floral Shoppe; Vektroid / PrismCorp; 100% Electronica; Vapor95; One Terabyte of Kilobyte Age)

**Canonical references:**
- Macintosh Plus — *Floral Shoppe* (2011): the founding album cover; marble bust, magenta gradient, bilingual title.
- Vektroid / PrismCorp Virtual Enterprises: fake-multinational corporate-melancholic register.
- 100% Electronica (label + store): canonical commercial vaporwave with restraint.
- Vapor95: streetwear bootleg lineage — Win95 dialog chrome on apparel.
- One Terabyte of Kilobyte Age (Olia Lialina): the 1995-personal-homepage substrate that vaporwave mines.

## Cultural identity

Vaporwave is a 2010s internet-music subculture nostalgizing a 1990s consumer future that never arrived: Muzak, mall food courts, Sega Saturn intros, Windows 95 dialogs, late-night Japanese commercials, hotel lobby art. It's corporate-melancholic and bilingual-by-default — the visuals pose as a fake multinational catalog (English + Japanese) selling something vague. The mood is sincere irony: not laughing at the artifacts, but mourning them.

The defining gesture is the **bilingual title pair** (Latin display line + Japanese gloss), the **classical marble bust** (Helios, Apollo Belvedere, Venus de Milo) recoded as a duotone PNG, and the **sunset-to-night gradient** over a perspective grid. Times New Roman Italic body type is non-negotiable — it signals 1994 catalog, not retro-game.

**Palette anchor:** deep purple-near-black `#16043A` base, sunset gradient through `#6B2FBB` → `#E93479` → `#F9AC53`, neon accents magenta `#FF71CE`, cyan `#01CDFE`, lilac `#B967FF`, and marble cream `#F5EFE2`. Greys are warm-violet, never neutral.

## Motifs / imagery vocabulary

- **One classical marble bust** per screen, duotone-tinted pink/cyan, cropped left not centered.
- **Bilingual title pair** — Latin display caps + Japanese subtitle (Noto Sans JP / Shippori Mincho), ~0.85× the Latin size.
- Choose ONE secondary motif: horizon grid in cyan-on-black perspective, pink-and-black checkerboard band, palm-tree silhouette, or single sun-disc gradient.
- Win95 dialog window chrome as content frame (hard 1px bevels, not soft shadows) — optional.
- Fake-multinational catalog SKUs ("SAMPLE / 見本 / Cat. № 03") as labels.

**Raster required:** marble busts, Windows 95 dialog screenshots, palm-tree silhouettes, plaza-grid photography, VHS-grain overlays. Vaporwave without these is just purple gradient. Follow the [**Raster requirements**](../prototype.md#raster-requirements--when-svg-will-not-deliver-the-genre) decision tree in the main playbook.

## Voice register

Corporate-melancholic, bilingual, measured. Product names read like 1994 catalog SKUs. English copy is plain and slightly stilted, glossed by a single Japanese line. Never exclamatory, never "Buy now," never lowercase-defiant, never ironic-meme. The tone is a fake luxury brand whose ad agency went out of business in 1996.

## Failure mode

Pink-to-cyan linear gradient as the page background + a stock Michelangelo David PNG centered at 60% opacity + VT323 or Press Start 2P for body + a random katakana string pasted as a sticker + a global CRT scanline overlay + neon `text-shadow` on every label = album-cover-cosplaying-as-website. The cheap version stacks every signifier (palms + grid + checkerboard + statue + scanlines) on one screen. The tasteful version keeps Times New Roman Italic for body, ONE Helvetica Bold display line glowing, ONE marble cropped left, ONE bilingual pair, and uses the checkerboard as a 96px footer band — never the wallpaper.

## Best for

- Indie record labels, nightclub / rave promo pages.
- Mixtape, Bandcamp, and single-release landings.
- Fashion drops in the streetwear-bootleg lineage.
- Art-book and zine shops, satirical fake-corporate brand pages.
- Vaporwave-adjacent musicians' tour and merch sites.
- Niche art portfolios wanting the 1994-mall-catalog register.

## Pairs well with

- **Shells:** `shell-centered-column` (over a dark hero — canonical), `shell-hero-stack` (sunset hero + tracklist below), `shell-scrapbook-substrate` (Win95-desktop-frame variant with draggable windows), `shell-editorial-broken-grid` (album-as-magazine).
- **Styles:** `style-serif-warm-paper` inverted to dark (Times Italic body is the throughline), `style-skeuomorphism` (for the Win95 dialog chrome variant), `style-holographic` (for the neon-glow display headline accent), `style-raster-cutout` (for the marble bust + cropped photography handling).

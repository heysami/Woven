---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-synthwave-outrun-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-synthwave-outrun-isolated.png
    reason: Signature motif, isolated.
---
# Synthwave / outrun (aesthetic)

**Tag:** heroic neon-horizon retrofuturism

**Canonical references:**
- Kavinsky "OutRun" / College "A Real Hero" cover art - the founding album-sleeve grammar: grid, sun, chrome logotype.
- Drive (2011) titles and the synthwave scene it ignited - magenta script over night-drive dusk.
- Sega Out Run (1986) sunset horizon - the arcade source of the eternal drive-into-the-sun composition.
- FM-84 / The Midnight / Timecop1983 sleeve tradition - striped sun, mountain silhouettes, starfields.
- Retrowave GIF/poster corpus (NewRetroWave) - the codified layout: horizon at two-thirds, logo above, grid below.

## Cultural identity

The heroic night-drive fantasy: a **receding cyan wireframe grid** rushes toward a horizon where a **striped sun disc** sets behind black mountain silhouettes, the dusk graded magenta-to-indigo, and above it all a **chrome-extruded 3D logotype** leans forward like it is doing 140. The composition is fixed and sacred - grid below, sun on the horizon, title in the sky - and everything else in the interface plays supporting cast: components are thin neon-outline HUD panels in cyan, indigo panels with magenta fills, starfields in the upper dark. The mood is sincere heroism - a fantasy 1984 that never existed, driven toward, not mourned.

This is NOT `aesthetic-vaporwave` - vaporwave is corporate-melancholic irony, pastel and broken, quoting dead malls; synthwave is earnest and kinetic, quoting movie posters. And it is NOT `aesthetic-y2k-futurism` - no chrome blobs, no translucent plastics, no millennium optimism about technology; synthwave's future is the 80s' own dream of itself, rendered at dusk.

## Palette anchor

Dusk gradient with neon signals:
- Magenta `oklch(65% 0.26 350)` (#ff2e97)
- Violet `oklch(58% 0.25 300)` (#8a3dff)
- Indigo ground `oklch(28% 0.12 280)` (#1b1b6b)
- Cyan `oklch(85% 0.14 210)` (#00e5ff) - the grid and the HUD outlines
- Sun yellow `oklch(85% 0.15 85)` (#ffc84d) through sun orange `oklch(72% 0.19 45)` to sun pink `oklch(66% 0.23 20)` - the disc's banded gradient
- Silhouette black `oklch(8% 0.01 280)`

The sky is always a vertical magenta-to-indigo grade; the sun is always banded yellow-to-pink. Cyan belongs to structure (grid, outlines), magenta to emotion (sky, fills, script).

## Decoration motifs

- **Receding wireframe grid** - one-point-perspective cyan grid on the lower third, glowing at the horizon line.
- **Striped sun** - a huge disc with horizontal gaps, banded yellow-orange-pink, half-set behind the horizon.
- **Mountain silhouettes** - jagged pure-black ranges flanking the sun.
- **Chrome-extruded display type** - italic 3D lettering with gradient faces and deep extrusion, tilted toward the vanishing point.
- **Neon HUD outlines** - 1px cyan borders with soft glow on cards, inputs, and buttons; magenta gradient fills for primary actions.
- **Starfields and scanlines** - sparse stars in the upper sky; optional fine scanlines over the whole frame.
- **Diamond separators** - small lozenge glyphs between letterspaced subtitle words.

**Raster required:** the chrome-extruded 3D logotype (illustration `y2k-chrome-3d` lineage, tilted italic). The grid, sun, mountains, and HUD chrome are honest CSS/SVG; the hero lettering is not.

## Voice register

Earnest drive-forever romance, letterspaced caps for structure and title case for poetry: "NEON HORIZON", "ECLIPSE DRIVE", "Plug in. Press play. Drive forever." Verbs of motion and night: drive, chase, escape, never stop. No irony, no lowercase detachment - synthwave means it.

## Failure mode

Pastel pink-and-teal with a marble bust and a glitched Windows dialog = vaporwave, the ironic cousin. A dark UI with random neon borders but no horizon composition = gamer RGB theme. The real thing commits to the sacred layout (grid below, sun at horizon, title in sky) at least once per experience, keeps the sky a true vertical grade, and reserves chrome extrusion for the title alone. Also fatal: daylight, gray neutrals anywhere, or replacing the striped sun with a plain circle - the stripes are the signature.

## Best for

- Music releases, DJ/producer sites, festival and club-night promo in the synth scene.
- Automotive and driving-game properties, night-drive apps.
- Products that want heroic retro-tech energy with total sincerity.
- Landing pages where one unforgettable hero frame matters more than density.

## Pairs well with

- Shells: `shell-hero-stack` (canonical - the horizon hero), `shell-scroll-journey-scene` (driving deeper as you scroll), `shell-mobile-app`
- Styles: `style-bold-display`, `style-outline-marquee` (neon HUD component grammar)

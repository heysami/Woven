---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-dubois-data-portraits-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-dubois-data-portraits-isolated.png
    reason: Signature motif, isolated.
---
# Du Bois data portraits (aesthetic)

**Tag:** hand-painted statistics

**Canonical references:**
- W. E. B. Du Bois's data portraits for the 1900 Paris Exposition - the founding corpus
- *W. E. B. Du Bois's Data Portraits: Visualizing Black America* (2018 reissue plates)
- Hand-drafted statistical atlases of the late 1800s - gouache and ink on board
- The spiral chart, the wrapped bar, the stepped area - forms invented to fit the board, not the software
- Archival exhibition boards: stamped caption capitals, hand-ruled dividers

## Cultural identity

Statistical graphics as hand-made moral argument: flat gouache data marks - spirals that coil to fit long values, bars that wrap rather than shrink, stepped blocks - painted in crimson, gold, emerald and ink black on aged cream board. Edges are confidently imperfect; paint density varies within a fill; captions are stamped in small hand-lettered capitals with full sentences of intent: "Count. Compare. Confront." The data IS the decoration - there is no ornament that is not also evidence, and the charts carry rhetorical force, not dashboard neutrality.

Where `aesthetic-swiss-modernist` is mechanical - objective grid, neutral sans, the designer erased - Du Bois data portraits keep the human hand and the argument visible in every mark. And against a `recipe-bloomberg-dashboard` register of live dense terminals, this is slow media: each chart is a composed plate, singular, framed, meant to be read like a poster.

## Palette anchor

- Aged cream `oklch(93% 0.03 90)`
- Crimson `oklch(48% 0.17 25)`
- Gold `oklch(75% 0.13 85)`
- Emerald `oklch(42% 0.09 160)`
- Ink black `oklch(20% 0.01 60)`
- Ochre `oklch(70% 0.10 80)`

Four pigment hues maximum per plate, always at full flat strength - never tints, never gradients, never a pastel.

## Decoration motifs

- Spiral and coiled bar charts; wrapped bars; stepped block-stack areas - painted, flat, thick
- Hand-ruled chart frames and dividers with slight waver; no pixel-perfect lines
- Stamped caption capitals, letterspaced, black, always declarative
- Numbers rendered large as painted figures (2.3X) doing hero duty
- Paint texture inside fills - visible brush density, dry edges, small overshoots
- One plate per viewport: chart, title, caption, nothing else competing

**Raster required:** the gouache paint fills and aged-board texture - the chart geometry can be SVG, but the imperfect painted surface is the aesthetic's soul.

## Voice register

Declarative, evidentiary, unhurried: "Truth in figures shapes power." "The pattern does not lie." Captions are complete sentences that state the finding, never "see chart above." Dignified and direct; never jokey, never corporate-neutral, never hedging.

## Failure mode

Feeding the palette into a charting library - crisp SVG bars with rounded corners and tooltips - produces a themed dashboard, not a data portrait. Adding gridlines, legends and axis clutter kills the poster clarity; the original plates label values directly on the marks. More than four hues, or any gradient, breaks the pigment discipline. Treating the style as "vintage skin" over trivial data is the deepest failure - the form demands data worth arguing.

## Best for

- Data journalism features, annual reports with a thesis, impact reports
- Museums, archives and exhibitions - especially history told through numbers
- Nonprofits and civic causes where numbers carry moral weight
- Teaching materials on statistics, inequality, demography

## Pairs well with

- Shells: `shell-centered-column`, `shell-hero-stack`, `shell-bento-grid`
- Styles: `style-serif-warm-paper`, `style-bold-display`, `style-cream-humanist`

---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: style-bubble-pop-rounded-ui.png
    reason: Style surface UI mockup.
  - src: style-bubble-pop-rounded-isolated.png
    reason: Signature surface, isolated.
---
# Bubble Pop Rounded (style)

**Tag:** Cooper Black 1922 · French yé-yé sleeves 1965-72 · ronde-era soft logotypes · 70s FMCG bubble wordmarks

**Canonical references:** Cooper Black and its 60s-70s revival, French pop 45rpm sleeve logotypes, ronde/bubble rounded sans lettering, period FMCG packaging wordmarks, modern soft-rounded revival faces (Baloo, Fredoka, Chubbo register).

## Surface treatment

**Background:** one flat saturated ground per surface - tangerine `#FF5A1F`, turquoise `#00B7B3`, or terracotta `#D35A3A`. Never a gradient, never white as the main ground; white space in this style is cream.

**Accent:** cream `#FFF2E2` does almost all foreground work - type, keylines, fills. One secondary warm (peche `#F6B28A` or sable `#E6C8A6`) for tints; espresso `#2A1A12` for small text on cream panels. The page is two-layer: hot ground, cream foreground.

**Type stack:** ONE inflated rounded face carries the whole identity - display, buttons, nav, all of it. Cooper-weight bubble sans or ronde: ball terminals, closed round counters, strokes that look air-filled. Body text in a plain rounded sans at regular weight. Never pair with a serif, a grotesque, or a second display face.

**Sizes:** display huge (10-16vw hero logotype, lowercase allowed and encouraged); the logotype IS the hero image. Labels and buttons 14-18px caps or lowercase; body 16-17px.

**Line-height:** display 0.9-1.0 (bubble letters nearly touching - the squeeze is the charm). Body 1.4-1.5.

**Radius:** everything full-soft - buttons 14-20px or full pill, cards 20-28px, inputs 12-16px. Nothing sharper than 10px anywhere. Corners must read as inflated, not merely rounded.

**Borders:** the signature move - 2-3px CREAM KEYLINES on the saturated ground outline every component: buttons, cards, inputs, nav bar. Active state fills the keyline shape with cream (ground-colored text); default state is outline only. Never gray borders, never 1px hairlines.

**Shadow:** none. Depth comes from the keyline system and flat color layering only.

## Decoration grammar

**Mandatory:**
- A big rounded logotype as the primary visual of any hero (lowercase bubble letters, tight leading)
- Cream keyline outlines on all interactive components; keyline-to-fill as the state change
- Flat saturated ground running full-bleed; sections separated by ground-color swaps, not rules
- Track-list / numbered-list furniture (01, 02, 03) set in the rounded face
- Round-cornered photo cards with cream frames when photography appears

**Forbidden:**
- Gradients, bevels, gloss, plastic 3D inflation renders
- Drop shadows of any kind
- Sharp corners, hairline rules, gray anything
- A second display face, condensed type, or all-caps body text
- Dark-mode grounds - this style lives in warm daylight color

## Motion budget

- 200-300ms ease-out scale (1.0 to 1.04) on hover - a gentle plump, not a bounce
- Keyline-to-fill state changes cross-fade at 150-200ms
- Section ground-color swaps may cross-fade at 300ms on scroll
- Forbidden: springy jelly physics, wobble loops, rotation - the letters are already the fun

## Failure mode

Cooper Black on white with black text = a 70s pastiche poster, not this style (the saturated ground is load-bearing). Adding shadows or gloss tips it into toy-store 3D. Mixing a grotesque headline in "for contrast" breaks the one-face rule that makes it read as an identity system. Thin keylines (1px) disappear against hot grounds - the outlines must be confidently thick. Neon or acid ground colors drift it toward rave flyer; the grounds stay warm and appetizing.

Distinct from `illust-typo-bubble-graffiti`: that register is street-art lettering - outlined graffiti balloons, spray texture, sticker chaos. Bubble Pop Rounded is a clean COMMERCIAL logotype register: one soft typeface as brand identity on flat grounds, no outlines-on-outlines, no street grit. And unlike `aesthetic-pastel-pop-fmcg`, which softens everything toward pastel tints, this style keeps grounds fully saturated with cream doing the softening.

## Best for

Music artists and labels, playlists and radio apps, cafes / bakeries / ice cream and appetite brands, kids-adjacent products that want retro charm without babyishness, fashion drops with a 60s-70s wink, event and festival identities.

Wrong for enterprise dashboards, legal / finance, data-dense tools, anything needing somber authority.

## Pairs well with

- **Shells:** shell-hero-stack, shell-centered-column, shell-bento-grid, shell-mobile-app
- **Aesthetics:** aesthetic-pastel-pop-fmcg, aesthetic-monochrome-pop-poster, aesthetic-avantropop, aesthetic-jp-recruit-pop

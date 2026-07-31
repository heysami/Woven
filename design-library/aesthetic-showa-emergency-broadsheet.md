---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-showa-emergency-broadsheet-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-showa-emergency-broadsheet-isolated.png
    reason: Signature motif, isolated.
---
# Showa emergency broadsheet (aesthetic)

**Tag:** kaiju-era civil-defense urgency

**Canonical references:**
- Toho kaiju-cycle broadcast and poster graphics (the *Godzilla* 1954-1975 era) - evacuation-order title cards over newsreel footage
- NHK emergency-broadcast slates and civil-defense (防災) drill posters of the Showa period
- Nippon News newsreel title typography - brush calligraphy cut against film grain
- Bureaucratic print ephemera: rationing notices, stamped municipal circulars, warning-striped public signage

## Cultural identity

The graphic voice of a Japanese city being officially alarmed, mid-century style. Enormous sumi brush calligraphy headlines (緊急警報) slam over newsreel-gray paper; red-and-white warning stripes frame the sheet; romaji subtitles run letterspaced beneath the kanji like a translator keeping pace (KINKYU KEIHOU); and every element wears bureaucratic furniture - wing-star insignia, classification tags (A-01), timestamp fields, inkan-style seals. The drama comes from the collision: the brush is urgent and human, the grid around it is procedural and calm. It is the aesthetic of an institution built to stay orderly while a monster is actually approaching.

Differentiation: `aesthetic-japanese-poster-layout` is the quiet photo-led editorial canon - gallery restraint, one dominant photograph, implied grid; this entry is its loud institutional sibling, type-led and stamped, with zero gallery composure. And `material-ink-wash-sumi-e` is the contemplative wash MATERIAL - misty gradients, meditative emptiness; here the brush is a siren, dry and slashing, mounted on bureaucratic furniture rather than floating in mist.

## Palette anchor

Newsreel monochrome plus signal inks:
- Newsreel black `oklch(20% 0 0)`
- Film gray `oklch(55% 0.01 240)`
- Alert white `oklch(95% 0 0)`
- Civil-defense red `oklch(52% 0.19 25)`
- Alarm amber `oklch(82% 0.16 85)`
- Alarm blue `oklch(45% 0.14 260)`

Red carries the alarm; amber and blue are secondary status codes. Never more than one signal color per component.

## Decoration motifs

- Sumi brush display calligraphy at broadsheet scale, dry-brush edges intact
- Red/white diagonal warning-stripe bands framing the page top and bottom
- Letterspaced romaji sublines under every kanji headline - the bilingual echo is signature
- Bureaucratic stamp furniture: wing-star insignia, boxed status seals (警告 / 解除 / 危険), classification codes
- Speed-line rules and triple-bar flourishes around subheads
- Newsreel grain and paper-stock texture across the whole ground; cracked-map figure panels with a single red arrow

**Raster required:** the brush calligraphy headlines and the newsreel grain ground (typography `sumi-brush-headline`, texture `newsreel-grain-paper`). Warning stripes are CSS; the brush and the film age are not.

## Voice register

Imperative and procedural: 避難する (evacuate), 詳細を見る (see details), coordinates, districts, issue times. Sentences are instructions with fields filled in - 対象地域 A-01, 発表時刻 10:30. Calm verbs under screaming type. Never marketing warmth, never exclamation marks - the brush does the shouting so the copy does not.

## Failure mode

Setting the headline in a "brush-style" font kills it instantly - the strokes must read as actually inked, irregular and dry. Second tell: hazard-yellow-and-black construction stripes; this genre's stripe is red/white civil defense, not roadwork. Third tell: dystopian grunge overlays or horror blood tones - the register is institutional composure under pressure, and the paper stays clean under its grain. Fourth tell: dropping the romaji echo lines; without the bilingual subtitle rhythm it reads as generic Asian-brush poster.

## Best for

- Alert and status dashboards, incident-response tools wanting narrative weight
- Kaiju/tokusatsu fan properties, film retrospectives, game UIs
- Disaster-preparedness campaigns with historical framing
- Any brief asking for "urgent, official, cinematic Japan"

## Pairs well with

- Shells: `shell-hero-stack`, `shell-centered-column`, `shell-top-bar-canvas`
- Styles: `style-bold-display`, `style-micro-text-frame`, `style-brutalist-raw`

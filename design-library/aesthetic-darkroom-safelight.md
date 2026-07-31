---
# Sample-image references for the System-tab design library. Images sit
# next to this file in design-library/ and were generated via image_gen.
images:
  - src: aesthetic-darkroom-safelight-ui.png
    reason: Aesthetic vocabulary in UI.
  - src: aesthetic-darkroom-safelight-isolated.png
    reason: Signature motif, isolated.
---
# Darkroom safelight (aesthetic)

**Tag:** amber-lit photochemical craft

**Canonical references:**
- The gelatin-silver printing darkroom - safelight physics: amber light that will not fog orthochromatic paper.
- Kodak / Ilford darkroom ephemera - bottle labels, enamel trays, boxed fiber paper, the Ilford Multigrade 1:9 dilution ritual.
- The Gralab 300 timer - glowing digits counting a developer bath in the dark.
- Test strips and step wedges - exposure ladders as the craft's native diagnostic graphic.
- Grease pencil on print backs - the era's handwriting: china marker crops and notes.

## Cultural identity

A room lit by one lamp that cannot ruin the work: **everything on screen sits under the same amber safelight**. The monochrome is physical, not stylistic - amber highlights, brown midtones, near-black shadows, because that is what any material looks like under a single filtered bulb. The materials are photochemical: speckled enamel trays, fiber paper with visible tooth, chemical bottles with matte peel labels, test strips stepping from white to black. Display lettering is **grease pencil** - thick, waxy, hand-dragged caps with pressure variance - while working data lives in **LCD timer digits**. Monochrome photographs are the only imagery, and they read as objects (prints in a bath, edges and borders visible), not as decoration.

This is NOT `material-crt-phosphor` - phosphor amber is EMISSIVE, a screen glowing its one color from inside; safelight amber is REFLECTED, one light falling on matte physical materials, with texture, shadow, and zero glow. A phosphor page is a display; a safelight page is a room.

## Palette anchor

One hue, by physics - everything is the safelight's amber at different depths:
- Safelight amber `oklch(80% 0.16 78)` (#ffb100) - highlights, lettering, the lamp itself
- Amber shadow `oklch(58% 0.13 70)` (#b36a00) - midtone material
- Darkroom brown `oklch(22% 0.05 65)` (#2a1b0b) - the room's ground
- Tray enamel `oklch(92% 0.05 90)` (#f3e6c4) - the brightest surface, amber-tinted cream
- Print black `oklch(10% 0 0)` (#0d0d0d) - photograph shadows
- Developer gray `oklch(48% 0.02 80)` - wet-print midtones

No second hue exists anywhere. Grayscale appears only inside photographs and test strips, and even those sit under the amber cast.

## Decoration motifs

- **The single-source light logic** - every element lit from the same direction, brighter near the lamp, falling into brown-black at the edges.
- **Grease-pencil display lettering** - waxy hand-drawn caps with a rough underline swipe; the human voice of the room.
- **LCD timer digits** - segmented countdown numerals ("00:45") as the working display face.
- **Photochemical materials** - enamel tray speckle, fiber-paper tooth, bottle-label matte, all rendered honestly.
- **Test strips** - stepped exposure ladders as progress bars, dividers, and diagnostic ornament.
- **Monochrome prints as objects** - photographs with borders and wet sheen, clipped to cards like prints in a bath.
- **Process annotations** - temperature ("20 C"), dilution ("Ilford MG 1:9"), agitation notes as ambient data.

**Raster required:** the material world - enamel speckle, paper tooth, and the monochrome photograph prints themselves (photo `monochrome-print-under-safelight`; pairs naturally with `photo-magnum-monochrome` for the print content). The amber grade is CSS; the physical texture is not.

## Voice register

Craft patience with stakes: "Chemistry and time shape the image.", "Watch the highlights. Protect the shadows.", "There is no undo." Process verbs - expose, develop, fix, pull. Labels are short caps ("START TIMER", "FIRST BATH"); notes read like a printer's log. Quiet, exact, irreversible.

## Failure mode

A dark theme with orange accent buttons = amber-flavored dashboard, not a darkroom. The real thing is monochromatic BY PHYSICS: if any element could not exist under one amber bulb (a blue link, a white card, a colorful chart), the room is broken. Also fatal: glow and bloom on the amber (that is phosphor, emissive, the other entry), clean flat surfaces with no material tooth, or cheerful urgency - the darkroom is patient or it is nothing.

## Best for

- Photography portfolios, print shops, film-lab services, analog-photo communities.
- Timer, process, and checklist tools that want ritual gravity.
- Archives and collections of monochrome imagery.
- Brand storytelling about craft, chemistry, and things you cannot undo.

## Pairs well with

- Shells: `shell-centered-column`, `shell-two-column-app`, `shell-mobile-app`
- Styles: `style-dense-mono-dark` (annotation discipline), `style-serif-warm-paper` (inverted into the amber world for longer prose)
- Photo: `photo-magnum-monochrome` (the prints in the trays)

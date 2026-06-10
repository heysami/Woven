# Backstage editorial BTS (photo)

**Tag:** photo-backstage-fashion  ·  **Era:** current  ·  **Category:** BTS  ·  **Role affinity:** hero, section

Available light, sometimes mixed with hair-light or makeup-station tungsten.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/photography-library.md`](../docs/research/photography-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- styleId: backstage-fashion
  name: Backstage editorial BTS
  era: current
  category: BTS
  visualSignatures:
    - Available light, sometimes mixed with hair-light or makeup-station tungsten
    - Models mid-prep: hair in foil, robe, half-makeup, phone in hand
    - Cluttered context: garment racks, clothespins, stylist's hands
    - Slightly desaturated, journalism-tone
    - Wide-ish 28-35mm framing
  promptKeywords:
    primary: [model in robe mid-prep, garment racks behind, hair in foil, phone in hand, half-makeup]
    lighting: [available mixed tungsten, soft window, slight motion blur tolerated]
    cameraOrLens: [Leica Q2, 28mm at f/2]
    filmStockOrPostProcessing: [natural color, slight desaturation, journalism tone]
    mood: [observed, in-process, intimate-professional]
    avoidKeywords: [studio polish, retouched, posed, glamour final-look]
  namedReferences:
    photographers: [Tim Walker BTS, Sonny Vandevelde, Kevin Tachman]
    magazines: [Vogue Runway BTS, AnOther backstage features]
    movements: [backstage editorial, Show Studio BTS]
    brands: [used by all major fashion houses for BTS social content]
  examplePromptTemplate: |
    Backstage photograph of a model in a white silk robe sitting in a director's chair, hair in foil curlers, phone in hand, half-applied makeup, garment racks of metallic dresses out of focus behind. Available mixed tungsten from makeup station with soft natural light from a window upper-right, slight tolerated motion blur on the phone. Shot on a Leica Q2 with a 28mm at f/2, natural color with slight desaturation. Observed, in-process, intimate-professional mood. Backstage editorial BTS, fashion week documentary.
  whenToUse: Behind-the-scenes content for fashion, beauty launches, behind-the-craft brand storytelling, documentary marketing.
  pairsWith:
    prototypeStyles: [recipe-editorial-magazine, recipe-readcv, aesthetic-corporate-grunge, recipe-restrained-ai-marketing]
  notForUseWhen: Polished hero, conversion product page.

---
```

## When NOT to use

Polished hero, conversion product page.

## Pairs with (prototype slugs)

- `recipe-editorial-magazine`
- `recipe-readcv`
- `aesthetic-corporate-grunge`
- `recipe-restrained-ai-marketing`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 1242–1272 of `docs/research/photography-library.md`. Full index: `docs/research/photography-library.index.json`._

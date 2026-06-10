# Pixel bitmap illustration (illust)

**Tag:** illust-pixel-bitmap-illustration  ·  **Category:** 3D  ·  **Role affinity:** subject

explicit pixel grid, no anti-aliasing.

## Full library entry

_Below is the verbatim YAML for this entry — same content the orchestrator + drawer read at dispatch. Edit upstream in [`docs/research/illustration-library.md`](../docs/research/illustration-library.md) then re-run `scripts/regen-prototype-details.py` + `scripts/build-library-indexes.py` to propagate._

```yaml
- styleId: pixel-bitmap-illustration
  name: Pixel bitmap illustration
  category: 3D
  subCategory: voxel
  role: subject
  source: curator addition + prototype/style-pixel-bitmap
  visualSignatures:
    - explicit pixel grid, no anti-aliasing
    - limited palette per era (NES 4-color, GameBoy 4-shade, SNES 16-color)
    - dithering for shading
  promptKeywords:
    primary: [pixel art, bitmap, dithering, limited palette]
    material: ["8-bit or 16-bit pixel"]
    line: ["pixel-grid edge"]
    color: ["era-limited palette"]
    style: ["dither shading", "explicit grid"]
    avoidKeywords: [smooth, vector, anti-aliased]
  namedReferences:
    illustrators: [Capcom NES era, eBoy]
    productsOrFilms: [NES Mario, GameBoy Pokemon, Stardew Valley]
  examplePromptTemplate: |
    Pixel bitmap illustration of [SUBJECT] with explicit pixel grid no anti-
    aliasing, [ERA]-limited palette, dithering for shading, isolated on
    transparent or solid color background.
  whenToUse: Gaming brands, retro tech, indie game marketing.
  pairsWith:
    prototypeStyles: [aesthetic-pixel-nes-mario, aesthetic-pixel-game-boy-mono, aesthetic-pixel-snes-jrpg, aesthetic-pixel-arcade, aesthetic-pixel-modern-cozy, aesthetic-pixel-ps1-tactics-ogre, style-pixel-bitmap]
  notForUseWhen: cinematic, photoreal, warm-restraint
```

## When NOT to use

cinematic, photoreal, warm-restraint

## Pairs with (prototype slugs)

- `aesthetic-pixel-nes-mario`
- `aesthetic-pixel-game-boy-mono`
- `aesthetic-pixel-snes-jrpg`
- `aesthetic-pixel-arcade`
- `aesthetic-pixel-modern-cozy`
- `aesthetic-pixel-ps1-tactics-ogre`
- `style-pixel-bitmap`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

---

_Indexed at line 2943–2971 of `docs/research/illustration-library.md`. Full index: `docs/research/illustration-library.index.json`._

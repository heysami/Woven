---
styleId: 3d-ps1-low-poly
name: PS1-era low-poly 3D
category: 3D
subCategory: low-poly-paper
role: subject
pairsPrototypes: [aesthetic-pixel-ps1-tactics-ogre, aesthetic-vaporwave, aesthetic-cassette-futurism, aesthetic-pc-98, recipe-terminal-on-web]
notForUseWhen: premium-luxury, restrained editorial, photoreal product
---

# PS1-era low-poly 3D

Characters, objects, and environments rendered in the **PlayStation-1-era low-poly aesthetic** — angular silhouettes, low-resolution texture maps (256×256 for hero, 128×128 for everything else), vertex-jitter / wobble (because the PS1 had no subpixel precision), flat-shaded planes, no antialiasing, affine texture mapping (textures warp on tilted faces). Used for retro-game revival, nostalgic gaming brands, demoscene-adjacent work, vaporwave hybrids, indie-game marketing.

## Visual signatures

- low polygon count — silhouettes obviously faceted, ~300-3000 polys per character
- low-res pixel-textured surfaces — 256×256 for main, 128×128 for secondary
- vertex jitter / wobble (PS1 lacked subpixel precision — vertices snap to nearest pixel each frame)
- flat or Gouraud shading per polygon; no smooth normals
- no antialiasing — visible pixel staircase on every edge
- affine texture warping — textures distort obviously on tilted faces (perspective-correct mapping was a PS2-era feature)
- limited palette per texture (often <64 colors) due to VRAM constraints
- environments often use sprite-billboards for distant objects

## Prompt keywords

**Primary**: PS1 low-poly, vertex jitter, affine texture, 256×256 pixel texture, PlayStation 1 aesthetic, faceted silhouette

**Material**: flat-shaded polygon, pixel-textured, no antialiasing, affine warp on tilted faces

**Line**: hard pixel staircase edges, no smooth curves

**Color**: limited palette per texture, often desaturated or VHS-era

**Style**: vertex-wobble, low-poly silhouette, sprite-billboard distant objects

**Avoid (negative prompt)**: antialiased, smooth normals, high-poly, photoreal, subpixel precision, modern shaders, soft shadow

## Named references

**Games**: Silent Hill (PSX), Resident Evil 1-2 (pre-rendered backgrounds + low-poly chars), Final Fantasy VII-IX, Vagrant Story, Tactics Ogre, MediEvil

**Modern revival artists**: Polygon Runway, AstroBob, the Haunted PS1 community, Puppet Combo (game studio)

**Movements**: PS1 horror revival 2018-current, vaporwave 3D (vaporwave often co-opts PS1 assets), demoscene low-poly

## Example prompt template

> PS1-era low-poly 3D [SUBJECT — character / object / environment], roughly
> 500-2000 polygons, obviously faceted silhouette, 256×256 pixel-textured
> surfaces with limited palette and visible pixel staircase edges, no
> antialiasing, vertex-jitter giving slight wobble, affine texture warp on
> tilted faces, flat-shaded polygons with hard normals, dark-VHS-era desaturated
> palette, sprite-billboard distant detail, late-1990s PlayStation 1 aesthetic,
> rendered as if at native 320×240 then upscaled.

## When to use

Retro-game brands, indie-game marketing, vaporwave-hybrid editorial, demoscene-adjacent music releases, gen-Z nostalgia merchandising, PSX horror revival.

## When NOT to use

premium-luxury, restrained editorial, photoreal product, anything wanting clean modern render

## Pairs with (prototype slugs)

- `aesthetic-pixel-ps1-tactics-ogre`
- `aesthetic-vaporwave`
- `aesthetic-cassette-futurism`
- `aesthetic-pc-98`
- `recipe-terminal-on-web`

<!-- image: sample-1.png -->
<!-- reason: representative reference shot of this style -->

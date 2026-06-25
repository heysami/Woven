# Woven -> Figma scene contract

The editor's DOM walker (`editor/figma-bridge.js`, `window.WovenFigma.domToScene`)
emits this JSON; the plugin sandbox (`code.js`) rebuilds it as Figma nodes. Keep
both sides in sync when extending the schema.

```jsonc
{
  "version": 1,
  "name": "Landing page",     // names the top frame in Figma
  "width": 1280,
  "height": 3200,
  "imageBytes": 1234567,      // diagnostic: total inlined raster size
  "root": { /* node */ }
}
```

## node

```jsonc
{
  "type": "FRAME" | "TEXT" | "IMAGE",
  "name": "section.hero",
  "x": 0, "y": 0,            // position RELATIVE to the parent node
  "width": 1280, "height": 720,

  // optional, all node types
  "opacity": 0.9,            // omitted when 1
  "clipsContent": true,      // overflow:hidden
  "fills":   [ Paint, ... ], // paint order = CSS paint order (bg color, then image)
  "strokes": [ Paint ],      // SOLID only; CSS border
  "strokeWeight": 1,
  "cornerRadius": 8 | { "tl":8, "tr":8, "br":0, "bl":0 },
  "effects": [ Effect, ... ],// box-shadow

  // TEXT only
  "characters": "Get started",
  "fontSize": 16,
  "fontFamily": "Inter",
  "fontStyle": "SemiBold",   // mapped from font-weight + italic
  "letterSpacing": 0.2,      // px
  "lineHeight": 24 | "AUTO", // px or AUTO
  "textAlign": "LEFT" | "CENTER" | "RIGHT" | "JUSTIFIED",
  "textColor": Paint,        // SOLID
  "textDecoration": "NONE" | "UNDERLINE" | "STRIKETHROUGH",

  // IMAGE only (also <img>)
  "image": { "b64": "...", "mime": "image/jpeg" },

  "children": [ node, ... ]
}
```

## Paint

```jsonc
{ "type": "SOLID", "color": { "r":0..1, "g":0..1, "b":0..1 }, "opacity": 0..1 }
{ "type": "GRADIENT_LINEAR", "angle": 180, "stops": [ { "position":0..1, "color": {r,g,b,a} } ] }
{ "type": "IMAGE", "scaleMode": "FILL", "image": { "b64", "mime" } }
```

## Effect

```jsonc
{ "type": "DROP_SHADOW" | "INNER_SHADOW",
  "offsetX": 0, "offsetY": 2, "radius": 8, "spread": 0,
  "color": { "r":0..1, "g":0..1, "b":0..1, "a":0..1 } }
```

## v1 limitations (intentional)

- Absolute positioning only. No auto-layout yet; the schema leaves room for a
  later `layout` field without breaking the plugin.
- CSS transforms (rotation/scale) are baked into x/y/size by
  `getBoundingClientRect`, so a rotated element lands un-rotated at its rendered
  box.
- `<canvas>`, inline `<svg>`, and `<video>` are walked as plain frames (their
  box decoration only). Rasterizing them via the already-loaded `html2canvas-pro`
  is the planned upgrade.
- One box-shadow / one linear-gradient layer is parsed (the first).
- Cross-origin images that block CORS fall back to a neutral gray fill.

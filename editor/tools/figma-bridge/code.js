/*
 * Woven Bridge - Figma plugin sandbox (code.js).
 *
 * Runs in Figma's plugin realm (has `figma`, no DOM / no fetch). It receives a
 * Woven "scene" JSON from the UI iframe (ui.html does the networking) and
 * rebuilds it as real, editable Figma nodes: frames, text, rectangles, image
 * fills, strokes, corner radii, shadows. See SCENE.md for the scene contract.
 *
 * Message protocol (ui.html <-> code.js):
 *   ui  -> code : { type: "build", job: { jobId, name, scene } }
 *   code -> ui  : { type: "status", jobId, state, message }   state in
 *                 building | done | error  (ui relays these to the daemon)
 */

figma.showUI(__html__, { width: 340, height: 460, title: "Woven Bridge" });

figma.ui.onmessage = function (msg) {
  if (!msg) return;
  if (msg.type === "build" && msg.job) { buildJob(msg.job); return; }
  if (msg.type === "getComponents") { sendComponentsState(msg.dsRef, msg.names); return; }
  if (msg.type === "bindComponent") { bindComponent(msg.dsRef, msg.component); return; }
  if (msg.type === "unbindComponent") { unbindComponent(msg.dsRef, msg.component); return; }
};

function report(jobId, state, message) {
  figma.ui.postMessage({ type: "status", jobId: jobId, state: state, message: message || "" });
}

// ---- base64 -> bytes (no atob in the plugin sandbox) --------------------
var _B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
var _B64LUT = (function () {
  var t = new Uint8Array(256);
  for (var i = 0; i < _B64.length; i++) t[_B64.charCodeAt(i)] = i;
  return t;
})();
function b64ToBytes(b64) {
  b64 = String(b64 || "").replace(/\s+/g, "");
  var len = b64.length;
  if (!len) return new Uint8Array(0);
  var pad = 0;
  if (b64[len - 1] === "=") pad++;
  if (b64[len - 2] === "=") pad++;
  var n = ((len * 3) >> 2) - pad;
  var bytes = new Uint8Array(n);
  var p = 0;
  for (var i = 0; i < len; i += 4) {
    var a = _B64LUT[b64.charCodeAt(i)], b = _B64LUT[b64.charCodeAt(i + 1)];
    var c = _B64LUT[b64.charCodeAt(i + 2)], d = _B64LUT[b64.charCodeAt(i + 3)];
    var chunk = (a << 18) | (b << 12) | (c << 6) | d;
    if (p < n) bytes[p++] = (chunk >> 16) & 255;
    if (p < n) bytes[p++] = (chunk >> 8) & 255;
    if (p < n) bytes[p++] = chunk & 255;
  }
  return bytes;
}

// ---- paints / effects ---------------------------------------------------

function clamp(n, lo, hi) { return n < lo ? lo : n > hi ? hi : n; }

function gradientTransform(angleDeg) {
  // CSS angle: 0deg points up, 90deg points right. Figma's default gradient
  // runs left->right, so rotate to align. Approximate (no per-stop skew).
  var a = ((angleDeg || 180) - 90) * Math.PI / 180;
  var cos = Math.cos(a), sin = Math.sin(a);
  return [
    [cos, sin, 0.5 - 0.5 * cos - 0.5 * sin],
    [-sin, cos, 0.5 + 0.5 * sin - 0.5 * cos]
  ];
}

function toPaint(p) {
  if (!p || !p.type) return null;
  if (p.type === "SOLID") {
    var paint = { type: "SOLID", color: { r: p.color.r, g: p.color.g, b: p.color.b } };
    if (typeof p.opacity === "number") paint.opacity = clamp(p.opacity, 0, 1);
    return paint;
  }
  if (p.type === "GRADIENT_LINEAR" && Array.isArray(p.stops)) {
    return {
      type: "GRADIENT_LINEAR",
      gradientTransform: gradientTransform(p.angle),
      gradientStops: p.stops.map(function (s) {
        return {
          position: clamp(s.position, 0, 1),
          color: { r: s.color.r, g: s.color.g, b: s.color.b, a: typeof s.color.a === "number" ? s.color.a : 1 }
        };
      })
    };
  }
  if (p.type === "IMAGE" && p.image && p.image.b64) {
    try {
      var img = figma.createImage(b64ToBytes(p.image.b64));
      return { type: "IMAGE", scaleMode: p.scaleMode || "FILL", imageHash: img.hash };
    } catch (e) {
      return null; // bad image data -> no fill (caller may keep solids)
    }
  }
  return null;
}

function toPaints(arr) {
  if (!Array.isArray(arr)) return [];
  var out = [];
  for (var i = 0; i < arr.length; i++) {
    var p = toPaint(arr[i]);
    if (p) out.push(p);
  }
  return out;
}

function toEffects(arr) {
  if (!Array.isArray(arr)) return [];
  var out = [];
  for (var i = 0; i < arr.length; i++) {
    var e = arr[i];
    if (e.type !== "DROP_SHADOW" && e.type !== "INNER_SHADOW") continue;
    var col = e.color || { r: 0, g: 0, b: 0, a: 0.25 };
    out.push({
      type: e.type,
      color: { r: col.r, g: col.g, b: col.b, a: typeof col.a === "number" ? col.a : 0.25 },
      offset: { x: e.offsetX || 0, y: e.offsetY || 0 },
      radius: Math.max(0, e.radius || 0),
      spread: Math.max(0, e.spread || 0),
      visible: true,
      blendMode: "NORMAL"
    });
  }
  return out;
}

function applyCorner(node, corner) {
  if (typeof corner === "number") {
    try { node.cornerRadius = corner; } catch (e) {}
  } else if (corner && typeof corner === "object") {
    try { node.topLeftRadius = corner.tl || 0; node.topRightRadius = corner.tr || 0;
          node.bottomRightRadius = corner.br || 0; node.bottomLeftRadius = corner.bl || 0; } catch (e) {}
  }
}

function applyBox(node, n) {
  if (n.fills) { try { node.fills = toPaints(n.fills); } catch (e) {} }
  if (n.strokes) {
    try {
      node.strokes = toPaints(n.strokes);
      if (typeof n.strokeWeight === "number") node.strokeWeight = Math.max(0, n.strokeWeight);
      node.strokeAlign = "INSIDE";
    } catch (e) {}
  }
  if (n.cornerRadius != null) applyCorner(node, n.cornerRadius);
  if (n.effects) { try { node.effects = toEffects(n.effects); } catch (e) {} }
  if (typeof n.opacity === "number") { try { node.opacity = clamp(n.opacity, 0, 1); } catch (e) {} }
  if (n.clipsContent != null && "clipsContent" in node) { try { node.clipsContent = !!n.clipsContent; } catch (e) {} }
}

// ---- fonts --------------------------------------------------------------

var FALLBACK = { family: "Inter", style: "Regular" };
var _fontMap = {};   // "family\nstyle" -> actual {family,style} we loaded

function collectFonts(node, set) {
  if (node.type === "TEXT" && node.characters) set[node.fontFamily + "\n" + node.fontStyle] = true;
  if (node.children) for (var i = 0; i < node.children.length; i++) collectFonts(node.children[i], set);
}

function loadFonts(root) {
  var wanted = {};
  collectFonts(root, wanted);
  var keys = Object.keys(wanted);
  var chain = figma.loadFontAsync(FALLBACK).catch(function () {});
  keys.forEach(function (key) {
    var parts = key.split("\n");
    var family = parts[0], style = parts[1] || "Regular";
    chain = chain.then(function () {
      return figma.loadFontAsync({ family: family, style: style }).then(function () {
        _fontMap[key] = { family: family, style: style };
      }, function () {
        // Fall back to Inter in the requested weight, then plain Inter.
        return figma.loadFontAsync({ family: "Inter", style: style }).then(function () {
          _fontMap[key] = { family: "Inter", style: style };
        }, function () {
          _fontMap[key] = FALLBACK;
        });
      });
    });
  });
  return chain;
}

function resolveFont(node) {
  return _fontMap[node.fontFamily + "\n" + node.fontStyle] || FALLBACK;
}

// ---- component mapping (Woven component -> Figma library instance) ------
// Bindings (componentName -> Figma component/set key) live in clientStorage,
// keyed by the project's design system, since Figma keys are file/library-local.
// The editor only authors the selector RULES that tag nodes; binding happens
// here, where the user can select the real Figma component.

var _compCache = {};   // componentName -> { node, kind } resolved for this build

function bindingsKey(dsRef) { return "woven.bindings." + (dsRef || "default"); }

function getBindings(dsRef) {
  return figma.clientStorage.getAsync(bindingsKey(dsRef)).then(function (v) { return v || {}; }, function () { return {}; });
}
function setBindings(dsRef, map) {
  return figma.clientStorage.setAsync(bindingsKey(dsRef), map).then(function () {}, function () {});
}

// Resolve the current canvas selection to a bindable component/set + its key.
function resolveSelectionComponent() {
  var sel = figma.currentPage.selection;
  if (!sel || !sel.length) return null;
  var n = sel[0];
  if (n.type === "INSTANCE") { n = n.mainComponent; if (!n) return null; }
  if (n.type === "COMPONENT") {
    if (n.parent && n.parent.type === "COMPONENT_SET") {
      return { key: n.parent.key || "", id: n.parent.id, kind: "SET", name: n.parent.name };
    }
    return { key: n.key || "", id: n.id, kind: "COMPONENT", name: n.name };
  }
  if (n.type === "COMPONENT_SET") return { key: n.key || "", id: n.id, kind: "SET", name: n.name };
  return null;
}

function sendComponentsState(dsRef, names) {
  getBindings(dsRef).then(function (map) {
    figma.ui.postMessage({ type: "componentsState", dsRef: dsRef, names: names || [], bindings: map });
  });
}

function bindComponent(dsRef, component) {
  var resolved = resolveSelectionComponent();
  if (!resolved) {
    figma.ui.postMessage({ type: "boundResult", component: component, ok: false,
      error: "Select a component, component set, or instance on the canvas, then Bind." });
    return;
  }
  getBindings(dsRef).then(function (map) {
    map[component] = resolved;
    setBindings(dsRef, map).then(function () {
      figma.ui.postMessage({ type: "boundResult", component: component, ok: true, figmaName: resolved.name });
      figma.ui.postMessage({ type: "componentsState", dsRef: dsRef, names: Object.keys(map), bindings: map });
    });
  });
}

function unbindComponent(dsRef, component) {
  getBindings(dsRef).then(function (map) {
    delete map[component];
    setBindings(dsRef, map).then(function () {
      figma.ui.postMessage({ type: "componentsState", dsRef: dsRef, names: Object.keys(map), bindings: map });
    });
  });
}

// Import every bound component referenced by the scene up front (like fonts),
// so the synchronous build can createInstance() without awaiting per node.
function loadComponents(scene) {
  _compCache = {};
  var names = scene.components || [];
  if (!names.length) return Promise.resolve();
  return getBindings(scene.dsRef || "default").then(function (map) {
    var chain = Promise.resolve();
    names.forEach(function (name) {
      var b = map[name];
      if (!b || (!b.key && !b.id)) return;
      chain = chain.then(function () {
        var p;
        if (b.kind === "SET" && b.key) p = figma.importComponentSetByKeyAsync(b.key);
        else if (b.key) p = figma.importComponentByKeyAsync(b.key);
        else p = Promise.reject();
        return p.then(function (node) {
          _compCache[name] = { node: node, kind: node.type === "COMPONENT_SET" ? "SET" : "COMPONENT" };
        }, function () {
          // Local/unpublished component: fall back to its node id in this file.
          if (!b.id || !figma.getNodeByIdAsync) return;
          return figma.getNodeByIdAsync(b.id).then(function (node) {
            if (node && (node.type === "COMPONENT" || node.type === "COMPONENT_SET")) {
              _compCache[name] = { node: node, kind: node.type === "COMPONENT_SET" ? "SET" : "COMPONENT" };
            }
          }, function () {});
        });
      });
    });
    return chain;
  });
}

// Best-effort variant/property application: match provided prop names to the
// instance's available properties (case-insensitive, ignoring the "#id" suffix
// Figma adds to non-variant props). setProperties is all-or-nothing, so retry
// per key and skip any that the component does not accept.
function applyComponentProps(inst, props) {
  var avail;
  try { avail = inst.componentProperties || {}; } catch (e) { return; }
  var keys = Object.keys(avail);
  var toSet = {};
  Object.keys(props).forEach(function (pk) {
    var want = String(pk).toLowerCase();
    for (var i = 0; i < keys.length; i++) {
      if (keys[i].split("#")[0].toLowerCase() === want) { toSet[keys[i]] = props[pk]; break; }
    }
  });
  if (!Object.keys(toSet).length) return;
  try { inst.setProperties(toSet); }
  catch (e) {
    Object.keys(toSet).forEach(function (k) {
      var one = {}; one[k] = toSet[k];
      try { inst.setProperties(one); } catch (e2) {}
    });
  }
}

function buildInstance(n, cached) {
  var inst = null;
  try {
    if (cached.kind === "SET") {
      var def = cached.node.defaultVariant || (cached.node.children && cached.node.children[0]);
      inst = def ? def.createInstance() : null;
    } else {
      inst = cached.node.createInstance();
    }
  } catch (e) { return null; }
  if (!inst) return null;
  inst.name = n.name || cached.node.name;
  if (n.componentProps) applyComponentProps(inst, n.componentProps);
  var s = size(n);
  try { inst.resize(s.w, s.h); } catch (e) {}
  if (typeof n.opacity === "number") { try { inst.opacity = clamp(n.opacity, 0, 1); } catch (e) {} }
  return inst;
}

// ---- node construction --------------------------------------------------

function size(n) {
  return { w: Math.max(0.01, n.width || 0.01), h: Math.max(0.01, n.height || 0.01) };
}

function buildText(n) {
  var t = figma.createText();
  t.fontName = resolveFont(n);
  t.fontSize = Math.max(1, n.fontSize || 16);
  t.characters = n.characters || "";
  if (n.textColor) { try { t.fills = [toPaint(n.textColor)].filter(Boolean); } catch (e) {} }
  try { t.textAlignHorizontal = n.textAlign || "LEFT"; } catch (e) {}
  if (typeof n.letterSpacing === "number" && n.letterSpacing) {
    try { t.letterSpacing = { value: n.letterSpacing, unit: "PIXELS" }; } catch (e) {}
  }
  if (n.lineHeight && n.lineHeight !== "AUTO") {
    try { t.lineHeight = { value: n.lineHeight, unit: "PIXELS" }; } catch (e) {}
  }
  if (n.textDecoration && n.textDecoration !== "NONE") {
    try { t.textDecoration = n.textDecoration; } catch (e) {}
  }
  // Size per the converter's hint. HUG width -> auto width+height (labels,
  // button text). Otherwise fixed width + auto HEIGHT, so the box hugs the
  // glyphs vertically (no tall box with top-aligned text) and the parent
  // auto-layout can vertically center it.
  try {
    var sz = n.sizing || {};
    if (sz.h === "HUG") {
      t.textAutoResize = "WIDTH_AND_HEIGHT";
    } else {
      t.textAutoResize = "HEIGHT";
      var s = size(n);
      t.resize(s.w, Math.max(1, t.height));
    }
  } catch (e) {}
  t.name = n.name || "text";
  return t;
}

function buildImage(n) {
  var r = figma.createRectangle();
  var s = size(n);
  r.resize(s.w, s.h);
  r.name = n.name || "image";
  var paint = n.image && n.image.b64 ? toPaint({ type: "IMAGE", scaleMode: "FILL", image: n.image }) : null;
  r.fills = paint ? [paint] : [{ type: "SOLID", color: { r: 0.9, g: 0.9, b: 0.9 } }];
  if (n.cornerRadius != null) applyCorner(r, n.cornerRadius);
  if (n.effects) { try { r.effects = toEffects(n.effects); } catch (e) {} }
  if (typeof n.opacity === "number") { try { r.opacity = clamp(n.opacity, 0, 1); } catch (e) {} }
  return r;
}

// Turn the scene's layout hint into a Figma auto-layout frame. Returns true
// when auto-layout was applied (so the caller flows children instead of
// positioning them by x/y).
function applyAutoLayout(frame, n) {
  var L = n.layout;
  if (!L || (L.mode !== "HORIZONTAL" && L.mode !== "VERTICAL")) return false;
  try { frame.layoutMode = L.mode; } catch (e) { return false; }
  try { frame.itemSpacing = Math.max(0, L.gap || 0); } catch (e) {}
  if (L.padding) {
    try {
      frame.paddingTop = L.padding.top || 0; frame.paddingRight = L.padding.right || 0;
      frame.paddingBottom = L.padding.bottom || 0; frame.paddingLeft = L.padding.left || 0;
    } catch (e) {}
  }
  try { frame.primaryAxisAlignItems = L.primaryAlign || "MIN"; } catch (e) {}
  try { frame.counterAxisAlignItems = L.counterAlign || "MIN"; } catch (e) {}
  if (L.wrap && L.mode === "HORIZONTAL") {
    try { frame.layoutWrap = "WRAP"; } catch (e) {}
    if (L.crossGap) { try { frame.counterAxisSpacing = L.crossGap; } catch (e) {} }
  }
  // Keep the frame's rendered size rather than hugging its contents.
  try { frame.primaryAxisSizingMode = "FIXED"; } catch (e) {}
  try { frame.counterAxisSizingMode = "FIXED"; } catch (e) {}
  return true;
}

function buildFrame(n) {
  var f = figma.createFrame();
  var s = size(n);
  f.resize(s.w, s.h);
  f.name = n.name || "frame";
  f.fills = []; // transparent unless the scene says otherwise
  applyBox(f, n);

  var kids = [];
  if (Array.isArray(n.children)) {
    for (var i = 0; i < n.children.length; i++) {
      var built = buildNode(n.children[i]);
      if (built) { f.appendChild(built); kids.push({ built: built, src: n.children[i] }); }
    }
  }

  var auto = applyAutoLayout(f, n);
  for (var k = 0; k < kids.length; k++) {
    var node = kids[k].built, src = kids[k].src;
    if (auto) {
      if (src.absolute) {
        // Out of the auto-layout flow: position it absolutely like CSS.
        try { node.layoutPositioning = "ABSOLUTE"; node.x = src.x || 0; node.y = src.y || 0; } catch (e) {}
      } else {
        // Honor the converter's per-child sizing (text hugs height / fills the
        // column width); default to FIXED (keep the measured box) for frames.
        var sz = src.sizing || {};
        try { node.layoutSizingHorizontal = sz.h || "FIXED"; } catch (e) {
          try { node.layoutSizingHorizontal = "FIXED"; } catch (e2) {}
        }
        try { node.layoutSizingVertical = sz.v || "FIXED"; } catch (e) {
          try { node.layoutSizingVertical = "FIXED"; } catch (e2) {}
        }
      }
    } else {
      // Absolute frame: scene child x/y are relative to this parent.
      try { node.x = src.x || 0; node.y = src.y || 0; } catch (e) {}
    }
  }
  // Enabling auto-layout can hug the frame as children are added; restore size.
  if (auto) { try { f.resize(s.w, s.h); } catch (e) {} }
  return f;
}

var _count = 0;
function buildNode(n) {
  if (!n || !n.type) return null;
  _count++;
  // A tagged component with a resolved binding becomes a real library instance;
  // otherwise fall through and build it from primitives.
  if (n.component && _compCache[n.component]) {
    var inst = buildInstance(n, _compCache[n.component]);
    if (inst) return inst;
  }
  if (n.type === "TEXT") return buildText(n);
  if (n.type === "IMAGE") return buildImage(n);
  return buildFrame(n);
}

function buildJob(job) {
  var jobId = job.jobId || "";
  var scene = job.scene || {};
  var root = scene.root;
  if (!root) { report(jobId, "error", "empty scene"); return; }
  report(jobId, "building", "Loading fonts");
  _count = 0; _fontMap = {};
  loadFonts(root).then(function () {
    report(jobId, "building", "Resolving components");
    return loadComponents(scene);
  }).then(function () {
    try {
      var frame = buildFrame(root);
      // Drop it just right of whatever is on the page, near the viewport.
      var vp = figma.viewport.center;
      frame.x = Math.round(vp.x - frame.width / 2);
      frame.y = Math.round(vp.y - frame.height / 2);
      figma.currentPage.appendChild(frame);
      figma.currentPage.selection = [frame];
      figma.viewport.scrollAndZoomIntoView([frame]);
      report(jobId, "done", "Built '" + (job.name || frame.name) + "' (" + _count + " layers)");
    } catch (e) {
      report(jobId, "error", String((e && e.message) || e));
    }
  }, function (e) {
    report(jobId, "error", "font load failed: " + String((e && e.message) || e));
  });
}

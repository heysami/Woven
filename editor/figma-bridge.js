/*
 * Woven -> Figma bridge: browser-side DOM walker.
 *
 * Loaded before app.js. Exposes window.WovenFigma.domToScene(rootEl), which
 * walks a rendered (same-origin) prototype document into an intermediate
 * "scene" JSON that the Woven Figma plugin rebuilds as real, editable Figma
 * nodes (frames / text / rectangles / image fills). The daemon is only a relay
 * for this payload; all DOM measurement happens here, where getComputedStyle
 * and getBoundingClientRect see the actual rendered result.
 *
 * Scene schema (see SCENE.md in editor/tools/figma-bridge/ for the contract):
 *   scene = { version, name, width, height, root }
 *   node  = {
 *     type:     "FRAME" | "TEXT" | "IMAGE",
 *     name:     string,
 *     x, y:     number,            // relative to the parent node
 *     width, height: number,
 *     opacity:  number,            // 0..1, omitted when 1
 *     clipsContent: boolean,       // overflow:hidden
 *     fills:    Paint[],           // SOLID | IMAGE | GRADIENT_LINEAR
 *     strokes:  Paint[],           // SOLID only
 *     strokeWeight: number,
 *     cornerRadius: number | {tl,tr,br,bl},
 *     effects:  Effect[],          // DROP_SHADOW | INNER_SHADOW
 *     // TEXT only:
 *     characters, fontSize, fontFamily, fontStyle, letterSpacing,
 *     lineHeight, textAlign, textColor, textDecoration,
 *     // IMAGE only:
 *     image: { b64, mime },
 *     children: node[]
 *   }
 *
 * Coordinates are absolute-position (each node carries x/y inside its parent).
 * CSS transforms are baked into position by getBoundingClientRect, so rotation
 * is flattened in v1 (the node lands where it visually renders, un-rotated).
 * Auto-layout is intentionally NOT emitted yet; the schema leaves room for a
 * later `layout` field without breaking the plugin.
 */
(function () {
  "use strict";

  var SCENE_VERSION = 1;
  // Total inlined-image budget. Past this we stop inlining and emit a flat
  // fill instead, so a heavy page cannot produce a multi-hundred-MB POST.
  var IMAGE_BUDGET_BYTES = 40 * 1024 * 1024;
  // Largest edge we keep for an inlined raster; bigger images are downscaled.
  var MAX_IMAGE_EDGE = 2000;

  function clamp01(n) { return n < 0 ? 0 : n > 1 ? 1 : n; }
  function px(v) { var n = parseFloat(v); return isFinite(n) ? n : 0; }
  function round(n) { return Math.round(n * 100) / 100; }

  // "rgb(12, 34, 56)" / "rgba(12,34,56,0.5)" -> { r,g,b in 0..1, a }
  function parseColor(str) {
    if (!str) return null;
    str = str.trim();
    if (str === "transparent") return { r: 0, g: 0, b: 0, a: 0 };
    var m = str.match(/^rgba?\(([^)]+)\)$/i);
    if (!m) return null;
    var parts = m[1].split(",").map(function (s) { return s.trim(); });
    if (parts.length < 3) return null;
    var r = parseFloat(parts[0]) / 255;
    var g = parseFloat(parts[1]) / 255;
    var b = parseFloat(parts[2]) / 255;
    var a = parts.length > 3 ? parseFloat(parts[3]) : 1;
    if (!isFinite(r) || !isFinite(g) || !isFinite(b)) return null;
    return { r: clamp01(r), g: clamp01(g), b: clamp01(b), a: isFinite(a) ? clamp01(a) : 1 };
  }

  function solidPaint(col) {
    if (!col || col.a <= 0) return null;
    var p = { type: "SOLID", color: { r: round(col.r), g: round(col.g), b: round(col.b) } };
    if (col.a < 1) p.opacity = round(col.a);
    return p;
  }

  // ---- image inlining ---------------------------------------------------

  var _imageBytesUsed = 0;

  function blobToDataUrl(blob) {
    return new Promise(function (resolve, reject) {
      var fr = new FileReader();
      fr.onload = function () { resolve(String(fr.result || "")); };
      fr.onerror = function () { reject(fr.error || new Error("read failed")); };
      fr.readAsDataURL(blob);
    });
  }

  function splitDataUrl(dataUrl) {
    var m = /^data:([^;,]+)[^,]*,(.*)$/i.exec(dataUrl || "");
    if (!m) return null;
    var mime = m[1] || "image/png";
    var b64 = m[2];
    // Approximate decoded size for the budget check.
    var bytes = Math.floor(b64.length * 3 / 4);
    return { b64: b64, mime: mime, bytes: bytes };
  }

  // Draw an already-decoded element (an <img> or a freshly loaded Image) to a
  // canvas, downscaling past MAX_IMAGE_EDGE, and return a data URL. Returns null
  // if the canvas is tainted (cross-origin without CORS) or drawing fails.
  function rasterizeImageEl(imgEl, naturalW, naturalH) {
    try {
      var w = naturalW || imgEl.naturalWidth || imgEl.width;
      var h = naturalH || imgEl.naturalHeight || imgEl.height;
      if (!w || !h) return null;
      var scale = Math.min(1, MAX_IMAGE_EDGE / Math.max(w, h));
      var cw = Math.max(1, Math.round(w * scale));
      var ch = Math.max(1, Math.round(h * scale));
      var canvas = document.createElement("canvas");
      canvas.width = cw; canvas.height = ch;
      var ctx = canvas.getContext("2d");
      ctx.drawImage(imgEl, 0, 0, cw, ch);
      // JPEG for opaque photos keeps the payload small; PNG would bloat it.
      return canvas.toDataURL("image/jpeg", 0.86);
    } catch (e) {
      return null;
    }
  }

  // Resolve a CSS url() or <img> src into { b64, mime } honoring the budget.
  function loadImage(url, hintEl) {
    return new Promise(function (resolve) {
      if (_imageBytesUsed >= IMAGE_BUDGET_BYTES) return resolve(null);
      // Fast path: an <img> already decoded in the page. Draw it directly.
      if (hintEl && hintEl.tagName === "IMG" && hintEl.complete && hintEl.naturalWidth) {
        var direct = rasterizeImageEl(hintEl);
        if (direct) {
          var dd = splitDataUrl(direct);
          if (dd) { _imageBytesUsed += dd.bytes; return resolve({ b64: dd.b64, mime: dd.mime }); }
        }
      }
      if (!url) return resolve(null);
      // Already a data URL: split and budget it.
      if (/^data:/i.test(url)) {
        var sd = splitDataUrl(url);
        if (sd && (_imageBytesUsed + sd.bytes) <= IMAGE_BUDGET_BYTES) {
          _imageBytesUsed += sd.bytes;
          return resolve({ b64: sd.b64, mime: sd.mime });
        }
        return resolve(null);
      }
      // Network fetch (same-origin /source/ assets succeed; cross-origin may
      // fail CORS and falls back to a flat fill upstream).
      var done = false;
      var img = new Image();
      img.crossOrigin = "anonymous";
      img.onload = function () {
        if (done) return; done = true;
        var data = rasterizeImageEl(img);
        if (!data) return resolve(null);
        var sd2 = splitDataUrl(data);
        if (!sd2 || (_imageBytesUsed + sd2.bytes) > IMAGE_BUDGET_BYTES) return resolve(null);
        _imageBytesUsed += sd2.bytes;
        resolve({ b64: sd2.b64, mime: sd2.mime });
      };
      img.onerror = function () {
        if (done) return; done = true;
        // Fetch fallback for hosts that allow it but block <img crossorigin>.
        fetch(url).then(function (r) { return r.blob(); }).then(blobToDataUrl).then(function (durl) {
          var sd3 = splitDataUrl(durl);
          if (!sd3 || (_imageBytesUsed + sd3.bytes) > IMAGE_BUDGET_BYTES) return resolve(null);
          _imageBytesUsed += sd3.bytes;
          resolve({ b64: sd3.b64, mime: sd3.mime });
        }).catch(function () { resolve(null); });
      };
      img.src = url;
    });
  }

  // ---- style extraction -------------------------------------------------

  function cssUrl(value) {
    if (!value || value === "none") return null;
    var m = /url\(\s*(['"]?)([^'")]+)\1\s*\)/i.exec(value);
    return m ? m[2] : null;
  }

  // Best-effort single linear-gradient -> Figma GRADIENT_LINEAR paint.
  // Falls back to null (caller uses background-color) when it cannot parse.
  function parseLinearGradient(value) {
    var m = /linear-gradient\(([^]*)\)/i.exec(value || "");
    if (!m) return null;
    var inner = m[1];
    var stops = [];
    // Split on commas not inside rgb()/rgba().
    var depth = 0, buf = "", segs = [];
    for (var i = 0; i < inner.length; i++) {
      var ch = inner[i];
      if (ch === "(") depth++;
      else if (ch === ")") depth--;
      if (ch === "," && depth === 0) { segs.push(buf); buf = ""; } else buf += ch;
    }
    if (buf.trim()) segs.push(buf);
    var angle = 180; // default "to bottom"
    var first = (segs[0] || "").trim();
    if (/deg/.test(first)) { angle = px(first); segs.shift(); }
    else if (/^to\s+/i.test(first)) {
      var dir = first.toLowerCase();
      if (dir.indexOf("right") >= 0) angle = 90;
      else if (dir.indexOf("left") >= 0) angle = 270;
      else if (dir.indexOf("top") >= 0) angle = 0;
      else angle = 180;
      segs.shift();
    }
    segs.forEach(function (seg, idx) {
      seg = seg.trim();
      var posM = /\s+([\d.]+)%\s*$/.exec(seg);
      var pos = posM ? parseFloat(posM[1]) / 100 : (segs.length > 1 ? idx / (segs.length - 1) : 0);
      var col = parseColor(posM ? seg.slice(0, posM.index) : seg);
      if (col) stops.push({ position: clamp01(pos), color: col });
    });
    if (stops.length < 2) return null;
    return { type: "GRADIENT_LINEAR", angle: angle, stops: stops };
  }

  function readCorner(cs) {
    var tl = px(cs.borderTopLeftRadius);
    var tr = px(cs.borderTopRightRadius);
    var br = px(cs.borderBottomRightRadius);
    var bl = px(cs.borderBottomLeftRadius);
    if (!tl && !tr && !br && !bl) return 0;
    if (tl === tr && tr === br && br === bl) return round(tl);
    return { tl: round(tl), tr: round(tr), br: round(br), bl: round(bl) };
  }

  function readStroke(cs) {
    var widths = [px(cs.borderTopWidth), px(cs.borderRightWidth), px(cs.borderBottomWidth), px(cs.borderLeftWidth)];
    var maxW = Math.max.apply(null, widths);
    if (maxW <= 0) return null;
    if (cs.borderTopStyle === "none" && cs.borderRightStyle === "none" &&
        cs.borderBottomStyle === "none" && cs.borderLeftStyle === "none") return null;
    var col = parseColor(cs.borderTopColor) || parseColor(cs.borderLeftColor);
    var paint = solidPaint(col);
    if (!paint) return null;
    return { paint: paint, weight: round(maxW) };
  }

  // Best-effort parse of the first box-shadow layer -> Figma effect.
  function readShadow(cs) {
    var raw = cs.boxShadow;
    if (!raw || raw === "none") return null;
    var inset = /inset/i.test(raw);
    var s = raw.replace(/inset/ig, "");
    var colM = /(rgba?\([^)]+\))/i.exec(s);
    var col = colM ? parseColor(colM[1]) : null;
    if (colM) s = s.replace(colM[1], "");
    var nums = (s.match(/-?[\d.]+px/g) || []).map(px);
    if (nums.length < 2) return null;
    var eff = {
      type: inset ? "INNER_SHADOW" : "DROP_SHADOW",
      offsetX: round(nums[0]),
      offsetY: round(nums[1]),
      radius: round(nums[2] || 0),
      spread: round(nums[3] || 0),
      color: col || { r: 0, g: 0, b: 0, a: 0.25 }
    };
    return eff;
  }

  function directText(el) {
    var out = "";
    for (var i = 0; i < el.childNodes.length; i++) {
      var n = el.childNodes[i];
      if (n.nodeType === 3) out += n.nodeValue;
    }
    return out.replace(/\s+/g, " ").trim();
  }

  function fontStyleFromWeight(weight, italic) {
    var w = parseInt(weight, 10) || 400;
    var name = w >= 800 ? "ExtraBold" : w >= 700 ? "Bold" : w >= 600 ? "SemiBold"
      : w >= 500 ? "Medium" : w <= 300 ? "Light" : "Regular";
    if (italic) name = name === "Regular" ? "Italic" : name + " Italic";
    return name;
  }

  function applyTextTransform(text, transform) {
    if (transform === "uppercase") return text.toUpperCase();
    if (transform === "lowercase") return text.toLowerCase();
    return text;
  }

  function textAlign(cs) {
    var a = (cs.textAlign || "left").toLowerCase();
    if (a.indexOf("center") >= 0) return "CENTER";
    if (a.indexOf("right") >= 0) return "RIGHT";
    if (a.indexOf("justify") >= 0) return "JUSTIFIED";
    return "LEFT";
  }

  function textDecoration(cs) {
    var d = (cs.textDecorationLine || cs.textDecoration || "").toLowerCase();
    if (d.indexOf("underline") >= 0) return "UNDERLINE";
    if (d.indexOf("line-through") >= 0) return "STRIKETHROUGH";
    return "NONE";
  }

  function makeTextChild(el, cs, rect, parentRect) {
    var text = applyTextTransform(directText(el), (cs.textTransform || "").toLowerCase());
    if (!text) return null;
    var fontFamily = (cs.fontFamily || "Inter").split(",")[0].replace(/['"]/g, "").trim() || "Inter";
    var lh = cs.lineHeight;
    var lineHeight = (!lh || lh === "normal") ? "AUTO" : round(px(lh));
    var ls = px(cs.letterSpacing);
    return {
      type: "TEXT",
      name: text.slice(0, 40),
      x: round(rect.left - parentRect.left),
      y: round(rect.top - parentRect.top),
      width: round(rect.width),
      height: round(rect.height),
      characters: text,
      fontSize: round(px(cs.fontSize) || 16),
      fontFamily: fontFamily,
      fontStyle: fontStyleFromWeight(cs.fontWeight, /italic|oblique/i.test(cs.fontStyle)),
      letterSpacing: isFinite(ls) ? round(ls) : 0,
      lineHeight: lineHeight,
      textAlign: textAlign(cs),
      textColor: solidPaint(parseColor(cs.color)) || { type: "SOLID", color: { r: 0, g: 0, b: 0 } },
      textDecoration: textDecoration(cs)
    };
  }

  // ---- node walk --------------------------------------------------------

  var SKIP_TAGS = { SCRIPT: 1, STYLE: 1, NOSCRIPT: 1, TEMPLATE: 1, LINK: 1, META: 1, HEAD: 1, TITLE: 1, BR: 1 };

  function isRendered(el, cs, rect) {
    if (!cs) return false;
    if (cs.display === "none" || cs.visibility === "hidden" || cs.visibility === "collapse") return false;
    if (parseFloat(cs.opacity) === 0) return false;
    if (rect.width <= 0 || rect.height <= 0) return false;
    return true;
  }

  // Does this frame carry any visible decoration of its own? Decorationless,
  // childless, textless frames are pruned so the Figma layer tree stays clean.
  function hasOwnPaint(node) {
    return (node.fills && node.fills.length) || (node.strokes && node.strokes.length) ||
      (node.effects && node.effects.length) || node.type === "IMAGE";
  }

  function walk(el, parentRect, win, pending) {
    var tag = el.tagName;
    if (!tag || SKIP_TAGS[tag]) return null;
    var rect = el.getBoundingClientRect();
    var cs = win.getComputedStyle(el);
    if (!isRendered(el, cs, rect)) return null;

    var node = {
      type: "FRAME",
      name: (tag.toLowerCase() + (el.id ? "#" + el.id : el.className && typeof el.className === "string" ? "." + el.className.split(" ")[0] : "")).slice(0, 40),
      x: round(rect.left - parentRect.left),
      y: round(rect.top - parentRect.top),
      width: round(rect.width),
      height: round(rect.height),
      fills: [],
      strokes: [],
      effects: [],
      children: []
    };

    var op = parseFloat(cs.opacity);
    if (isFinite(op) && op < 1) node.opacity = round(op);
    if (cs.overflow === "hidden" || cs.overflowX === "hidden" || cs.overflowY === "hidden") node.clipsContent = true;

    // Background: gradient takes precedence over color; an image overlays as a
    // deferred IMAGE paint (resolved after the synchronous walk).
    var bgImage = cs.backgroundImage;
    var grad = bgImage && /linear-gradient/i.test(bgImage) ? parseLinearGradient(bgImage) : null;
    var bgCol = solidPaint(parseColor(cs.backgroundColor));
    if (bgCol) node.fills.push(bgCol);
    if (grad) node.fills.push(grad);
    var bgUrl = cssUrl(bgImage);
    if (bgUrl) {
      var ip = { type: "IMAGE", scaleMode: "FILL", image: null };
      node.fills.push(ip);
      pending.push({ url: bgUrl, el: null, paint: ip });
    }

    var stroke = readStroke(cs);
    if (stroke) { node.strokes.push(stroke.paint); node.strokeWeight = stroke.weight; }

    var corner = readCorner(cs);
    if (corner) node.cornerRadius = corner;

    var shadow = readShadow(cs);
    if (shadow) node.effects.push(shadow);

    // <img> becomes an IMAGE node with a deferred fill.
    if (tag === "IMG") {
      node.type = "IMAGE";
      node.image = null;
      pending.push({ url: el.currentSrc || el.src, el: el, node: node });
    }

    // Children: recurse element children, then attach a TEXT child for the
    // element's own direct text (most leaves have text and no element kids).
    var elementKids = [];
    for (var i = 0; i < el.children.length; i++) elementKids.push(el.children[i]);
    if (elementKids.length) {
      for (var k = 0; k < elementKids.length; k++) {
        var child = walk(elementKids[k], rect, win, pending);
        if (child) node.children.push(child);
      }
    }
    if (tag !== "IMG") {
      var t = makeTextChild(el, cs, rect, rect);
      if (t) node.children.push(t);
    }

    // Prune empty decorationless containers.
    if (node.type === "FRAME" && !hasOwnPaint(node) && !node.children.length && !node.clipsContent) return null;
    if (!node.fills.length) delete node.fills;
    if (!node.strokes.length) delete node.strokes;
    if (!node.effects.length) delete node.effects;
    if (!node.children.length) delete node.children;
    return node;
  }

  /*
   * domToScene(rootEl, opts) -> Promise<scene>
   *   rootEl: an element in a SAME-ORIGIN document (e.g. iframe.contentDocument
   *           .body). opts.name names the top frame in Figma.
   */
  function domToScene(rootEl, opts) {
    opts = opts || {};
    _imageBytesUsed = 0;
    var win = (rootEl.ownerDocument && rootEl.ownerDocument.defaultView) || window;
    var rootRect = rootEl.getBoundingClientRect();
    var pending = [];

    var root = {
      type: "FRAME",
      name: opts.name || "Woven export",
      x: 0, y: 0,
      width: round(rootRect.width || rootEl.scrollWidth || 0),
      height: round(rootRect.height || rootEl.scrollHeight || 0),
      clipsContent: true,
      fills: [],
      children: []
    };
    var rootBg = solidPaint(parseColor(win.getComputedStyle(rootEl).backgroundColor));
    // Default page surface to white when the body has no explicit background.
    root.fills.push(rootBg || { type: "SOLID", color: { r: 1, g: 1, b: 1 } });

    var kids = [];
    for (var i = 0; i < rootEl.children.length; i++) kids.push(rootEl.children[i]);
    for (var j = 0; j < kids.length; j++) {
      var n = walk(kids[j], rootRect, win, pending);
      if (n) root.children.push(n);
    }

    // Resolve all deferred image fills concurrently.
    return Promise.all(pending.map(function (job) {
      return loadImage(job.url, job.el).then(function (img) {
        if (img && job.paint) job.paint.image = img;
        else if (img && job.node) job.node.image = img;
        else if (job.paint) {
          // Image failed: drop the empty IMAGE paint so it does not render black.
          var fills = null;
          // job.paint lives inside some node.fills; mark for removal via flag.
          job.paint._drop = true;
        } else if (job.node) {
          // <img> we could not inline: convert to a neutral placeholder frame.
          job.node.type = "FRAME";
          delete job.node.image;
          job.node.fills = [{ type: "SOLID", color: { r: 0.9, g: 0.9, b: 0.9 } }];
        }
      });
    })).then(function () {
      stripDroppedFills(root);
      return {
        version: SCENE_VERSION,
        name: root.name,
        width: root.width,
        height: root.height,
        imageBytes: _imageBytesUsed,
        root: root
      };
    });
  }

  function stripDroppedFills(node) {
    if (node.fills) {
      node.fills = node.fills.filter(function (f) { return !f._drop; });
      if (!node.fills.length) delete node.fills;
    }
    if (node.children) node.children.forEach(stripDroppedFills);
  }

  window.WovenFigma = {
    version: SCENE_VERSION,
    domToScene: domToScene,
    parseColor: parseColor // exported for tests
  };
})();
